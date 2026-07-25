# Next tasks

Backlog of substantive work not yet done. Mirrors the open GitHub issues; this file
carries the execution detail. Keep in sync — close a GitHub issue and check the box here.

**Last reconciled: 2026-07-25.** No open GitHub issues, no open PRs. There is no CI in this
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

## Open — the remaining `[template]` tolerances are still inference-only

PR #24 established the pattern (`[benchmark]` provenance, a re-runnable `scripts/bench_*.py`, an
audit trail under `ref/research/`) and applied it to the two tolerances marked *provisional*. It did
**not** touch the other ~18 `[template]` tolerances in `ref/thresholds_and_standards.md`. Those were
*reviewed* — the mechanisms were checked against the literature — but their magnitudes were never
measured. That is the same defect class the two provisional ones had; they simply weren't labelled.

Every oracle pair below is installed and verified runnable on this machine (2026-07-25):
`~/phenix-2.0-5936`, CCP4 9.0.015, `/opt/homebrew/bin/gemmi` (CLI; the *Python module* is **not**
installed — use the CLI recipes), `~/tools/tmalign/TMalign`, `~/tools/probe-src/probe`,
`~/tools/reduce-src/build/reduce_src/reduce`, `mkdssp`, biotite 1.7.1, DockQ 2.1.3.

### [ ] Benchmark the independent-code-path R offset — the last self-declared unmeasured magnitude

`ref/thresholds_and_standards.md` states this one's magnitude is **unbenchmarked** in the row
itself: "an independent R re-derivation may differ *by a small amount* … (magnitude
**unbenchmarked**)". It is the closest analogue to the two just settled, and the only tolerance left
that admits in-line that it has no number.

**Execute:** `gemmi sfcalc` vs `phenix.model_vs_data` on a set of deposited model+MTZ pairs spanning
resolution; tabulate the R offset; replace the prose with a measured band. Note that gemmi uses the
same flat-mask bulk-solvent + anisotropic scaling as PHENIX, so this is *not* a "simple vs
sophisticated" comparison — the write-up already corrects that misconception and the benchmark
should confirm it.

### [ ] Benchmark clashscore ± 1.0 and H-placement ± 2 % (one pass, same tool pair)

`phenix.reduce` / cctbx clashscore vs standalone Richardson `reduce` + `probe`. The repo has exactly
**one** observation behind ±1.0 (1SAR: 3.13 cctbx vs 3.63 standalone), and it already knows the
H-build convention (electron-cloud vs nuclear) is a precondition — a benchmark would separate the
convention effect from the implementation noise floor. Both metrics come from the same run, so they
are one job, not two.

### [ ] Benchmark CA RMSD ± 0.10 Å and aligned-residue count ± 2 (one pass, same tool pair)

`phenix.superpose_models` vs `TMalign`. Both tolerances carry selection-matching preconditions
(same residue selection; same aligner class) that are precisely what a benchmark would quantify —
how much of the observed spread is the selection and how much is the superposition itself.

### [ ] Benchmark bond-length RMSD ± 0.003 Å

PHENIX vs `gemmi validate` (CLI). Bond-*angle* was already made library-conditional by the review
(CDL vs Engh & Huber shifts it 0.3–0.4°); bond-length was left at ±0.003 Å untested, and the same
library difference plausibly affects it.

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
