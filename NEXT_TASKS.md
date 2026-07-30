# Next tasks

Backlog of substantive work not yet done. Mirrors the open GitHub issues; this file
carries the execution detail. Keep in sync — close a GitHub issue and check the box here.

**Last reconciled: 2026-07-29** (round 15). No open GitHub issues, no open PRs. There is no CI in this
repo — `bash scripts/validate.sh` is the gate, and it must exit 0 before a merge.

## Where the tolerance work stands

Fifteen rounds of benchmarking have replaced inferred magnitudes with measured ones. **Every tolerance
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
| 10 | [#50](https://github.com/realmarcin/protstruct_review/pull/50) (2026-07-27) | EM set completed (CC_mask band breached and widened); §4 high-res end filled; rotamer chi geometry verified |
| 11 | [#52](https://github.com/realmarcin/protstruct_review/pull/52) (2026-07-27) | both "edge" bands breached; CC_mask made resolution-conditional; rotamer library corroborated |
| 12 | [#54](https://github.com/realmarcin/protstruct_review/pull/54) (2026-07-27) | CC_mask holds at 22 entries and its split is located; `d_FSC_model` band made relative |
| 13 | [#56](https://github.com/realmarcin/protstruct_review/pull/56) (2026-07-27) | CC_mask `< 3.0 Å` breached and widened; `d_FSC_model` band corrected to one-sided |
| 14 | [#60](https://github.com/realmarcin/protstruct_review/pull/60) (2026-07-27) | EM benchmark made reproducible; entry count shown not to be evidence; split kept |
| 15 | [#62](https://github.com/realmarcin/protstruct_review/pull/62) (2026-07-28) | pre-registered low-resolution widening: P1–P4 confirmed, P5/P6 falsified, clustering withdrawn |
| 16 | [#66](https://github.com/realmarcin/protstruct_review/pull/66) (2026-07-29) | per-entry record made durable; all 5 predictions held; `d_FSC_model` tail shown to be sampled thinly, not thin |

Per-tolerance detail lives in the audit trails under `ref/research/tolerance_benchmark_*.md` and in
the re-runnable `scripts/bench_*.py`. It is deliberately **not** duplicated here — a backlog that
accumulates a changelog stops being readable as a backlog.

**Lessons live in [`ref/research/lessons.md`](ref/research/lessons.md)** — fifteen rounds of
rules about how these tolerances fail, extracted so this file stays readable as a backlog (#65).
Record new ones there. The operative few, for anyone about to add a tolerance or widen a band:

- **A tolerance that has never been run is a hypothesis** — it lost 21 times out of 21 here. So is a
  "blocked" item, a measured band outside its measured regime, and a mechanism from two data points.
- **Register the prediction before the data.** It changed the outcome twice in round 15 alone.
- **Count what the clause can actually be broken by.** A one-sided band gains nothing from an
  improvement, so a round can raise every count in the tolerance row while strengthening nothing.
- **Check the clause's direction and shape before sizing it.** Two rounds were spent widening a band
  that was the wrong shape, and one reported improvements as breaches.

## Open

Round 16 targeted `d_FSC_model` at 1.045× headroom with 12 entries at 3.00–4.11 Å. **All five
registered predictions held**, which is itself worth distrusting — three were near-certain, and the
one I called risky (P2, the 5 % band holding) held for a reason that indicts how I set its
probability.

**Two items from the previous backlog are now closed.** The per-entry recovery item was
**infeasible**: round 13 named 2 of its 6 entries, and the other 4 cannot be re-run because nothing
records what they were. The count is permanently 15–20. The cause is fixed instead — every run now
appends to `ref/research/data/em_refinement_deltas.tsv`, and it earned its keep inside the same round
by enabling the first cross-round resolution analysis (ρ = +0.397, n = 44).

**Attrition is 6 of 31 (19 %) across rounds 14–16**, from exactly two causes. Charged models are now
screened before the map download, at no cost; unparameterised ligands still cost a full download and
a refinement attempt.

### [ ] A selectively recorded history biases priors, not just counts

The sharpest finding of round 16, and it generalises past this repo. I set P2's probability from the
three `d_FSC_model` magnitudes then on record — 2 of 3 above 4 % — and concluded the band was at
real risk. With every value now recorded, **1 of 6 is above 4 %, median 0.240 %**. The old sample
contained the alarming values *because* they were the ones worth writing down.

**Execute:** audit the other tolerance rows for magnitudes quoted from partial records. Any row citing
"worst observed" without a denominator is suspect in the same way — the worst is always recorded, the
typical often is not. `ref/research/data/` now gives a place to put the denominators.

### [ ] The `d_FSC_model` band is safer than 1.045× suggests, but the worst case is untouched

10BU's +4.787 % still stands as the only observation near the 5 % band, and round 16 did not approach
it (worst +1.476 %). So the band is not in imminent danger, but neither has anything been learned
about *why* 10BU was six times the median.

**Execute:** re-run 10BU specifically and check whether +4.787 % reproduces, before treating it as
the number that sets the band. One irreproducible outlier setting a tolerance is the failure mode this
series has hit repeatedly — and unlike the historical worst cases, 10BU's inputs are still on disk.

### [ ] Screen unparameterised ligands at fetch time

The charge screen removed one attrition cause from the expensive path. The ligand cause — 3 of the 6
skips — still costs a model download, a map download and a `real_space_refine` attempt before failing.
Residues absent from the CCP4 monomer library are checkable from the model alone.

### [ ] CC_mask degradation rate is not resolution-driven — find what does drive it

Round 15 (3.00–3.90 Å) degraded 4 of 8; round 16 (3.00–4.11 Å, coarser) degraded 1 of 9. A four-fold
difference between adjacent windows means resolution sets the *magnitude* envelope but not the rate.
The TSV now holds pre/post CC_mask, resolution and charge inventory for every entry from round 14 on,
so candidate predictors can be tested without new refinements.

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
- **GitHub #57** *(closed 2026-07-27, PR #56)*: a self-review finding — the round-13 write-up claimed
  a "fifth consecutive round" of thinnest-band failures when the record is 3 breaks in 4 widenings,
  round 12 having held. Logged because the correction changed a stated rule of thumb, not just a
  number: the heuristic is 3 for 4, and its one miss was a band of the wrong *shape* rather than the
  wrong size — a failure mode headroom does not track.
- **GitHub #59** *(closed 2026-07-28, PR #58)*: the round-11 "below 1.2× headroom, treat as already
  broken" rule, back-tested and found not to hold — breaks at 1.15×, 1.44× and 1.55× while the one
  band that survived two rounds of set growth sat at 1.26×. Logged because it retired a *lesson*, not
  a tolerance: the rule was generalised from one observation and never re-tested.
- **GitHub #61** *(closed 2026-07-28, PR #60)*: degradation frequency and magnitude conflated, which
  had inverted a widening recommendation. Degradation is more frequent below 3.0 Å (4/8 vs 5/14) but
  3–7× larger above it; only magnitude re-fits a band. Round 15 then confirmed the corrected version.
- **GitHub #63** *(closed 2026-07-29, PR #62)*: "14 CC_mask degradations" stated as a count when it is
  a lower bound (14–19) — round 13 published only its branch minimum. Logged because the degradation
  count is now the headline evidence measure, so an unverifiable figure there is not an improvement on
  an inflated one.
