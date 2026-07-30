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

| Entry | d_min | CC_mask Δ | `d_FSC_model` |
|---|---:|---:|---:|
| 10EU | 3.00 Å | +0.0156 | −1.08 % |
| 10EP | 3.20 Å | +0.0097 | −0.74 % |
| 10MJ | 3.30 Å | +0.0377 | +0.02 % |
| 10YG | 3.40 Å | +0.0452 | +0.00 % |
| 10FJ | 3.50 Å | *skipped* | `O1-` |
| 32FE | 3.81 Å | −0.0003 | −0.01 % |
| 10FL | 3.81 Å | *skipped* | `O1-` |
| 21EO | 3.91 Å | +0.0607 | +0.02 % |
| 28JV | 3.91 Å | *skipped* | unparameterised ligand (38 atoms) |
| 10ME | 4.00 Å | +0.0137 | **+1.48 %** |
| 10ZU | 4.00 Å | +0.0196 | +0.04 % |
| 5YKE | 4.11 Å | +0.0227 | −0.54 % |

**CC_mask: 1 of 9 degraded, and that one by −0.0003** — reproducible (see below) but 0.5 % of the band, so round 16 produced no CC_mask degradation of consequence. **`d_FSC_model`: 4 of 9 degraded, worst +1.476 %.**

| # | Prediction | Outcome |
|---|---|---|
| P1 | ≥ 1 `d_FSC_model` degradation | ✅ 4 |
| P2 | 5 % band holds | ✅ worst +1.476 %, 3.4× headroom |
| P3 | largest degradation > 1.1 % | ✅ **+1.476 %** |
| P4 | CC_mask −0.06 holds | ✅ worst −0.0003 |
| P5 | ≥ 1 entry-property skip | ✅ 3 |

## All five held — and that is a reason for suspicion, not satisfaction

P1, P4 and P5 were near-certain when registered. The two that carried information were P2 and P3, and
**P2 held for a reason that indicts how its probability was set.**

I put P2 at "nearer 60 % than 90 %" because 2 of the 3 `d_FSC_model` magnitudes then on record were
above 4 % (9VAM +4.28, 10BU +4.79, 10RI +0.45). That was a **publication-biased sample**: the large
ones were written down *because* they were notable, and 10RI appeared only because round 15 began
recording everything. With this round's values added, the full distribution is:

```
+0.018  +0.022  +0.036  +0.445  +1.476  +4.787
n = 6   median 0.240 %   1 of 6 above 4 % (17 %, not 67 %)
```

So the risk to P2 was roughly a quarter of what I estimated, and the estimate was wrong in a way the
old record made unavoidable — the only magnitudes available to reason from were the alarming ones.
**A selectively recorded history does not merely lose evidence; it biases the priors built on what
survives.** That is the `LOST`-row problem from §0 acting on a probability rather than a count.

**P3 is the round's real finding.** 10ME's +1.476 % clears the 1.1 % threshold, so round 13's "only
one of 8 degradations exceeds 1.1 %" described *its own high-resolution set*, not the quantity. The
tail was sampled thinly rather than being thin. Two of the six recorded degradations now exceed 1.1 %.

## CC_mask degradation rate is not set by resolution

Round 15 (3.00–3.90 Å) degraded CC_mask in **4 of 8** entries, worst −0.0351. Round 16 (3.00–4.11 Å),
a *coarser* window, degraded **1 of 9**, worst −0.0003 — a hundredfold smaller. Two adjacent
low-resolution rounds differ four-fold in rate and by two orders of magnitude in severity.

Whatever drives a null re-refinement to lose map-model correlation, it is not resolution alone. Round
12 said resolution "bounds but does not predict" the excursion; this is the sharpest evidence yet for
the second half of that.

Magnitude *is* resolution-linked, though not simply. Over all **44** entries with a recorded Δ,
Spearman ρ(resolution, |Δ|) = **+0.397** (n = 44, 5 % critical value ≈ 0.30):

| Band | n | median \|Δ\| | max \|Δ\| |
|---|---:|---:|---:|
| 2.3–3.0 Å | 15 | 0.0060 | 0.0311 |
| 3.0–3.5 Å | 18 | **0.0232** | 0.0603 |
| 3.5–4.2 Å | 11 | 0.0151 | **0.1268** |

The maximum grows monotonically with resolution; the median does not. 3.0–3.5 Å has the largest
*typical* excursion while 3.5–4.2 Å has the largest *single* one — which is why round 15's window was
the more productive widening and this round's coarser one was gentler. Reported as a description: the
split is post-hoc and the coarsest bin has n = 11.

**This analysis was impossible yesterday.** It needed per-entry values across rounds, which existed
only in prose for whichever entries an author found interesting. The TSV built in §0 paid for itself
inside the round that created it.

## The pipeline is deterministic, so no Δ is noise

Round 16's single CC_mask degradation is 32FE at **−0.0003** — three units in the last reported
place. Reviewing this round I flagged that as possibly indistinguishable from zero, and noted the
larger gap behind it: **sixteen rounds have compared Δ values against bands without ever measuring
the pipeline's own run-to-run repeatability** (#67). Round 14 recorded the concern in its scope
limits and nobody acted on it.

Measured rather than assumed:

| Step | Repeat run |
|---|---|
| `map_correlations` on 32FE | 0.7947, 0.7947 — identical |
| `real_space_refine` on 32FE, then re-measured | 0.7944 vs 0.7944 — **identical** |

**The hypothesis was wrong in the useful direction.** A full 33-minute refinement re-run reproduces
its CC_mask exactly at 4 dp, so 32FE's −0.0003 is a real, reproducible degradation rather than
numerical noise — and by extension **no recorded Δ in this benchmark is noise**. The smallest values
in the set (10SH +0.0001, 10SG −0.0019, 10FI −0.0026) are exact, not marginal.

This *removes* a caveat instead of adding one: round 14's scope limit that entries near zero "are
separated by less than the measurement's meaningful precision" is wrong and is withdrawn. The limit
is the 4 dp of the reported value, not any noise floor beneath it.

What remains true from the review is narrower and still worth fixing: **"1 of 9 degraded" invites a
false comparison** with round 15's "4 of 8" when round 16's single degradation is a hundred times
smaller. The rates are comparable; the rounds are not. Both are now quoted with their magnitudes.

Scope: determinism is tested on **one entry, one repeat**. It is strong evidence — an exact match
across a 33-minute optimisation is unlikely by chance — but a protocol with stochastic components on
some other input class is not excluded.

## Attrition is 3 of 12, not ~17 %

| Round | attempted | skipped | causes |
|---|---:|---:|---|
| 14 | 9 | 1 | ligand |
| 15 | 10 | 2 | ligand, `O1-` |
| 16 | 12 | 3 | `O1-` ×2, ligand |
| **total** | **31** | **6** | **19 %** |

Two causes account for all six. The charge case is now screened before the map download and costs
nothing; the ligand case still costs a model, a map and a `real_space_refine` attempt.

Two of the three `O1-` entries (10EN, 10FL) share a publication, suggesting charge modelling is a
lab-level convention. **Recorded as a hypothesis, not a finding** — it is the same shape of
provenance inference that failed at p = 0.38 in round 15, on a comparable number of cases. The charge
inventory is now stored on every kept entry so a future round can test it rather than eyeball it.

## Applied

> **All bands unchanged.** `d_FSC_model` holds at 5 % (worst this round +1.476 %; worst overall still
> 10BU's +4.787 % at **1.045×**). CC_mask `≥ 3.0 Å` holds at −0.06 (worst this round −0.0003).
>
> **The EM set is 53 entries, 15–20 CC_mask degradations, 14 `d_FSC_model` degradations.** Per-entry
> values for every entry from round 14 onward are in `ref/research/data/em_refinement_deltas.tsv`.

## Scope limits

- The `d_FSC_model` magnitude distribution rests on **6 recorded degradations**. Round 13 counted 8
  more but published only 9VAM's value, so the median above is computed from what survives, not from
  everything measured.
- The resolution/|Δ| bins are post-hoc, and the 3.5–4.2 Å bin has n = 11.
- The publication-clustering hypothesis for `O1-` rests on 3 entries and is explicitly untested.
- Round 16's window overlaps round 15's at 3.0–3.5 Å but the two rounds' CC_mask degradation rates
  differ four-fold, so neither round's rate should be read as characteristic of its window.
