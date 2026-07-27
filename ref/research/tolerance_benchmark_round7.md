# Round 7 — the three narrow items

Two produced results that **invalidate bands set in rounds 5 and 6**; one hypothesis failed and is
recorded as a negative result with a diagnosis.

```bash
python3 scripts/bench_refinement_deltas.py --cache <low-res cache> --json <out.json>
python3 scripts/bench_vs_deposited.py --ids-file <ids.json> --cache <dir> --json <out.json>
```

## 1. §4 evidence base widened — and the round-5 bands fail at low resolution

Round 5 derived the §4 bands from 8 entries spanning **1.37–2.92 Å**. This adds 11 entries at
**3.00–3.60 Å** (low-resolution X-ray, where geometry is less constrained), for 19 total, and
re-checks every band on the combined set.

| Band (round 5 / 6) | breaches over 19 |
|---|---|
| `RMSD_post ≤ RMSD_pre + 0.15 Å` | **4 / 19** |
| `favored_post ≥ favored_pre − 1.5 pp` | **6 / 19** |
| `rotamer outliers_post ≤ outliers_pre + 4 pp` | 0 / 19 |
| `clashscore ratio ≥ 5×` (should not fire on a null run) | 0 / 19 |

The failures are entirely a resolution effect:

| Subset | n | Cα shift median / max | favored drop median / max | null clashscore ratio max |
|---|---:|---|---|---:|
| d_min < 2.5 Å | 5 | 0.045 / **0.075 Å** | 0.00 / **0.25 pp** | 4.26× |
| d_min ≥ 2.5 Å | 14 | 0.111 / **0.285 Å** | +1.23 / **+5.26 pp** | 3.45× |

**Finding.** A null re-refinement moves a low-resolution model **4× further** than a high-resolution
one (0.285 vs 0.075 Å) and costs up to **5.26 pp** of Ramachandran-favored where a high-resolution
model loses at most 0.25 pp. Round 5's single band was fitted to a set that was 5/8 above 2.5 Å only
by a small margin, and it does not transfer. This is the same failure mode the earlier rounds kept
finding in *other people's* numbers, now in mine: a band derived from one regime, applied to another.

The **clashscore ratio gate survives** the widening — no null re-refinement in either subset reached
5× (max 4.26×), including entries starting as high as 17.21, whose ratio was 1.25×. That is
consistent with round 6's prediction that the ratio compresses as the starting clashscore rises, and
it extends the observed range from 13.6 to **17.2** without a false positive.

### What the widened bands cost

Widening is correct — the old bands flagged 10/19 correct refinements — but it removes most of the
check at low resolution, and that has to be said rather than left for the reader to derive.

Against the round-6 perturbation data, the median Cα shift each noise level produces:

| σ (Å) | median Cα shift | exceeds `< 2.5 Å` band (0.10) | exceeds `≥ 2.5 Å` band (0.35) |
|---:|---:|---|---|
| 0.05 | 0.086 | no | no |
| 0.10 | 0.173 | yes | **no** |
| 0.20 | 0.346 | yes | **no** |
| 0.30 | 0.518 | yes | yes |

**The detection floor at `d_min ≥ 2.5 Å` is ~0.35 Å Cα — about 3× worse than the ~0.1 Å floor round 6
measured at high resolution.** Only damage at σ ≳ 0.3 Å is visible.

The favored clause weakens the same way: −6 pp applied to these models (deposited favored
80.5–96.9 %) lets a model at 92 % fall to 86 % and pass, well under §2's 97 % quality bar.

**So §4 is primarily a high-resolution check.** At `d_min ≥ 2.5 Å` it catches gross damage only, and
the absolute §2 quality bars — not the Δ clauses — carry most of the weight. A wide band reported
without its detection floor reads as "the refinement was fine" when it means "this check cannot see
much here".

## 2. `d_FSC_model` with half-maps — the hypothesis was wrong

Round 6 recorded that mtriage's model-map FSC crossings are degenerate without half-maps and
proposed fetching them. Both half-maps were downloaded for two EM entries and passed via
`half_map=`:

| | 27WR (2.7 Å) | 9VJD (2.86 Å) |
|---|---|---|
| `FSC(half map 1,2)=0.143` — **new, sensible** | 2.61 Å | 2.82 Å |
| `d99 (half map 1/2)` — **new, sensible** | 3.24 / 3.25 Å | 4.87 / 4.80 Å |
| `d_fsc_model` at 0.143 (masked) | 2.62 Å (unchanged) | **23.11 Å** (was 29.65) |
| `d_fsc_model` at 0.5 (masked) | **29.79 Å** (unchanged) | **29.32 Å** |

Half-maps fix the **half-map** FSC — they make the *map* resolution estimate work — and leave the
**model-map** FSC crossings degenerate. They are different quantities and only the second is what
the tolerance gates on.

**Diagnosis: it is a model-to-map coverage problem, not a missing reference.**

| Entry | atoms | map box | atoms per 10⁶ Å³ | `d_fsc_model` |
|---|---:|---|---:|---|
| 27WR | 2220 | 140³ Å (2.7 × 10⁶ Å³) | **813** | sensible (2.62 Å) |
| 9VJD | 1186 | 353³ Å (44.1 × 10⁶ Å³) | **27** | degenerate |

9VJD's model occupies a thirtieth of the density of 27WR's box — a subunit deposited against a large
assembly map. The model-map FSC is then dominated by unmodelled density, and no amount of half-map
information repairs that, because the half-maps describe the *map*, not the model's coverage of it.

**Applied:** `d_FSC_model` stays ungateable, now with the reason established rather than assumed. A
usable version of the clause would have to be conditioned on model-to-map coverage — measurable as
atoms per unit box volume — and that condition is not currently part of the tolerance.

## 3. Rotamer favored/allowed boundary — bounded rather than verified

The wwPDB report carries no rotamer score (its `ModelledSubgroup` attributes are `rota`, `rscc`,
`rsr`, `rsrz`, `EDIAm`, `OPIA`, occupancies and identity — no library density), so the
classification genuinely cannot be compared across pipelines. `phenix.rotalyze` *does* publish the
score, as `residue:occupancy:score%:chi1..chi4:evaluation:rotamer`, which allows the **exposure** to
be bounded instead.

MolProbity classifies score < 0.3 % as OUTLIER, 0.3–2.0 % as Allowed and > 2.0 % as Favored. Over
8054 residues in 17 entries:

| Residues whose score lies within a factor … of the 2 % cutoff | share |
|---|---:|
| ×1.25 | **3.90 %** |
| ×1.5 | 6.36 % |
| ×2.0 | 11.10 % |

**Finding.** If two implementations' rotamer scores agreed to within ±25 %, at most **3.9 pp** of
favored % could move — and only if every exposed residue flipped the same way. That is above the
± 1.0 pp tolerance, so the band is *not* robust to a systematic scoring difference of that size; it
is safe only because the two pipelines assign the identical rotamer to all 8054 residues (round 6),
which strongly implies a shared library rather than merely a shared vocabulary.

This converts the item from "unverifiable" to "bounded, and contingent on an assumption that is
stated": ± 1.0 pp holds if the scoring libraries match, and would not survive a genuinely
independent rotamer library.

## Applied

> **§4 bands become resolution-conditional.**
> - **d_min < 2.5 Å**: `RMSD_post ≤ RMSD_pre + 0.10 Å` (null max 0.075 Å);
>   `favored_post ≥ favored_pre − 0.5 pp` (null max 0.25 pp).
> - **d_min ≥ 2.5 Å**: `RMSD_post ≤ RMSD_pre + 0.35 Å` (null max 0.285 Å);
>   `favored_post ≥ favored_pre − 6 pp` (null max 5.26 pp).
>
> The round-5 single bands (+0.15 Å, −1.5 pp) are retired: they were fitted to a 1.37–2.92 Å set and
> are breached by null re-refinement on 4/19 and 6/19 entries respectively once low-resolution
> entries are included.
>
> **§4 is primarily a high-resolution check.** The widened `≥ 2.5 Å` bands have a detection floor of
> **~0.35 Å Cα** (σ ≈ 0.3), about 3× worse than the ~0.1 Å floor at high resolution, and the −6 pp
> favored clause permits a drop from 92 % to 86 %. At low resolution rely on the absolute §2 quality
> bars rather than these Δ clauses.
>
> **Unchanged and now better supported:** `rotamer outliers_post ≤ outliers_pre + 4 pp` (0/19
> breaches) and the clashscore ratio gate ≥ 5× (0/19 false positives, starting clashscores up to
> 17.2).
>
> **`d_FSC_model` remains ungateable**, because the model-map FSC degenerates when the model covers a
> small fraction of the map box — not because half-maps were missing.
>
> **Rotamer favored % ± 1.0 pp holds contingently**: 3.9 % of residues sit within ×1.25 of the
> Favored/Allowed cutoff, so the band assumes the two pipelines share a rotamer library, which the
> identical assignment of 8054/8054 residues supports but does not prove.

## Scope limits

- The low-resolution subset is 11 entries at 3.00–3.60 Å; nothing between 2.92 and 3.00 Å, and
  nothing beyond 3.60 Å. The 2.5 Å split is a convenience boundary, not a measured inflection.
- One refinement protocol throughout (`phenix.refine`, 3 macro-cycles, default weights). Low-
  resolution refinement in practice would use restraints and NCS this benchmark does not apply,
  which likely makes these null spreads *pessimistic*.
- The coverage diagnosis for `d_fsc_model` rests on two EM entries at opposite extremes; the
  atoms-per-volume threshold at which the FSC degenerates is not established.
- Boundary exposure is computed from one implementation's scores. It bounds how far favored % could
  move under a hypothetical scoring difference; it does not measure an actual difference.
