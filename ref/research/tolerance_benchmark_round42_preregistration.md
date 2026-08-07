# Round 42 — pre-registration

Registered **before the band values are recomputed**, in a commit containing no results. This is
**#269**: re-express the §4 `d_min ≥ 2.5 Å` X-ray band widths as **distribution-based coverage bounds
over the 44 fresh named entries** (rounds 37 + 38 + 41), replacing widths sized just above a single
lost maximum.

## Why

The deep-research pass that closed #225 established (against primary sources) that sizing a band on one
observed maximum is unsound regardless of recoverability: the sample maximum is a **downward-biased**,
**least-robust** (breakdown point 0), **low-confidence** estimator that rises with more data, and
structural-biology validation (MolProbity, wwPDB/EMDB) sizes tolerances on **distribution percentiles**,
not observed maxima. The band widths are therefore re-based on the 44 fresh named entries, which makes
them fully-backed `[benchmark]` figures and **resolves the `⚠ partial record` marks** on the two §4
X-ray band rows (their widths no longer rest on a lost number).

## Method (registered)

**Registered target: a one-sided upper tolerance limit at 99 % coverage / 95 % confidence** — the
structural-biology-aligned target, chosen on the repo's own "detection power, not headroom" criterion,
**before** the band value is computed; the value falls out of the method, it is not chosen.

The distribution **shape was examined first** (the step #269 lists first), and is disclosed here because
it determines the estimator and is a methods choice, not a result:

- **Cα-shift RMSD** is positive and right-skewed; `log(Cα-shift)` passes Shapiro–Wilk normality
  (W = 0.960, p = 0.129) while the raw values do not (p = 0.037). So the Cα band uses a **lognormal**
  one-sided UTL: `exp(mean_log + k·sd_log)`, k the Natrella one-sided factor. Computed by the committed
  `scripts/analyze_xray_band_coverage.py`.
- **Favored drop** has no clean parametric fit (left-skewed by large favored *gains*), so its bound is
  **nonparametric**. Its value is **kept at −6 pp** — round 39 arm 1 already settled it (the breach is an
  unrestrained artefact restraints tame), and this round only re-justifies it as a coverage figure.

## Predictions / decision rule

**The Cα band becomes the computed 99/95 lognormal UTL, rounded to 0.01 Å, whatever it is** — no value
is hand-picked. Registered consequences:

- **P1 — the recomputed Cα band flags 0 of the 44 fresh entries.** A band that flags a null
  re-refinement would be too tight. *Falsified* if any of the 44 exceeds it.
- **P2 — the recomputed Cα band is *below* the retired +0.35 Å** (i.e. the old max-based band was too
  loose). *Falsified* if it lands at or above 0.35.
- **The favored band is re-justified, not re-valued**: report the empirical coverage of the kept −6 pp
  band over the 44 entries (a nonparametric coverage statement), with 6LE5 the single exceedance.

## What this round does and does not do

- **Does:** re-base both §4 X-ray band widths on 44 named entries; change the Cα band value to its
  coverage bound; resolve the two `⚠ partial record` marks and update the registry's backed/partial
  count; add a committed re-runnable script so the widths are re-derivable.
- **Does not:** change the `d_min < 2.5 Å` bands, the favored band *value*, or any EM/§4 non-X-ray row;
  reproduce the lost maxima (retired as the wrong target, #225); apply the refuted German-tank inflation
  formula; move a value without this registered method producing it.

## Scope limits

- **Same-binary.** `phenix-2.0-5936` pinned; a PHENIX upgrade is untested.
- **Unrestrained.** The 44 entries are unrestrained null re-refinements, as the bands are quoted for.
- **n = 44** supports a parametric (lognormal) 99/95 bound for Cα; a purely nonparametric 99/95 bound
  would need ~300 entries, so the lognormal fit is load-bearing and is stated with its Shapiro p.
- **Coverage is 99 %/95 %**, not a maximum: ~1 % of null re-refinements may exceed the band by design,
  which is the point — the band flags the least-probable tail as candidate degradation, as MolProbity
  does with its percentile contours.
