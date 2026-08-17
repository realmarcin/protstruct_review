# Decisions — 3ZOJ blinded recovery (round 5)

Blinded agentic repair of a perturbed model against its own diffraction data.
No deposited coordinates, no network, no reference files were consulted.

- **Perturbed input:** `/tmp/nc_round1_work/r4p_3zoj.pdb`
- **Data:** `/tmp/nc_round1_cache/3zoj.mtz` — `FOBS,SIGFOBS`, free set `R-free-flags`
- **Final model:** `final.pdb` (= `/tmp/agent_r5_3zoj/r6_006.pdb`)
- **Refinement budget:** 6 of 6 invocations used

---

## Step 0 — Characterize the data and the damage before touching anything

**What.** Read the MTZ header with `gemmi mtz --dump`, ran `phenix.model_vs_data`,
`phenix.molprobity`, `phenix.clashscore/ramalyze/rotalyze` on the perturbed model, and
scripted checks on B-factors, ANISOU consistency, altlocs, and occupancies.

**Why.** Spending refinement budget before knowing *what kind* of damage was inflicted
is how you burn runs on the wrong strategy. Diagnosis is free; refinement is not.

**Measured.**

| Quantity | Perturbed input |
|---|---|
| Resolution | 60.15 – 0.885 Å, I4, 251 823 reflections, 99.8 % complete |
| R-work / R-free | **0.3744 / 0.3772** |
| MolProbity score | 1.74 |
| Clashscore | 5.97 |
| Rama favored / outliers | 93.82 % / 0.00 % |
| Rotamer outliers | 0.49 % |
| RMS bonds / angles | 0.0109 Å / 1.17° |
| Waters | 212 |
| Composition | 2102 protein + 2176 H + 266 BOG/Cl/HOH, altlocs A/B/C present |

**Concluded.** Three diagnostic facts drove everything downstream:

1. **R-work ≈ R-free (0.3744 vs 0.3772).** A model that is *overfit* has a wide gap;
   a model whose coordinates have been *displaced* has almost none. This is displacement
   damage, not overfitting.
2. **Geometry was essentially intact** (bond RMSD 0.0109 Å, zero Rama outliers). So the
   perturbation was a coordinate shake followed by geometry regularization, not a
   shredded model. That matters: gradient refinement can recover this, and expensive
   rescue tactics (simulated annealing, torsion dynamics) were unlikely to be needed.
3. **R degraded monotonically with resolution** — 0.23 at 4 Å rising to 0.45 at 0.9 Å.
   Random coordinate error smears high-resolution terms preferentially. A rigid-body
   misplacement would have wrecked the low-resolution shells too, and it did not.

At 0.885 Å the radius of convergence of reciprocal-space refinement is large relative
to the implied displacement, so I chose **plain restrained refinement first** and held
simulated annealing in reserve. It was never needed.

**Also verified before refining:**
- **Free-flag convention.** Counted the flag column directly with `gemmi mtz2cif`:
  2381 reflections flagged free (0.95 %), 249 442 work. Small — σ(R-free) ≈ 0.002 — so
  I treated R-free differences under ~0.003 as noise throughout rather than chasing them.
- **ADPs were not independently scrambled.** Mean |B_eq − B_iso| across 4526 ANISOU
  records was 0.0025 Å², i.e. perfectly self-consistent. This ruled out ADP damage and
  confirmed coordinates as the sole target.

---

## Step 1 — Refinement 1/6: coordinates + ADPs, **no** new solvent

**What.** `phenix.refine`, 5 macrocycles, default strategy
(`individual_sites + individual_sites_real_space + individual_adp + occupancies`).
Ordered solvent deliberately left **off**.

**Why staged this way.** With protein atoms displaced, running the solvent picker in the
same breath would let it drop waters into difference density that actually belongs to
mis-placed protein atoms — poisoning the model with waters that then have to be removed.
Get the protein back into its density first, *then* build solvent against a correct model.

**Measured.** R-work/R-free **0.3745/0.3775 → 0.1077/0.1141**. ML coordinate-error
estimate 0.03 Å. All 2375 non-H atoms refined anisotropically; H handled as riding.

**Concluded.** The diagnosis was right — this was recoverable displacement, and one
ordinary refinement recovered the bulk of it. Waters untouched at 212, as intended.

---

## Step 2 — Refinement 2/6: ordered-solvent rebuilding

**What.** Continued from run 1 with `main.ordered_solvent=True`, 5 macrocycles.

**Why.** 212 waters for a 262-residue protein at 0.885 Å is well below what such data
supports; missing solvent is unmodelled scattering that inflates R everywhere.

**Measured.** R-work/R-free **0.1026/0.1081**; independently recomputed with
`phenix.model_vs_data` as 0.1034/0.1086. Waters cycled 212 → 197 → 342 → 266.
MolProbity 1.74 → **0.83**, clashscore 5.97 → 1.15, Rama favored 93.82 → **98.46 %**,
rotamer outliers 0.49 → **0.00 %**.

**A judgement I initially got wrong, and corrected.** Mid-run, R-free rose to 0.1237
with the work/free gap widening from 0.006 to 0.013 — the textbook signature of the
solvent picker fitting noise. My first read was that solvent building was overfitting.
It was not: the last two macrocycles recovered to 0.1015/0.1086 as the added waters were
refined and filtered. **Lesson applied for the rest of the session: judge a refinement
on its converged result, not on a mid-run snapshot**, because the solvent picker
transiently degrades the model at the moment it adds peaks.

---

## Step 3 — Refinement 3/6: weight optimization *(tested, rejected)*

**What.** `target_weights.optimize_xyz_weight=True` + `optimize_adp_weight=True`,
3 macrocycles, from the run-2 model.

**Why — a real hypothesis, not a shot in the dark.** Bond RMSD had settled at 0.0073 Å.
For 0.885 Å data that is *too tight*: sub-Ångström structures typically refine to
0.012–0.015 Å because the data can support looser stereochemical restraints. Restraint
weights tuned for ~2 Å data over-restrain atomic-resolution models and leave R higher
than necessary. If that were happening here, letting PHENIX search the weight grid
should loosen geometry and drop R.

**Measured.** R-work/R-free **0.1026/0.1092** — R-work identical to run 2, R-free
marginally worse. The optimizer moved the X-ray weight *down* (wxc 21.3 → 1.7), i.e. it
tightened geometry rather than loosening it.

**Concluded.** Hypothesis refuted by measurement. PHENIX's automatic per-macrocycle
weighting was already at or near optimum, and the expensive grid search bought nothing.
**Discarded this model and kept run 2.** Recording the negative result matters as much
as the positive ones: this is a lever that looked principled and did not pay.

---

## Step 4 — Diagnose what was still limiting *(free — no budget spent)*

**What.** Re-examined the R-vs-resolution profile of the run-2 model and audited the
per-atom anisotropy, plus read the `ordered_solvent` parameter defaults.

**Measured.** Two findings:

1. **The outermost shell is the outlier.** R-work by shell ran 0.0799 (1.55–1.23 Å) →
   0.0920 (1.23–0.98 Å) → **0.1581** (0.977–0.885 Å). The finest shell is nearly twice
   the adjacent one. Some of this is irreducible — ⟨Fobs⟩ falls to 34 there, so the data
   are noise-dominated — but a jump that size also points to model detail that is missing
   *specifically at high resolution*.
2. **75 waters and 1 chloride were isotropic.** PHENIX's default is
   `ordered_solvent.new_solvent = *isotropic`, so every water the picker added in run 2
   carried a single B while all 2102 protein atoms were anisotropic.

**Concluded.** An isotropic water at 0.885 Å is an under-parameterized atom in a model
where everything around it is anisotropic, and anisotropy is precisely a
high-resolution term — it lines up with the shell where the model is weakest. Making all
non-H atoms anisotropic costs ~375 extra parameters against 251 823 reflections
(≈10 observations per parameter overall), which this data comfortably supports.

---

## Step 5 — Refinement 4/6: anisotropic solvent + picker — **crashed** *(counted)*

**What.** `ordered_solvent=True` with `ordered_solvent.new_solvent=anisotropic` and
`refine.adp.individual.anisotropic="not element H"`, 6 macrocycles.

**Measured.** Completed two macrocycles, then died:

```
RuntimeError: cctbx Internal Error: ... CCTBX_ASSERT(f.use_u_iso()) failure
  mmtbx/solvent/ordered_solvent.py:713  in refine_oat
```

The ordered-solvent module's own refinement step calls `set_refine_u_iso` on the water
selection, which asserts if those waters are anisotropic. Notably `refine_oat = False`
was already the effective setting (confirmed in `r4_004.eff`) yet `refine_oat()` was
called anyway — the guard is not honoured in this build, so the incompatibility cannot
be parameterized around.

**Budget accounting.** This run **did** perform refinement before failing, so I counted
it against the 6-invocation budget rather than treating it as a free parameter rejection.
(The one launch I did *not* count — annotated in `transcript.md` §4 — exited on an
unrecognized PHIL parameter before any refinement began and wrote no model.)

**Concluded.** `ordered_solvent=True` and anisotropic waters are mutually exclusive in
PHENIX 2.0-5936. With 2 runs left I chose not to gamble a second one on the picker:
decouple the two and take the anisotropy, since the solvent set had already converged
at 266 waters across runs 2 and 3.

---

## Step 6 — Refinement 5/6: all non-H atoms anisotropic, picker off

**What.** From the run-2 model: `anisotropic="not element H"`,
`ordered_solvent=False`, 5 macrocycles.

**Measured.** R-work/R-free **0.1010/0.1069** (independently 0.1018/0.1076).
MolProbity 0.83 → **0.72**, clashscore 1.15 → **0.69**. All 266 waters and the chloride
now anisotropic.

**Concluded.** The anisotropy hypothesis paid, unlike the weight hypothesis: R-free
improved 0.1081 → 0.1069 and R-work 0.1026 → 0.1010 while geometry *also* improved.
Gains on fit and geometry moving together is the signature of a genuinely better model
rather than parameter-count overfitting.

---

## Step 7 — Refinement 6/6: convergence polish

**What.** Same protocol as run 5, 8 macrocycles, from the run-5 model.

**Why.** Run 5 was still descending slowly at its macrocycle limit. Every fresh
`phenix.refine` invocation in this session showed a characteristic restart bump
(R rises ~0.005 in macrocycle 1 as bulk-solvent and scale parameters are re-derived,
then recovers), so a longer run was the way to confirm true convergence.

**Measured.** Final three macrocycles were flat at 0.1011/0.1070, 0.1011/0.1070,
0.1009/0.1069 — converged. Final R-work/R-free **0.1009/0.1069**.
MolProbity 0.72 → **0.66**, clashscore 0.69 → **0.46**.

**Concluded.** The model is at its refinement limit under this protocol. Further
macrocycles would not help.

---

## Final model selection

Runs 5 and 6 are statistically indistinguishable on fit — R-free 0.1069 for both from
`phenix.refine`, and 0.1076 vs 0.1087 on independent `model_vs_data` recomputation, a
spread well inside the ~0.002 noise floor of a 2381-reflection free set. I therefore
**selected run 6 on geometry**, where it is cleanly better: MolProbity 0.66 vs 0.72,
clashscore 0.46 vs 0.69, at equal R.

| | Perturbed input | **final.pdb (run 6)** |
|---|---|---|
| R-work / R-free | 0.3744 / 0.3772 | **0.1009 / 0.1069** |
| MolProbity score | 1.74 | **0.66** |
| Clashscore | 5.97 | **0.46** |
| Rama favored | 93.82 % | **98.46 %** |
| Rama outliers | 0.00 % | 0.39 % |
| Rotamer outliers | 0.49 % | **0.00 %** |
| RMS bonds / angles | 0.0109 Å / 1.17° | 0.0075 Å / 0.95° |
| Waters | 212 | 266 |
| Anisotropic non-H atoms | 2350 of 2431 | **2431 of 2431** |

## Known residual issues — stated rather than hidden

- **One Ramachandran outlier**, ASN A 224 (pre-proline, φ=175.1°, ψ=99.5°), giving
  0.39 % against the <0.2 % goal. The input model had zero Rama outliers, so this
  appeared during refinement. **I deliberately did not force it back.** At 0.885 Å the
  data, not a Ramachandran prior, should dictate main-chain conformation; genuinely
  strained pre-proline residues do occur and are resolvable at atomic resolution.
  Applying Ramachandran restraints to flatten a single residue at this resolution would
  be model bias dressed up as a better validation number. Flagging it as the one place
  the final model is worse than its input.
- **266 waters may still be conservative** for 0.885 Å data. The picker converged there
  under default cutoffs across two runs, and the PHENIX crash in step 5 removed my
  ability to build more solvent *and* keep waters anisotropic within the remaining
  budget. I chose the measured gain (anisotropy, +0.0012 R-free) over the unmeasured one
  (more waters) rather than gamble a run on a code path that had already failed once.
- **The 0.977–0.885 Å shell remains at R-work ≈ 0.16.** Partly irreducible given
  ⟨Fobs⟩ ≈ 34 in that shell, but unmodelled alternate side-chain conformations are the
  likely remaining contributor. Building new altlocs was out of reach on the remaining
  budget and is the first thing I would try with more runs.

## Self-measured numbers are advisory

All figures above are my own measurements. R values were cross-checked with
`phenix.model_vs_data` (an independent recomputation with its own bulk-solvent
treatment) rather than trusted from the refinement log alone, and validation came from
`phenix.molprobity`. The benchmark's independent re-measurement from `final.pdb` is
authoritative.
