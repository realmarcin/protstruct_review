# Tolerance benchmark — Wilson B (phenix.xtriage ML vs CCP4 ctruncate)

De-provisionalizes `Wilson B` in `ref/thresholds_and_standards.md` and the `T13_wilson_b` entry in
`ref/structural_criteria.yaml` (GitHub #19). The previous `± 5 Å²` was inference-only: no primary
source on inter-program Wilson-B reproducibility survived the earlier review. This is the
measurement.

Reproduce with:

```bash
python3 scripts/bench_t13_wilson_b.py --ids-file <ids.json> --cache <dir> --json <out.json>
```

## Configuration

Both programs read the **same MTZ**, converted once from the deposited structure-factor cif
(`cif2mtz`), and are pointed at the **same intensity columns** (`obs_labels` / `-colin`), so the
estimator is the only difference:

| | phenix.xtriage | ctruncate |
|---|---|---|
| Estimator | maximum-likelihood isotropic Wilson scaling, anisotropy-aware | classic Wilson-plot slope, BEST-reference corrected |
| Reported as | "ML estimate of overall B value" | "Estimate of Wilson B factor" |
| Fit range | program default | program default (**not** matched — see scope limits) |

Datasets: 24 X-ray entries drawn from RCSB stratified into six resolution bins (0.5–1.2, 1.2–1.6,
1.6–2.0, 2.0–2.5, 2.5–3.0, 3.0–3.8 Å), newest-first within each bin, then filtered to those that
deposited **merged intensities**. That filter is not incidental: of the first 24 candidates drawn,
11 had deposited amplitudes only, and a Wilson B derived from F is not the same measurement.
Anisotropy is not pre-labelled — it is read off xtriage's B_cart eigenvalues (ΔB_cart = max − min)
and used to stratify after the fact.

## Results

| Entry | d_min (Å) | ΔB_cart (Å²) | xtriage ML (Å²) | ctruncate (Å²) | Δ (Å²) | Δ (%) |
|---|---:|---:|---:|---:|---:|---:|
| 9PLB | 0.88 | 4.0 | 5.33 | 3.98 | +1.35 | +28.9 |
| 9ZHM | 1.07 | 4.8 | 9.34 | 8.01 | +1.33 | +15.4 |
| 9PM1 | 1.08 | 6.8 | 9.56 | 9.29 | +0.27 | +2.9 |
| 9HW2 | 1.15 | 6.1 | 15.60 | 14.57 | +1.03 | +6.8 |
| 9PNX | 1.35 | 9.1 | 17.04 | 14.74 | +2.30 | +14.4 |
| 12LO | 1.37 | 5.6 | 12.67 | 10.47 | +2.20 | +19.0 |
| 9LLR | 1.45 | 14.5 | 12.87 | 11.17 | +1.70 | +14.2 |
| 9PLC | 1.54 | 6.8 | 27.13 | 34.68 | −7.55 | −24.4 |
| 37AP | 1.82 | 5.3 | 24.99 | 22.97 | +2.02 | +8.4 |
| 37AS | 1.91 | 12.9 | 32.41 | 33.13 | −0.72 | −2.2 |
| 37BG | 1.93 | 19.3 | 21.15 | 18.54 | +2.61 | +13.2 |
| 32CR | 1.98 | 9.5 | 26.00 | 29.61 | −3.61 | −13.0 |
| 30IZ | 2.02 | 2.8 | 17.59 | 16.97 | +0.62 | +3.6 |
| 28JJ | 2.10 | 2.4 | 21.51 | 27.00 | −5.49 | −22.6 |
| 28SV | 2.21 | 8.7 | 27.14 | 30.77 | −3.63 | −12.6 |
| 28JK | 2.29 | 11.9 | 49.99 | 54.65 | −4.66 | −8.9 |
| 28SZ | 2.52 | 35.5 | 37.67 | 49.41 | −11.74 | −27.0 |
| 28SX | 2.59 | 47.8 | 28.64 | 38.84 | −10.20 | −30.2 |
| 31EG | 2.89 | 55.8 | 70.84 | 59.98 | +10.86 | +16.6 |
| 28SW | 2.92 | 14.1 | 37.95 | 33.89 | +4.06 | +11.3 |
| 9PN7 | 3.02 | 27.5 | 64.00 | 61.19 | +2.81 | +4.5 |
| 9HX9 | 3.07 | 6.8 | 57.95 | 49.71 | +8.24 | +15.3 |
| 9RWI | 3.45 | 42.2 | 130.62 | 109.19 | +21.44 | +17.9 |
| 9PI0 | 3.50 | 30.9 | 90.15 | 81.75 | +8.40 | +9.8 |

Wilson B spans 5.3 → 130.6 Å² over the set.

## Findings

**1. `± 5 Å²` was the wrong *shape*, not merely the wrong number.** Absolute disagreement scales with
the Wilson B itself (Pearson r = **0.81** vs B; 0.70 vs d_min; 0.73 vs ΔB_cart — the three are
mutually correlated). Relative disagreement, by contrast, is **flat across resolution** (r = −0.02
between d_min and |Δ| %):

| Subset | n | median \|Δ\| (Å²) | max \|Δ\| (Å²) | median \|Δ\| (%) | max \|Δ\| (%) |
|---|---:|---:|---:|---:|---:|
| d_min < 1.5 Å | 7 | 1.35 | 2.30 | 14.4 | 28.9 |
| 1.5–2.5 Å | 9 | 3.61 | 7.55 | 12.6 | 24.4 |
| ≥ 2.5 Å | 8 | 9.30 | 21.44 | 16.0 | 30.2 |

So a fixed ±5 Å² is **vacuous at high resolution** — at d_min 0.88 Å the whole Wilson B is 5.3 Å², so
±5 Å² permits a ~100 % error — and **routinely violated at low resolution**: 8 of 24 datasets exceed
it, all but one at d_min ≥ 1.5 Å. An absolute tolerance cannot be right at both ends of a quantity
that ranges over 25×.

**2. The disagreement is large: median 13.7 %, p90 27 %, max 30.2 %.** These estimators are close
cousins measuring the same physical quantity and they still differ by ~1 part in 7 on typical data.
The sign is not fixed (xtriage higher in 16/24, lower in 8/24), so this is genuine method
divergence, not a calibration offset that could be corrected out.

**3. Strong anisotropy breaks the comparison.** Splitting at ΔB_cart = 25 Å²:

| Subset | n | median \|Δ\| (%) | max \|Δ\| (%) |
|---|---:|---:|---:|
| ΔB_cart < 25 Å² | 18 | 13.1 | 28.9 |
| ΔB_cart ≥ 25 Å² | 6 | 17.2 | 30.2 |

Both datasets that break the recommended envelope below (28SX, ΔB_cart 47.8 Å²; 28SZ, 35.5 Å²) come
from this group, and the group's signs are mixed (2 negative, 4 positive). This is expected from the
mechanism: xtriage's ML scaling models anisotropy explicitly, ctruncate's isotropic straight-line
plot averages over it, so the more anisotropic the data the less the two are answering the same
question. Comparing them there is a category error, not a tolerance failure.

## Applied tolerance

> **|Δ| ≤ 25 % of the mean, or 2.5 Å², whichever is larger** — `phenix.xtriage` (ML) vs `ctruncate`
> (classic), on the same reflection file and the same intensity columns. **Void when xtriage reports
> ΔB_cart ≥ 25 Å²** (max − min B_cart eigenvalue): under strong anisotropy the two estimators diverge
> without bound and in either direction.

This envelope covers **18/18** datasets below the anisotropy cutoff, and fails only the two most
anisotropic datasets in the set. The 2.5 Å² floor exists because the percentage term becomes
unreasonably tight when B itself is small (the sub-10 Å² regime at sub-Å resolution).

**Read this tolerance as weak corroboration, not confirmation.** A 25 % band on a quantity that
drives B-factor sanity checks is not a precision agreement — it says only that the two programs are
looking at the same data. Where a precise Wilson B matters, the earlier review's advice stands and is
now quantified: compare **like methods** (ML vs ML, or straight-line vs straight-line), or compare
against the value in the deposition's Table 1, which is the harness tiebreaker.

## Scope limits

- **Fit ranges were not matched.** Each program chose its own resolution range for the Wilson fit;
  ctruncate's log does not state the range it used, so it could not be forced to match xtriage's.
  Some fraction of the 13.7 % median is bin/range choice rather than estimator difference. This is a
  real remaining confound, and it makes the measured spread an **upper bound** on pure estimator
  divergence — which is the right direction for a tolerance, but means the number should not be cited
  as "ML vs straight-line disagree by 14 %" in isolation.
- Merged intensities only. Entries depositing amplitudes are out of scope by construction.
- **Single-block sf-cifs only.** `cif2mtz` converts the first `data_` block, so a multi-block entry
  (several crystals, or native/derivative datasets) would be benchmarked on an arbitrary block and
  its `d_min` might not describe the dataset the entry's stated resolution refers to. The script now
  skips such entries loudly ([#27](https://github.com/realmarcin/protstruct_review/issues/27)).
  Checked retroactively: **none of the 24 datasets above is multi-block**, so the guard did not
  change any published number.
- One version pair: PHENIX 2.0-5936 (xtriage) and CCP4 9.0.015 (ctruncate).
- 24 datasets, sampled newest-first per resolution bin from entries with released experimental data.
  Recent depositions may under-represent older processing pipelines.
- Anisotropy is measured by xtriage itself, so the void condition is evaluated by one of the two
  programs being compared. That is acceptable here (the criterion is data-derived, not
  estimator-derived) but it is not an independent measure.
