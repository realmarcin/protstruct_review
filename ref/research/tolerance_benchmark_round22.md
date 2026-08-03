# Tolerance benchmark — round 22: is 10BU explicable, and can a partial row be made regenerable?

Three standing risks were left after round 21, none of them an open task:

1. **Seven rows carry `⚠ partial record`** — each quotes a figure from a set that cannot be rebuilt.
2. **The §4 X-ray band widths rest on ~11 entries named nowhere.** Round 20 established these are
   unrecoverable; only a fresh low-resolution measurement could give those bands a checkable basis.
3. **`d_FSC_model` rests on one verified extreme** — 10BU at +4.786 %, **3.24×** above anything else
   on record and 30.6× the median.

This round takes (3) and (1). Risk (2) needs a new low-resolution X-ray refinement set and is left
alone rather than half-done.

## Item 1 — is 10BU explicable, or just extreme?

The band is `post ≤ pre × 1.05` and exists entirely for 10BU. Round 17 proved it reproduces
byte-identically, so it cannot be dismissed. Rounds 16 and 19 both hunted for a second large
degradation in the low-resolution regime and found none — worst +1.476 % and +0.277 %.

So the open question is not "is it real" but **"is it explicable"**. If some property of 10BU predicts
its excursion, the band could eventually be conditioned on that property rather than on one entry.

**Hypothesis: the crossing was poorly determined to begin with.** `d_FSC_model` is the resolution at
which the model–map FSC falls below 0.143 and stays there. When that crossing sits far beyond the
map's own stated resolution, the curve is flat and noisy where it is being read, so **a small change
in the model moves the reported crossing a long way.** 10BU's pre-refinement crossing is 4.35 Å for a
**3.20 Å** map.

### Disclosure of what I had already seen

I know 10BU's own numbers — pre 4.3513 Å at 3.20 Å, ratio **1.36** — because they appear throughout
rounds 17–21. What I have **not** computed is that ratio for any other entry, nor any correlation.
The predictions below are about the *other* 35 measurements, and P1 is stated as a rank rather than a
value precisely because 10BU's value was already in front of me.

### Registered scope limit: the arithmetic runs against the hypothesis

Round 17's P2 held as registered and was still wrong, because the predictor shared a term with the
outcome. The same check applies here, and this time it cuts the *helpful* way:

`d_fsc_model_delta_pct = (post − pre) / pre × 100`, and the proposed predictor is `pre / resolution`.
Both contain `pre`. A larger `pre` **inflates the denominator of the outcome**, which biases the
correlation **negative**. So a *positive* correlation would be found against the arithmetic bias, not
because of it — which is the opposite of round 17's situation and makes a positive result stronger
rather than weaker. Recorded before running it.

### Predictions

| # | Prediction | Falsified if | P |
|---|---|---|---|
| **P0** | **Gate:** 10BU is a statistical outlier among the degradation magnitudes — above Q3 + 1.5 × IQR. | It sits inside that fence, i.e. there is no anomaly to explain. | 85 % |
| **P1** | 10BU has the **highest** `d_fsc_model_pre / resolution` ratio of all entries with both values. | Any entry ranks above it. | 55 % |
| **P2** | \|`d_fsc_model_delta_pct`\| correlates **positively** with `d_fsc_model_pre / resolution` (Spearman, p < 0.05). | ρ ≤ 0, or p ≥ 0.05. | 45 % |
| **P3** | P2 survives **removing 10BU** — the relationship is not one point. | ρ ≤ 0 or p ≥ 0.05 without 10BU. | 30 % |

**P2 and P3 are the informative ones and I do not expect P3 to hold.** Three mechanism hunts in this
series have failed (rounds 7, 15, 17), and the honest prior is that this is a fourth. P3 is registered
separately from P2 precisely so that "the correlation exists but is carried by 10BU alone" is recorded
as a *failure* rather than written up as support.

**If P0 fails there is nothing to explain** and P1–P3 become decoration, exactly as round 17's P0
made P1–P3 decoration.

### Results

`scripts/analyze_dfsc_outlier.py`, over the 36 entries carrying both a `d_FSC_model` pre value and a
delta.

| # | Prediction | Outcome |
|---|---|---|
| **P0** | 10BU is a statistical outlier | ✅ **on 8 degradations**, and under **every** quartile convention — fence 3.017 (exclusive), 2.370 (hinges), 1.724 (inclusive), against 4.786 %. Assumption-free: **3.24× the next value** |
| **P1** | 10BU has the highest pre/resolution ratio | ❌ **falsified — it is 2nd** |
| **P2** | ratio predicts \|excursion\| | ✅ ρ = **+0.346**, p = 0.039 |
| **P3** | P2 survives removing 10BU | ❌ **falsified** — ρ = +0.288, p = 0.094 |

**P3 failing is the honest headline: this is the fourth mechanism hunt in the series and it does not
establish its mechanism either.** It was registered at 30 % for exactly that reason.

But the shape of the failure is more interesting than the previous three.

### The entry above 10BU is the largest excursion in the set — in the opposite direction

| rank | entry | d_min | pre | **pre / resolution** | Δ |
|---:|---|---:|---:|---:|---:|
| 1 | **9H7U** | 2.96 Å | 4.060 | **1.372** | **−36.150 %** |
| 2 | **10BU** | 3.20 Å | 4.351 | **1.360** | **+4.786 %** |
| 3 | 10EU | 3.00 Å | 3.229 | 1.076 | −1.084 % |
| 4 | 10ET | 3.00 Å | 3.180 | 1.060 | −0.779 % |

P1 was falsified by **9H7U**, whose crossing sits 1.372× its map resolution — and which is the
**largest single excursion ever recorded in this benchmark**, a 36 % *improvement*. So the two entries
whose crossing sits furthest beyond their map's stated resolution are the two largest movements in the
set, one up and one down.

The ratio distribution has a clean gap there: **1.372, 1.360, then 1.076.** The step from rank 2 to
rank 3 is **0.284**; from rank 1 to rank 2 it is **0.012**.

| ratio | n | median \|Δ\| |
|---|---:|---:|
| > 1.3 | **2** | **20.468 %** |
| ≤ 1.3 | 34 | **0.112 %** |

A ~180× difference in median excursion. A rank test here is **near-tautological** — the high group
*is* the two largest |Δ| in the set, chosen after seeing the gap — so the descriptive contrast is the
honest output. For completeness: Mann–Whitney **p = 0.010 one-sided, 0.020 two-sided**.

### Why that is a hypothesis and not a finding

**n = 2.** Round 8's rule applies directly and by name: *a mechanism inferred from two data points is a
hypothesis.* Everything above rests on 9H7U and 10BU, and:

- The correlation fails on removing **either** of them (both leave ρ = +0.288, p = 0.094), and drops
  to ρ = +0.222, p = 0.206 without both.
- The 1.3 split was chosen **after seeing the gap**, so the Mann–Whitney p is post-hoc on n = 2 vs 34.
- 10ME, the 4th-largest excursion at 1.476 %, ranks **29th of 36** on the ratio — a direct
  counterexample.

So the registered verdict is: **P2 holds against the arithmetic bias, P3 fails, and the mechanism is
not established.** What has changed is that "10BU is unexplained" becomes "here is a specific,
pre-specifiable test that would settle it".

### The successor test, specified now

A future round can settle this cheaply, because the prediction is sharp and the sampling is targeted:

> **Fetch EM entries whose deposited `d_FSC_model` crossing exceeds ~1.3× their map resolution** —
> measurable from `mtriage` before any refinement — and refine them. If the hypothesis holds, their
> \|Δ\| should be one to two orders of magnitude above the ≤ 1.3 population's median of 0.112 %.
> **Register that before fetching**, and note that the screen is a *pre*-refinement quantity, so the
> set can be selected on it without circularity.

If it holds on a targeted set, the `d_FSC_model` Δ becomes conditionable on a measurable property
instead of resting on one entry. If it fails, 10BU stays what it is: real, reproducible and singular.

### Applied

> **No band changed.** The `d_FSC_model` row gains a **caveat**, not a gate: when the pre-refinement
> crossing sits far beyond the map's own resolution the curve is flat where it is read, and the two
> such entries on record are the two largest excursions in the set. **n = 2 — this is a hypothesis.**

## Self-review findings, filed as issues

Reviewing this PR's own diff found four defects
([#100](https://github.com/realmarcin/protstruct_review/issues/100)–[#103](https://github.com/realmarcin/protstruct_review/issues/103)),
all fixed here. The first is a repeat of a defect this series fixed five rounds ago.

- **#101 (high)** — the published ρ/p figures were **not what the cited script outputs**. They were
  recomputed from the JSON's `entries` array, which this script rounds to 4 dp for readability; three
  ratios that are distinct at full precision (0.984281, 0.984253, 0.984304) **tie at 0.9843** and
  shift the rank correlation. Published 0.343/0.041 and 0.284/0.098; the script gives **0.346/0.039**
  and **0.288/0.094**.

  **This is round 17's backfill artefact, repeated.** That round found `d_FSC_model`'s headline
  +4.787 % was a ratio recomputed from 4-dp-rounded values, corrected it to +4.786 %, and wrote the
  lesson down. Round 22 then did the same thing to a rank correlation. Verdicts are unaffected, but
  in a repo whose premise is that every figure is re-derivable from a committed script, **a published
  number the script does not produce is the defect**, whatever its size. Every robustness check is
  now computed *inside* `analyze_dfsc_outlier.py`, so one artefact produces every quoted figure.

- **#100 / #103 (medium)** — P0's Tukey fence was quoted as a single number without saying it rests
  on **8 values**, and without noting it is **method-dependent**: 3.017 (exclusive), 2.370 (hinges),
  1.724 (inclusive). The conclusion survives all three — and the assumption-free statement, **3.24×
  the next-largest degradation**, carries it without any convention at all. That now leads instead.
  The registry's caveat and the backlog bullet were also stating the n = 2 hypothesis more flatly
  than the analysis supports.

- **#102 (low-medium)** — the Mann–Whitney p was one-sided and unlabelled, and is near-tautological
  anyway: the high group *is* the two largest |Δ|, selected after seeing the gap. Both sidednesses
  are now reported with the caveat attached.

**The pattern across rounds 20, 21 and 22 is consistent and worth naming**: the arithmetic keeps
being right while the *presentation* claims more than the arithmetic does — a version upgrade that
never happened, an independent replication that was a subset re-run, a fence stated as though one
convention were canonical. Round 22 adds a fourth variant: a figure quoted from the wrong precision
of the right computation.

## Item 2 — make a partial row regenerable

Round 21 showed the route: a row whose set cannot be rebuilt can still be given figures **anyone can
regenerate**, by re-running on the committed subset. It also showed the ceiling — when the new set
overlaps the lost one, that is reproducibility, not corroboration, and the `⚠` mark stays.

Both candidates carry a committed partial set already:

| row | committed set | missing |
|---|---:|---|
| H-placement / flip sets | 12 of 17 | the 5 models with **zero** disagreements |
| Ramachandran favored % + outlier % | 11 of 17 | 6 entries, unnamed |

The flip-set row is the better target: its shortfall is **structured** rather than arbitrary. The five
missing models are exactly the ones that showed *no* disagreement, so the published aggregate
(48 disagreements over 639 residues, 7.5 %) has a known numerator and an unknown denominator — the
same shape as the L-test, and the same reason it might be recoverable in substance even if not in
membership.

### The trick does not transfer, and the reason is worth recording

**Round 21's route does not apply to the flip-set row — and running it anyway would produce a number
that looks like it contradicts the published one.**

The published figure is **7.5 %**, being **48 disagreements over 639 flippable residues across 17
models**. The five missing models are precisely those with **zero** disagreements. So they contribute
**nothing to the numerator and everything they have to the denominator**.

A re-run on the committed 12 would therefore reproduce all 48 disagreements over **fewer than 639**
residues, and report a **higher** rate than 7.5 % — not because anything disagreed, but because the
denominator shrank. Anyone comparing the two would see a discrepancy that is purely an artefact of
which models survived the record.

That is the difference from the L-test, where the missing datasets were unremarkable
middle-of-distribution ones and the surviving subset reproduced the aggregate closely. **Whether a
subset re-run helps depends on *which* members were lost**, not on how many:

| row | what was lost | subset re-run gives |
|---|---|---|
| L-test | ~3 unremarkable datasets | the same figures — reproducibility |
| flip sets | the 5 **zero-disagreement** models | a **higher, incomparable** rate |

So the flip-set row keeps its `⚠ partial record` mark and does **not** get a re-run. That is a
result, not a deferral: the row's 7.5 % is unrecoverable *in principle* from the committed set,
because the lost models are the denominator.
