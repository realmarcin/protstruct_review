# 7OYN blinded agentic recovery — decisions

Agent working directory: `/tmp/agent_r5_7oyn/`
Final model: `final.pdb` (= `/tmp/agent_r5_7oyn/run4_001.pdb`, the output of refinement #4)

---

## Step 0 — The input data file was gone

`/tmp/nc_round1_cache/7oyn.mtz` did not exist when the task started; the `/tmp`
reaper had removed it. Per the task rules I did **not** re-fetch anything from the
network and did not read any other file in `/tmp/nc_round1_cache`.

**What I did.** A phenix.refine output MTZ carries the experimental data verbatim in
its dataset 1, `Original-experimental-data-mapped-to-asu`. I recovered the
observations from `/tmp/nc_round1_work/r5o_r4p_7oyn_001.mtz`, taking **only**
observation columns and the deposited free-flag column, and rebuilt the original
column layout with `build_obs_mtz.py`:

| original label | recovered from | valid reflections |
|---|---|---|
| `FOBS` | `F-obs` | 119042 |
| `SIGFOBS` | `SIGF-obs` | 119042 |
| `DANO` | `DANOF-obs` | 100106 |
| `SIGDANO` | `SIGDANOF-obs` | 100106 |
| `R-free-flags` | `R-free-flags(+)` / `(-)` | 119042 |

No model-derived column was read or propagated: `F-model`, `PHIF-model`,
`F-obs-filtered` (which is outlier-filtered *against a model*), `2FOFCWT`,
`FOFCWT`, `ANOM` and their phases were all left behind. The result is
`/tmp/agent_r5_7oyn/7oyn_obs.mtz`.

**Why I trust the recovery.** Four independent checks:

1. The MTZ title recorded inside every prior output file is
   `/tmp/nc_round1_cache/7oyn.mtz:FOBS,SIGFOBS,DANO,SIGDANO,systematic_abs`, and the
   prior `.eff` recorded `name = "FOBS,SIGFOBS,DANO,SIGDANO"` with
   `user_selected_labels = "FOBS,SIGFOBS"` and `"R-free-flags"`. My rebuilt file
   presents *exactly* those two arrays to phenix — same labels, same array grouping
   (`xray.reconstructed_amplitude`, n=219148 anomalous-expanded; free flags
   n=119042).
2. The free flags are bit-identical between two prior output MTZs written on
   different dates from different input models (234158 values compared, 0
   differences), so they are the deposited flags rather than a per-run regeneration.
   The `(+)`/`(-)` anomalous halves also agree on all 115116 reflections where both
   are present, so collapsing them back to one column is lossless.
3. The flag convention is CCP4 (`test_flag_value = 0`): value 0 selects 2381 of
   119042 merged reflections = **2.00%**, matching the per-shell `Nfree` totals in a
   prior log (4378 of 219144 anomalous = 2.0%). Had I assumed the phenix convention
   (1 = free) I would have refined against 2% of the data and reported meaningless
   statistics. I pass `test_flag_value=0` explicitly on every run rather than relying
   on auto-detection.
4. **The decisive check:** `phenix.model_vs_data` on the *unmodified perturbed model*
   against my recovered file returns **R-work 0.3480, R-free 0.3572**. A prior
   pipeline log records `bulk-solvent and scaling: r(all,work,free)=0.3482 0.3480
   0.3570` for the same model. Agreement to 0.0002 on data I rebuilt independently
   means the reconstruction reproduces the deleted original.

I read prior logs/`.eff` files in `/tmp/nc_round1_work` **only** to identify column
labels, the free-flag convention and the anomalous treatment — i.e. to rebuild the
data file. No coordinates from any prior model were used; my model descends solely
from the supplied `r4p_7oyn.pdb`.

## Step 1 — What the perturbation did

| | perturbed input |
|---|---|
| R-work / R-free | 0.3480 / 0.3572 |
| clashscore | 11.79 |
| Ramachandran | 92.55% favored, **0 outliers** |
| rotamer outliers | 1.30% |
| B-factors | min 6.3, median 12.9, max 56.4 — intact, all 2519 atoms have ANISOU |

Content: 259 residues, 1 Zn, ligand 65T, 364 waters, altlocs A/B/C, P2₁,
0.98–35.6 Å, 80% complete, anomalous.

**Reading.** Geometry is *plausible but wrong*: no Ramachandran outliers and only a
mild rotamer excess, yet R is catastrophic. That is the signature of a restrained
MD shake — coordinates displaced while restraints kept bonds and angles legal. So
this is a **positional** recovery problem, not a rebuild; ADPs and the ligand/ion
content survived and did not need reconstruction.

**Two consequences for strategy.** (a) At 0.98 Å the input already carries ANISOU,
so anisotropic ADP refinement is both justified (≈119k reflections vs ≈22.7k
parameters) and what the depositors evidently did. (b) The model had no hydrogens;
riding H are standard at atomic resolution and worth real R. I added them with
`phenix.ready_set` (2084 H; ANISOU, Zn, 65T and waters all preserved). 65T restraints
ship with phenix in geostd, so no custom CIF was needed.

I considered simulated annealing to escape the shake, and rejected it after
refinement #1: plain gradient refinement recovered R-free 0.357 → 0.145 in one run,
so the coordinates were evidently inside the convergence radius and SA would only
have risked damaging a model that was already converging.

## Step 2 — The refinement ladder

Six refinements were permitted and six were spent. Two further launches died
*before refinement started* and per the rules do not count; both are in the
transcript and annotated below.

| # | model | change from previous | R-work | R-free | clash | rota out | bond rmsZ | waters |
|---|---|---|---|---|---|---|---|---|
| — | perturbed | — | 0.3480 | 0.3572 | 11.79 | 1.30% | — | 364 |
| 1 | `run1_001` | xyz + aniso ADP + occ, 8 macrocycles, riding H, no solvent update | 0.1320 | 0.1448 | 1.18 | 0.00% | 1.521 | 364 |
| 2 | `run2_002` | + ordered solvent every macrocycle after first | 0.1256 | 0.1370 | 4.72 | 0.00% | 1.559 | 557 |
| 3 | `run3_001` | stricter solvent: `dist_min` 2.3, peak dist 2.3, CC 0.80 | 0.1241 | 0.1399 | 1.89 | 0.00% | 1.534 | 472 |
| **4** | **`run4_001`** | **weight optimization (xyz+ADP) + occupancies, no solvent update** | **0.1185** | **0.1356** | **2.36** | **0.00%** | **1.676** | **472** |
| 5 | `run5_001` | 6 more weight-optimized macrocycles | 0.1175 | 0.1345 | 2.59 | 0.43% | 1.648 | 472 |
| 6 | `run6_001` | solvent `filter_only`, `dist_min` 2.5 | 0.1203 | 0.1365 | 2.12 | 0.43% | 1.582 | 432 |

Ramachandran was 96.47% favored / 0 outliers for every refined model.

**#1 — bulk recovery.** Deliberately *without* solvent updating, so I could see what
plain refinement is worth before spending budget on anything clever. It was worth
almost everything: R-free 0.3572 → 0.1448, clashscore 11.79 → 1.18, rotamer outliers
1.30% → 0.00%. This is the measurement that killed the simulated-annealing plan.

**#2 — solvent rebuilding earns its cost, but not for free.** Waters 364 → 557 and
R-free 0.1448 → 0.1370, the single largest gain after #1. But clashscore *rose*
1.18 → 4.72. Diagnosis: 13 of 20 clashes involved newly-placed waters, mostly jammed
into Lys/Arg side chains. The cause is structural, not random —
`ordered_solvent.mask_atoms_selection` only protects backbone + CB, and
`peak_search.map_next_to_model` requires just 1.8 Å from model atoms and ignores
hydrogens entirely. Side chains are simply not defended by the defaults.

**#3 — buying the geometry back.** Raising the water-placement distance to 2.3 Å and
the map-CC filter to 0.80 cut clashscore 4.72 → 1.89 for +0.003 in R-free. I judged
that a good trade: 0.003 in R-free is near the noise floor of a 2381-reflection test
set, while a 2.5× clashscore difference is not.

**#4 — weight optimization, the chosen model.** At 0.98 Å the default `wxc_scale`
over-restrains; letting phenix optimize the xyz and ADP weights recovered the R-free
lost in #3 and more (0.1399 → 0.1356) while restoring occupancy refinement for the
altloc groups, which had been idle since #1 (see the crash note below). Geometry
stayed clean: 0 Ramachandran outliers, 0 rotamer outliers, clashscore 2.36.

**#5 — the stopping signal.** Six further macrocycles moved R-free 0.1356 → 0.1345,
i.e. 0.001 — indistinguishable from noise on 2381 free reflections — while
introducing a genuine full-occupancy rotamer outlier (A238 GLU, 0.43%) and nudging
clashscore up. Buying a noise-level R-free gain with a real geometry defect is a bad
trade, so I stopped chasing R and rejected this model.

**#6 — a targeted fix that missed.** The residual clashes were 3–4 waters pressed
against backbone N/CA atoms, which *are* in the solvent mask, so a `filter_only` pass
with `dist_min=2.5` should have removed them. It did not: the offenders sit at
almost exactly 2.50 Å (an overlap of 0.571 Å against N implies 3.07 − 0.571 = 2.50 Å)
and fell on the wrong side of a strict inequality. The run deleted 40 *other* waters
instead, costing R-free (0.1356 → 0.1365) and inheriting #5's rotamer outlier. A net
negative, reported as such.

### Two launches that did not count

- **Parameter rejection.** `refinement.input.xray_data.r_free_flags.test_flag_value=0`
  is not a valid path in the phenix 2.0 CLI; the correct one is
  `data_manager.fmodel.xray_data.r_free_flags.test_flag_value`. Rejected during
  parameter parsing, before any refinement.
- **Pre-refinement crash.** Combining `ordered_solvent=True` with `occupancies` in the
  strategy crashes in `mmtbx/refinement/occupancies.py:472`
  (`ValueError: list.remove(x): x not in list`), triggered by the 48 altloc water
  atoms in the model. It dies in "Extract refinement strategy and selections", before
  refinement begins. I worked around it by dropping `occupancies` from the strategy
  on solvent-updating runs (#2, #3, #6) and restoring it on the runs without solvent
  updating (#4, #5) — which is why the chosen model has refined altloc occupancies.

## Step 3 — Why `run4_001` is the final model

Choosing among already-computed models costs no budget, so I picked on the full
evidence rather than on R-free alone.

- It has the **lowest R-free of any model with zero rotamer outliers** (#5 and #6 both
  carry the A238 GLU outlier).
- Against #3, the nearest clean rival: −0.0043 in R-free for +0.5 clashscore. That
  R-free difference is roughly twice the noise of a 2% test set, while both models
  have zero Ramachandran and zero rotamer outliers.
- Against #5: +0.0011 R-free — noise — but 0.00% vs 0.43% rotamer outliers and lower
  clashscore.

**Honest cost of this choice.** Weight optimization loosened the restraints: bond
rmsZ 1.676 vs 1.521 for #1, bond RMSD ≈0.017–0.019 Å where 0.010–0.015 Å is more
typical at this resolution. All chirality is correct (0 of 316 wrong) and there are
no outlier-class violations, but this model sits at the loose end of the ladder and
that is the price paid for the R-free.

**What I did not do.** Three clashing waters remain (S737, S743, S1457, against
ARG253 N / HIS4 N / SER2 CA). I could have deleted them by hand to shave the
clashscore, but with no refinement budget left to re-settle the model, hand-trimming
atoms to improve a validation number is metric management rather than refinement. The
model is delivered exactly as refinement produced it.

I also declined to apply Ramachandran restraints to lift the 96.47% favored fraction.
The 9 residues in allowed regions are mostly the *same* Gly/Asn/Pro that were already
allowed before refinement (27, 65, 104, 150, 166, 243, 251) — the perturbation's own
damage went from 24 allowed entries to 10 — and they look intrinsic. At 0.98 Å the
data should decide backbone conformation, not a conformational prior.

## Step 4 — Independent verification (no PHENIX grading PHENIX)

| quantity | PHENIX | independent tool | agreement |
|---|---|---|---|
| R-work | 0.1185 (`model_vs_data`) | 0.1213 (`gemmi sfcalc`) | 0.003 |
| R-free | 0.1356 (`model_vs_data`) | 0.1355 (`gemmi sfcalc`) | **0.0001** |
| bond RMSD | 0.017 Å (geostd) | 0.019 Å (`gemmi rmsz`, CCP4 monomer lib) | 0.002 Å |
| chirality | 0 outliers | 0 of 316 wrong (`gemmi rmsz`) | agree |

The gemmi R-factors are genuinely independent: gemmi computed the structure factors,
fitted its own bulk-solvent model (k_sol 0.455, B_sol 120.2) and did its own
anisotropic scaling over 119004 reflections, with the free/work split taken from the
deposited flag column. R-free agreeing to 0.0001 while R-work differs by 0.003 is the
expected signature of two different bulk-solvent/scaling treatments of the same
correct model.

`gemmi blobs` finds **no unmodelled difference density** anywhere in the asymmetric
unit down to 2.8σ (and none at 3.0σ or 3.5σ). Nothing is missing from the model — no
unmodelled ion, ligand or ordered solvent — which is what closed the model-building
question and redirected the last two refinements toward convergence and solvent
quality instead of rebuilding.

## Final self-measured numbers

**R-work 0.1185, R-free 0.1356** (`phenix.model_vs_data`, recovered data, deposited
free flags, 2381 free reflections). Independently, `gemmi sfcalc`: R-work 0.1213,
R-free 0.1355.

Geometry: clashscore 2.36; Ramachandran 96.47% favored, **0 outliers**; rotamer
outliers **0.00%**; C-beta deviations 0; chirality 0 wrong of 316; bond RMSD
0.017 Å (PHENIX) / 0.019 Å (gemmi). 472 waters, riding hydrogens retained,
anisotropic ADPs on all non-hydrogen atoms.

Recovery achieved: R-free **0.3572 → 0.1356**, clashscore **11.79 → 2.36**, rotamer
outliers **1.30% → 0.00%**, Ramachandran favored **92.55% → 96.47%**.
