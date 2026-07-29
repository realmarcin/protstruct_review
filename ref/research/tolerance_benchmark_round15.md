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

## P6: a second, looser cluster — registered before it runs

**10EH has run: CC_mask 0.6531 → 0.7799, Δ +0.1268** — double the record 10EQ set minutes earlier,
and more than twice the width of the entire `≥ 3.0 Å` band. Its starting CC_mask, 0.6531, is the
lowest in the benchmark.

10EH belongs to the second cluster in this set, the yeast kinetochore series (10EH, 10DQ, 10FI).
**10DQ and 10FI are 7th and 10th in the fetch order and have not run.** That gives a second test of
the same claim, on a cluster that is deliberately *looser* than the first:

| Cluster | Members | What is shared |
|---|---|---|
| Glutamyl peptidase (P5) | 10EQ, 10ET, 10EO | **one protein**, three mutants/conformations |
| Yeast kinetochore (P6) | 10EH, 10DQ, 10FI | one paper, **three different complexes** (CBF3-CEN, apo CCAN, Cbf1-CCAN-CEN) |

> **P6.** 10DQ and 10FI land within ±0.02 of 10EH's +0.1268 — the same absolute window as P5, which
> is now a *tighter* relative test since the observed range has grown to 0.157.
>
> **P6b.** The kinetochore cluster is **looser** than the peptidase cluster: its within-cluster
> spread exceeds the peptidase cluster's.

P6b is the more interesting half. If clustering is about shared protocol alone, both should be
equally tight. If it is about the *structure* as well — same molecule, same map-making, same
difficulties — then one protein in three conformations should agree more closely than three distinct
complexes from one lab. P6b predicts the second, and it is the claim that would tell a future round
*how* to define a cluster rather than merely that clusters exist.

Same fairness note as P5: 10EH is now the extreme value of the whole benchmark, so regression to the
mean again works against the prediction.

## P6 is falsified — and that is the round's most useful result

**10DQ: CC_mask 0.7536 → 0.7687, Δ +0.0151**, against its cluster-mate 10EH's **+0.1268**. The gap is
**0.1117 — 5.6× the ±0.02 window**. P6 fails on its first data point, before 10FI has even run.

| Pair | Shares | Spread |
|---|---|---:|
| Myoglobin fibrils (24UM, 27WR) | same protein, one fibril study | **0.0005** |
| Spectral tuning (9UPM, 9UPO) | same protein family | 0.0073 |
| **Yeast kinetochore (10EH, 10DQ)** | **same paper, three different complexes** | **0.1117** |

The kinetochore pair is not merely loose — its spread is **larger than the benchmark's entire
observed Δ range was before this round**. Same paper, same lab, same reconstruction pipeline, same
software, and the two entries behave as differently as any two entries ever measured here.

**So shared publication is not sufficient for non-independence.** The claim committed earlier in this
round — that citation clustering explains the tight historical pairs — is too coarse as stated. What
the tight pairs share is the **protein**, not merely the paper: myoglobin fibrils with the same
myoglobin, 9UPM/9UPO with the same rhodopsin family. The kinetochore entries share a paper and
nothing structural, and they came apart.

This has a direct consequence for the fetcher change made earlier this round, which keys
`--max-per-pub` on the primary-citation **DOI**. If the operative grouping is the molecule rather than
the publication, DOI is the wrong key: it would drop 10DQ as a duplicate of 10EH when the two are, by
measurement, independent observations — discarding real evidence in a benchmark whose central
problem is that it has too little.

**P5 now decides it.** The glutamyl peptidase cluster is *one protein* in three
mutants/conformations, exactly the configuration the tight historical pairs have. 10ET and 10EO are
still unrun.

- **P5 holds and P6 failed** → the rule is "same molecule", not "same paper"; re-key the fetcher.
- **P5 also fails** → clustering is a bookkeeping artefact throughout, the evidence recount in this
  round should be withdrawn, and `--max-per-pub` should default to off.

Either way the answer is measured rather than assumed, which it was not when the fetcher was changed.

## P5 fails too — the clustering finding is withdrawn

**10ET: Δ −0.0351. 10EO: Δ −0.0221.** Against 10EQ's **+0.0603**, from the same protein:

| Cluster | Members | Spread |
|---|---|---:|
| Peptidase (P5) — *one protein*, three mutants | +0.0603, −0.0351, −0.0221 | **0.0954** |
| Kinetochore (P6) — one paper, three complexes | +0.1268, +0.0151 | 0.1117 |

P5 fails by 4.8×, and worse than P6 in one respect: the *same protein* produced an improvement of
+0.0603 and a degradation of −0.0351. Opposite signs.

A permutation test over every entry with a known cluster label settles it:

| | pairs | mean \|Δ difference\| |
|---|---:|---:|
| Within cluster | 21 | **0.0318** |
| Between clusters | 414 | 0.0354 |
| ratio | | 0.897 |

**Permutation p = 0.38.** Cluster-mates are not measurably more similar than unrelated entries. The
tight historical pairs — myoglobin at 0.0005, spectral tuning at 0.0073 — were coincidence among 21
within-cluster pairs, which is exactly what picking the two smallest of 21 looks like.

### What is withdrawn, and what stands

Earlier in this round I committed the claim that the historical evidence base is smaller than round 14
said, because 22 entries came from 12 publications and the four largest degradations arrived as two
same-paper pairs. **That claim is withdrawn.** It was inference from provenance, never a measurement,
and when measured it failed at p = 0.38.

The decision rule for this was registered before P5 ran — *"P5 also fails → clustering is a
bookkeeping artefact throughout, the evidence recount should be withdrawn, and `--max-per-pub` should
default to off"* — and is followed here rather than renegotiated.

**Round 14's finding stands unchanged**: entry count is not evidence for a one-sided band, because
only degradations can breach it, so 36 entries carry roughly 9 pieces of evidence. That argument
never depended on clustering. What is withdrawn is only the *further* deflation from ~9 to ~6.

`--max-per-pub` now defaults to **0 (no limit)**. The citation key is still computed and recorded on
every entry, because provenance is worth knowing and may predict something else — it simply no longer
filters anything unless explicitly asked for.

**The four largest degradations still come from two papers.** That observation was true and remains
true; what the test refutes is the inference that it *matters*. With 21 within-cluster pairs among
30 entries, some striking coincidence was likely, and this one was.

## Results

| Entry | d_min | CC_mask | Δ | d_FSC_model |
|---|---:|---|---:|---:|
| 10ET | 3.00 Å | 0.7822 → 0.7471 | **−0.0351** | −0.78 % |
| 10BU | 3.20 Å | 0.7577 → 0.7278 | **−0.0299** | **+4.79 %** |
| 10EO | 3.20 Å | 0.8707 → 0.8486 | **−0.0221** | −0.25 % |
| 10EQ | 3.30 Å | 0.7162 → 0.7765 | +0.0603 | −2.35 % |
| 10FI | 3.30 Å | 0.8181 → 0.8155 | **−0.0026** | −0.00 % |
| 10EH | 3.50 Å | 0.6531 → 0.7799 | **+0.1268** | −0.75 % |
| 10RI | 3.60 Å | 0.7481 → 0.7596 | +0.0115 | +0.45 % |
| 10DQ | 3.90 Å | 0.7536 → 0.7687 | +0.0151 | +0.00 % |

Skipped: **10EG** (unparameterised ligand, 195 atoms) and **10EN** (`O1-` absent from the electron
scattering table). Both are entry properties, not tool failures.

**CC_mask: 4 of 8 degraded (50 %), worst −0.0351. `d_FSC_model`: 2 of 8 degraded, worst +4.79 %.**

## Scoring the predictions

| # | Prediction | Outcome |
|---|---|---|
| **P1** | ≥ 1 entry degrades | ✅ **4 did** |
| **P2** | largest degradation > 0.0139 | ✅ **0.0351 — 2.5×** |
| **P3** | −0.06 band holds | ✅ **holds**, worst −0.0351, 1.71× headroom |
| **P4** | rate nearer 36 % than 0 % | ✅ **50 %** |
| **P5** | peptidase cluster within ±0.02 | ❌ **falsified**, spread 0.0954 |
| **P6** | kinetochore cluster within ±0.02 | ❌ **falsified**, spread 0.1117 |
| **P6b** | kinetochore looser than peptidase | ✅ 0.1117 > 0.0954 — but both are loose and the gap is small, so this is a comparison between two failures, not a useful confirmation |

**P2 was the round's real test and it passed.** The rationale for widening at low resolution rather
than high — that degradations here are large enough to re-fit a band — is confirmed: the worst
degradation is 2.5× anything ever recorded below 3.0 Å. Round 14's frequency/magnitude correction was
right, and the resolution split it supports is better evidenced than before.

**P4 confirms the frequency half too.** 50 % against round 14's 0 % in the same number of entries.
Round 14's 8-improvement run really was anomalous rather than a change in the benchmark.

## The band under threat is `d_FSC_model`, not CC_mask

P3 was registered about CC_mask because that tolerance has broken in 3 of its 4 widenings. It came
through comfortably at 1.71× headroom. Meanwhile **10BU degraded `d_FSC_model` by +4.79 % against a
5 % band — 1.045× headroom**, displacing 9VAM's +4.28 % as the worst ever recorded.

That is now the thinnest margin anywhere in `ref/thresholds_and_standards.md`. It is **not** widened
here: the band holds with 0 breaches, and this series has learned not to move a band on anticipation.
It is recorded as the first thing to re-test.

**10RI also showed the two quantities disagreeing in direction** — CC_mask +0.0115 while
`d_FSC_model` degraded +0.45 %. §4 gates on both, so they are not interchangeable evidence, and a
refinement can pass one while failing the other.

## Deposition headroom, again

10EH started at CC_mask **0.6531** and gained **+0.1268** on a null re-refinement — twice the width of
the band it is measured against, and the largest movement ever recorded here. 10EQ gained +0.0603 from
a start of 0.7162.

Round 14 argued that a Δ this large means the deposited model was not at any optimum, so the
measurement is *deposition headroom* rather than refinement noise. Round 15 supplies the two most
extreme examples yet, both at low resolution and low starting CC_mask.

## Applied

> **All bands unchanged.** CC_mask `≥ 3.0 Å` holds at −0.06 (worst −0.0351 this round, −0.0475
> overall); `< 3.0 Å` untested here; `d_FSC_model` holds at 5 % with **1.045× headroom**, its worst
> case now 10BU's +4.79 %.
>
> **The EM set is 44 entries with 14–19 CC_mask degradations and 10 `d_FSC_model` degradations.**
> Quote the degradation counts; the entry count overstates the evidence for a one-sided band. The
> CC_mask figure is a **range, not a count** — round 13 published only its branch minimum for 5 of
> the entries it added, so 14 is what is verifiable and 19 is the ceiling (#63).
>
> **`--max-per-pub` defaults to off** — publication clustering was tested and does not predict a
> similar null Δ (p = 0.38).

## Scope limits

- Two of ten entries were skipped for entry properties (unparameterised ligand; atom type outside the
  electron scattering table). Across rounds 14–15 that is **3 of 18 attempted**, a ~17 % attrition
  biased toward chemically simple structures. The direction of any resulting bias in Δ is untested.
- The permutation test uses the 30 entries with a known cluster label, which excludes rounds 13–14's
  entries whose per-entry values were published without provenance keys.
- **The CC_mask degradation total is a lower bound.** Round 13 added 6 net entries and published only
  its branch minimum (9O9K, −0.0311), so 5 of them have no recorded Δ. Verifiable total 14; ceiling 19.
  This is the second analysis in this round limited by the same gap, which promotes "recover per-entry
  values for rounds 5 and 9–13" from housekeeping to a prerequisite for stating the headline number.
- P6b is scored confirmed but should not be relied on: both clusters failed their tightness test, and
  0.1117 versus 0.0954 is well inside the noise of two 2–3 entry groups.
- The `d_FSC_model` 5 % band now rests on a worst case 4.5 % of the way to it. One further degradation
  of any size above +4.79 % breaks it.
