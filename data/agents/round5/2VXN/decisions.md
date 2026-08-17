# 2VXN blinded recovery — decisions log

Agent working dir: `/tmp/agent_r5_2vxn/`
Inputs: `/tmp/nc_round1_work/r4p_2vxn.pdb` (perturbed model), `/tmp/nc_round1_cache/2vxn.mtz` (data).
Final model: `final.pdb` (copy of `/tmp/agent_r5_2vxn/r6/r6_001.pdb`).

## Refinement budget accounting

Limit was 6 invocations of a refinement program. I made **6 `phenix.refine` invocations**, of
which **5 performed refinement** and **1 (the first) aborted in 4 s on a PHIL parameter error
without refining anything**. I counted the aborted call against the budget anyway, because the
rule is written as "invocations of refinement programs" and the conservative reading protects
the entry. Everything else I ran (`model_vs_data`, `molprobity`, `ramalyze`, `rotalyze`,
`clashscore`, `real_space_correlation`, `ready_set`, `gemmi`) is a validation/measurement or
model-prep tool and is unlimited.

## Step 0 — characterize the data

`gemmi mtz --dump` on the MTZ: space group C 1 2 1, cell 98.36 50.65 58.66 / 90 117.56 90,
**0.82–19.08 Å**, 223 327 reflections, 89.7 % complete. Columns: `FOBS`, `SIGFOBS`,
`R-free-flags`. I confirmed the free set by counting flag values directly with `iotbx.mtz`:
`{1: 212160, 0: 11167}` — so the test set is flag value **0**, 5.0 % of data, which is what
PHENIX auto-detects. I did not override the auto-detection, but I verified it rather than
assuming it.

This is atomic-resolution data. That single fact drove every subsequent decision: at 0.82 Å
the correct model is anisotropic-ADP, hydrogen-bearing, and heavily hydrated, and the
acceptable R range is far below what one would accept at 2 Å.

## Step 1 — baseline, and diagnosing *what kind* of damage this was

`phenix.model_vs_data` on the perturbed model: **R-work 0.3915 / R-free 0.3908**.

Rather than start refining, I first asked what had actually been broken, because the answer
changes the protocol. Measurements:

| probe | result | reading |
|---|---|---|
| MolProbity geometry | bond RMSD **0.006 Å**, angle RMSD **1.15°** | local geometry is *pristine* |
| Ramachandran | 95.55 % favored, 0.40 % outliers | mildly degraded |
| Rotamers | **3.60 %** outliers | elevated (goal < 0.3 %) |
| Clashscore | 8.54 | moderate |
| ANISOU stripped, re-measured | R-work 0.3966 (vs 0.3915) | **ADPs are not the damage** |
| protein real-space CC | ~0.82 typical, spread 0.55–0.95 | globally degraded, not one bad patch |
| water real-space CC | mean **0.53**, 174 of 419 below 0.5 | solvent is badly wrong |

The decisive combination is *perfect bond/angle geometry with R = 39 %*. Random Cartesian
noise would have wrecked bond lengths; it did not. So the perturbation displaced atoms in a
way that preserves local geometry — a smooth/torsional displacement field — plus it damaged
side-chain rotamers and the solvent model.

I also checked the shell-wise R profile: ~0.25 at 6–4 Å rising monotonically to **0.456** in
the 0.96–0.82 Å shell. A gross misplacement (wrong origin, rigid-body error) would be bad at
*all* resolutions; this profile is the signature of sub-Ångström per-atom displacement, which
costs you progressively more as resolution increases. Estimated displacement ~0.3–0.5 Å.

**Conclusion:** rigid-body refinement would be wasted budget. What is needed is coordinate
refinement with a convergence radius comfortably larger than ~0.5 Å, then anisotropic ADPs and
a rebuilt solvent shell to recover the high-resolution shells.

## Step 2 — model preparation (no budget cost)

`phenix.ready_set` added **2125 riding hydrogens** and generated restraints for the four
ligand types present (PGH, PGA, GOL, ACT).

**Caught a trap here.** ready_set's `.cif` output contains *five* data blocks: the four
`data_comp_*` restraint blocks **and a `data_default` block holding a complete copy of the
model** (33 `_atom_site` records). PHENIX's DataManager reported it as "Found model", so
passing that file to `phenix.refine` alongside the real model would have loaded the structure
twice. I split the file with a short Python pass and kept only the four `data_comp_*` blocks
as `ligands.cif`. This was caught by reading the file, not by a failure — it would have been a
silent corruption.

## Step 3 — refinement 1 (aborted): the canary earned its keep

I deliberately made the first refinement a cheap low-resolution run so that a mistake would
surface in seconds rather than after an hour. It failed in **4 seconds**:
`refinement.input.xray_data.high_resolution` is **not a valid parameter in PHENIX 2.0** — that
scope now exists only under the GUI-mirror `gui.` scope; data selection moved to the
DataManager. Everything else in my command line parsed correctly.

Having burned a slot, I stopped guessing at syntax and instead read the authoritative PHIL
source at
`lib/python3.9/site-packages/phenix/refinement/__init__.params` for every remaining parameter.
Two useful findings from that read:

- `main.stir` (stepwise increase of resolution) is documented but **has no implementation** in
  this build — no reference to it anywhere in the refinement module. Do not rely on it.
- `main.switch_to_isotropic_high_res_limit = 1.5` means PHENIX force-converts ADPs to isotropic
  at resolutions worse than 1.5 Å, *and does not automatically re-expand them*. Anisotropic
  refinement therefore has to be requested explicitly via
  `refine.adp.individual.anisotropic`.

Since no resolution-cut parameter exists, I truncated the MTZ myself with `iotbx.mtz`,
preserving the exact column labels (verified with `gemmi mtz --dump`: 29 721 reflections at
1.6 Å, labels intact).

## Step 4 — refinement 2: 1.6 Å convergence stage

**Why lower resolution first.** The convergence radius of reciprocal-space refinement scales
with d_min (~d_min/2). At 0.82 Å that is ~0.4 Å, right at the edge of the displacement I had
estimated — a meaningful fraction of atoms would have been stranded in the wrong minimum, and
once you over-refine a wrong model at atomic resolution it is very hard to back out. At 1.6 Å
the radius is ~0.8 Å, comfortably larger than the damage. 1.6 Å (rather than 2.5 Å) also keeps
enough data to leave the model well-determined, and sits just above the 1.5 Å isotropic
threshold, so ADPs stay isotropic — which is what I wanted at a stage where anisotropic ADPs
would only absorb coordinate error and disguise it.

Settings: `individual_sites + individual_sites_real_space + individual_adp + occupancies`,
5 macrocycles, `nqh_flips=True`, `ordered_solvent=True`. I included real-space refinement
deliberately — its per-residue convergence radius is larger than reciprocal-space and it is the
part of the protocol that can fix the elevated rotamer outliers. I turned on ordered solvent
here rather than deleting the waters outright: PHENIX's update cycle removes waters with poor
density and adds new ones, which addresses the bad solvent without throwing away the real
scattering of the good waters.

**Result: R-work 0.1114 / R-free 0.1469 at 1.6 Å**, 566 waters (from 419). Measured against
the *full* 0.82 Å data this model gives **0.1683 / 0.1824**, with the outer 0.96–0.82 Å shell
at 0.282 — exactly the shell that anisotropic ADPs address. Confirmed ANISOU count was now 0,
as predicted.

## Step 5 — refinement 3: full resolution, anisotropic ADPs restored

Full 0.82 Å data, 4 macrocycles, `refine.adp.individual.anisotropic="not element H"`,
ordered solvent on. Parameter ratio check before committing: ~2650 non-H atoms × (6 ADP + 3
xyz) ≈ 24 k parameters against 212 k working reflections, ~9:1 — comfortably determined.

**Result: R-work 0.0999 / R-free 0.1138.** Geometry: 0.00 % Rama outliers, 97.98 % favored,
rotamer outliers down 3.60 % → 0.90 %, clashscore 8.54 → 5.93, MolProbity score 1.33.

The per-macrocycle trajectory (0.1162 → 0.1094 → 0.1013 → 0.0999) was still falling, so this
was **not converged** and further refinement was justified rather than reflexive.

## Step 6 — refinement 4: weight optimization (killed, no output)

Diagnosis motivating this step: bond RMSD was **0.0068 Å**. That is *tighter* than a 0.82 Å
structure should be — at atomic resolution 0.010–0.015 Å is normal, and an over-tight value
means the geometry restraints were dominating data that is well able to speak for itself.
Loosening the restraint weight here is not overfitting; R-free is the guard, and PHENIX's
weight optimization selects the weight *by* R-free.

Located the correct parameter path by reading the source
(`phenix/refinement/xyz_reciprocal_space.py` → `params.target_weights.optimize_xyz_weight`;
defaults in `mmtbx/refinement/weights.py`). Also noted the guard in `_optimize_xyz_weight()`:
optimization is skipped when |R-free − R-work| < 0.01. Our gap was 0.0139, so it would engage.

This run reached **R-work 0.0931 / R-free 0.1068** at macrocycle 4 and then **died mid-cycle
with no output PDB and no traceback**. I diagnosed rather than assumed: `memory_pressure`
showed 72 % free and the jetsam log showed no kill of this process, so it was **not** OOM —
the background (`nohup`) job was reaped. A concurrent PHENIX job belonging to a different
agent was visible in `ps`, but it was not the cause. Because the run produced no file, its
result was unusable; `r3_001.pdb` remained my best surviving model.

**Corrective action:** run the remaining refinements in the **foreground** so they cannot be
reaped, and disable the 10.8 MB `.geo` output to cut I/O.

## Step 7 — refinement 5: weight-optimized polish (foreground)

Same settings as step 6 but 3 macrocycles, foreground, `write_geo_file=False`.

**Result: R-work 0.0931 / R-free 0.1075.** Independently re-measured with
`phenix.model_vs_data`: **0.0932 / 0.1075** — agrees with phenix.refine's self-report, so the
number is not an artifact of the refinement program grading itself. Bond RMSD rose to the
expected 0.0087 Å. Geometry essentially unchanged (MolProbity 1.36, clashscore 6.40).

Against r3 this trades a hair of geometry for a clearly better R-free (0.1138 → 0.1075) on the
*free* set, so r5 superseded r3.

## Step 8 — refinement 6: final continuation

Gains had not yet vanished (last run improved R-free by 0.0063), so I spent the final slot on a
3-macrocycle continuation with the same settings.

**Result: R-work 0.0917 / R-free 0.1060**, independently confirmed by `phenix.model_vs_data` at
**0.0918 / 0.1060**.

This model is better than r5 on *every* axis measured, so the choice needed no trade-off:

| metric | r5 | **r6 (final)** |
|---|---|---|
| R-work / R-free | 0.0932 / 0.1075 | **0.0918 / 0.1060** |
| Clashscore | 6.40 | **5.22** |
| Rotamer outliers | 0.90 % | **0.45 %** |
| MolProbity score | 1.36 | **1.28** |

The R-free improvement had shrunk to 0.0015, i.e. marginal gains were genuinely flattening, so
stopping was the right call independent of the budget being exhausted.

## Final model — independently verified

`final.pdb`: 4863 atoms, 646 waters, 2720 anisotropic non-H atoms, CRYST1 preserved.

| metric | perturbed input | **final** |
|---|---|---|
| R-work | 0.3915 | **0.0917** |
| R-free | 0.3908 | **0.1060** |
| R-free − R-work gap | −0.0007 | 0.0143 (healthy) |
| Ramachandran outliers | 0.40 % | **0.00 %** |
| Ramachandran favored | 95.55 % | **97.98 %** |
| Rotamer outliers | 3.60 % | **0.45 %** |
| Clashscore | 8.54 | **5.22** |
| MolProbity score | — | **1.28** |
| Bond RMSD | 0.006 Å | 0.0087 Å |
| Angle RMSD | 1.15° | 1.16° |
| Protein real-space CC | ~0.82 | **0.925** (0 residues < 0.80) |
| Water real-space CC | 0.53 | **0.912** |
| Waters | 419 | 646 |
| Outer shell (0.96–0.82 Å) R-work | 0.456 | **0.142** |

Cross-tool checks, per this harness's trust model (never PHENIX grading PHENIX unchallenged):

- R-factors re-measured by `phenix.model_vs_data` independently of `phenix.refine`, agreeing to
  within 0.0001.
- Geometry graded by **MolProbity**, not by the refinement program's own restraint residuals.
- Fit-to-density corroborated by `real_space_correlation`, an orthogonal real-space measure.
- **gemmi** (independent, non-PHENIX toolchain) parses `final.pdb` cleanly and round-trips it
  PDB → mmCIF → PDB without error.

## Compliance

No network access of any kind was used. No deposited coordinates were retrieved. Nothing in the
repository's `ref/` or `data/` trees was read, and no `*_mask.json`, `*_validation.xml`, or any
file under `/tmp/nc_round1_cache/` other than `2vxn.mtz` was opened. Every shell command is
recorded verbatim and in order in `transcript.md`.
