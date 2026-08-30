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

**Note what this is and is not.** The L-test row reports n = 27 and Wilson B's is 24, so at least three
datasets are unique to the L-test. But the 24 is almost certainly a **subset** of the 27, not a fresh
draw — see "This is a re-run, not a replication" below, which was written after the results and
corrects the framing this section originally carried.

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
| P5 | 0 datasets match the resolution range | ✅ **0 of the 15** where ctruncate reported one (the other 9 are `unknown`, not mismatches) |
| P6 | max does not exceed 0.047 | ✅ **exactly 0.047** |

**All six holding is itself worth distrusting**, as round 16 established — and here the reason is
concrete rather than a hedge. See the next section: the agreement is closer than the sample sizes
deserve because the samples are mostly the same samples.

### This is a re-run, not a replication — and the round originally said otherwise

**The 24 is a subset of the 27.** This section corrects the framing above, which was written before
the results and treated the measurement as an independent draw. It is not:

| | historical (27) | round 21 (24) |
|---|---:|---:|
| ctruncate reported a range | 18 | 15 |
| ctruncate printed **no** range | **9** | **9** |

The "no range" count is **exactly 9 in both runs**, and 18 − 15 = 3 = 27 − 24, so the three extra
historical datasets all sit in the reporting group. All five historically-named datasets are in
Wilson B's committed 24. Both benchmarks read the same Wilson B cache, so the historical L-test set
was that era's Wilson B set plus whatever else was in the directory.

**So the agreement on median, breach count, max and twin call is largely guaranteed** — the same
deposited structures through the same two deterministic programs. P2 and P6, registered at 70 %, were
not meaningfully uncertain for the entries that determine the median and the maximum.

What round 21 **does** establish, and it is worth having:

- **The historical figures are reproducible.** All five named datasets return their published values
  to the digit, fifteen-odd rounds later.
- **The L-test has a committed, re-runnable set** — the actual objective, and it stands regardless.

What it does **not** establish is independent corroboration of the band. The row should say so.

### The breaching datasets were already named — and that is structural, not lucky

The two datasets that exceed ±0.02 are **9PLC (−0.047)** and **30IZ (+0.030)**, and
`tolerance_benchmark_l_test.md` **named both before this round ran** —
*"exceeding ±0.02 | 2 / 27 (30IZ +0.030, 9PLC −0.047)"*. Round 21 reproduces both to the published
digit but did not discover them.

In fact **all five** datasets the old trail tabulated reproduce exactly:

| dataset | published Δ | round 21 Δ |
|---|---:|---:|
| 9PLC | −0.047 | **−0.0470** |
| 30IZ | +0.030 | **+0.0300** |
| 9RWI | −0.016 | **−0.0160** |
| 12LO | −0.014 | **−0.0140** |
| 9LLR | −0.013 | **−0.0130** |

So the *overlap* between the old set and the new one is verified dataset by dataset, which is
stronger than the aggregate agreement above: the two runs are measuring the same thing the same way.

The useful observation is not that this was lucky but that it is **structural**. Breaches are by
construction the largest-magnitude entries, and a "worst cases" table is sorted by magnitude — so
**any worst-N table contains every breach whenever the breach count is ≤ N.** With 2 breaches and
N = 5, preservation was close to guaranteed.

That is a better rule than the coincidence it was first written up as: worst-case tabulation
*reliably* keeps breach evidence and *reliably* loses the denominator. For a one-sided band, whose
evidence **is** its breach count, the half that survives is the half that matters — predictably, and
without anyone intending it.

It does not make the 27 reconstructable. Three or more datasets remain unidentifiable, and the
*rate* (2 in 27 versus 2 in 24) still cannot be checked against the original.

### What changes

The row no longer rests solely on a set nobody can rebuild. It now carries a **24-dataset measurement
anyone can regenerate from a clean checkout**. That measurement is a **re-run of most of the original
set**, not an independent check of it, so it does not corroborate the historical figures — it makes
them **reproducible**, which is a different and more modest claim.

The `⚠ partial record` mark stays on the row: the historical 27 is still unreconstructable, and the
new 24 inherits rather than replaces that limitation. What has changed is that anyone can now
regenerate the numbers the row quotes.

## Self-review findings, filed as issues

Reviewing this PR's own diff found six defects
([#93](https://github.com/CultureBotAI/protstruct_review/issues/93)–[#98](https://github.com/CultureBotAI/protstruct_review/issues/98)),
all fixed here. The first two are the round's own headline claims:

- **#93 (high)** — the measurement was framed as an **independent** one agreeing with the historical
  figures. It is a **subset re-run**: same structures, same deterministic programs, so the agreement
  was largely guaranteed. The round even noticed the agreement was "closer than the sample sizes
  deserve" and reached for a hedge instead of the one-line check that explains it.
- **#94 (medium-high)** — "publication bias preserved the half that matters" was written as a
  discovery and a piece of luck. The breaching datasets were **already named in the old trail**, and
  their preservation is **structural**: a worst-N table contains every breach whenever breaches ≤ N.
- **#96 (medium)** — the backlog said six rows carry the partial-record mark; the registry literally
  has seven, and the L-test keeps its own.
- **#95, #97, #98 (low)** — round table out of order again (as in #90), a denominator switched between
  two lines, and a stale comment implying the two sets are mostly disjoint.

**Both headline defects point the same way: the round wanted its result to be stronger than it was.**
That is the failure round 20 recorded as "stating a stronger version of a true result", repeated one
round later on a different subject — and this time it took an outside reading to catch, because the
supporting arithmetic was all correct. Numbers being right is not the same as the story being right.

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
