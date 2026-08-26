#!/usr/bin/env python3
"""Unit tests for the negative-control record guard (#312).

Each check builds a synthetic ref/research tree in a temp dir and runs the
guard against it — the guard must both pass a clean tree and fail each drift
class it exists to catch (the #311 provenance error was caught by hand; this
is the mechanization).
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
GUARD = REPO / "scripts" / "check_negative_control_records.py"
PASSED = 0


def check(label: str, got, want) -> None:
    global PASSED
    if got != want:
        print(f"FAIL  {label}: got {got!r}, want {want!r}")
        sys.exit(1)
    PASSED += 1
    print(f"PASS  {label}")


def run_guard(root: Path) -> tuple[int, str]:
    proc = subprocess.run([sys.executable, str(GUARD), "--root", str(root)],
                          capture_output=True, text=True)
    return proc.returncode, proc.stdout + proc.stderr


def make_tree(root: Path, screen=None, enrolled=None, reps=None, doc=None):
    data = root / "ref" / "research" / "data"
    data.mkdir(parents=True, exist_ok=True)
    if screen is not None:
        (data / "negative_control_round9_screen.json").write_text(
            json.dumps(screen))
    if enrolled is not None:
        (data / "negative_control_round9_enrolled.json").write_text(
            json.dumps(enrolled))
    if reps is not None:
        (data / "negative_control_round9_reps.json").write_text(json.dumps(reps))
    if doc is not None:
        (root / "ref" / "research" / "negative_control_round9.md").write_text(doc)


def row(pdb_id, status="screened", enrolled=True):
    r = {"pdb_id": pdb_id, "status": status}
    if status == "screened":
        r["paths"] = {"phenix": {"delta": 0.001}, "gemmi": {"delta": 0.001}}
        r["enrolled"] = enrolled
    return r


CLEAN_SCREEN = {"run": {"run_mode": "full"},
                "rows": [row("1AAA"), row("2BBB", "floor")],
                "d6": {"n_screened": 1, "n_enrolled": 1}}

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    make_tree(root, screen=CLEAN_SCREEN,
              enrolled={"n_enrolled": 1, "entries": [{"pdb_id": "1AAA"}]},
              reps={"initial_representatives": [{"pdb_id": "1AAA",
                                                 "cluster": "c1"}],
                    "clusters": [{"cluster": "c1"}]},
              doc="Attempted 2: 1 floor, 0 data defects, 1 screened.")
    code, out = run_guard(root)
    check("clean tree passes", code, 0)

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    bad = {**CLEAN_SCREEN, "rows": [row("1AAA"), row("1AAA", "floor")]}
    make_tree(root, screen=bad)
    code, out = run_guard(root)
    check("duplicate row ids fail", code, 1)
    check("duplicate message names the file", "duplicate pdb_ids" in out, True)

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    make_tree(root, screen={**CLEAN_SCREEN,
                            "run": {"run_mode": "diagnostic"}})
    code, out = run_guard(root)
    check("diagnostic manifest in a committed record fails", code, 1)
    check("manifest message cites #319", "#319" in out, True)

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    make_tree(root, screen=CLEAN_SCREEN,
              enrolled={"n_enrolled": 1, "entries": [{"pdb_id": "9ZZZ"}]})
    code, out = run_guard(root)
    check("enrolled entry absent from screen fails", code, 1)

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    make_tree(root, screen=CLEAN_SCREEN,
              doc="Attempted 2: 1 floor, 0 data defects — screened count lost.")
    code, out = run_guard(root)
    check("round doc missing a headline figure fails", code, 1)
    check("drift message cites the #311 class", "#311" in out, True)

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    make_tree(root, reps={"initial_representatives":
                          [{"pdb_id": "1AAA", "cluster": "ghost"}],
                          "clusters": [{"cluster": "c1"}]})
    code, out = run_guard(root)
    check("representative naming an unknown cluster fails", code, 1)

# The screened-row-missing-delta class: a screened row with a dead path.
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    broken = {"rows": [{"pdb_id": "1AAA", "status": "screened",
                        "paths": {"phenix": {"delta": 0.001},
                                  "gemmi": {"delta": None}}}]}
    make_tree(root, screen=broken)
    code, out = run_guard(root)
    check("screened row with a missing delta fails", code, 1)

# Malformed committed JSON must be a NAMED failure, not a traceback (r1).
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    data = root / "ref" / "research" / "data"
    data.mkdir(parents=True)
    (data / "negative_control_round9_screen.json").write_text("{truncated…")
    code, out = run_guard(root)
    check("malformed record fails by name", code, 1)
    check("malformed message names the file",
          "negative_control_round9_screen.json" in out and
          "malformed" in out, True)
    check("no traceback leaks", "Traceback" in out, False)

# --- #338: bench and recover records join the gate ----------------------------------

FLAGS_CLEAN = {"F-data": False, "F-geom": False, "F-protected": False,
               "F-shift": False}
FLAGS_TWO = {"F-data": True, "F-geom": True, "F-protected": False,
             "F-shift": False}


def bench_row(pdb_id, subject="null", flags=None, verdict="not-degraded"):
    return {"pdb_id": pdb_id, "subject": subject, "status": "benched",
            "flags": dict(flags or FLAGS_CLEAN),
            "numbers": {"d_phenix": 0.001, "d_gemmi": 0.001,
                        "d_refmac": None, "n_protected_fixed": 0},
            "conflicts": [], "verdict": verdict}


def recover_row(pdb_id, subject="osol", verdict="not-degraded",
                fit=False, flags=None, success=True, refmac=0.001):
    return {"pdb_id": pdb_id, "subject": subject, "status": "completed",
            "recovery_success": success, "w4_contradiction": False,
            "recovered": {"status": "judged", "flags": dict(flags or FLAGS_CLEAN),
                          "fit_degraded": fit, "verdict": verdict,
                          "two_path_only": refmac is None,
                          "numbers": {"d_phenix": 0.001, "d_gemmi": 0.001,
                                      "d_refmac": refmac}}}


def sandbox_recover_row(pdb_id, pgid):
    row = recover_row(pdb_id, subject="osol_h")
    process = {
        "returncode": 0, "start_new_session": True,
        "termination_signal": None,
        "cache_input_hashes": {"input": "a" * 64},
        "output_sha256": "b" * 64,
    }
    row.update({
        "sandbox": pdb_id,
        "pgid": pgid,
        "refmac_convention": "ANIS",
        "refinement_terminated_by_signal": False,
        "store_unchanged": True,
        "processes": {
            "dynamics": dict(process, pgid=pgid - 20),
            "ready_set": dict(process, pgid=pgid - 10),
            "refine": dict(process, pgid=pgid),
            "hydrogen_count_ready": 100,
            "hydrogen_count_refined": 100,
        },
        "anis_log_verification": {"checked": 2, "with_anis": 2},
        "achieved_shift_unmasked": 0.2,
        "achieved_shift_all": 0.25,
        "perturbation_reproduction": {
            "committed_unmasked": 0.19,
            "regenerated_unmasked": 0.2,
            "absdiff_unmasked": 0.01,
            "committed_all": 0.24,
            "regenerated_all": 0.25,
            "absdiff_all": 0.01,
        },
    })
    return row


def make_br_tree(root, bench=None, recover=None, doc=None):
    data = root / "ref" / "research" / "data"
    data.mkdir(parents=True, exist_ok=True)
    if bench is not None:
        (data / "negative_control_round9_bench.json").write_text(
            json.dumps(bench))
    if recover is not None:
        (data / "negative_control_round9_recover.json").write_text(
            json.dumps(recover))
    if doc is not None:
        (root / "ref" / "research" / "negative_control_round9.md").write_text(doc)


CLEAN_BENCH = {"run": {"run_mode": "full"},
               "rows": [bench_row("1AAA"),
                        bench_row("2BBB", "sa", FLAGS_TWO, "DEGRADED")],
               "summary": {"null": {"attempted": 1, "benched": 1,
                                    "degraded": 0, "conflicts": 0,
                                    "protected_fixes": 0},
                           "sa": {"attempted": 1, "benched": 1, "degraded": 1,
                                  "conflicts": 0, "protected_fixes": 0}}}
CLEAN_RECOVER = {"run": {"run_mode": "full"},
                 "rows": [recover_row("1AAA"),
                          recover_row("2BBB", verdict="FIT-DEGRADED",
                                      fit=True, success=False)],
                 "summary": {"osol": {"attempted": 2, "completed": 2,
                                      "successes": 1, "two_path_only": 0,
                                      "w4_contradictions": 0,
                                      "excluded_by_ruling": 0}}}

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    make_br_tree(root, bench=CLEAN_BENCH, recover=CLEAN_RECOVER,
                 doc="Q1: 0/1 false verdicts on nulls.")
    code, out = run_guard(root)
    check("#338: clean bench+recover tree passes", code, 0)

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    bad = {**CLEAN_BENCH,
           "rows": [bench_row("1AAA", flags=FLAGS_TWO)] + CLEAN_BENCH["rows"][1:]}
    make_br_tree(root, bench=bad, doc="Q1: 0/1 false verdicts on nulls.")
    code, out = run_guard(root)
    check("#338: bench verdict contradicting its flags fails", code, 1)
    check("#338:   and names the registered rule", "registered rule" in out, True)

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    bad = json.loads(json.dumps(CLEAN_BENCH))
    bad["summary"]["null"]["degraded"] = 3
    make_br_tree(root, bench=bad, doc="Q1: 0/1 false verdicts on nulls.")
    code, out = run_guard(root)
    check("#338: bench summary miscount fails", code, 1)

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    bad = json.loads(json.dumps(CLEAN_RECOVER))
    bad["rows"][1]["recovered"]["verdict"] = "not-degraded"   # fit says otherwise
    bad["summary"]["osol"]["successes"] = 1
    make_br_tree(root, recover=bad)
    code, out = run_guard(root)
    check("#338: recover verdict contradicting precedence fails", code, 1)
    check("#338:   and names the precedence", "precedence" in out, True)

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    bad = json.loads(json.dumps(CLEAN_RECOVER))
    bad["rows"][0]["recovered"]["two_path_only"] = True   # d_refmac present
    make_br_tree(root, recover=bad)
    code, out = run_guard(root)
    check("#338: two_path_only contradicting d_refmac fails", code, 1)

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    bad = json.loads(json.dumps(CLEAN_RECOVER))
    bad["summary"]["osol"]["w4_contradictions"] = 2
    make_br_tree(root, recover=bad)
    code, out = run_guard(root)
    check("#338: recover per-subject summary miscount fails", code, 1)

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    make_br_tree(root, bench=CLEAN_BENCH,
                 doc="A round doc that never states the Q1 figure.")
    code, out = run_guard(root)
    check("#338: bench round doc without the Q1 headline fails", code, 1)
    check("#338:   and cites the #311 class", "#311" in out, True)

# #382: the FLAT (round-4-style) summary branch, tested synthetically.
FLAT_RECOVER = {"run": {"run_mode": "full"},
                "rows": [dict(recover_row("1AAA"), subject=None),
                         dict(recover_row("2BBB", success=False),
                              subject=None)],
                "summary": {"attempted": 2, "completed": 2,
                            "v2_recovery_success": 1}}

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    make_br_tree(root, recover=FLAT_RECOVER)
    code, out = run_guard(root)
    check("#382: clean flat-summary recover record passes", code, 0)

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    bad = json.loads(json.dumps(FLAT_RECOVER))
    bad["summary"]["v2_recovery_success"] = 2
    make_br_tree(root, recover=bad)
    code, out = run_guard(root)
    check("#382: flat-summary v2 miscount fails", code, 1)

# #356: a sandbox declaration is evidence-bearing, not decorative.  The
# guard checks the row/process join, uniqueness, normal exits, ANIS, and the
# byte-unchanged durable-store claim.
SANDBOX_RECOVER = {
    "run": {"run_mode": "full", "refmac_convention": "ANIS",
            "sandbox_protocol": "per-entry-process-group-v1",
            "set_record": "ref/research/data/negative_control_round2_enrolled.json",
            "perturbation_record":
                "ref/research/data/round4_perturbation_fixture.json",
            "comparison_record":
                "ref/research/data/round5_comparison_fixture.json"},
    "rows": [sandbox_recover_row("1AAA", 1001),
             sandbox_recover_row("2BBB", 1002)],
    "summary": {
        "osol_h": {"attempted": 2, "completed": 2, "successes": 2,
                   "two_path_only": 0, "w4_contradictions": 0,
                   "excluded_by_ruling": 0},
        "sandbox_verification": {"distinct_sandboxes": 2,
                                 "distinct_pgids": 2,
                                 "signal_terminated": 0,
                                 "store_mutations": 0},
        "anis_verification": {"measurable": 2,
                              "mixed_convention_rows": 0,
                              "logs_checked": 4,
                              "logs_with_anis": 4},
        "hydrogen_verification": {"models": 2,
                                  "minimum_ready": 100,
                                  "maximum_ready": 100,
                                  "retained_equal": 2},
        "comparison_with_osol": {
            "record": "ref/research/data/round5_comparison_fixture.json",
            "osol_attempted": 2,
            "osol_successes": 1,
            "osol_h_attempted": 2,
            "osol_h_successes": 2,
            "gained": ["2BBB"],
            "lost": [],
        },
        "perturbation_reproduction": {"n": 2,
                                      "max_absdiff_unmasked": 0.01,
                                      "max_absdiff_all": 0.01},
    },
}


def make_sandbox_tree(root, record):
    make_br_tree(root, recover=record)
    enrolled = root / "ref/research/data/negative_control_round2_enrolled.json"
    enrolled.write_text(json.dumps({
        "n_enrolled": 2,
        "entries": [{"pdb_id": "1AAA"}, {"pdb_id": "2BBB"}],
    }))
    perturbation = root / "ref/research/data/round4_perturbation_fixture.json"
    perturbation.write_text(json.dumps({
        "rows": [
            {"pdb_id": "1AAA", "achieved_shift_unmasked": 0.19,
             "achieved_shift_all": 0.24},
            {"pdb_id": "2BBB", "achieved_shift_unmasked": 0.19,
             "achieved_shift_all": 0.24},
        ]
    }))
    comparison = root / "ref/research/data/round5_comparison_fixture.json"
    comparison.write_text(json.dumps({
        "rows": [
            recover_row("1AAA", subject="osol", success=True),
            recover_row("2BBB", subject="osol", success=False),
        ]
    }))

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    make_sandbox_tree(root, SANDBOX_RECOVER)
    code, out = run_guard(root)
    check("#356: clean sandbox process evidence passes", code, 0)

for label, mutate, expected in (
    ("duplicate pgids", lambda d: d["rows"][1].update(
        {"pgid": 1001, "processes": {"refine": {
            "pgid": 1001, "returncode": 0, "start_new_session": True,
            "termination_signal": None}}}), "not unique"),
    ("wrong entry directory", lambda d: d["rows"][0].update(
        {"sandbox": "2BBB"}), "entry directory"),
    ("non-session refine", lambda d: d["rows"][0]["processes"]["refine"].update(
        {"start_new_session": False}), "start_new_session"),
    ("non-session ready_set", lambda d: d["rows"][0]["processes"]
     ["ready_set"].update({"start_new_session": False}), "ready_set"),
    ("signal-terminated refine", lambda d: d["rows"][0].update(
        {"refinement_terminated_by_signal": True}), "signal-terminated"),
    ("durable-store mutation", lambda d: d["rows"][0].update(
        {"store_unchanged": False}), "byte-unchanged"),
    ("mixed REFMAC convention", lambda d: d["rows"][0].update(
        {"refmac_convention": "ISOT"}), "ANIS"),
    ("drifted perturbation disclosure", lambda d: d["rows"][0]
     ["perturbation_reproduction"].update({"absdiff_all": 0.0}),
     "perturbation reproduction"),
    ("drifted ANIS summary", lambda d: d["summary"]["anis_verification"].update(
        {"logs_with_anis": 3}), "anis_verification"),
    ("row missing one ANIS log", lambda d: d["rows"][0]
     ["anis_log_verification"].update({"checked": 1, "with_anis": 1}),
     "both pre/post"),
    ("invalid cache input hash", lambda d: d["rows"][0]["processes"]
     ["dynamics"]["cache_input_hashes"].update({"input": "not-a-hash"}),
     "content-addressed"),
    ("drifted hydrogen summary", lambda d: d["summary"]
     ["hydrogen_verification"].update({"retained_equal": 1}),
     "hydrogen_verification"),
    ("drifted prior-round comparison", lambda d: d["summary"]
     ["comparison_with_osol"].update({"gained": []}),
     "comparison_with_osol"),
):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        bad = json.loads(json.dumps(SANDBOX_RECOVER))
        mutate(bad)
        make_sandbox_tree(root, bad)
        code, out = run_guard(root)
        check(f"#356: {label} fails", code, 1)
        check(f"#356: {label} is named", expected in out, True)

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    partial = json.loads(json.dumps(SANDBOX_RECOVER))
    partial["rows"] = partial["rows"][:1]
    partial["summary"]["osol_h"].update(
        {"attempted": 1, "completed": 1, "successes": 1}
    )
    partial["summary"]["sandbox_verification"].update(
        {"distinct_sandboxes": 1, "distinct_pgids": 1}
    )
    make_sandbox_tree(root, partial)
    code, out = run_guard(root)
    check("#356: interrupted full record fails enrollment completeness", code, 1)
    check("#356: interrupted record names the missing enrollment id",
          "2BBB" in out and "does not exactly match" in out, True)

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    clean_doc = (
        "osol_h success 2/2; osol comparison 1/2; ANIS 2/2; "
        "H/D 100–100 per model, retained 2/2; all **4** logs; "
        "2 distinct sandbox directories; 2 distinct refinement PGIDs; "
        "0.01 Å unmasked; 0.01 Å all-residue; gained 2BBB. "
        "No old success was lost."
    )
    make_sandbox_tree(root, SANDBOX_RECOVER)
    (root / "ref/research/negative_control_round9.md").write_text(clean_doc)
    code, out = run_guard(root)
    check("#419: clean recover prose headlines pass", code, 0)
    (root / "ref/research/negative_control_round9.md").write_text(
        clean_doc.replace("2/2; osol comparison", "1/2; osol comparison", 1)
    )
    code, out = run_guard(root)
    check("#419: drifted recover prose headline fails", code, 1)
    check("#419: prose drift names the protected headline",
          "osol_h success" in out and "#419" in out, True)

# #434: record families the per-family checks never opened must still be
# parsed, carry a run manifest, and be cited by filename from the round doc.
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    data = root / "ref/research/data"
    data.mkdir(parents=True)
    rec = data / "negative_control_round12_echo.json"
    (root / "ref/research/negative_control_round12_preregistration.md").write_text("# p\n")
    good_run = {"round": 12, "preregistration":
                "negative_control_round12_preregistration.md",
                "tools": {"gemmi": "0.7.5"}}
    rec.write_text(json.dumps({"run": good_run, "l1": {}}))
    code, out = run_guard(root)
    check("#434: orphan-family record without a round doc fails",
          code == 1 and "no round doc" in out, True)
    doc = root / "ref/research/negative_control_round12.md"
    doc.write_text("# round 12\n\nRecord: elsewhere.\n")
    code, out = run_guard(root)
    check("#434: uncited orphan-family record fails",
          code == 1 and "not cited by filename" in out, True)
    doc.write_text("# round 12\n\nRecord: `negative_control_round12_echo.json`.\n")
    code, out = run_guard(root)
    check("#434: cited orphan-family record with a run block passes", code, 0)
    rec.write_text(json.dumps({"l1": {}}))
    code, out = run_guard(root)
    check("#434: orphan-family record without a run manifest fails",
          code == 1 and "no run manifest" in out, True)
    rec.write_text(json.dumps({"run": {}, "l1": {}}))
    code, out = run_guard(root)
    check("#443: an empty run block fails on round, prereg and tools",
          code == 1 and "run.round" in out and "run.preregistration" in out
          and "run.tools" in out, True)
    rec.write_text(json.dumps({"run": dict(good_run, tools={}), "l1": {}}))
    code, out = run_guard(root)
    check("#451: empty run.tools fails", code == 1 and "run.tools" in out, True)
    (root / "escape.md").write_text("x")
    rec.write_text(json.dumps({"run": dict(good_run, preregistration="../../escape.md"),
                               "l1": {}}))
    code, out = run_guard(root)
    check("#450: a ../ preregistration path fails",
          code == 1 and "run.preregistration" in out, True)
    rec.write_text(json.dumps({"run": dict(good_run, round=11), "l1": {}}))
    code, out = run_guard(root)
    check("#443: run.round disagreeing with the filename fails",
          code == 1 and "does not match the filename" in out, True)
    rec.write_text(json.dumps({"run": dict(good_run, run_mode="canary"),
                               "l1": {}}))
    code, out = run_guard(root)
    check("#443: a canary run_mode in an orphan family fails (#319)",
          code == 1 and "full runs only" in out, True)
    rec.write_text("{not json")
    code, out = run_guard(root)
    check("#434: malformed orphan-family record is a named failure",
          code == 1 and "negative_control_round12_echo.json" in out, True)

# #433: the registry's section 6 must restate the record-derived constants.
import importlib.util  # noqa: E402

_spec = importlib.util.spec_from_file_location("cncr", GUARD)
_g = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_g)
CONSTS = {
    "REGISTERED_FIT_THRESHOLDS": {"d_phenix": 0.012, "d_gemmi": 0.01025,
                                  "d_refmac": 0.0056},
    "REGISTERED_FIT_THRESHOLDS_ANIS": {"d_phenix": 0.012, "d_gemmi": 0.01025,
                                       "d_refmac": 0.0115},
    "CANDIDATE_LEG_THIRD_OPINION_STANDDOWN": {"2VXN"},
    "S_R2": {"phenix": 0.00275, "gemmi": 0.0026},
    "MAD_FLOOR": 0.0005,
    "SHIFT_BAND_A": 0.12,
}
GOOD = """## 5. x

| a |

## 6. Negative-control verdict rules (x)

| Rule | Registered form | Provenance |
|---|---|---|
| Family flags | **F-data**: ΔR-free > +3·S_r2 on **both** paths, S_r2 = round-2 scales **0.00275 / 0.00260**; **F-shift**: unmasked Cα shift > **0.12 Å** | p |
| E1 | MAD floored at **0.0005** | p |
| FIT thresholds — ISOT convention (history) | d_phenix **0.01200**, d_gemmi **0.01025**, d_refmac **0.00560** (retired 0.01220) | p |
| FIT thresholds — ANIS convention (current) | d_phenix **0.01200**, d_gemmi **0.01025** (unchanged), d_refmac **0.01150** from x | p |
| W4 | no residual above **2×** its threshold | p |
| Stand-down | Set: **{2VXN}**; membership | p |

## Adding a threshold
"""


import contextlib  # noqa: E402
import io  # noqa: E402


def registry_failures(text, consts=CONSTS):
    fl = []
    with contextlib.redirect_stdout(io.StringIO()):  # #448: quiet negatives
        _g.check_registry_section(text, consts, fl)
    return fl


check("#433: a faithful section 6 passes", registry_failures(GOOD), [])
check("#433: missing section 6 fails",
      any("no '## 6." in f for f in registry_failures(GOOD.split("## 6.")[0])),
      True)
check("#433: a drifted ANIS d_refmac fails",
      any("ANIS convention row states" in f
          for f in registry_failures(GOOD.replace("**0.01150**", "**0.01100**"))),
      True)
check("#433: a drifted ISOT d_phenix fails",
      any("ISOT convention row states" in f
          for f in registry_failures(GOOD.replace("**0.01200**, d_gemmi **0.01025**, d_refmac **0.00560**",
                                                  "**0.01220**, d_gemmi **0.01025**, d_refmac **0.00560**"))),
      True)
check("#433: a widened stand-down set fails",
      any("stand-down set" in f
          for f in registry_failures(GOOD.replace("{2VXN}", "{2VXN, 9YGW}"))),
      True)
check("#433: a drifted S_r2 fails",
      any("S_r2" in f
          for f in registry_failures(GOOD.replace("0.00260**", "0.00270**"))),
      True)
check("#433: a W4 row without the 2x bound fails",
      any("W4" in f for f in registry_failures(GOOD.replace("**2×**", "twice"))),
      True)
check("#433: a drifted MAD floor fails",
      any("MAD_FLOOR" in f
          for f in registry_failures(GOOD.replace("**0.0005**", "**0.0010**"))),
      True)
REAL_CONSTS = _g.registered_constants(REPO / "scripts")
REAL_TEXT = (REPO / "ref/thresholds_and_standards.md").read_text()
check("#442: the real registry passes against the real record-derived constants",
      registry_failures(REAL_TEXT, REAL_CONSTS), [])
check("#442: real registry with ANIS d_refmac 0.01150→0.01100 fails by name",
      any("ANIS convention row states" in f for f in registry_failures(
          REAL_TEXT.replace("d_refmac **0.01150**", "d_refmac **0.01100**"),
          REAL_CONSTS)), True)
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    (root / "ref/research/data").mkdir(parents=True)
    (root / "scripts").mkdir()
    (root / "scripts/bench_recover_leg.py").write_text("raise ImportError('x')\n")
    (root / "ref/thresholds_and_standards.md").write_text("## 6. Negative-control verdict rules\n")
    code, out = run_guard(root)
    check("#442/#447: a tree carrying bench_recover_leg.py enforces §6 and names the exception type",
          code == 1 and "ImportError" in out, True)
code, out = run_guard(REPO)
check("#452: the real checkout passes the guard end-to-end with §6 enforced",
      code == 0 and "cannot be checked" not in out, True)

print(f"\n{PASSED} checks passed")
