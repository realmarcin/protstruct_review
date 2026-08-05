# Round 31 — pre-registration

Registered **before any measurement**, in a commit containing no results.

## The claim under test

Round 30 concluded: *"the gap is adherence, not invention"* — 56 % of wrong-at-write figures were
counts restated from memory against a rule the repo already had. That conclusion is about the
**population of all wrong figures**. It says nothing about *where in the writing process* they enter.

Rounds 30 and 31 have supplied a pattern round 30 could not have seen, because it swept rounds 24–29
and this is about what happened next. Every defect below is a defect **in a correction**:

| defect | what it corrected | what was wrong with the correction |
|---|---|---|
| #187 | the #185 analysis | four claims, one a *confirmed* prediction that is falsified |
| #191 | #187 | left P2's cause split at 15 + 9 against a total of 27 |
| #194 | #191 | attached an instance count to the wrong scope |
| #195 | (same commit as #194) | refuted its own durability count within one sentence |
| #201 | #187's classification | inverted the `#167c`/`#177c` pairing |
| #202 | #195 | missed a paraphrase of the very count it was fixing |
| #204 | #203's own body | miscounted its own sweep |

Seven, in a stretch of work whose entire subject was defect counts. Either this is a run of bad luck
in a small sample, or **corrections carry a higher defect rate than the text they correct** — and if
so, the review-and-fix loop this repo runs is partly self-defeating, which matters more than any
further gate.

Round 28 already measured the comparison arm: ~326 numeric claims swept by hand, ~307 verifiable,
**7 wrong ≈ 2.3 %**. That is the rate for load-bearing documents written as original text. The
correction rate has never been measured against it, and the seven above are — exactly like round 27's
"nine miscounts" — **a tally of what I happened to notice**, not a measurement.

## Method, fixed in advance

**Population.** Every commit whose subject begins `Fix #` — the repo's convention for a commit that
exists to repair a previously filed defect — reachable from any merged pull request.

The obvious enumerator is wrong and was tested before being registered: `git log main | grep '^Fix #'`
returns **3**, because every PR is squash-merged, so a correction made *inside* a round's PR is
absorbed into a subject beginning `Round NN:`. The correct enumerator walks the PRs
(`gh pr view <n> --json commits`), which GitHub retains **after the branch is deleted** — verified on
#193, whose branch is gone and whose three `Fix #` commits still resolve. That yields **39** commits
across the merged PRs, a population worth measuring rather than the 3 the naive command reports.

**The primary population is the 33 from round 24 onward** (PRs #114 … #193), because the comparison
arm — round 28's ~2.3 % — was swept over rounds 24–27 documents, and a numerator drawn from a wider
window than its denominator is not a rate. The other **6** (PRs #22, #86, #99, #106; rounds 7–23)
are measured and reported **separately**, not pooled.

That split is #208, found reviewing this document before it merged: it first stated the population as
all 39 against a rounds-24-27 denominator. **A scope error in a count, inside the pre-registration
that nominates scope errors as the dominant class** — and the fifth in the series after #164, #174,
#176 and #194. It is left recorded here rather than quietly corrected, because a prediction is worth
less if the document making it has already demonstrated the failure and hidden it.

Recording the enumerator here rather than in the results is deliberate for the same reason: round 30's
finding was that evidence gets called unrecoverable without running the command that recovers it, and
a method that silently sampled 3 of 39 would have produced a confident, meaningless rate.

**Unit.** A *numeric claim introduced or modified by that commit* — a count, a rate, an n, a range
endpoint — in the commit's diff to `.md` files. Not: tolerance values, resolutions, PDB ids, issue
numbers, dates, version strings. This is round 28's rule verbatim, so the two arms are commensurable;
using a different rule would make the comparison meaningless, which is the point of reusing it.

**Verdict.** Each claim is **verifiable** (a committed source settles it) or **unverifiable**, and
each verifiable one **correct** or **wrong**, checked by re-deriving it from its source — not by
pattern-matching, and not by whether an issue was ever filed against it. Filing is the sampling bias
this round exists to remove.

**Denominators are stated with numerators**, and the correction arm's denominator is claims, not
commits — a commit touching twenty claims is not one observation.

## Predictions

**P1 — the correction arm's wrong-claim rate is HIGHER than round 28's ~2.3 %.**
The direct test. *Falsified* if the rate is at or below 2.3 %, which would mean the seven noticed
defects are a visibility artefact of corrections being reviewed harder than original text, and the
loop is not self-defeating.

**P2 — the dominant cause in the correction arm is SCOPE, not memory.**
Round 30's overall split was memory 56 % / incomplete edit 44 %. But #194, #201 and #204 are none of
those exactly: each states a number that is right for some population and wrong for the one named.
*Falsified* if memory-restatement outnumbers scope errors among what this sweep finds. This one is a
genuine fork: if P2 holds, `round_figures.py` (#188) addresses the wrong half of the problem, since
deriving a count does not tell you which population it should range over.

**P3 — a correction-of-a-correction is more defective than a first correction.**
Chain depth is derivable: #191 corrects #187 corrects #185 is depth 3. *Falsified* if depth ≥ 2 has a
rate at or below depth 1. If it holds, the actionable rule is about *when to stop editing a
paragraph*, not about how to check a number.

**P4 — at least one wrong claim is currently live on `main` in a correction commit's own text.**
The seven above were all filed and fixed. *Falsified* if every wrong claim the sweep finds has
already been corrected, which would mean review is keeping pace even if corrections are noisy.

## What this round cannot answer

- **Whether the sweep is complete.** One reader over a commit range. The same "lower bound, not a
  total" caveat that round 28 carried applies here, and the result must be reported that way rather
  than as a defect density.
- **Whether the two arms are truly comparable.** Round 28 swept *documents as they stand*; this
  sweeps *claims as introduced by a commit*. A claim written wrong and fixed later is invisible to
  the first and visible to the second. That asymmetry favours P1 and is disclosed **before** the
  measurement, not offered afterwards as a caveat on a result I liked.
- **Anything causal.** If corrections are more defective, this cannot say whether that is haste,
  narrowed attention, or that corrections are simply written about harder subjects.
- **Whether a fix would work.** Nothing is gated this round regardless of the outcome. Round 29 and
  round 30 both declined to build on a falsified or indeterminate premise; that precedent holds here.
