# Tolerance benchmark — the §4 refinement Δ-tolerances

Settles the last unmeasured block in `ref/thresholds_and_standards.md`. §4 governs the
compare→refine flow and asserts how far a refinement may move a quantity before it counts as
degradation:

- **ΔRMSD sanity** — `RMSD_post ≤ RMSD_pre + 0.05 Å`
- **Geometry did not degrade** — `clashscore_post ≤ max(clashscore_pre, 4)`;
  `favored_post ≥ min(favored_pre, 97 %)`; `rotamer outliers_post ≤ max(outliers_pre, 2 %)`
- **Map-model fit did not degrade** — `CC_mask_post ≥ CC_mask_pre − 0.01`;
  `d_FSC_model_post ≤ d_FSC_model_pre + 0.05 Å`

These are **not** cross-tool agreement tolerances, so none of the rounds 1–4 machinery applies. The
question is not "do two tools agree" but "how much does a refinement that did *not* degrade the
model actually move these numbers". That needs a refine → re-measure loop.

```bash
python3 scripts/bench_refinement_deltas.py --cache <bench_t06 cache> --json <out.json>
python3 scripts/bench_refinement_deltas_em.py --cache <em cache> --json <out.json>
```

## Method — the null case

Each **deposited** model is re-refined against its **own deposited data**: `phenix.refine`
(3 macro-cycles) for X-ray, `phenix.real_space_refine` for cryo-EM. The model is already at its
refinement optimum, so a correctly-behaving refinement should barely move these quantities. Whatever
spread remains is the floor any Δ band has to clear — if a null re-refinement breaches the band, the
band flags correct work as degradation.

RMSD is computed **without re-superposition**, over matched (chain, resseq) Cα pairs: refinement
preserves the coordinate frame, so the raw shift is the quantity of interest and superposing first
would absorb part of what is being measured.

X-ray set: 8 entries (9 attempted; 9LK0's `phenix.refine` aborted on a ligand with no matching CIF
restraints). EM set: 2 entries (3 attempted; 13GH's `real_space_refine` failed).

## X-ray results

| Entry | Cα shift (Å) | clashscore pre → post | favored % pre → post | rotamer outlier % pre → post |
|---|---:|---|---|---|
| 12LO | 0.0084 | 1.18 → 0.00 | 98.15 → 98.15 | 0.00 → 0.00 |
| 37AP | 0.0310 | 2.49 → 2.22 | 100.00 → 100.00 | 0.00 → 0.00 |
| 30TW | 0.0453 | 1.17 → **4.99** | 98.79 → 98.99 | 0.26 → 0.00 |
| 30IZ | 0.0684 | 1.83 → 3.82 | 96.23 → **95.98** | 0.70 → 1.00 |
| 24MR | 0.0751 | 13.61 → 10.91 | 89.12 → 90.40 | 5.92 → 3.07 |
| 28SX | 0.0968 | 4.24 → **14.63** | 98.26 → 97.21 | 1.18 → 1.18 |
| 28SW | 0.1056 | 11.53 → **13.27** | 96.13 → **94.72** | 0.00 → **3.60** |
| 11AF | 0.1067 | 6.65 → 6.46 | 93.45 → 93.45 | 6.64 → 4.55 |

| Quantity | signed median | worsened / improved | signed range |
|---|---:|---:|---|
| Cα shift | **0.072 Å** | n/a (a magnitude) | 0.008 → **0.107 Å** |
| clashscore | **+0.78** | **4 / 4** | −2.70 → **+10.39** |
| Ramachandran favored | 0.00 pp | 2 / 3 | **−1.41** → +1.28 pp |
| rotamer outliers | 0.00 pp | 2 / 3 | −2.85 → **+3.60 pp** |

Signed statistics are reported deliberately. An earlier revision quoted |Δ| medians — "clashscore
median +1.87" — which reads as a systematic worsening when the split is in fact even (4 up, 4 down,
signed median +0.78). For a degradation check the direction is the whole question.

**How often a null re-refinement fails the tolerance as written:**

| Clause | failures |
|---|---|
| `RMSD_post ≤ RMSD_pre + 0.05 Å` | **5 / 8** |
| `clashscore_post ≤ max(clashscore_pre, 4)` | **3 / 8** |
| `favored_post ≥ min(favored_pre, 97 %)` | **2 / 8** |
| `rotamer outliers_post ≤ max(outliers_pre, 2 %)` | 1 / 8 |

## Cryo-EM results

| Entry | resolution | CC_mask pre → post | Δ | d_FSC_model pre → post |
|---|---:|---|---:|---|
| 27WR | 2.70 Å | 0.8039 → 0.7974 | **−0.0065** | 2.62 → 2.62 Å |
| 9VJD | 2.86 Å | 0.9081 → 0.9165 | +0.0084 | *unreliable* (29.65 → 29.77 Å) |

## Findings

**1. The ± 0.05 Å ΔRMSD band is breached by doing nothing.** Re-refining a deposited model against
its own data moves it by a median of **0.072 Å** and up to **0.107 Å** — 5 of 8 entries exceed the
band without any modelling change at all. The band is tighter than the reproducibility of the
refinement program it is meant to police.

**2. Clashscore moves in both directions and its worst excursion is unbounded by any useful band.**
The split is even — 4 of 8 worsened, 4 improved, signed median **+0.78** — but the range is −2.70 to
**+10.39** (28SX: 4.24 → 14.63). The likely mechanism is that `phenix.refine` optimises a target in
which the nonbonded term is one weighted contributor, while clashscore counts all-atom overlaps
after H placement; a small coordinate shift that improves the refinement target can add contacts.

The consequence for the tolerance is sharper than "widen the band". A Δ band that covers +10.39
would permit a clashscore to quadruple, which is not a check; a tighter band is breached by a null
re-refinement, which is the defect this benchmark exists to catch. **So clashscore Δ should not be
gated at all** — see the applied section.

**3. The absolute floors are quality bars, not refinement checks — and half the sample fails them at
deposition.** Of the 8 deposited models, only **4/8** have clashscore ≤ 4, **4/8** have favored
≥ 97 %, and 6/8 have rotamer outliers ≤ 2 %. A "did not degrade" clause with an embedded absolute
floor conflates two claims: whether the refinement made things worse, and whether the structure is
good in absolute terms. The second is a §2-style literature threshold and belongs there, cited, not
smuggled into a Δ check where it silently excuses degradation on already-poor models (28SW's
clashscore worsened 11.53 → 13.27 *and* it was above the floor to begin with).

**4. Map-model CC_mask is the one clause roughly the right size** — but not by much. The band is
−0.01 and a null real-space refinement consumed **65 % of it** on 27WR (−0.0065). With n = 2 that is
suggestive, not settled.

**5. `d_FSC_model` is not reliably measurable in this setup.** `phenix.mtriage`'s model-map FSC
crossings are degenerate without half-maps: 27WR reports FSC = 0.5 at 29.79 Å for a 2.7 Å map, and
9VJD reports FSC = 0.143 at 29.65 Å for a 2.86 Å map. Passing `resolution=` explicitly does not fix
it, and the logs show `d99 (half map 1): None`. The benchmark now flags any crossing beyond 2.5× the
map resolution as unreliable rather than differencing it into a tolerance — which is what turned an
apparent "Δ +0.12 Å, band exceeded" into "not measured".

## Applied

> **ΔRMSD sanity: `RMSD_post ≤ RMSD_pre + 0.15 Å`** (was + 0.05 Å). A null re-refinement of a
> deposited model moves Cα by a median 0.072 Å and up to 0.107 Å, so the old band flagged 5/8
> correct refinements as degradation.
>
> **Geometry did not degrade — split the Δ from the floor.**
> - Δ clause: **`favored_post ≥ favored_pre − 1.5 pp`** (worst null drop 1.41 pp) and
>   **`rotamer outliers_post ≤ outliers_pre + 4 pp`** (worst null rise 3.60 pp). Both cover the
>   observed null-refinement spread on 8/8 entries.
> - **No clashscore Δ gate.** Its null-case range is −2.70 to +10.39: any band covering that would
>   permit a clashscore to quadruple, and any tighter band is breached by a refinement that changed
>   nothing. Report the clashscore Δ as informational.
> - The absolute floors (clashscore ≤ 4, favored ≥ 97 %, rotamer outliers ≤ 2 %) are **quality bars,
>   not refinement checks**. Half the deposited sample fails them. They should be evaluated and
>   reported separately against §2's literature thresholds (Chen 2010 / Williams 2018), never used
>   to excuse a degradation.
> - **Clashscore is a poor degradation signal for X-ray refinement**: it moved in both directions on
>   a null re-refinement (4 up, 4 down) with a worst excursion of +10.39. Never call a refinement
>   degrading on a clashscore rise alone; require Ramachandran favored or rotamer outliers to agree.
>
> **Map-model fit: `CC_mask_post ≥ CC_mask_pre − 0.01` retained**, with the caveat that a null
> refinement already consumed 65 % of that band on one of two entries — revisit with a larger set.
> **`d_FSC_model` is unmeasurable without half-maps** and should not be gated on until the benchmark
> supplies them.

## Scope limits

- 8 X-ray entries and 2 EM entries. The EM conclusions in particular are indicative only.
- The **null case only**: this measures what a refinement that should change nothing actually does.
  It does not measure a genuinely degrading refinement, so it calibrates the false-positive side of
  each band, not the false-negative side.
- One refinement protocol (`phenix.refine`, 3 macro-cycles, default weights). A different
  macro-cycle count or weighting would move the null spread; REFMAC5/servalcat as a second refiner is
  not benchmarked.
- The clashscore mechanism in finding 2 is inferred from the numbers, not verified by inspecting
  which contacts appeared.
- Two runs failed and are reported rather than dropped: 9LK0 (`phenix.refine`, missing ligand
  restraints) and 13GH (`real_space_refine`).
