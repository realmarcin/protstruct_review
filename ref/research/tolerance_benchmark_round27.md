# Tolerance benchmark — round 27: gating the counts, and the gate that shipped two false passes

Eight self-referential miscounts had shipped across rounds 24–26 — #130, #135, #147, #150, #155,
#156, and two more in #158. Every one was a number restated from memory when the source was
committed and one command away. This round makes them checkable.

**No tolerance, band or measurement changed.** No registry figure is touched.

## What was gated

`scripts/check_summary_coverage.py` checks the two summary files against the record:

| check | kind | what it catches |
|---|---|---|
| round coverage in `NEXT_TASKS.md` | representation | a round with no row |
| round coverage in `lessons.md` | representation | a round with no lesson |
| `**N defects** (#A–#B)` | derivation | #155 — a count that includes the round's own PR |
| `twenty-N rounds of` | derivation | #154 — a round count two rounds behind |

The two kinds are not the same and the difference is stated in the file: **coverage is
representation only** — a pass means the round is not missing, not that its row is right. That
distinction is what #155 walked straight through: round 26 *had* a row, and the row was wrong.

The defect counts work because **the claim carries the range it counts** — `**14 defects**
(#139–#153)` — so the check needs no hardcoded round-to-issue map that could drift on its own. The
record contains issues only, so deriving from it cannot repeat #155's mistake of counting `#141`,
the round's own PR.

## The gate merged one PR earlier had two false passes

#154 added a NEXT_TASKS coverage check and its PR body called it *"representation only, exactly like
its sibling"*. A delegated review — which reported **after** that merge — found both checks matched
any `| … |` line anywhere in the file. Verified:

```
| 27 | unrelated |          in an unrelated "Priority" table   ->  round 27 reported covered
| 27 | [#999](x) | ... |    inside a fenced example block       ->  round 27 reported covered
```

The second is **precisely the class round 26 spent itself hardening `check_round_figures.py`
against** (#151: a quoted literal satisfying a check the prose contradicted). The new gate had no
quotation-awareness at all — not even the imperfect kind its sibling had by then.

Two things went wrong, and they are different:

1. **"Exactly like its sibling" was offered as reassurance and was false.** The lessons check matches
   the round in a row's **last** cell across every table in the file; the new one matched the
   **first**. They shared a flaw from opposite ends. Asserting equivalence to something already
   trusted is a claim to verify, not a reason to stop — the same move that let #142 sit unexamined
   because `oracle_family` was believed schema-enforced.
2. **It was in shell, so it could not be tested.** Both checks were embedded python inside
   `validate.sh`. Nothing exercised their failure modes because nothing *could*. Moving them into a
   script cost a few lines; the tests that come with it are the point, and they are what proved the
   false passes.

Both are fixed by scoping a table to its own header and stripping fenced blocks, and
`scripts/test_summary_coverage.py` now carries a partition map — including the sibling's version of
both attacks, which was exploitable the same way and is fixed with it.

## Two more miscounts, found by the same review

**#158.** `NEXT_TASKS` said the different-lens pass found **5** defects; round 26's trail says
**two**. The 5 is pass 6's figure misapplied.

And the findings-record staleness count disagreed **three ways**:

| source | says |
|---|---|
| round 26 scope limits | twice |
| round 26 body, six sections earlier | *"a third time"* |
| `NEXT_TASKS` | four times |

The scope-limits tally is the one presented as authoritative, and its own body contradicted it —
**#91's shape**, corrected here in *both* files rather than only the one that inherited it, since
leaving the source wrong guarantees the next summary repeats it.

## Two defects in this round's own script, caught before review

- **The rewrite contract was claimed and not implemented.** The docstring said a reworded claim fails;
  rewording `**14 defects** (#139–#153)` to `fourteen defects` made the check *silently disappear*
  from the results. Fixed by pinning the expected ranges, so absence is `MISSING`. This is the "a gate
  that only compares numbers is defeated by a rewrite" lesson, written into a docstring and then not
  honoured by the code beneath it.
- **A failure message mixed two different quantities.** It read *"there are 20 rounds, so it should
  say twenty-six"* — 20 is the number of trail *files*, 26 the highest round, because rounds 1–5 and
  9 have no separate trail. Incoherent as printed.

## The gate caught its own round

Adding round 27's own row to `NEXT_TASKS.md`, a scripted edit left a blank line between it and row 26.
Markdown renders that as two tables; the round-27 row was outside the one the check reads, and the
gate reported `no round-table row for round(s): ['27']`.

That is the #157 fix working on the round that made it — the same "a table ends at the first line that
is not a row" scoping that stopped an unrelated table counting also stops an orphaned row *looking*
like it counts. An orphaned row is the failure this file exists to catch, arriving unprompted within
minutes of the check being written.

## And two of the round's own tests were brittle in the same way

Both negative fixtures hardcoded a value this round then changed, so both quietly stopped testing:

- `ABSENT = ROUNDS + ["27"]` chose round 27 as "a round with no row" — and then round 27 was created,
  turning every negative case into a false pass. Now `999`, which cannot collide.
- The round-count tests substituted the literal `"twenty-six rounds of"`; this round moved the file to
  twenty-seven, so the substitution became a no-op and the negative cases passed without testing
  anything. Now derived from the highest round on disk.

Both were caught by the gate rather than by reading, because the assertions flipped from pass to fail.
The pattern is worth naming: **a test fixture that hardcodes a value the change under test modifies is
a test that stops testing exactly when the change lands.**

## Scope limits

- **Coverage is representation, counts are derivation, and only four figures are derived.** Every
  other number in `NEXT_TASKS.md` is unchecked. Eight miscounts shipped; this catches the two shapes
  that recurred, not the class.
- **The expected-claims list is itself a hand-maintained figure.** `EXPECTED_DEFECT_CLAIMS` must be
  extended when a round adds a count, and nothing enforces that — the same snapshot problem round 26
  recorded for its findings record.
- **#156's claim is not covered.** *"sixth reconcile … and two earlier"* lives in a code comment, is
  derivable from `git log`, and is not checked. Stated rather than left to look covered.
- **The gate does not know what a round's row should say.** `NEXT_TASKS` could describe round 26 as
  anything at all and coverage would pass.
