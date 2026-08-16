# 8QXQ blinded recovery — decisions log

Agent working directory: `/tmp/agent_r5_8qxq/`
Inputs: `/tmp/nc_round1_work/r4p_8qxq.pdb` (perturbed model), `/tmp/nc_round1_cache/8qxq.mtz` (data).
Final deliverable: `final.pdb` (byte-identical to `/tmp/agent_r5_8qxq/r3_001.pdb`, md5 `7ad665f6bd93f7f12e31b1b80b19c26b`).

**Refinement budget: 6 of 6 used.** No network access, no deposited coordinates, no `ref/`, `data/`,
mask, or validation files were read. The MTZ never disappeared, so no recovery-from-output was needed
(a byte-identical copy was made to `/tmp/agent_r5_8qxq/data.mtz` at the start as insurance; md5 verified
against the original).

---

## Step 0 — Characterize the data and the damage (no refinement spent)

**What.** Read MTZ metadata with `gemmi mtz --dump` / `-s`, then measured the starting model with
`phenix.model_vs_data`, `phenix.ramalyze`, `phenix.rotalyze`, `phenix.clashscore`, plus two small
Python passes over the PDB (ADP/occupancy distribution; ANISOU-vs-B consistency; water H-bond distances).

**Measured.**

| Property | Value |
| --- | --- |
| Space group / cell | P2₁2₁2₁, 49.34 × 78.52 × 83.93 Å |
| Resolution | 24.99 – 0.94 Å, 211 278 reflections, 99.9 % complete |
| Columns used | `FOBS,SIGFOBS`; free flags `R-free-flags` (test value 0, 3179 free reflections, 1.5 %) |
| Contents | 1 chain (~318 residues), ligands SAH + X8Q (two altlocs), 2 Cl, 451 waters, 2789 riding H, full ANISOU |
| Starting R-work / R-free | **0.3901 / 0.4020** |
| Starting clashscore | 5.56 |
| Starting Ramachandran | 91.19 % favored, 1.89 % outliers |
| Starting rotamer outliers | 0.33 % |

**Concluded.** The perturbation is a *coordinate* shake, not an ADP or occupancy scramble:

- ANISOU traces agree with the B-factor column to within 0.005 Å² for all 3262 atoms, so the ADPs are
  internally consistent and were not randomized.
- B-factors (mean 17.2 Å²) and occupancies are physically sensible.
- Local geometry survived (clashscore 5.6, rotamer outliers 0.33 %) while Ramachandran degraded
  (91 % favored) — the signature of a shake followed by geometry regularization, not of a scramble.
- Waters still peak at 2.5–3.0 Å from protein polar atoms, so the solvent shell was displaced but not
  randomized.
- R rises steeply with resolution (0.26 at 8 Å → 0.43–0.47 at 1.1–1.4 Å), which is how a small random
  displacement behaves — it attenuates high-resolution amplitudes like an extra B-factor.

PHENIX's own maximum-likelihood coordinate-error estimate on the starting model was **0.26 Å**, which
confirmed the diagnosis quantitatively. That is comfortably inside the convergence radius of ordinary
gradient refinement at 0.94 Å, so I decided **not** to spend budget on simulated annealing and to rely
on straightforward reciprocal-space refinement instead.

I also confirmed both ligands (SAH, X8Q) have restraints in the PHENIX `geostd` library, so no custom
CIF generation was needed and no run would be lost to a missing-restraint failure.

**Free checks before paid ones.** Every refinement command below was first validated with
`phenix.refine --dry-run`, which exits after argument validation without refining. Those dry runs cost
nothing and do not count against the 6-run budget.

---

## Run 1 — Bulk recovery (xyz + anisotropic ADP + occupancies)

**What.** `phenix.refine` from the perturbed model: 6 macrocycles, strategy
`individual_sites+individual_adp+occupancies`, anisotropic ADPs for all non-hydrogen atoms, ordered
solvent **off**, `nproc=10`.

**Why.** Fix coordinates first. Anisotropic ADPs are appropriate at 0.94 Å (≈29 k parameters against
208 k work reflections, a 7:1 ratio). I deliberately froze the solvent: rebuilding water while the
protein is still 0.26 Å off would fit water to displaced density.

**Measured.** R-work 0.3901 → **0.1477**, R-free 0.4023 → **0.1561**. Clashscore 5.56 → **1.79**.
Ramachandran 91.19 % → **98.43 % favored, 0.00 % outliers**. Bond RMSD 0.006 Å, angle 0.99°.

**Concluded.** The recovery essentially succeeded in one run, and the geometry came back to
publication quality. The R-free − R-work gap was only 0.0084 — remarkably tight — which says the model
is *over-restrained*, not overfit, and that there is headroom to add parameters or relax weights.
Solvent was untouched (451 waters throughout), making it the obvious next lever.

---

## Run 2 — Ordered-solvent rebuild

**What.** Same strategy, continued from run 1, with `ordered_solvent=True`, 6 macrocycles.

**Why.** At 0.94 Å the difference maps resolve far more water than 451 sites, and the guidance flagged
solvent as a likely damage target. With coordinates now correct, water picking is trustworthy.

**Measured.** R-work **0.1431**, R-free **0.1509**; waters 451 → **681**. Clashscore 3.05 (up from 1.79),
Ramachandran 98.43 % favored / 0 % outliers, bond RMSD 0.007 Å, angle 1.07°.

**Concluded.** The rebuild earned 0.005 in R-free. Worth noting for anyone reading the logs: the *first*
solvent-picking cycle pushed R-free **up** to 0.1650 before later macrocycles pulled it down to 0.1505.
I nearly called this overfitting prematurely; the transient is just the water set being added before
xyz/ADP refinement has caught up with it. Clashscore rose because the new waters introduce contacts,
but R-free — an unbiased statistic — endorsed them.

---

## Run 3 — Weight optimization

**What.** Continued from run 2 with `optimize_xyz_weight=True optimize_adp_weight=True`, ordered solvent
on, 5 macrocycles.

**Why.** The 0.008 R-free/R-work gap after run 2 said the restraints were dominating the data. At atomic
resolution the data should win. Optimizing weights *inside* one run spends wall-clock time instead of
refinement budget, which is the right trade when the budget is the scarce resource.

**Measured.** R-work **0.1325**, R-free **0.1490** (independently re-measured with `phenix.model_vs_data`,
which agreed: 0.1325 / 0.1490). Waters 748. Clashscore 3.05, Ramachandran 98.11 % favored / 0 % outliers,
rotamer outliers 0.33 %, RMS(bonds) 0.0097 Å, RMS(angles) 1.19°, MolProbity score 1.10.

**Caveat I want on the record.** PHENIX's weight optimizer selects weights by consulting R-free. That is
standard crystallographic practice, but it is a mild dependency on the test set, and it means run 3's
R-free is very slightly optimistic relative to a weight chosen blind.

**Concluded.** Best model so far, and the gap widened to a healthy 0.0165 — normal for atomic resolution.
The process was killed by the machine during result export (the MTZ came out 0 bytes), but the PDB and
CIF were written completely; I verified the file ends with `END`, carries all 6348 atoms and 3449 ANISOU
records, and re-measured it from disk rather than trusting the log.

---

## Run 4 — Continuation (killed by the system; no model produced)

**What.** Same recipe as run 3, continued from `r3_001.pdb`, 5 macrocycles, `nproc=8`.

**Measured.** Reached R-work 0.1282 / R-free 0.1489 before the process was killed mid-macrocycle during
an ordered-solvent update. No output coordinates were written — no traceback, no PHENIX error, just
termination. The box was running several concurrent PHENIX jobs at load ≈ 10 on 10 cores.

**Concluded.** **This run counts against the budget** — refinement genuinely started and ran for several
macrocycles; only the output was lost. I am counting it as invocation 4 of 6 rather than claiming it as
a pre-refinement failure. Its one useful signal: R-free had flattened at ≈0.1489, matching run 3, so
further refinement of this kind was already into diminishing returns. I reduced `nproc` to 4 and
shortened subsequent runs to lower the kill risk, and banked run 3's model to the deliverable directory
immediately so that a later crash could not leave me empty-handed.

---

## Run 5 — Shorter, safer consolidation

**What.** From `r3_001.pdb`, weight optimization on, ordered solvent on, 3 macrocycles, `nproc=4`.

**Measured.** R-work **0.1304**, R-free **0.1492**. Clashscore 3.77, RMS(bonds) 0.0123 Å,
RMS(angles) 1.34°, MolProbity score 1.17, rotamer outliers 0.33 %.

**Concluded.** **Rejected.** R-free is statistically identical to run 3 (0.1492 vs 0.1490; with 3179 free
reflections σ(R-free) ≈ 0.002, so this difference is noise), while every geometry metric got worse.
Continued weight loosening had stopped buying fit and started buying only R-work at geometry's expense —
the classic point of diminishing returns. Run 5 is dominated by run 3 on every axis.

I also noticed a consistent pattern across runs 3 and 5: PHENIX's final water-filtering step removes
~100 waters and costs ~0.0013 in R-free. I chose **not** to defeat that filter. R-free mildly prefers
the extra waters, but retaining sites that PHENIX's own occupancy/B criteria reject, purely to lower R,
is water-stuffing, and 0.0013 is within noise anyway.

---

## Run 6 — Final experiment: tighter (default) weights

**What.** From `r3_001.pdb`, ordered solvent on, 4 macrocycles, **no** weight optimization (default
restraint weights), `nproc=4`.

**Why.** Runs 3 and 5 had traded restraint tightness for fit. With one run left, the open question was
whether the reverse trade — default weights — would buy meaningfully better geometry at negligible cost
in R-free, since R-free was flat across that weight range. Clear fallback: keep run 3 if not.

**Measured.** Completed cleanly. R-work **0.1342**, R-free **0.1514**. Clashscore **2.69**,
RMS(bonds) **0.0076 Å**, RMS(angles) **1.12°**, MolProbity score **1.06**, but rotamer outliers rose to
**0.98 %** (from 0.33 %).

**Concluded.** **Rejected**, and the deciding factor was not the R-free cost alone. Tighter restraints
did clean up the restraint statistics, but they tripled the rotamer outlier rate — meaning side chains
were pulled toward library ideals and *away* from what the 0.94 Å density actually shows. At atomic
resolution that is the wrong direction: the data are more informative than the geometry library. The
0.0024 R-free penalty points the same way.

---

## Final selection

Compared with MolProbity as an independent oracle (never PHENIX grading its own refinement):

| Model | R-work | R-free | Clashscore | RMS(bonds) Å | RMS(angles)° | Rama outliers | Rota outliers | MolProbity |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| perturbed input | 0.3901 | 0.4020 | 5.56 | — | — | 1.89 % | 0.33 % | — |
| run 1 | 0.1477 | 0.1562 | 1.79 | 0.006 | 0.99 | 0.00 % | 0.33 % | — |
| run 2 | 0.1431 | 0.1509 | 3.05 | 0.007 | 1.07 | 0.00 % | 0.33 % | — |
| **run 3 → final.pdb** | **0.1325** | **0.1490** | **3.05** | **0.0097** | **1.19** | **0.00 %** | **0.33 %** | **1.10** |
| run 5 | 0.1304 | 0.1492 | 3.77 | 0.0123 | 1.34 | 0.00 % | 0.33 % | 1.17 |
| run 6 | 0.1342 | 0.1514 | 2.69 | 0.0076 | 1.12 | 0.00 % | 0.98 % | 1.06 |

**`final.pdb` = run 3's model.** It has the best R-free of any model produced, ties the best rotamer
agreement, has zero Ramachandran outliers, and its bond/angle deviations (0.0097 Å, 1.19°) sit squarely
in the normal range for a 0.94 Å structure — at atomic resolution, deviations from library ideals are
expected because the data genuinely determine the geometry. Runs 5 and 6 probed the weight axis in both
directions and neither beat it, which is the evidence that run 3 sits at the optimum rather than merely
being the last thing I tried.

Model contents: 6348 atoms, 3449 anisotropic ADPs, 748 waters, SAH + X8Q (both with alternate
conformations) + 2 Cl, riding hydrogens retained throughout.

**Stopping rationale.** R-free trajectory 0.4020 → 0.1562 → 0.1509 → 0.1490 → (0.1489) → 0.1492 → 0.1514.
It plateaued at ≈0.149 after run 3 and moved only within noise thereafter, while the water count
oscillated (748 ↔ 941) between runs — solvent picking had reached its noise floor. Marginal gains had
vanished and the budget was spent.

**Self-measured numbers are advisory.** All values above come from my own PHENIX/MolProbity runs against
the supplied MTZ; the benchmark re-measures independently from `final.pdb`.
