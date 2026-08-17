# 6XVM — blinded agentic recovery (round 5)

Agent working directory: `/tmp/agent_r5_6xvm/`
Deliverable model: `final.pdb` (= `/tmp/agent_r5_6xvm/r6_001.pdb`)

## Headline

| | R-work | R-free | clashscore | Rama favored | Rama outliers | Rotamer outliers | waters |
|---|---|---|---|---|---|---|---|
| Perturbed input `r4p_6xvm.pdb` | 0.4153 | 0.4137 | 6.28 | 88.44% | 0.44% | 2.82% | 337 |
| **final.pdb** | **0.1056** | **0.1200** | **2.63** | **96.44%** | **0.00%** | **0.00%** | **479** |

Resolution 40.61–0.90 Å, P2<sub>1</sub>, 130,658 reflections, 92.4% complete, free set 4.92%
(6,431 reflections, test flag value 0). Independent re-measurement with `phenix.model_vs_data`
on the final model gives R-work 0.1057 / R-free 0.1205, consistent with the refinement log.

Refinement budget: **6 of 6 invocations used** (one of the six crashed mid-refinement and is
counted; see step 3). One additional launch was rejected on a parameter error before refinement
began and is *not* counted — see step 2a.

---

## Step 0 — the diffraction data had been deleted; recovering it

`/tmp/nc_round1_cache/6xvm.mtz` did not exist when the task started. The `/tmp` reaper had
removed it (the directory itself survived, along with `6xvm.mtz.sha256`, but the MTZ was gone).
Per the task rules I did not touch the network and did not read anything else under
`nc_round1_cache/`.

Following the sanctioned recovery route, I looked for a phenix.refine output MTZ carrying a
faithful copy of the observations. `/tmp/nc_round1_work/r4r_r4p_6xvm_001.mtz` is a refinement
output whose MTZ `TITLE` record still reads:

```
/tmp/nc_round1_cache/6xvm.mtz:FOBS,SIGFOBS,DANO,SIGDANO,systematic_abs
```

That names the deleted file and its original column labels.

**What I copied, and what I deliberately did not.** I extracted *only* experimental-observation
columns — `F-obs`, `SIGF-obs`, and the free flags — by raw column access
(`/tmp/agent_r5_6xvm/recover_data.py`). Every model-derived column in that file
(`F-model`, `PHIF-model`, `2FOFCWT`, `FOFCWT`, `ANOM`, and the phenix-derived
`F-obs-filtered`) was discarded, so no prior model — mine or anyone else's — can leak into
this run through the data. `F-obs`/`SIGF-obs` are the values phenix read verbatim from the
original file, as distinct from `F-obs-filtered` which phenix computed.

**Fidelity checks before trusting the recovery:**

- The dataset is anomalous, so phenix had expanded the single original `R-free-flags` column
  into a Friedel pair. I asserted `R-free-flags(+) == R-free-flags(-)` on all 137,865 rows
  where both mates are present. Zero disagreements, so collapsing back to one column is exact.
- Recovered free-set fraction is 4.92% at flag value 0, matching `test_flag_value = 0`
  recorded in the archived round-4 parameter file.
- Recovered labels are `FOBS,SIGFOBS` / `R-free-flags` — identical to the labels the original
  cache file used, so the recovered MTZ is a drop-in replacement.
- Scoring the *given perturbed model* against the recovered data yields R-work 0.4153 /
  R-free 0.4137. A mispaired or corrupted dataset would give R near 0.5+; a coherent 0.41
  confirms the data belong to this crystal and this model.

I did **not** read the archived `mvd_phenix_r4p_6xvm.log` (which contains a prior measurement of
this same perturbed model) even though nothing forbade it — the fidelity checks above are
self-contained, and I preferred not to anchor on another leg's numbers.

The recovered file is included here as `6xvm_recovered.mtz` because the original observations no
longer exist on disk and the benchmark's independent re-measurement will need them.

## Step 1 — reading the damage before spending budget

At 0.90 Å the model is 4,146 atoms in 4 protein chains (~59 residues each) with A/B alternate
conformations, 337 waters, and 2 glycerols.

I initially misread the ADP state: 1,841 of 4,146 atoms carry no `ANISOU` record, which looked
like the perturbation had stripped ADPs. Checking the element column showed those 1,841 atoms
are **riding hydrogens**, correctly isotropic; all 2,305 heavy atoms were already anisotropic.
So ADP *type* was undamaged and needed no intervention. This mattered — acting on the wrong
reading would have wasted a run converting hydrogens to anisotropic.

The real damage was coordinates: R 0.41, Ramachandran favored down at 88.4% with 0.44%
outliers, 2.82% rotamer outliers, clashscore 6.28.

**Hydrogens — attempted and abandoned.** Since the model already had riding H, none needed
adding, but before establishing that I ran `phenix.ready_set` and `phenix.reduce`. Both
returned models I discarded: I verified their output and found the heavy-atom count did not
match the input. That verification is why the mangled files never entered the refinement —
I used the untouched `start.pdb` throughout and let `phenix.refine`'s own `nqh_flips` handle
Asn/Gln/His flips.

## Step 2 — run 1: restore coordinates

`phenix.refine start.pdb`, default strategy (`individual_sites` + `individual_sites_real_space`
+ `individual_adp` + `occupancies`), 8 macrocycles, riding H. No solvent manipulation — I wanted
the coordinates recovered before letting an automatic water-picker interpret the maps.

Result: **0.4153/0.4137 → 0.1264/0.1373.** Clashscore 6.28→4.19, Rama outliers 0.44%→0.00%
(favored 88.4%→96.4%), rotamer outliers 2.82%→0.47%. The real-space component of the default
strategy did most of the work; no simulated annealing was needed, and I concluded the
perturbation was a smooth displacement rather than anything requiring a large-radius search.

### Step 2a — a launch that does not count against budget

My first attempt passed `nproc=8`, which phenix rejected as ambiguous
(`refinement.main.nproc` vs two `qi.*` scopes). It exited during PHIL parsing, before any
refinement, and wrote no output. Per the rules this is not counted. Relaunched as
`main.nproc=4`.

## Step 3 — run 2: ordered solvent, crashed (counted)

Ran solvent rebuilding with `ordered_solvent.new_solvent=anisotropic`, reasoning that new waters
should match the anisotropic model at 0.90 Å.

It refined normally to r_work 0.1216 / r_free 0.1348, then **crashed** at the first solvent
update:

```
RuntimeError: cctbx Internal Error: ... CCTBX_ASSERT(f.use_u_iso()) failure.
  mmtbx/refinement/calculators.py -> data.set_refine_u_iso(selection=selection)
```

phenix's ordered-solvent code path refines water ADPs isotropically and asserts on it, so
`new_solvent=anisotropic` is incompatible with it. No model was written. Because this run did
perform refinement before dying, **I count it against the 6-invocation budget** rather than
claiming it as a pre-refinement failure.

## Step 4 — run 3: ordered solvent, default isotropic new waters

Same run from `r1_001.pdb` with the offending parameter dropped.

Result: **0.1192/0.1312**, waters 337→447, rotamer outliers 0.47%→0.00%. Solvent rebuilding
earned its cost (R-free −0.006), confirming the perturbation had indeed cost real solvent
structure.

## Step 5 — run 4: weight optimization

Run 3 ended at bond RMSD 0.008 Å / angles 1.161°. At 0.90 Å that is *tighter* than the data
warrant — geometry restraints were over-weighted relative to an exceptionally strong X-ray
term, holding atoms back from the density. So I turned on
`target_weights.optimize_xyz_weight` and `optimize_adp_weight`.

Result: **0.1059/0.1194** — the single largest gain after run 1 (R-free −0.012), with bonds
relaxing to a resolution-appropriate 0.010 Å. Waters 447→475.

**But clashscore regressed to 7.61**, worse than the perturbed input's 6.28. Diagnosing before
reacting: of 29 clashes, 21 involved newly-added chain-S waters sitting on top of side chains.
The cause is phenix's own defaults — `ordered_solvent.dist_min` is 1.8 Å, and its
`mask_atoms_selection` covers only backbone atoms (`CA/CB/N/C/O`), so nothing was policing
water-to-side-chain distance.

## Step 6 — run 5: stricter solvent distance (did not work)

Re-picked solvent with `dist_min=2.3` and `mode=every_macro_cycle_after_first`.

Result: 0.1053/0.1198, waters 496 — R-free flat, and **clashscore still 7.61**. Raising
`dist_min` was ineffective *because* the distance test is applied against backbone atoms only;
the clashes were with side-chain methyls and hydroxyls, which that filter never examines. A
correct read of the parameter's scope would have predicted this. Budget spent for information
rather than improvement.

## Step 7 — targeted water removal (no refinement invocation)

Rather than fight the automatic picker again, I parsed the clash list and removed the specific
waters at fault: 17 unique waters clashing with non-water atoms, out of 496 (3.4%), removed with
`phenix.pdbtools`. Their clash partners cluster on flexible surface side chains — Glu93, Thr96,
Glu97, Lys103, Glu106, Val111, Asp117 — which strongly suggests those waters were occupying
density belonging to alternate side-chain conformations the model does not carry, rather than
being real solvent.

Effect of the deletion alone: **clashscore 7.61 → 2.10.**

## Step 8 — run 6: final polish

Weight-optimized refinement of the trimmed model with `ordered_solvent=False`, so no new waters
could be introduced to undo the cleanup. 6 macrocycles.

Result: **R-work 0.1056 / R-free 0.1200**, clashscore 2.63, Rama 96.44% favored / 0.00%
outliers, rotamer outliers 0.00%, bonds 0.009 Å / angles 1.209°.

## Why this model was chosen

| candidate | R-work | R-free | clashscore |
|---|---|---|---|
| run 4 | 0.1059 | **0.1194** | 7.61 |
| run 5 | **0.1053** | 0.1198 | 7.61 |
| **run 6 (final.pdb)** | 0.1056 | 0.1200 | **2.63** |

Run 4 holds the nominally best R-free, but by 0.0006 — far inside the noise of which waters
happen to be present. Run 6 gives that up to cut clashscore by a factor of three. Since the task
asks for fit to data *and* sound geometry, and a clashscore of 7.6 at 0.90 Å is poor by any
standard while 0.0006 in R-free is not a real difference, run 6 is the honest choice.

## Known remaining weaknesses

- **Ramachandran favored is 96.44%, short of the 98% goal**, and did not move after run 1
  despite four further refinements. Zero outliers, so nothing is grossly wrong, but ~8 residues
  sit in allowed-but-not-favored space. Fixing these likely needs alternate-conformation
  rebuilding, which I had neither the tooling nor the remaining budget for.
- **~8 protein–protein clashes remain** (e.g. Lys103 HD2 / Glu106 OE1; Leu108 HD13 / Ile132
  HD13). Same root cause — unmodelled alternate conformers on flexible surface side chains.
- **203 heavy atoms (the ordered-solvent waters) are isotropic** while the other 2,248 are
  anisotropic. At 0.90 Å they arguably should be anisotropic, but the crash in step 3 shows
  phenix will not do this inside the solvent code path, and I had no invocation left to convert
  them in a separate pass.
- Self-measured numbers only; the benchmark's independent re-measurement governs.
