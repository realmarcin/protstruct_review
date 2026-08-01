# Per-entry benchmark data

Cumulative, committed per-entry values. `scripts/bench_refinement_deltas_em.py` appends here on
every run (`--results-tsv`), so an entry measured once stays identifiable.

## `em_refinement_deltas.tsv`

One row per EM entry ever attempted. The `status` column says what the row is:

| status | meaning |
|---|---|
| `measured` | full pre/post values, from rounds 14 onward which recorded them |
| `delta-only` | Δ published in round 12's table; per-entry pre/post never recorded |
| `d_FSC only` | 9H7U — round 13 published its `d_FSC_model` but not its CC_mask Δ |
| `skipped: …` | attempted and unprocessable, with the reason |
| `LOST: …` | **measured, counted in the published totals, and unidentifiable** |

### The `round` column

Added in round 17, which needed it: no cross-round comparison is reproducible if the rounds
themselves have to be reconstructed by matching prose in the audit trails against row order in this
file. Every analysis of *when* a value was measured — attrition per round, degradation rate per
round, whether a window has been sampled already — depends on it.

Values are `12`–`17`, plus `<=12` for three `real_space_refine` failures (9VXE, 13GH, 9TZY) that
rounds 12 and 13 both report as cumulative totals "across the series" without saying which round
attempted them. `<=12` is written rather than a guess: the bound is what the record supports.

## Why the `LOST` rows exist

Round 13 measured 6 entries and named 2. Results went only to a JSON in a temporary cache, so when
that cache was cleared the other 4 entries became unrecoverable — not their values, their
*identities*. They cannot be re-run, because nothing records what they were.

This is why the CC_mask degradation count is **14–19** rather than a number: 14 verifiable
degradations among 39 entries with a recorded Δ, plus 5 entries (9H7U and the 4 `LOST` rows) whose Δ
was measured but never written down. Since a one-sided band's evidence *is* its degradation count,
an unrecoverable identity is an unrecoverable piece of evidence.

`d_FSC_model` is affected the same way: round 13 reported 8 degradations among 27 measurements but
published only 9VAM's magnitude (+4.28 %), so the per-entry values behind that 8 are also gone.

Prose in an audit trail is not a record. It names the entries the author found interesting, which is
precisely the subset that cannot be used to recount anything.

## `em_fetch_attrition.tsv`

The other half of the same record, added in round 18 to close the two gaps round 17 found.

`em_refinement_deltas.tsv` records entries from the refinement attempt onward. That is now the
smaller half of attrition: both screens deliberately reject entries **before** any refinement, so
their rejections were landing only in the fetch run's `entries.json`, inside a temporary cache.
`fetch_em_entries.py` now appends every fetch outcome here — kept and rejected alike — with the
charge and ligand inventories the screens actually saw.

| column | meaning |
|---|---|
| `outcome` | `kept`, `rejected: <reason>`, or `unrecorded: …` for the backfilled rows |
| `charges` | what the charge screen saw, on kept entries too — not only on the fatal ones |
| `unparameterised` | components with no monomer-library restraints, as `CODE×atoms` |

**Why kept entries are recorded, not just rejections.** An attrition *rate* needs a denominator.
Recording only failures gives the numerator and leaves the rate unrecoverable — the same shape as
recording only the worst case and leaving the distribution unrecoverable.

### The backfilled `unrecorded` rows

Six models were found on disk in rounds 14's and 16's caches that appear in no record at all: they
were downloaded and never benchmarked, and **nothing says why**. Four (10GJ, 10GK, 10GL, 10GM) carry
an unparameterised ligand and would fail the round-18 screen; 10TP carries charges the screen
refuses; 10UA passes both and has no visible reason to have been dropped.

They are recorded as `unrecorded` rather than as rejections, because the screen verdicts above were
computed in round 18 and are **not** the reason those entries were dropped at the time — the ligand
screen did not exist yet. Writing a plausible reason into a record is how a record stops being one.
