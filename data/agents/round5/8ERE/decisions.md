# 8ERE — blinded agentic recovery: decisions log

Working dir: `/tmp/agent_r5_8ere/`
Inputs: `/tmp/nc_round1_work/r4p_8ere.pdb` (perturbed model), `/tmp/nc_round1_cache/8ere.mtz` (data).
Final model: `final.pdb` (= `/tmp/agent_r5_8ere/r6_001.pdb`).

Refinement-program budget: **6 permitted, 6 used.** One additional launch (the first
`r1.eff` attempt) was rejected at PHIL parsing and never entered refinement, so it is
not counted; it is annotated below and in `transcript.md`.

---

## Step 0 — Characterize the inputs (no refinement cost)

**Did.** Read MTZ headers with `gemmi mtz --headers`; enumerated columns and free-flag
distributions with the cctbx/gemmi Python API; censused the model.

**Measured.**
- Data: P1, cell 30.07 / 30.56 / 35.01 Å, 75.03 / 68.46 / 89.62°, **d_min = 0.87 Å**,
  84819 usable amplitudes, 93.0% complete.
- Amplitude pair `FOBS,SIGFOBS`. Two candidate flag columns: `R-free-flags` (binary,
  4505 reflections have value 0 = 4.9%) and `R-free-flags-1` (20 bins). The binary
  column is the 0-bin of the 20-bin column. Chose **`R-free-flags` with
  `test_flag_value = 0`**; `phenix.model_vs_data` independently auto-detected flag
  value 0, confirming the choice.
- Model: single chain A, residues 1–127 with **no gaps**, 1081 protein heavy atoms,
  1091 riding H, 154 waters, alternate conformers A–D with partial occupancies,
  ANISOU on all 1240 heavy atoms, mean B = 10.7 Å².

**Concluded.** This is a subatomic-resolution dataset with an intact, fully-connected
chain. Nothing is missing from the polymer, so the repair job is about coordinates,
ADPs and solvent — not chain tracing or rebuilding.

## Step 1 — Baseline (no refinement cost)

**Did.** `phenix.model_vs_data`, then `phenix.clashscore` / `ramalyze` / `rotalyze` on
the perturbed model.

**Measured.** R-work **0.3979**, R-free **0.4103**. Clashscore 7.31; Rama 96.80%
favored with 1 outlier (0.80%); rotamer outliers 0.00%.

**Concluded.** The diagnostic signature is important: R is catastrophic (0.40) while
*local geometry is nearly intact*. A perturbation that scrambled bonds and angles would
have wrecked the validation scores too. So the damage is a coordinate displacement that
was geometry-regularized afterwards — which means gradient refinement against very
strong high-resolution data should recover it, and expensive escape strategies
(simulated annealing, torsion-space SA) are probably not needed. I deliberately did not
spend budget on SA on the strength of this reasoning.

## Step 2 — Confirm the data supports full-resolution refinement (no cost)

**Did.** Binned `<F/sigma>` by resolution shell.

**Measured.** `<F/sigma>` = 79 (low res) falling smoothly to **9.5 in the 0.92–0.87 Å
shell** (roughly I/sigma ~5).

**Concluded.** The outermost shell is real signal, not noise. Refined against all data
to 0.87 Å with no high-resolution cutoff, and kept every heavy atom anisotropic
throughout — both justified by the resolution rather than assumed.

## Step 3 — Rejected launch (does NOT count against budget)

**Did.** First `phenix.refine` invocation using classic `refinement.input.xray_data.*`
and `refinement.output.prefix` PHIL paths.

**Measured.** Exit 1 in 2.8 s: *"Some PHIL parameters are not recognized"* —
Phenix 2.0's new CLI moved data selection to `data_manager` /
`miller_array.labels.name` and file naming to top-level `output.prefix`.

**Concluded.** Nothing was refined; no model was read past parameter validation. Fixed
by reading `--show-defaults` and rewriting the parameter file. **Not counted.**

## Step 4 — Refinement 1/6: coordinates + anisotropic ADPs + occupancies

**Did.** From the perturbed model: `individual_sites` + `individual_sites_real_space` +
`individual_adp` + `occupancies`, anisotropic for all non-H and isotropic for H, riding
hydrogens, N/Q/H flips on, **6 macro-cycles**, default weights, **no** solvent update.
I deliberately withheld solvent rebuilding here: at R = 0.40 the maps are unreliable and
automatic water picking would have decorated a wrong model with spurious peaks.

**Measured.** R-work **0.3979 → 0.1314**, R-free **0.4105 → 0.1415**. Bond RMSD
0.007 Å, angle 1.02°. R-free flat over the last two macro-cycles (0.1421 → 0.1415), so
converged. Clashscore 7.31 → **1.83**; Rama outliers 0.80% → **0.00%** (99.20%
favored); rotamer outliers 0.00%.

**Concluded.** Step 1's read was right — the perturbation was recoverable by plain
gradient refinement, and geometry *improved* rather than being traded away. This one
run did the overwhelming majority of the repair.

## Step 5 — Locate what remains (no refinement cost)

**Did.** `phenix.find_peaks_holes` on the refined model, then scripted each peak
against its nearest non-H model atom (gemmi `NeighborSearch`).

**Measured.** 105 positive peaks > 3σ (30 > 6σ, 12 > 9σ, max 13.3σ) against only
**8 negative holes**, none deeper than −3.8σ. Of the positive peaks, 71 lie 2.2–3.6 Å
and 34 lie 1.2–2.2 Å from an existing atom; the top 20 are almost all adjacent to
existing water oxygens.

**Concluded.** Strong positive density with essentially no negative density means
**missing atoms, not misplaced ones** — and their H-bond-distance relationship to
existing waters identifies them as an unmodelled outer solvent shell. This is direct
evidence that ordered-solvent rebuilding will pay, rather than a hopeful guess, so it
earned the next slot in the budget.

## Step 6 — Refinement 2/6: solvent update, CRASHED (counts against budget)

**Did.** `ordered_solvent = True`, `mode = every_macro_cycle_after_first`,
`new_solvent = anisotropic`, keeping the explicit `anisotropic = not element H`
selection.

**Measured.** Ran macro-cycle 1 and reached the solvent update of macro-cycle 2, then
died: `CCTBX_ASSERT(f.use_u_iso()) failure` inside
`mmtbx/refinement/data.py:set_refine_u_iso`.

**Concluded.** `new_solvent = anisotropic` conflicts with the ordered-solvent updater,
which sets `u_iso` flags on newly placed waters that my selection had already flagged
anisotropic. **Refinement had genuinely started (two macro-cycles of work), so I count
this against the budget — 2 of 6 — rather than excusing it as a launch failure.** The
fix was to let new waters arrive isotropic and convert them later, and to drop the
explicit ADP selection so Phenix inherits ADP types from the input model.

## Step 7 — Refinement 3/6: ordered solvent, isotropic new waters

**Did.** Re-ran from the 4/6 output (`r1_001.pdb`) with `new_solvent = isotropic` and
no explicit ADP selection; 8 macro-cycles.

**Measured.** R-work **0.1227**, R-free **0.1309**; 212 waters. Clashscore 3.20, Rama
0.00% outliers / 99.20% favored, rotamer 0.00%. Residual density fell to 68 peaks > 3σ
(4 > 9σ). Verified atom-by-atom that the 1081 protein heavy atoms are the *same set*
as in the input — nothing lost, nothing invented.

**Concluded.** Solvent was indeed the deficit. One detail mattered: the trace showed
the mandatory final filtering step dropping 267 waters to 212 and simultaneously
*raising* R-free from 0.1268 to 0.1309. Since R-free is cross-validated, the discarded
waters were genuinely predictive, so the filter was costing model quality.

## Step 8 — Refinement 4/6: finish the solvent shell

**Did.** Continued with `filter_at_start = False` and
`ignore_final_filtering_step = True`, 8 macro-cycles.

**Measured.** R-work **0.1159**, R-free **0.1262**; 275 waters. Water count oscillated
288 → 275 while R-free sat flat at 0.1251–0.1262 from macro-cycle 5 onward.

**Concluded.** Solvent had converged — additional cycles were shuffling marginal waters
without moving R-free. 275 waters for 127 residues (2.2 per residue) is normal for a
0.87 Å structure, so this is not water-stuffing. Stopped solvent work here.

## Step 9 — Refinement 5/6: anisotropic waters + weight optimization

**Did.** Two changes together: converted all waters to anisotropic ADPs
(`modify_start_model.modify.adp.convert_to_anisotropic` on `water`, plus the explicit
anisotropic selection — now safe because `ordered_solvent = False` removes the Step 6
conflict), and enabled `optimize_xyz_weight` + `optimize_adp_weight`. 4 macro-cycles.

I combined two changes in one slot deliberately. Both are near-certain wins at 0.87 Å,
and with a spare run in hand the downside was bounded: had R-free regressed I would have
fallen back to the Step 8 model and used the last slot to apply only one of them.

**Measured.** Log confirms `aniso = 1356` (1081 protein + 275 water) and `iso = 1091`
(H only). R-work **0.1071**, R-free **0.1199**. Bond RMSD 0.009 Å, angle 1.20°.
Clashscore 4.11, Rama 0.00% outliers / 99.20% favored, rotamer 0.00%. Residual density
collapsed: max peak **15.8σ → 5.2σ**, with **nothing above 6σ**.

**Concluded.** Clear improvement on both R-work and R-free, so the combined change was
kept. Restraint RMSDs loosened slightly (0.007 → 0.009 Å bonds) because weight
optimization shifted the data/restraint balance — appropriate at subatomic resolution,
where 0.009 Å is still tight, and validated by the fact that clash/Rama/rotamer scores
did not degrade.

*Caveat I want on the record:* Phenix's weight optimization consults R-free when
selecting weights, so my self-measured R-free is mildly optimistic as a fully
independent statistic. The R-work/R-free gap (0.0136) is small and healthy, and the
independent geometry oracles are untouched by this, but the benchmark's re-measurement
is the number to trust.

## Step 10 — Refinement 6/6: final polish

**Did.** Continued from the Step 9 model with identical settings, 5 macro-cycles, no
solvent update. I chose polish over one more solvent pass because the residual map was
already clean (max 5.2σ, nothing > 6σ, only 20 water-like peaks left), whereas another
`ordered_solvent` run against 275 now-anisotropic waters risked re-triggering the
Step 6 crash and wasting the final slot for a marginal gain.

**Measured.** R-work **0.1059**, R-free **0.1195**. Independently re-measured with
`phenix.model_vs_data`: R-work **0.1059**, R-free **0.1195** — exact agreement.

**Concluded.** Improvement over Step 9 was 0.0012/0.0004 — marginal gains had vanished,
which was my stated stopping criterion, and the budget was spent regardless.

---

## Final model

`final.pdb` (from `r6_001.pdb`), chosen because it is best on **both** R-work and
R-free among all six candidates.

| Run | R-work | R-free | Waters |
|---|---|---|---|
| perturbed input | 0.3979 | 0.4103 | 154 |
| 1/6 xyz+ADP | 0.1314 | 0.1415 | 154 |
| 2/6 (crashed) | — | — | — |
| 3/6 solvent | 0.1227 | 0.1309 | 212 |
| 4/6 solvent, no final filter | 0.1159 | 0.1262 | 275 |
| 5/6 aniso waters + weight opt | 0.1071 | 0.1199 | 275 |
| **6/6 polish (final)** | **0.1059** | **0.1195** | **271** |

Self-measured final statistics (confirmed by `phenix.model_vs_data`):

- **R-work 0.1059 / R-free 0.1195**, gap 0.0136
- Bond RMSD 0.009 Å, angle RMSD 1.20°
- Clashscore **4.57**
- Ramachandran **0.00% outliers, 99.20% favored**
- Rotamer outliers **0.00%**
- Residual density: max +5.23σ, min −3.43σ, **no peak above 6σ**
- 127 residues, 1081 protein heavy atoms (**identical set to the input — none lost,
  none invented**), 1091 riding H, 271 waters, all 1356 heavy atoms anisotropic

## Compliance notes

- No network access of any kind; no `phenix.fetch_pdb`, `curl`, or `wget`.
- No deposited coordinates consulted. The only file read from
  `/tmp/nc_round1_cache/` was `8ere.mtz`. No `ref/` or `data/` tree in this repository
  was read, and no `*_mask.json` or `*_validation.xml` was opened.
- 6 counted refinement invocations; 1 uncounted PHIL-rejected launch, annotated above.
- Every shell command is recorded verbatim and in order in `transcript.md`.
