# Next tasks

Backlog of substantive work not yet done. Mirrors the open GitHub issues; this file
carries the execution detail. Keep in sync — close a GitHub issue and check the box here.

**Last reconciled: 2026-07-25.** Backlog reflects PR #24 and PR #28. There is no CI in this
repo — `bash scripts/validate.sh` is the gate, and it must exit 0 before a merge.

## Tolerance benchmarks (from the domain-expert `[template]` review) — DONE 2026-07-25, PR #24

Both provisional agreement tolerances have been benchmarked by running the tools on a structured
test set. **No tolerance in `ref/thresholds_and_standards.md` is provisional any more.** Both changed
*shape*, not just magnitude: each is now a relative band with an absolute floor, because in both
cases the disagreement scales with the quantity being measured. The new `[benchmark]` provenance tag
marks a tolerance whose magnitude was **measured in this repo** rather than inferred.

### [x] Benchmark interface BSA: biotite SASA vs PISA — GitHub #18 (corrected per #25)

`|Δ| ≤ 10 %` (provisional) → **`|Δ| ≤ 3 % of the mean, or 30 Å², whichever is larger`**.

- Script: `scripts/bench_t16_bsa_vs_pisa.py`. Audit trail:
  `ref/research/tolerance_benchmark_interface_bsa.md`.
- 25 protein–protein interfaces across 17 entries (275 → 1839 Å² per side). PISA came from the
  **PDBe REST API** (`/pdbe/api/pisa/interfaces/<id>/1`), not the web form — machine-readable, same
  PISA 2.0 computation, so this is no longer web-blocked.
- Median |Δ| 1.2 %, p90 2.4 %, max 3.7 %. **One-sided: biotite reads high in 25/25.**
- Three traps now documented in `ref/structural_criteria.yaml` and guarded in the script: PISA's
  `interface_area` is **per side** (the harness metric is both sides — a factor of 2), symmetry-mate
  interfaces cannot be reproduced from ASU coordinates, and **chain pairs that are fragments of one
  cleaved molecule are not interfaces** (#25 — the first run counted three such pairs in 1CHO, which
  loosened the floor to 60 Å²).

### [x] Benchmark Wilson B: phenix.xtriage vs CCP4 ctruncate — GitHub #19

`± 5 Å²` (provisional) → **`|Δ| ≤ 25 % of the mean, or 2.5 Å², whichever is larger`, void when
`xtriage` reports ΔB_cart ≥ 25 Å²**.

- Script: `scripts/bench_t13_wilson_b.py`. Audit trail: `ref/research/tolerance_benchmark_wilson_b.md`.
- 24 datasets, six resolution bins, 0.88 → 3.50 Å; both programs on the **same MTZ and the same
  intensity columns**.
- Median |Δ| 13.7 %, p90 27 %, max 30.2 %. Absolute disagreement scales with B itself (r = 0.81);
  relative disagreement is flat across resolution (r = −0.02). The old ±5 Å² was vacuous below 1.5 Å
  and violated by 8/24 datasets.
- Wilson-B cross-tool agreement is now explicitly **weak corroboration**: for a precise value,
  compare like-method or use the deposition's Table 1.

**Known residual confound (not blocking):** the two programs' Wilson-plot fit *ranges* were not
matched — ctruncate does not report the range it used. The measured 13.7 % is therefore an upper
bound on pure estimator divergence. Tightening this would need a ctruncate build that reports (or
accepts) an explicit fit range.

## Other tracked work

- **GitHub #2** *(closed — informational)*: driving examples complete (17/17).
- **GitHub #3** *(closed — informational)*: T15/T16/T17 runnable; only web/report-blocked pieces remain.
- **GitHub #25, #26, #27** *(closed 2026-07-25, PR #24)*: review findings on the benchmarks —
  intramolecular fragment pairs counted as interfaces (moved the BSA floor 60 → 30 Å²),
  cache written into the working tree, multi-block sf-cifs silently reduced to one crystal.

## Tolerance benchmarks, round 2 — DONE 2026-07-25, PR #28

Four more `[template]` tolerances measured, using the pattern PR #24 established. **Every one
changed**, and three changed shape rather than magnitude — in each case the disagreement is
dominated by a *configuration* difference that the old tolerance did not name.

### [x] Independent-code-path R offset — was the last self-declared unmeasured magnitude

"a small amount" → **|Δ R| ≤ 0.02**, matched mask radii (`--radii-set=cctbx`).
15 entries, 1.20–2.92 Å: median 0.0069, p90 0.0116, max 0.0151, **one-sided** (gemmi high 15/15,
because PHENIX refits scaling per resolution bin and gemmi applies one global scale).
`scripts/bench_t06_r_offset.py`, `ref/research/tolerance_benchmark_r_offset.md`.

### [x] Clashscore ± 1.0 and H-placement ± 2 %

→ **clashscore |Δ| ≤ max(1.0, 20 %)** with a matched H-build convention; **H count ± 0.1 %**.
Matched convention: median |Δ| 0.115. Mismatched (nuclear vs electron-cloud): median **9.95**, max
22.97 — the convention *is* the signal, and the old single-observation figure (≈ 0.5) understated it
by an order of magnitude. H **count** agrees to 0.013 %, so the ±2 % check was ~150× too loose and
insensitive to the thing that matters.
`scripts/bench_t05_clashscore_h.py`, `ref/research/tolerance_benchmark_clashscore_h.md`.

### [x] CA RMSD ± 0.10 Å and aligned-residue count ± 2

→ **CA RMSD |Δ| ≤ 0.03 Å**, void unless both aligners report the same aligned-residue count.
Matched selection: max 0.02 Å over 7/10 pairs. Unmatched: up to 0.50 Å — and a **one-residue**
difference alone moved RMSD by 0.15 Å. Aligned count keeps ±2 but gains a chain-handling
precondition (`TMalign -ter 0`; without it ΔN reached 185 instead of 31).
`scripts/bench_t01_superposition.py`, `ref/research/tolerance_benchmark_superposition.md`.

### [x] Bond-length RMSD ± 0.003 Å

→ **|Δ| ≤ 0.008 Å** across differing restraint libraries, void unless both tools restrain the same
number of bonds (only 6/17 did). The old value was exceeded by the *typical* case (median 0.0040 Å
on matched counts, gemmi high 17/17) — the same CDL-vs-CCP4-library mechanism the review already
confirmed for bond angles.
`scripts/bench_t05_bond_rmsd.py`, `ref/research/tolerance_benchmark_bond_rmsd.md`.

### Tooling fixed along the way

- **gemmi was on PATH but unrunnable** — the Homebrew build links `libz-ng`, which is not pulled in
  as a dependency, so every invocation died in dyld. `brew install zlib-ng` fixed it. Two documented
  oracle pairings (T05, T06) had never actually been executed.
- **`gemmi validate` does not exist.** The geometry validator is `gemmi rmsz`, and it prints rmsZ
  (unitless) and rmsD (Å) on separate lines — only rmsD compares to a PHENIX RMSD.
- Registry entries added for `T06_r_factor_offset`, `T05_bond_length_rmsd`, `T01_ca_rmsd`, which
  previously lived only in the prose table.

## Tolerance benchmarks, round 3 — DONE 2026-07-25, PR #32

Three items closed, including both debt items from PR #28. One of them **corrected a claim PR #28
published**.

- **Asn/Gln/His flip sets**: 0 disagreements over 634 residues — because `phenix.reduce` **is** the
  standalone Richardson binary (both `reduce.4.16.250520`). The tolerance clause is a
  same-implementation identity check, not corroboration. This also re-attributes PR #28's
  matched-convention clashscore residual (median 0.115): it cannot be H placement, so it is the
  clash-counting step.
- **Restraint library vs implementation**: isolating the library inside PHENIX (CDL vs Engh & Huber)
  shows it accounts for only **9 %** of the bond-length gap — PR #28 attributed it to the library by
  analogy with bond angles. Corrected. For **angles** the framing does hold (51 %; median 0.265°,
  an in-repo confirmation of the 0.3–0.4° literature figure). Matched-library bond floor: 0.006 Å,
  barely tighter than the cross-library 0.008 Å.
- **L-test ⟨|L|⟩**: median |Δ| 0.006, 25/27 inside ±0.02, twin call agreed **27/27**. The
  "matched resolution range" precondition held in **0/27** — ctruncate restricts the L-test by a
  median 0.46 Å and exposes no flag to change it, so the precondition is unachievable and is now
  stated as a caveat.

## Open — remaining tolerances

Every item below has its oracle pair verified runnable on this machine (2026-07-25). Ordered by
priority: the first two are debt from PR #28, then the cheap wins, then the ones needing new design.

### [x] Asn/Gln/His flip-set agreement — DONE 2026-07-25, PR #32

The H-placement tolerance requires "same Asn/Gln/His flip set" but PR #28 measured only H count and
clashscore, because `phenix.clashscore` does not emit flip records. **`reduce` does**: both
`phenix.reduce` and standalone `reduce` write `USER  MOD ... :FLIP  amide:` records into the output
PDB, so the flip sets can be diffed directly.

**Execute:** run both builders over the PR #28 model set, parse `USER  MOD` lines into
{chain, resseq, resname, flip-decision} sets, report exact-match rate and the residues that differ.
Also record the flip *category* (`K`=keep, `C`=clashes, `X`=uncertain, `F`=flip) — an `X` on one side
and a `K` on the other is a weaker disagreement than `F` vs `K`. Expect near-identity if
`phenix.reduce` wraps the same binary; **if so, say that plainly** — the tolerance would then be
checking nothing, and the real flip-set risk lies between reduce and a *different* H builder.

### [x] Matched-library bond-RMSD floor — DONE 2026-07-25, PR #32

PR #28 measured bond RMSD only **across** libraries (PHENIX/CDL vs gemmi/CCP4) and set ± 0.008 Å.
The matched-library floor is unknown and will be much tighter.

**Execute:** `gemmi rmsz` vs **REFMAC5** (`refmac5 NCYC=0`), both against the CCP4 monomer library —
same library, different implementations. Report the floor and add it to the bond-RMSD row as the
matched-library branch, so the ± 0.008 Å is explicitly the cross-library case.

### [x] L-test ⟨|L|⟩ — DONE 2026-07-25, PR #32

`xtriage` reports `<|L|> : 0.483`; `ctruncate` reports `L statistic = 0.497`. Both were already
produced for every dataset in the Wilson-B benchmark, so this needs parsing, not re-running.

**Execute:** parse both from the cached `bench_t13` logs. The tolerance's stated precondition is a
**matched resolution range**, and ctruncate prints the range it used (`Data has used to 40.01 - 1.69
A`) while xtriage prints its own — so for once the precondition can actually be *checked* rather
than assumed. Report the spread with and without a range mismatch. Note the two share the
Padilla-Yeates method, so this measures consistent computation, not method independence — say so.

### [ ] Ramachandran / rotamer outlier % and R-free vs deposited — one pass, three tolerances

The **PDBe validation API** returns the wwPDB-computed values per entry:
`https://www.ebi.ac.uk/pdbe/api/validation/global-percentiles/entry/<id>` →
`percent-rama-outliers`, `percent-rota-outliers`, `DCC_Rfree`, `clashscore` (all `rawvalue`).
This is the harness's documented tiebreaker, and it is a different *pipeline* from a local PHENIX run
even though it is also MolProbity-derived — state that limit rather than claiming independence.

**Execute:** `phenix.ramalyze` / `phenix.rotalyze` / `phenix.model_vs_data` against those values over
a stratified entry set. Bonus check already observed on 12LO: PDBe clashscore 1.18 exactly matches
the cctbx clashscore measured in PR #28 — worth confirming across the set, since it would corroborate
the clashscore tolerance from a third source.

### [ ] Secondary-structure agreement — script already exists

`scripts/t15_ss_agreement.py` runs DSSP (H-bond energetics) against biotite P-SEA (Cα geometry) and
emits a three-state agreement fraction. The tolerance is "two independent assigners floor ≥ 0.80 on a
well-ordered model" and has never been run over a set.

**Execute:** run it over ~20 models spanning resolution and fold class; report the agreement
distribution and whether the ≥ 0.80 floor holds. Genuinely method-independent — different physics on
each side — so this is one of the few tolerances where cross-tool agreement means what it says.

### [ ] Flip-set agreement against a genuinely independent H builder — a gap round 3 opened

Round 3 established that `phenix.reduce` and standalone `reduce` are the same binary, so the
flip-set clause currently checks nothing. `mmtbx.reduce2` / `phenix.reduce2` (the cctbx
reimplementation) is installed and *is* independent.

**Execute:** re-run `scripts/bench_t14_flip_sets.py` with reduce2 on one side. Also worth perturbing
inputs: deposited models are flip-optimised before deposition, so only 7 of 17 had any flips at all
and the decision boundary is barely exercised.

### [ ] Completeness (overall) vs deposition — partially data-blocked

`phenix.model_vs_data` reports completeness; the deposited value should come from the entry's
Table 1. The PDBe experiment API exposes a `completeness` field but it returned **null** for 12LO, so
coverage needs checking before this is worth running. If PDBe coverage is poor, the value must be
scraped from the wwPDB validation report XML instead.

### [ ] DockQ ± 0.01 — needs a different design

The current tolerance compares an agent against `scripts/t16_interface_quality.py`, i.e. DockQ
against itself, so a cross-tool benchmark is not available (no second DockQ implementation is
installed). What *is* measurable is the documented dominant variance source: **chain-mapping
ambiguity in multimers**.

**Execute:** run DockQ over multi-chain complexes with every plausible `--mapping`, and report the
score spread. That bounds what "fixing the chain mapping" is worth, which is what the precondition
asserts without a number.

### [ ] NMR ensemble precision ± 0.05 Å — needs a different design

Same situation: no second implementation. The documented dominant factor is the **ordered-core
selection**, so measure that: run `scripts/t17_nmr_ensemble.py` over several ensembles while varying
the ordered-core RMSF cutoff, and report how much the mean Cα RMSF moves. That turns "precision is
dominated by the superposition selection" into a magnitude.

## Not actionable in this repo (listed so the gaps are explained, not recommended)

- **ctruncate Wilson-plot fit range** (residual confound from #19): the two programs' fit ranges were
  not matched because ctruncate does not report the range it used, so the measured 13.7 % is an
  upper bound on estimator divergence. Needs a ctruncate that reports or accepts an explicit range.
  *Partial local probe:* re-run `phenix.xtriage` with a restricted low-resolution cutoff to bound how
  much of the gap is range choice — worth doing only if the Wilson-B tolerance becomes load-bearing.
- **Fragment guard is `SSBOND`-only** (from #25): a cleaved molecule held together by something other
  than a disulfide, or an entry omitting `SSBOND` records, would not be caught. Extending it needs
  RCSB entity annotations rather than the coordinate file alone.
- **T16 BSA covers protein–protein only**: nucleic-acid and protein–ligand interfaces are out of
  scope for the tolerance as written (protein-only atom selection).
- **T17 independent NMR oracle**: no local wwPDB NMR validation / PROCHECK-NMR / RPF install;
  deposited validation reports are fetched per entry. A deliberate gap in `ref/oracle_tools.md`.
- **ChimeraX (T01, T08), MoRDa (T09), STRIDE (T15)**: recorded deliberate gaps; install only if those
  tasks become regression targets.

- Nothing tracked. The backlog is empty; new work starts as a GitHub issue.
