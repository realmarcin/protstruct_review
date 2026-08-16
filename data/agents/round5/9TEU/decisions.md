# 9TEU blinded recovery — decisions log

Agent working directory: `/tmp/agent_r5_9teu/`
Inputs: `/tmp/nc_round1_work/r4p_9teu.pdb` (perturbed model), `/tmp/nc_round1_cache/9teu.mtz` (data).
Final model: `final.pdb` (copy of `/tmp/agent_r5_9teu/final_candidate.pdb`).

Refinement budget: **6 of 6 invocations used** (two of them were unproductive — one I aborted, one crashed
inside PHENIX; both had already started refining, so I counted them against the budget rather than
claiming them as free).

All R-factors quoted for comparison are measured by a single consistent yardstick —
`phenix.model_vs_data` on the written PDB — because phenix.refine's self-reported "Final R" is computed
under its own last scaling pass and is not comparable across runs. Numbers labelled "mid-run" come from
refinement logs and are used only for trend-watching.

---

## Step 0 — Characterise the data and the damage (no refinement spent)

**What I did.** Read MTZ headers with gemmi; ran `phenix.model_vs_data`, `phenix.clashscore`,
`phenix.ramalyze`, `phenix.rotalyze`, `phenix.model_statistics` on the perturbed model; scanned all
consecutive C(i)–N(i+1) peptide distances with a short Python script.

**What I measured.**

| quantity | perturbed input |
|---|---|
| resolution | 41.6 – **0.90 Å** (94.6% complete; C 1 2 1) |
| data columns | `FOBS,SIGFOBS`; free flags `R-free-flags` (flag value 0) |
| R-work / R-free | **0.3798 / 0.3878** |
| bond / angle RMSD | 0.008 Å / 0.88° |
| clashscore | 3.54 |
| Ramachandran | 0 outliers, **93.80% favored** |
| rotamer outliers | 1.64% |
| contents | 131 residues (2–132), 1115 protein atoms, 226 waters, A/B/C altlocs, ANISOU present |

**What I concluded.** This is a *geometry-preserving* perturbation, not a coordinate jitter: bonds and
angles are already at ideal values and there are no broken peptide bonds, yet R-free is 0.388. The R
rises monotonically with resolution (0.19 in the lowest shell, 0.44 in the highest), which is the
signature of atoms displaced by a few tenths of an Ångström rather than a misplaced molecule. The
depressed Ramachandran favored fraction (93.8% against a ~98% norm) says backbone torsions were pushed
into strained-but-allowed regions. Diagnosis: reciprocal-space refinement should recover this, and
restraints will not have to fight the model.

Two red herrings I checked and dismissed:
- `phenix.ready_set` warned of a chain break between GLU 111 and LYS 112. Inspection showed the **B**
  conformer of LYS 112 simply has no N atom — an alternate-conformation modelling quirk, present in the
  input, not damage. No peptide C–N distance anywhere in the chain is anomalous.
- Data extend to 0.90 Å, so anisotropic ADPs and riding hydrogens are both justified; I added riding H
  with `phenix.ready_set` before refining.

**Canary discipline.** Every refinement command was first validated with `phenix.refine --dry-run`,
which exits before refinement starts and therefore costs nothing against the budget. This caught nothing
fatal but confirmed label selection and selection syntax on each run.

---

## Step 1 — Refinement 1/6: recover the coordinates

`individual_sites + individual_adp + occupancies`, ordered solvent on, xyz and ADP weight optimisation,
8 macrocycles. ADP type was inherited from the input (the 1307 ANISOU records were kept and refined
anisotropically); newly added waters come in isotropic.

**Result: 0.1356 / 0.1478.** Clashscore 1.77, 0 Ramachandran outliers, 287 waters (median water
B = 19.5, only 5 above B = 40 — a sane hydration shell, not padding; Matthews coefficient 2.0,
38.5% solvent).

**Concluded.** The bulk of the damage was coordinate error and it is now gone. Remaining gains must come
from the ADP model and the solvent.

## Step 2 — Refinement 2/6: full anisotropic ADPs

Same strategy from the run-1 model, adding `adp.individual.anisotropic="not element H"` so that *every*
non-hydrogen atom (including the waters added in run 1) is anisotropic. 6 macrocycles.

**Result: 0.1304 / 0.1439.** Bond 0.010 Å, angle 1.23°, clashscore 1.77, 283 waters.

**Concluded.** Anisotropic ADPs are worth ~0.004 in R-free here, as expected at 0.90 Å where the
data-to-parameter ratio (≈76 000 working reflections against ≈12 000 parameters) comfortably supports
them. Note that macrocycle 1 *transiently* pushed R up to 0.1414/0.1587 while the weight optimiser
explored; this recovered by macrocycle 3. I learned to read mid-run spikes as weight search, not failure.

## Step 3 — Difference-map diagnosis (no refinement spent)

`phenix.find_peaks_holes` on the run-2 model and its map coefficients, then a Python script classifying
every peak by its nearest protein atom and nearest water.

**What I measured.** 36 positive peaks above 4σ, 7 above 7σ, max 8.95σ — and **no negative peaks below
−4σ anywhere**. Peaks fell into three groups: one 12.5σ peak sitting exactly on HOH A 358; four peaks
1.9–2.4 Å from side-chain atoms (ARG 122 CZ, ASN 41 O, LYS 112 CD, GLU 57 CG); the rest 2.3–2.9 Å from
existing waters.

**Concluded.** The complete absence of negative density means the protein is correctly placed — nothing
is modelled where there is no density. The residual signal is solvent and alternate conformations, not
main-chain error. The side-chain-adjacent peaks indicate unmodelled alternate conformers; building those
by hand without graphics is error-prone, so I deliberately left them and spent the budget on solvent and
convergence instead.

## Step 4 — Refinement 3/6: the chloride hypothesis, tested and rejected

HOH A 358 refined to **B = 5.41 at full occupancy — the sharpest atom in the entire structure**, and
*still* carried a +12.5σ difference peak. I verified this was not an artefact of a B-factor floor
(`b_iso_min = 1.0`; only this one atom sits below B = 6). Its coordination — 3.07/3.08/3.24 Å to three
waters and 3.28 Å to the PHE 96 backbone amide — is too long for Na⁺ or Mg²⁺ but textbook for chloride,
which also supplies the missing electrons (17 vs 8).

I converted it to Cl⁻ and launched refinement.

**What I measured.** The starting R jumped from 0.1304/0.1439 to **0.1446/0.1575** on that single
substitution. I diffed the input files to confirm the chloride was the only change — it was (one HETATM
rewritten, one ANISOU dropped).

**Concluded — hypothesis rejected.** A full-occupancy chloride puts *too many* electrons at that site.
The honest reading is that the site needs somewhat more than an oxygen but much less than a chloride,
and I cannot identify the species from density alone without knowing the crystallisation buffer. Rather
than model an ion I could not justify, I **aborted the run and reverted to water**. I counted this
invocation against the budget because it had already refined two macrocycles. The site keeps its
residual peak in the final model; that is a known, documented, small imperfection, and I judged it a
smaller error than inventing a heavy atom.

## Step 5 — Refinement 4/6: crashed (PHENIX bug)

Attempted a longer run with better solvent handling: `ordered_solvent.mode=every_macro_cycle_after_first`,
`include_altlocs=True` (the default `False` was skipping exactly the peaks I had found near alternate
conformations), and `new_solvent=anisotropic`.

**What happened.** It refined macrocycle 1, added 511 waters, then died in macrocycle 2 with
`RuntimeError: cctbx Internal Error: CCTBX_ASSERT(f.use_u_iso()) failure` — `new_solvent=anisotropic`
conflicts with the ordered-solvent code's water-only ADP sub-minimisation, which assumes isotropic
waters. The parameters passed `--dry-run` validation; this is a runtime bug reachable only by actually
refining, which is precisely why a dry run is not a substitute for a canary.

**Concluded.** Counted against the budget (it had refined). With two invocations left I dropped the
experimental flags and fell back to the parameter set already proven in run 2.

## Step 6 — Refinement 5/6: convergence

Run-2 parameters exactly, from the run-2 model, extended to 12 macrocycles. The default solvent mode
`second_half` then gives six water-update opportunities instead of three.

**Result as written: 0.1302 / 0.1442**, 286 waters, clashscore 2.66 — no better than run 2.

**But the log told a different story:** at macrocycle 10 the model stood at 0.1250/0.1394 with 352
waters. The *final filtering step* then deleted ~66 waters and gave back the entire gain. Since R-free
is cross-validated, waters whose removal *raises* R-free were carrying real signal — the filter
(map-CC and B-range based) was too aggressive for this structure.

## Step 7 — Refinement 6/6: keep the waters the filter would discard

Same parameters plus `ordered_solvent.ignore_final_filtering_step=True`, 6 macrocycles.

**Result: 0.1263 / 0.1414** — the best fit of the whole session. Ramachandran favored rose to **99.22%**
and rotamer outliers halved to 0.82%. **But clashscore rose to 6.64**, and every one of the 15 bad
clashes involved an unfiltered water against protein.

**Concluded.** The fit gain is real but it arrived bundled with genuinely bad solvent contacts. Trading
geometry for R is exactly the failure mode this task warns against, so I did not stop here.

## Step 8 — Prune the clashing waters (free model edit, no refinement)

Parsed the 15 bad contacts, collected the 10 distinct waters responsible, and deleted them (and their
ANISOU records) from the model. This is a file edit, not a refinement invocation.

**What I measured.**

| | R-work | R-free | clashscore |
|---|---|---|---|
| run 6 output | 0.1263 | 0.1414 | 6.64 |
| after pruning 10 waters | **0.1271** | **0.1410** | **0.00** |

**Concluded.** R-free went *down* while every bad clash disappeared — the deleted waters were noise, not
signal, and this is a dominant improvement rather than a trade. I did not re-refine afterwards (no
budget left, and none was needed: deleting ten low-occupancy waters perturbs nothing else).

---

## Final model

`final.pdb` — 131 residues, 340 water sites (223.9 occupancy-weighted), 1143 riding hydrogens,
anisotropic ADPs on all non-hydrogen atoms, A/B/C alternate conformations retained.

| metric | perturbed input | **final** |
|---|---|---|
| R-work | 0.3798 | **0.1271** |
| R-free | 0.3878 | **0.1410** |
| clashscore | 3.54 | **0.00** |
| Ramachandran outliers | 0.00% | 0.00% |
| Ramachandran favored | 93.80% | **99.22%** |
| rotamer outliers | 1.64% | 0.82% |
| bond RMSD | 0.008 Å | 0.011 Å |
| angle RMSD | 0.88° | 1.19° |

Two waters sit on crystallographic two-folds with appropriately fractional occupancies (0.25, 0.24),
which is correct handling rather than an error.

## Known remaining imperfections (stated rather than hidden)

1. **HOH A 358 still carries a large positive difference peak.** The site wants more electrons than an
   oxygen; a full-occupancy chloride overshoots. Resolving it properly needs either the crystallisation
   conditions or an occupancy-refined ion test I had no budget left to run.
2. **One rotamer outlier: ILE 56, conformer A, occupancy 0.43.** A minor alternate conformer in weak
   density. 0.82% is above MolProbity's 0.3% goal but half the input's 1.64%.
3. **Unmodelled alternate conformations** near ARG 122, ASN 41, LYS 112 and GLU 57, identified as
   difference peaks 1.9–2.4 Å from those side chains. Building them would likely take R-free below 0.135,
   but hand-building alternate conformers without interactive graphics risks doing more harm than good.
4. Bond and angle RMSDs are marginally looser than the input's (0.011 vs 0.008 Å; 1.19 vs 0.88°) because
   the input's ideal geometry was an artefact of the perturbation being geometry-preserving. The final
   values are normal for a refined 0.9 Å structure.

## Notes on rules compliance

- No network access of any kind; no deposited coordinates were retrieved for this or any entry.
- Nothing was read from this repository's `ref/` or `data/` trees, from any `*_mask.json` or
  `*_validation.xml`, or from any file under `/tmp/nc_round1_cache` other than `9teu.mtz`.
  The deliverable directory was written to, never read.
- All 6 refinement invocations are accounted for above, including the one I aborted (step 4) and the one
  that crashed mid-run (step 5). `--dry-run` parameter validations exited before refinement began and
  are annotated as free in the transcript.
- `/tmp/nc_round1_cache/9teu.mtz` remained present throughout; no recovery from a refinement MTZ was
  needed.
