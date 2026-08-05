# Round 30 — pre-registration

Registered **before the classification**, in a commit containing no results.

## The proposal under test

Round 28 measured the round trails at ~6.2 % wrong against the registry's ~1.1 %, concluded *"being
re-read is the constraint, not coverage"*, and proposed a convention: **a figure in a finished trail
is a historical snapshot and should be written as one** — with its denominator and its date. It
deliberately did not implement it (#183).

The convention helps exactly one failure mode: a figure that was **correct when written** and rotted
because nobody reread it. It does nothing for a figure that was **wrong at write time**.

Round 29 set out to close a real gap and declined after measuring. This round asks the same question
before building, rather than after.

## Method, fixed in advance

Classify **every figure found wrong in a round trail or summary file across rounds 24–29** into:

- **STALE** — demonstrably correct when written; the source moved underneath it.
- **WRONG-AT-WRITE** — never correct; the value did not match its source on the day.
- **UNDECIDABLE** — cannot establish which, from the committed history.

Evidence must be the **committed record** — `git log -S` on the figure, the round document that
introduced it, and the data file as it stood at that commit — not recollection. Each classification
names the commit that settles it.

The population is the issues already filed: #130, #135, #147, #150, #155, #156, #158, #163, #164,
#165, #166, #167, #169–#174, #176, #177, #179, #182. Figures wrong in **scripts** rather than prose
are out of scope; this is about documents.

## Predictions

**P1 — STALE does not reach a majority.** Of the classifiable figures, fewer than half will be stale.

*Falsified* if stale figures are a majority, which would mean the convention targets the dominant
failure and should be written.

The four errors round 28 itself found split two-two, which is the basis for predicting no majority —
but four is not a sample, and the wider population may look nothing like it.

**P2 — the dominant kind is WRONG-AT-WRITE, and its dominant cause is a count restated from memory
when the source was one command away.** This is a claim about *cause*, not just kind, and it is the
one that determines what would actually help.

*Falsified* if wrong-at-write figures are mostly something else — transcription slips, arithmetic
errors, or misread sources.

**P3 — more than two figures will be UNDECIDABLE.** Several were introduced in squashed commits
whose intermediate states are gone.

*Falsified* if the committed history settles all but two or fewer.

## What this round cannot answer

- **Whether the convention would have prevented the stale ones in practice.** It can show what fraction
  the convention *could* address, not whether a reader would have heeded it. That distinction must be
  stated in the result rather than glossed.
- **Anything about trails before round 24.** The issue record starts at #130 and the earlier rounds'
  figures were never audited this way.
- **The rate.** This classifies figures *already known wrong*. It says nothing about how many wrong
  figures remain unfound, which round 28 established is a lower bound in any case.
