# Next tasks

Backlog of substantive work not yet done. Mirrors the open GitHub issues; this file
carries the execution detail. Keep in sync — close a GitHub issue and check the box here.

**Last reconciled: 2026-08-03** (round 21). Rounds 17–18 merged as
[#69](https://github.com/realmarcin/protstruct_review/pull/69); rounds 19 and 20 followed in
[#82](https://github.com/realmarcin/protstruct_review/pull/82) and its successor. **Check the issue
tracker for open issues; this file does not mirror it in real time.** There is no CI in this
repo — `bash scripts/validate.sh` is the gate, and it must exit 0 before a merge.

## Where the tolerance work stands

Twenty-one rounds of benchmarking have replaced inferred magnitudes with measured ones. Round 6 found
that **two of three "blockers" were wrong** — both mis-invocations rather than limits of a tool.
Round 7 then found that **two bands set in rounds 5 and 6 were themselves wrong**, fitted to a narrow
resolution range and breached by null re-refinement once low-resolution entries were included.

**Where the registry stands.** Round 17 audited every `[benchmark]` row and found **7 quote a figure
from a set that can no longer be reconstructed**; they are marked `⚠ partial record`. Round 18 fixed
the cause — **every `bench_*.py` now commits the set it ran on**, and `scripts/validate.sh` fails if
one does not. **13 rows are fully backed.**

**The counts, reconciled (round 18) — there are two different 21s and both are right.** §3 and §4
hold **21 rows**, of which **20 carry `[benchmark]`**; the exception is §4's *absolute geometry
floors*, which is `[literature]` and was never measured here. Those 20 rows carry **21 benchmarked
tolerances**, because the map-model row holds two, CC_mask and `d_FSC_model`. So "21 rows" and "lost
21 times out of 21" are both correct and count different things — and round 17's "20 rows, not 21"
was itself a miscount, blaming the shared map-model row when the real exception is the `[literature]`
floors row.

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
| 16 | [#66](https://github.com/realmarcin/protstruct_review/pull/66) (2026-07-30) | per-entry record made durable; all 5 predictions held; `d_FSC_model` tail shown to be sampled thinly, not thin |
| 17 | [#69](https://github.com/realmarcin/protstruct_review/pull/69) (2026-07-30) | rate question closed as underpowered; 10BU verified byte-identical; registry audited (7 rows marked partial); ligand screen moved to fetch time |
| 18 | [#69](https://github.com/realmarcin/protstruct_review/pull/69) (2026-07-31) | every benchmark commits its set + gate; bond-angle recovered and DockQ mark withdrawn; fetch attrition made durable; §4 staleness diagnosed as two untested clauses |
| 19 | [#82](https://github.com/realmarcin/protstruct_review/pull/82) (2026-08-01) | EM set 59→69 named entries; all bands held; P4 falsified and round 16's tail reading corrected; 10BU located at 3.24× the next-largest; zero refinement-stage attrition |
| 21 | (2026-08-03) | L-test given a re-derivable 24-dataset set instead of being retired — agrees with the historical 27 on every quantity; EM benchmark now writes per-entry results as it goes |
| 20 | [#86](https://github.com/realmarcin/protstruct_review/pull/86) (2026-08-02) | the two §4 clauses untested since round 7 re-measured: both hold, both worst cases reproduce exactly; the clashscore ratio gate found undefined at `pre = 0` and given a low-end guard; `phenix.refine` shown deterministic 8/8 |

Per-tolerance detail lives in the audit trails under `ref/research/tolerance_benchmark_*.md` and in
the re-runnable `scripts/bench_*.py`. It is deliberately **not** duplicated here — a backlog that
accumulates a changelog stops being readable as a backlog.

**Lessons live in [`ref/research/lessons.md`](ref/research/lessons.md)** — twenty-one rounds of
rules about how these tolerances fail, extracted so this file stays readable as a backlog (#65).
Record new ones there. The operative few, for anyone about to add a tolerance or widen a band:

- **A tolerance that has never been run is a hypothesis** — it lost 21 times out of 21 here. So is a
  "blocked" item, a measured band outside its measured regime, and a mechanism from two data points.
- **Register the prediction before the data.** It changed the outcome twice in round 15 alone.
- **Count what the clause can actually be broken by.** A one-sided band gains nothing from an
  improvement, so a round can raise every count in the tolerance row while strengthening nothing.
- **Check the clause's direction and shape before sizing it.** Two rounds were spent widening a band
  that was the wrong shape, and one reported improvements as breaches.
- **Record every entry, not the interesting ones.** A partial history does not just lose evidence, it
  biases the priors built on what survives — and four entries counted in the published totals are now
  unidentifiable. `scripts/validate.sh` gates that each round leaves its lesson here.
- **Check the power before hunting the mechanism.** Mechanism hunts are 0 for 3 here. Round 17's
  gate showed the phenomenon it was asked to explain (4/8 vs 1/9) is p = 0.131 — the question needed
  ~20 entries per arm and the rounds build 8.
- **Registering a prediction does not protect you from registering a bad test.** Round 17's P2 held
  as registered and was still wrong, because correlating a change against its own baseline is
  negatively biased by construction. Name the test's artefacts *in* the registration.
- **Confirm a suspected gap by running, not by reading.** Round 17 marked the DockQ row partial from
  a `limit=8` in the code; re-running showed the cap was never reached and the record was complete.
- **When the set grows, re-test every clause it backs.** Rounds 8/10/11 grew the §4 X-ray set
  19 → 37 while re-testing only two of its four clauses; the other two have been untested since
  round 7.
- **A reproduced extreme is binding, not disposable.** 10BU sits 3.24× above every other
  `d_FSC_model` degradation, and round 17 proved it reproduces byte-identically — so the band stays
  where it is, precisely located rather than defended.
- **A prediction confirmed once describes the round that confirmed it.** Round 16 confirmed
  "largest degradation > 1.1 %"; round 19 registered the same threshold and falsified it.
- **A lost set can sometimes be replaced instead of recovered.** Round 18 proposed retiring the
  L-test's unverifiable half; round 21 re-measured it on a committed set instead, because a fix made
  three rounds earlier for an unrelated reason had made the inputs reproducible.
- **A relative gate needs bounds at both ends.** The 5× clashscore ratio was guarded above
  `pre ≈ 20` and not below; at `pre = 0` it is undefined and fires on a model well inside the
  absolute quality bar.

## Open

**Round 21 closed both remaining items.**

The **L-test** was re-measured rather than retired. Round 18 had proposed dropping its unverifiable
figures; round 19 spotted that the inputs were already committed, and round 21 ran it: Wilson B's
committed 24-dataset set regenerates L-test inputs, giving a measurement anyone can reproduce from a
clean checkout. It agrees with the historical 27 on **every** quantity — median |Δ| 0.0065 vs 0.006,
22/24 vs 25/27 inside ±0.02, max 0.047 vs 0.047, twin call unanimous both times. Both breaching
datasets turned out to be among the five the old trail named, so the breach evidence was recoverable
even though the denominator was not. The original 27 remain unreconstructable; the row simply no
longer rests only on them.

The **EM benchmark** now appends each entry's result as it completes, on all five exit paths. The
last all-or-nothing step in the pipeline is gone — a crash nine hours into a batch no longer takes
the completed entries with it. Tested by simulating a crash at entry 3 of 5.

### Where the remaining risk is

**No item is open.** The registry's live gaps are the ones that cannot be closed from here, and they
are listed below rather than as tasks. For anyone picking this up, the three worth knowing:

- **Six rows are still `⚠ partial record`** (H-placement, Ramachandran/rotamer favored %,
  Ramachandran/rotamer outlier %, §4 ΔRMSD, §4 geometry Δ, §4 map-model). Each quotes a figure from a
  set that cannot be rebuilt. The L-test showed one route out — re-measure on a committed set rather
  than recover — and it worked because a sibling benchmark's set happened to be committed. **Check
  whether the same trick applies to the others before assuming it does not.**
- **The §4 X-ray band widths still rest on ~11 entries named nowhere.** Round 20 re-measured what it
  could (16 of 37) and both clauses held, but the two quoted maxima that actually size the bands come
  from the lost batch.
- **The `d_FSC_model` band still rests on one verified extreme**, 10BU at +4.786 %, 3.24× above
  anything else on record. It is real and reproducible, so the band stays — but a single entry is
  what stands between it and a re-fit.

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
- **Rounds 17–18 self-corrections** *(no issue raised; recorded in the round trails and PR #69)*.
  Three, all of the same family as #57/#59/#61/#63 — a published figure that did not survive being
  checked:
  - **`d_FSC_model`'s worst degradation is +4.786 %, not +4.787 %.** The old value came from
    recomputing the ratio out of intermediates already rounded to 4 dp during round 16's backfill.
    Logged because it is *the* number setting the thinnest band in the file, and it was not the
    number the pipeline produces. Headroom 1.0445× → 1.0448×; no verdict changed.
  - **Round 17's DockQ "partial record" mark was wrong**, and round 18 withdrew it. The audit
    inferred unpublished mappings from a `limit=8` in the code; re-running showed the cap was never
    reached. Logged because it retired an *audit finding* rather than a tolerance — the first time
    this series over-reported a gap rather than under-reporting one.
  - **Round 17's row-count correction was itself a miscount.** It reported "20 rows, not 21" and
    blamed the shared map-model row; §3+§4 really do hold 21 rows, and the exception is the
    `[literature]` absolute-floors row. Reconciled in round 18: **21 rows, 20 `[benchmark]`, 21
    benchmarked tolerances.** Logged because the wrong explanation had already propagated into four
    files before it was caught.
