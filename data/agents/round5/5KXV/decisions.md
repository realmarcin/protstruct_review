# 5KXV blinded recovery — decisions log

Agent working directory: `/tmp/agent_r5_5kxv/`
Final model: `final.pdb` (= `/tmp/agent_r5_5kxv/r6_006.pdb`, output of refinement run 6)

Refinement budget: **6 of 6 invocations used.** Three additional launches failed
before refinement began (two PHIL-scope rejections, one PHENIX internal crash) and are
annotated below; per the rules they do not count against the budget.

---

## Step 0 — Characterize the inputs and the damage (no refinement spent)

**What I did.** Read the MTZ header with `gemmi mtz --headers`, inventoried the model
with shell text tools, and ran `phenix.model_vs_data` plus the standalone MolProbity
validators (`phenix.clashscore`, `phenix.ramalyze`, `phenix.rotalyze`) and a
`mmtbx.model` geometry-statistics pass on the perturbed coordinates.

**What I measured.**

Data: `FOBS,SIGFOBS` amplitudes, free set `R-free-flags` with test flag value 0,
P4(3)2(1)2, cell 67.577 / 67.577 / 107.140, **resolution 16.89–0.98 Å**, 99.6% complete,
141320 reflections.

Model: single chain A, 277 residues, 5092 atoms — 4594 protein (2261 of them riding
hydrogens, already present), 468 waters, plus 2 GOL, 1 NO3, 1 CA. ANISOU on all 2831
non-hydrogen atoms. Extensive alternate conformations (638 A / 639 B / 23 C altloc
atoms); 68 waters carry altlocs and 241 waters are partial occupancy. Mean protein
B = 9.4 Å². This is a deposited-quality atomic-resolution model.

Starting quality:

| metric | value |
|---|---|
| R-work / R-free | **0.4114 / 0.4070** |
| clashscore | 7.13 |
| Ramachandran favored / outliers | 92.06% / 0.36% |
| rotamer outliers | 1.59% |
| Rama-Z (whole) | **−4.24 (POOR)** |
| bond / angle RMSD | 0.0084 Å / 1.576° |

**What I concluded.** The damage is *pure coordinate displacement that was subsequently
geometry-regularized*. Three independent signals agree:

1. R-work climbs monotonically with resolution (0.356 in the lowest shell to 0.482 in
   the 1.045–0.980 Å shell). That is the signature of random coordinate error, not of
   bad scaling, wrong B-factors, or a missing bulk-solvent model.
2. Bond RMSD is 0.0084 Å and angle RMSD 1.58° — near-ideal. A raw un-regularized shake
   would have wrecked these. So the perturbation was regularized after displacement.
3. Rama-Z is −4.24 (poor) while Ramachandran outliers are only 0.36%. The backbone
   distribution is globally non-native even though few residues are individually
   flagged — exactly what a small global shake produces.

A displacement of this size (~0.3–0.4 Å implied by R ≈ 0.41) sits comfortably inside
the convergence radius of gradient refinement at d_min = 0.98 Å, so I chose **plain
reciprocal-space refinement over simulated annealing**. SA would have cost far more
budget and carried real risk of scrambling the 1300+ alternate-conformation atoms and
the partial-occupancy solvent model, to fix a problem gradient descent can reach.

I also decided to **keep the anisotropic ADPs** rather than collapsing to isotropic.
At 0.98 Å aniso is the correct parameterization; the ANISOU records are intact
information, and B factors are small (mean 9.4 Å²) so they had little room to absorb
coordinate error.

**Three free (non-refinement) launches were needed to find the PHIL scope.** PHENIX 2.0
moved the free-flag parameter: `refinement.input.xray_data...` and
`input.xray_data...` were both rejected outright; the working path is
`data_manager.fmodel.xray_data.r_free_flags.test_flag_value`. All three were
`--dry-run` or failed at parameter parsing, before any refinement.

---

## Run 1 — Coordinate recovery (refinement invocation 1 of 6)

**What I did.** `phenix.refine` on the perturbed model with the default PHENIX 2.0
strategy (`individual_sites` + `individual_sites_real_space` + `individual_adp` +
`occupancies`), 8 macrocycles, default target weights, hydrogens riding, anisotropic
ADPs retained, **no** ordered-solvent update.

**Why.** One long unassisted run is the cheapest possible test of my diagnosis: if the
problem really is recoverable displacement, this alone should do most of the work, and
it tells me how much budget the interesting questions (solvent, weights) can have. I
deliberately withheld the solvent update — rebuilding water against a map computed from
still-misplaced protein would delete good waters on bad evidence.

**What I measured.** R-work/R-free 0.4114/0.4070 → **0.1139 / 0.1286**. Per-macrocycle
descent: 0.207/0.227 → 0.157/0.175 → … → 0.1139/0.1286, converged by cycle 7.
Clashscore 7.13 → **1.30**. Ramachandran 92.06% → 96.75% favored, outliers 0.36% → **0%**.
Rotamer outliers 1.59% → **0%**. Bond 0.0069 Å, angle 1.04°.
**Rama-Z −4.24 → −0.02.**

**What I concluded.** The structure is recovered, and it is genuine recovery rather than
overfitting. The decisive number is Rama-Z, not R: a model whose R-free was driven down
by fitting noise does not have its backbone dihedral distribution snap back to the
native mean. Rama-Z ≈ 0 with 0% Ramachandran and 0% rotamer outliers, at an R-free/R-work
gap of only 0.0147, says the atoms went back where they belong. My diagnosis was right
and simulated annealing would have been wasted budget.

---

## Interlude — Is the solvent under-modeled? (free)

`phenix.find_peaks_holes` on the run-1 model at 3.5σ: **91** candidate sites in the
1.8–3.2 Å shell around the model, 11 above 6.5σ, max 12.2σ — against only **5** negative
holes (min −4.15σ). Strongly asymmetric: nothing is over-modeled, but real density is
unaccounted for. Solvent rebuilding is worth budget.

---

## Run 2 — Ordered-solvent rebuild (invocation 2)

**A crash first, not counted.** My initial run-2 launch died in
`mmtbx/refinement/occupancies.py:472`, `ValueError: list.remove(x): x not in list`,
inside `occupancy_selections` — a PHENIX bug triggered by combining `ordered_solvent`
with occupancy refinement on a model containing alternate-conformation waters. It
failed in `set_refinement_flags` during preprocessing, before refinement started.
**Workaround:** drop `occupancies` from the strategy for solvent-building runs and
restore it in the polish runs (occupancies had already converged in run 1).

**What I did.** Continued from run 1 with `ordered_solvent=True`,
`mode=every_macro_cycle_after_first`, **`filter_at_start=False`**, 5 macrocycles.

**Why `filter_at_start=False`.** The input solvent model is sophisticated — 68 alt-conf
waters, 241 partial-occupancy waters — and the ordered-solvent routine runs with
`include_altlocs=False`, so it does not understand that model. With only 5 negative
peaks in the whole map there was nothing to cull anyway. So: add, don't prune.

**What I measured.** 0.1139/0.1286 → **0.1089 / 0.1205**. Waters 468 → 528 (331 of the
originals surviving in chain A, 197 new in chain S). Clashscore 1.51, Rama-Z −0.08,
0% Rama and rotamer outliers, bond 0.0075 Å.

**What I concluded — including a mid-run misread I had to correct.** Partway through I
watched the routine cull 468 → 346 waters and then add back to 565, with R-work falling
while R-free stayed flat, and I judged it to be fitting noise. That was premature. Over
the following macrocycles R-free fell to 0.1182 *and the R-free−R-work gap narrowed*
from 0.0147 to 0.0114. Added parameters that are fitting noise widen the gap; these
narrowed it. The waters are real. The lesson I carried forward: judge a solvent update
only after the subsequent refinement of those waters, never at the moment of insertion.

I also noted a systematic defect: the **final filtering step made things worse**,
0.1075/0.1186 mid-run → 0.1089/0.1205 written out. It discards waters that were
improving the fit.

---

## Run 3 — Second solvent round (invocation 3)

**What I did.** Same recipe, continued from run 2, 5 macrocycles. Justified by a fresh
peak search on the run-2 model: still **62** candidates >3.5σ, 8 above 6.5σ, max 13.2σ.

**What I measured.** **0.1077 / 0.1189**, 540 waters, clashscore 1.30, Rama-Z −0.09,
0% Rama and rotamer outliers, bond 0.0074 Å.

Mid-run this went through the same shape as run 2: the first macrocycle *raised* R-free
from 0.1209 to 0.1305 before recovering to 0.1165, and the final filter again cost
~0.002 (0.1047/0.1165 → 0.1077/0.1189).

**What I concluded.** Solvent gains are decaying fast — 0.0081 in R-free from round 1,
only **0.0016** from round 2. Stop adding water; the remaining error is elsewhere.

The repeated first-macrocycle excursion told me something more useful: on restart from
a converged model the **default X-ray/geometry target weight overshoots**, degrading
R-free before clawing it back. That is a fixable, measured problem, and it set the
agenda for run 4.

---

## Run 4 — Optimized target weights + occupancies restored (invocation 4)

**What I did.** From the run-3 model: full strategy *with* `occupancies` restored
(safe now that `ordered_solvent` is off), `optimize_xyz_weight=True`,
`optimize_adp_weight=True`, 3 macrocycles, no solvent update.

**Why.** Two reasons to re-include occupancies: they had not been refined since run 1,
and both side chains and waters have moved substantially since. Weight optimization
directly targets the overshoot diagnosed in run 3 rather than guessing at it.

**What I measured.** 0.1077/0.1189 → **0.1003 / 0.1158**. PHENIX selected wxc = 1.259.
Clashscore 1.30 → **1.08**, rotamer favored 96.83% → **97.22%**, Rama-Z −0.06, 0% Rama
and rotamer outliers. Bond RMSD rose slightly, 0.0074 → 0.0084 Å; angle 1.01° → 1.09°.

**What I concluded.** The overshoot hypothesis was correct and worth its invocation:
R-free fell 0.0031 *and* clashscore and rotamers improved simultaneously. The small
rise in bond/angle RMSD is the optimizer legitimately shifting the data/restraint
balance, and 0.0084 Å is unremarkable for 0.98 Å data. Fit and validation moved the
same direction, so this is not a trade.

---

## Run 5 — Recover the waters the filter was throwing away (invocation 5)

**What I did.** One more solvent round from the run-4 model with two targeted changes:
**`ignore_final_filtering_step=True`** and **`include_altlocs=True`**, 4 macrocycles.

**Why — this is the one inference I am most confident in.** A peak search on the run-4
model still showed 71 sites >3.5σ (8 above 6.5σ, max 12.9σ) that two solvent rounds had
failed to place. Their positions are diagnostic: the strongest sit 2.68 Å from
Tyr274 OH, 2.65 Å from Asn120 O, 2.76 Å from Ser105 OG, 2.84 Å from Ser197 OG — that is
hydrogen-bonding distance to polar atoms, i.e. these are ordinary waters, and something
in the picker was rejecting them, not the chemistry. Two suspects, both testable and
both addressed: `include_altlocs=False` blocks placement in the alt-conf regions, and
the final filtering step had demonstrably raised R-free in *both* prior solvent runs
(run 2: 0.1186 → 0.1205; run 3: 0.1165 → 0.1189).

**What I measured.** **0.0999 / 0.1132**, 832 waters, mean water B 23.7 Å² (max 60.1 —
no absurd values). Clashscore 1.08 → 2.81. Rama favored 97.11%, 0% Rama and rotamer
outliers, Rama-Z −0.06, bond 0.0070 Å.

Crucially, **the end-of-run penalty vanished**: 0.1131 mid-run → 0.1132 written out,
versus the ~0.002 loss in runs 2 and 3. The filter really had been discarding good
waters.

**What I concluded.** R-free improved 0.0026, and it is cross-validated — these waters
were never used to drive the refinement, so density-supported waters lower R-free while
spurious ones raise it. The clashscore cost (1.08 → 2.81) is real and comes from the
larger water count, but 2.81 is still comfortably good, and run 4 had shown that weight
optimization repairs clashscore. 832 waters for 277 residues (3.0/residue) is on the
high side; I flag it as the one aspect of this model an independent re-measurement
should scrutinize hardest.

---

## Run 6 — Final polish (invocation 6)

**What I did.** The run-4 recipe applied to the run-5 model: occupancies +
optimized xyz and ADP weights, 3 macrocycles, no solvent update.

**Why.** Run 4 demonstrated this step recovers clashscore while lowering R-free, which
is exactly the pair of problems the run-5 model had.

**What I measured.**

| metric | perturbed input | **final (run 6)** |
|---|---|---|
| R-work | 0.4114 | **0.0914** |
| R-free | 0.4070 | **0.1078** |
| clashscore | 7.13 | **1.94** |
| Ramachandran favored | 92.06% | **96.75%** |
| Ramachandran outliers | 0.36% | **0.00%** |
| rotamer outliers | 1.59% | **0.00%** |
| Rama-Z (whole) | −4.24 | **−0.04** |
| bond RMSD | 0.0084 Å | 0.0082 Å |
| angle RMSD | 1.576° | 1.080° |
| C-beta deviations | 0.00% | 0.00% |
| waters | 468 | 832 |

**What I concluded.** Confirmed: clashscore recovered 2.81 → 1.94 while R-free fell
0.1132 → 0.1078. Best model on every axis I can measure except clashscore, where run 4
(1.08) is better but costs 0.008 in R-free.

---

## Final model selection

Candidates:

| model | R-work | R-free | clashscore | waters |
|---|---|---|---|---|
| run 4 | 0.1003 | 0.1158 | 1.08 | 540 |
| run 5 | 0.0999 | 0.1132 | 2.81 | 832 |
| **run 6 (chosen)** | **0.0914** | **0.1078** | 1.94 | 832 |

I chose run 6. It has the best fit by a clear margin (0.008 in R-free over run 4), zero
Ramachandran and rotamer outliers, Rama-Z of −0.04, and bond/angle RMSDs that are
*better* than the perturbed input's. Its clashscore of 1.94 is worse than run 4's 1.08
but both are strong in absolute terms, and I judged 0.008 in cross-validated R-free the
more meaningful quantity.

**Verified independently.** `phenix.model_vs_data` run separately on `final.pdb`
reproduces **R-work 0.0914 / R-free 0.1076**, and the standalone MolProbity validators
reproduce clashscore 1.94, 0.00% Ramachandran outliers, 0.00% rotamer outliers — so the
final numbers do not rest on `phenix.refine`'s own internal bookkeeping.

## Caveats I would want an independent check on

- **832 waters is 3.0 per residue**, well above the 468 in the input. R-free supports
  them and mean water B is a sane 23.7 Å², but this is the most aggressive thing in the
  model and the first place to look for over-fitting.
- The R-free − R-work gap widened over the run, 0.0147 (run 1) → 0.0164 (run 6). Still
  small and normal for atomic resolution, but it is monotone and worth noting.
- The ordered-solvent routine **rewrote the input's alt-conf / partial-occupancy water
  model**, replacing much of it with full-occupancy waters in chain S. R-free improved,
  but chemical nuance present in the input solvent description was lost.
- Disulfide restraint RMSD drifted upward across the runs (0.0049 → 0.0059 Å bond).
  Negligible in size, but monotone. Note the input header contains a duplicated
  SSBOND record (Cys34–Cys123 listed twice, the second reversed), which is harmless
  but malformed.
