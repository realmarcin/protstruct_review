# 7R2H blinded agentic recovery — decisions log

Scratch dir: `/tmp/agent_r5_7r2h/`
Inputs: `/tmp/nc_round1_work/r4p_7r2h.pdb` (perturbed model), `/tmp/nc_round1_cache/7r2h.mtz` (data)
Final model: `final.pdb` (= `/tmp/agent_r5_7r2h/r6_001.pdb`)

Refinement-program invocations used: **6 of 6** (runs 1, 2, 3, 4, 5, 6; run 4 was
killed mid-execution and produced no model, but it is counted against the budget).

---

## Step 0 — Characterise the inputs (no refinement budget spent)

**Data.** `gemmi mtz` on the MTZ: P4(1)2(1)2, cell 57.348 57.348 87.562 90 90 90,
159 899 reflections, resolution 47.97–0.789 Å. Columns present: `FOBS/SIGFOBS`
(amplitudes), `R-free-flags` (0/1), `R-free-flags-1` (0–19 CCP4-style bins), plus
`FWT/PHWT` and `DELFWT/PHDELWT` map coefficients carried over from the original
deposition.

I used `FOBS,SIGFOBS` as the amplitude pair and `R-free-flags` as the free-flag
column. I checked the flag convention rather than assuming it: a direct count gave
8080 reflections with value 0 and 151 819 with value 1, i.e. **the test set is
flag value 0** at 5.05%. `phenix.model_vs_data` independently auto-detected the
same thing ("flag value: 0", Nfree summing to 7538 of 149 186 after filtering).
I passed `test_flag_value=0` explicitly to every refinement run so the working/test
split could not silently invert between runs.

*Conclusion: this is a true atomic-resolution (0.79 Å) data set. That single fact
drove every subsequent decision — at sub-Ångström resolution the data, not the
restraint library, should determine the geometry.*

**Model.** `gemmi contents`: single chain A, 164 residues, 334 waters, 1578 non-H
atoms, 1253 H atoms present, anisotropic ADPs (1258 ANISOU records — macromolecule
anisotropic, waters isotropic). Two residues carry alternate conformations
(ILE 117 A/B, HIS 131 A/B at 0.66/0.34).

---

## Step 1 — Diagnose *what kind* of damage this is

This mattered more than anything else, because the right repair strategy for
"coordinates nudged" is completely different from "chemistry destroyed".

Baseline `phenix.model_vs_data`: **R-work 0.4327, R-free 0.4417.** Badly broken.

But the geometry was *not* broken:

| Metric | Perturbed input |
|---|---|
| Bond RMSD | 0.010 Å |
| Angle RMSD | 1.02° |
| Clashscore | 7.61 |
| Ramachandran outliers | 2.47% (87.04% favored) |
| Rotamer outliers | 0.00% |
| Cβ deviations | 0.00% |

An atom-by-atom random shake large enough to drive R to 0.43 would have shredded
bond lengths and thrown up rotamer outliers. Instead bonds and angles are at
*restrained-refinement* quality and every side chain is still sitting in a rotamer
well. The R-vs-resolution breakdown reinforced this: R rose smoothly with
resolution (0.26 in the 36–9.8 Å shell, 0.48 by 1.0 Å), which is the signature of
a coordinate/ADP error smeared over the whole model, not of a misplaced molecule.
Low-resolution R was mediocre but not catastrophic, so there was no large
rigid-body offset to chase.

*Conclusion: this is a shake-then-regularise style perturbation — atoms displaced
by a few tenths of an Ångström with local chemistry subsequently restored. Plain
gradient refinement has ample radius of convergence for that at 0.79 Å. I decided
**not** to spend budget on rigid-body refinement or simulated annealing, and to bet
the first run on straightforward restrained refinement.*

## Step 1b — One free repair before refining: hydrogen occupancies

The 1253 hydrogens had occupancies scattered essentially uniformly across 0.00–1.00
(197 of them at exactly 0.00) while their parent heavy atoms sat at 1.00. That is
not a physically meaningful state for riding hydrogens and not something a
deposition would contain. I reset every H occupancy to the occupancy of its own
residue+altloc parent group (`gemmi` via Python; 786 atoms changed) — so ILE 117
altloc A hydrogens went to 0.00, HIS 131 A/B to 0.66/0.34, everything else to 1.00.

Measured effect: R-work 0.4327→0.4332, R-free 0.4417→0.4408. **Essentially
R-neutral.** I kept the fix anyway because it is physically correct and costs
nothing, but I explicitly noted that the H occupancies were *not* the real damage —
which told me the damage was in the coordinates, and stopped me from wasting a
refinement run chasing hydrogens.

---

## Step 2 — Refinement run 1: does plain restrained refinement recover it?

`phenix.refine` from the H-corrected model, 8 macro-cycles, default weights,
`ordered_solvent` off, riding H, existing aniso/iso ADP assignment retained.
Deliberately no solvent rebuilding yet: with coordinates still 0.4 R-factor away
from correct, a solvent picker would have been fitting waters into a wrong map and
could have deleted genuine ones.

**Result: R-work 0.4332 → 0.1473, R-free 0.4410 → 0.1585.** Hypothesis confirmed.
Converged cleanly (R-free over the last three macro-cycles: 0.1589, 0.1588, 0.1584).

Geometry after run 1 was excellent: clashscore 0.40, **0.00% Ramachandran
outliers** (96.91% favored, up from 87.04%), 0.00% rotamer outliers, bond RMSD
0.005 Å.

*Conclusion: the model was recovered. Everything from here is refinement quality,
not rescue.*

## Step 2b — Where is the remaining signal? (free measurement)

Rather than guess at the next move, I looked at the residual density with an
independent tool. `gemmi blobs` on the run-1 mFo−DFc map (`FOFCWT/PHFOFCWT`,
3σ, relaxed volume/score cutoffs appropriate for partial waters) found **9
unmodelled blobs**, the strongest 5.1 electrons in 3.1 Å³ peaking at 27.9σ near
ASN 108. Those are missing solvent, not missing protein.

*Note: the `--mask-water` option advertised in this gemmi build's help text is not
actually implemented ("Invalid option"); I dropped it. Since the search is run on a
difference map, well-fitted existing waters produce no residual peak anyway, so the
result stands.*

*Conclusion: spend the next run on ordered solvent.*

---

## Step 3 — Refinement run 2: ordered-solvent rebuild

`main.ordered_solvent=True`, 6 macro-cycles, from run 1's model. Phenix defaults
(3σ primary map cutoff, CC and map-value filters, B range 1–80, 1.8–3.2 Å distance
window) were left alone — they are appropriate at this resolution.

Waters grew 335 → 460 during refinement; the terminal filter pruned them to 376.

**Result: R-work 0.1409, R-free 0.1513** (from 0.1473/0.1585). A 0.7% R-free gain —
the largest single improvement after the initial recovery.

Verified with `gemmi blobs` on the run-2 map: residual peaks dropped from 9 blobs
(max 5.1 e⁻, 27.9σ) to **3 blobs (max 2.4 e⁻)**. The solvent model was now
essentially complete. Independent `phenix.model_vs_data` on the run-2 model gave
0.1411/0.1513, agreeing with refine's own numbers.

Geometry held: clashscore 1.20 (up from 0.40 purely because of the added waters),
0.00% Rama outliers, 0.00% rotamer outliers.

---

## Step 4 — Refinement run 3: are anisotropic waters justified? (a test I let fail)

At 0.79 Å, anisotropic ADPs for solvent are common practice, and the 376 waters
were still isotropic. Parameter budget looked affordable (≈1880 extra parameters
against 141 647 working reflections). I converted **all** non-H atoms to
anisotropic (`refine.adp.individual.anisotropic="not (element H or element D)"`)
and refined 6 macro-cycles with the solvent set frozen, so the effect would be
cleanly attributable.

Conversion verified: ANISOU records 1258 → 1638, including all 376 waters.

**Result: R-work 0.1403 (−0.0006), R-free 0.1516 (+0.0003).**

*Conclusion: rejected.* R-work fell fractionally while R-free rose fractionally —
the textbook signature of parameters that buy nothing once cross-validated. 1880
extra parameters for zero cross-validated gain is not a better model, it is a
better-decorated one. **I discarded run 3 and continued from run 2's isotropic-water
model.* Common practice at this resolution is not the same as justified on this
data set, and R-free is the arbiter.

---

## Step 5 — Refinement run 4: weight optimisation (killed, but informative)

Bond RMSD of 0.005 Å is *tight* for 0.79 Å data. At atomic resolution the
observations should be allowed to pull harder against the restraint library than
this; a value that low suggested the X-ray term was under-weighted and the
geometry library was doing work the data should be doing. I enabled
`optimize_xyz_weight` and `optimize_adp_weight` with `ordered_solvent=True`,
3 macro-cycles — one run that searches many weights internally, rather than
several runs each testing one weight by hand.

**The process was killed mid-ADP-refinement** (two sibling agents were running
concurrent phenix jobs on the same machine; no traceback, no output model). It
counts against the budget. But its log preserved the answer I wanted:

```
 R-FACTORS             RMSD           CLASH  RAMA  ROTA CBET WEIGHT
 work   free   delta   bonds   angl
 0.1476 0.1585 0.0109  0.003   0.7    0.4   0.0   0.0    0   0.090
 0.1408 0.1530 0.0121  0.005   0.9    0.4   0.0   0.0    0   0.814
 0.1407 0.1529 0.0122  0.005   0.9    0.4   0.0   0.0    0   0.905  <- phenix default
 0.1401 0.1528 0.0127  0.006   1.0    0.4   0.0   0.0    0   1.628  <- selected
 0.1401 0.1529 0.0128  0.007   1.0    0.4   0.0   0.0    0   1.900
```

Two things came out of this, and the second was worth more than the first:

1. The optimiser did prefer a looser weight (1.628 vs the default 0.905, i.e.
   `wxc_scale` ≈ 0.9 rather than 0.5) — but the R-free difference between default
   and optimum was **0.0001**. Weight optimisation was *not* the win I had
   hypothesised.
2. The run nonetheless reached 0.1364/0.1493 by its third macro-cycle. Since the
   weight itself explained almost none of that, the gain had to be coming from the
   *second* pass of ordered-solvent picking on an already-converged model (plus the
   shake-and-reminimise the optimiser performs as a side effect).

*Conclusion: with 2 runs left, buy the second solvent pass — which demonstrably
helps — and not the weight search, which costs ~3× the runtime for 0.0001 R-free.
Carry the optimiser's preferred `wxc_scale=0.9` forward since it is free to apply
and is the data-driven choice at this resolution.*

## Step 5b — A launch that did not consume budget

I attempted to detach run 5 with `setsid`, which does not exist on macOS. The
shell created the redirect target (`r5.log`, 58 bytes: "setsid: command not
found") but **no phenix process ever started** — confirmed by `ps`/`lsof`, which
showed the only two live `phenix_refine` processes had working directories
`/tmp/agent_r5_2vxn/r6` and `/tmp/agent_r5_4m7g`, i.e. both belonged to sibling
agents. That failed launch is in the transcript but is not counted as an
invocation, because no refinement program ran. I switched to foreground execution
for the remaining runs.

---

## Step 6 — Refinement run 5: second solvent pass

From run 2's model: `ordered_solvent=True`, 8 macro-cycles, `wxc_scale=0.9`.

Waters 376 → 470 during refinement; **R reached 0.1377 / 0.1501** at macro-cycle 7.
Then the terminal solvent filter pruned 470 → 388 and R rebounded to
**0.1401 / 0.1513**.

This exposed a consistent pattern. In both solvent-updating runs the final filter
removed ~80 waters and cost ~0.001 R-free (run 2: 0.1506→0.1513; run 5:
0.1503→0.1513). Run 1, with `ordered_solvent` off, showed no such end-step penalty
at all (0.1584 → 0.1585).

I considered relaxing phenix's water-quality filters to retain those ~80 waters and
bank the 0.001. **I decided against it.** R-free saying those waters help by 0.001
is not a strong enough mandate to override density-support criteria and ship
80 marginally-supported waters; that is R-factor cosmetics, and a model padded with
waters that fail CC and map-value tests is a worse structure even when it prints a
prettier number. I kept phenix's filtered water set.

---

## Step 7 — Refinement run 6 (final): polish without the filter penalty

The pattern above implied a clean, honest way to recover the end-step loss: take
the *already-filtered* 388-water model and refine it with `ordered_solvent=False`.
No waters are added, none are removed, and there is no terminal filter to undo the
convergence — the model simply finishes converging at the water set phenix's own
criteria had already endorsed.

From run 5's model: 6 macro-cycles, `ordered_solvent=False`, `wxc_scale=0.9`.

**Result: R-work 0.1393, R-free 0.1511**, 388 waters, no end-step rebound
(macro-cycle 6 = end = 0.1393/0.1511). Best of every candidate on both R-work and
R-free. This is `final.pdb`.

---

## Final model — independent verification

Every number below was re-measured from the final coordinates with a tool other
than the one that produced them.

| Metric | Perturbed input | **final.pdb** |
|---|---|---|
| R-work (`phenix.refine`) | — | 0.1393 |
| R-free (`phenix.refine`) | — | 0.1511 |
| R-work (`phenix.model_vs_data`, independent) | 0.4327 | **0.1394** |
| R-free (`phenix.model_vs_data`, independent) | 0.4417 | **0.1512** |
| Clashscore | 7.61 | 1.60 |
| Ramachandran outliers | 2.47% | **0.00%** |
| Ramachandran favored | 87.04% | 96.91% |
| Rotamer outliers | 0.00% | **0.00%** |
| Cβ deviations | 0.00% | 0.00% |
| Bond RMSD | 0.010 Å | 0.006 Å |
| Angle RMSD | 1.02° | 0.98° |
| Waters | 334 | 388 |
| Residual mFo−DFc blobs >3σ (`gemmi`) | — | 2 (max 3.1 e⁻) |

`phenix.refine` and `phenix.model_vs_data` agree to 0.0001 on both R-work and
R-free, from independent scaling and bulk-solvent treatments. The residual
difference map is essentially flat: two blobs of 3.1 and 2.3 electrons, down from
nine blobs peaking at 27.9σ after the first refinement.

## What I would do with more budget

- **Alternate conformations.** The model carries altlocs at only 2 of 164 residues.
  A genuine 0.79 Å structure almost certainly supports many more. Building them is
  the largest remaining source of R-free, and the two surviving difference blobs
  (near CYS 161 and ARG 151) look like exactly that. I did not attempt it because
  it needs iterative build-and-refine cycles well beyond a 6-run budget, and a
  half-built alt-conf set is worse than none.
- **Individual (non-riding) hydrogen refinement**, which sub-Ångström data can in
  principle support.
- Re-testing anisotropic solvent *after* alt-confs are in — the parameters might
  earn their keep against a more complete model even though they did not here.

## Honest notes / caveats

- Run 4 died and produced no model. I counted it against the 6-run budget rather
  than treating it as a free retry.
- The `setsid` launch failure produced a log file but ran no refinement program;
  I verified via `ps`/`lsof` that no process started before deciding not to count it.
- Run 3 (anisotropic waters) is a deliberate negative result that I discarded.
  Runs 1, 2, 5, 6 form the chain leading to `final.pdb`.
- No deposited coordinates were retrieved and no network access of any kind was
  made. The only file read from `/tmp/nc_round1_cache/` was `7r2h.mtz`. Nothing in
  the repository's `ref/` or `data/` trees was read.
- Self-measured numbers above are advisory; the benchmark re-measures independently.
