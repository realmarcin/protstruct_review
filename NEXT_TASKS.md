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

## Open

- **Remaining `[template]` tolerances**: Ramachandran/rotamer favoured and outlier %, L-test ⟨|L|⟩,
  secondary-structure agreement, DockQ, NMR ensemble precision, R-free vs deposited, completeness.
  Each needs the same treatment; the pattern and the tooling now exist.
- **Asn/Gln/His flip-set agreement** (part of the H-placement tolerance) is still unmeasured —
  `phenix.clashscore` does not emit the flip records, so it needs a different cctbx entry point.
- **Matched-library bond RMSD floor**: this round measured only the cross-library case. The
  matched-library tolerance (PHENIX vs PHENIX, gemmi vs REFMAC) will be much tighter and is unknown.

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
