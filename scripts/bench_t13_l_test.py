#!/usr/bin/env python3
"""Benchmark the L-test ⟨|L|⟩ agreement tolerance: phenix.xtriage vs CCP4 ctruncate.

Settles the `L-test ⟨|L|⟩ | ± 0.02, same twin/no-twin call, matched resolution range`
`[template]` tolerance in `ref/thresholds_and_standards.md`.

Both values are produced by the same runs the Wilson-B benchmark already performs, so
this reads the cached logs rather than re-running the programs:

  - `phenix.xtriage` → `<|L|>       : 0.483  (untwinned: 0.500; perfect twin: 0.375)`
  - `ctruncate`      → `L statistic =  0.497  (untwinned 0.5 perfect twin 0.375)`
                       `Data has used to  40.01 -   1.69 A resolution`

The tolerance's stated precondition is a **matched resolution range**, and ctruncate
prints the range it actually used while xtriage prints its own — so for once the
precondition can be *checked* rather than assumed, and the spread reported with and
without a range mismatch.

Both programs implement the same Padilla-Yeates statistic, so agreement here checks
consistent computation, **not** method independence. The scale is also narrow: the
whole physical range is 0.500 (untwinned) to 0.375 (perfect twin), i.e. 0.125, so a
±0.02 tolerance is ~16 % of the full scale and should be read in those terms.

Usage:
    python3 scripts/bench_t13_l_test.py --cache <dir used by bench_t13_wilson_b.py>
"""
from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from pathlib import Path
from typing import Any

_XT_L = re.compile(r"<\|L\|>\s*:\s*([\d.]+)")
_XT_RESO = re.compile(r"Resolution range:\s*([\d.]+)\s+([\d.]+)")
_CT_L = re.compile(r"L statistic\s*=\s*([\d.]+)")
_CT_RANGE = re.compile(r"Data has used to\s+([\d.]+)\s*-\s*([\d.]+)\s*A")

# Padilla & Yeates: untwinned ⟨|L|⟩ ≈ 0.5, perfect twin ≈ 0.375. The midpoint is the
# conventional dividing line for a "possibly twinned" call.
UNTWINNED, PERFECT_TWIN = 0.500, 0.375
TWIN_CALL_CUTOFF = (UNTWINNED + PERFECT_TWIN) / 2


def twin_call(l_value: float) -> str:
    """Twinned / untwinned verdict from ⟨|L|⟩."""
    return "possibly_twinned" if l_value < TWIN_CALL_CUTOFF else "untwinned"


def collect(cache: Path) -> tuple[list[dict], list[dict]]:
    """Read every cached xtriage/ctruncate log pair in `cache`."""
    rows, skipped = [], []
    for xt_log in sorted(cache.glob("xt_*.log")):
        stem = xt_log.name[len("xt_"):-len(".log")]
        ct_log = cache / f"ct_{stem}.log"
        if not ct_log.exists():
            skipped.append({"dataset": stem, "reason": "no matching ctruncate log"})
            continue
        xt_text, ct_text = xt_log.read_text(errors="ignore"), ct_log.read_text(errors="ignore")
        xt_l, ct_l = _XT_L.search(xt_text), _CT_L.search(ct_text)
        if not xt_l or not ct_l:
            skipped.append({"dataset": stem, "reason": "an L-test value was not reported"})
            continue
        xt_value, ct_value = float(xt_l.group(1)), float(ct_l.group(1))

        xt_reso, ct_range = _XT_RESO.search(xt_text), _CT_RANGE.search(ct_text)
        xt_dmin = float(xt_reso.group(2)) if xt_reso else None
        ct_dmin = float(ct_range.group(2)) if ct_range else None
        # ctruncate reports the range it used for the analysis; xtriage reports the
        # range of the data it read. Tri-state on purpose: ctruncate does not always
        # print its range, and recording "unknown" as "mismatched" would silently
        # inflate the headline claim about the precondition.
        if xt_dmin is None or ct_dmin is None:
            range_state = "unknown"
        elif abs(xt_dmin - ct_dmin) < 0.05:
            range_state = "matched"
        else:
            range_state = "mismatched"

        delta = xt_value - ct_value
        rows.append({
            "dataset": stem.upper(),
            "xtriage_L": xt_value,
            "ctruncate_L": ct_value,
            "delta": round(delta, 4),
            "abs_delta": round(abs(delta), 4),
            "xtriage_d_min": xt_dmin,
            "ctruncate_d_min": ct_dmin,
            "resolution_range_state": range_state,
            "xtriage_call": twin_call(xt_value),
            "ctruncate_call": twin_call(ct_value),
            "same_call": twin_call(xt_value) == twin_call(ct_value),
            # As a fraction of the full physical scale (0.500 → 0.375).
            "delta_pct_of_scale": round(100.0 * abs(delta) / (UNTWINNED - PERFECT_TWIN), 1),
        })
        print(f"  {stem.upper():8} xtriage {xt_value:.3f}  ctruncate {ct_value:.3f}  "
              f"Δ {delta:+.4f}  d_min {xt_dmin}/{ct_dmin}  "
              f"range {range_state}", file=sys.stderr)
    return rows, skipped


def summarize(rows: list[dict]) -> dict[str, Any]:
    """|Δ| distribution overall and split on whether the resolution ranges matched."""
    if not rows:
        return {"n": 0}

    def stats(subset: list[dict]) -> dict[str, Any]:
        if not subset:
            return {"n": 0}
        ordered = sorted(r["abs_delta"] for r in subset)
        idx = min(len(ordered) - 1, max(0, round(0.9 * (len(ordered) - 1))))
        return {
            "n": len(subset),
            "signed_median": round(statistics.median(r["delta"] for r in subset), 4),
            "abs_median": round(statistics.median(ordered), 4),
            "abs_p90": round(ordered[idx], 4),
            "abs_max": round(ordered[-1], 4),
        }

    by_state = {s: [r for r in rows if r["resolution_range_state"] == s]
                for s in ("matched", "mismatched", "unknown")}
    return {
        "overall": stats(rows),
        "matched_resolution_range": stats(by_state["matched"]),
        "mismatched_resolution_range": stats(by_state["mismatched"]),
        "unknown_resolution_range": stats(by_state["unknown"]),
        "same_twin_call": sum(1 for r in rows if r["same_call"]),
        "n_possibly_twinned_either": sum(1 for r in rows if "possibly_twinned"
                                         in (r["xtriage_call"], r["ctruncate_call"])),
        "max_delta_pct_of_scale": max(r["delta_pct_of_scale"] for r in rows),
    }


# INCOMPLETE: 5 of the 27 datasets, committed in round 18 as the most recoverable.
#
# This script has no id argument at all -- it reads whatever `xt_*.log` / `ct_*.log`
# pairs a prior `bench_t13_wilson_b.py` run left in `--cache`. So its set was never
# expressible, let alone recorded, and the trail tables only the 5 worst cases. The
# other 22 are named nowhere.
#
# The set is NOT Wilson B's 24, even though the same two tools produce both rows: this
# benchmark reports n = 27. At least three datasets are therefore unique to it and
# cannot be identified even by cross-referencing the sibling benchmark.
#
# What IS reproducible: the twin/no-twin call agreed 27/27, and that is the load-bearing
# half of the tolerance. What is not: the median |Δ| 0.006 and the max 0.047.
PUBLISHED_N = 27
KNOWN_IDS = ["9PLC", "30IZ", "9RWI", "12LO", "9LLR"]
SET_IS_COMPLETE = False
SET_SHORTFALL = "5 of 27 named -- only the worst cases were tabulated"
# This script takes no ids: it parses whatever xt_*/ct_* logs a prior Wilson B run
# left in --cache, so KNOWN_IDS is a record of what was named, not a runnable default.
SET_NOT_RUNNABLE = "no id argument exists; the set is whatever the cache holds"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cache", required=True,
                    help="directory holding xt_*.log / ct_*.log from bench_t13_wilson_b.py")
    ap.add_argument("--json", dest="json_out")
    args = ap.parse_args()

    rows, skipped = collect(Path(args.cache))
    if len(rows) != PUBLISHED_N:
        print(f"WARNING: {len(rows)} datasets in this cache; the published tolerance "
              f"used {PUBLISHED_N}. The set is unrecoverable ({SET_SHORTFALL}), so this "
              f"run is a new measurement, not a reproduction.", file=sys.stderr)
    summary = summarize(rows)
    if args.json_out:
        Path(args.json_out).write_text(
            json.dumps({"rows": rows, "skipped": skipped, "summary": summary}, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    return 0 if rows else 1


if __name__ == "__main__":
    raise SystemExit(main())
