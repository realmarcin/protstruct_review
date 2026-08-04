#!/usr/bin/env python3
"""Benchmark what the NMR-precision tolerance's precondition is actually worth.

The `NMR ensemble precision (mean Cα RMSF)` tolerance in
`ref/thresholds_and_standards.md` is `|Δ| ≤ 0.05 Å` **only on a matched ordered-core
selection**, on the grounds that "precision is dominated by the superposition
selection". No second implementation is installed, so a cross-tool benchmark is not
available — but the claim the precondition rests on *is* measurable: sweep the
ordered-core cutoff and see how far the reported precision moves.

`scripts/t17_nmr_ensemble.py` defines the ordered core; its cutoff is read from
`_ORDERED_CORE_RMSF_CUTOFF` rather than restated here, and the harness's own
`ordered_core_precision()` computes the value at that cutoff, so the "harness" column
IS the harness's metric.

That sentence used to claim this and was false (#139): the module was imported only for
`run_precision()`, the filter was reimplemented inline, and `2.0` was hardcoded as a
string key. The two copies also disagreed on rounding (`sum/len` to 3 dp against
`fmean` to 4) and on empty cores (loud failure against a silent `None`), so the sweep
was a re-implementation labelled as the original.

Usage:
    python3 scripts/bench_t17_ordered_core.py ENSEMBLE.pdb [...] --json out.json
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import statistics
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parent.parent

# Cutoffs spanning plausible choices: OLDERADO/PSVS-style ordered-core definitions
# vary, and the harness's pick is only one of them -- which is the point of the sweep.
# The harness's own value is NOT listed here; it is read from the harness and added to
# the sweep at run time, so changing it there moves this benchmark with it (#139).
SWEEP_CUTOFFS = [1.0, 1.5, 2.0, 2.5, 3.0, 4.0]


def load_t17():
    """Import the harness's T17 script so the benchmark measures its actual metric."""
    spec = importlib.util.spec_from_file_location("t17", REPO / "scripts" / "t17_nmr_ensemble.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def collect(models: list[Path]) -> tuple[list[dict], list[dict]]:
    """Sweep the ordered-core cutoff over each ensemble."""
    t17 = load_t17()
    rows, skipped = [], []
    for model in models:
        print(f"[{model.name}]", file=sys.stderr)
        try:
            rmsf = t17.run_precision(model).get("rmsf_values")
        except SystemExit as exc:           # the T17 script fails loudly by design
            print(f"  ! {exc}", file=sys.stderr)
            skipped.append({"model": model.name, "reason": str(exc)})
            continue
        if not rmsf:
            skipped.append({"model": model.name, "reason": "no per-residue RMSF available"})
            continue

        whole_chain = statistics.fmean(rmsf)
        # The harness's own cutoff, read from the harness. Merged into the sweep so the
        # sweep always contains it, whatever it is set to.
        harness_cutoff = t17._ORDERED_CORE_RMSF_CUTOFF
        per_cutoff = {}
        for cutoff in sorted(set(SWEEP_CUTOFFS) | {harness_cutoff}):
            core = [v for v in rmsf if v <= cutoff]
            per_cutoff[str(cutoff)] = {
                "mean_rmsf": round(statistics.fmean(core), 4) if core else None,
                "n_core": len(core),
            }
        # The harness column is computed by the HARNESS, not re-derived here: it rounds
        # to 3 dp via sum/len and fails loudly on an empty core, and a benchmark that
        # quietly used fmean/4 dp and `None` was measuring something else (#139).
        try:
            # Cutoff passed EXPLICITLY. `ordered_core_precision`'s default argument is
            # bound at def time, so calling it bare would use the value the module had
            # when it was imported and silently ignore `harness_cutoff` -- two copies
            # again, by a subtler route than the one #139 was filed for.
            harness_mean, harness_n = t17.ordered_core_precision(rmsf, harness_cutoff)
        except SystemExit as exc:
            harness_mean, harness_n = None, 0
            print(f"  ! harness ordered core: {exc}", file=sys.stderr)
        means = [v["mean_rmsf"] for v in per_cutoff.values() if v["mean_rmsf"] is not None]
        rows.append({
            "model": model.name,
            "n_residues": len(rmsf),
            "whole_chain_mean_rmsf": round(whole_chain, 4),
            "by_cutoff": per_cutoff,
            "spread_across_cutoffs": round(max(means) - min(means), 4) if means else None,
            # Named for the cutoff it used, not for a literal that can go stale: at
            # cutoff 2.0 this key is `whole_chain_minus_2.0A_core`, and it MOVES if the
            # harness's cutoff moves rather than silently reporting the old bucket.
            "harness_cutoff": harness_cutoff,
            "harness_ordered_core_mean_rmsf": harness_mean,
            "harness_ordered_core_n": harness_n,
            f"whole_chain_minus_{harness_cutoff}A_core": (
                round(whole_chain - harness_mean, 4) if harness_mean is not None else None),
        })
        print(f"  whole-chain {whole_chain:.4f} Å; cutoff sweep "
              + ", ".join(f"{c}→{per_cutoff[c]['mean_rmsf']}" for c in per_cutoff)
              + f"  (spread {rows[-1]['spread_across_cutoffs']} Å)", file=sys.stderr)
    return rows, skipped


def summarize(rows: list[dict]) -> dict[str, Any]:
    """How far the reported precision moves with the selection, vs the 0.05 Å band."""
    if not rows:
        return {"n": 0}
    spreads = [r["spread_across_cutoffs"] for r in rows if r["spread_across_cutoffs"] is not None]
    gaps = [abs(r["whole_chain_minus_2A_core"]) for r in rows
            if r["whole_chain_minus_2A_core"] is not None]
    return {
        "n_ensembles": len(rows),
        "cutoff_sweep_spread": {
            "median": round(statistics.median(spreads), 4) if spreads else None,
            "max": round(max(spreads), 4) if spreads else None,
        },
        "whole_chain_vs_ordered_core_gap": {
            "median": round(statistics.median(gaps), 4) if gaps else None,
            "max": round(max(gaps), 4) if gaps else None,
        },
        "tolerance_band": 0.05,
    }


# The 5 NMR ensembles the ordered-core sensitivity was measured on, plus the one that
# failed outright, committed in round 18. Recovered from the per-entry table in
# `ref/research/tolerance_benchmark_selection_sensitivity.md`, which gives every
# ensemble's mean RMSF at every cutoff from 1.0 to 4.0 A -- so unlike most rows in the
# registry, this one's numbers can be recounted.
#
# This script takes model FILES rather than ids, so the set cannot be a runnable
# default; it is recorded here because a set that exists only in a markdown table is one
# reorganisation away from the position the L-test set is already in.
DEFAULT_SET = ["1D3Z", "1G6J", "1XPW", "2K39", "2N54"]
SET_IS_COMPLETE = True
SET_FAILED = ["2JZ4"]        # reported as failing outright; kept so the set is 6 attempts
# Ensembles are passed as file paths, not ids, so the set cannot drive a run.
SET_NOT_RUNNABLE = "takes model files rather than PDB ids"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("models", nargs="+", type=Path)
    ap.add_argument("--json", dest="json_out")
    args = ap.parse_args()

    rows, skipped = collect(args.models)
    summary = summarize(rows)
    if args.json_out:
        Path(args.json_out).write_text(
            json.dumps({"rows": rows, "skipped": skipped, "summary": summary}, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    return 0 if rows else 1


if __name__ == "__main__":
    raise SystemExit(main())
