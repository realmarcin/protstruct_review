# Tolerance benchmark — round 16: the thinnest band in the file

Round 15 left `d_FSC_model` at **1.045× headroom** — 10BU degraded it by +4.79 % against a 5 % band —
making it the tightest margin in `ref/thresholds_and_standards.md`. Any future degradation above
+4.79 % breaks it. This round targets that.

```bash
python3 scripts/fetch_em_entries.py --cache <dir> --min-res 3.0 --max-res 4.2 --limit 12 \
    --strata 12 --per-stratum 5 --max-map-mb 300 --max-model-mb 8 --exclude <every prior entry>
python3 scripts/bench_refinement_deltas_em.py --cache <dir> --json out.json
```

The window is 3.0–4.2 Å, slightly wider than round 15's, because both `d_FSC_model` degradations so
far (10BU 3.20 Å, 10RI 3.60 Å) came from the low-resolution regime and round 14's 2.4–3.1 Å window
produced none.

## 0. The recovery item was infeasible, and the cause is now fixed

The backlog's second item asked to recover per-entry values for rounds 5 and 9–13, since the CC_mask
degradation count could not otherwise be stated as a number. **It cannot be done.**

Round 13 measured 6 entries and **named two**: 9O9K's CC_mask Δ and 9H7U's `d_FSC_model`. The other
four appear nowhere in this repo. Results were written only to a JSON inside a temporary cache, so
clearing that cache destroyed not the values but the **identities** — those entries cannot be re-run
because nothing records what they were. The same holds for the 8 `d_FSC_model` degradations round 13
counted while publishing only 9VAM's magnitude.

So the count is permanently **14–19**: 14 verifiable degradations among 39 entries with a recorded Δ,
plus 5 entries measured but never written down. Since a one-sided band's evidence *is* its degradation
count, an unrecoverable identity is an unrecoverable piece of evidence.

The cause is fixed rather than the symptom. `bench_refinement_deltas_em.py` now appends every
per-entry value to a committed TSV, `ref/research/data/em_refinement_deltas.tsv`, deduplicated by id.
It is backfilled with everything recoverable, and the four unidentifiable entries are listed as
`LOST` rows — visible, because a gap that is visible can bound a claim.

**Prose in an audit trail is not a record.** It names the entries an author found interesting, which
is exactly the subset that cannot be used to recount anything.

## Predictions, registered before the results

Baseline: **10 `d_FSC_model` degradations in 44 entries (23 %)**. Magnitudes are known for only three
— 9VAM +4.28 %, 10BU +4.79 %, 10RI +0.45 % — and round 13 recorded that of its 8, only one exceeded
1.1 %. The band is `post ≤ pre × 1.05`.

| # | Prediction | Falsified if |
|---|---|---|
| **P1** | At least one entry degrades `d_FSC_model`. | None do. |
| **P2** | **The 5 % band holds** — no degradation exceeds 5 %. | Any degradation exceeds 5 %. |
| **P3** | The largest `d_FSC_model` degradation exceeds **1.1 %**, i.e. this window keeps producing degradations in the large class rather than the small one. | Every degradation is ≤ 1.1 %. |
| **P4** | CC_mask `≥ 3.0 Å` holds at −0.06. | Any entry degrades CC_mask by more than 0.06. |
| **P5** | At least one entry is skipped for an entry property (ligand or scattering table), continuing the ~17 % attrition. | All fetched entries process cleanly. |

**P2 is the one at risk.** With ~23 % of entries degrading and 2 of the 3 known magnitudes above
4 %, a dozen entries should produce roughly 3 degradations, and the band has 1.045× headroom over the
worst yet seen. I put P2 at **better than even but well short of safe** — nearer 60 % than 90 %.

**P3 is the informative one.** If the low-resolution window keeps yielding degradations above 1.1 %,
then round 13's "only one of 8 exceeds 1.1 %" describes its own high-resolution set rather than the
quantity, and the tail is not thin — it was sampled thinly. If instead the new degradations come in
small, the 5 % band is safer than 1.045× suggests, because the worst cases would be rare rather than
routine.

**P5 is registered to make attrition a measurement rather than an anecdote.** Three of 18 entries in
rounds 14–15 were unprocessable; this round should see roughly two.

## Results

*(pending — refinements running)*
