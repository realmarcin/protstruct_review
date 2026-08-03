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

## The fetch, and the canary

**13 entries attempted, 10 kept.** Three were rejected at fetch time, none of them expensively:

| entry | rejected for | cost |
|---|---|---|
| 3JAH | model 26 MB exceeds `--max-model-mb 8` | one model download |
| 6JHS | map 415 MB exceeds `--max-map-mb 300` | one map download |
| 10TQ | **formal charges** absent from the electron scattering table (`O1-×36`) | one model download |

10TQ is the round-16/18 screen working on live data: it would previously have cost a 200–300 MB map
download and a `real_space_refine` attempt before failing. The ligand screen rejected nothing this
round. All 13 outcomes — the 10 kept as well as the 3 rejected — are recorded in
`ref/research/data/em_fetch_attrition.tsv`, with the charge inventory that produced the refusal.

The 10 kept entries span **3.05–3.45 Å**, come from **10 distinct publications**, and overlap no
prior entry.

### Canary

One entry (10DP, the smallest map at 16 MB) was run **end to end through the same script, the same
cache and the same committed TSV** before the other nine were launched. Verified on side effects
rather than exit code:

| check | result |
|---|---|
| benchmark JSON holds a complete row | ✅ CC_mask 0.7554 → 0.9030, `d_FSC_model` −0.363 % |
| committed TSV grew by exactly one row | ✅ `+1 insertion`, no duplicate |
| that row's values are non-empty | ✅ pre, post, Δ and both `d_FSC_model` values written |
| the `--round 19` label was written | ✅ |
| the refined model is on disk and non-empty | ✅ 2 087 961 bytes |

**What the canary did not exercise**, and is therefore still unverified going into the batch: the
larger maps (131–187 MB) under time and memory pressure, and both refinement-stage failure paths —
no entry in this set carries an unparameterised ligand or a charge, so P5 is tested by the batch, not
by the canary.

## Results

**10 of 10 processed. No skips at any stage.**

| entry | d_min | CC_mask pre → post | CC_mask Δ | `d_FSC_model` |
|---|---:|---|---:|---:|
| 36QD | 3.05 Å | 0.8922 → 0.8925 | +0.0003 | 0.000 % |
| 6IFU | 3.05 Å | 0.7957 → 0.8204 | +0.0247 | −0.113 % |
| 6FKF | 3.15 Å | 0.7734 → 0.8067 | +0.0333 | 0.000 % |
| 6LX3 | 3.15 Å | 0.8494 → 0.8645 | +0.0151 | **+0.277 %** |
| 6O1M | 3.15 Å | 0.7779 → 0.8110 | +0.0331 | −1.362 % |
| 10DP | 3.25 Å | 0.7554 → 0.9030 | **+0.1476** | −0.363 % |
| 13LT | 3.25 Å | 0.8036 → 0.7658 | **−0.0378** | −0.041 % |
| 11FW | 3.35 Å | 0.8324 → 0.8338 | +0.0014 | **+0.012 %** |
| 12QJ | 3.35 Å | 0.5901 → 0.6192 | +0.0291 | −0.309 % |
| 5O5J | 3.45 Å | 0.8734 → 0.8550 | −0.0184 | −0.109 % |

**CC_mask: 2 of 10 degraded, worst −0.0378** (1.59× headroom against the −0.06 band).
**`d_FSC_model`: 2 of 10 degraded, worst +0.277 %** (18× headroom against the 5 % band).

| # | Prediction | Outcome |
|---|---|---|
| P1 | ≥ 1 `d_FSC_model` degradation | ✅ 2 |
| P2 | the 5 % band holds | ✅ worst +0.277 %, **18× headroom** |
| P3 | CC_mask −0.06 holds | ✅ worst −0.0378 |
| **P4** | **largest degradation > 1.1 %** | ❌ **falsified — largest is +0.277 %** |
| P5 | zero refinement-stage losses | ✅ **0 of 10**, no skips at all |
| P6 | median \|CC_mask Δ\| in [0.010, 0.040] | ✅ **0.0269** |

## P4 is the round's finding, and it partly retracts round 16's

Round 16 registered the same threshold and **confirmed** it: 10ME degraded `d_FSC_model` by +1.476 %,
clearing 1.1 %, and round 16 concluded that round 13's "only one of 8 degradations exceeds 1.1 %"
had *described its own high-resolution set* — that **the tail was sampled thinly rather than being
thin**.

Round 19 sampled the low-resolution regime again, ten fresh entries in the window that produced
10BU itself, and got **two degradations of +0.012 % and +0.277 %.** P4 was well calibrated at 60 %
— two degradations at a ~33 % chance each of clearing 1.1 % gives ~62 % — and it lost.

With the full record now at **8 degradations in 36 measurements**:

```
+0.012  +0.018  +0.022  +0.036  +0.277  +0.444  +1.476  +4.786
median 0.157 %      2 of 8 exceed 1.1 % (25 %)      1 of 8 exceeds 4 %
```

The honest reading is **both halves at once**: the tail was sampled thinly *and* it is thin. Round
16's correction was right that the earlier record under-represented large degradations; it was too
strong in implying they are routine. A quarter of degradations exceed 1.1 %, and a degradation
happens 22 % of the time — so a given entry clears 1.1 % about **6 %** of the time.

## What this does to 10BU, and why the band should not move

10BU now stands **3.24× above the next-largest degradation ever recorded** and **30.6× the median**.
Its own window has since been sampled 22 times:

| 3.0–3.5 Å window | value |
|---|---|
| `d_FSC_model` measurements | 22 |
| degradations | 4 |
| worst | **+4.786 % (10BU)** |
| **second worst** | **+0.277 % (6LX3) — 17× smaller** |

It is tempting to call 10BU an outlier and tighten the band. **That would be wrong**, for a reason
round 17 established: 10BU was re-run from a clean directory and reproduced **byte-identically** —
same refined-model MD5, same FSC crossings to full float precision. It is not an estimator artefact,
a parsing error, or a fluke of one run. It is a real, reproducible degradation that any tightened
band would fail on immediately.

So the band's position is now precisely characterised rather than merely defended: **`× 1.05` sits
1.0448× above one verified extreme, and roughly 18× above everything else.** Every clause below the
extreme is comfortable; the band exists for one entry, and that entry is real. Keeping it is the
conservative choice, and this round is the evidence that the choice is not costing detection power
across the rest of the distribution — 9 of the 10 entries here moved `d_FSC_model` by under 0.4 % (only 6O1M, at −1.362 %, moved more).

## Two other things the entries showed

**The benchmark's premise fails harder than before.** 10DP gained **+0.1476** CC_mask on a null
re-refinement — the **largest improvement ever recorded in this series**, beating 10EH's +0.1268
from round 15. The §4 benchmark assumes a deposited model sits at its own optimum, so whatever a null
re-refinement moves is the floor a band must clear. A model that gains 0.15 in CC_mask was not at its
optimum, and its Δ mixes refinement behaviour with deposition headroom. Round 14 recorded this as a
scope limit; it is now twice as large.

**12QJ starts at CC_mask 0.5901**, the lowest starting value in the whole 69-entry set, and still
improved (+0.0291). Recorded because the set's low-fit end is thin and now has a named member.

## Attrition: the screens have moved the cost, as designed

| stage | round 19 | rounds 14–16 |
|---|---|---|
| rejected at **fetch** (cheap) | **3 of 13** — 1 charge, 2 size caps | 0 |
| lost at **refinement** (expensive) | **0 of 10** | **6 of 31** |

P5 held. Both causes that produced all six of the rounds-14–16 refinement failures are now screened
before the map download, and this round paid nothing for them. The one entry that would have been a
refinement failure under the old pipeline — 10TQ, `O1-×36` — cost a 0.5 MB model download instead of
a 200 MB map and a multi-hour refinement.

## Applied

> **No band changed.** `d_FSC_model` holds at 5 % (worst this round +0.277 %; worst overall still
> 10BU's +4.786 % at **1.0448×**). CC_mask `≥ 3.0 Å` holds at −0.06 (worst this round −0.0378).
>
> **The EM set is 69 entries**, with **8 `d_FSC_model` degradations in 36 measurements** and
> **17 CC_mask degradations among 58 recorded deltas** (17–22 including the five measured but never
> written down).

## Self-review findings, filed as issues

Reviewing this PR's own diff turned up four defects, all introduced by round 19's edits and all fixed
in the same PR ([#71](https://github.com/realmarcin/protstruct_review/issues/71)–[#74](https://github.com/realmarcin/protstruct_review/issues/74)):

- **#71** the §4 map-model row quoted **two different set sizes** — the CC_mask half updated to 69,
  the `d_FSC_model` half left at 53.
- **#72** `ρ = +0.397 over 44 entries` was round-16 vintage and unlabelled, and a second `44` was
  being used as a *live* denominator. Recomputed on the grown set: **ρ = +0.361, n = 58, p = 0.005** —
  the correlation survives round 19's ten entries essentially unchanged, which is worth more than the
  relabelling would have been.
- **#73** round 14's premise-failure lesson still cited 10EH's +0.1268 when 10DP's +0.1476 now
  supersedes it.
- **#74** a doubled parenthetical left the counting argument unreadable.

A second review pass, run against the rebuilt branch after #69 merged, found three more
([#83](https://github.com/realmarcin/protstruct_review/issues/83)–[#85](https://github.com/realmarcin/protstruct_review/issues/85)),
also fixed here:

- **#84** — the §4 EM set size went **53 → 69** for a round that added **10** entries, because the
  headline silently switched from the *refinement-attempt* count to the *named-entry* count. Both are
  computable from the same file and neither is wrong; presenting the change as "+10 this round" was.
  The row now states all four denominators (69 named / 63 attempted / 58 with a Δ / 35 fully
  measured) so a later round cannot re-drift.
- **#85** — "8 of the 10 entries moved `d_FSC_model` by under 0.4 %" was an off-by-one; it is 9,
  with only 6O1M at −1.362 % moving more. The error understated this round's own case.
- **#83** — the backlog header was stamped 2026-08-01 while describing events from 08-03, and its
  "no issues open" clause read as current while four were open.

The conflict resolution that rebuilt this branch on `main` was checked separately and **lost
nothing**: all seven of #69's late fixes survive.

Three of the four are the same failure: **round 19 updated one instance of a figure and missed its
siblings in the same row.** That is round 18's "when the set grows, re-test every clause it backs"
applied to prose rather than to clauses — and it argues the §4 map-model row is now too long to edit
safely by hand.

## Scope limits

- **P4's falsification is two degradations, not a distribution.** This round produced only two
  `d_FSC_model` degradations; that they were both small is weak evidence about the tail on its own,
  and the reading above rests on the pooled record of 8.
- **No rate claim is made.** Round 19's 2-of-10 is not compared with round 16's 4-of-9 or round 15's
  4-of-8; round 17 established that comparison needs ~20 entries per arm.
- The 3.0–3.5 Å window replicated its median CC_mask excursion (P6), but that is one interval hit on
  n = 10, not a validation of the round-16 resolution bins generally.
- **The canary did not exercise the refinement-stage failure paths**, because no entry in the set
  carried a ligand or a charge. P5 held on a set that contained nothing to trip it — it confirms the
  fetch screens caught what was there, not that the refinement-stage reporting still works.

## Not asked

**No rate question.** Round 17 established that comparing per-round degradation *rates* needs ~20
entries per arm against the 8–10 a round builds, and that the apparent 4/8-vs-1/9 difference was
p = 0.131. Whatever this round's degradation count is, it will not be compared with another round's
as if the difference meant something. Magnitude is what re-fits a band.
