# Next tasks

Backlog of substantive work not yet done. Mirrors the open GitHub issues; this file
carries the execution detail. Keep in sync — close a GitHub issue and check the box here.

**Last reconciled: 2026-07-26.** No open GitHub issues, no open PRs. There is no CI in this
repo — `bash scripts/validate.sh` is the gate, and it must exit 0 before a merge.

## Where the tolerance work stands

Five rounds of benchmarking have replaced inferred magnitudes with measured ones. **Every tolerance
in `ref/thresholds_and_standards.md` now carries `[benchmark]` provenance** (21 rows), with two
named exceptions recorded below where no reference exists to measure against.

| Round | PR | Settled |
|---|---|---|
| 1 | [#24](https://github.com/realmarcin/protstruct_review/pull/24) (2026-07-25) | interface BSA, Wilson B — the two marked *provisional* |
| 2 | [#28](https://github.com/realmarcin/protstruct_review/pull/28) (2026-07-26) | R offset, clashscore, H-placement, CA RMSD, aligned-residue count, bond-length RMSD |
| 3 | [#32](https://github.com/realmarcin/protstruct_review/pull/32) (2026-07-26) | restraint-library decomposition, Asn/Gln/His flip sets, L-test |
| 4 | [#36](https://github.com/realmarcin/protstruct_review/pull/36) (2026-07-26) | Ramachandran/rotamer outlier %, R-free, completeness, SS agreement, DockQ mapping, NMR ordered core |
| 5 | [#39](https://github.com/realmarcin/protstruct_review/pull/39) (2026-07-26) | the §4 refinement Δ-tolerances (X-ray + cryo-EM), Ramachandran favored % |

Per-tolerance detail lives in the audit trails under `ref/research/tolerance_benchmark_*.md` and in
the re-runnable `scripts/bench_*.py`. It is deliberately **not** duplicated here — a backlog that
accumulates a changelog stops being readable as a backlog.

The pattern held to the end. Tolerances generalised from a single observation — clashscore ±1.0 from
one 1SAR pair; H-count ±0.1 % from one builder in two conventions; the SS floor ≥0.80 from 1SAR
alone; the bond-length attribution by analogy with bond angles; the DockQ and NMR preconditions
asserted with no magnitude at all — **every one moved when measured**. Three moved by more than an
order of magnitude; one (SS agreement) was the wrong *shape* of check entirely; and the §4 bands in
round 5 were breached by re-refining a deposited model against its own data, with no modelling
change at all.

Carry the same suspicion into anything added next: a tolerance that has never been run is a
hypothesis, and in this repo the hypothesis lost 21 times out of 21.

## Open

### [ ] Rotamer **favored** % — no reference exists

Round 5 measured the Ramachandran favored % (± 1.0 pp → ± 0.2 pp) but could not measure the rotamer
half. The wwPDB validation report's `rota=` attribute holds the rotamer **name** (`m-10`, `mp`,
`mt-10`, …) with no favored/allowed classification and no `OUTLIER` value, so there is no reference
figure to compare a local `phenix.rotalyze` run against. `phenix.rotalyze` also prints only an
outlier SUMMARY line, not a favored one.

**Execute:** needs a different oracle — MolProbity's own rotamer classification, or counting
per-residue rotamer verdicts from a full MolProbity run rather than the wwPDB report. Until then the
clause stays unmeasured; `bench_vs_deposited.py` returns `None` for it rather than a confident 0 %.

### [ ] Flip sets vs an independent H builder — BLOCKED on reduce2's output

Round 3 established that `phenix.reduce` and standalone `reduce` are the **same binary**
(`reduce.4.16.250520`), so the "same Asn/Gln/His flip set" clause currently checks nothing.
`mmtbx.reduce2` (v2.14.0) is the independent implementation — but it reports **no flip information**:
zero occurrences of "flip" in its `.txt` log and no `USER  MOD` records in its output PDB, so flip
calls cannot be extracted.

Re-check on the next PHENIX upgrade.

### [ ] Widen the §4 refinement benchmark

Round 5 settled §4 on **8 X-ray entries and 2 cryo-EM entries** — enough to show the old bands failed
on a null re-refinement (5/8 breached ΔRMSD, 3/8 clashscore), but thin for the EM half in particular.
Three specific gaps:

- **`d_FSC_model` is ungateable without half-maps.** `phenix.mtriage`'s model-map FSC crossings are
  degenerate (27WR: FSC = 0.5 at 29.79 Å for a 2.7 Å map) and `resolution=` does not fix it. EMDB
  serves half-maps separately; fetching them would make the second map-model clause measurable.
- **Null case only.** The benchmark calibrates the false-positive side of each band — what a
  refinement that should change nothing actually does. It never tests a genuinely *degrading*
  refinement, so the false-negative side is unknown.
- **One refinement protocol** (`phenix.refine`, 3 macro-cycles, default weights). REFMAC5/servalcat
  as a second refiner would show how much of the null spread is protocol-specific.
- **Clashscore Δ is currently ungated** (issue #40): its null-case range is −2.70 to +10.39, so no
  useful band exists. A larger set would show whether the +10.39 outlier is representative or a
  one-off, and whether the even 4-up/4-down split holds.

## Not actionable in this repo (listed so the gaps are explained, not recommended)

- **ctruncate Wilson-plot fit range** (residual confound from #19): the fit ranges were not matched
  because ctruncate does not report the range it used, so the measured 13.7 % is an upper bound on
  estimator divergence. Needs a ctruncate that reports or accepts an explicit range. *Partial local
  probe:* re-run `phenix.xtriage` with a restricted low-resolution cutoff to bound how much of the
  gap is range choice — worth doing only if the Wilson-B tolerance becomes load-bearing.
- **L-test matched resolution range**: the same shape, and confirmed unachievable — ctruncate
  restricts the L-test by a median 0.46 Å and its usage line exposes no resolution flag. Recorded as
  a caveat on the tolerance rather than a gate.
- **Fragment guard is `SSBOND`-only** (from #25): a cleaved molecule held together by something other
  than a disulfide, or an entry omitting `SSBOND` records, would not be caught. Extending it needs
  RCSB entity annotations rather than the coordinate file alone.
- **T16 BSA covers protein–protein only**: nucleic-acid and protein–ligand interfaces are out of
  scope for the tolerance as written (protein-only atom selection).
- **T17 independent NMR oracle**: no local wwPDB NMR validation / PROCHECK-NMR / RPF install;
  deposited validation reports are fetched per entry. A deliberate gap in `ref/oracle_tools.md`.
- **ChimeraX (T01, T08), MoRDa (T09), STRIDE (T15)**: recorded deliberate gaps; install only if those
  tasks become regression targets. **STRIDE is worth more now than before**: it is a third SS
  assigner, and round 4 could not tell whether DSSP or P-SEA is the outlier when they disagree.

## Other tracked work

- **GitHub #2** *(closed — informational)*: driving examples complete (17/17).
- **GitHub #3** *(closed — informational)*: T15/T16/T17 runnable; only web/report-blocked pieces remain.
- **GitHub #18, #19** *(closed 2026-07-25, PR #24)*: the two provisional tolerances.
- **GitHub #25, #26, #27** *(closed 2026-07-26, PR #24)*: intramolecular fragment pairs counted as
  interfaces, cache written into the working tree, multi-block sf-cifs.
- **GitHub #29, #30, #31** *(closed 2026-07-26, PR #28)*: two-block `model_vs_data` logs and outlier
  asymmetry, the near-identical-pairs weakness in the CA RMSD floor, dead code.
- **GitHub #33, #34, #35** *(closed 2026-07-26, PR #32)*: subset-dependent library share,
  unknown-vs-mismatched L-test ranges, and the het-dictionary difference that exposed a wrong
  H-count tolerance.
- **GitHub #37, #38** *(closed 2026-07-26, PR #36)*: the Ramachandran 0.00-vs-0.00 evidence base, and
  the SS-agreement metric being degenerate at the bad end.
