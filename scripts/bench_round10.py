#!/usr/bin/env python3
"""Round-10 execution: ``osol_h`` recovery in per-entry sandboxes (#356).

Implements ``negative_control_round10_preregistration.md``:

* regenerate the registered round-4 perturbation;
* add riding hydrogens with ``phenix.ready_set``;
* refine for three macro cycles with ordered solvent and riding H;
* grade both R-free sides with the adopted ANIS REFMAC convention; and
* isolate every entry in ``<work>/<PDB_ID>/`` with process-group-scoped
  timeout/interrupt cleanup.

Diagnostic runs never write under ``ref/``.  Full runs write the SET_RECORD-
gated recover record after every entry so an interruption preserves evidence.

Usage:
    python3 scripts/bench_round10.py --canary
    python3 scripts/bench_round10.py
"""
from __future__ import annotations

import argparse
import concurrent.futures
import importlib.util
import json
import os
import sys
from pathlib import Path
from typing import Sequence

if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
from entry_sandbox import EntrySandbox
from toolchain import phenix

REPO = Path(__file__).resolve().parent.parent
SET_RECORD = "ref/research/data/negative_control_round2_enrolled.json"
ENROLLED_JSON = REPO / SET_RECORD
OUT_JSON = REPO / "ref/research/data/negative_control_round10_recover.json"
R4_RECOVER_RECORD = "ref/research/data/negative_control_round4_recover.json"
R4_RECOVER_JSON = REPO / R4_RECOVER_RECORD
COMPARISON_RECORD = "ref/research/data/negative_control_round5_recover.json"
COMPARISON_JSON = REPO / COMPARISON_RECORD
SUBJECT = "osol_h"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(
        name, REPO / "scripts" / f"{name}.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_scr = _load("screen_round1")
_bnc = _load("bench_negative_control")
_brl = _load("bench_recover_leg")
_b5 = _load("bench_round5")
_bench = _load("bench_refinement_deltas")
_gold = _load("gold_mask")


def _stage(
    sandbox: EntrySandbox,
    name: str,
    arguments: list,
    output_name: str,
    *,
    inputs: Sequence[Path],
    timeout: float,
) -> tuple[Path | None, dict]:
    """Run or resume one stage only when its content identity matches."""
    output = sandbox.child(output_name)
    process_record = sandbox.child(f"{name}_process.json")
    argv = [os.fspath(argument) for argument in arguments]
    input_hashes = {
        str(path.resolve()): _scr.sha256_file(path) for path in inputs
    }
    if output.exists() and process_record.exists():
        try:
            cached = json.loads(process_record.read_text())
        except (json.JSONDecodeError, OSError):
            cached = {}
        cache_matches = (
            cached.get("returncode") == 0
            and cached.get("arguments") == argv
            and cached.get("cache_input_hashes") == input_hashes
            and cached.get("output_sha256") == _scr.sha256_file(output)
        )
        if cache_matches:
            return output, cached
    # Killed, stale, or modified stages can leave plausible partial products.
    # None is reusable without an exact process/input/output identity (#417).
    output.unlink(missing_ok=True)
    result = sandbox.run_logged(arguments, f"{name}.log", timeout=timeout)
    record = result.to_record()
    if result.returncode != 0 or not output.exists():
        sandbox.write_json_atomic(f"{name}_process.json", record)
        return None, record
    record["cache_input_hashes"] = input_hashes
    record["output_sha256"] = _scr.sha256_file(output)
    sandbox.write_json_atomic(f"{name}_process.json", record)
    return output, record


def _stored_inputs(pdb_id: str, durable: Path) -> tuple[dict[str, Path], str]:
    """Resolve the shared store without downloading or mutating it."""
    stem = pdb_id.lower()
    paths = {
        "model": durable / f"{stem}.pdb",
        "cif": durable / f"{stem}.cif",
        "mtz": durable / f"{stem}.mtz",
        "validation": durable / f"{stem}_validation.xml",
    }
    missing = [name for name, path in paths.items()
               if not path.is_file() or path.stat().st_size == 0]
    if missing:
        return paths, "durable inputs missing: " + ", ".join(missing)
    return paths, ""


def _hash_inputs(paths: dict[str, Path]) -> dict[str, str]:
    return {name: _scr.sha256_file(path) for name, path in paths.items()}


def _hydrogen_count(model: Path) -> int:
    import gemmi

    structure = gemmi.read_structure(str(model))
    return sum(
        1
        for model_ in structure
        for chain in model_
        for residue in chain
        for atom in residue
        if atom.element.name in {"H", "D"}
    )


def perturb(
    model: Path, sandbox: EntrySandbox
) -> tuple[Path | None, dict]:
    """Regenerate the registered round-4 perturbation inside one sandbox."""
    prefix = f"r4p_{model.stem}"
    return _stage(
        sandbox,
        "dynamics",
        [
            phenix("phenix.dynamics"),
            model,
            f"stop_at_diff={_brl.STOP_AT_DIFF}",
            f"random_seed={_brl.RANDOM_SEED}",
            f"output_file_name_prefix={prefix}",
        ],
        f"{prefix}.pdb",
        inputs=[model],
        timeout=3600,
    )


def refine_osol_h(
    perturbed: Path,
    mtz: Path,
    sandbox: EntrySandbox,
    pair: tuple[str, str],
    flag: str | None,
) -> tuple[Path | None, dict]:
    """The registered ``osol_h`` subject: ready_set then riding-H refine."""
    # ready_set appends the coordinate extension itself in PHENIX 2.0; giving
    # it ``name.pdb`` produces ``name.pdb.pdb`` (the round-10 canary caught
    # this before the batch).
    ready_stem = f"r10h_{perturbed.stem}_ready"
    ready_name = f"{ready_stem}.pdb"
    ready, ready_process = _stage(
        sandbox,
        "ready_set",
        [
            phenix("phenix.ready_set"),
            perturbed,
            f"ready_set.input.output_dir={sandbox.path}",
            f"ready_set.input.output_file_name={ready_stem}",
            "ready_set.actions.hydrogens=True",
            "ready_set.actions.add_h_to_water=False",
            "ready_set.actions.ligands=True",
        ],
        ready_name,
        inputs=[perturbed],
        timeout=3600,
    )
    processes = {"ready_set": ready_process}
    if ready is None:
        return None, processes
    hydrogen_count_ready = _hydrogen_count(ready)
    if hydrogen_count_ready == 0:
        processes["failure_reason"] = "ready_set output contains no H/D atoms"
        return None, processes

    selectors = [f"miller_array.labels.name={pair[0]},{pair[1]}"]
    if flag is not None:
        selectors.append(f"miller_array.labels.name={flag}")
    prefix = f"r10h_{perturbed.stem}"
    refined, refine_process = _stage(
        sandbox,
        "refine",
        [
            phenix("phenix.refine"),
            ready,
            mtz,
            f"main.number_of_macro_cycles={_bench.MACRO_CYCLES}",
            "ordered_solvent=True",
            "hydrogens.refine=riding",
            *selectors,
            f"output.prefix={prefix}",
            "--overwrite",
        ],
        f"{prefix}_001.pdb",
        inputs=[ready, mtz],
        timeout=10800,
    )
    processes["refine"] = refine_process
    processes["hydrogen_count_ready"] = hydrogen_count_ready
    if refined is not None:
        processes["hydrogen_count_refined"] = _hydrogen_count(refined)
    return refined, processes


def _failure_reason(processes: dict, fallback: str) -> str:
    if processes.get("failure_reason"):
        return str(processes["failure_reason"])
    for name in ("refine", "ready_set", "dynamics"):
        process = processes.get(name)
        if isinstance(process, dict) and process.get("returncode") not in (None, 0):
            return (f"{name} failed with returncode {process['returncode']}"
                    f" (pgid {process.get('pgid')})")
    return fallback


def _run_entry_science(
    row: dict,
    pdb_id: str,
    inputs: dict[str, Path],
    durable: Path,
    sandbox: EntrySandbox,
    thresholds: dict,
    s_r2: dict,
) -> dict:
    mask = _gold.build_mask(pdb_id, durable)
    pair, flag = _scr.select_arrays(inputs["mtz"])
    if pair is None:
        row["status"], row["reason"] = "data_defect", "no registered obs labels"
        return row
    row["array_selection"] = {"obs": list(pair), "free_flag": flag}

    perturbed, dynamics_process = perturb(inputs["model"], sandbox)
    row["processes"] = {"dynamics": dynamics_process}
    if perturbed is None:
        row["status"] = "data_defect"
        row["reason"] = _failure_reason(row["processes"], "dynamics failed")
        return row
    achieved_unmasked, _, achieved_all = _bnc.unmasked_ca_shift(
        inputs["model"], perturbed, _bnc.mask_key_set(mask, "masked")
    )
    row["achieved_shift_unmasked"] = achieved_unmasked
    row["achieved_shift_all"] = achieved_all
    round4_rows = {
        old["pdb_id"].upper(): old
        for old in json.loads(R4_RECOVER_JSON.read_text())["rows"]
    }
    old = round4_rows[pdb_id]
    row["perturbation_reproduction"] = {
        "committed_unmasked": old.get("achieved_shift_unmasked"),
        "regenerated_unmasked": achieved_unmasked,
        "absdiff_unmasked": round(
            abs(achieved_unmasked - old["achieved_shift_unmasked"]), 4
        ),
        "committed_all": old.get("achieved_shift_all"),
        "regenerated_all": achieved_all,
        "absdiff_all": round(abs(achieved_all - old["achieved_shift_all"]), 4),
    }

    recovered, subject_processes = refine_osol_h(
        perturbed, inputs["mtz"], sandbox, pair, flag
    )
    row["processes"].update(subject_processes)
    refine_process = row["processes"].get("refine")
    if isinstance(refine_process, dict):
        row["pgid"] = refine_process.get("pgid")
        row["refinement_terminated_by_signal"] = (
            refine_process.get("termination_signal") is not None
        )
    if recovered is None:
        row["status"] = "data_defect"
        row["reason"] = _failure_reason(row["processes"], "osol_h recovery failed")
        return row

    pre_m = _bnc.measure_model(
        inputs["model"], inputs["mtz"], sandbox.path, "pre", pair, flag,
        deposited_for_refmac=inputs["cif"], anis=True,
    )
    judged = _brl.judge_state(
        SUBJECT, recovered, inputs["model"], inputs["mtz"], sandbox.path,
        pair, flag, mask, pre_m, thresholds, s_r2,
        fit_fn=_b5.e1_fit_degraded, anis=True,
    )
    judged["two_path_only"] = judged.get("numbers", {}).get("d_refmac") is None
    row["recovered"] = judged
    anis_logs = sorted(sandbox.path.glob("refmac_*.log"))
    row["anis_log_verification"] = {
        "checked": len(anis_logs),
        "with_anis": sum(
            "REFI BREF ANIS" in log.read_text(errors="replace")
            for log in anis_logs
        ),
    }
    if judged.get("status") != "judged":
        row["status"] = "data_defect"
        row["reason"] = judged.get("reason", "judgment failed")
        return row
    row["recovery_success"] = (
        judged["numbers"]["shift_unmasked"] is not None
        and judged["numbers"]["shift_unmasked"] < _brl.SHIFT_BAND_A
        and judged["verdict"] == "not-degraded"
    )
    row["w4_contradiction"] = _b5.w4_contradiction(
        judged, thresholds, row["recovery_success"]
    )
    row["status"] = "completed"
    return row


def run_entry(
    entry: dict,
    durable: Path,
    work: Path,
    thresholds: dict,
    s_r2: dict,
) -> dict:
    pdb_id = entry["pdb_id"].upper()
    sandbox = EntrySandbox(work, pdb_id)
    row: dict = {
        "pdb_id": pdb_id,
        "subject": SUBJECT,
        "stratum": entry.get("stratum"),
        "d_min": entry.get("d_min"),
        "sandbox": sandbox.path.name,
        "refmac_convention": "ANIS",
    }
    inputs, input_error = _stored_inputs(pdb_id, durable)
    if input_error:
        row["status"], row["reason"] = "data_defect", input_error
        return row
    before_hashes = _hash_inputs(inputs)
    row["input_hashes"] = before_hashes
    try:
        return _run_entry_science(
            row, pdb_id, inputs, durable, sandbox, thresholds, s_r2
        )
    finally:
        try:
            after_hashes = _hash_inputs(inputs)
        except OSError:
            after_hashes = None
        row["store_unchanged"] = before_hashes == after_hashes
        row["sandbox_files"] = sandbox.inventory()
        if not row["store_unchanged"]:
            raise SystemExit(
                f"bench_round10: {pdb_id} mutated the durable store"
            )


def summarize(rows: list[dict]) -> dict:
    completed = [row for row in rows if row.get("status") == "completed"]
    sandboxes = [row.get("sandbox") for row in completed]
    pgids = [row.get("pgid") for row in completed]
    reproductions = [
        row["perturbation_reproduction"]
        for row in completed
        if isinstance(row.get("perturbation_reproduction"), dict)
    ]
    ready_h = [
        row.get("processes", {}).get("hydrogen_count_ready")
        for row in completed
    ]
    refined_h = [
        row.get("processes", {}).get("hydrogen_count_refined")
        for row in completed
    ]
    old_rows = json.loads(COMPARISON_JSON.read_text()).get("rows", [])
    old_successes = {
        row["pdb_id"].upper() for row in old_rows
        if row.get("subject") == "osol" and row.get("recovery_success")
    }
    current_successes = {
        row["pdb_id"].upper() for row in completed
        if row.get("recovery_success")
    }
    return {
        SUBJECT: {
            "attempted": len(rows),
            "completed": len(completed),
            "successes": sum(1 for row in completed if row.get("recovery_success")),
            "two_path_only": sum(
                1 for row in completed
                if row.get("recovered", {}).get("two_path_only")
            ),
            "w4_contradictions": sum(
                1 for row in completed if row.get("w4_contradiction")
            ),
        },
        "anis_verification": {
            "measurable": sum(
                1 for row in completed
                if row.get("recovered", {}).get("numbers", {}).get("d_refmac")
                is not None
            ),
            "mixed_convention_rows": sum(
                1 for row in completed if row.get("refmac_convention") != "ANIS"
            ),
            "logs_checked": sum(
                row.get("anis_log_verification", {}).get("checked", 0)
                for row in completed
            ),
            "logs_with_anis": sum(
                row.get("anis_log_verification", {}).get("with_anis", 0)
                for row in completed
            ),
        },
        "hydrogen_verification": {
            "models": len(ready_h),
            "minimum_ready": min(ready_h, default=None),
            "maximum_ready": max(ready_h, default=None),
            "retained_equal": sum(
                ready == refined
                for ready, refined in zip(ready_h, refined_h, strict=True)
            ),
        },
        "comparison_with_osol": {
            "record": COMPARISON_RECORD,
            "osol_attempted": sum(
                row.get("subject") == "osol" for row in old_rows
            ),
            "osol_successes": len(old_successes),
            "osol_h_attempted": len(completed),
            "osol_h_successes": len(current_successes),
            "gained": sorted(current_successes - old_successes),
            "lost": sorted(old_successes - current_successes),
        },
        "sandbox_verification": {
            "distinct_sandboxes": len(set(sandboxes)),
            "distinct_pgids": len(set(pgids)),
            "signal_terminated": sum(
                1 for row in completed
                if row.get("refinement_terminated_by_signal")
            ),
            "store_mutations": sum(
                1 for row in completed if not row.get("store_unchanged")
            ),
        },
        "perturbation_reproduction": {
            "n": len(reproductions),
            "max_absdiff_unmasked": max(
                (row["absdiff_unmasked"] for row in reproductions), default=None
            ),
            "max_absdiff_all": max(
                (row["absdiff_all"] for row in reproductions), default=None
            ),
        },
    }


def main() -> int:
    from benchmark_environment import announce_benchmark_environment

    announce_benchmark_environment()
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--durable", default=str(Path.home() / "protstruct_bench_inputs")
    )
    parser.add_argument("--work", default="/tmp/nc_round10_work")
    parser.add_argument("--canary", action="store_true")
    parser.add_argument("--only", default="")
    parser.add_argument("--out", help="output for diagnostic runs")
    parser.add_argument(
        "--jobs", type=int, default=1,
        help="isolated entries to run concurrently (default: 1)",
    )
    args = parser.parse_args()
    if args.jobs < 1:
        raise SystemExit("bench_round10: --jobs must be >= 1")

    thresholds = _brl.anis_thresholds_from_record()
    s_r2 = _brl.s_r2_from_record()
    enrolled = json.loads(ENROLLED_JSON.read_text())["entries"]
    queue = list(enrolled)
    if args.only:
        wanted = {item.strip().upper() for item in args.only.split(",")}
        queue = [entry for entry in queue if entry["pdb_id"].upper() in wanted]
    if args.canary:
        queue = queue[:1]

    full_run = not (args.canary or args.only)
    if args.out:
        out_path = Path(args.out)
    elif full_run:
        out_path = OUT_JSON
    else:
        out_path = Path("/tmp/nc_round10_diagnostic.json")
        print(f"  diagnostic run: writing {out_path}", file=sys.stderr)
    if not full_run and (REPO / "ref") in out_path.resolve().parents:
        raise SystemExit(
            "bench_round10: a diagnostic run may not write inside ref/ (#319)"
        )

    durable, work = Path(args.durable).resolve(), Path(args.work).resolve()
    if durable == work or durable in work.parents or work in durable.parents:
        raise SystemExit("bench_round10: durable store and work root must be disjoint")
    work.mkdir(parents=True, exist_ok=True)
    manifest = {
        "run_mode": "full" if full_run else "diagnostic",
        "preregistration": "negative_control_round10_preregistration.md",
        "round": 10,
        "subject": SUBJECT,
        "set_record": SET_RECORD,
        "perturbation_record": R4_RECOVER_RECORD,
        "comparison_record": COMPARISON_RECORD,
        "fit_rule": "E1",
        "fit_thresholds": thresholds,
        "refmac_convention": "ANIS",
        "sandbox_protocol": "per-entry-process-group-v1",
        "jobs": args.jobs,
        "durable_store": str(durable),
        "tools": _scr.tool_versions(),
    }
    rows_by_index: dict[int, dict] = {}

    def record_row(index: int, row: dict) -> None:
        rows_by_index[index] = row
        rows = [rows_by_index[key] for key in sorted(rows_by_index)]
        tag = (
            f"{row['recovered']['verdict']} success={row['recovery_success']} "
            f"sandbox={row['sandbox']} pgid={row.get('pgid')}"
            if row["status"] == "completed"
            else row.get("reason", "")
        )
        print(f"  -> {row['status']}: {tag}", file=sys.stderr)
        _scr.write_json_atomic(
            out_path, {"run": manifest, "rows": rows, "summary": summarize(rows)}
        )

    if args.jobs == 1:
        for index, entry in enumerate(queue):
            print(f"[{entry['pdb_id']} / {SUBJECT}]", file=sys.stderr)
            record_row(index, run_entry(entry, durable, work, thresholds, s_r2))
    else:
        print(f"  launching {len(queue)} entries with jobs={args.jobs}",
              file=sys.stderr)
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs)
        futures = {
            executor.submit(run_entry, entry, durable, work, thresholds, s_r2): index
            for index, entry in enumerate(queue)
        }
        try:
            for future in concurrent.futures.as_completed(futures):
                record_row(futures[future], future.result())
        except BaseException:
            EntrySandbox.terminate_all_active()
            for future in futures:
                future.cancel()
            executor.shutdown(wait=True, cancel_futures=True)
            raise
        else:
            executor.shutdown(wait=True)

    rows = [rows_by_index[key] for key in sorted(rows_by_index)]
    summary = summarize(rows)
    print(json.dumps(summary, indent=2))
    subject_summary = summary[SUBJECT]
    if subject_summary["w4_contradictions"]:
        raise SystemExit(
            "bench_round10: W4 violated — a success contradicts its own evidence"
        )
    if full_run:
        sandbox_summary = summary["sandbox_verification"]
        expected = len(queue)
        if (
            subject_summary["completed"] != expected
            or sandbox_summary["distinct_sandboxes"] != expected
            or sandbox_summary["distinct_pgids"] != expected
            or sandbox_summary["signal_terminated"]
            or sandbox_summary["store_mutations"]
        ):
            raise SystemExit("bench_round10: the registered sandbox prediction failed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
