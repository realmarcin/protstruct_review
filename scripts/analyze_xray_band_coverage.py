#!/usr/bin/env python3
"""Re-express the §4 X-ray band widths as coverage bounds over the fresh named set (round 42, #269).

The §4 `d_min >= 2.5 A` X-ray band widths were sized just above a single lost maximum
(Ca-shift +0.35 A above 0.285 A; favored -6 pp above 5.26 pp) whose entries were never
recorded. A deep-research pass (#225) showed an observed maximum is a downward-biased,
least-robust, low-confidence basis for a tolerance band, and that structural-biology
validation (MolProbity, wwPDB) sizes tolerances on distribution percentiles instead. This
script recomputes the band widths as one-sided upper tolerance limits at a registered
coverage/confidence, over the 44 fresh NAMED entries from rounds 37 + 38 + 41 (round 41
pre-registration; #269), so the widths rest on committed data rather than a lost number.

Method, per the round-42 pre-registration:
  - Ca-shift RMSD is positive and right-skewed; log(Ca-shift) passes Shapiro-Wilk normality
    (W=0.960, p=0.129) while raw does not (p=0.037), so a LOGNORMAL one-sided upper
    tolerance limit is used: exp(mean_log + k * sd_log), k = Natrella one-sided factor.
  - favored DROP has no clean parametric fit (left-skewed by large favored *gains*), so its
    bound is NONPARAMETRIC: the empirical coverage of the current -6 pp band is reported and
    the band value is kept (round 39 settled it; the breach is an unrestrained artefact).

Registered target: 99% coverage at 95% confidence (structural-biology-aligned; the repo's
"detection power, not headroom" criterion). No scipy dependency: norm.ppf is Acklam's
rational approximation (|error| < 1.2e-9), validated against scipy on this dataset.

    python3 scripts/analyze_xray_band_coverage.py
"""
from __future__ import annotations

import json
import math
import statistics
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ROUNDS = ("round37", "round38", "round41")
COVERAGE, CONFIDENCE = 0.99, 0.95


def norm_ppf(p: float) -> float:
    """Inverse standard-normal CDF (Acklam's algorithm)."""
    a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
         1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
         6.680131188771972e+01, -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
         -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
         3.754408661907416e+00]
    plow, phigh = 0.02425, 1 - 0.02425
    if p < plow:
        q = math.sqrt(-2 * math.log(p))
        return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / \
               ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    if p <= phigh:
        q = p - 0.5
        r = q * q
        return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q / \
               (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)
    q = math.sqrt(-2 * math.log(1 - p))
    return -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / \
            ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)


def natrella_k(n: int, p: float, conf: float) -> float:
    """One-sided normal tolerance factor (Natrella approximation)."""
    zp, zg = norm_ppf(p), norm_ppf(conf)
    a = 1 - zg**2 / (2 * (n - 1))
    b = zp**2 - zg**2 / n
    return (zp + math.sqrt(zp**2 - a*b)) / a


def pooled(key: str) -> list[float]:
    """Values across the three fresh named X-ray sets, usable protein entries only."""
    out = []
    for rnd in ROUNDS:
        d = json.loads((REPO / f"ref/research/data/{rnd}_xray_deltas.json").read_text())
        out += [r[key] for r in d["rows"]
                if r.get(key) is not None and r.get("ca_shift_rmsd") is not None]
    return out


def main() -> int:
    ca = pooled("ca_shift_rmsd")
    drop = [-x for x in pooled("rama_favored_pct_delta")]  # positive = favored fell
    n = len(ca)
    print(f"pooled fresh named X-ray entries (rounds 37+38+41): n = {n}\n")

    # Ca-shift: lognormal one-sided UTL
    logca = [math.log(x) for x in ca]
    mu, sd = statistics.mean(logca), statistics.stdev(logca)
    k = natrella_k(n, COVERAGE, CONFIDENCE)
    utl = math.exp(mu + k * sd)
    band = round(utl, 2)  # to the nearest 0.01 A (0.2514 -> 0.25)
    print("Ca-shift RMSD (lognormal one-sided upper tolerance limit)")
    print(f"  fresh max {max(ca):.4f}  |  {int(COVERAGE*100)}/{int(CONFIDENCE*100)} UTL "
          f"{utl:.4f} A (k={k:.3f})  ->  band {band:.2f} A")
    print(f"  false positives at band {band:.2f}: {sum(1 for x in ca if x > band)} of {n}")
    print(f"  the retired +0.35 band flagged 0 of {n} and sat {0.35/max(ca):.2f}x above the max")

    # favored drop: nonparametric coverage of the kept -6 band
    dsort = sorted(drop)
    covered = sum(1 for x in drop if x <= 6.0)
    print("\nfavored DROP (nonparametric; band kept at 6 pp per round 39)")
    print(f"  band 6 pp covers {covered}/{n} = {covered/n*100:.1f}% of null re-refinements")
    print(f"  worst drop {max(drop):.2f} pp (6LE5), the single exceedance; p95 "
          f"{dsort[min(n-1, round(0.95*(n-1)))]:.2f}")

    # clashscore: re-base the geometry row's null-ratio figures on named data (round 44).
    # The gate is ratio post/pre >= 5x, valid only while 1 <= pre <= 20; the starting
    # ceiling is what the upper bound guards.
    # Same 44 protein entries as the Ca/favored basis (Ca-matched), not 45 -- 12CI is
    # nucleic acid with a clashscore but null Ca, and mixing it in would make the
    # clashscore denominator differ from round 42's, the same-word-different-count trap.
    pre_post = []
    for rnd in ROUNDS:
        d = json.loads((REPO / f"ref/research/data/{rnd}_xray_deltas.json").read_text())
        for r in d["rows"]:
            pre, post = r.get("clashscore_pre"), r.get("clashscore_post")
            if pre is not None and post is not None and r.get("ca_shift_rmsd") is not None:
                pre_post.append((pre, post))
    gated = [post / pre for pre, post in pre_post if 1 <= pre <= 20]
    starts = [pre for pre, _ in pre_post]
    over5 = [round(x, 2) for x in gated if x >= 5]
    print("\nclashscore null RATIO (round 44; gate is >= 5x while 1 <= pre <= 20)")
    print(f"  max ratio over {len(gated)} gate-valid entries: {max(gated):.3f}x  "
          f"(>= 5x: {over5 or 'none'}; was 4.26x on the lost 19)")
    print(f"  starting clashscore ceiling: {max(starts):.2f} over {len(starts)} entries, "
          f"{sum(1 for s in starts if s > 20)} above pre = 20  (was 17.2 on the lost set)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
