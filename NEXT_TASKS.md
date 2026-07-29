# Next tasks

Backlog of substantive work not yet done. Mirrors the open GitHub issues; this file
carries the execution detail. Keep in sync — close a GitHub issue and check the box here.

**Last reconciled: 2026-07-27** (round 14). No open GitHub issues. There is no CI in this
repo — `bash scripts/validate.sh` is the gate, and it must exit 0 before a merge.

## Where the tolerance work stands

Thirteen rounds of benchmarking have replaced inferred magnitudes with measured ones. **Every tolerance
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

Round 13 adds a rule about *reading* a band rather than sizing it: **check the clause's direction
before measuring it.** `d_FSC_model` is a resolution, so larger is worse, and the §4 clause says
"did not degrade". Round 12 measured a two-sided `|Δ|` and reported 3 breaches; two of them were
models that got *better*. Under the one-sided band the clause actually specifies, the tolerance
holds on all 28 entries — and the largest change in the whole set, a 36 % improvement, is exactly
the kind of result a symmetric band would have flagged as a failure.

Round 12 adds the counterpart to the headroom rule: **when a band keeps breaking as the set grows,
check its shape before widening it again.** `d_FSC_model` was widened and re-widened as an absolute
± 0.05 Å band and broke anyway at 3 of 21 entries — because the quantity ranges 2.2–6.1 Å and no
absolute band serves both ends. As a **relative** 5 % band the same data has zero violations and a
median of 0.31 %. Rounds 1 and 2 reached the identical conclusion for interface BSA and Wilson B;
it took ten rounds to apply it here.

Round 11 proposed a working rule — **when a band's headroom drops below ~1.2×, treat it as already
broken** — after round 10 measured 1.15× on the §4 Cα band and round 11 broke it on the first
attempt. **Back-tested in the round-13 reconciliation, the rule does not hold** (#59): breaks have
occurred at 1.15×, 1.44× and 1.55×, while the one band that survived two rounds of set growth had
the second-lowest headroom of the four at 1.26×. It was generalised from a single observation and
never re-tested — the same construction this file warns about everywhere else, applied to a rule
*about* tolerances rather than to a tolerance. Treat low headroom as worth noting, not as a
predictor, and treat **set growth** as the thing that actually precedes a break.

Round 10 adds a sixth, which is really the first one turned on this repo's own work: **a band is
only as good as the last entry added to its set.** Completing the EM set from 2 to 6 entries broke
the CC_mask band that had stood since round 5 — and round 5 had itself flagged that a null
refinement consumed 65 % of it. The warning was in the file for five rounds before the data caught
up with it.

Round 9 closes the earlier thread with the fifth and sharpest: **"unmeasurable" usually means "not yet
read properly".** Four rounds carried `d_FSC_model` as ungateable — blamed on missing half-maps,
then on model-to-map coverage, then on nothing at all. Reading the FSC curve mtriage already writes
took one comparison and showed the tool reports the *first* threshold crossing, which one anomalous
low-resolution shell defeats. The clause was gateable the whole time. The §4 bands held on 19/19 entries at 1.4–2.9 Å and failed on 10/19 once 3.0–3.6 Å
entries were added. Before trusting any band here, check the range of the set it came from — every
benchmark records that in its scope limits for exactly this reason.

## Open

Round 15 widened at 3.0–4.0 Å with **predictions registered before the data**, after round 14 had to
label its own p-values as computed post hoc. Four of six held.

| # | Prediction | Outcome |
|---|---|---|
| P1 | ≥ 1 entry degrades | ✅ 4 did |
| P2 | largest degradation > 0.0139 | ✅ 0.0351, 2.5× |
| P3 | −0.06 band holds | ✅ 1.71× headroom |
| P4 | rate nearer 36 % than 0 % | ✅ 50 % |
| P5/P6 | cluster-mates behave alike | ❌ **both falsified** |

**P2 was the round's real test.** The rationale for widening low rather than high — that degradations
there are large enough to re-fit a band — is confirmed, so round 14's frequency/magnitude correction
was right and the resolution split is better evidenced than before.

**P5/P6 cost a finding.** Mid-round I claimed the evidence base was smaller than round 14 said,
because 22 entries came from 12 publications and the four largest degradations arrived as same-paper
pairs. Both registered tests failed — the peptidase cluster produced **opposite signs on the same
protein** — and a permutation test put within-cluster agreement at **p = 0.38**. Withdrawn, per the
rule registered before the test ran. Round 14's count argument is untouched; only the further
deflation from ~9 to ~6 is gone.

### [ ] `d_FSC_model` has 1.045× headroom — the thinnest margin in the file

10BU degraded it by **+4.79 %** against a **5 %** band, displacing 9VAM's +4.28 %. **Any future
degradation above 4.79 % breaks it.**

Deliberately **not** widened: it holds with 0 breaches, and this series does not move bands on
anticipation. But it is now the first thing to re-test, ahead of CC_mask — which is the reversal of
where attention has been for six rounds. P3 was registered about CC_mask because that tolerance has
all the breakage history; it came through at 1.71× while the quantity nobody was watching nearly
broke.

**Execute:** the next EM widening should be sized to produce `d_FSC_model` degradations specifically.
Note that CC_mask and `d_FSC_model` can move in **opposite directions** on one refinement (10RI), so a
set chosen to stress one does not automatically stress the other.

### [ ] Entry attrition is systematic, at ~17 %

Three of 18 attempted entries across rounds 14–15 were unprocessable: 11MR and 10EG (unparameterised
ligands, 128 and 195 atoms), 10EN (`O1-` outside the electron scattering table). These are entry
properties, not tool failures, and they bias the set toward chemically simple structures every run.

**Execute:** quantify whether ligand-bearing entries differ in Δ, or record the bias as permanent in
the tolerance row. Currently the direction is unknown, only the existence is.

### [ ] Both CC_mask bands are still set from single worst cases

−0.04 above 9O9K's −0.0311 and −0.06 above 9UPM's −0.0475. Round 15 added 4 degradations to the
`≥ 3.0 Å` branch but none exceeded −0.0351, so the worst case is unchanged and the band is untested at
its edge.

### [ ] Recover per-entry values for rounds 5 and 9–13 — now a prerequisite, not housekeeping

Round 15 hit this gap twice. The permutation test could only use 30 of 44 entries, and **the headline
CC_mask degradation count cannot be stated as a number at all** — round 13 published only its branch
minimum, so 5 of its entries have no recorded Δ and the total is a range, 14–19 (#63).

Since round 14 established that the degradation count *is* the evidence measure for a one-sided band,
not being able to state it is a direct limit on every claim built on it.

**Execute:** re-run rounds 5 and 9–13's entries through `bench_refinement_deltas_em.py`, now that
`fetch_em_entries.py` can rebuild the cache. The entry lists survive in the audit trails even though
the per-entry values do not.

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
