# Tolerance benchmark — round 38: the selector fix stops the attrition, and a fresh sample breaches the favored band

**No tolerance, band or measurement is changed.** No registry figure is touched. Round 38 measured a
fresh set and one entry breaches a §4 band; the pre-registration required that the decision to widen
be **registered separately** rather than taken in the round that first sees the breach, so it is filed,
not made.

Round 38 is [round 37](tolerance_benchmark_round37.md) with the selection defect removed. Round 37
lost 11 of 21 selected entries to three defects with one root cause — the selector took the head of
each stratum, which is the oldest depositions, which are also the entries missing R-free flags and
most likely to be nucleic acid. All three are fixed (**#241 (medium)**, **#243 (medium)**, #247), and
round 38's first job was to say whether that was the whole problem.

The registration is in
[`tolerance_benchmark_round38_preregistration.md`](tolerance_benchmark_round38_preregistration.md),
committed before any refinement in a commit containing no results. The set, its measurements and the
selection are committed alongside this document in
[`ref/research/data/round38_xray_selection.json`](data/round38_xray_selection.json) and
[`ref/research/data/round38_xray_deltas.json`](data/round38_xray_deltas.json).

## Result

| prediction | verdict |
|---|---|
| **P1** — both bands hold, no breach | **FALSIFIED** — the `d_min ≥ 2.5 Å` favored band is breached |
| **P2** — fresh Cα-shift max below the lost 0.285 Å | confirmed — **0.2004 Å**, but above round 37's 0.1828 Å |
| **P3** — fresh favored drop below the lost 5.26 pp | **FALSIFIED** — **6.28 pp** (6LE5) |
| **P5** — no deposited model starts above the "not reproducible" clashscore 17.2 | **FALSIFIED** — max **27.71** (1B9B) |
| **P6** — refinement failure rate below round 37's 7 of 18 | confirmed — **3 of 17** (17.6 %), only 1 the R-free cause |
| **P7** — usable n at least 14 of 17 | confirmed — exactly **14** |

| quantity | round 38 (n = 14) | round 37 (n = 10) | the lost figure | band |
|---|---|---|---|---|
| Cα-shift max | **0.2004 Å** (7P4U, 2.74 Å) | 0.1828 Å | 0.285 Å | + 0.35 Å |
| Cα-shift median | 0.1273 Å | 0.1237 Å | — | — |
| worst favored drop | **6.28 pp** (6LE5, 3.10 Å) | 2.61 pp | 5.26 pp | − 6 pp |
| max starting clashscore | **27.71** (1B9B) | 38.70 | 17.2 "not reproducible" | — |

## P3 is the one that matters, and it is the strong direction

The pre-registration stated the asymmetry in advance, carried over from round 37:

> A larger sample can only push a maximum up, so **P2/P3 failing at n = 20 is meaningful while P2/P3
> holding is weaker evidence.**

P3 failed. **6LE5** (3.10 Å) drops from 93.86 % favored to 87.58 % under a null re-refinement — a
**6.28 pp** fall, past the lost maximum of 5.26 pp and past the −6 pp band the §4 *favored* clause
publishes for `d_min ≥ 2.5 Å`. The refinement is well-behaved by every other measure: R-work improves
0.2769 → 0.2526, R-free 0.3180 → 0.3167, rotamer outliers fall 0.51 → 0.06 %, and 2165 Cα pairs
match. It is not a broken refinement flagged by its own R-factors; it is a correctly-behaving one that
the favored band would wrongly call degradation. That is exactly the null-case failure the §4 bands
exist to be calibrated against — the same shape as round 11's 0.1011 Å ΔRMSD breach.

**This is a single-entry breach.** The next-worst favored drop is 7P4U at −2.97 pp, less than half of
6LE5's, and the 14 usable entries split 7 down / 7 up (signed median +0.035 pp) — a null refinement
moves favored in both directions, and only one entry moves it past the band. That is the pattern the
registry already records for these bands: *"each new band is again set just above a single worst case,
so treat a further break as the base case."* Round 38 is that further break.

**Nothing is re-fitted here.** Whether the −6 pp band should widen to clear 6.28 pp is a decision the
pre-registration required to be registered on its own, before the widened number is seen against more
data — filed as a new issue, not taken in this document.

## P6 and P7: the selector fix stopped the attrition

Round 37 lost 7 of 18 refinement attempts, **all** to missing R-free flags — a failure class
concentrated in the early depositions the old selector favoured. Round 38, sampling evenly across
deposition era, lost **3 of 17**, and only **one** of those (1RD7) is the R-free cause. The other two
are unrelated crystallographic faults the era spread simply exposes more of:

| id | stage | reason |
|---|---|---|
| 12UN, 1Y4S, 7CS8 | fetch | no amplitudes or no FREE column |
| 1RD7 | refine | no usable R-free flags in the deposited data |
| 3VDD | refine | improper rotation matrix in the deposited coordinates |
| 4UDM | refine | cctbx `merge_equivalents_exact`: incompatible Friedel-mate flags |

The R-free failure rate fell from **7/18 to 1/17**. Per the registration, that settles **#242**'s
methodological half: whether to generate R-free flags is now moot, because the flags are no longer the
dominant loss. **Zero entries were lost at the measure stage** — the protein filter (#241) held, where
round 37 lost 12CI as nucleic acid. So the selector defect was the whole problem for the *excess*
attrition it caused — the R-free failure class (7/18 → 1/17) and the nucleic-acid loss (→ 0). It was
**not** the whole of attrition: 20 selected → 3 fetch rejects → 17 pairs → 3 refine failures → **14
usable** still loses **6 of 20 (30 %)** — round 38 keeps **14 of 17** refinement attempts against
round 37's 10 of 18. The 6 that remain are baseline
crystallographic attrition no selector fix touches — 3 fetch rejects (no amplitudes/FREE column) and 2
non-R-free refine failures (3VDD improper rotation matrix, 4UDM incompatible Friedel-mate flags) — the
kind any unbiased low-resolution sample carries.

And it was **not** the whole problem for the bands. A representative sample is exactly what let the
favored band be breached — round 37's all-pre-2000 set never reached an entry like 6LE5.

## P5 replicates on an era-spread sample

Round 37 falsified P5 — a fresh sample reached starting clashscore 38.70 against the registry's
"not reproducible" 17.2 — but on a set that was entirely pre-2000. Round 38's set spans eras, and P5
falsifies again: **four** of the 14 deposited models start above 17.2 (1B9B 27.71, 1VYJ 25.14,
2QTU 19.90, 1RH7 17.63). So 17.2 is unremarkable for this branch regardless of deposition era; it was
never an extreme only a lost entry could supply. As in round 37 this is a property of *deposited
models*, not of the refinement behaviour the bands govern, and it moves no band.

## Absolute floors

The deposited models meet the §2 quality bars rarely, as at every low resolution: clashscore ≤ 4 in
**0 of 14**, favored ≥ 97 % in **2 of 14**, rotamer outliers ≤ 2 % in **5 of 14**. These are quality
bars, not refinement checks (§4), and are reported here only to show the branch is, as expected,
populated by models that would not pass §2 on geometry alone.

## Scope limits

- **The lost entries are still lost.** This measures the `d_min ≥ 2.5 Å` branch on fresh entries; it
  does not recover the ~11 unnamed entries that set the published band widths. A fresh breach is new
  evidence the band is too tight, not a reconstruction of the old maximum.
- **n = 14, and the breach is one entry.** 6.28 pp rests on 6LE5 alone; the second-worst drop is
  2.97 pp. A band decision on a single worst case is precisely what the registry warns to treat as the
  base case, which is why widening is deferred to a registered decision rather than taken here.
- **Unrestrained refinement.** The −6 pp band is quoted for unrestrained refinement, and this set was
  refined unrestrained. The registry already records that resolution-appropriate NCS + secondary-
  structure restraints shrink the low-resolution favored spread (5.26 → 3.35 pp); whether 6LE5's drop
  survives restraints is untested and is part of the deferred decision.
- **P2/P3 asymmetry.** P2 holding (Cα max 0.2004 < 0.285) is weak evidence by the registration's own
  statement; P3 failing is strong. The Cα maximum did rise from round 37's 0.1828 to 0.2004 with four
  more usable entries, consistent with a maximum that a still-larger sample would push further.
- **Nothing is re-fitted**, P1's breach notwithstanding. The band-widening decision is filed.
