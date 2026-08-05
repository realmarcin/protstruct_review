# Tolerance benchmark — round 33: the population is exhausted, and the question should be dropped

**No tolerance, band or measurement changed.** No registry figure is touched.

Round 31 asked whether corrections are more defective than the text they correct and could not answer.
Round 32 exhausted the committed-document arm and could not answer. Round 33 widened to the arm round
32 named — PR and issue prose — exhausted **that**, and **still cannot answer**.

It also establishes why, which is the useful part: **the effect is too small to find with any amount
of work this repo can produce.**

## Result

| | |
|---|---|
| population | **109 bodies**, #110–#219 (20 merged PRs, 89 issues) |
| claim-bearing lines | **493**, all processed — exhausted per the registered stopping rule |
| claims classified | **102** |
| verifiable | **101** |
| **wrong at write** | **3** |
| rate | **2.97 %** |

Comparison arms: round 32's committed-correction arm **3.45 %**, round 28's documents **2.28 %**.

## The predictions

**P6 — the ungated channel is worse. FALSIFIED, in direction.**

PR and issue bodies pass through no `validate.sh`, no gate, no diff review, no second reader. They
should have been the worst text in the repo. They are **2.97 %** against the gated, reviewed,
committed arm's **3.45 %** — *cleaner*, not worse.

The difference is not significant (`P(≥3 | p = 0.0345, n = 101) = 0.681`), so the honest statement is
**not** "prose is cleaner than gated documents". It is that **the gating apparatus this repo spent
rounds 24–30 building is not detectable in the error rate of the text it protects.** That is a
result about the gates, arrived at by a round that was not looking for it.

**P7 — this population yields n ≥ 130. FALSIFIED.** It yields **101**. Claim density was **0.21 per
line**, below round 32's 0.26, and 493 lines were not enough. The projection made at the interim
point (~128) was optimistic by 27.

**P2 — scope is the dominant cause. FALSIFIED on the pooled evidence.**

| wrong claim | cause |
|---|---|
| `Fix #170` — today's range on round 12's set (round 32) | scope |
| `Fix #187` — 62 % "of all defects" (round 32) | scope + memory |
| #188 body — "15 of 24 (62 %)", 96 s after the correction | **memory** |
| #132 body — "a 20-file audit round" of a 19-file diff | **memory** |
| #215 body — "already stated three times"; it is twice | **memory** |

All three body-arm failures are **counts restated from memory when the source was one command away**.
Zero are scope. Pooled across both arms: **memory 3, scope 2.** Round 32's "scope in 2 of 2" was a
sample of two, and it did not survive contact with a sample of five.

That reverses round 32's parting note about `round_figures.py`. It would have caught **all three** of
this round's failures: `--issues` for #188's count, `--diff` for #132's file count, `--commits`-style
derivation for #215's. The tool addresses the majority cause after all.

**P9 — edited bodies are wronger than never-edited ones. Direction holds, and it is the selection
effect it was registered as.**

| | claims | wrong | rate |
|---|---:|---:|---:|
| bodies ever edited | 26 | 2 | 7.69 % |
| never edited | 75 | 1 | 1.33 % |

Two wrong claims against one. Both edited bodies (#188, #215) were edited **because review found the
error** — the edit is downstream of the defect, not evidence about it. Registered in advance
precisely so this would be reported as tautology rather than insight.

One thing it does show: #215's wrong sentence is **still in the current body**. The correction was
*appended* as a new section rather than applied to the sentence, so the body simultaneously asserts
"already stated three times" and explains that it is twice.

## Why the question should now be dropped

Pooled across both correction arms: **5 wrong of 159 verifiable = 3.14 %**, against the document base
rate of **2.28 %**. `P(≥5 | p = 0.0228, n = 159) = 0.298`.

The difference is **0.86 percentage points**. To detect a difference that size at 80 % power and
α = 0.05 requires:

    n ≈ 5,542 claims per arm

Three rounds of exhaustive hand-verification produced **159**. At that rate the test needs roughly
**105 more rounds** of sweeping, and there is no more population to sweep — committed documents and
prose are both exhausted. Widening again means other repositories, which changes the question.

**So the answer is not "corrections are more defective" or "they are not". It is that the effect, if
it exists, is around one part in a hundred, and this repo cannot resolve one part in a hundred.**
Rounds 31, 32 and 33 asked a question whose answer was never going to fit inside the evidence
available, and the honest close is to say so and stop, rather than to widen a fourth time.

## What the three rounds did establish

Not nothing — but none of it is the registered question:

- **The base rate of wrong numeric claims in this repo is about 2–3 %**, consistent across gated
  documents (2.28 %), committed corrections (3.45 %) and ungated prose (2.97 %). Three independent
  measurements of the same quantity by different methods, which is the strongest thing in this series.
- **Gating is not visible in that rate.** Whatever `validate.sh` and the review pass buy, it is not a
  measurable reduction in wrong figures.
- **Memory is the dominant cause**, at 3 of 5 pooled, and the existing tool addresses it.
- **PR and issue prose is auditable** (#219), which round 32 denied. Timestamps settle wrong-at-write
  exactly: the *"62 %"* figure appears 15 times, and three of the four assertions were **correct when
  written** — the fourth missed by **96 seconds**.

## Scope limits

- **101 claims is the whole population, not a sample.** As in round 32, this is stronger than a lower
  bound and worse for the question.
- **Single rater, no second pass**, and the classification of *cause* (memory vs scope) is a judgement
  about mechanism, not a measurement — round 30 disclosed the same limit for the same split.
- **Author effects.** Every body has one author. Nothing generalises.
- **The three arms may not be commensurable.** A PR body argues, a registry row states, and the same
  claim rule applied to both may partly measure prose style. Disclosed before the measurement.
- **Nothing is gated.** Four consecutive rounds have now declined to build on an unresolved premise.
  This one declines and additionally recommends the question be closed.
