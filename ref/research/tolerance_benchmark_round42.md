# Tolerance benchmark — round 42: the §4 X-ray band widths re-based on coverage, resolving the most expensive partial record (#269)

**One tolerance value changes: the §4 `d_min ≥ 2.5 Å` Cα-shift band, 0.35 → 0.25 Å.** The favored band
is kept at −6 pp. Both X-ray band *widths* stop resting on a lost maximum and are now **distribution-based
coverage bounds over the 44 fresh named entries** (rounds 37/38/41), which resolves the §4 ΔRMSD row's
`⚠ partial record` mark — "the most expensive instance in the file."

The change is approved and pre-registered: the target (99 %/95 % upper tolerance limit) and method were
registered in [`tolerance_benchmark_round42_preregistration.md`](tolerance_benchmark_round42_preregistration.md)
before the value was computed; the figures are re-derivable by
[`scripts/analyze_xray_band_coverage.py`](../../scripts/analyze_xray_band_coverage.py) from the committed
`round{37,38,41}_xray_deltas.json`.

## Why the basis changed

The deep-research pass that closed #225 (adversarially verified against JCGM/GUM, MolProbity, wwPDB/EMDB
and National-Academies primary sources) established that a band sized on **one observed maximum** is
unsound regardless of whether that maximum is recoverable:

- the sample maximum is a **downward-biased** (E[X₍ₙ₎] < true max), **least-robust** (breakdown point 0),
  **low-confidence** estimator that **rises with more data** — at n = 44 it is only 89.5 % confident of
  covering 95 % of the population;
- structural-biology validation **never** sizes tolerances this way — MolProbity Ramachandran outliers are
  a 0.05 % (3.5σ) percentile contour over ~100 k curated residues, wwPDB ranks by archive percentile, and
  geometry is judged by normalized Z-scores.

So the lost 0.285 Å / 5.26 pp maxima are retired as **the wrong target**, not mourned as lost data.

## What was computed

| quantity | shape | method | result |
|---|---|---|---|
| Cα-shift RMSD | right-skewed; **log is normal** (Shapiro W=0.960, p=0.129; raw p=0.037) | lognormal one-sided UTL | **99/95 UTL = 0.2514 Å → band 0.25 Å** |
| favored drop | left-skewed by large gains; no clean fit | nonparametric coverage | **−6 pp covers 43/44 (97.7 %)**; kept |

**Predictions (from the pre-registration):**

| prediction | verdict |
|---|---|
| **P1** — the recomputed Cα band flags 0 of the 44 fresh entries | **confirmed** — 0 of 44 (max is 0.2004 Å) |
| **P2** — the recomputed Cα band is below the retired +0.35 Å | **confirmed** — 0.25 < 0.35 (the old band sat 1.75× above the fresh max) |
| favored re-justified, not re-valued | done — kept at −6 pp (round 39), stated as ~98 % coverage |

## Why 0.25 Å is better, not just different

The old 0.35 Å band flagged **0 of 44** null re-refinements — and so does 0.25 Å — but 0.35 sat 1.75× above
the fresh maximum, i.e. it would miss a genuine degradation at 0.28–0.34 Å that a null refinement never
produces. Tightening to the 99/95 coverage bound keeps zero false positives while restoring detection power
in that band, which is the registry's own stated criterion (*"headroom against breaching is not the
criterion — detection power is"*). The Cα detection floor accordingly improves from ~0.35 to ~0.25 Å.

## The partial-record accounting (checked, not assumed)

The §4 preamble count moves **13 → 14 fully backed, 7 → 6 marked**. Only the **ΔRMSD row** fully resolves.
The **geometry row keeps its `⚠ partial record` mark**, because its *clashscore* figures — the 4.26× null
ratio and the 17.2 starting clashscore — still come from the same lost ~11 entries; round 42 resolved that
row's *favored* sub-figure only. Resolving one sub-figure is not resolving the row, and treating it as such
would have been exactly the miscount this repo guards against.

## Scope and limits

- **One value moved** (Cα 0.35 → 0.25). The `d_min < 2.5 Å` bands, the favored value, and every EM/non-X-ray
  row are untouched.
- **The lognormal fit is load-bearing** — n = 44 cannot support a purely nonparametric 99/95 bound (that
  needs ~300), so the band rests on `log(Cα)` passing Shapiro (p = 0.129), stated openly.
- **Coverage, not a maximum**: ~1 % of null re-refinements may exceed the band by design; that is the point,
  matching MolProbity's percentile philosophy.
- **Same-binary, unrestrained**, as the bands are quoted for.
- The **refuted German-tank inflation formula** was not used (it is exact only for the uniform-urn model).
