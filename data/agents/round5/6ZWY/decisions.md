# 6ZWY blinded agentic recovery — decision log

Scratch dir: `/tmp/agent_r5_6zwy/`. Inputs: perturbed model
`/tmp/nc_round1_work/r4p_6zwy.pdb`, data `/tmp/nc_round1_cache/6zwy.mtz`.
Refinement budget used: **5 of 6** invocations (one rejected, see step 7).

---

## A self-imposed restriction beyond the stated rules

The supplied MTZ contains, in addition to the observations, four columns that are
**computed from the deposited model**: `FC`, `PHIFC`, `FWT`, `PHWT`, `DELFWT`,
`PHDELWT`, `FOM`. Phases derived from the deposited coordinates are, for practical
purposes, the answer this benchmark is blinding me from — refining or rebuilding
against `FWT/PHWT` would be equivalent to reading the deposited structure.

I therefore used **only `FOBS`, `SIGFOBS` and `R-free-flags`** and let every phase in
this work come from my own model. Every difference map I inspected was computed by
PHENIX from the model I had at that moment. This is stricter than rule 1 requires; I
believe it is the honest reading of the benchmark's intent, and I am recording it so
the audit can confirm it against the transcript.

## Step 1 — Read the data before touching the model

`gemmi mtz --dump` / `-s` and a short numpy pass over the reflection arrays.

**Measured.** C222₁, cell 77.39 × 116.57 × 61.97, 146 396 observations spanning
19.67–**1.00 Å** at 97.3 % completeness. The MTZ's HKL grid extends to 0.83 Å but is
empty below 1.00 Å, so the true limit is 1.00 Å, not the 0.833 Å the header suggests.

Two amplitude pairs and four free-flag columns were present, so I had to choose:

- `FOBS-1` = `FOBS` × 1.421 (ratio std 0.044) — the same data on a different scale.
  I took **`FOBS,SIGFOBS`**, the pair the deposited `FC` was computed against.
- `R-free-flags` and `R-free-flags-2` are bitwise identical; `R-free-flags-1` and
  `-3` are the CCP4-style 0–20 binned forms whose bin 0 contains exactly the same
  7188 reflections. So all four encode one test set. I took **`R-free-flags` with
  `test_flag_value=0`** (4.9 % of data). PHENIX independently auto-detected flag
  value 0, which confirms the reading.

**Concluded.** Atomic-resolution data. That governs everything downstream: anisotropic
ADPs are affordable, riding hydrogens are standard, and the radius of convergence of
gradient refinement is large enough that a sub-ångström perturbation should be
recoverable without simulated annealing.

## Step 2 — Diagnose what was actually damaged

`phenix.model_vs_data` + `phenix.molprobity` on the untouched input.

**Measured.** R-work **0.3538** / R-free **0.3676**. But the geometry was *clean*:
RMS(bonds) 0.0084 Å, RMS(angles) 1.16°, clashscore 8.13, Ramachandran outliers 0.40 %,
rotamer outliers 1.27 %, MolProbity 1.97. All 2547 atoms carried ANISOU, and the ANISOU
traces agreed with the B_iso column to within 0.005 Å² — the ADPs were internally
self-consistent, not scrambled. All residues were complete (my first missing-atom script
said 43 residues were short; that was my own off-by-one for ALA and SER, corrected and
re-run — nothing is missing). Chain A runs 223–479 with no breaks, plus U5P, two GOL, a
free PRO, a CSS at 304, and 307 water sites, with A/B alternates throughout.

R rose monotonically with resolution (0.19 at 10 Å → 0.47 in the outer shell).

**Concluded.** This is *not* a geometry scramble and *not* a rigid-body displacement — a
rigid-body error would damage low resolution too, and a coordinate scramble would have
wrecked the bond lengths. A monotonic falloff under intact local geometry is the
signature of **random positional error applied and then regularised**, i.e. atoms moved
a few tenths of an ångström while restraints kept the bonds ideal. Side chains sitting
in *valid but wrong* rotamers (only 1.27 % outliers) fits the same picture.

**Therefore:** no simulated annealing, no rebuilding from scratch. Straightforward
gradient refinement should recover this, provided the per-macro-cycle local real-space
step is active to pull mis-rotamered side chains back. I also decided against spending a
run on rigid-body refinement, since the diagnosis says there is no rigid-body error to
find.

## Step 3 — Model preparation (not a refinement invocation)

`phenix.ready_set add_h_to_water=False` → 2312 riding hydrogens on 2547 non-H atoms.
U5P, GOL, PRO and CSS were all matched to the PHENIX monomer library, so no custom
restraint CIF was needed.

At 1.0 Å, hydrogens are standard practice and materially affect both R and clashscore,
so **final.pdb retains them** (riding, refined throughout).

## Step 4 — Free validation before paid runs

Per the canary principle, every phenix.refine command was first run with `--dry-run`,
which validates arguments without executing refinement. This caught nothing serious but
cost nothing, and confirmed the data selectors resolved to `FOBS,SIGFOBS` and
`R-free-flags` rather than silently picking `FOBS-1`. These dry runs are annotated
**[NOT COUNTED]** in the transcript because the refinement program never executed.

## Step 5 — [REFINE 1/6] Coordinate and ADP recovery

xyz + local real-space + individual (anisotropic) ADP + occupancies, 5 macro-cycles, no
solvent update. Solvent was deliberately held fixed: rebuilding waters against a
difference map dominated by model error would build noise.

**Measured.** 0.3538/0.3676 → **0.1248/0.1426**. ML coordinate error 0.23 → 0.09 Å.
Cumulative atomic shift 0.348 Å, which retro-fits the perturbation magnitude inferred in
step 2. Waters untouched at 307.

**Concluded.** The diagnosis held; the bulk of the damage was positional and it is gone.
A peak search on the result showed **172 positive peaks > 3σ against only 52 negative**,
max 7.9σ, most of them 1.8–2.9 Å from existing waters. That asymmetry is unmodelled
density, predominantly solvent — which is what justified spending the next run on it.

## Step 6 — [REFINE 2/6] Ordered-solvent rebuilding

Same strategy plus `ordered_solvent=True`, `mode=every_macro_cycle_after_first`,
6 macro-cycles.

**Measured.** Waters 307 → 439 → 463 → 477 → 482 → 485; R-free 0.1427 → **0.1350**,
R-work 0.1217. Geometry improved markedly at the same time: clashscore 8.13 → **1.11**,
Ramachandran outliers → **0.00 %**, rotamer outliers → **0.00 %**, MolProbity 1.97 →
**0.82**. Residual peaks fell 172 → 92, max 7.9 → 6.7σ.

**Concluded.** The solvent shell really had been stripped or displaced, and restoring it
was worth a full run. The last two solvent additions returned 0.0001 in R-free, so
solvent building had converged; further water cycles were not worth another invocation.

## Step 7 — [REFINE 3/6] and [REFINE 4/6] Finding the right data/geometry balance

**Run 3** turned on both `optimize_xyz_weight` and `optimize_adp_weight` (4 macro-cycles,
nproc=6). R-free 0.1350 → **0.1293**, but geometry paid: clashscore 1.11 → 3.32,
RMS(bonds) 0.0079 → 0.0105 Å, RMS(angles) 1.09 → 1.23°, rotamer outliers 0 → 0.42 %,
MolProbity 0.82 → 1.12.

Reading the step-by-step table rather than just the endpoint showed *where* that came
from. Comparing the chosen weights against run 2's automatic ones, the XYZ weight was
essentially unchanged (wxc ≈ 1.6 both times) while the **ADP weight rose about fivefold**
(wxu ≈ 21 → ≈ 105) — so the real gain was ADPs being allowed to fit the data. Meanwhile
the final macro-cycle's `4_xyzrec` step bought **0.0003** in R-free while pushing bonds
from 0.009 to 0.011 Å and angles from 1.130 to 1.234°. A bad trade, and an avoidable one.

**Run 4** therefore kept `optimize_adp_weight=True` and turned `optimize_xyz_weight`
back **off**, 3 macro-cycles from run 3's model.

**Measured.** R-work 0.1133 / R-free **0.1292** with RMS(bonds) back to **0.0080 Å**,
RMS(angles) **1.14°**, clashscore **2.66**, rotamer outliers back to **0.00 %**,
MolProbity **1.05**.

**Concluded.** Run 4 **dominates** run 3 — the same R-free (0.1292 vs 0.1293) for
materially better geometry. The hypothesis that the ADP weight carried the gain and the
XYZ weight carried the cost was correct, and separating them was worth the invocation.

## Step 8 — [REFINE 5/6] Bulk-solvent mask optimization — **tried and rejected**

The one visibly weak part of run 4's fit was low resolution: R-work 0.22–0.27 in the
19.7–5.6 Å shells with k_iso 0.60–0.78 (well off 1.0), versus 0.083–0.10 through the
middle shells. Low k_iso at low resolution points at the bulk-solvent mask, so I spent a
run on `optimize_mask=True`.

**Measured.** The low-resolution shell R-work did improve (0.2617 → 0.2446), confirming
the mask diagnosis. But overall R-free went **0.1292 → 0.1308** and R-work stayed flat.

**Concluded.** **Rejected, model discarded.** The mask parameters that suit ~700 low-
resolution reflections are the wrong ones for the other 145 000. I kept run 4. I am
recording this because a rejected experiment is a result: it says the residual low-
resolution misfit is not worth buying at this price, and it is the reason final.pdb comes
from run 4 rather than the last run executed.

## Step 9 — Independent re-measurement and selection

Rather than trust each run's internal `fmodel` state, I re-measured every candidate with
`phenix.model_vs_data`, which rebuilds scaling and bulk solvent from scratch:

| model | R-work | R-free | MolProbity | clashscore | RMS bonds / angles |
|---|---|---|---|---|---|
| r1_001 | 0.1246 | 0.1425 | — | — | — |
| r2_002 | 0.1218 | 0.1350 | 0.82 | 1.11 | 0.0079 / 1.09 |
| r3_003 | 0.1124 | 0.1298 | 1.12 | 3.32 | 0.0105 / 1.23 |
| **r4_004** | **0.1133** | **0.1294** | **1.05** | **2.66** | **0.0080 / 1.14** |
| r5_005 | 0.1134 | 0.1306 | — | — | — |

**Chosen: r4_004 → final.pdb.** Best R-free under independent re-scaling, and its
geometry is sound in absolute terms, not merely relative: zero Ramachandran outliers,
zero rotamer outliers, zero C-beta deviations, all Rama-Z within ±2, bond RMSD 0.0080 Å.

The one honest caveat: r2_002 has a better clashscore (1.11 vs 2.66) and MolProbity
(0.82 vs 1.05). I chose r4_004 anyway because r2_002 is **over-restrained for 1.0 Å
data** — it pays 0.0056 in R-free for tightness the data does not require — and because
I checked what r4_004's clashes actually are. There are exactly **three** bad clashes in
the whole model, all protein-H to water-O, and two of the three waters sit at occupancy
0.30. Partial-occupancy waters clashing with a side chain are physically reasonable
(the water is present when the side chain adopts its alternate), and clashscore does not
weight by occupancy. Deleting them would improve the reported score without improving
the model, so I left them.

## Stopping

R-free across the last three runs went 0.1298 → 0.1294 → 0.1306, and residual peaks
plateaued (92 → 93 above 3σ, no peak above 9σ, no hole below −6σ). Marginal gains had
vanished, so I stopped with one invocation unspent rather than spend it for noise. The
remaining 7 peaks above 6σ are near side chains (LYS332 NZ, ASN427 CB, ILE286 CD1,
ARG245 NH1, ILE454 CD1) and look like unmodelled alternate conformations — real
remaining signal, but building alternates is not something phenix.refine does, and it is
not reachable within this budget.

## Final self-measured numbers (advisory)

Refinement moved non-water atoms an RMS of 0.487 Å from the perturbed input (median
0.224 Å; 10 % beyond 0.5 Å; max 7.07 Å, a side-chain refit).

| | perturbed input | final.pdb |
|---|---|---|
| R-work | 0.3538 | **0.1133** |
| R-free | 0.3676 | **0.1292** (0.1294 re-measured) |
| Clashscore | 8.13 | 2.66 |
| Ramachandran outliers | 0.40 % | 0.00 % |
| Rotamer outliers | 1.27 % | 0.00 % |
| RMS(bonds) / RMS(angles) | 0.0084 / 1.16 | 0.0080 / 1.14 |
| MolProbity score | 1.97 | 1.05 |
| water sites | 307 | 453 |

final.pdb contains 5009 atoms (2697 non-H + 2312 riding H), chain A (protein 223–479,
U5P, 2 × GOL, PRO, CSS) and chain S (PHENIX-added waters), C222₁, cell unchanged.
