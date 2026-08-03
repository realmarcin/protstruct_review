#!/usr/bin/env python3
"""Test candidate predictors of the CC_mask degradation *rate* (round 17).

Round 16 left an unexplained observation: round 15 (3.00-3.90 A) degraded CC_mask in
4 of 8 entries, round 16 (3.00-4.11 A, coarser) in 1 of 9. Resolution sets the
magnitude envelope (Spearman rho = +0.397, n = 44) but appeared not to set the rate.

This script tests the predictions registered in
`ref/research/tolerance_benchmark_round17.md` *before* it was written, in the commit
that introduced that file with no results in it. It needs no new refinements: every
input is a column of `ref/research/data/em_refinement_deltas.tsv`.

  P0  the round-15 vs round-16 rate difference is real       Fisher exact, p < 0.05
  P1  degraders start from a higher CC_mask than improvers   Mann-Whitney, one-sided
  P2  cc_mask_delta correlates negatively with cc_mask_pre   Spearman rho < 0
  P3  round 15's mean cc_mask_pre exceeds round 16's         means
  P4  resolution does NOT separate degraders from improvers  Mann-Whitney, two-sided

Usage:
    python3 scripts/analyze_em_deltas.py
    python3 scripts/analyze_em_deltas.py --tsv path/to.tsv --json out.json
"""
from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path
from typing import Any

from scipy import stats

TSV = "ref/research/data/em_refinement_deltas.tsv"
ALPHA = 0.05


def load(path: Path) -> list[dict[str, Any]]:
    """Rows with a recorded pre/post CC_mask pair.

    `delta-only` rows carry a Delta but no pre value, so they cannot serve a
    hypothesis about the *starting* CC_mask -- that is the round-13 record loss acting
    on an analysis rather than on a count, and it is why n here is smaller than the 44
    entries the magnitude correlation could use.
    """
    lines = path.read_text().splitlines()
    header = lines[0].split("\t")
    rows = []
    for line in lines[1:]:
        if not line.strip():
            continue
        row = dict(zip(header, line.split("\t")))
        if not (row.get("cc_mask_pre") and row.get("cc_mask_post")):
            continue
        rows.append({
            "pdb_id": row["pdb_id"],
            "round": row["round"],
            "resolution": float(row["resolution"]),
            "cc_mask_pre": float(row["cc_mask_pre"]),
            "cc_mask_delta": float(row["cc_mask_delta"]),
        })
    return rows


def spearman_critical(n: int) -> float:
    """Two-sided 5 % critical |rho| for Spearman's rho at sample size n.

    Uses the t approximation the repo has quoted since round 12 (rho ~= 0.30 at
    n = 44), rather than a table lookup, so it stays defined at any n.
    """
    if n < 4:
        return 1.0
    t = stats.t.ppf(1 - ALPHA / 2, n - 2)
    return float((t ** 2 / (t ** 2 + n - 2)) ** 0.5)


def analyze(rows: list[dict[str, Any]]) -> dict[str, Any]:
    degraders = [r for r in rows if r["cc_mask_delta"] < 0]
    improvers = [r for r in rows if r["cc_mask_delta"] >= 0]

    r15 = [r for r in rows if r["round"] == "15"]
    r16 = [r for r in rows if r["round"] == "16"]
    r15_deg = sum(1 for r in r15 if r["cc_mask_delta"] < 0)
    r16_deg = sum(1 for r in r16 if r["cc_mask_delta"] < 0)

    # P0 -- is there a rate difference to explain at all?
    table = [[r15_deg, len(r15) - r15_deg], [r16_deg, len(r16) - r16_deg]]
    p0_odds, p0_p = stats.fisher_exact(table, alternative="two-sided")

    # P1 -- do degraders start higher? One-sided: the hypothesis has a direction.
    p1 = stats.mannwhitneyu([r["cc_mask_pre"] for r in degraders],
                            [r["cc_mask_pre"] for r in improvers],
                            alternative="greater")

    # P2 -- does the starting value predict the signed magnitude?
    rho, rho_p = stats.spearmanr([r["cc_mask_pre"] for r in rows],
                                 [r["cc_mask_delta"] for r in rows])
    crit = spearman_critical(len(rows))

    # P4 -- the control. Two-sided: a difference in EITHER direction refutes it.
    p4 = stats.mannwhitneyu([r["resolution"] for r in degraders],
                            [r["resolution"] for r in improvers],
                            alternative="two-sided")

    mean = lambda xs, k: round(statistics.mean([x[k] for x in xs]), 4) if xs else None
    return {
        "n": len(rows), "n_degraders": len(degraders), "n_improvers": len(improvers),
        "P0_rate_difference_real": {
            "round15": f"{r15_deg}/{len(r15)}", "round16": f"{r16_deg}/{len(r16)}",
            "fisher_p": round(float(p0_p), 4), "odds_ratio": round(float(p0_odds), 3),
            "holds": bool(p0_p < ALPHA),
        },
        "P1_degraders_start_higher": {
            "mean_pre_degraders": mean(degraders, "cc_mask_pre"),
            "mean_pre_improvers": mean(improvers, "cc_mask_pre"),
            "median_pre_degraders": round(statistics.median(
                [r["cc_mask_pre"] for r in degraders]), 4) if degraders else None,
            "median_pre_improvers": round(statistics.median(
                [r["cc_mask_pre"] for r in improvers]), 4) if improvers else None,
            "mannwhitney_p": round(float(p1.pvalue), 4),
            "holds": bool(p1.pvalue < ALPHA),
        },
        "P2_delta_vs_pre": {
            "spearman_rho": round(float(rho), 4), "p": round(float(rho_p), 4),
            "critical_rho_5pct": round(crit, 4),
            "holds": bool(rho < 0 and abs(rho) > crit),
        },
        "P3_round15_starts_higher": {
            "mean_pre_round15": mean(r15, "cc_mask_pre"),
            "mean_pre_round16": mean(r16, "cc_mask_pre"),
            "holds": bool(r15 and r16 and mean(r15, "cc_mask_pre") > mean(r16, "cc_mask_pre")),
        },
        "P4_resolution_does_not_set_rate": {
            "median_res_degraders": round(statistics.median(
                [r["resolution"] for r in degraders]), 3) if degraders else None,
            "median_res_improvers": round(statistics.median(
                [r["resolution"] for r in improvers]), 3) if improvers else None,
            "mannwhitney_p": round(float(p4.pvalue), 4),
            "holds": bool(p4.pvalue >= ALPHA),
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tsv", default=TSV)
    ap.add_argument("--json", dest="json_out")
    args = ap.parse_args()

    rows = load(Path(args.tsv))
    result = analyze(rows)
    result["entries"] = [
        {"pdb_id": r["pdb_id"], "round": r["round"], "resolution": r["resolution"],
         "cc_mask_pre": r["cc_mask_pre"], "cc_mask_delta": r["cc_mask_delta"]}
        for r in sorted(rows, key=lambda r: r["cc_mask_pre"])]
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
