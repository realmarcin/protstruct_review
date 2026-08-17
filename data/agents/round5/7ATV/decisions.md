# 7ATV — blinded agentic recovery: decisions log

Scratch directory: `/tmp/agent_r5_7atv/`
Final model: `final.pdb` (= `/tmp/agent_r5_7atv/r6_001.pdb`)

Refinement budget: **6 of 6 phenix.refine invocations used.** No network access, no
deposited coordinates, no files read from the repo `ref/`/`data/` trees or from
`/tmp/nc_round1_cache/` other than `7atv.mtz`.

---

## Step 0 — Characterize the inputs before spending any budget

**What.** Dumped the MTZ with gemmi; inspected the perturbed PDB's composition,
B-factors, occupancies, ANISOU coverage and altlocs; ran `phenix.model_vs_data`,
`phenix.clashscore`, `phenix.ramalyze`, `phenix.rotalyze`, and a full
`mmtbx.model.geometry_statistics()` pass on the starting model.

**Why.** The strategy for an atomic-resolution case is very different from a 2.5 Å
case, and the refinement budget is small enough that a wrong first command is
expensive. I also needed to resolve the free-flag ambiguity before any refinement,
because refining against the wrong flag set silently destroys R-free.

**Measured.**

| Property | Value |
| --- | --- |
| Space group / cell | P1, 46.78 47.56 51.00 Å, 66.80 88.96 88.75° |
| Resolution | 33.28 – 0.98 Å, 189 835 reflections, 81.8 % complete |
| Data columns | `FOBS`/`SIGFOBS` (amplitudes), `IOBS`/`SIGIOBS`, plus `FWT`/`DELFWT` map coefficients |
| Free flags | `R-free-flags` (free = 0) and `R-free-flags-1` (free = 1) |
| Model | 6633 atoms; 3083 H; **all 3550 non-H atoms anisotropic**; altlocs A/B on 1241 atoms; 451 waters; ligands RXE (57 atoms, contains Br), EDO, CL |
| Start R-work / R-free | **0.3636 / 0.3499** |
| Start geometry | bond 0.0104 Å, angle 1.008°, clashscore 5.66 |
| Start MolProbity | Rama 90.49 % favored / 0.61 % outliers, **Rama-Z −4.83 (poor)**, rotamer outliers 1.51 % |

**Concluded.**

1. *The two free-flag columns are the same test set.* Set-algebra on the two columns
   showed `R-free-flags == 0` and `R-free-flags-1 == 1` select an identical 1931
   reflections among those with observed FOBS. No ambiguity; I used
   `R-free-flags` with `test_flag_value=0` for every run so all numbers are
   comparable. **The test set is only 1.02 % of the data (1931 reflections)**, so
   σ(R-free) ≈ 0.0023 — differences below ~0.005 are near noise. This mattered a
   great deal later.
2. *The perturbation is a coordinate shake, not a B-factor or occupancy scramble.*
   B-factors were sane (mean 17.2 Å², waters 29.3 Å²) and occupancies summed
   correctly over altloc pairs, but R had blown up to 0.36 and Rama-Z to −4.83.
3. *RXE needs no external CIF.* I confirmed `chem_data/geostd/r/data_RXE.cif` and
   `geostd/e/data_EDO.cif` exist and that a restraints build produced no
   unknown-residue warnings — so `phenix.ready_set`/`elbow` was unnecessary and the
   ligand would not be distorted by missing restraints.
4. Anisotropic ADPs must be preserved: at 0.98 Å there are ~53 reflections per non-H
   atom, which comfortably supports 9 parameters/atom.

I also verified the correct PHIL paths with `--show-defaults` after a first
`phenix.refine` invocation was rejected for an unrecognized parameter. That failed
call did no refinement (it exited during parameter parsing) and is not counted
against the budget; it is recorded in the transcript.

---

## Step 1 — Refinement 1/6: coordinate recovery

**What.** `phenix.refine` from the perturbed model:
`individual_sites + individual_sites_real_space + individual_adp + occupancies`,
anisotropic ADPs for `not element H`, isotropic for H, 6 macrocycles, automatic
weights, **no** solvent update.

**Why.** Recover coordinates first and measure how much plain refinement buys,
before confounding it with solvent rebuilding. A 0.2–0.3 Å shake is well inside the
radius of convergence of reciprocal-space refinement, and phenix's default strategy
already includes real-space refinement, which helps most here. Withholding the
solvent update also avoids picking waters out of a still-bad map.

**Measured.** R-work 0.3636 → **0.1383**, R-free 0.3499 → **0.1539**. Clashscore
5.66 → 1.29. Rama outliers 0.61 % → **0.00 %**, favored 90.49 % → 97.24 %, Rama-Z
−4.83 → **−0.54 (good)**. Rotamer outliers 1.51 % → 0.90 %. Bond 0.0104 → 0.0075 Å,
angle 1.008 → 1.011°. ML coordinate error 0.05 Å.

**Concluded.** One refinement recovered essentially all of the damage. Everything
after this point is a much smaller optimization, so the remaining 5 runs should be
spent carefully rather than repeating this step.

---

## Step 2 — Where is the remaining signal? (free measurement)

**What.** `phenix.find_peaks_holes` on the run-1 model and map.

**Why.** Before spending budget on solvent rebuilding or weight tuning, check
whether unmodeled density actually exists and what it looks like.

**Measured.** 230 peaks > 3σ, 14 > 6σ, 3 > 9σ, max 16.6σ; 65 holes < −3σ, min
−4.8σ; 7 existing waters sitting under their own > 3σ peak. The great majority of
peaks lie 2.4–3.0 Å from a protein N or O.

**Concluded.** That distance signature is unmodeled *water*, not a misplaced main
chain. The perturbation did damage solvent structure. Ordered-solvent rebuilding is
worth a run.

---

## Step 3 — Refinement 2/6: ordered-solvent rebuilding

**What.** Same strategy plus `ordered_solvent=True`,
`mode=every_macro_cycle_after_first`, 6 macrocycles, default picking parameters.

**Measured.** Waters 451 → 775 during refinement, then phenix's own final filter cut
back to 653. R-work 0.1383 → **0.1352**, R-free 0.1539 → **0.1476** (confirmed
independently by `phenix.model_vs_data`: 0.1352 / 0.1475). But **clashscore
regressed 1.29 → 5.02**, minimum non-bonded distance 2.39 → 2.14 Å.

**Concluded.** Solvent rebuilding is a genuine gain on fit (ΔR-free = −0.006) but it
introduced a geometry problem that must be dealt with rather than accepted.

---

## Step 4 — Diagnose the clashes instead of accepting the trade (free)

**What.** Ran `phenix.clashscore verbose=True` on both the run-1 and run-2 models and
diffed the clash lists. Also wrote a neighbour-search audit of every water.

**Why.** "R-free improved, clashscore worsened" is not a verdict — it is a question
about *which atoms* got worse. The answer determines whether the fix is a different
weight, different water picking, or simple deletion.

**Measured.** Run 1 had 8 clashes; run 2 had 30. Twelve of the new ones involve
newly-added chain-S waters jammed into protein side chains (e.g. HOH S1334 overlapping
Lys77 CD/CE *and* Glu28 CG/CD — a water inside a lysine).

My own geometric audit initially flagged 93 waters, but I discarded that number: it
ignored altloc compatibility, so it counted A-vs-B conformer contacts that are not
real clashes. MolProbity handles altlocs correctly, so I used its list instead. This
is the one place where my first analysis was wrong and I threw it away.

**Concluded.** The regression is *added waters*, not the protein. Deleting the 12
clashing chain-S waters — a pure geometry edit using no diffraction data, and no
refinement budget — dropped **clashscore 5.02 → 1.94** while leaving R essentially
unchanged (0.1358 / 0.1480). I kept the pre-existing chain-A waters even where one
(HOH A700, against Leu214) clashes, because it came with the given model and is
likely an unmodeled Leu214 alternate conformation rather than my error.

---

## Step 5 — Refinement 3/6: weight optimization (rejected)

**What.** From the cleaned run-2 model: `optimize_xyz_weight=True`,
`optimize_adp_weight=True`, plus stricter solvent picking
(`primary_map_cutoff=3.5`, `poor_cc_threshold=0.80`, `dist_min=2.0`), 5 macrocycles.

**Why.** At atomic resolution the restraint/data balance is the largest remaining
lever, and phenix's optimizer chooses it against R-free.

**Measured.** R-work **0.1282**, R-free **0.1417** — the best fit of any run. But
bond RMSD 0.009 → **0.021 Å**, angle 1.117 → **1.638°**, chirality 0.088 → 0.123,
clashscore 7.28. The log shows the optimizer selected wxc ≈ 24.3 in the first two
macrocycles against the automatic value of ≈ 2.85 — an **8.5× stronger data weight**.

Cleaning 17 clashing waters (free) brought clashscore to 1.78 and left R-work 0.1292 /
R-free **0.1437**, with 0 Rama outliers and the best rotamer outlier rate seen
(0.60 %). On the headline validation metrics this model looked like the winner.

**So I checked the bonds individually** — and this is why the entry is not that model:

| bond | model | ideal | Δ |
| --- | --- | --- | --- |
| EDO 401 C2–O2 | 1.156 Å | 1.410 Å | 0.254 |
| Ile95 CG1–CD1 | 1.303 Å | 1.513 Å | 0.210 |
| Met164 SD–CE | 1.609 Å | 1.791 Å | 0.182 |
| Ile95 CB–CG1 | 1.690 Å | 1.530 Å | 0.160 |

**Concluded — rejected.** A 1.16 Å C–O bond is not chemistry, it is a side chain
being stretched to chase noise and unmodeled alternate-conformer density. The
bond RMSZ of 1.02 could be argued as "correctly relaxed for 0.98 Å data", but the
individual outliers cannot be defended, and the R-free gain was being purchased with
them. **Selecting a weight to minimize R-free on a 1931-reflection test set is
exactly the overfitting trap this small test set invites**, so I discarded the
optimized weight and kept the model only as a coordinate starting point.

---

## Step 6 — Refinement 4/6: restore geometry at the automatic weight

**What.** From the cleaned run-3 model, back to the automatic weight
(`wxc_scale` at its 0.5 default), ordered solvent on, 8 macrocycles.

**Measured.** R-work 0.1343, R-free 0.1475; bond back to **0.009 Å**, angle 1.117°;
671 waters. After removing 12 clashing waters (free): clashscore 1.94, R-work 0.1351 /
R-free 0.1481, 654 waters.

**Concluded.** Geometry fully restored, and R-free returned to ~0.148 — confirming
that run 3's 0.1417 was bought with the distorted bonds, not earned.

---

## Step 7 — Refinement 5/6: is there a defensible middle weight?

**What.** `wxc_scale=1.0` — a deliberate, *bounded* 2× relaxation (against the
optimizer's 8.5×), ordered solvent on, 6 macrocycles.

**Why.** Relaxing restraints at d ≤ 1.0 Å is legitimate practice; I wanted to know
whether a modest, pre-chosen relaxation gains R-free without breaking bonds — rather
than letting an optimizer pick the weight on a 1 % test set.

**Measured.** R-work 0.1315, R-free **0.1486**; bond 0.013 Å, angle 1.344°. The
work–free gap widened from 0.0130 to 0.0174.

**Concluded — rejected.** R-work improved and R-free did not. That is the textbook
signature of overfitting, and it settles the question: at this resolution and with
this test set, **relaxing the weight buys nothing real.** The automatic weight is
correct here.

---

## Step 8 — Water quality filtering (free)

**What.** `phenix.real_space_correlation detail=residue` on the run-4 model; then
built variants of the cleaned model with waters removed below real-space CC
thresholds of 0.5 / 0.6 / 0.7 and measured each with `phenix.model_vs_data`.

**Why.** Run 3 had the fewest waters and the lowest R-free, which raised the
hypothesis that the water count itself was overfitting. A density-based filter is
the principled test — and it is phenix's own ordered-solvent criterion
(`poor_cc_threshold = 0.70`), just applied to every water rather than only at
picking time.

**Measured.** Ligands are all well supported and stay in the model: **RXE CC 0.979,
CL 0.978, EDO 0.897**. But 162 of 646 waters fell below CC 0.70, 93 below 0.60, and
39 below 0.50 — some with *negative* correlation.

| model | waters | R-work | R-free |
| --- | --- | --- | --- |
| run-4 cleaned | 654 | 0.1351 | 0.1481 |
| CC < 0.5 removed | 620 | 0.1357 | 0.1475 |
| **CC < 0.6 removed** | **567** | 0.1364 | **0.1454** |
| CC < 0.7 removed | 499 | 0.1374 | 0.1474 |

**Concluded.** CC < 0.6 is the best cut: R-work rises slightly (expected — fewer
atoms) while R-free falls, which is what removing overfit atoms looks like. The
non-monotonic behaviour at 0.7 shows we are partly in the noise, so I did not tune
the threshold further. I also checked EDO specifically because it clashes with
Asp176 in every model — its CC of 0.897 says it is real density, so the clash is a
hydroxyl-hydrogen torsion artefact and deleting the ligand would have been wrong.

---

## Step 9 — Refinement 6/6: final settle

**What.** From the CC-filtered model: automatic weight, **solvent update off**,
6 macrocycles.

**Why.** Last run in the budget. Solvent off so no new junk waters could be
introduced at the final step; the water set had already been curated by two
independent criteria (MolProbity clashes and real-space CC).

**Measured.** R-work **0.1327**, R-free **0.1481**; bond **0.0074 Å**, angle
**1.003°**; 567 waters.

Applying the CC < 0.6 filter again removed only 11 more waters and made both R
factors slightly worse (0.1331 / 0.1487), so I did **not** apply it — the water set
had converged.

---

## Final selection

Budget exhausted, three sound-geometry candidates:

| candidate | R-work | R-free | bond | angle | clash | note |
| --- | --- | --- | --- | --- | --- | --- |
| run-4 cleaned | 0.1351 | 0.1481 | 0.009 | 1.117 | 1.94 | |
| run-4 + CC<0.6 | 0.1364 | **0.1454** | 0.009 | 1.117 | 1.94 | not re-refined after deletion |
| **run 6 (chosen)** | **0.1327** | 0.1481 | **0.0074** | **1.003** | **1.78** | |
| *(run-3 cleaned)* | *0.1292* | *0.1437* | *0.021* | *1.638* | *1.94* | **rejected — broken bonds** |

I chose the run-6 model. It wins on four of five metrics, and the one number it
loses on — R-free 0.1481 vs 0.1454 — is a 0.0027 difference against σ(R-free) ≈
0.0023, i.e. about 1.2σ, on a test set of 1931 reflections. The CC<0.6 variant's
anomalously small work–free gap (0.0090, against 0.013–0.017 for every other model
measured) is itself a hint that its R-free is a downward fluctuation rather than a
better model. Submitting a fully-refined, self-consistent model with the best
geometry is the honest call; chasing 0.003 in R-free on a 1 % test set is not.

## Final model vs. starting model

| metric | perturbed input | final.pdb |
| --- | --- | --- |
| R-work | 0.3636 | **0.1327** |
| R-free | 0.3499 | **0.1481** |
| bond RMSD | 0.0104 Å (max 0.075) | **0.0074 Å (max 0.062)** |
| angle RMSD | 1.008° | **1.003°** |
| chirality / planarity | 0.083 / 0.008 | 0.084 / 0.012 |
| clashscore | 5.66 | **1.78** |
| Rama favored / outliers | 90.49 % / 0.61 % | **97.24 % / 0.00 %** |
| Rama-Z (whole) | −4.83 (poor) | **−0.78 (good)** |
| rotamer outliers | 1.51 % | **0.90 %** |
| C-beta deviations | 0.00 % | 0.00 % |
| waters | 451 | 567 |

Anisotropic ADPs on all non-H atoms, altlocs, and all three ligands (RXE, EDO, CL)
were preserved throughout.

## Known residual issues

- **Rotamer outliers 0.90 %** (3 residues) against MolProbity's < 0.3 % goal. Fixing
  these properly needs manual rebuilding or alternate-conformer modelling.
- **Unmodeled alternate conformations.** Both phenix's water picker and I kept
  finding residual density adjacent to side chains that is almost certainly a second
  conformer, not solvent — this is what generated the clashing waters at every
  solvent step, and it is also where run 3's loose weight did its damage. Building
  those altlocs (Coot/qFit) is the single largest remaining improvement and was out
  of reach with the available tools.
- **EDO 401** clashes with Asp176 via a hydroxyl H whose torsion is not well
  determined. The ligand itself is real (CC 0.897); only the H placement is at fault.
- Three ligand-related MolProbity "clashes" are chemistry, not error: the Ile117
  O···Br2 contact is a halogen bond.
