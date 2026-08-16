# 9TXE blinded agentic recovery — decisions

Agent scratch dir: `/tmp/agent_r5_9txe/`
Deliverable: `final.pdb` (copied from `/tmp/agent_r5_9txe/final_candidate.pdb`)

Refinement-program invocations used: **6 of 6** (runs r1–r6, all of which actually
performed refinement; no failed or aborted launches).

---

## Step 0 — Input data had to be recovered (the /tmp reaper struck)

**What I did.** The named input `/tmp/nc_round1_cache/9txe.mtz` did not exist when I
started; only `9txe.mtz.sha256` and unrelated files remained under that directory. Per
the task's stated fallback I recovered the observations from a phenix.refine output MTZ
rather than the network.

**Which source and why.** I used `/tmp/nc_round1_work/r4r_r4p_9txe_001.mtz`. Its MTZ
TITLE records its own provenance verbatim — `/tmp/nc_round1_cache/9txe.mtz:FOBS,SIGFOBS,
systematic_absences_elimina` — and its dataset 1 is labelled
`Original-experimental-data-mapped-to-asu`. That is a faithful copy of the observations
I was supposed to be given.

**Hygiene applied.** That MTZ also carries `F-model`, `PHIF-model`, `2FOFCWT`,
`PH2FOFCWT`, `FOFCWT`, `PHFOFCWT` — all model-derived. I did **not** refine against that
file. I extracted only `F-obs`, `SIGF-obs` and `R-free-flags` with a cctbx script
(`strip.py`) and wrote a clean `9txe_obs.mtz` containing exactly H K L, FOBS, SIGFOBS,
FreeR_flag. Every subsequent refinement read only that stripped file, and every
phenix.refine call additionally passed `refinement.main.target=ml` and
`main.use_experimental_phases=False` as belt-and-braces against an MLHL switch.

**What I deliberately did not touch.** No network access of any kind. I never read this
repository's `ref/` or `data/` trees, no `*_mask.json`, no `*_validation.xml`, and no
file under `/tmp/nc_round1_cache/` (I listed that directory to establish that the MTZ was
gone, but opened nothing in it). From `/tmp/nc_round1_work/` I opened exactly one file —
the MTZ above — and no coordinate file, log, or `.geo` from any prior round, so no
pre-perturbation or previously-recovered model informed this work.

**Verification of the recovered data.** P2<sub>1</sub>2<sub>1</sub>2<sub>1</sub>, cell
30.265 51.212 61.169 90 90 90, 59 899 reflections, 30.58–0.95 Å, 98.7 % complete,
non-anomalous. I checked the free-flag convention explicitly rather than assuming it:
value 0 occurs in 1776 reflections (2.96 %) and value 1 in 58 123 (97.04 %), so the test
set is **flag value 0**, and I passed `test_flag_value=0` to every run. Refining against
the 97 % subset would have been the obvious catastrophic error here.

## Step 1 — Characterising the damage

`phenix.model_vs_data` on the perturbed model: **R-work 0.3706, R-free 0.3759**. The two
are essentially equal, which says the perturbation erased any memory of the work/test
split — the model is uniformly displaced rather than selectively refit.

Geometry of the perturbed model, however, was largely *intact*: bonds 0.008 Å, angles
1.05°, no C-beta deviations. What was damaged was backbone conformation and packing:
clashscore 9.30, Ramachandran 1.02 % outliers / 9.18 % allowed, rotamer 1.11 % outliers,
and Rama-Z **whole −3.35, helix −4.93** (both "poor").

**Conclusion.** This is a coordinate displacement applied with geometry regularisation
afterwards, not broken chemistry. So the job is to pull atoms back into density, not to
rebuild. At 0.95 Å the radius of convergence of straight gradient refinement is narrow
but the data are extremely informative, and R ≈ 0.37 is within reach of ordinary
refinement — I judged simulated annealing unnecessary and did not spend a run on it.

Two further observations drove the strategy: the model already carried **ANISOU** records
(871 atoms) from its pre-perturbation refinement, and it had **no hydrogens**. At 0.95 Å
with 59 899 reflections, anisotropic ADPs for all non-H atoms cost 7839 parameters — 7.6
observations per parameter, comfortably supported — and discarding the existing ANISOU by
refining isotropically would have thrown away good information. Riding hydrogens are
standard at this resolution and improve both R and clash detection.

## Step 2 — `phenix.ready_set` (not a refinement invocation)

Added 725 riding hydrogens, preserved all 871 ANISOU, and detected the four Fe–S<sub>γ</sub>
links to Cys39, Cys44, Cys47 and Cys77 (the protein is a small ferredoxin-like fold,
~100 residues, with one 2Fe-2S cluster and 90 waters).

## Step 3 — Run r1: coordinates + anisotropic ADPs, no solvent changes

`individual_sites + individual_adp + occupancies`, 8 macro-cycles, anisotropic for
`not element H`, riding H, `ordered_solvent=False`.

Deliberately left solvent alone so I could see what plain refinement recovers — re-picking
waters against a 0.37-R model would place them into noise.

**Result: R-work 0.3701 → 0.1658, R-free 0.3736 → 0.1796.** Geometry: clashscore 9.30 →
**0.66**, Rama outliers 1.02 % → **0**, rotamer outliers 1.11 % → **0**. The bulk of the
perturbation was recovered in a single run, confirming the "displaced but chemically
sound" diagnosis.

## Step 4 — Run r2: ordered-solvent rebuilding

90 waters for ~100 residues at 0.95 Å is low; 1.5–2 waters/residue is typical. Added
`ordered_solvent=True`, `mode=every_macro_cycle`.

**Result: R-work 0.1546, R-free 0.1704** (−0.009 R-free), waters 90 → 185. Geometry held
(clashscore 1.33, bonds 0.011). Solvent rebuilding earned its cost.

## Step 5 — Run r3: weight optimisation

`optimize_xyz_weight=True`, `optimize_adp_weight=True`.

**Result: R-work 0.1435, R-free 0.1592** (−0.011 R-free) — the largest single gain after
r1. But geometry regressed: bonds 0.011 → 0.017, clashscore 1.33 → **6.64**, minimum
nonbonded distance 1.85 Å.

**Diagnosis before reacting.** I listed the clashes rather than assuming the looser weights
were to blame. All eight bad clashes involved waters, one of them (S1070) overlapping the
Glu31 carboxylate by 1.08 Å. So the clashscore regression was *spurious solvent*, not the
weights. Note `ordered_solvent.dist_min` defaults to 1.8 Å, which permits a water 1.8 Å
from a protein heavy atom — physically impossible for a real water.

## Step 6 — Run r4: stricter solvent criteria + a bond-RMSD ceiling

Deleted the four clashing waters with `phenix.pdbtools`, then refined with
`ordered_solvent.dist_min=2.4` and
`target_weights.weight_selection_criteria.bonds_rmsd=0.013`.

**Result: R-work 0.1426, R-free 0.1597 — and it did not work.** Bonds stayed 0.017,
clashscore stayed 6.64. Waters were simply re-picked into the *same* positions (now named
S1335, S1278, S1104).

**What that taught me.** These positions carry genuine ≥3σ difference density, but they
are not water: they are unmodelled **alternate side-chain conformations** of Glu31, Phe0,
Glu−1 and Lys4. At 0.95 Å the automatic water picker fills alt-conformer density with
waters, which is a classic ultra-high-resolution artifact. A single distance cutoff cannot
separate them, because a legitimate H-bonded water sits 2.7–3.1 Å from N/O while these sit
~2.4 Å from carbon.

I considered building the alternate conformations explicitly. With two runs left and no
interactive density-fitting tool available, a botched alt-conf split would have cost more
than it returned, so I chose not to. This is the clearest remaining improvement available
to a future pass on this structure.

## Step 7 — Run r5: stop picking, keep filtering

Deleted the three re-picked spurious waters and refined with
`ordered_solvent.mode=filter_only` (existing waters still filtered on map criteria, no new
ones added) plus weight optimisation.

**Result: R-work 0.1438, R-free 0.1590 — best R-free of the whole series — with clashscore
back to 0.66** and a single marginal H–H contact (Glu71 HG2 / Trp73 HD1, 0.416 Å) as the
only bad clash. Bonds 0.014 Å (RMSZ 0.66), 170 waters.

## Step 8 — Residual-density check before spending the last run

`phenix.find_peaks_holes`: max peak 7.47σ, only two peaks > 6σ, none > 9σ, deepest hole
−3.87σ. That is a well-modelled structure at this resolution.

Locating the strongest peaks against the model showed most are H-bond-distance water sites
that `filter_only` had forbidden r5 from adding (2.73 Å from Ser46 OG, 3.06 Å from Tyr37 N,
2.67 Å from Asp26 OD2, 2.75 Å from HOH202). One peak, 5.70σ at 1.96 Å from Leu95 C, was
different: **Leu95 is the C-terminal residue and its OXT atom was missing entirely.** I
added OXT at proper sp2 carboxylate geometry (C–OXT 1.251 Å, direction bisecting the
CA–C–O angle) — a genuine completion of the molecule, not a fitting device.

## Step 9 — Run r6: last refinement, water picking re-enabled

From r5 + OXT, `mode=every_macro_cycle`, `dist_min=2.2`, weight optimisation.

**Result: R-work 0.1401, R-free 0.1588**, waters 212, clashscore **9.95**.

**This is the decisive measurement of the whole exercise.** R-work improved by 0.0037
while R-free improved by 0.0002. Extra parameters that fit the work set and not the free
set are, by definition, fitting noise — the 37 added waters are overfitting, and they
restored exactly the Glu31/Glu30/Phe0/Lys4/Lys91 clashes seen in r3 and r4. The refined
OXT landed 0.09 Å from my geometric placement, confirming that placement.

## Step 10 — Choosing the deliverable (no refinement budget left)

Three candidates, all re-measured identically with `phenix.model_vs_data` and
`phenix.clashscore`:

| candidate | R-work | R-free | R-free − R-work | clashscore | waters |
|---|---|---|---|---|---|
| r5_001 (run 5) | 0.1438 | 0.1589 | 0.0151 | 0.66 | 170 |
| r6_001 trimmed of 5 clashing waters | 0.1406 | 0.1602 | 0.0196 | 1.33 | 207 |
| **r5_001 + refined OXT (chosen)** | **0.1438** | **0.1600** | **0.0162** | **0.66** | **170** |

R-free is statistically indistinguishable across all three: with only 1776 free
reflections the standard error on R-free is roughly R-free/√(2N) ≈ 0.003, so the 0.001
spread is noise. Given that, I chose on the criteria that are *not* noise — clashscore
(0.66 vs 1.33), the R-free minus R-work gap (0.0162 vs 0.0196, i.e. less overfitting), and
chemical completeness (OXT present). Including OXT costs ~0.001 R-free, which is inside
the noise, while omitting a real atom of the molecule is a genuine model defect; so the
grafted-OXT model wins on both counts.

Trimming waters after the final refinement is a model edit, not a refinement, and it is
the honest move: those waters were demonstrably fitting alt-conformer density.

## Final self-measured state of `final.pdb`

Measured with `phenix.model_vs_data` (fit) and `mmtbx.model.geometry_statistics` /
`phenix.clashscore` / `phenix.ramalyze` / `phenix.rotalyze` (geometry) — these are advisory;
the benchmark re-measures independently.

| metric | perturbed input | final.pdb |
|---|---|---|
| R-work | 0.3706 | **0.1438** |
| R-free | 0.3759 | **0.1600** |
| clashscore | 9.30 | **0.66** |
| Ramachandran outliers | 1.02 % | **0.00 %** |
| Ramachandran favored | 89.80 % | **98.98 %** |
| rotamer outliers | 1.11 % | **0.00 %** |
| Rama-Z (whole) | −3.35 (poor) | **−0.36 (good)** |
| Rama-Z (helix) | −4.93 (poor) | **+0.33 (good)** |
| bond RMSD | 0.008 Å | 0.014 Å (RMSZ 0.66) |
| angle RMSD | 1.05° | 1.40° (RMSZ 0.76) |
| C-beta deviations | 0.00 % | 0.00 % |
| waters | 90 | 170 |

Bond and angle RMSDs rose because weight optimisation loosened the restraints, which is
appropriate at 0.95 Å where the data, not the library, should dominate; the corresponding
RMSZ values (0.66 and 0.76, both < 1) say the deviations are within the restraints' own
stated uncertainties. Rama-Z moving from −3.35/−4.93 ("poor") to −0.36/+0.33 ("good") is
the strongest single indicator that backbone conformation was genuinely recovered rather
than merely refit to the data.

Model contents: 1677 atoms — 951 anisotropic non-H atoms, 725 riding hydrogens, the intact
2Fe-2S cluster with its four Cys links (metal-coordination bond RMSD 0.011 Å), 170 waters,
and the completed C-terminal OXT.

## Known remaining defects

1. **Unmodelled alternate conformations** at Glu31, Glu30, Phe0, Glu−1, Lys4 and Lys91.
   These are the peaks the water picker kept trying to fill. Modelling them is the highest-
   value next step and would likely take R-free below 0.155 legitimately.
2. **170 waters may be conservative.** Several genuine H-bond-distance sites identified in
   step 8 remain unmodelled because r5 ran in `filter_only` mode. Adding them selectively
   (as opposed to the automatic picker's indiscriminate pass) would be a small honest gain.
3. One marginal H–H clash, Glu71 HG2 / Trp73 HD1 at 0.416 Å overlap.
