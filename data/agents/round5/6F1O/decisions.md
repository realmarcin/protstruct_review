# 6F1O — blinded agentic recovery: decisions log

Subject: perturbed model `/tmp/nc_round1_work/r4p_6f1o.pdb` + data `/tmp/nc_round1_cache/6f1o.mtz`
Scratch: `/tmp/agent_r5_6f1o/`
Final model: `final.pdb` (= `/tmp/agent_r5_6f1o/r6_006.pdb`)

## Headline

| | R-work | R-free | gap | MolProbity | clashscore | Rama favored | Rama-Z (whole) | waters |
|---|---|---|---|---|---|---|---|---|
| start (perturbed) | 0.4009 | 0.4086 | 0.008 | 1.76 | 4.44 | 90.40% | -5.05 (poor) | 171 |
| **final** | **0.1203** | **0.1366** | 0.016 | 1.18 | 3.95 | 100.00% | -0.77 (good) | 327 |

Refinement budget: **6 of 6 used** (one of the six crashed partway; see run 4).

## Step 0 — characterize the damage before touching it

Data: P2₁2₁2₁, 30.06 × 56.18 × 73.29 Å, **0.96 Å** resolution, 76,639 reflections,
99.2% complete. Columns found with `gemmi mtz --dump`: `FOBS/SIGFOBS` (amplitudes),
`DANO/SIGDANO` (anomalous), `R-free-flags` (0/1), `R-free-flags-1` (0–19), and
`FWT/PHWT`, `DELFWT/PHDELWT` (map coefficients).

Free-flag polarity: counted directly — 3,839 reflections with value 0 vs 72,800 with
value 1, i.e. **5% test set at flag value 0** (CCP4 convention). Passed explicitly as
`test_flag_value=0` rather than trusting auto-detection.

**Deliberate abstention:** the MTZ contains `FWT/PHWT` and `DELFWT/PHDELWT`, which are
map coefficients computed from the *deposited* model. Using them to rebuild would import
deposited phase information through the back door and make the "recovery" partly
fictitious. I used **only `FOBS,SIGFOBS` and `R-free-flags`** throughout. Every phase in
this work came from my own model.

Model: single chain A, 129 residues, 1,206 heavy atoms + 991 riding hydrogens, 171
waters, one PO4, one Cl, alternate conformations at several residues, fully anisotropic
ADPs. Four disulfides (6–127, 30–115, 64–80, 76–94).

**The key diagnostic.** Baseline R-work/R-free = 0.4009/0.4086 — badly wrong. But
MolProbity on the *same* file said: 0% Ramachandran outliers, 0% rotamer outliers,
clashscore 4.44, bond RMSD 0.0097 Å, angle RMSD 1.14°. Geometry was essentially clean.

That combination — terrible R, ideal local geometry — rules out a random atom shake
(which wrecks bonds and angles). It is the signature of a perturbation applied in a way
that *preserved* restraint terms while moving the structure off the data. Two further
observations pinned it down:

- R-work rose monotonically with resolution (0.33 at low res → 0.48 in the outer shell),
  which is the classic signature of a **random coordinate error** of a few tenths of an Å
  rather than a rigid-body misplacement.
- Rama-Z was **-5.05 ("poor")** despite zero outliers, so backbone *conformation* was
  systematically distorted even though no single residue crossed an outlier threshold.

Conclusion: this is a coordinate/conformation problem, not a stereochemistry problem.
That decided the whole strategy — the job was to move atoms back, not to regularize them.

**Do the anisotropic ADPs carry usable signal?** Tested rather than assumed: converted
the model to isotropic and re-measured. R went 0.4009/0.4086 → 0.4061/0.4132, a cost of
only ~0.005. The anisotropic ADPs were nearly worthless while coordinates were wrong. I
therefore started from **isotropic** ADPs — they are far more stable when coordinates are
off, because anisotropic ADPs otherwise absorb coordinate error and cement atoms into
wrong positions. The 0.005 was recovered many times over later.

Hydrogens were regularized with `phenix.ready_set` (the model already had 991 H; ready_set
renamed/rebuilt them to match the monomer library).

## Run 1 — simulated annealing (the decisive move)

`start_iso.updated.pdb`, SA (Cartesian, mode=first) + default Phenix 2.0 strategy
(individual sites + local real-space + individual ADP + occupancies), 5 macrocycles.

**Why SA rather than plain minimization:** the radius of convergence of gradient
refinement is roughly d_min/2 — about 0.5 Å here — which is uncomfortably close to the
error I estimated. Plain minimization risked stalling in a local minimum around 0.30.
SA also performs ordinary minimization within its macrocycles, so it costs one run and
buys both. With R-free at 0.41 the downside risk was small.

Result: **0.4061/0.4135 → 0.1742/0.1861.** The SA log reported `dist_moved = 0.32 Å`,
which retrospectively confirms the diagnosis: the perturbation was a ~0.3 Å coordinate
displacement.

Geometry improved at the same time, which is the important part — this was repair, not
overfitting: Rama favored 90.4% → **100%**, Rama-Z -5.05 → **-0.86 (good)**, clashscore
4.44 → 1.97, MolProbity 1.76 → 0.96.

## Run 2 — anisotropic ADPs

Now that coordinates were essentially right, the anisotropic model becomes justified:
72,800 working reflections against 1,206 × 9 ≈ 10,900 ADP parameters is ~6.7
observations per parameter, comfortable at 0.96 Å.

`anisotropic="not element H"`, 4 macrocycles. Result: **0.1742/0.1861 → 0.1373/0.1505**.
Geometry held or improved (MolProbity 0.79, clashscore 0.99). Run separately from solvent
work specifically so the anisotropic gain could be attributed on its own.

## Run 3 — ordered solvent

The strategy guidance flagged solvent as possibly damaged, and the maps were now much
better than at the start, so this was the right point to rebuild it.
`ordered_solvent=True`, `mode=every_macro_cycle_after_first`, 5 macrocycles.

Result: **0.1373/0.1505 → 0.1312/0.1426**. Waters 171 → 295 (~2.3 per residue, normal for
sub-Å). Note R-work briefly *rose* at the start of this run as the initial filter deleted
poorly-supported input waters — evidence that the input solvent model had indeed been
damaged.

## Run 4 — crashed, and it counts

Attempted anisotropic ADPs for *all* heavy atoms including the 146 newly-placed waters,
via `ordered_solvent.new_solvent=anisotropic`. Phenix died with a cctbx internal error:

```
mmtbx/solvent/ordered_solvent.py -> refine_oat -> calculators.adp -> set_refine_u_iso
RuntimeError: cctbx Internal Error: ... CCTBX_ASSERT(f.use_u_iso()) failure.
```

The ordered-solvent code path that refines newly-added waters assumes they are isotropic,
so `new_solvent=anisotropic` is incompatible with solvent updating in this build.

**This run completed two full macrocycles of genuine refinement (reaching 0.1296/0.1592)
before dying, so I am counting it against the 6-run budget.** No model was written; the
best model on disk remained run 3's. (For contrast: the earlier launch rejected for the
unrecognized PHIL name `refinement.input.xray_data.r_free_flags.test_flag_value`, and the
`phenix.refine --version` traceback, both failed *before* refinement began and are not
counted. Both appear in the transcript.)

## Run 5 — anisotropic waters, done safely — and rejected on the evidence

Achieved the same intent without the crashing code path: converted all 1,330 heavy atoms
to anisotropic *outside* refinement with `phenix.pdbtools` (not a refinement invocation),
then refined in the configuration run 3 had already proven stable.

Result: **0.1258/0.1438**. Compared with run 3's 0.1312/0.1426 — R-work better by 0.005,
**R-free slightly worse**, and the work–free gap widened from 0.011 to 0.018.

That is textbook overfitting: the extra 6 parameters per water bought agreement with the
working set and nothing for the test set. **I rejected run 5 and carried run 3 forward.**
Confirmed by independent re-measurement with `phenix.model_vs_data` rather than trusting
the refinement log's own number (r3_003 0.1312/0.1425 vs r5_005 0.1258/0.1444).

## Run 6 — weight optimization (final, chosen)

Last run, started from run 3's model. `optimize_xyz_weight=True`,
`optimize_adp_weight=True`, ordered solvent on, 5 macrocycles.

Rationale: Phenix's default `wxc_scale=0.5` is tuned for typical resolutions and tends to
be *over*-restrained at sub-Å, where the data genuinely determine the structure and
should be allowed to outvote the restraint library. Optimization selected wxc ≈ 1.59.

Result: **0.1203/0.1366** — better than run 3 on *both* R-work and R-free.

**Disclosure of a real caveat:** `optimize_xyz_weight`/`optimize_adp_weight` select the
weight using R-free. This is standard, widely-used Phenix practice and it tunes only two
global scalars, but it does couple the free set to a hyperparameter, so my final R-free
is very mildly optimistic. I judged the improvement genuine rather than cosmetic because
geometry stayed sound and the change is physically motivated for 0.96 Å data — but the
caveat belongs on the record, and the benchmark's independent re-measurement will
reproduce the same (slightly optimistic) value rather than correct it.

Bond RMSD rose to 0.0116 Å and angle RMSD to 1.15° as the weight relaxed. That is
expected and remains entirely normal for a 0.96 Å structure; it reflects real
data-driven deviation from library ideals, not strain.

## Final model selection

| candidate | R-work | R-free | MolProbity | bond RMSD | verdict |
|---|---|---|---|---|---|
| r3_003 | 0.1312 | 0.1425 | 1.14 | 0.0083 | superseded |
| r5_005 | 0.1258 | 0.1444 | 1.09 | 0.0082 | rejected — R-free worse, gap widened |
| **r6_006** | **0.1203** | **0.1366** | **1.18** | 0.0116 | **chosen** |

Chose r6_006: best R-free by a clear margin (0.006 over r3_003, well beyond the ~0.002
noise on 3,839 free reflections), with geometry statistically indistinguishable from the
alternatives.

Final chemical sanity check: all four disulfides intact at 2.04–2.07 Å (ideal), 327
waters, B-factors 8.2–50.8 Å² (mean 16.4), occupancies 0.21–1.00, alternate conformations
A/B preserved.

## Where I stopped and why

The budget was spent, and marginal returns had flattened: run 5 showed added parameters
no longer buying R-free, and run 6's gain came from rebalancing existing parameters
rather than adding new ones. Remaining avenues I judged not worth the risk with the runs
available: modelling additional alternate conformations (needs manual map inspection and
would have consumed the budget unpredictably), and explicit H-position refinement (riding
H are adequate even at 0.96 Å).

## Self-measured final numbers

**R-work = 0.1203, R-free = 0.1366** at 0.96 Å — confirmed by `phenix.model_vs_data`
independently of the refinement log. These are advisory; the benchmark re-measures.
