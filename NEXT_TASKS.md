# Next tasks

Backlog of substantive work not yet done. Mirrors the open GitHub issues; this file
carries the execution detail. Keep in sync — close a GitHub issue and check the box here.

## Tolerance benchmarks (from the domain-expert `[template]` review) — DONE

Both provisional agreement tolerances have been benchmarked by running the tools on a structured
test set. **No tolerance in `ref/thresholds_and_standards.md` is provisional any more.** Both changed
*shape*, not just magnitude: each is now a relative band with an absolute floor, because in both
cases the disagreement scales with the quantity being measured. The new `[benchmark]` provenance tag
marks a tolerance whose magnitude was **measured in this repo** rather than inferred.

### [x] Benchmark interface BSA: biotite SASA vs PISA — GitHub #18

`|Δ| ≤ 10 %` (provisional) → **`|Δ| ≤ 3 % of the mean, or 60 Å², whichever is larger`**.

- Script: `scripts/bench_t16_bsa_vs_pisa.py`. Audit trail:
  `ref/research/tolerance_benchmark_interface_bsa.md`.
- 26 protein–protein interfaces across 14 entries (216 → 2853 Å² per side). PISA came from the
  **PDBe REST API** (`/pdbe/api/pisa/interfaces/<id>/1`), not the web form — machine-readable, same
  PISA 2.0 computation, so this is no longer web-blocked.
- Median |Δ| 1.3 %, p90 3.6 %, max 9.1 %. **One-sided: biotite reads high in 26/26.**
- Two traps now documented in `ref/structural_criteria.yaml`: PISA's `interface_area` is **per side**
  (the harness metric is both sides — a factor of 2), and symmetry-mate interfaces cannot be
  reproduced from ASU coordinates.

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

## Open

- Nothing tracked. The backlog is empty; new work starts as a GitHub issue.
