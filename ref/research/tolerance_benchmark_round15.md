# Tolerance benchmark — round 15: a pre-registered low-resolution widening

Round 14 established that entry count is not evidence for a one-sided band, and that the informative
entries are the ones that **degrade**. It also found that degradation *frequency* and *magnitude*
point at opposite resolutions: degradation is more common below 3.0 Å (4/8) than above it (5/14), but
every degradation above 3.08 Å is ≥ 0.0217 while every one below 3.0 Å is ≤ 0.0139. Only magnitude
re-fits a band.

This round widens at **3.0–4.0 Å** for that reason.

```bash
python3 scripts/fetch_em_entries.py --cache <dir> --min-res 3.0 --max-res 4.0 --limit 10 \
    --strata 10 --per-stratum 5 --max-map-mb 300 --max-model-mb 8 --exclude <existing set>
python3 scripts/bench_refinement_deltas_em.py --cache <dir> --json out.json
```

## Predictions, registered before the results

Round 14 computed its p-values *after* noticing the pattern they described, and said so. That is a
weak form of evidence, and this series has enough history now to do better: the historical rates
support specific, falsifiable predictions, so they are recorded here **before** the refinements
finish. Whatever happens, this file keeps them.

Baseline, from the `≥ 3.0 Å` entries measured in rounds 5–13: **5 degradations in 14 entries (36 %)**,
with magnitudes 0.0217, 0.0371, 0.0402, 0.0421, 0.0475 against a **−0.06** band.

| # | Prediction | Falsified if |
|---|---|---|
| **P1** | At least one entry degrades — unlike round 14, which got 0 in 8. | No entry degrades. |
| **P2** | The largest degradation **exceeds 0.0139**, the largest ever seen below 3.0 Å. | Every degradation is ≤ 0.0139. |
| **P3** | The **−0.06 band holds** — no degradation reaches it. | Any entry degrades by more than 0.06. |
| **P4** | The degradation *rate* lands nearer 36 % than round 14's 0 %. | Rate below 12.5 % (≤ 1 in 8). |

**P2 is the real test of this round's rationale.** The whole argument for widening at low resolution
rather than high was that degradations there are *large* — 3–7× larger. If the new degradations come
in small, that rationale was wrong, and the resolution split it supports weakens with it.

**P3 is the prediction most likely to be wrong**, and deliberately so. The band has 1.26× headroom
over the worst observation ever recorded, this series has broken a CC_mask band in 3 of its 4
widenings, and this is the first widening aimed squarely at the regime that produces large
degradations. Predicting it holds is the conservative call, not the confident one.

## P5: a natural experiment on independence, registered mid-run

The independence finding above was made by inspecting citations, not by measuring anything. This
round's set happens to contain a direct test of it, and the test is still in the future at the time
of writing.

**10EQ has run: CC_mask 0.7162 → 0.7765, Δ +0.0603** — the largest improvement ever recorded in this
benchmark, displacing 9OID's +0.0595. 10EQ belongs to the chloroplast glutamyl peptidase series, and
its two cluster-mates **10ET and 10EO have not yet been refined** — they are 8th and 9th in the fetch
order, with six entries between.

> **P5.** 10ET and 10EO will both land within **±0.02** of 10EQ's +0.0603, i.e. inside a window one
> fifth the width of the benchmark's observed Δ range (−0.0475 to +0.0603, span 0.108).
>
> **Falsified if** either cluster-mate falls outside ±0.02, which under independence is where most of
> the distribution sits.

If P5 holds, "one entry per publication" is measuring something real rather than being a
precaution. If it fails, the citation clustering is a bookkeeping artefact and the entry counts stand
as they were — in which case the fetcher change is harmless but the evidence recount in this round
should be withdrawn.

Note the asymmetry that makes this a fair test: 10EQ is the *largest* value in the whole set, so
regression to the mean works **against** P5. Cluster-mates drawn independently would be expected to
fall well below it.

## Results

*(pending — refinements running)*
