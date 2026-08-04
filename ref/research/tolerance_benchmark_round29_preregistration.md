# Round 29 — pre-registration

Registered **before writing the check**, in a commit containing no results.

## The claim under test

Round 28 measured the registry at ~1.1 % wrong (2 of ~185 verifiable figures) and recorded its sweep
as **"a lower bound, not a total"**. Both errors it found were **per-entry** figures — values quoted
for a named PDB id — and `scripts/check_registry_figures.py` gates none of those; its 12 `CHECKS` are
all aggregate.

## Prediction

**P1 — a mechanical check over the registry's per-entry figures finds at least one wrong value that
round 28's hand sweep missed.**

*Falsified* if every per-entry figure the check can derive already matches the TSV. That is a real
result and the more useful one for planning: it would mean the hand sweep was effectively complete
over the registry, and would argue **against** extending mechanical coverage further — the same shape
of conclusion round 28 reached for the trails, reached here by measurement rather than by analogy.

**P2 — the per-entry figures the check CANNOT derive outnumber those it can.**

Many registry figures name entries whose values were never recorded per-entry (the `LOST` rows,
round 13's unpublished values, the `delta-only` rows). #167 already found one — 9VAM's 6.10 Å, quoted
from round 12 with no `d_fsc_model_pre` in the file.

*Falsified* if derivable figures outnumber underivable ones. If P2 holds, the honest output of this
round is a **coverage statement** — how much of the registry's per-entry prose is checkable at all —
and not merely a passing gate, because a gate that covers the minority while reporting "OK" overstates
what it verified. That is #116's shape and this round should not repeat it.

## Method, fixed in advance

- Extract every `(PDB id, value)` pair the registry asserts in its §4 map-model row.
- Classify each as **derivable** (the id has that column in `em_refinement_deltas.tsv`) or
  **underivable** (no recorded value), and report both counts. The denominator ships with the
  numerator.
- Compare only the derivable ones; a mismatch is a defect, an underivable one is a coverage gap and
  must be reported as such rather than skipped silently.
- Any figure found wrong is filed and fixed; any *underivable* figure is reported, not "corrected"
  from a value it never had.

## What this round cannot answer

- **Whether the extraction is complete.** A regex over prose will miss forms nobody anticipated, so
  the count of per-entry figures is itself a lower bound — the same caveat as round 28's sweep, and it
  must be stated in the result rather than implied away.
- **Anything outside the §4 map-model row.** §3's rows quote per-entry values too, from sets that are
  committed but not in this TSV. Out of scope, and the scope limit says so.
