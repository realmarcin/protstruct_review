# Per-entry benchmark data

Cumulative, committed per-entry values. `scripts/bench_refinement_deltas_em.py` appends here on
every run (`--results-tsv`), so an entry measured once stays identifiable.

## `em_refinement_deltas.tsv`

One row per EM entry ever attempted. The `status` column says what the row is:

| status | meaning |
|---|---|
| `measured` | full pre/post values, from rounds 14–15 which recorded them |
| `delta-only` | Δ published in round 12's table; per-entry pre/post never recorded |
| `d_FSC only` | 9H7U — round 13 published its `d_FSC_model` but not its CC_mask Δ |
| `skipped: …` | attempted and unprocessable, with the reason |
| `LOST: …` | **measured, counted in the published totals, and unidentifiable** |

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
