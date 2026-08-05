# Tolerance benchmark — round 37: the lost maxima are not reproduced, on a sample too narrow to conclude from

**No tolerance, band or measurement changed.** No registry figure is touched.

Round 37 set out to give the `d_min ≥ 2.5 Å` band widths a checkable basis by measuring a **fresh,
named, committed** low-resolution set. It produced one: 21 entries selected by query, **10 usable
Cα-shift measurements**, all ids recorded. That is the first named low-resolution X-ray set this work
has ever had.

It also shows why the attempt is harder than it looks: **11 of 21 selected entries produced nothing**,
for three distinct and separately fixable reasons.

## Result

| prediction | verdict |
|---|---|
| **P1** — both bands hold, no breach | **confirmed** |
| **P2** — fresh Cα-shift max below the lost 0.285 Å | **confirmed** — 0.1828 Å |
| **P3** — fresh favored drop below the lost 5.26 pp | **confirmed** — 2.61 pp |
| **P4** — at least one deposited model fails an absolute floor | **confirmed**, emphatically |
| **P5** — no deposited model starts above the unreproducible clashscore 17.2 | **FALSIFIED** — 38.70 |

| quantity | fresh set (n = 10) | the lost figure | band |
|---|---|---|---|
| Cα-shift max | **0.1828 Å** (1ZY2) | 0.285 Å | 0.35 Å |
| Cα-shift median | 0.1237 Å | — | — |
| worst favored drop | **2.61 pp** (12OC) | 5.26 pp | 6 pp |
| max starting clashscore | **38.70** | 17.2 "not reproducible" | — |

## P5 is the one that changes something

The registry says of the lost batch:

> The quoted **starting clashscore 17.2 is not reproducible** — the highest in the recoverable set is
> 13.61, confirming it came from a lost entry and can never be checked.

A fresh sample of ten reaches **38.70**. So 17.2 was **not** an extreme value that only a lost entry
could supply; it is unremarkable for this branch, and the recoverable set's 13.61 ceiling was an
artefact of which entries survived rather than evidence about the population.

That does not recover the lost entry. It removes the *mystery* about it — and it is the only claim in
this area that a fresh set could settle without also settling the band, because clashscore-pre is a
property of deposited models rather than of refinement behaviour.

## P2 and P3 hold, and the pre-registration already said that means little

Both fresh maxima come in well under the lost ones — 0.1828 Å against 0.285 Å, 2.61 pp against
5.26 pp. The registration stated the asymmetry **in advance**:

> A larger sample can only push a maximum up, so **P2/P3 failing at n = 20 is meaningful while P2/P3
> holding is weaker evidence.**

n is 10, not 20, and the sample is not representative (below). So the honest reading is: **a fresh
sample of this size and composition does not reach the lost maxima, and that is consistent both with
the lost figures being extremes and with this sample being too small and too narrow to find their
equal.** The bands are not re-fitted, and nothing about their width changes.

## What the round genuinely delivers

**A named set.** Twenty-one ids, selected by query, verified against the entry record, and committed
with their measurements. `bench_refinement_deltas.py`'s `SET_SHORTFALL` — *"16 of 37 … named
nowhere"* — is not repaired, because these are new entries rather than the lost ones. But the
mechanism that lost them is closed: selection is now a re-runnable query, not a directory someone
populated by hand.

The benchmark also refused to run on an unnamed set. Passing `--cache` without ids fell back to
`DEFAULT_SET` and found zero pairs, exactly as #78 intended. **The guard fired on the round that
needed it.**

## Attrition: 21 selected, 10 usable

| stage | lost | reason |
|---|---:|---|
| fetch | 3 | no amplitudes or no FREE column (12UN, 13OY, 155C) |
| refine | 7 | `phenix.refine` failed — **missing R-free flags** (#242) |
| measure | 1 | nucleic acid, 0 Cα matched (12CI) (#241) |
| **usable** | **10** | |

Three separate defects, all filed:

- **#242 (high)** — the 7 refinement failures report only `phenix.refine failed`. The log says exactly
  what is wrong: the deposited data carry no R-free flags PHENIX will accept. A 39 % failure rate with
  no stated cause is indistinguishable from a broken pipeline. And the obvious fix —
  `r_free_flags.generate=True` — would refine against *newly generated* flags, which is a different
  experiment from the one the other entries got, so it is a choice to register rather than a flag to
  set.
- **#241 (medium)** — no protein filter, so nucleic-acid entries are selected and measure nothing.
- **#243 (medium)** — the ascending sort ties-break by identifier, so the query returned **twenty
  1990s-era ids**. That is not a sample of the branch; it is a sample of early depositions, which are
  also the ones missing R-free flags and most likely to be nucleic acid. The three defects compound.

## Scope limits

- **n = 10, and the sample is biased by deposition era.** Every conclusion above is conditioned on
  that. #243 is the fix, and until it lands a repeat would draw the same twenty entries.
- **The lost entries are still lost.** This measures the branch, not the batch. A fresh maximum
  agreeing with 0.285 Å would have been corroboration; falling short is not refutation.
- **P5's falsification is about clashscore-pre only** — a property of deposited models, not of the
  refinement behaviour the bands govern. It says the 17.2 was ordinary, not that any band is wrong.
- **Nothing is re-fitted.** P1 held; no breach was observed. Had one been, the registration required
  the decision to be registered separately rather than taken here.
- **Seven entries remain unmeasured** and are recoverable at the cost of a registered decision on
  R-free flag generation (#242). That is the cheapest available route to a larger n.
