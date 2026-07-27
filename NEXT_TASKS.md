# Next tasks

Backlog of substantive work not yet done. Mirrors the open GitHub issues; this file
carries the execution detail. Keep in sync — close a GitHub issue and check the box here.

**Last reconciled: 2026-07-26.** No open GitHub issues, no open PRs. There is no CI in this
repo — `bash scripts/validate.sh` is the gate, and it must exit 0 before a merge.

## Where the tolerance work stands

Nine rounds of benchmarking have replaced inferred magnitudes with measured ones. **Every tolerance
in `ref/thresholds_and_standards.md` carries `[benchmark]` provenance** (21 rows). Round 6 found that
**two of three "blockers" were wrong** — both mis-invocations rather than limits of a tool. Round 7
then found that **two bands set in rounds 5 and 6 were themselves wrong**, fitted to a narrow
resolution range and breached by null re-refinement once low-resolution entries were included.

| Round | PR | Settled |
|---|---|---|
| 1 | [#24](https://github.com/realmarcin/protstruct_review/pull/24) (2026-07-25) | interface BSA, Wilson B — the two marked *provisional* |
| 2 | [#28](https://github.com/realmarcin/protstruct_review/pull/28) (2026-07-26) | R offset, clashscore, H-placement, CA RMSD, aligned-residue count, bond-length RMSD |
| 3 | [#32](https://github.com/realmarcin/protstruct_review/pull/32) (2026-07-26) | restraint-library decomposition, Asn/Gln/His flip sets, L-test |
| 4 | [#36](https://github.com/realmarcin/protstruct_review/pull/36) (2026-07-26) | Ramachandran/rotamer outlier %, R-free, completeness, SS agreement, DockQ mapping, NMR ordered core |
| 5 | [#39](https://github.com/realmarcin/protstruct_review/pull/39) (2026-07-26) | the §4 refinement Δ-tolerances (X-ray + cryo-EM), Ramachandran favored % |
| 6 | [#42](https://github.com/realmarcin/protstruct_review/pull/42) (2026-07-26) | flip sets vs reduce2, rotamer assignment agreement, §4 detection floor |
| 7 | [#44](https://github.com/realmarcin/protstruct_review/pull/44) (2026-07-26) | §4 bands made resolution-conditional; rotamer boundary bounded |
| 8 | [#46](https://github.com/realmarcin/protstruct_review/pull/46) (2026-07-26) | 2.5 Å split validated; restraint effect measured; round-7 `d_FSC_model` diagnosis withdrawn |
| 9 | [#48](https://github.com/realmarcin/protstruct_review/pull/48) (2026-07-27) | `d_FSC_model` mechanism found; the clause is gateable after all |

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
hypothesis, and in this repo the hypothesis lost 21 times out of 21. Round 6 adds a corollary —
**a "blocked" item is also a hypothesis**. Two of the three blockers dissolved on re-examination:
`reduce2` reports flips once `add_flip_movers=True` is passed (it defaults off), and the §4
false-negative side was testable all along by damaging models rather than refining them.

Round 7 adds the third: **a band this repo measured is a hypothesis too, outside the regime it was
measured in.** Round 8 adds the fourth, and it is about explanations rather than numbers: **a
mechanism inferred from two data points is a hypothesis.** Round 7 explained a degenerate
`d_FSC_model` as a coverage problem on n = 2; round 8 refuted it with four more entries. The number
(1 of 6 entries fails) survived; the story did not.

Round 9 closes that thread with the fifth and sharpest: **"unmeasurable" usually means "not yet
read properly".** Four rounds carried `d_FSC_model` as ungateable — blamed on missing half-maps,
then on model-to-map coverage, then on nothing at all. Reading the FSC curve mtriage already writes
took one comparison and showed the tool reports the *first* threshold crossing, which one anomalous
low-resolution shell defeats. The clause was gateable the whole time. The §4 bands held on 19/19 entries at 1.4–2.9 Å and failed on 10/19 once 3.0–3.6 Å
entries were added. Before trusting any band here, check the range of the set it came from — every
benchmark records that in its scope limits for exactly this reason.

## Open

Round 9 identified the `d_FSC_model` mechanism and **unblocked the clause** — it was never
ungateable, only mis-read. Two items remain, one of them a verified dead end.

### [ ] Finish the `d_FSC_model` Δ band (3 of 6 entries measured)

The corrected crossing works on all 6 EM entries, but the before/after band rests on **3**:
`real_space_refine` on 10QT (78 939 atoms) did not finish, and 21BQ and 24UM were queued behind it.
Observed null Δ is at most **0.0007 Å** against a ± 0.05 Å band — ~70× headroom — but 3 refinements
is not a basis for tightening.

**Execute:** re-run `scripts/bench_refinement_deltas_em.py` with the cache warm (the mtriage
measurements are already cached; only the three refinements are outstanding), then decide whether
± 0.05 Å can be tightened. Budget hours, not minutes, for 10QT.

### [ ] Rotamer favored/allowed boundary — verified dead end

No independent rotamer library is installed: every `molprobity.*`/`phenix.*` rotamer tool is cctbx,
biotite exposes only geometric rotation helpers, Bio.PDB has none, and the local Richardson tools are
`probe`/`reduce`/`tmalign`. ± 1.0 pp stays contingent on the shared-library assumption (3.9 % of
residues within ×1.25 of the cutoff). Reopen only if a non-cctbx rotamer implementation appears.

### [ ] High-resolution end of the §4 split is thin

Only **3 entries below 2.0 Å** in the 26-entry set, and the `< 2.5 Å` band (0.10 Å) is 2× the largest
shift observed there (0.045 Å). Safe but under-evidenced at the tight end — worth 5–6 more entries at
1.0–2.0 Å if §4 becomes load-bearing at high resolution.

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
