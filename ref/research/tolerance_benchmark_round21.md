# Tolerance benchmark — round 21: giving the L-test a set, and closing the last all-or-nothing write

Two backlog items, one of them a measurement and one a code change.

## Item 1 — the L-test set: re-measure rather than retire

Round 18 marked the L-test row `⚠ partial record`: it reports **27 datasets** and names **5**. The
script is the extreme case in the registry — `bench_t13_l_test.py` has **no id argument at all**. It
parses whatever `xt_*.log` / `ct_*.log` pairs a prior `bench_t13_wilson_b.py` run left in a cache, so
its set was never even expressible, let alone recorded.

Round 18 proposed **retiring** the unverifiable half (median |Δ| 0.006, max 0.047) and keeping the
twin/no-twin call, which is the load-bearing part and agreed 27/27. Round 19 found the cheaper option:
**the inputs are already committed.** `bench_t13_wilson_b.py` carries a hardcoded 24-dataset
`DEFAULT_SET` (round 18) and CCP4 is installed locally, so re-running Wilson B regenerates L-test
inputs for a **named, re-derivable** set.

That does not recover the original 27. It replaces "5 of 27 named" with "24 named and re-derivable",
which is a different and better position: the published figures stay unverifiable, and the row gains
numbers anyone can regenerate from a clean checkout.

**Note the set is not the same one.** The L-test row reports n = 27 and Wilson B's is 24 — at least
three datasets are unique to the L-test and cannot be identified even by cross-reference. So this is a
**new measurement with its own denominator**, exactly as round 20's was.

### Predictions, registered before the data

Baseline, from the unreconstructable 27: median |Δ| **0.006**, **25/27** inside ±0.02, twin call
**27/27**, max **0.047**, matched resolution range in **0 of 18** where ctruncate reported one.

| # | Prediction | Falsified if | P |
|---|---|---|---|
| **P1** | The twin/no-twin call agrees on **all 24** — the load-bearing half. | Any dataset disagrees. | 90 % |
| **P2** | Median \|Δ\| falls in **[0.003, 0.012]**, replicating 0.006 within a factor of two. | It falls outside. | 70 % |
| **P3** | At least **21 of 24** fall inside ±0.02, replicating the 25/27 rate. | Fewer than 21 do. | 75 % |
| **P4** | **At least one** dataset exceeds ±0.02 — the band is breached by somebody, as 2 of 27 were. | None does. | 65 % |
| **P5** | The **matched-resolution-range precondition stays unachievable**: 0 datasets match. | Any dataset matches. | 85 % |
| **P6** | Max \|Δ\| does **not** exceed the published 0.047. | Some dataset exceeds it. | 70 % |

**P3 and P4 are deliberately opposed.** Together they say the band should be *mostly* right and *not*
vacuous — the failure this repo keeps finding is a band so wide nothing can breach it, and the
published 2-of-27 breach rate is the evidence that this one is not. If P4 fails while P3 holds, ±0.02
is looser on this set than on the old one and the row should say so.

**P6 is the one that would move the row.** The published max of 0.047 is 38 % of the whole physical
scale (0.500 → 0.375). A larger excursion on an independently drawn set would say the disagreement is
worse than recorded — and unlike most figures in this file, this one cannot be checked against its
original set, so a new maximum simply replaces it.

### Results — all six held, and the replication is close

24 of 24 datasets processed. The full per-dataset table is regenerable with
`bench_t13_wilson_b.py --cache DIR` followed by `bench_t13_l_test.py --cache DIR`.

| | published (27, unreconstructable) | round 21 (24, re-derivable) |
|---|---|---|
| median \|Δ\| | 0.006 | **0.0065** |
| inside ±0.02 | 25/27 (93 %) | **22/24 (92 %)** |
| max \|Δ\| | 0.047 | **0.047** |
| twin/no-twin call agrees | 27/27 | **24/24** |
| matched resolution range | 0 of 18 reporting | **0 of 15 reporting** |

| # | Prediction | Outcome |
|---|---|---|
| P1 | twin call agrees on all 24 | ✅ 24/24 |
| P2 | median \|Δ\| in [0.003, 0.012] | ✅ **0.0065** |
| P3 | ≥ 21 of 24 inside ±0.02 | ✅ **22** |
| P4 | at least one exceeds ±0.02 | ✅ **two** — 9PLC 0.047, 30IZ 0.030 |
| P5 | 0 datasets match the resolution range | ✅ 0 of 24 |
| P6 | max does not exceed 0.047 | ✅ **exactly 0.047** |

**All six holding is itself worth distrusting**, as round 16 established. P1 and P5 were near-certain
— both restate structural facts about the two programs rather than sampling anything. The informative
ones were P2, P3 and P6, and their agreement with the historical figures is closer than the
sample sizes deserve.

### The breaching datasets were both already named

This is the round's real finding, and it inverts the usual pattern.

The two datasets that exceed ±0.02 are **9PLC (0.047)** and **30IZ (0.030)**. Both are among the
**five** the old trail happened to name. So the historical "25/27 inside ±0.02" had **2 breaches, and
both are recoverable** — the published maximum of 0.047 is 9PLC's, reproduced here to four decimals.

Everywhere else in this series, selective recording destroyed the evidence and kept the anecdote.
Here it did the opposite: an author tabulating "the worst cases" preserved **exactly the observations
a breach-counting argument needs**, and lost only the denominator. For a band whose evidence *is* its
breaches, that is the more useful half to have kept — by luck, not design.

It does not make the 27 reconstructable. Three or more datasets remain unidentifiable, and the
*rate* (2 in 27 versus 2 in 24) still cannot be checked against the original.

### What changes

The row no longer rests solely on a set nobody can rebuild. It now carries a **24-dataset measurement
anyone can regenerate from a clean checkout**, which agrees with the historical figures on every
quantity. The historical 27 stays as corroboration rather than as the only evidence.

The `⚠ partial record` mark stays on the *historical* figures, because they are still unverifiable in
their own right. What has changed is that the row is no longer *only* that.

## Item 2 — the EM benchmark's all-or-nothing write

`bench_refinement_deltas_em.py` calls `append_results()` **once, after every entry has finished**.
Round 19 ran for roughly nine hours; a crash at entry 9 of 10 would have left the committed TSV with
**nothing**, losing the durable record for eight completed refinements.

The values would technically be re-derivable from the cached logs — but only by whoever still had the
cache, which is precisely the failure mode rounds 16–18 spent three rounds closing. It is the last
all-or-nothing step in the pipeline.

No prediction is registered: this is a code change, not a measurement.

### Done

`collect()` now takes a `record` callback and calls it after **every** entry, on all five exit paths
— the four skip paths as well as the success path. `main()` wires it to `append_results`, whose
dedup by id makes the retained end-of-run call an idempotent safety net rather than a second write.

Tested by simulating a crash at entry 3 of 5: the two completed entries are on disk with their round
label. The no-callback path is pinned too, so removing the wiring surfaces as a failing test rather
than as a silently empty file after a nine-hour run.
