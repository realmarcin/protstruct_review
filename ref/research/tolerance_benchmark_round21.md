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

## Item 2 — the EM benchmark's all-or-nothing write

`bench_refinement_deltas_em.py` calls `append_results()` **once, after every entry has finished**.
Round 19 ran for roughly nine hours; a crash at entry 9 of 10 would have left the committed TSV with
**nothing**, losing the durable record for eight completed refinements.

The values would technically be re-derivable from the cached logs — but only by whoever still had the
cache, which is precisely the failure mode rounds 16–18 spent three rounds closing. It is the last
all-or-nothing step in the pipeline.

No prediction is registered: this is a code change, not a measurement.
