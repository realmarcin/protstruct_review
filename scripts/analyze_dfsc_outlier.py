#!/usr/bin/env python3
"""Test whether 10BU's `d_FSC_model` excursion is explicable (round 22).

The §4 `d_FSC_model` band (`post <= pre * 1.05`) exists for one entry: 10BU, at
+4.786 %, which is 3.24x above the next-largest degradation ever recorded. Round 17
showed it reproduces byte-identically, so it cannot be dismissed as an artefact.
Rounds 16 and 19 both hunted for a second large degradation in the low-resolution
regime and found none.

So the question is not whether it is real but whether it is **explicable**.

Hypothesis: the crossing was poorly determined to begin with. `d_FSC_model` is the
resolution beyond which the model-map FSC stays under 0.143. When that crossing sits
far past the map's own stated resolution, the curve is flat where it is being read,
so a small model change moves the reported crossing a long way. 10BU's crossing is
4.35 A for a 3.20 A map.

Predictions registered in `ref/research/tolerance_benchmark_round22.md` BEFORE this
script was written:

  P0  gate: 10BU is an outlier among the degradations (above Q3 + 1.5*IQR)
  P1  10BU has the highest pre/resolution ratio of any entry
  P2  |delta_pct| correlates positively with pre/resolution (Spearman, p < 0.05)
  P3  P2 survives removing 10BU

NOTE the arithmetic runs AGAINST the hypothesis: delta_pct = (post-pre)/pre, and the
predictor is pre/resolution, so a larger `pre` inflates the outcome's denominator and
biases the correlation negative. A positive result is found against that bias, not
because of it -- the opposite of round 17's P2, which held only because of one.

Usage:
    python3 scripts/analyze_dfsc_outlier.py
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
    """Entries carrying both a `d_FSC_model` pre value and a delta."""
    lines = path.read_text().splitlines()
    header = lines[0].split("\t")
    rows = []
    for line in lines[1:]:
        if not line.strip():
            continue
        r = dict(zip(header, line.split("\t")))
        if not (r.get("d_fsc_model_pre") and r.get("d_fsc_model_delta_pct")
                and r.get("resolution")):
            continue
        pre = float(r["d_fsc_model_pre"])
        rows.append({
            "pdb_id": r["pdb_id"],
            "resolution": float(r["resolution"]),
            "d_fsc_pre": pre,
            "delta_pct": float(r["d_fsc_model_delta_pct"]),
            # How far past the map's own resolution the crossing sits. > 1 means the
            # curve is being read beyond where the map claims to carry signal.
            "pre_over_res": pre / float(r["resolution"]),
        })
    return rows


def outlier_fences(values: list[float]) -> dict[str, dict[str, float]]:
    """Upper 1.5 x IQR fence under each common quartile convention.

    There is no single "standard" quartile definition, and on n = 8 the choice
    moves the fence by nearly 2x -- so reporting one number would overstate the
    criterion. All three are returned and the write-up quotes the range (#100,
    #103). `statistics.quantiles` defaults to the exclusive method.
    """
    ordered = sorted(values)
    out = {}
    for name, q in (("exclusive", statistics.quantiles(ordered, n=4, method="exclusive")),
                    ("inclusive", statistics.quantiles(ordered, n=4, method="inclusive"))):
        out[name] = {"q1": q[0], "q3": q[2], "fence": q[2] + 1.5 * (q[2] - q[0])}
    # Tukey's original hinges: median of each half, lower half including the
    # median when n is odd.
    half = len(ordered) // 2
    lo, hi = ordered[:half], ordered[-half:]
    q1, q3 = statistics.median(lo), statistics.median(hi)
    out["hinges"] = {"q1": q1, "q3": q3, "fence": q3 + 1.5 * (q3 - q1)}
    return out


def analyze(rows: list[dict[str, Any]]) -> dict[str, Any]:
    degradations = sorted(r["delta_pct"] for r in rows if r["delta_pct"] > 0)
    fences = outlier_fences(degradations)
    worst = max(rows, key=lambda r: r["delta_pct"])
    # The assumption-free statement: how far clear of the next value it sits.
    ratio_to_next = worst["delta_pct"] / degradations[-2] if len(degradations) > 1 else None

    ranked = sorted(rows, key=lambda r: -r["pre_over_res"])
    rank_10bu = next((i + 1 for i, r in enumerate(ranked) if r["pdb_id"] == "10BU"), None)

    def spearman(subset: list[dict[str, Any]]) -> dict[str, Any]:
        rho, p = stats.spearmanr([r["pre_over_res"] for r in subset],
                                 [abs(r["delta_pct"]) for r in subset])
        return {"n": len(subset), "rho": round(float(rho), 4), "p": round(float(p), 4),
                "holds": bool(rho > 0 and p < ALPHA)}

    without = [r for r in rows if r["pdb_id"] != "10BU"]
    # Every robustness figure the write-up quotes is produced HERE, at full
    # precision. Round 22 first computed these from the rounded `entries` array
    # this script emits for readability, which ties three ratios at 4 dp and
    # shifts the rank correlation -- the round-17 backfill artefact, repeated
    # (#101). One artefact now produces every quoted number.
    top_two = sorted(rows, key=lambda r: -r["pre_over_res"])[:2]
    return {
        "n_entries": len(rows),
        "P0_10bu_is_an_outlier": {
            "n_degradations": len(degradations),
            "worst": worst["pdb_id"], "worst_pct": worst["delta_pct"],
            "fences": {k: {kk: round(vv, 4) for kk, vv in v.items()}
                       for k, v in fences.items()},
            # Reported because it needs no distributional assumption at all, and
            # carries the same conclusion as every fence convention.
            "ratio_to_next_largest": round(ratio_to_next, 3) if ratio_to_next else None,
            "holds_under_all_conventions": bool(
                all(worst["delta_pct"] > v["fence"] for v in fences.values())),
            "holds": bool(worst["delta_pct"] > fences["exclusive"]["fence"]),
        },
        "P1_10bu_has_highest_ratio": {
            "rank": rank_10bu, "of": len(rows),
            "top5": [(r["pdb_id"], round(r["pre_over_res"], 3)) for r in ranked[:5]],
            "holds": rank_10bu == 1,
        },
        "P2_ratio_predicts_excursion": spearman(rows),
        "P3_survives_without_10bu": spearman(without),
        "robustness": {
            "without_9H7U": spearman([r for r in rows if r["pdb_id"] != "9H7U"]),
            "without_top_two": spearman(
                [r for r in rows if r["pdb_id"] not in {t["pdb_id"] for t in top_two}]),
        },
        "high_ratio_split": _split(rows),
    }


def _split(rows: list[dict[str, Any]], cut: float = 1.3) -> dict[str, Any]:
    """|delta| above vs below a pre/resolution cut.

    The cut is POST-HOC -- chosen after seeing the gap at 1.372 / 1.360 / 1.076 --
    and the high group is by construction the two largest |delta| in the set, so a
    rank test here is close to tautological. The descriptive medians are the
    honest output; the p-value is reported with its sidedness stated (#102).
    """
    hi = [abs(r["delta_pct"]) for r in rows if r["pre_over_res"] > cut]
    lo = [abs(r["delta_pct"]) for r in rows if r["pre_over_res"] <= cut]
    u_one = stats.mannwhitneyu(hi, lo, alternative="greater")
    u_two = stats.mannwhitneyu(hi, lo, alternative="two-sided")
    return {
        "cut": cut, "n_above": len(hi), "n_below": len(lo),
        "median_abs_delta_above": round(statistics.median(hi), 4),
        "median_abs_delta_below": round(statistics.median(lo), 4),
        "mannwhitney_p_one_sided": round(float(u_one.pvalue), 4),
        "mannwhitney_p_two_sided": round(float(u_two.pvalue), 4),
        "caveat": "cut is post-hoc; the high group IS the two largest |delta|, "
                  "so this test is near-tautological",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tsv", default=TSV)
    ap.add_argument("--json", dest="json_out")
    args = ap.parse_args()
    rows = load(Path(args.tsv))
    result = analyze(rows)
    result["entries"] = [
        {k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()}
        for r in sorted(rows, key=lambda r: -r["pre_over_res"])]
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "entries"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
