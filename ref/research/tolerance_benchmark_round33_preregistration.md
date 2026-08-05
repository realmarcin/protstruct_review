# Round 33 — pre-registration

Registered **before any measurement**, in a commit containing no results.

## Why this round exists

Round 32 exhausted the committed-document population and found it cannot answer the question:
**58 verifiable numeric claims where the test needs 130.** Its parting instruction was to widen the
population or drop the question. This widens it.

The new arm is **PR bodies and issue text** — the place where #204 lived, and where part of #187 did.

## The reliability question, settled before registering rather than assumed

Round 32's scope limit said this population is *"not diffable"*. It is (#219). GraphQL
`userContentEdits` returns every prior version of a body with an `editedAt` timestamp, and
`totalCount: 0` means a body was never edited — so its current text **is** its original.

Canaried before this file was written, not after:

    pullRequest(203) -> totalCount 2, both prior bodies in full, including the
                        pre-correction "7 hits" text that became #204
    issue(204)       -> totalCount 0   (never edited; current text is original)
    issue(210)       -> totalCount 0

So **wrong-at-write is directly determinable here**, which is the property round 31 and 32 depended on
and had to reconstruct from commit diffs. This arm is, on that one axis, *better* evidence than the
committed documents — an inversion of what round 32 assumed.

## Population, fixed in advance

**All bodies numbered #110–#219 inclusive**: 20 merged pull requests and 89 issues, **109** bodies.

Both bounds are stated because the population moved while this file was being written: the first
count gave 88 issues, and filing #219 — the correction that made this round's method sound — made it
89. A population defined as *"from #110 onward"* is not a population; it is a query whose answer
changes every time the work touches it. **#219 is the upper bound and is included**, since it was
filed before any measurement began.

#110 is the lower bound because it is the first PR of the rounds-24+ window round 28 swept, which
keeps this arm comparable with both prior ones.

- **Original text** is `userContentEdits` oldest node when `totalCount > 0`, else the current body.
- Bodies I edited during rounds 31–32 are the interesting cases and are **not** excluded; excluding
  them would remove exactly the errors that were caught, which is the sampling bias this series
  exists to remove.

## Unit and verdict — unchanged for the fourth time

A numeric claim: a count, rate, n, or range endpoint asserted about the work. Not tolerance values,
resolutions, PDB ids, issue numbers, dates, version strings. Round 28's rule verbatim. Each claim is
verifiable or unverifiable, and each verifiable one correct or wrong, **by re-deriving from its
source**.

Changing the rule now would break comparability with all three prior arms, which is the only reason
this round can say anything at all.

## Stopping rule, fixed in advance

> **Exhaust the population. Report whatever n results and the power it buys.**

Same rule as round 32, for the same reason: any count-based stop licences quitting early on a good run
and padding a thin one.

## Predictions

**P6 (new, the round's point) — the body arm's wrong-at-write rate is HIGHER than the committed-document
arm's 3.45 %.** Bodies pass through no `validate.sh`, no gate, no diff review, and no second reader.
If gating and review do anything at all, the ungated channel should be worse. *Falsified* if the body
rate is at or below 3.45 % at an n that can distinguish them — which the power calculation will state
rather than assume.

**P7 (new) — this population yields n ≥ 130**, and so can resolve P1 where the committed documents
could not. 109 bodies against 155 lines, and bodies are far denser in figures than a diff line.
*Falsified* if n < 130, in which case **the question is dropped**, not widened a second time.

**P2 (carried) — scope is the dominant cause among wrong claims.** Round 32 found scope in 2 of 2 on a
sample too small to mean anything. This is the first arm that might have the numbers.

**P9 (new) — bodies that were later edited have a higher wrong-at-write rate than bodies never
edited.** Registered because it sounds like a finding and is mostly a **selection effect**: a body is
usually edited *because* something was wrong with it. It is registered so that if it holds it is
reported as tautological rather than as insight, and if it fails — if never-edited bodies are just as
wrong — that is genuinely informative, because it means the errors that got caught are not the errors
that exist.

## What this round cannot answer

- **Whether bodies and documents are commensurable.** A PR body argues; a registry row states. The
  same rule applied to both may be measuring prose density as much as accuracy. Disclosed **before**
  the measurement, and the reason P6 is stated as a comparison rather than as an absolute.
- **Author effects.** Every body in this population has the same author. Nothing here generalises to
  a repo with several.
- **Whether editing history is complete.** `userContentEdits` is trusted, not audited; it cannot be
  cross-checked against anything, unlike a git object.
- **Whether a fix would work.** Nothing is gated this round regardless of outcome. Rounds 29–32 each
  declined to build on an unresolved premise, and a fourth consecutive decline is still cheaper than
  building on one.
