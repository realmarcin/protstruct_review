#!/usr/bin/env python3
"""Benchmark what the NMR-precision tolerance's precondition is actually worth.

The `NMR ensemble precision (mean Cα RMSF)` tolerance in
`ref/thresholds_and_standards.md` is `|Δ| ≤ 0.05 Å` **only on a matched ordered-core
selection**, on the grounds that "precision is dominated by the superposition
selection". No second implementation is installed, so a cross-tool benchmark is not
available — but the claim the precondition rests on *is* measurable: sweep the
ordered-core cutoff and see how far the reported precision moves.

`scripts/t17_nmr_ensemble.py` defines the ordered core as residues with per-residue
Cα RMSF ≤ 2.0 Å. This re-uses its own functions, so the sweep measures the harness's
metric rather than a re-implementation of it.

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
# vary, and 2.0 Å is only the harness's pick.
CUTOFFS = [1.0, 1.5, 2.0, 2.5, 3.0, 4.0]


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
        per_cutoff = {}
        for cutoff in CUTOFFS:
            core = [v for v in rmsf if v <= cutoff]
            per_cutoff[str(cutoff)] = {
                "mean_rmsf": round(statistics.fmean(core), 4) if core else None,
                "n_core": len(core),
            }
        means = [v["mean_rmsf"] for v in per_cutoff.values() if v["mean_rmsf"] is not None]
        rows.append({
            "model": model.name,
            "n_residues": len(rmsf),
            "whole_chain_mean_rmsf": round(whole_chain, 4),
            "by_cutoff": per_cutoff,
            "spread_across_cutoffs": round(max(means) - min(means), 4) if means else None,
            "whole_chain_minus_2A_core": round(
                whole_chain - per_cutoff["2.0"]["mean_rmsf"], 4)
            if per_cutoff["2.0"]["mean_rmsf"] is not None else None,
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
