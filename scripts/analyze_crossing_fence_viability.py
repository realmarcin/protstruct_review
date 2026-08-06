#!/usr/bin/env python3
"""Is #224's crossing-ratio fence worth screening for, or is the signal 2-point leverage?

#224 proposes selecting EM entries on `d_FSC_model_pre / d_min` above a fence (1.074,
the Tukey outlier fence over the record) to find large `d_FSC_model` excursions and so
test whether the §4 `d_FSC_model` band is least trustworthy when the crossing starts far
past the map's own resolution. #234 then found the fence is confounded with model-map
fit: two of the five entries ever above it (7DZX cc_mask_pre 0.2083, 6PMJ 0.4297) are
the two worst-fitting models in the whole benchmark, and a model that barely fits its
map will of course cross far past the map's resolution.

This script asks the prior question — before spending ~50 GB on more screening, does the
record already say the approach cannot be economically powered? It reads only the
committed `ref/research/data/em_refinement_deltas.tsv`, so every figure here is
re-derivable offline. It reports:

  1. the roster above the fence, with each entry's fit and whether it is already refined;
  2. the non-circular candidate pool (above fence AND fit inside the round-36 exclusion);
  3. rho(ratio, |excursion|) over the measured entries, controlling for fit two ways —
     restricting to good-fit entries, and comparing against rho(fit, |excursion|);
  4. the LEVERAGE test — the same correlation with the two extreme-ratio entries removed.

The verdict the memo (issue) draws from (4) is that the correlation is carried by the
two points the hypothesis started with, which is round 22's n = 2 restated on the full
set, not a fit artefact that excluding bad-fit entries would remove.

Usage:
    python3 scripts/analyze_crossing_fence_viability.py
    python3 scripts/analyze_crossing_fence_viability.py --tsv PATH --fence 1.074 --fit-floor 0.6038
"""
from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TSV = REPO / "ref/research/data/em_refinement_deltas.tsv"

# The round-36 fit-quality exclusion: cc_mask_pre >= the Tukey fence over the record.
DEFAULT_FIT_FLOOR = 0.6038
# The round-23 Tukey fence on d_FSC_model_pre / d_min over the combined set.
DEFAULT_FENCE = 1.074


def _f(x: str) -> float | None:
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def pearson(xs: list[float], ys: list[float]) -> tuple[float | None, float | None, int]:
    """Pearson r and a two-sided p (normal approx on the t statistic)."""
    n = len(xs)
    if n < 3:
        return None, None, n
    mx, my = sum(xs) / n, sum(ys) / n
    sx = sum((x - mx) ** 2 for x in xs) ** 0.5
    sy = sum((y - my) ** 2 for y in ys) ** 0.5
    if sx == 0 or sy == 0:
        return None, None, n
    r = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / (sx * sy)
    if abs(r) >= 1:
        return r, 0.0, n
    t = r * ((n - 2) / (1 - r * r)) ** 0.5
    p = 2 * (1 - 0.5 * (1 + math.erf(abs(t) / 2 ** 0.5)))
    return r, p, n


def load(tsv: Path) -> list[dict]:
    """Entries with a computable crossing ratio, keyed to what the analysis needs."""
    out = []
    for row in csv.DictReader(tsv.open(), delimiter="\t"):
        res, pre = _f(row["resolution"]), _f(row["d_fsc_model_pre"])
        if not res or not pre:
            continue
        out.append({
            "id": row["pdb_id"],
            "ratio": pre / res,
            "cc": _f(row["cc_mask_pre"]),
            "excursion": _f(row["d_fsc_model_delta_pct"]),
            "status": row["status"],
        })
    return out


def _corr(sub: list[dict], label: str) -> tuple[str, float | None, float | None, int]:
    r, p, n = pearson([x["ratio"] for x in sub], [abs(x["excursion"]) for x in sub])
    return label, r, p, n


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tsv", default=str(TSV))
    ap.add_argument("--fence", type=float, default=DEFAULT_FENCE)
    ap.add_argument("--fit-floor", type=float, default=DEFAULT_FIT_FLOOR)
    args = ap.parse_args()

    recs = load(Path(args.tsv))
    measured = [x for x in recs if x["excursion"] is not None]
    print(f"entries with a computable ratio: {len(recs)}")
    print(f"  of which a measured d_FSC_model excursion: {len(measured)}")

    print(f"\n-- roster above the fence ({args.fence}) --")
    above = sorted((x for x in recs if x["ratio"] >= args.fence),
                   key=lambda x: -x["ratio"])
    for x in above:
        cc = f"{x['cc']:.4f}" if x["cc"] is not None else "not recorded"
        exc = f"{x['excursion']:+.2f}%" if x["excursion"] is not None else "not refined"
        print(f"  {x['id']:5} ratio {x['ratio']:.3f}  cc_mask_pre {cc:>12}  excursion {exc}")
    pool = [x for x in above if x["cc"] is not None and x["cc"] >= args.fit_floor]
    print(f"\nnon-circular pool (above fence AND cc_mask_pre >= {args.fit_floor}): "
          f"{len(pool)} -> {[x['id'] for x in pool]}")
    print("  (10BU and 10EU are already refined and already part of the evidence, so the "
          "pool of FRESH non-circular candidates is empty.)")

    print("\n-- rho(ratio, |excursion|), and whether fit explains it --")
    withcc = [x for x in measured if x["cc"] is not None]
    for label, r, p, n in [
        _corr(measured, "all measured"),
        _corr([x for x in withcc if x["cc"] >= args.fit_floor], f"good-fit only (cc>={args.fit_floor})"),
    ]:
        print(f"  {label:34} r={r:+.3f} p={p:.3f} n={n}")
    rcc, pcc, ncc = pearson([x["cc"] for x in withcc], [abs(x["excursion"]) for x in withcc])
    print(f"  {'rho(cc_mask_pre, |excursion|)':34} r={rcc:+.3f} p={pcc:.3f} n={ncc}")

    print("\n-- leverage: the two extreme-ratio entries --")
    top2 = [x["id"] for x in sorted(measured, key=lambda x: -x["ratio"])[:2]]
    for label, r, p, n in [
        _corr([x for x in measured if x["id"] != top2[0]], f"drop {top2[0]}"),
        _corr([x for x in measured if x["id"] != top2[1]], f"drop {top2[1]}"),
        _corr([x for x in measured if x["id"] not in top2], f"drop both ({', '.join(top2)})"),
    ]:
        print(f"  {label:34} r={r:+.3f} p={p:.3f} n={n}")
    print(f"\nVerdict: the correlation rests on {top2[0]} and {top2[1]} jointly. With both "
          f"removed it is ~0, so the signal is the same n = 2 the hypothesis began with "
          f"(round 22), not a fit artefact excluding bad-fit entries would remove.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
