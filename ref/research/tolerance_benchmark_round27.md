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

## #160 — a lookup sized to today's values

`spell()` converts the round number to the form the summary file uses. Its tens table held exactly
`{20: "twenty", 30: "thirty"}`, so it raised a bare `KeyError` below 20 and at 40 and above — the gate
would crash with a traceback at round 40, thirteen rounds out.

It fails **closed**, which is the right direction, but with a stack trace where a diagnosis belongs,
and a gate that crashes is one somebody disables rather than debugs. Now covers 20–99 and refuses
anything else by name.

The shape is the round's own recurring one, a third time: **code sized to the range the repo currently
occupies is a fixture pretending to be a function.** `EXPECTED_DEFECT_CLAIMS` is the same instinct
(and is disclosed below), and both test fixtures had already been corrected for it in this round.

## #161 — three more, and the same shape a fourth time

A review enumerating the input space found three defects in the new script. One is a **false pass**:

| | defect | direction |
|---|---|---|
| **1** | a range claimed twice took the **last** value, so a wrong round-table figure passed whenever a later sentence restated it correctly | **false pass** |
| **2** | the `\|---\|` separator was assumed rather than checked, so a malformed table lost its first data row | false MISSING (loud) |
| **3** | *any* digit in the lessons Round cell credited that round — an issue reference such as `26, cf. issue #27` covered round 27 with no entry behind it | false OK |

The first matters most, and it is the exact failure this check exists to prevent: these documents
restate figures constantly, so a correct restatement three paragraphs later would have silently
excused a wrong round-table row. A range claimed with two different numbers is now a `CONFLICT`;
claimed twice with the *same* number it stays `OK`.

**This is the fourth naming of one shape in this round.** Each of the three was written against the
input these files happen to contain today: every range claimed exactly once, every table well-formed,
every Round cell holding only round numbers. The hardcoded test fixtures, `spell()`'s lookup table
and now the parsing itself — all the same instinct, and only enumeration found them. Reading found
none of the four.

## #162 — the fix for #161 had the shape a fifth time

`round_tokens`, added by #161, expands `N–M` ranges. A **descending** range covered nothing:
`range(5, 2)` is empty, and the range text is stripped before the fallback digit scan, so both
endpoints were lost as well — **strictly worse than the bare digit scan #161 replaced**, which at
least credited 5 and 1.

Latent, loud, no masked gap. Filed and fixed anyway because it is a regression rather than an
inherited gap, and because the cause is the round's recurring one for the fifth time: the expansion
was written for the ranges this file happens to contain, and every one of them ascends.

Endpoints are now ordered before expanding — a descending range is a typo, and reading it as the range
its author meant is never less safe than the old behaviour.

## The #157 fix earned itself immediately

Adding a candidate-options table to `NEXT_TASKS.md` put a **second table** in the file — the exact
construct that false-passed before #157, when the check matched any `| … |` line anywhere. Under the
scoped check it is inert: the round table still resolves to exactly its 27 rows, every first cell a
digit, and nothing from the new table leaks in.

That is not a hypothetical partition being defended; it is the first ordinary edit after the fix
landing on the case the fix was for.

## #163 — the ninth miscount, and what the gate does not reach

Reviewing the candidate table added at the end of this round found two wrong counts.

**Mine, and new.** The table said the `scripts/` audit had *"found defects every time — 12, then 5,
then 5"*. Forty lines below, the same file says **12, then 2, then 5**. I wrote pass 6's figure for
pass 4 — the identical mistake #158 corrected three commits earlier — in a table whose subject is how
reliably audits find defects. Ninth of the class.

**Pre-existing.** The 1.074 fence base rate was stated as *"3 of 60"* in one place and *"4 of 60 =
6.7 %"* in another. Derived from the data: 4 of 60 above 1.074, 2 of 60 above 1.3. So 4 is right, the
registry already said so, and `NEXT_TASKS` was contradicting both the registry and itself. My new
table happened to quote 6.7 % — the correct side of a contradiction I had not noticed, which is luck
rather than checking.

**Neither would have been caught by this round's gate.** `check_summary_coverage.py` derives only
`**N defects** (#A–#B)` claims and the spelled-out round count; neither of these matches that form.
The scope limits below already said only four figures are derived. This is what that limitation costs,
measured two commits after it was written rather than asserted.

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
