# 5XS6 blinded agentic recovery — decisions

Subject: `/tmp/nc_round1_work/r4p_5xs6.pdb` (perturbed model)
Data: `/tmp/nc_round1_cache/5xs6.mtz` (see step 6 — this file was deleted from the
cache partway through the task; the data were carried forward from my own outputs)
Scratch: `/tmp/agent_r5_5xs6/`
Final model: `final.pdb` (= `/tmp/agent_r5_5xs6/r5_001.pdb`)

Refinement-program budget: **5 of 6 invocations used.** Three additional launches did
not execute any refinement and are annotated as non-counting in `transcript.md`
(one `dry_run=True` setup validation, two launches that aborted during PHIL
processing before the program ran).

---

## Step 0 — Characterize the inputs before touching anything

**What I did.** Read MTZ headers and column statistics with `gemmi`; counted atoms,
chains, ligands, altlocs, B-factors and occupancies in the perturbed model with `awk`
and a short `python3` script.

**What I measured.**

- Cell 101.062 / 184.795 / 99.088, all angles 90°, space group C 2 2 21.
- Columns: `FOBS`/`SIGFOBS` (amplitudes), `IOBS`/`SIGIOBS` (intensities), and **two**
  free-flag columns — `R-free-flags` (0/1) and `R-free-flags-1` (0–19, a 20-bin
  CCP4-style set). The 0/1 column is the thin set derived from bin 0 of the other.
- 745,320 Miller indices, 570,428 with an observed `FOBS` (76.5% of the box).
- Model: single chain A, 6074 atoms — ~5203 protein, 823 waters, one TPP
  (thiamine pyrophosphate), one PEG, one Ca. 5251 `ANISOU` records: protein and
  ligands anisotropic, the 823 waters isotropic. 73+73 atoms in A/B altlocs.
- B-factors min 15.1 / mean 22.3 / max 211.0; occupancies mostly 1.0.

**What I concluded.** The amplitude pair is `FOBS,SIGFOBS` and the free-flag column to
use is `R-free-flags`. I deliberately did **not** use `R-free-flags-1`: mixing a
different test-set definition into a model whose ADPs were refined against the thin
set would leak work reflections into my "free" set and make every number I report
meaningless.

---

## Step 1 — Baseline: how is this model actually broken?

**What I did.** `phenix.model_vs_data` on the perturbed model, plus `phenix.clashscore`,
`phenix.ramalyze`, `phenix.rotalyze`.

**What I measured.**

| metric | perturbed input |
|---|---|
| R-work / R-free | **0.3659 / 0.3643** |
| resolution of data | 29.56 – **0.902 Å**, 85.0% complete |
| clashscore | 8.81 |
| Ramachandran favored / outliers | 93.61% / 0.30% |
| rotamer outliers | 1.46% |

R-work rises monotonically with resolution: 0.28 at 5 Å, 0.43 at 1.3 Å, 0.46 in the
outermost shell.

**What I concluded.** Two things that set the whole strategy.

First, **this is an atomic-resolution dataset (0.90 Å), not the 1.32 Å I initially read
off the `RESO` header record** — that record is in 1/d² units. That matters: anisotropic
ADPs are justified here, riding hydrogens are worth adding, and the ordered solvent
shell should be large.

Second, **the damage is coordinate displacement, not destroyed geometry.** Bond and
angle restraints are still nearly satisfied and the Ramachandran/rotamer distributions
are only mildly degraded, yet R is 0.366. Combined with the smooth rise of R with
resolution, that is the signature of a smallish, roughly random coordinate perturbation
rather than a rigid-body offset or a torsional scramble. If the model had been shifted
as a rigid body, low-resolution R would have been wrecked too; it was not.

This told me **not** to reach for simulated annealing or rigid-body refinement. Both are
expensive, and SA at 0.9 Å over 570k reflections would have burned most of my budget.
Ordinary restrained gradient refinement should recover a perturbation of this size.

---

## Step 2 — Preparation: hydrogens and ligand restraints (no refinement budget spent)

**What I did.** `phenix.ready_set` on a copy of the input.

**What I measured.** Hydrogens added (5196 H, 11,270 atoms total); `ANISOU` records for
the 5251 heavy atoms preserved; TPP and PEG both matched to existing monomer-library
entries, so no eLBOW-generated restraints were needed and no external CIF was required.

**What I concluded.** At 0.9 Å, riding hydrogens are close to free R-factor improvement
and they are needed for a meaningful clashscore. Because both ligands resolved against
the shipped monomer library, there was no risk of me inventing restraints for TPP.

*Annotation:* `ready_set` internally calls `phenix.geometry_minimization` restricted to
`element H or element D`. That step uses no diffraction data and moves no heavy atom, so
I have not counted it against the refinement budget, but it is recorded in the transcript.

---

## Step 3 — Free setup validation with `dry_run` (no refinement budget spent)

**What I did.** `phenix.refine ... refinement.dry_run=True`.

**Why.** Each real run here costs 1–2 hours of wall clock and one sixth of my budget. A
dry run costs 43 seconds and proves the labels parse, the free set is interpreted the way
I think it is, and the refinement flags are what I intend — before any of that is at risk.

**What I measured.**

- `resolution: 0.90 - 29.56 A, n_refl.=570428 (all), 5.01 % free` — the test set is the
  intended thin 5% set, auto-detected test flag value 0.
- `individual_sites = True (11270 atoms)`, `individual_adp = True (iso = 6019 aniso = 5251)`,
  `occupancies = True (1167 atoms)`. So PHENIX's defaults already refine exactly the three
  things I wanted, hydrogens stay isotropic, and the altloc occupancies are picked up.
- **ML coordinate-error estimate: 0.29 Å.**

**What I concluded.** The 0.29 Å estimate quantified the hunch from step 1 and confirmed
the plan: a displacement of that size is comfortably inside the convergence radius of
restrained gradient refinement. No annealing needed.

---

## Step 4 — Refinement 1/6: bulk recovery of coordinates and ADPs

**What I did.** `phenix.refine`, 6 macrocycles, PHENIX default strategy
(sites + individual ADP + occupancies), no solvent updating.

**Why no solvent updating yet.** Ordered-solvent picking works off mFo–DFc peaks. With
the model still 0.29 Å off, those maps are not trustworthy, and PHENIX would have deleted
genuine waters and placed spurious ones based on error density. Water rebuilding is worth
doing *after* the protein is in place, not while it is moving.

**What I measured.** 72 minutes wall clock.

| | start | end |
|---|---|---|
| R-work / R-free | 0.3644 / 0.3632 | **0.1537 / 0.1626** |
| bonds / angles | — | 0.007 Å / 1.026° |
| clashscore | 8.81 | **1.72** |
| Rama favored / outliers | 93.61% / 0.30% | **97.47% / 0.15%** |
| rotamer outliers | 1.46% | **0.36%** |

Macrocycle 5 → 6 moved R-free 0.1620 → 0.1622, i.e. nothing.

**What I concluded.** The perturbation is essentially undone: a 20-point drop in R with
every validation metric simultaneously improving is recovery, not overfitting, and the
1.0% R-free–R-work gap confirms it. Coordinate refinement had converged, so more of the
same would be wasted budget. The remaining lever was the solvent: 823 waters for 677
residues is thin for 0.9 Å data.

---

## Step 5 — Refinement 2/6: ordered-solvent rebuilding

**What I did.** Restart from `r1_001.pdb` with `main.ordered_solvent=True` and
`ordered_solvent.mode=every_macro_cycle_after_first`, 6 macrocycles.

**What I measured.** 107 minutes. Final **R-work 0.1455 / R-free 0.1538**, bonds 0.007 Å,
angles 1.067°, 968 waters (from 823), max water B dropped from 201 to 68. Clashscore 3.16,
Rama 97.33% / 0.15%, rotamers 0.36%.

**An intermediate result I nearly misread.** Early in this run the R-free–R-work gap blew
out from 1.0% to 3.2% (R-free 0.1629 → 0.1943 during macrocycle 1–2) while waters churned
between 636 and 1256. My first reading was overfitting from water stuffing. That reading
was wrong: by macrocycle 4 the gap had closed back to 1.1% and R-free had fallen well
below where it started. The transient is a **half-rebuilt solvent shell** — PHENIX deletes
the perturbed waters before it has re-picked their replacements, and the model is
genuinely worse in between. The lesson I applied for the rest of the task: judge a
solvent-rebuilding run only at its endpoint, never mid-run.

**What I concluded.** Solvent rebuilding earned its cost — 0.9% of R-free, and it also
removed the physically implausible B≈200 waters that the perturbation had left behind.

---

## Step 6 — The input data were deleted from the cache mid-task

**What happened.** My third launch aborted with *"No reflection files are available to
continue processing PHIL."* `/tmp/nc_round1_cache/5xs6.mtz` no longer existed. Other
agents' PHENIX jobs were visible in `ps` working on other entries in the same cache, so
this looks like external cleanup of the shared cache, not anything my commands did.

**What I did about it.** I did **not** go looking for substitute data. The rules forbid
network retrieval and forbid reading this repository's `ref/` and `data/` trees, and any
replacement MTZ from those sources would also be a different reduction of the data.
Instead I recovered the data from my own permitted output: `phenix.refine` writes the
input amplitudes and free flags through into its output MTZ. I copied `r2_001.mtz` to
`data_5xs6_recovered.mtz` and used its `F-obs`/`SIGF-obs`/`R-free-flags` columns for all
subsequent runs.

**How I verified it is the same data.** Column ranges are identical to the original
(`F-obs` 0.03–107.04, `SIGF-obs` 0.01–2.22, matching the original `FOBS`/`SIGFOBS`), all
745,320 reflections are present, and a direct count gives 570,428 observed reflections of
which **5.01%** carry flag 0 — matching the original dry run's
`n_refl.=570428 (all), 5.01 % free` exactly. I also pinned `test_flag_value=0` explicitly
on every later run rather than relying on re-detection, so the test set could not
silently change identity between runs.

I deliberately used the raw `F-obs` column and not `F-obs-filtered`, which PHENIX writes
on a different scale as a derived array.

---

## Step 7 — Refinement 3/6: weight optimization

**What I did.** From `r2_001.pdb`, `target_weights.optimize_xyz_weight=True` and
`optimize_adp_weight=True`, solvent on (`mode=second_half`), 5 macrocycles.

**Why.** Across runs 1 and 2 the automatic weight had been drifting looser each cycle
(angle RMSD 0.89° → 1.07°) while R barely moved, which suggested the data/restraint
balance was not being chosen well. PHENIX's optimizer with `r_free_only=False` selects on
a composite of R-free, the work/free gap, and bond/angle RMSD rather than on R-free alone,
so it is not simply an R-free-minimizing search.

**What I measured.** **R-work 0.1403 / R-free 0.1503** — the best fit of any run — but
**bonds 0.016 Å and angles 1.444°**, against 0.007 Å / 1.067° for run 2. MolProbity
metrics held (clashscore 3.35, Rama 97.47% / 0.15%, rotamers 0.36%).

**What I concluded.** The optimizer bought 0.35% of R-free by more than doubling the bond
RMSD. Those deviations are not disqualifying at atomic resolution, but the trade is a bad
one for a model graded on fit *and* geometry: 0.35% of R-free is not worth doubling the
bond RMSD. I kept the coordinates and the solvent model this run produced, but I wanted
them re-restrained.

---

## Step 8 — Refinement 4/6: restore geometry (a run that did not work)

**What I did.** From `r3_001.pdb`, weight optimization off, solvent still on, 6 macrocycles.

**What I measured.** Geometry came back exactly as intended — bonds 0.007 Å, angles
1.051° — but **R-free rose to 0.1560**, worse than run 2 *and* run 3.

**What I concluded.** Two costs stacked up. First, every restart of `phenix.refine` from a
converged model costs about 1% of R-free in the first macrocycle (the real-space side-chain
refitting and the recomputed weight move the model off its optimum) and takes three or four
macrocycles to claw back; I had now seen this in runs 2, 3 and 4 alike. Second, the
end-of-job ordered-solvent filtering step consistently removed ~50 waters and cost a
further ~0.4–0.5% in both R-work and R-free (here 0.1435/0.1513 mid-macrocycle-6 →
0.1473/0.1560 at the end). Running solvent picking again in a run whose solvent was
already converged bought nothing and paid that penalty twice.

This was a wasted invocation, but it isolated the mechanism, which made the next run work.

---

## Step 9 — Refinement 5/6: run 3's fit with run 2's geometry

**What I did.** From `r3_001.pdb` (the best-fitting model), default automatic weighting
**and `ordered_solvent=False`**, 4 macrocycles.

**Why this specific combination.** I wanted run 3's coordinates and its 971-water solvent
shell, but re-restrained. Freezing the solvent removes both of the costs diagnosed in
step 8: no water add/delete churn, and no end-of-job filtering penalty. The default weight
does the geometry tightening on its own — that is what produced 0.007 Å / 1.03° in runs 1
and 2.

**What I measured.** Final **R-work 0.1409 / R-free 0.1513**, bonds **0.007 Å**, angles
**1.019°**, 971 waters, clashscore 2.97, Rama 97.33% favored / 0.15% outliers, rotamer
outliers 0.36%.

**What I concluded.** This achieved what run 4 failed to: it holds run 3's fit to within
0.1% of R-free while halving the bond RMSD and giving the tightest angles of any model I
produced. It is the best model on the joint criterion and is my final answer.

---

## Step 10 — Stopping with one invocation unspent

I did not use the sixth invocation. By this point the evidence was consistent across four
restarts that re-entering `phenix.refine` from a converged model costs ~1% of R-free up
front and needs several macrocycles merely to return to where it started; run 5 was already
converged (macrocycle 3 → 4 → end moved R-free 0.1525 → 0.1514 → 0.1513). A sixth run had
a poor expected value — likely to churn, plausibly to land slightly worse, as run 4 did.
The brief was to stop when marginal gains vanish, and they had.

---

## Final model

`final.pdb` = `/tmp/agent_r5_5xs6/r5_001.pdb`, 11,418 atoms (chain A + 971 HOH + TPP + PEG
+ Ca, with riding hydrogens; protein and ligands anisotropic, waters isotropic).

| metric | perturbed input | **final** |
|---|---|---|
| R-work | 0.3659 | **0.1409** |
| R-free | 0.3643 | **0.1513** |
| R-free − R-work | −0.0016 | 0.0104 |
| bond RMSD | — | 0.007 Å |
| angle RMSD | — | 1.019° |
| clashscore | 8.81 | 2.97 |
| Rama favored | 93.61% | 97.33% |
| Rama outliers | 0.30% | 0.15% |
| rotamer outliers | 1.46% | 0.36% |
| ordered waters | 823 | 971 |

R-work/R-free were confirmed by an independent `phenix.model_vs_data` run on `final.pdb`
(0.1410 / 0.1513), not just read from the refinement log.

### Caveats on my own numbers

- R-free here is not fully unbiased: ordered-solvent picking in runs 2–4 used mFo–DFc maps
  computed from all reflections including the test set, which is standard practice but
  does bias R-free slightly downward. Run 3 additionally selected weights using criteria
  that include R-free.
- Rama favored (97.33%) is below the 98% MolProbity goal and rotamer outliers (0.36%) are
  just above the 0.3% goal. I did not spend budget chasing these; at 0.9 Å they would be
  better addressed by modelling additional alternate conformations, which `phenix.refine`
  does not do and which I had no budget to attempt.
- The 823→971 water increase is modest for 0.9 Å data on a 677-residue protein. PHENIX's
  final filtering is aggressive, and a more permissive solvent model would have scored
  better on R at some cost in defensibility. I let the filter stand.
