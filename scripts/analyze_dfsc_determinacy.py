#!/usr/bin/env python3
"""Compute round 40's P1/P2/P3 from the committed determinacy measures (#266, #267).

`bench_dfsc_determinacy.py` commits the raw per-entry measures (D_perturb, D_width, the
excursion label) in `round40_dfsc_determinacy.json`. This turns those into the figures
the round document quotes, so every one is re-derivable offline rather than computed by
hand in prose — the gap #257 closed for the viability memo, reopened by round 40 (#267).

  P1  Spearman ρ(D_perturb, |excursion|), all and with the two extremes (9H7U, 10BU)
      removed, plus leave-one-out on the extremes-removed set.
  P2  |excursion| against D_perturb at σ = 0.2, expressed in the same unit (percent of
      the deposited crossing), for the high-ratio entries.
  P3  partial Spearman ρ(D_perturb, |excursion| | cc_mask_pre), via the STANDARD formula
      (ρxy − ρxz·ρyz)/√((1−ρxz²)(1−ρyz²)) — NOT a rank-residual method, which inflated
      this figure to 0.818 when the correct value is 0.773 (#266).

The Spearman implementation is hand-rolled (no scipy dependency, as in
`analyze_crossing_fence_viability.py`) and validated against `scipy.stats.spearmanr` on
this dataset: 0.505 / 0.792 (D_perturb) and 0.319 / 0.049 (ratio) agree exactly.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "ref/research/data/round40_dfsc_determinacy.json"
EXTREMES = ("9H7U", "10BU")


def _rank(xs: list[float]) -> list[float]:
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    r = [0.0] * len(xs)
    i = 0
    while i < len(xs):
        j = i
        while j + 1 < len(xs) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        for k in range(i, j + 1):
            r[order[k]] = (i + j) / 2 + 1
        i = j + 1
    return r


def spearman(xs: list[float], ys: list[float]) -> float:
    rx, ry = _rank(xs), _rank(ys)
    n = len(xs)
    mx, my = sum(rx) / n, sum(ry) / n
    sx = sum((a - mx) ** 2 for a in rx) ** 0.5
    sy = sum((b - my) ** 2 for b in ry) ** 0.5
    return sum((a - mx) * (b - my) for a, b in zip(rx, ry)) / (sx * sy)


def partial_spearman(x: list[float], y: list[float], z: list[float]) -> float:
    """Standard partial correlation on Spearman coefficients."""
    rxy, rxz, ryz = spearman(x, y), spearman(x, z), spearman(y, z)
    return (rxy - rxz * ryz) / math.sqrt((1 - rxz ** 2) * (1 - ryz ** 2))


def load(path: Path) -> list[dict]:
    d = json.loads(path.read_text())
    return [r for r in d["rows"]
            if r.get("d_perturb") is not None and r.get("excursion_pct") is not None]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", default=str(DATA))
    args = ap.parse_args()
    rows = load(Path(args.json))
    ne = [r for r in rows if r["pdb_id"] not in EXTREMES]
    absx = lambda rs: [abs(r["excursion_pct"]) for r in rs]

    print(f"n = {len(rows)} entries with D_perturb and a committed excursion\n")

    print("P1 — Spearman ρ(D_perturb, |excursion|)")
    print(f"  all {len(rows)}: {spearman([r['d_perturb'] for r in rows], absx(rows)):.3f}")
    rp = spearman([r['d_perturb'] for r in ne], absx(ne))
    print(f"  extremes removed ({len(ne)}): {rp:.3f}   [P1 needs >= 0.4]")
    loo = []
    for i in range(len(ne)):
        s = ne[:i] + ne[i + 1:]
        loo.append(spearman([r['d_perturb'] for r in s], absx(s)))
    print(f"  leave-one-out: {min(loo):.3f} – {max(loo):.3f}")

    print("\nContrast — same set, other predictors (extremes removed)")
    print(f"  ratio:   all {spearman([r['ratio'] for r in rows], absx(rows)):+.3f}   "
          f"removed {spearman([r['ratio'] for r in ne], absx(ne)):+.3f}")
    print(f"  D_width: all {spearman([r['d_width'] or 0 for r in rows], absx(rows)):+.3f}   "
          f"removed {spearman([r['d_width'] or 0 for r in ne], absx(ne)):+.3f}")

    print("\nP3 — partial ρ(D_perturb, |excursion| | cc_mask_pre), STANDARD formula")
    wc = [r for r in rows if r.get("cc_mask_pre")]
    p3 = partial_spearman([r['d_perturb'] for r in wc], absx(wc),
                          [r['cc_mask_pre'] for r in wc])
    print(f"  n = {len(wc)} (9H7U excluded, no cc on record): {p3:.3f}   [P3 needs >= 0.3]")
    print(f"  ρ(cc, |excursion|) = {spearman([r['cc_mask_pre'] for r in wc], absx(wc)):+.3f}")

    print("\nP2 — |excursion| vs D_perturb at σ=0.2 (both as % of the crossing), high-ratio")
    for r in sorted(rows, key=lambda r: -r["ratio"])[:5]:
        d02 = r.get("d_perturb_at_0.2")
        d02p = (d02 / r["d_fsc_model_dep"] * 100) if d02 else None
        exc = abs(r["excursion_pct"])
        ratio = (exc / d02p) if d02p else None
        print(f"  {r['pdb_id']:5} |exc| {exc:6.2f}%  D_perturb@0.2 "
              f"{('%.3f%%' % d02p) if d02p is not None else '   0 (quantised)':>10}  "
              f"exc/Dp {('%.0f×' % ratio) if ratio else '—'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
