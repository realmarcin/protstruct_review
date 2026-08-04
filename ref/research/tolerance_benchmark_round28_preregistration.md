# Round 28 — pre-registration

Registered **before any measurement**, in a commit containing no results.

## The claim under test

Round 27 closed with: *"nine miscounts across four rounds, and the gate now catches two of their
shapes. It helps; it doesn't close the class."*

Both halves are assertions, not measurements. **Nine** is a tally of the miscounts I happened to
notice — every one was found by a reviewer or by me reading, none by a systematic sweep. It is
therefore a lower bound of unknown tightness, and it says nothing about how many wrong numbers sit on
`main` right now.

The instinct after round 27 is to add a third literal→derivation pair. That would be the fourth time
this series mechanised a defect class **before measuring it**, and round 17's lesson is the opposite:
check the power before hunting the mechanism.

## Method, fixed in advance

Sweep every numeric claim in the load-bearing documents and verify each **by hand against its
source**, not by pattern-matching:

    ref/thresholds_and_standards.md      (the registry)
    NEXT_TASKS.md
    ref/research/lessons.md
    ref/research/tolerance_benchmark_round2[4-7].md

A "numeric claim" is a figure the text asserts about the work — a count, a rate, an n, a range
endpoint. Not: tolerance values, resolutions, PDB ids, issue numbers, dates, version strings.

Each claim is classified as **verifiable** (a committed source can settle it) or **unverifiable** (no
source exists), and each verifiable one as **correct** or **wrong**. The denominator is stated with
the numerator, which is this repo's own rule and the one whose breach produced several of the nine.

## Predictions

**P1 — the sweep finds at least one wrong number currently on `main`.**
Direct test of "it doesn't close the class". *Falsified* if every verifiable claim is correct, which
would mean the class is closed in practice and the remaining risk is only prospective.

**P2 — the dominant shape is a figure stated in TWO PLACES that disagree, not a figure that
contradicts the record.** Of the nine, at least three were internal contradictions (#156's nesting,
#158's three-way staleness count, #163's `3 of 60` vs `4 of 60`). Internal disagreement is checkable
**without knowing the right answer**, which is why the shape matters: it needs no derivation and no
hand-maintained expected list.

*Falsified* if wrong-against-record outnumbers self-contradiction among what the sweep finds.

**P3 — more than half of the wrong numbers found will be in documents the round-27 gate already
covers** (`NEXT_TASKS.md`, `lessons.md`), rather than in the registry.
The registry has had a derivation gate since round 24 and 14 checks; the summary files got theirs two
commits ago and it derives four figures. If P3 holds, coverage is the constraint rather than the
existence of a gate.

**P4 — the true count of miscounts across rounds 24–27 is HIGHER than nine.**
Nine is what review happened to catch. *Falsified* if the sweep finds no historical miscount that was
never filed.

## What this round cannot answer

- **Whether the sweep is itself complete.** It is one reader over six documents. The same "lower
  bound, not a total" caveat applies to it as to the `scripts/` audit, and the result must be reported
  that way rather than as a defect density.
- **Anything about documents outside the six.** PR bodies are not in the repo and are excluded;
  #147 and #150 both involved a PR body, so the sweep structurally cannot see that shape.
- **Whether a fix would hold.** Gating comes after the measurement, and only for the shapes the
  measurement says dominate. If P1 is falsified, nothing should be gated at all.
