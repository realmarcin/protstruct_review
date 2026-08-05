# Tolerance benchmark — round 35: the first screened candidate, and the confound it exposed

**No tolerance, band or measurement changed.** No registry figure is touched.

Round 34 diagnosed the screen's real ceiling as the **query**, not the download budget. Round 35 acted
on that: `--per-stratum 20` in place of 6, offering **160 candidates** against 48. It worked exactly
as predicted — **50 entries fetched from 81 considered**, where round 34 got 14 from 26.

The screen then produced something rounds 23 and 34 never did: **a candidate**. And inspecting it
showed the screen has been selecting the wrong thing.

## Result

| | |
|---|---|
| candidates offered by the query | **160** (`--per-stratum 20 × 8 strata`) |
| considered | **81** |
| fetched | **51** (63 % yield, 7.7 GB) |
| screened | **50** |
| skipped as unmeasurable | **1** (6QI8, `11.03 Å for a 3.75 Å map`) |
| ratio range | **0.6845 – 1.2101**, median **0.9758** |
| **above the 1.074 fence** | **1** — 7DZX |
| above the 1.3 cut | 0 |

## The candidate does not survive inspection (#234)

**7DZX: ratio 1.210, crossing 4.272 Å against a 3.53 Å map — and `cc_mask_pre` = 0.2083.**

| | `cc_mask_pre` |
|---|---|
| this batch of 50 | min **0.2083** (7DZX), next lowest 0.5928, median 0.8313 |
| the 59 on record | min 0.4297, median 0.8053 |

**7DZX fits its own map worse than every entry anywhere in this work.** A model that barely correlates
with its map will have an FSC crossing far past the map's stated resolution as a matter of arithmetic.
That is not the hypothesis; it is a mismatch.

Set against the other entries above the fence:

| entry | ratio | `cc_mask_pre` |
|---|---|---|
| 9H7U | 1.372 | not recorded |
| 10BU | 1.360 | **0.7577** |
| 6PMJ | 1.094 | **0.4297** |
| 10EU | 1.076 | 0.7542 |
| 7DZX | 1.210 | **0.2083** |

**The fence selects two different populations.** 10BU and 10EU — the entries that motivated the
hypothesis — have ordinary fits near 0.75. 6PMJ and 7DZX are the two worst-fitting entries on record.
Screening on the ratio alone cannot separate *"the crossing genuinely runs past the resolution"* from
*"the model does not fit the map"*, and **two of the five entries ever found above the fence are the
second kind**.

No correlation is claimed. Pearson r(`cc_mask_pre`, ratio) over the 50 is **−0.088**, and **+0.466**
with 7DZX removed. A statistic whose sign flips on one point is not interpretable — round 22's own
n = 2 lesson applies to this as much as to the hypothesis it concerns.

## The base rate has moved, and against the project

| | above 1.074 |
|---|---|
| prior record | 4 of 60 = **6.7 %** |
| this batch | 1 of 50 = **2.0 %** |
| combined | **5 of 110 = 4.5 %** |

`P(≤1 of 50 | p = 0.067) = 0.145` — low but not decisive, so 6.7 % is **probably** an overestimate
rather than demonstrably one. The likely reason is structural: the prior 60 include the two entries
that motivated the hypothesis, so the rate was partly estimated on the observations that defined it.

The cost consequence is direct. Three candidates needs **~66 screened** at 4.5 %, not the ~45 that
6.7 % implied — and if the two poor-fit entries are excluded as #234 argues, the rate of *genuine*
candidates is **3 of 110 = 2.7 %**, needing **~110 screened**.

## What round 34 predicted, and got right

> `--per-stratum 20` would offer 160, and the same money would buy three to four times the entries.
> **The project is not expensive; it was under-queried.**

Confirmed: 14 entries became 50, from the same pipeline and the same window. Yield held at 63 %
against round 34's 54 %. The 30 rejections split 11 unparameterised ligands, 7 oversized models,
7 formal-charge failures and 5 oversized maps.

## Both round-34 fixes held under a real batch

#231 and #232 were found on a 14-entry run. This was their first genuine test:

    51 entries in entries.json, 51 maps, 51 models, 0 orphans,
    canary entry preserved across ~9 flush() calls

Had #231 still been live, the batch would have erased the canary and screened 50 against 51 cached —
a denominator off by one in the round that revises a base rate.

## Scope limits

- **The hypothesis remains untested.** One candidate was found and it is probably an artefact. No
  refinement was run; no `d_FSC_model` delta was produced; no band was tested.
- **The 4.5 % combined rate pools two non-independent samples.** The 60 and the 50 come from the same
  stratified query over the same 2.4–4.2 Å window, so this is not an independent replication.
- **`cc_mask_pre` is not recorded for 9H7U**, one of the two motivating entries, so the confound
  cannot be checked against the strongest case for the hypothesis.
- **The exclusion threshold is not set here.** #234 argues for one; choosing it after seeing 7DZX's
  ratio would be fitting the criterion to the data, which is what round 26 filed as #146. It belongs
  in a pre-registration.
- **Nothing is gated.** Six consecutive rounds have declined to build on an unresolved premise.
