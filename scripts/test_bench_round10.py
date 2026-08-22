#!/usr/bin/env python3
"""Network/PHENIX-free tests for the round-10 sandboxed driver (#356)."""
from __future__ import annotations

import importlib.util
import sys
import tempfile
from pathlib import Path

from entry_sandbox import ProcessGroupResult

REPO = Path(__file__).resolve().parent.parent
PASSED = 0


def load():
    spec = importlib.util.spec_from_file_location(
        "bench_round10", REPO / "scripts" / "bench_round10.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["bench_round10"] = module
    spec.loader.exec_module(module)
    return module


def check(label, got, want):
    global PASSED
    if got != want:
        print(f"FAIL  {label}: got {got!r}, want {want!r}")
        sys.exit(1)
    PASSED += 1
    print(f"PASS  {label}")


b10 = load()


class FakeSandbox:
    def __init__(self, path: Path):
        self.path = path
        self.path.mkdir()
        self.calls = []
        self.next_pid = 100

    def child(self, relative):
        return self.path / relative

    def write_json_atomic(self, relative, payload):
        import json
        path = self.child(relative)
        path.write_text(json.dumps(payload))
        return path

    def run_logged(self, arguments, log_name, timeout=None):
        self.calls.append([str(argument) for argument in arguments])
        self.child(log_name).write_text("synthetic log\n")
        if "phenix.ready_set" in str(arguments[0]):
            output_stem = next(
                argument.split("=", 1)[1]
                for argument in map(str, arguments)
                if "output_file_name=" in argument
            )
            self.child(f"{output_stem}.pdb").write_text("ready\n")
        else:
            prefix = next(
                argument.split("=", 1)[1]
                for argument in map(str, arguments)
                if argument.startswith("output.prefix=")
            )
            self.child(f"{prefix}_001.pdb").write_text("refined\n")
        result = ProcessGroupResult(
            arguments=[str(argument) for argument in arguments],
            returncode=0, pid=self.next_pid, pgid=self.next_pid,
            timed_out=False, termination_signal=None,
        )
        self.next_pid += 1
        return result


with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    sandbox = FakeSandbox(root / "1AAA")
    perturbed = sandbox.child("r4p_1aaa.pdb")
    reflections = root / "1aaa.mtz"
    perturbed.write_text("perturbed\n")
    reflections.write_text("reflections\n")
    original_hydrogen_count = b10._hydrogen_count
    b10._hydrogen_count = lambda _path: 42
    try:
        recovered, processes = b10.refine_osol_h(
            perturbed, reflections, sandbox, ("FOBS", "SIGFOBS"), "FREE"
        )
    finally:
        b10._hydrogen_count = original_hydrogen_count
    ready_args, refine_args = sandbox.calls
    check("ready_set is the registered H-addition mechanism",
          any("phenix.ready_set" in argument for argument in ready_args), True)
    check("waters do not receive hydrogens",
          "ready_set.actions.add_h_to_water=False" in ready_args, True)
    check("ordered solvent remains enabled", "ordered_solvent=True" in refine_args,
          True)
    check("hydrogens are explicitly refined as riding",
          "hydrogens.refine=riding" in refine_args, True)
    check("registered array selection reaches refine",
          ("miller_array.labels.name=FOBS,SIGFOBS" in refine_args
           and "miller_array.labels.name=FREE" in refine_args), True)
    check("both isolated process records are retained",
          set(processes) >= {"ready_set", "refine"}, True)
    check("the H-bearing refined output is returned", recovered.exists(), True)


# ANIS must reach the REFMAC call used by both pre and post measurement.  This
# test stubs every scientific tool and observes only that load-bearing switch.
seen_anis = []
originals = {
    "phenix": b10._bnc._scr.model_vs_data_rfree,
    "gemmi": b10._bnc._scr.gemmi_rfree,
    "refmac": b10._bnc.refmac_pass,
    "measure": b10._bnc._bench.measure,
    "residues": b10._bnc.per_residue_verdicts,
}
b10._bnc._scr.model_vs_data_rfree = lambda *_a, **_k: 0.1
b10._bnc._scr.gemmi_rfree = lambda *_a, **_k: 0.1
b10._bnc.refmac_pass = (
    lambda *_a, anis=False, **_k:
    (seen_anis.append(anis) or {"r_free": 0.1, "z_bond": 0.0})
)
b10._bnc._bench.measure = lambda *_a, **_k: {}
b10._bnc.per_residue_verdicts = lambda *_a, **_k: {}
try:
    b10._bnc.measure_model(
        Path("model.pdb"), Path("data.mtz"), Path("."), "pre",
        ("F", "SIGF"), "FREE", anis=True,
    )
finally:
    b10._bnc._scr.model_vs_data_rfree = originals["phenix"]
    b10._bnc._scr.gemmi_rfree = originals["gemmi"]
    b10._bnc.refmac_pass = originals["refmac"]
    b10._bnc._bench.measure = originals["measure"]
    b10._bnc.per_residue_verdicts = originals["residues"]
check("measure_model forwards ANIS to REFMAC", seen_anis, [True])


def completed_row(index: int) -> dict:
    return {
        "pdb_id": f"E{index:03d}", "status": "completed",
        "sandbox": f"E{index:03d}", "pgid": 1000 + index,
        "refmac_convention": "ANIS", "store_unchanged": True,
        "refinement_terminated_by_signal": False,
        "recovery_success": index < 14, "w4_contradiction": False,
        "perturbation_reproduction": {
            "absdiff_unmasked": round(index / 10000, 4),
            "absdiff_all": round(index / 20000, 4),
        },
        "recovered": {"two_path_only": index == 21,
                      "numbers": {"d_refmac": None if index == 21 else 0.001}},
    }


summary = b10.summarize([completed_row(index) for index in range(22)])
check("Y1 summary counts successes from rows", summary["osol_h"]["successes"], 14)
check("Y2 summary counts 21 measurable ANIS rows",
      summary["anis_verification"],
      {"measurable": 21, "mixed_convention_rows": 0})
check("Y3 summary derives distinct sandboxes and pgids",
      summary["sandbox_verification"],
      {"distinct_sandboxes": 22, "distinct_pgids": 22,
       "signal_terminated": 0, "store_mutations": 0})
check("perturbation disclosure is derived from every row",
      summary["perturbation_reproduction"],
      {"n": 22, "max_absdiff_unmasked": 0.0021,
       "max_absdiff_all": 0.001})

print(f"\n{PASSED} checks passed")
