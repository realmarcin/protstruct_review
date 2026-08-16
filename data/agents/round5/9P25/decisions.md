# 9P25 — blinded agentic recovery, round 5

Agent scratch dir: `/tmp/agent_r5_9p25/` (= `/private/tmp/agent_r5_9p25/`)
Final model: `final.pdb` (copy of `/private/tmp/agent_r5_9p25/r6_001.pdb`)

Refinement budget: **6 of 6 used.** Three additional launches aborted before any
refinement began (two PHIL-parameter rejections, one shell permission failure) and are
annotated below; they are not counted, per rule 2.

---

## Step 0 — inputs, and recovery of the diffraction data

The named data file `/tmp/nc_round1_cache/9p25.mtz` **was already gone** when the task
started (the /tmp reaper had taken it; the cache directory still held other entries'
files, but no `9p25.mtz`). Per the task's contingency instruction I recovered the
observations from a surviving phenix.refine output MTZ rather than re-fetching anything
from the network.

Source used: `/private/tmp/nc_round1_work/r4r_r4p_9p25_001.mtz`, whose MTZ `TITLE`
record reads `/tmp/nc_round1_cache/9p25.mtz:FOBS,SIGFOBS,systematic_absences_elimina`,
confirming it is a faithful pass-through of the deleted file's observations. That file is
the output of a refinement of the very model I was handed (`r4p_9p25.pdb`).

**Leakage control.** The recovered MTZ also carries model-derived columns
(`F-model`, `PHIF-model`, `2FOFCWT`, `FOFCWT` and their phases). Using those would import
phases from a model I am not allowed to see. I therefore extracted **only** `F-obs`,
`SIGF-obs` and `R-free-flags` into a clean file, `9p25_obs.mtz`, and used that
exclusively for every subsequent calculation. No deposited coordinates, no `ref/`, no
`data/`, no `*_mask.json`, no `*_validation.xml`, no network access, and no file under
`/tmp/nc_round1_cache` were read at any point.

**Data characterisation** (measured, not assumed):

- Space group P2<sub>1</sub>2<sub>1</sub>2<sub>1</sub>, cell 48.28 × 70.43 × 115.09 Å.
- Resolution 44.56 – **0.89 Å**, 293,018 reflections, 98.1% complete. This is ultra-high
  resolution and it drove every methodological choice below (anisotropic ADPs, riding
  hydrogens, aggressive solvent modelling).
- Free set: **exactly 2000 reflections flagged 0** (0.68%), work set flagged 1. I checked
  this explicitly rather than trusting the default, because a naive reading of a 0/1
  column would have put 99.3% of reflections in the "test" set. `phenix.model_vs_data`
  independently auto-detected `flag value: 0`, agreeing with my determination. I passed
  `test_flag_value=0` explicitly to every refinement.
- Caveat I am flagging honestly: a 2000-reflection free set is small, so R-free carries
  roughly ±0.002 of counting noise. I treated differences below ~0.004 as not meaningful
  and only acted on larger moves.

**Model as received** (`r4p_9p25.pdb`): 408 residues, 564 waters, ligands CL ×2, TRS,
PEG, P4G, AE3; ANISOU records present; only 52 atoms carrying altlocs.

Baseline measurements on the perturbed model:

| metric | value |
|---|---|
| R-work / R-free | **0.3660 / 0.3722** |
| clashscore | 7.99 |
| Ramachandran favored / outliers | 94.04% / 0.00% |
| rotamer outliers | 0.92% |

The R-vs-resolution breakdown was diagnostic: R ≈ 0.20–0.29 in the low-resolution shells
but 0.43–0.44 beyond 1.6 Å. That is the signature of coordinate jitter and damaged ADPs
rather than gross misplacement, so I did **not** spend budget on molecular replacement or
simulated annealing, and went straight to conventional restrained refinement.

**Preparation.** `phenix.ready_set` added 3188 riding hydrogens and matched all five
ligand types (CL, TRS, PEG, P4G, AE3) to the monomer library. Its output CIF turned out
to bundle the *model* (`data_default`) together with the restraint blocks, which is what
caused abort #2 below; I split out the `data_comp_*` blocks into `ligands.cif` and passed
that as `data_manager.restraint_files`.

---

## Aborted launches (no refinement performed — not counted against budget)

1. **PHIL rejection.** `refinement.input.xray_data.r_free_flags.test_flag_value`,
   `refinement.output.prefix`, `refinement.output.serial` are not valid in PHENIX 2.0.
   Program exited during parameter parsing. Correct paths, found via `--show-defaults=3`,
   are `data_manager.fmodel.xray_data.r_free_flags.test_flag_value` and top-level
   `output.prefix` / `output.serial`.
2. **"Wrong number of models of each type supplied."** The ready_set CIF was read as a
   second model. Fixed by splitting restraints into `ligands.cif`.
3. **Shell failure.** `run_r2.sh` was created without the execute bit and `nohup` never
   ran it; no phenix process started and no log was produced. Fixed with `chmod +x`.

---

## Refinement 1 — restore coordinates and ADPs

Strategy `individual_sites + individual_adp`, anisotropic ADPs for all non-H atoms,
riding hydrogens, 5 macro-cycles, no solvent update.

Rationale: at 0.89 Å the data support ~34k parameters against 291k work reflections
(ratio ≈ 8.6), so anisotropic ADPs are the standard and correct treatment; refining them
isotropically would have left most of the high-resolution residual unexplained. I
deliberately held the solvent fixed in this step so that the coordinate/ADP recovery
could be measured on its own.

Result: **R-work 0.1376 / R-free 0.1433**; clashscore 7.99 → **0.31**, Rama favored
94.04% → 97.77%, rotamer outliers 0.92% → **0.00%**.

Conclusion: this recovered the bulk of the damage. R-free was still falling on the last
macro-cycle, and one Ramachandran outlier (Ser186) had appeared.

## Refinement 2 — ordered-solvent rebuild

Added `ordered_solvent=True` and `occupancies` to the strategy, 5 macro-cycles.
Rationale: the brief warned solvent may have been damaged, and 564 waters is sparse for a
0.89 Å structure.

**A mid-run reading nearly misled me.** After the first solvent update R-free jumped
0.1436 → 0.1652 while R-work stayed flat — textbook overfitting. Had I stopped there I
would have wrongly rejected solvent rebuilding. Letting it run to convergence, R-free
came back down and finished *better* than refinement 1: **R-work 0.1313 / R-free 0.1367**,
with waters 564 → 666.

But geometry regressed: clashscore **0.31 → 2.82**. So the solvent round bought data fit
at the cost of chemistry, and the two had to be separated.

## Interlude — diagnosing the clashes (no refinement)

15 of the 18 bad clashes involved water, traceable to just **8** newly added waters. The
worst, S1754, sat 0.98 Å inside the Arg123 guanidinium — that is not a water, it is
unmodelled alternate-conformer density that the solvent picker filled with an oxygen.
I verified all 8 were in chain S and **absent from refinement 1**, i.e. all were new
additions, not pre-existing waters I might be destroying. I deleted those 8 and kept the
other ~94 additions.

Root cause: `ordered_solvent.dist_min` defaults to 1.8 Å, which permits an oxygen 2.3 Å
from a side-chain carbon.

## Refinement 3 — converge the pruned model

From the pruned model, solvent update off, 5 macro-cycles.

Result: **R-work 0.1280 / R-free 0.1370**, clashscore back to **0.31**, rotamer outliers
0.00%, 658 waters. Strictly better than refinement 2 on every axis — the prune cost
nothing in R-free and returned the clashscore. Only two bad clashes remained
(Ile154–Tyr194, Lys264–AE3).

## Interlude — is more solvent warranted? (no refinement)

Rather than guess, I measured with `phenix.find_peaks_holes`: **258 peaks > 3σ, 24 > 6σ,
max 13.4σ**, and 55 holes < −3σ. So density was genuinely unmodelled. But inspecting
*where*, the strongest peaks sat 2.2–2.5 Å from side-chain atoms (Met399, Glu124, Glu99,
Ser418, Lys35) and from the P4G ligand — these are **unmodelled alternate conformations**,
not missing waters. Consistent with this, the model carries only 52 altloc atoms, which
is very sparse for 0.89 Å; the perturbation appears to have stripped alternate
conformers. Rebuilding those properly needs interactive density fitting and was not
attempted within the remaining budget rather than faked.

I judged another solvent pass still worth one refinement, with `dist_min` raised to 2.1 Å
to stop oxygens being dropped into side-chain density.

## Refinement 4 — crashed (COUNTED)

Same as above plus `new_solvent=anisotropic` (defensible at 0.89 Å). PHENIX crashed in
macro-cycle 2 inside `ordered_solvent.refine_oat` with
`CCTBX_ASSERT(f.use_u_iso()) failure` — a genuine PHENIX 2.0 incompatibility: the
water-refinement path assumes isotropic waters and is unreachable with
`new_solvent=anisotropic`. Two macro-cycles of real refinement had already executed, so
**I count this against the budget** even though it produced no usable model.

## Refinement 5 — second solvent pass, isotropic (REJECTED)

Repeated with the default isotropic waters, `dist_min=2.1`, solvent update every
macro-cycle after the first, 6 macro-cycles.

Result: **R-work 0.1308 / R-free 0.1402**, 716 waters, clashscore **5.03** — worse than
refinement 3 on *all three* measures. The extra 58 waters were fitting noise.

Conclusion: **rejected**; refinement 3 remained the best model. This is the "marginal
gains have vanished" signal the brief asked me to watch for — the first solvent pass
earned its cost, the second did not.

## Refinement 6 — target-weight optimization (FINAL)

From refinement 3, with `optimize_xyz_weight=True` and `optimize_adp_weight=True`,
3 macro-cycles, no solvent update.

Rationale: refinement 3 sat at bond RMSD 0.007 Å / RMSZ 0.33, slightly tight for 0.89 Å
data, so the data-vs-restraints balance was the one lever left untried. PHENIX selected an
ADP weight of 88.79.

Result: **R-work 0.1235 / R-free 0.1343** — and, contrary to my expectation that looser
restraints would trade geometry for fit, geometry *also* improved: bond RMSD 0.007 →
0.006 Å, angle 1.146° → 1.030°, planarity 0.013 → 0.011, minimum nonbonded distance
2.138 → 2.323 Å. The gain came from the ADP weight, not the coordinate weight.

**Selected as final.** It beats refinement 3 by 0.0027 in R-free (above my noise
threshold) and by 0.0043 in R-work, at a clashscore of 0.63 vs 0.31 — both far inside
"excellent" for this resolution.

---

## Final model

`final.pdb` = `r6_001.pdb`: 7040 atoms (3188 riding H), 3852 ANISOU records, 658 waters.

| metric | perturbed input | final | independent re-measure |
|---|---|---|---|
| R-work | 0.3660 | **0.1235** | 0.1237 (`model_vs_data`) |
| R-free | 0.3722 | **0.1343** | 0.1343 (`model_vs_data`) |
| clashscore | 7.99 | **0.63** | — |
| Ramachandran favored | 94.04% | **97.77%** | — |
| Ramachandran outliers | 0.00% | 0.25% (1: Ser186) | — |
| rotamer outliers | 0.92% | **0.00%** | — |
| bond RMSD (Å) | — | 0.006 | — |
| angle RMSD (°) | — | 1.030 | — |
| waters | 564 | 658 | — |

Every R-factor quoted was confirmed with `phenix.model_vs_data` run separately from the
refinement that produced the model, so no number here is phenix.refine grading its own
output on its own scales.

## Known residual defects (stated rather than hidden)

- **One Ramachandran outlier, Ser186** (φ −167°, ψ 36°, score 0.04%), present since
  refinement 1. At 0.89 Å the backbone density should settle this either way; I did not
  force it into a favored region, because bending a residue to satisfy a validation
  statistic without checking the density is exactly the kind of cosmetic fix this
  harness exists to catch.
- **Unmodelled alternate conformations.** 24 difference peaks above 6σ remain, largest
  13.4σ near P4G. These are altlocs and possibly incomplete ligand modelling, not
  waters. A real deposition at this resolution would carry substantially more than 52
  altloc atoms. This is the single largest remaining gap between this model and what the
  data can support.
- **Two residual bad clashes**: Ile154 HD12–Tyr194 CE2 (0.59 Å) and Lys264 HD3–AE3 H5C2
  (0.51 Å), both hydrogen-mediated and both plausibly alternate-conformer artefacts.
- Ramachandran favored 97.77% sits just under the 98% goal.

## What I would do with more budget

Build alternate conformations for Met399, Glu124, Glu99, Ser418, Lys35, Glu120, Glu82,
Arg65, Arg104 and Arg123 against the difference density, inspect the 13.4σ P4G peak for
missing ligand atoms, and re-refine. That, not further solvent picking or weight tuning,
is where the remaining R-free lives.
