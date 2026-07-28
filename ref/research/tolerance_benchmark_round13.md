# Round 13 — the thin branch broke, and a band shape was wrong in a new way

Round 12 named two thin things and predicted the CC_mask `< 3.0 Å` branch would break next. It did —
the fifth consecutive round in which the thinnest branch failed on the next widening. The
`d_FSC_model` result is more interesting: the band did *not* fail, but the way round 12 stated it
was wrong.

```bash
python3 scripts/bench_refinement_deltas_em.py --cache <em cache> --json <out.json>
```

Seven more EM entries at **2.60–2.96 Å**, chosen because the `< 3.0 Å` branch had only 8 entries and
five of them below 2.9 Å. The set reaches **28 entries**.

## 1. CC_mask `< 3.0 Å` — breached, as predicted

| Branch | n | min | median | band | breaches |
|---|---:|---:|---:|---:|---:|
| **< 3.0 Å** | **14** | **−0.0311** | +0.0012 | −0.02 | **1** |
| ≥ 3.0 Å | 14 | −0.0475 | +0.0073 | −0.06 | 0 |

**9O9K (2.90 Å): CC_mask 0.8441 → 0.8130, Δ −0.0311** on a null real-space refinement — 1.5× the
band. Round 12 set −0.02 from a single worst-case observation (21BQ, −0.0139) on 8 entries and
recorded that as the configuration most likely to break. It broke on the first widening.

Band widened to **−0.04**. The two branches are now −0.04 (< 3.0 Å, 14 entries) and −0.06
(≥ 3.0 Å, 14 entries), which is a much weaker resolution distinction than round 11 proposed — the
gap between branches has narrowed from 3× to 1.5× as both sides gained entries.

## 2. `d_FSC_model` — the band holds; round 12's framing did not

The new set contains a 36 % change, seven times the 5 % band:

| Entry | resolution | d_FSC_model pre → post | relative |
|---|---:|---|---:|
| 9H7U | 2.96 Å | 4.0604 → **2.5924** | **36.15 %** |

But it goes the *right way*. `d_FSC_model` is a resolution: **larger is worse**. 9H7U's refinement
improved model-map agreement from 4.06 Å to 2.59 Å — a large improvement, not a degradation.

The §4 clause is one-sided by construction — "map-model fit **did not degrade**",
`d_FSC_model_post ≤ d_FSC_model_pre + …` — and round 12 measured it as a two-sided `|Δ|`. Splitting
the 27 measurements by direction:

| | n | max |
|---|---:|---:|
| Degradations (post worse) | 8 | **+4.28 %** (9VAM) |
| Improvements (post better) | 17 | −36.15 % (9H7U) |
| Unchanged | 2 | — |

**As the one-sided band the clause actually specifies, 5 % holds with 0 breaches over 28 entries**,
and the largest degradation is 9VAM's 4.28 %. The apparent breach was an artefact of measuring a
directional clause symmetrically.

This also revisits round 12's headline. Its "3 of 21 entries breach ± 0.05 Å" counted two
improvements (9ELS −4.40 %, 9OID −2.43 %) as failures. Only **9VAM** was a genuine degradation
breach — the conclusion that the band had to become relative still stands on that entry, but the
count was inflated 3×.

## Applied

> **Map-model CC_mask `< 3.0 Å`: `CC_mask_post ≥ CC_mask_pre − 0.04`** (was −0.02, breached by
> 9O9K at −0.0311 over 14 entries). `≥ 3.0 Å` unchanged at −0.06 (14 entries, min −0.0475).
>
> **`d_FSC_model`: `d_FSC_model_post ≤ d_FSC_model_pre × 1.05` — one-sided.** Improvements are
> unbounded, which is what "did not degrade" means. Over 28 entries the largest degradation is
> **+4.28 %** and there are no breaches; the largest *change* is a 36 % improvement, which the
> previous two-sided reading would have failed.

## Scope limits

- 28 EM entries, 4 `real_space_refine` failures across the series (9VXE, 13GH, 9TZY, 9Z4O) reported
  rather than dropped.
- The `< 3.0 Å` CC_mask band is again set just above a single worst case (9O9K, −0.0311 → −0.04).
  On this series' record that is the configuration that breaks next; it is stated rather than
  presented as settled.
- The one-sided `d_FSC_model` band rests on 8 degradations, of which only one exceeds 1.1 %. The
  tail is thinner than the 27-entry count suggests.
- The two CC_mask branches now differ by only 1.5× (−0.04 vs −0.06). Whether the split earns its
  complexity is worth re-testing: a single −0.06 band would hold on all 28 entries today.
