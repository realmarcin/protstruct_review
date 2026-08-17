#!/usr/bin/env python3
"""Round-5 execution: S-osol and S-agent recoveries under the E1 fit rule.

Implements `negative_control_round5_preregistration.md`:

- **E1**: fit status always requires positive evidence. REFMAC measurable →
  the C1 all-three rule; REFMAC unmeasurable → the TWO-PATH rule stands alone
  (both `d_phenix` and `d_gemmi` past their null-centered thresholds), with
  the row marked `two_path_only`.
- **S-osol**: the null protocol + `ordered_solvent=True`, recovering the
  cached round-4 `r4p_` perturbed models (prefix `r5o_`).
- **S-agent**: judgment of committed agent artifacts (final model per entry
  under `data/agents/round5/<ID>/final.pdb`) — the models are produced by the
  blinded agent sessions per the registration; this script only JUDGES them
  (no agent-reported number enters any verdict).
- **W4 invariant**: computed per row — a success whose measurable residuals
  exceed twice their thresholds contradicts its own evidence; any such row
  fails the run loudly.

Usage:
    python3 scripts/bench_round5.py --subject osol --canary
    python3 scripts/bench_round5.py --subject osol
    python3 scripts/bench_round5.py --subject agent
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SET_RECORD = "ref/research/data/negative_control_round2_enrolled.json"
ENROLLED_JSON = REPO / SET_RECORD
OUT_JSON = REPO / "ref/research/data/negative_control_round5_recover.json"
AGENT_DIR = REPO / "data/agents/round5"

PHENIX_BIN = Path.home() / "phenix-2.0-5936" / "phenix_bin"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / f"{name}.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


_scr = _load("screen_round1")
_bnc = _load("bench_negative_control")
_brl = _load("bench_recover_leg")
_bench = _load("bench_refinement_deltas")
_gold = _load("gold_mask")


def e1_fit_degraded(numbers: dict, thresholds: dict) -> bool:
    """E1: positive evidence always. All-three when REFMAC is measurable;
    two-path standing alone when it is not. Never None."""
    if numbers.get("d_refmac") is not None:
        return all(numbers.get(t) is not None and numbers[t] > thresholds[t]
                   for t in thresholds)
    return all(numbers.get(t) is not None and numbers[t] > thresholds[t]
               for t in ("d_phenix", "d_gemmi"))


def w4_contradiction(row_state: dict, thresholds: dict, success: bool) -> bool:
    """W4: a success may not contradict its own evidence — no measurable
    path's residual may exceed TWICE its threshold."""
    if not success:
        return False
    n = row_state.get("numbers", {})
    return any(n.get(t) is not None and n[t] > 2 * thresholds[t]
               for t in thresholds)


def refine_osol(perturbed: Path, mtz: Path, work: Path,
                pair, flag) -> tuple[Path | None, dict]:
    """S-osol: the null protocol + ordered_solvent=True, own prefix."""
    selectors = f"\"miller_array.labels.name={pair[0]},{pair[1]}\""
    if flag is not None:
        selectors += f" \"miller_array.labels.name={flag}\""
    prefix = f"r5o_{perturbed.stem}"
    out = work / f"{prefix}_001.pdb"
    log = work / f"refine_{prefix}.log"
    if not out.exists():
        subprocess.run(
            ["bash", "-c",
             f"cd {work} && {PHENIX_BIN / 'phenix.refine'} {perturbed} {mtz} "
             f"main.number_of_macro_cycles={_bench.MACRO_CYCLES} "
             f"ordered_solvent=True {selectors} "
             f"output.prefix={prefix} --overwrite > {log} 2>&1"],
            capture_output=True, text=True, timeout=10800, env=dict(os.environ))
    if not out.exists():
        return None, {"failure_reason": _bench.refine_failure_reason(log)}
    return out, {}


def run_entry(entry: dict, subject: str, cache: Path, work: Path,
              thresholds: dict, s_r2: dict) -> dict:
    pdb_id = entry["pdb_id"].upper()
    row: dict = {"pdb_id": pdb_id, "subject": subject,
                 "stratum": entry.get("stratum"), "d_min": entry.get("d_min")}
    model, mtz, fetch_err = _scr.fetch_pair(pdb_id, cache)
    if fetch_err:
        row["status"], row["reason"] = "data_defect", fetch_err
        return row
    mask = _gold.build_mask(pdb_id, cache)
    pair, flag = _scr.select_arrays(mtz)
    if pair is None:
        row["status"], row["reason"] = "data_defect", "no registered obs labels"
        return row

    perturbed = work / f"r4p_{model.stem}.pdb"
    if not perturbed.exists():
        perturbed, err = _brl.perturb(model, work)
        if perturbed is None:
            row["status"], row["reason"] = "data_defect", err
            return row

    if subject == "osol":
        recovered, r_stats = refine_osol(perturbed, mtz, work, pair, flag)
        if recovered is None:
            row["status"] = "data_defect"
            row["reason"] = r_stats.get("failure_reason", "recovery failed")
            return row
    else:                                     # agent
        artifact = AGENT_DIR / pdb_id / "final.pdb"
        if not artifact.exists():
            row["status"] = "artifact_missing"
            row["reason"] = f"no committed agent artifact at {artifact}"
            return row
        transcript = AGENT_DIR / pdb_id / "transcript.md"
        row["artifact_hashes"] = {
            "final": _scr.sha256_file(artifact),
            "transcript": _scr.sha256_file(transcript)
            if transcript.exists() else None}
        # Stage under a unique stem: every artifact is named final.pdb, so
        # judging in place collides every post-measurement cache across
        # entries (the #314 class, resurrected — W4 caught it as 18
        # certifications contradicting their own evidence).
        recovered = work / f"r5a_{pdb_id.lower()}.pdb"
        recovered.write_bytes(artifact.read_bytes())

    pre_m = _bnc.measure_model(model, mtz, work, "pre", pair, flag,
                               deposited_for_refmac=(cache / f"{pdb_id.lower()}.cif")
                               if (cache / f"{pdb_id.lower()}.cif").exists() else None)
    judged = _brl.judge_state(subject, Path(recovered), model, mtz, work,
                              pair, flag, mask, pre_m, thresholds, s_r2,
                              fit_fn=e1_fit_degraded)
    judged["two_path_only"] = judged.get("numbers", {}).get("d_refmac") is None
    row["recovered"] = judged
    if judged.get("status") != "judged":
        row["status"] = "data_defect"
        row["reason"] = judged.get("reason", "judgment failed")
        return row
    row["recovery_success"] = (
        judged["numbers"]["shift_unmasked"] is not None
        and judged["numbers"]["shift_unmasked"] < _brl.SHIFT_BAND_A
        and judged["verdict"] == "not-degraded")
    row["w4_contradiction"] = w4_contradiction(judged, thresholds,
                                               row["recovery_success"])
    row["status"] = "completed"
    return row


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--subject", choices=("osol", "agent"), required=True)
    ap.add_argument("--cache", default="/tmp/nc_round1_cache")
    ap.add_argument("--work", default="/tmp/nc_round1_work")
    ap.add_argument("--canary", action="store_true")
    ap.add_argument("--only", default="")
    ap.add_argument("--out", help="output for diagnostic runs")
    args = ap.parse_args()

    thresholds = _brl.fit_thresholds_from_record()
    s_r2 = _brl.s_r2_from_record()
    enrolled = json.loads(ENROLLED_JSON.read_text())["entries"]
    queue = list(enrolled)
    if args.only:
        wanted = {i.strip().upper() for i in args.only.split(",")}
        queue = [e for e in queue if e["pdb_id"].upper() in wanted]
    if args.canary:
        queue = queue[:1]

    full_run = not (args.canary or args.only)
    if args.out:
        out_path = Path(args.out)
    elif full_run:
        out_path = OUT_JSON
    else:
        out_path = Path("/tmp/nc_round5_diagnostic.json")
        print(f"  diagnostic run: writing {out_path}", file=sys.stderr)
    if not full_run and (REPO / "ref") in out_path.resolve().parents:
        raise SystemExit("bench_round5: a diagnostic run may not write "
                         "inside ref/ (#319)")

    cache, work = Path(args.cache), Path(args.work)
    cache.mkdir(parents=True, exist_ok=True)
    work.mkdir(parents=True, exist_ok=True)

    # The canonical record accumulates BOTH subjects across invocations
    # (S-agent runs after S-osol's record is committed, per registration);
    # rows for the invoked subject are replaced, the other subject's kept.
    prior: list[dict] = []
    if full_run and out_path.exists():
        prior = [r for r in json.loads(out_path.read_text()).get("rows", [])
                 if r.get("subject") != args.subject]

    manifest = {"run_mode": "full" if full_run else "diagnostic",
                "preregistration": "negative_control_round5_preregistration.md",
                "round": 5, "fit_rule": "E1",
                "fit_thresholds": thresholds, "tools": _scr.tool_versions()}

    rows: list[dict] = list(prior)
    for entry in queue:
        print(f"[{entry['pdb_id']} / S-{args.subject}]", file=sys.stderr)
        row = run_entry(entry, args.subject, cache, work, thresholds, s_r2)
        rows.append(row)
        tag = (f"{row['recovered']['verdict']} success={row['recovery_success']}"
               f"{' TWO-PATH' if row['recovered'].get('two_path_only') else ''}"
               if row["status"] == "completed" else row.get("reason", ""))
        print(f"  -> {row['status']}: {tag}", file=sys.stderr)
        _scr.write_json_atomic(out_path, {"run": manifest, "rows": rows})

    summary = {}
    for subject in ("osol", "agent"):
        sub = [r for r in rows if r.get("subject") == subject]
        if not sub:
            continue
        summary[subject] = {
            "attempted": len(sub),
            "completed": sum(1 for r in sub if r["status"] == "completed"),
            "successes": sum(1 for r in sub if r.get("recovery_success")),
            "two_path_only": sum(1 for r in sub
                                 if r.get("recovered", {}).get("two_path_only")),
            "w4_contradictions": sum(1 for r in sub
                                     if r.get("w4_contradiction")),
        }
    _scr.write_json_atomic(out_path, {"run": manifest, "rows": rows,
                                      "summary": summary})
    print(json.dumps(summary, indent=2))
    if any(s["w4_contradictions"] for s in summary.values()):
        raise SystemExit("bench_round5: W4 violated — a success contradicts "
                         "its own evidence")
    return 0


if __name__ == "__main__":
    sys.exit(main())
