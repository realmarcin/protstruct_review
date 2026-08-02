# Tolerance benchmark — round 19: back to testing bands

Rounds 17 and 18 added **no entries to any benchmark**. They audited the registry's records, fixed
the mechanism that lost them, and verified one entry byte-for-byte. All of that was worth doing and
none of it tested a tolerance. This round goes back to the series' actual work.

The target is the thinnest margin in the file. `d_FSC_model` is gated at `post ≤ pre × 1.05` and the
worst degradation on record is **+4.786 %** (10BU, 3.20 Å) — **1.0448× headroom**. Round 17 verified
that entry reproduces byte-identically, which makes it *certain* rather than *safe*: the band is
proved to sit 4.5 % above a real observation.

## Method, fixed before the data

```bash
python3 scripts/fetch_em_entries.py --cache <dir> --min-res 3.0 --max-res 3.5 \
    --limit 10 --strata 10 --per-stratum 6 --max-map-mb 300 --max-model-mb 8 \
    --round 19 --exclude <every prior entry> --json fetched.json
python3 scripts/bench_refinement_deltas_em.py --cache <dir> --round 19 --json out.json
```

**Window 3.0–3.5 Å**, chosen because round 16 measured it as carrying the largest *median* CC_mask
excursion (0.0232 over 18 entries) even though 3.5–4.2 Å holds the largest single one. Both
`d_FSC_model` degradations in the large class so far (10BU 3.20 Å, 10RI 3.60 Å) sit at or just past
its edge.

**Target 10 entries, every prior entry excluded** — the 58 in `em_refinement_deltas.tsv` plus the 6
in `em_fetch_attrition.tsv`. **Every entry attempted is reported**, whatever it does; the stopping
rule is the `--limit`, fixed above, not a look at the results.

**One entry is run end to end as a canary before the rest are launched**, through the same script and
the same cache, with the committed TSV checked for a real appended row. A batch of ten multi-hour
refinements is exactly the case where a silent misconfiguration costs ten times what it should.

## Baseline, as the record stands

| quantity | state |
|---|---|
| `d_FSC_model` degradations | **6 of 26** measurements (23 %), median **0.240 %**, max **4.786 %** |
| `d_FSC_model` band | `× 1.05`, headroom **1.0448×** |
| CC_mask, 3.0–3.5 Å | 23 entries, **8 degraded** (35 %), worst **−0.0475**, median \|Δ\| **0.0244** |
| CC_mask band, ≥ 3.0 Å | **−0.06**, headroom 1.26× against that worst |

The six `d_FSC_model` magnitudes are, for the first time, a **complete** record rather than the
alarming subset — rounds 14 onward wrote down every value. Round 16's prior was wrong precisely
because it reasoned from the incomplete version, so the probabilities below are set from this table
and stated explicitly.

## Predictions, registered before the data

| # | Prediction | Falsified if | P |
|---|---|---|---|
| **P1** | At least one entry degrades `d_FSC_model`. | None do. | 90 % |
| **P2** | **The 5 % band holds** — no degradation exceeds 5 %. | Any does. | **70 %** |
| **P3** | CC_mask `≥ 3.0 Å` holds at −0.06. | Any entry degrades CC_mask by more than 0.06. | 85 % |
| **P4** | The largest `d_FSC_model` degradation **exceeds 1.1 %**. | Every degradation is ≤ 1.1 %. | 60 % |
| **P5** | **Zero entries are lost at the refinement stage** to an unparameterised ligand or a charge. | Any entry reaches `real_space_refine` and fails for either cause. | 85 % |
| **P6** | This round's median \|CC_mask Δ\| lands in **[0.010, 0.040]**. | It falls outside that interval. | 70 % |

**How P2's 70 % was set, since round 16's equivalent was wrong by a factor of four.** At a 23 %
degradation rate, 10 entries should produce ~2.3 degradations. The chance a fresh draw exceeds the
maximum of six existing ones is ~1/7 by symmetry, so P(at least one exceeds 10BU) ≈ 1 − (6/7)^2.3 ≈
30 %; clearing 5 % rather than 4.786 % is slightly harder still. That puts P2 near 70 % — **at risk,
and the reason this window was chosen.** The estimate now rests on a complete magnitude record, which
is the one thing round 16's did not.

**P4 is the informative one.** Two of the six recorded degradations exceed 1.1 %, so this asks
whether the large class is a real, repeatable feature of the low-resolution regime or an artefact of
which entries happened to be drawn. It was confirmed once already, in round 16.

**P5 tests round 18's work rather than a tolerance.** Both attrition causes are now screened before
the map download, so the expensive path should see none of them. A failure here means a screen does
not cover what it claims to — which is more useful than another entry.

**P6 is a replication.** Round 16's 3.0–3.5 Å median (0.0232) was a post-hoc bin with n = 18. If a
fresh, independently drawn set lands in the same range, the bin describes the quantity; if not, it
described that set. The interval is fixed here, before the draw.

## Not asked

**No rate question.** Round 17 established that comparing per-round degradation *rates* needs ~20
entries per arm against the 8–10 a round builds, and that the apparent 4/8-vs-1/9 difference was
p = 0.131. Whatever this round's degradation count is, it will not be compared with another round's
as if the difference meant something. Magnitude is what re-fits a band.
