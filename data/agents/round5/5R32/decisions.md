# 5R32 blinded agentic recovery — decisions

Subject: `/tmp/nc_round1_work/r4p_5r32.pdb` (perturbed) + `/tmp/nc_round1_cache/5r32.mtz`
Scratch: `/tmp/agent_r5_5r32/`
Final model: `final.pdb` (derived from `run6_001.pdb`, see step 9)

## Headline

| | R-work | R-free | MolProbity | Clashscore | RMS bonds | RMS angles | waters |
|---|---|---|---|---|---|---|---|
| start (perturbed) | 0.3986 | 0.3965 | 1.95 | 7.50 | 0.0097 | 1.21 | 358 |
| **final** | **0.1100** | **0.1278** | **0.50** | **0.00** | **0.0061** | **0.93** | 1053 |

Ramachandran outliers 0.00% (99.09% favored), rotamer outliers 0.00%, C-beta deviations 0.

Refinement-program invocations used: **6 of 6** (plus one launch that was rejected before
refinement started — annotated in step 8, not counted).

## Step 0 — Data and free-set identification (no refinement budget spent)

`gemmi mtz --dump` reports P2₁, cell 45.235 72.828 52.602 90 109.338 90, 0.90–49.6 Å,
237444 rows, wavelength 0.827 Å. Amplitudes are `FOBS,SIGFOBS` (201473 observed).

The file carries **four** flag columns (`R-free-flags`, `-1`, `-2`, `-3`) whose zero-counts
differ wildly over all rows (2494 vs 38087). That looked like an ambiguity worth resolving
before it could silently corrupt every R-free I would quote. Restricting to reflections
that actually have FOBS, **all four columns agree exactly**: 2116 free reflections, flag
value 0, 1.05% of observed data. The discrepancies live entirely in unobserved rows. So the
test set is unambiguous, and I pinned it explicitly with
`xray_data.r_free_flags.test_flag_value=0` in every run rather than relying on
auto-detection.

A 1.05% test set is small; σ(R-free) ≈ 0.13/√2116 ≈ 0.003. I used that as my significance
yardstick throughout and refused to treat sub-0.005 differences as real.

**Deliberate self-restriction.** The MTZ also contains `FWT/PHWT` and `DELFWT/PHDELWT` —
map coefficients computed from the *deposited* model. Reading the MTZ is permitted, but
those columns are effectively the answer key in phase form; rebuilding against them would
be retrieval of deposited coordinates by another route. I used only `FOBS`, `SIGFOBS` and
the free flags, and every map I looked at was computed from my own model's phases.

## Step 1 — Diagnosing the perturbation (no refinement budget spent)

Baseline `phenix.model_vs_data`: R-work 0.3986 / R-free 0.3965. Baseline MolProbity:
clashscore 7.50, RMS bonds 0.0097, angles 1.21, Rama outliers 0.91%, **rotamer outliers
0.00%**.

Composition: 5161 atoms in one chain (330 protein residues + 358 waters), 2820 ANISOU
records, 436 atoms in A/B alternate conformations.

I first misread the ANISOU coverage. 2820 ANISOU against 5161 atoms, with main chain and CB
100% anisotropic and ~75% of "side-chain" atoms isotropic, looked like a fingerprint of
side chains having been snapped to idealized rotamers — which would have fit the 0.00%
rotamer-outlier reading. Breaking the count down **by atom name** killed that hypothesis:
every isotropic atom is a hydrogen. All 2820 heavy atoms are anisotropic and the model
already carries 2341 riding H.

Corrected diagnosis: geometry is intact and ADPs are original; the damage is **coordinates
only**. R rises with resolution (0.28 at low angle → 0.47 at 1.3–1.7 Å), the signature of
coordinate error rather than a scaling or B-factor problem. That argued for straightforward
gradient refinement at 0.9 Å rather than simulated annealing or rigid-body work.

## Step 2 — Refinement 1: recover the coordinates

`phenix.refine`, 8 macrocycles, xyz + individual ADP + occupancies, anisotropic for
`not element H`, ordered solvent left at `mode=second_half` with `filter_at_start=False`
so the 358 original (untouched, anisotropic) waters would not be culled against a map
computed from an R=0.40 model.

Result: **0.1253 / 0.1379**, MolProbity 0.58, clashscore 0.21, bonds 0.0057, waters 497.
The bulk of the recovery happened here — 0.399 → 0.125 — and it converged smoothly
(0.216 → 0.154 → 0.143 → 0.131 across macrocycles).

## Step 3 — What is left (no refinement budget spent)

`phenix.find_peaks_holes` on run 1: 104 mFo-DFc peaks > 3.5σ, max 11.3σ.

Before assuming these were solvent, I checked for a ligand: 5R32-style entries can carry a
bound fragment, and a fragment would appear as a contiguous blob. Single-linkage clustering
of the 61 peaks above 4.5σ gave a **maximum cluster size of 2** — no ligand-sized feature.
The strongest peak (11.3σ) sits 2.67 Å from one water and 4.1 Å from the nearest protein
atom: a solvent site. So the residual is solvent plus alternate conformations, and no
ligand building was warranted (which also keeps me safely inside "repair the model").

Also noted: only 286 of 497 waters were anisotropic — the ones PHENIX added mid-run default
to isotropic.

## Step 4 — Refinement 2: crashed (counted against budget)

Same as run 1 plus `ordered_solvent.mode=every_macro_cycle`, `include_altlocs=True`,
`new_solvent=anisotropic`. It died inside the ordered-solvent update with
`CCTBX_ASSERT(f.use_u_iso()) failure` — `new_solvent=anisotropic` is incompatible with the
water-refinement path, which assumes u_iso.

**I counted this against the 6-run budget.** The rule exempts launches that fail "before
refinement starts (shell failure, parameter rejection)". This was neither: it got through
NQH flips, reached r_work 0.1266, added 412 waters and refined their occupancies to
0.1202/0.1328 before dying. It modified the model, so it counts.

It also paid for itself as an experiment: going 497 → 909 waters moved R-free from 0.1383
to 0.1272.

## Step 5 — Refinement 3: aggressive solvent, and the filter problem

Identical minus `new_solvent=anisotropic`. Final: **0.1215 / 0.1357**, 746 waters.

Watching the per-step trace inside the solvent update exposed the real obstacle:

```
909 waters, refined  -> r_work=0.1160 r_free=0.1272
filter               ->  806 waters  0.1176 / 0.1300
CC filter            ->  707 waters  0.1238 / 0.1393
```

PHENIX's map-CC filter (`poor_cc_threshold=0.70`, `poor_map_value_threshold=1.0`) was
discarding waters that the **free set** says are real — R-free degraded by 0.012 (≈4σ) as
they were removed. At 0.9 Å a large partial-occupancy solvent shell is expected, and the
default thresholds are tuned for lower resolution.

## Step 6 — Refinement 4: relaxed filter + weight optimization → the fit/geometry trade

From run 3, with all waters anisotropic (the `not element H` selection is applied to the
input model, so run 3's 746 waters were promoted), relaxed filters (cc 0.60, map value
0.8), `ignore_final_filtering_step=True`, and `optimize_xyz_weight` +
`optimize_adp_weight`.

Result: **0.1103 / 0.1300** — the best fit so far — but geometry paid for it:

| | run 1 | run 4 |
|---|---|---|
| RMS bonds | 0.0057 | **0.0142** |
| RMS angles | 0.91 | 1.29 |
| Clashscore | 0.21 | **2.91** |
| MolProbity | 0.58 | 1.08 |
| C-beta dev | 0 | 1 |
| waters | 497 | 1034 (3.13/residue) |

This is exactly the trade the task warns about, so I refused to accept it on the R-free
number alone and asked *where* the damage was. `phenix.clashscore verbose=True` gave an
unusually clean answer: **all 14 bad clashes involve a water**, and they cluster on
HIS 164 CE1/NE2, LYS 243 CD, ASP 146 CB/CG, LYS 110 CD, TYR 79. PHENIX was papering over
unmodeled **alternate side-chain conformations** by dropping partial-occupancy waters into
them. The bond-length loosening, separately, came from weight optimization pushing the
X-ray weight up.

Two independent defects, two separate fixes.

## Step 7 — Refinement 5: back off the weights, prune the impossible waters

Water pruning, first attempt: I flagged waters within 2.20 Å of any protein heavy atom and
found only 2. That cutoff was wrong — probe calls a clash at ≥0.4 Å vdW overlap, which for
water-O against carbon (1.52 + 1.75 = 3.27 Å) is a *distance of 2.87 Å*, not 2.2 Å. A water
2.5 Å from a CH₂ carbon is a clash even though 2.5 Å is a perfectly good H-bond to N/O.
Redoing it element-aware (O···C,S < 3.00 Å; O···N,O < 2.40 Å; altloc-aware so A never
"clashes" with B) flagged 34 waters, every one at occupancy 0.21–0.77 and every one wedged
against a side-chain carbon.

Refinement 5: pruned model, **default automatic weighting** (no weight optimization),
`ordered_solvent=False` so the destructive filter could not run.

Result: **0.1096 / 0.1323**, MolProbity 0.50, **clashscore 0.00**, bonds 0.0058, angles
0.93, 0 C-beta deviations. Against run 4: R-work marginally better, R-free 0.0023 worse
(0.6σ — noise), and geometry decisively better. Run 5 dominated run 4.

## Step 8 — Reading the residual honestly (no refinement budget spent)

Peak search on run 5: 48 peaks > 3.5σ (down from 104) but with strong survivors, and they
split cleanly into two kinds:

- **Genuine solvent sites I had over-pruned.** The 25.7σ peak sits 2.54 Å from NZ of
  B-LYS 311, 2.77 Å from O of ASP 14 and 3.47 Å from O of THR 223 — textbook H-bond
  coordination. The 16.6σ peak is 2.7–2.9 Å from three backbone atoms. My 3.00 Å O···C
  cutoff was stricter than probe's own 2.87 Å, so I had deleted ~15 legitimate waters.
- **Alternate conformations.** The 10.3σ peak lies 2.01 Å from ASP 146's own CG, 2.31 Å
  from its CB and 2.35 Å from its OD1 — *inside* the side chain, where no water can go.
  Same pattern for TYR 79 (2.43 Å from CE2, 1.84 Å from CD1).

Systematically: 9 residues carry a peak closer than 2.87 Å to their own side-chain carbon —
ASP 146, TYR 79, HIS 164, LEU 128, THR 143, GLN 140, ILE 77, LYS 149, SER 84.

I wrote a χ1/χ2 scan that rotates a duplicated side chain and scores it by how well it
covers the local peaks, penalized for clashes. **It only worked for one residue.** ASP 146
scored 9.2 against its 10.3σ peak; TYR 79, HIS 164, LEU 128, THR 143, GLN 140 and SER 84
all scored ≈ 0 — the optimizer found no rotation that explains their density and instead
swung the side chain somewhere arbitrary. Shipping seven speculative conformers that my own
scoring function rates as explaining nothing would be fabrication dressed as modeling, so I
kept **ASP 146 only** and left the rest as declared residual.

**Rejected launch (not counted against budget).** My first run-6 launch died with
`Sorry: An atomic model is required` — my hand-edited PDB had duplicate atom serials and
ANISOU records separated from their parent ATOM lines. This failed at file parsing, before
any refinement, so per the rules it does not count. I rebuilt the split through the
`iotbx.pdb` hierarchy instead of text surgery, which also let me do it properly: shared
backbone at full occupancy, side chain split A/B at 0.50.

## Step 9 — Refinement 6: final

From run 5 + the ASP 146 alternate conformer: default automatic weighting, ordered solvent
back on (`every_macro_cycle`, `include_altlocs=True`) at PHENIX's **strict default**
CC thresholds — to re-place the waters I had over-pruned via density rather than by hand —
but with `ignore_final_filtering_step=True` to suppress the terminal cull that cost run 3
its gains.

Result: **0.1100 / 0.1278**, MolProbity 0.76, clashscore 0.83, bonds 0.0061, angles 0.93,
0 Rama / 0 rotamer / 0 C-beta outliers, 1056 waters. ASP 146 refined to a real two-state:
both conformers held at 0.50 with distinct carboxylate positions and comparable B-factors
(17–21 Å²), not one conformer collapsing to zero occupancy.

Four bad clashes remained, all water-against-side-chain at LYS 243, TYR 79, HIS 164 and
SER 84 — the same residues whose alternate conformations I had declined to guess at. I
deleted those three water residues and re-measured with `phenix.model_vs_data`:
R-free 0.1277 → 0.1279 (+0.0002, ~0.07σ) while clashscore went 0.83 → **0.00**. Free, so I
took it. A water 2.5 Å from a lysine CD is simply wrong; deleting it is more honest than
keeping it for a fit contribution that measurably is not there.

That model is `final.pdb`.

## Verification

`final.pdb` re-measured independently with `phenix.model_vs_data` (recomputes its own bulk
solvent and scaling, so it is not just echoing the refinement log): **r_work 0.1105,
r_free 0.1279** — agrees with the refinement-reported 0.1100/0.1278. For comparison under
the identical protocol, run 5 gives 0.1100/0.1320.

## What I did not do, and what is still wrong

- **7–8 unmodeled alternate side-chain conformations** (TYR 79, HIS 164, LEU 128, THR 143,
  GLN 140, ILE 77, SER 84, and a third state at LYS 149). These are the largest identified
  remaining defect. My automated χ-scan could not place them credibly and I had no
  refinement budget left to iterate; a Coot session or qFit would likely take R-free below
  0.125 and is the obvious next step.
- **The 25.7σ peak near LYS 311** is now modeled as water. Its coordination — 2.54 Å from a
  lysine ammonium NZ, 2.77 Å and 3.47 Å from two backbone carbonyls — plus a peak height
  well above what an oxygen accounts for, is suggestive of a bound anion (chloride). I did
  not model it as an ion: identifying it would require the crystallization conditions, which
  I cannot obtain without network access, and a wrongly-assigned ion is a worse error than a
  slightly under-modeled water.
- **1053 waters (3.2/residue) is a large solvent model.** I am reporting it plainly rather
  than trimming to look conventional. It is justified by R-free, not by R-work: the free
  set improved by ~0.012 as this shell was built, and R-free is computed on reflections
  never used in refinement. The R-work/R-free gap did widen from 0.013 (run 1) to 0.018
  (final), which is the honest cost of the extra parameters.
- **No simulated annealing, no rigid-body, no TLS.** The perturbation was pure coordinate
  error well inside the convergence radius of gradient refinement at 0.9 Å; run 1 confirmed
  that empirically, so spending budget on SA would have been waste.
