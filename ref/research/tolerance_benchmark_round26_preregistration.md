# Round 26 — pre-registration

Registered **before any measurement**, in a commit containing no results. Round 25 closed with three
statements that are claims rather than conclusions; this round tests them.

## What round 25 left open

1. **#136's class — one rule, two copies.** The regression came from the log-naming rule existing in
   both the writer (`measure()`) and the reader (`collect()`). Pass 3 grepped cache *filenames* and
   found no sibling. Filenames are one instance of the class, not the class.
2. **Two miscounts (#130, #135)** came from recounting from memory. The repo already has the rule —
   *every figure a document quotes must come from a committed, re-runnable script* — and it has never
   applied to the round documents' own self-referential counts.
3. **"Twelve on the first pass is a lower bound, not a total."** Stated, not tested.

## Predictions

**P1 — a fourth pass finds at least one new MAJOR defect in `scripts/`.**
This is the direct test of "twelve is a lower bound". Major = would change a computed result, hide an
error, or make a document claim something untrue — the same bar as passes 1–3. Style, naming and
wording do not count.

*Falsified if* pass 4 returns zero major defects. That is a real result and would mean the first three
passes were closer to exhaustive than round 25 claimed, and the "lower bound" caveat should be
softened rather than repeated.

**P2 — the status vocabulary is currently consistent: 0 violations in the committed TSV.**
`ref/research/data/em_refinement_deltas.tsv`'s `status` column is written by `append_results` and read
by at least four predicates in `check_registry_figures.py` (`startswith("skipped")`,
`startswith("screened only")`, `== "measured"`). No single definition exists. I predict **every one of
the 97 rows already matches a known status** — i.e. this is a guard against future drift, not a fix
for a present defect.

*If violated*, some row's status is already unrecognised by one of the predicates, and at least one
published denominator is wrong today. That would be a live high-severity finding, so state it now:
**this prediction failing is the more consequential outcome.**

**P3 — round 25's document survives its own new check: 0 discrepancies.**
The self-count gate will be applied to `tolerance_benchmark_round25.md` as committed. Its counts were
corrected under #130 and #135. I predict the gate finds nothing further.

*If violated*, the corrections were incomplete — which is the more interesting result, because both
were found by review rather than by a check, and a third would show review is not enough.

**P4 — the duplicated-rule audit finds at least one instance beyond filenames, but fewer than five.**
The status vocabulary above is already known to be one, so the interesting half is the upper bound: I
predict this is a small, enumerable class in this repo, not a pervasive one.

*Falsified downward* if the status vocabulary is the only instance (the class is narrower than #136
suggested). *Falsified upward* at five or more, which would mean duplication is systemic and a
one-off fix is the wrong response.

## What this round cannot answer

- **Whether pass 4 is exhaustive.** If P1 confirms, the same argument applies to pass 4 and the honest
  statement remains "lower bound" at every depth. This round can show twelve was not a total; it
  cannot produce a total.
- **Whether the self-count gate generalises to earlier rounds.** It will be written against round 25's
  vocabulary. Rounds 1–24 have their own phrasings and are not in scope; if the gate only ever covers
  one document it is worth less than it looks, and that will be stated rather than glossed.
- **Anything requiring the network at gate time.** `validate.sh` is offline today and stays offline. A
  check that silently skips when `gh` is unavailable would be a guard that does not guard, so the
  issue-derived facts must be committed as data and refreshed deliberately, the way
  `em_refinement_deltas.tsv` already works.

## Method, fixed in advance

- Pass 4 uses **different lenses** from passes 1–3, not a repeat: passes 1–3 read for silent failure,
  wrong quantity and guard gaps. Pass 4 reads for **duplicated derivations, contracts between two
  files, and assumptions about input shape**. A repeat of the same lens would test reviewer variance,
  not depth.
- The findings TSV is generated from `gh` by a committed script, not typed. Any count in the round
  document must come from it.
- Every finding is verified by hand before it is filed, as in rounds 25's passes.
