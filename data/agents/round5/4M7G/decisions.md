# Decisions — blinded agentic recovery of 4M7G (round 5)

Perturbed model `/tmp/nc_round1_work/r4p_4m7g.pdb`, data `/tmp/nc_round1_cache/4m7g.mtz`
(FOBS,SIGFOBS; free flags `R-free-flags`). Scratch: `/tmp/agent_r5_4m7g/`.
Final model: `final.pdb` (= `r5_001.pdb`, refinement run 5 of 6).

No deposited coordinates were retrieved, no network access was used, and nothing under
`ref/`, `data/`, or `/tmp/nc_round1_cache/` other than `4m7g.mtz` was read.

## Headline

| | perturbed input | final.pdb |
|---|---|---|
| R-work | 0.3939 | **0.1208** |
| R-free | 0.3984 | **0.1298** |
| RMS(bonds) Å | 0.0104 | 0.0063 |
| RMS(angles) ° | 1.25 | 0.96 |
| Clashscore | 3.74 | 1.88 |
| Ramachandran outliers | 0.46 % | 0.00 % |
| Ramachandran favoured | 90.37 % | 98.17 % |
| Rama-Z (whole) | −4.26 (poor) | −0.15 (good) |
| Rotamer outliers | 1.95 % | 0.49 % |
| MolProbity score | 1.92 | 0.95 |
| Ordered waters | 353 | 399 |
| max mFo−DFc peak | 14.78 σ | 9.37 σ |

Final model differs from the perturbed input by **0.383 Å RMSD** over all 1891 protein
heavy atoms (mean 0.297, median 0.250, max 2.94; 9.7 % of atoms moved >0.5 Å).

## Step 0 — Characterise inputs before touching anything

**Did:** read the MTZ header with `gemmi mtz --headers`, counted atoms/elements/altlocs/
occupancies/ANISOU in the model, ran `phenix.model_vs_data`, `phenix.clashscore`,
`phenix.ramalyze`, `phenix.rotalyze`, `phenix.molprobity`.

**Measured:**
- P2₁2₁2₁, 46.958 × 61.249 × 74.149 Å, one chain of 223 residues (1–223, no gaps),
  353 waters, no ligands, 36 residues with alternate conformations, 3 disulfides.
- **The data go to 0.808 Å**, not 1.6 Å. The MTZ `RESO` record is in 1/d² units
  (1/√1.606 = 0.79 Å); 217 476 reflections, 99.7 % complete, 5.01 % free set.
- The model already carries riding hydrogens (1828 H) and **anisotropic ADPs on all
  2244 heavy atoms**; the ANISOU trace/B agreement was exact for all 2244, so ADPs were
  internally consistent and not scrambled.
- Baseline R-work/R-free 0.3939/0.3984.
- Baseline geometry: bonds 0.0104 Å, angles 1.25° — **essentially undamaged locally**.

**Concluded:** this is an ultra-high-resolution case, which changes the whole plan
(anisotropic ADPs are justified rather than reckless; a very low R is achievable). The
damage is *not* bond-level noise — local geometry is near-normal while Rama-Z is −4.26.
That is the signature of coordinated displacements, not white noise on Cartesian
coordinates.

**Sizing the perturbation without a reference:** R rises monotonically with resolution
(0.229 at 5.4–4.3 Å → 0.481 at 1.0–0.81 Å). For random coordinate error the structure
factor correlation falls as exp(−2π²σ²/d²); R ≈ 0.48 at d ≈ 0.9 Å is near the random
value, and R ≈ 0.23 at 4 Å, which brackets **σ ≈ 0.25–0.30 Å**. That is comfortably
inside the convergence radius of gradient refinement, so I rejected the classic
staged low-resolution-first strategy and the use of simulated annealing — both cost
budget to solve a problem I did not have. (The final 0.383 Å RMSD confirms the estimate.)

## Step 1 — [REFINE 1/6] Straight reciprocal-space refinement at full resolution

**Did:** `phenix.refine`, default strategy (which already includes
`individual_sites`, `individual_sites_real_space`, `individual_adp`, `occupancies`),
5 macrocycles, full resolution, no solvent update.

**Why:** with σ ≈ 0.3 Å the cheapest thing that can work is ordinary restrained
refinement. Real-space site refinement is on by default and handles the damaged side
chains; NQH flips are on by default too.

**Measured:** R-work/R-free 0.3939/0.3984 → **0.1255/0.1368**. Geometry recovered to
bonds 0.006, angles 0.92, clashscore 1.34, Rama 98.17 % favoured / 0 % outliers,
MolProbity 0.86.

**Concluded:** the bulk of the perturbation was recoverable in one pass. Remaining work
is solvent and fine polish, not backbone rescue.

## Step 2 — Locate what is still unmodelled

**Did:** `phenix.find_peaks_holes` on the run-1 map.

**Measured:** 93 peaks > 3.5 σ, 14 > 6.5 σ, 5 > 9.5 σ, max 14.78 σ; only 7 holes < −3.5 σ.
The strong peaks sit 1.8–2.9 Å from waters, backbone O, Lys NZ, Gln OE1 and Glu OE1.

**Concluded:** these are **missing waters**, not ions — ion sites would show shorter
(2.0–2.4 Å) contacts with multiple carboxylate/carbonyl coordination, and I have no
independent evidence for any particular ion. Placing waters is the defensible call;
guessing at ion identities is not. 353 waters for 223 residues (1.58/residue) is low for
0.81 Å data, which independently supports the same conclusion.

## Step 3 — [REFINE 2/6] Ordered-solvent rebuild

**Did:** `ordered_solvent=True`, 6 macrocycles, from the run-1 model.

**Measured:** R-work/R-free **0.1214/0.1304**; waters 353 → 397 (47 of the original
waters were rejected on map CC/B/occupancy criteria and 91 new ones added). Max residual
peak 14.78 σ → 8.52 σ, peaks > 9.5 σ went 5 → 0. Rama-Z improved to −0.23,
clashscore 1.07, MolProbity 0.81.

**Also observed a problem worth chasing:** macrocycles 1–2 *degraded* the model
(R-free 0.1371 → 0.1465 → 0.1545) before macrocycles 3–6 recovered it. The reported
X-ray/geometry weight was ≈ 9.5 in cycles 1–2 and ≈ 0.9 in cycles 3–6.

## Step 4 — [REFINE 3/6] Anisotropic solvent + weight optimisation — **CRASHED**

**Did:** tried to combine, in one run, `new_solvent=anisotropic`,
`anisotropic="not element H"`, `optimize_xyz_weight=True`, `optimize_adp_weight=True`.

**What happened:** crashed at the macrocycle-3 solvent update with
`CCTBX_ASSERT(f.use_u_iso()) failure` in `mmtbx/refinement/data.py`. The ordered-solvent
water-ADP refinement path assumes isotropic waters, so it is **incompatible with
anisotropic solvent**. No model was written; the invocation was spent for nothing.

**Also learned before the crash:** `optimize_xyz_weight` did not scan xyz weights in
macrocycle 1 (single trial at 9.539); only the ADP weight was scanned, and it selected
9.648 — the *best* of its trials but still leaving R-free at 0.1397, worse than the
0.1304 it started from, because macrocycle 1 had already damaged the model.

**Concluded:** my own error — I bundled four changes into one run and lost an invocation
to an interaction I could have avoided. Do not combine anisotropic ADPs with
ordered-solvent updating.

## Step 5 — [REFINE 4/6] Pinning the weight — **failed experiment, killed**

**Did:** read `mmtbx/refinement/weights.py` and confirmed `fix_wxc` overrides `wxc` and
forces `wxc_scale = 1.0`. Set `fix_wxc=0.9`, `fix_wxu=4.5` to reproduce the effective
weights of the well-behaved late macrocycles.

**Measured:** immediately worse and not recovering — R-work/R-free 0.1416/0.1507 in
macrocycle 1, bonds over-restrained to 0.003 Å, still 0.1386/0.1509 by macrocycle 3.
Killed it rather than burn another 20 minutes.

**Why it failed:** reading further into `weights.py`, `wxc = gc_norm / gxc_norm` — it is
a **per-macrocycle normalisation of gradient norms**, not an absolute scale. The user
knob is `wxc_scale`. Pinning `wxc` therefore destroys the normalisation, and the
apparent "weight" values in different macrocycles are not comparable quantities at all.
My whole reading of the step-3 observation was wrong.

## Step 6 — The actual diagnosis

**Did:** grepped `Set refinement target` out of the run logs.

**Measured:** in both run 1 and run 2, macrocycles 1–2 use `ls_wunit_k1` and macrocycles
3+ use `ml`. PHENIX's `target=auto` starts with least-squares and switches to maximum
likelihood at macrocycle 3.

**Concluded:** the early degradation was never a weighting problem. At 0.81 Å nearly half
the reflections (101 224 of 217 476) lie in the weakest shell; a unit-weighted
least-squares target is dominated by them and actively damages an already-good model.
The weight excursion was a *symptom* — gradient norms differ between the two targets —
not the cause. Fix: force `target=ml` from macrocycle 1.

## Step 7 — [REFINE 5/6] ML target throughout — **the final model**

**Did:** `target=ml`, `ordered_solvent=True`, 6 macrocycles, from the run-2 model.

**Measured:** macrocycle 1 now *holds* at 0.1213/0.1303 instead of collapsing to
0.1303/0.1465 — the predicted behaviour, which confirms the diagnosis. Converged to
**R-work 0.1208 / R-free 0.1298**; 399 waters; max residual peak 9.37 σ, none > 9.5 σ,
only 1 suspicious water.

## Step 8 — [REFINE 6/6] Anisotropic ADPs on the remaining waters

**Did:** `anisotropic="not element H"` (to promote the 96 still-isotropic new waters),
`target=ml`, `ordered_solvent=False` (to avoid the step-4 crash), 5 macrocycles.

**Measured:** R-work/R-free **0.1210/0.1311** — flat on R-work and 0.0013 *worse* on
R-free than run 5.

**Concluded:** rejected. The extra ~480 ADP parameters bought nothing; R-free is the
guard and it moved the wrong way. Even at 0.81 Å, anisotropic ADPs on newly placed
partial-occupancy waters are not free.

## Final selection

Budget exhausted (6/6). All three surviving candidates were re-measured independently
with `phenix.model_vs_data` rather than trusting the refinement logs:

| model | R-work | R-free | clashscore | MolProbity |
|---|---|---|---|---|
| r2_001 (run 2) | 0.1214 | 0.1304 | 1.07 | 0.81 |
| **r5_001 (run 5)** | **0.1208** | **0.1302** | 1.88 | 0.95 |
| r6_001 (run 6) | 0.1210 | 0.1312 | 1.88 | 0.95 |

Chose **r5_001** on R-free, which is the criterion that actually guards against
overfitting. Run 2 is marginally better on clashscore (1.07 vs 1.88) and MolProbity
(0.81 vs 0.95), but the differences in both directions are small; R-free is the more
meaningful discriminator and run 5 is the model with the best fit to data at
indistinguishable geometry quality. Both are far better than the input on every metric.

Independent cross-checks on `final.pdb`: `gemmi contents` gives Matthews 2.32,
47 % solvent, 223 residues, consistent with the cell and content;
`phenix.model_vs_data` reproduces R-work/R-free 0.1208/0.1302 from coordinates alone.

## What I would do with more budget

- The remaining ~9 σ difference peaks and the small negative holes near Leu92 CD1,
  Leu94 CD2, Val211 CG2 and Arg201 NH2 point to unmodelled **alternate side-chain
  conformations**, which reciprocal-space refinement cannot introduce on its own.
  At 0.81 Å these are real and would need explicit alt-conf building.
- A further ordered-solvent pass under the ML target (run 5's solvent building started
  from the pre-ML model), which is the one thing run 6 spent its budget not doing.

## Honest caveats

- The ML-target diagnosis was found only after losing two invocations (runs 3 and 4);
  a cleaner agent would have reached 0.1298 in about three.
- Self-measured numbers here come from PHENIX tools throughout. The only genuinely
  independent check I ran is `gemmi` on model content, not on R factors.
