# Next tasks

Backlog of substantive work not yet done. Mirrors the open GitHub issues; this file
carries the execution detail. Keep in sync — close a GitHub issue and check the box here.

**Last reconciled: 2026-08-06** (round 42; the "Open" section below was reconciled against rounds 37–42 and the Codex review). Rounds 17–18 merged as
[#69](https://github.com/realmarcin/protstruct_review/pull/69); rounds 19 and 20 followed in
[#82](https://github.com/realmarcin/protstruct_review/pull/82) and its successor. **Check the issue
tracker for open issues; this file does not mirror it in real time.** There is no CI in this
repo — `bash scripts/validate.sh` is the gate, and it must exit 0 before a merge.

## Where the tolerance work stands

Forty-six rounds of benchmarking have replaced inferred magnitudes with measured ones. Round 6 found
that **two of three "blockers" were wrong** — both mis-invocations rather than limits of a tool.
Round 7 then found that **two bands set in rounds 5 and 6 were themselves wrong**, fitted to a narrow
resolution range and breached by null re-refinement once low-resolution entries were included.

**Where the registry stands.** Round 17 audited every `[benchmark]` row and found **7 quote a figure
from a set that can no longer be reconstructed**; they are marked `⚠ partial record`. Round 18 fixed
the cause — **every `bench_*.py` now commits the set it ran on**, and `scripts/validate.sh` fails if
one does not. **17 rows are fully backed** (rounds 42 and 44 re-based every §4 `d_min ≥ 2.5 Å` X-ray figure — both band widths and the geometry row's clashscore null ratio / starting ceiling — off their lost sets onto the 44 named entries, fully backing the ΔRMSD and geometry rows; rounds 45–46 backed both vs-deposited geometry-% rows on the 42 named entries — **favored %** on named data, and **outlier %** by making the check per-shared-residue classification agreement rather than the denominator-sensitive raw % (#284)).

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
| 20 | [#86](https://github.com/realmarcin/protstruct_review/pull/86) (2026-08-02) | the two §4 clauses untested since round 7 re-measured: both hold, both worst cases reproduce exactly; the clashscore ratio gate found undefined at `pre = 0` and given a low-end guard; `phenix.refine` shown deterministic 8/8 |
| 21 | [#92](https://github.com/realmarcin/protstruct_review/pull/92) (2026-08-03) | L-test made re-derivable on a committed 24-dataset set instead of being retired — a subset re-run, so reproducible rather than corroborating; EM benchmark now writes per-entry results as it goes |
| 22 | (2026-08-03) | 10BU shown to be a genuine statistical outlier; a candidate mechanism supported but not established (n = 2), with the successor test specified; flip-set row shown **not** to be fixable by round 21's route |
| 23 | (2026-08-03) | crossing-quality test **could not be run at the 1.3 cut** — 0 of 24 screened; at the data-driven 1.074 fence one already-refined near-miss (10EU) leans against it; estimator characterised over 60 crossings; the fetcher's all-or-nothing write fixed |
| 24 | (2026-08-04) | staleness audit: the registry's `named entries` definition had drifted to yield 93 not 69; a gate now recomputes 8 dataset-dependent figures and fails on a stale value **or** a rewrite |
| 25 | [#129](https://github.com/realmarcin/protstruct_review/pull/129) (2026-08-04) | first systematic audit of `scripts/` itself — **12 defects** (#116–#127), 4 high, including a guard that **could not fail** (it compared four counts it derived itself and never read the registry) and a wwPDB parser fabricating `0.0` violations where the real value is 17.4. No tolerance changed |
| 26 | [#141](https://github.com/realmarcin/protstruct_review/pull/141) (2026-08-04) | tested round 25's three parting claims: **P1 and P3 confirmed, P2 falsified, P4 indeterminate**. Declared the EM `status` vocabulary once beside its writer; gated a round document's claims about its own findings. Six review passes found **14 defects** (#139–#153), several inside the round's own fixes. No tolerance changed |
| 27 | (2026-08-04) | gated the counts the summary files quote, after **9 miscounts** shipped across rounds 24–26; found the round-coverage gate merged one PR earlier had **two false passes** (an unrelated table, and a fenced example row) because it lived in shell and could not be tested |
| 28 | (2026-08-04) | **measured** the miscount class instead of gating it again: ~326 numeric claims swept by hand, ~307 verifiable, **7 wrong** (~2.3 %) + 3 contested. Two of four predictions falsified — self-contradiction does *not* dominate (2 of 7), and the gate-covered files are *not* where the errors are. The registry is **~5.7× cleaner** than the round trails, which have no gate at all |
| 29 | (2026-08-04) | set out to gate the registry's **per-entry** figures (12 aggregate, 0 per-entry, and both of round 28's registry errors were per-entry) and **did not**: P1 falsified — every derivable per-entry figure already matched — and **P2 indeterminate**, the derivable/underivable split flipping with the counting method (#182). Five checks ship, on P1 alone; the gate now states its own coverage |
| 30 | (2026-08-04) | classified every figure found wrong in rounds 24–29: **27 wrong-at-write, 6 stale, 0 undecidable** (corrected in #187 — P3 was reported confirmed and is falsified). Round 28's proposed snapshot convention addresses **1 in 5**, so it was **not written**. 56 % of the rest are counts restated from memory, against a rule the repo already has — **the gap is adherence, not invention** |
| 31 | (2026-08-05) | asked whether **corrections are more defective than the text they correct**. **Indeterminate — underpowered**: 0 of 35 verified claims wrong across 33 `Fix #` commits, but P(0) = 0.446 at round 28's 2.3 % base rate, and 130 verified claims are needed before zero is surprising. Three stale-by-nature counts, no wrong-at-write. Three copies of one pre-#187 figure outlived the correction that fixed the fourth — two live on `main` (#210), one in the tool built to prevent it (#209): **review is not a sweep** |
| 32 | (2026-08-05) | exhausted round 31's inventory under a stopping rule fixed in advance: **58 verifiable claims, 2 wrong (3.45 %)** against round 28's 2.28 % — the predicted direction, and `P(≥2) = 0.382`, indistinguishable from chance. **P5 confirmed**: the inventory yields 58, the test needs 130, so **this population cannot answer the question**. Both wrong claims were introduced by `Fix #` commits and both involve **scope**, which `round_figures.py` would not have caught |
| 33 | (2026-08-05) | exhausted the ungated arm — PR and issue prose, 109 bodies, 493 lines, **101 claims, 3 wrong (2.97 %)**. **P6 falsified in direction**: the ungated channel is *cleaner* than the gated one (3.45 %), so **the gating apparatus is not visible in the error rate**. P7 falsified (101 < 130), P2 falsified on pooled evidence (memory 3, scope 2). Pooled 5 of 159 = 3.14 % vs a 2.28 % base rate — a **0.86 pp** difference needing **~5,542 claims per arm**. **The question is closed as unanswerable here** |
| 34 | (2026-08-05) | ran the crossing-quality screen at the **1.074 fence** round 23 established: **0 of 13** above it, `P(0) = 0.408` at the prior rate — an underpowered draw, **not a refutation**. The blocker is the **query**, not cost: `--per-stratum 6 × 8 strata` offers only 48 candidates, so 2.5 GB bought 14 entries. Six tooling defects found by the canary and the batch (#226–#228, #230–#232), including `entries.json` **overwriting** itself and dropping a paid-for entry from the screen's denominator |
| 35 | (2026-08-05) | widened the query as round 34 said to — 160 candidates, **50 entries fetched** against round 34's 14 — and screened up the **first candidate** the project has ever produced, 7DZX at ratio 1.210. It does not survive inspection: `cc_mask_pre` **0.2083**, worse than every entry on record. **The fence is confounded with model-map fit** (#234) — 2 of the 5 entries ever above it barely fit their maps. Base rate revised **6.7 % → 4.5 %**, or **2.7 %** counting genuine candidates only |
| 36 | (2026-08-05) | pre-registration only — fixed the fit-quality exclusion (`cc_mask_pre ≥ 0.6038`, the Tukey fence over the record) **before** it could be fitted to 7DZX. What it leaves is the finding: the eligible, **non-circular** candidate pool for #224 has **one** member, 10EU, which already fails the 10× bar. Three such candidates needs **~330 screened, ~220 more** |
| 37 | (2026-08-05) | first **named** low-resolution X-ray set — 21 selected by query, **10 usable**. Bands hold; fresh maxima **0.1828 Å** and **2.61 pp** fall short of the lost 0.285 Å / 5.26 pp, which the registration said in advance is weak evidence. **P5 falsified**: the "not reproducible" clashscore 17.2 is ordinary — a fresh sample reaches **38.70**. 11 of 21 lost to three filed defects (#241–#243) |
| 38 | (2026-08-05) | round 37 with the selector fixed. The fix removed the selector-caused **excess attrition** — R-free refinement failures fell **7/18 → 1/17**, **14 of 17** refinement attempts usable against round 37's 10 of 18, 0 lost to nucleic acid — though ~30 % baseline loss (fetch rejects, non-R-free refine failures) remains, untouched by any selector. But an era-spread sample **breached the −6 pp favored band** for the first time: **6LE5 drops 6.28 pp** under a well-behaved null re-refinement, past the lost 5.26 pp. **P3 falsified** (the strong direction); P2 holds weakly (Cα max 0.2004 < 0.285, up from 0.1828); P5 falsified again (max 27.71). Band **not re-fitted** — widening deferred to a registered decision |
| 39 | (2026-08-06) | **arm 1 only.** Settled #253: the favored-band breach is an **unrestrained artefact**. Re-refined the round-38 set **with restraints** (no downloads): **6LE5's drop fell 6.28 → 2.21 pp** (P1), 11 of 14 entries improved and **no restrained entry breached** −6 pp (P2), median favored Δ +0.035 → +1.505. **Band kept at −6 pp** — the breach is specific to unrestrained refinement, not the low-resolution restrained protocol; §4 caveat strengthened. Arm 2 (fresh unrestrained set, P3) left registered and unrun; subsumed by #225 |
| 40 | (2026-08-06) | **answered #224** — the redesign. The crossing-quality mechanism is real, but the *ratio* was the wrong measure: over 19 entries its Spearman ρ with \|excursion\| collapses +0.319 → **+0.049** without the two extremes (2-point leverage), while **crossing determinacy (perturbation-recross) predicts robustly** — ρ **+0.792** extremes-removed (LOO 0.75–0.85), partial **+0.773** controlling for fit (P1, P3 confirmed, so not the #234 confound). **P2 falsified**: the excursion is real movement, 2–2900× the perturbation shift, not jitter. §4 caveat retired the n=2 ratio hypothesis; band unchanged. Resolved on existing labels, ~5 GB, no 50 GB screen. #224 closed, #234/#258 superseded |
| 41 | (2026-08-06) | **#225** — largest fresh X-ray set (round 39 arm 2): **20 usable of 25**, era-spread, excluding all 37 round-37/38 ids. **P3 falsified** (weak direction): worst favored drop **−1.85 pp**, nowhere near round 38's 6.28 — so **6LE5 is an isolated outlier**, 1 of **44** pooled fresh entries to breach −6 pp, and the one arm 1 showed restraints tame. Cα max **0.1849 Å** (< 0.2004 < lost 0.285). Both §4 X-ray bands hold; nothing re-fitted. Lost maxima still unreproduced — the *widths* rest on them, but the bands now have 44 fresh entries under them |
| 42 | (2026-08-06) | **#269** — re-based the §4 `d_min ≥ 2.5 Å` X-ray band *widths* off their lost maxima onto **coverage bounds over the 44 named entries** (research from #225: a lone observed max is a biased, least-robust, low-confidence basis; structural biology uses percentiles). **Cα band 0.35 → 0.25 Å** (99/95 lognormal UTL 0.2514, flags 0 of 44, better detection power); **favored kept at −6 pp** (round 39), re-justified as ~98% coverage. **Resolved the "most expensive partial record"** — 13→**14 backed rows**; the geometry row stays marked only for its clashscore figures. Re-runnable via `analyze_xray_band_coverage.py` |
| 44 | (2026-08-07) | **P3b triage item #1** — re-based the geometry row's last partial figures (clashscore 4.26× null ratio, 17.2 starting) onto the **44 fresh named entries**: max null ratio **4.25×** (37 gate-valid, none ≥ 5×; the figure that set the gate reproduces on named data) and starting clashscore reaches **38.70** (the lost "not reproducible 17.2" exceeded). **No band value changed**; the geometry row **resolves** — 14→**15 backed**, 6→**5 marked**. Five partial rows remain (triage: 3 remeasure, 1 cite round 21, 1 retain) |
| 45 | (2026-08-07) | **P3b items #3 + #4** — re-based the vs-deposited geometry-% rows on the **42 named entries** (`round45_ids.json`). The run first uncovered an **oracle bug** (#281/#282: rotamer outlier % was read from `key_validation_stats`' `protein_sidechains`, a broader metric inconsistent with the report's per-residue `rota=OUTLIER` verdicts — fixed, tested). On the corrected instrument: **#3 favored resolves** (median \|Δ\| **0.000**, band holds — 15→**16 backed**), **#4 outlier half-resolves** — Ramachandran ≤ 0.11 pp, rotamer exact on **39/41**, but **14ZZ (1.52 pp)** and 2YOL (0.57) breach ±0.5 for an **altloc denominator** reason (rotamer names agree exactly). Per the decision rule a breached band is a finding, not a widen — #4's mark **stays** (#284); historical rotamer "0.34 pp" superseded. **5→4 marked** |
| 46 | (2026-08-07) | **#284 closed** — settled the vs-deposited band question round 45 opened. The raw favored-/rotamer-% bands are denominator-sensitive under altloc/completeness, so the **load-bearing check is now per-shared-residue classification agreement** (do the pipelines assign the same verdict to residues they both evaluate?), robust to the denominator difference; raw-% `\|Δ\|` demoted to reported diagnostics. Rotamer OUTLIER-verdict agreement **1.0000 on all 41** and Ramachandran verdict agreement (new `ramachandran_agreement`, tested, keyed with insertion code) **1.0000 on all 41**; the stricter rotamer-*name* agreement is 0.9919 on 15C8 (three insertion-code residues, different names, all Favored — named). **#4 outlier row resolves** — 16→**17 backed**, 4→**3 marked** |

Per-tolerance detail lives in the audit trails under `ref/research/tolerance_benchmark_*.md` and in
the re-runnable `scripts/bench_*.py`. It is deliberately **not** duplicated here — a backlog that
accumulates a changelog stops being readable as a backlog.

**Lessons live in [`ref/research/lessons.md`](ref/research/lessons.md)** — forty-six rounds of
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
  19 → 37 while re-testing only two of its four clauses; the other two went untested from round 7
  until round 20 re-measured them (both held, both worst cases reproduced exactly).
- **A reproduced extreme is binding, not disposable.** 10BU sits 3.24× above every other
  `d_FSC_model` degradation, and round 17 proved it reproduces byte-identically — so the band stays
  where it is, precisely located rather than defended.
- **A prediction confirmed once describes the round that confirmed it.** Round 16 confirmed
  "largest degradation > 1.1 %"; round 19 registered the same threshold and falsified it.
- **Catching a class three times by luck is not a process.** Three aged figures (#72, #107, #113)
  were all found while reviewing something else. The signal to build the guard is the second
  recurrence, not the third.
- **Price the sampling before promising the test.** Round 22 called its successor test cheap because
  the selector was measurable before refinement. The candidates occur at 3.3 %, so screening 24 found
  none; three candidates need ~60–90 screened entries. A cheap selector is not a cheap experiment.
- **Whether a subset re-run helps depends on which members were lost.** The L-test's missing
  datasets were unremarkable; the flip-set row's are the zero-disagreement models, i.e. the
  denominator — re-running there manufactures a contradiction rather than resolving one.
- **A lost set can sometimes be replaced instead of recovered.** Round 18 proposed retiring the
  L-test's unverifiable half; round 21 re-measured it on a committed set instead, because a fix made
  three rounds earlier for an unrelated reason had made the inputs reproducible.
- **A relative gate needs bounds at both ends.** The 5× clashscore ratio was guarded above
  `pre ≈ 20` and not below; at `pre = 0` it is undefined and fires on a model well inside the
  absolute quality bar.
- **A gate that only compares numbers is defeated by a rewrite.** The staleness gate therefore fails
  in two ways: when the recomputed value differs, and when the quoted literal has *disappeared*. A
  reworded claim cannot be silently correct, because nothing verified it.
- **Review the code that makes the number, not only the number.** Twenty-four rounds re-read the
  registry adversarially; the scripts computing it had been read once each, when written. The first
  systematic pass found twelve defects, four high.
- **A guard must assert against the artefact it polices.** Round 24's nesting check compared four
  counts it derived *itself* from one file, and those inclusions hold by construction of the writer —
  so no run of the pipeline could fail it. If a check's inputs and expectations come from the same
  place, it is a tautology with a status field.
- **A default bucket makes "unrecognised" and "miscounted" independent.** 28 of 97 status values
  matched no declared predicate, and every denominator was still correct, because `attempted` is
  defined by subtraction. Right by luck of the default, and only until a status arrives that does not
  belong there.
- **Register the consequence you will check, not one you assume follows** — and a prediction
  resolvable only by a rule you invent afterwards was not a well-formed prediction. Round 26 wrote
  "0 rows outside the vocabulary, and if violated a denominator is wrong today" as one claim; they
  are two, and the second did not follow.

## Open

**Round 21 closed both remaining items.**

The **L-test** was re-measured rather than retired. Round 18 had proposed dropping its unverifiable
figures; round 19 spotted that the inputs were already committed, and round 21 ran it: Wilson B's
committed 24-dataset set regenerates L-test inputs, giving a measurement anyone can reproduce from a
clean checkout. It returns the historical figures — median |Δ| 0.0065 vs 0.006, 22/24 vs 25/27
inside ±0.02, max 0.047 vs 0.047, twin call unanimous both times — but that is **reproducibility, not
corroboration**: the 24 is almost certainly a *subset* of the 27, so the same structures went through
the same deterministic programs. Both breaching datasets were already named in the old trail, which
turns out to be structural rather than lucky — a worst-N table contains every breach whenever
breaches ≤ N. The original 27 remain unreconstructable; what changed is that anyone can now
regenerate the numbers the row quotes.

The **EM benchmark** now appends each entry's result as it completes, on all five exit paths. The
last all-or-nothing step in the pipeline is gone — a crash nine hours into a batch no longer takes
the completed entries with it. Tested by simulating a crash at entry 3 of 5.

### Open

**The two bounded measurement projects that dominated this section since round 22 are now done.** What
was "state as of round 27" — a menu of three candidates — has resolved into rounds 40–42:

- **Crossing-quality hypothesis (#224)** — **answered by round 40's determinacy redesign.** The ratio
  screen was 2-point leverage (Spearman ρ with |excursion| collapses to **+0.049** without the two
  extremes); a perturbation-recross *determinacy* measure predicts the excursion robustly (ρ **+0.792**
  extremes-removed, LOO 0.75–0.85) and independent of fit (partial **+0.773**). Resolved on 19 existing
  labels — no 50 GB screen. **#224 closed**, #234/#258 superseded, the §4 caveat re-based.
- **Fresh low-resolution X-ray measurement (#225)** — **done across rounds 37/38/41/42.** Rounds
  37/38/41 built **44 fresh named entries**; round 42 (#269) re-based the §4 `d_min ≥ 2.5 Å` X-ray band
  widths off their lost maxima onto **coverage bounds** over those 44 (Cα **0.35 → 0.25 Å**; favored kept
  at −6 pp, re-justified as ~98 % coverage), resolving the "most expensive partial record." **#225/#269
  closed.**

**What is open now** is the Codex conceptual-review action plan
([`ref/research/codex_review_action_plan.md`](ref/research/codex_review_action_plan.md)): **P1** — the
registry→consumer drift gate — shipped (#271); **P2** is this reconciliation; **P3** is a preregistered
**cross-version reproducibility round** (pinned `phenix-2.0-5936` vs a newer build), a **triage of the
remaining `⚠ partial record` rows**, and **shoring up the small-n load-bearing fits** (round 42's n = 44
lognormal, round 40's 19 labels); **P4** is explicit stopping/consolidation criteria for the round
cadence and its gate machinery.

The one **unbounded** option that persists from the old menu: **another `scripts/` audit pass with a
new lens** — it has found defects every time (12, then 2, then 5), the lens must differ each pass, and
there is no defined endpoint. Cheap per pass, unbounded in total; picking it is a deliberate choice to
spend a round on assurance rather than on measurement.

#### [x] Crossing-quality hypothesis — answered (round 40, #224)

Rounds 23–36 priced and screened this at the 1.074 fence and could not power it (0–1 candidate per
batch, ~50 GB for three). Round 40 stopped screening for the rare event and **measured the mechanism
directly** instead: crossing determinacy (perturbation-recross) predicts the excursion where the ratio
was 2-point leverage, so the §4 caveat is re-based and #224 is closed without the expensive screen. The
detail lives in `ref/research/tolerance_benchmark_round40.md` and the memo #258.

### Standing risk, not tasks

- **Three rows carry `⚠ partial record`** (rounds 42/44 resolved the ΔRMSD and geometry rows; rounds
  45–46 resolved both vs-deposited geometry-% rows — favored on named data, outlier by making the check
  classification agreement, #284). Round 21 showed one route
  out (re-measure on a committed subset) and round 22 showed its limit: **it works only when the lost
  members were unremarkable.** For the flip-set row it is established *not* to work — the five missing
  models are the zero-disagreement ones, so a 12-model re-run would report a higher rate than the
  published 7.5 % purely because the denominator shrank. Round 42 showed a *third* route for a band
  width: retire the lost maximum as the wrong estimator and re-base on a coverage bound over named data.
  Round 45 showed a *fourth* outcome: re-measuring can resolve the **record** (name the set, commit
  per-entry values) yet surface that the **band itself** fails on named data — the rotamer ±0.5 pp check
  is denominator-sensitive under altlocs. Round 46 then showed the *fifth*: when the raw band is the
  wrong instrument, **change what the check measures** — per-shared-residue classification agreement is
  robust to the denominator and resolved #4 (#284 closed). The remaining three: #2 L-test and #6 EM
  map-model are RETAIN; #5 H-placement is the one clean REMEASURE left. Ask what the lost members
  contributed before trying to re-measure.
- **The §4 X-ray band widths no longer rest on lost entries** (was a standing risk through round 41).
  Round 42 re-based both `d_min ≥ 2.5 Å` widths onto coverage bounds over the 44 fresh named entries
  (rounds 37/38/41), so the widths are now fully-backed, re-runnable figures. The two lost maxima
  (0.285 Å, 5.26 pp) are retired as the wrong target, not mourned as lost data.
- **The audit of `scripts/` is a lower bound, not a total.** Round 25 found 12 defects in the first
  systematic pass; round 26 found 2 more with a *different lens*, and a sixth pass — enumerating each
  guard's input space rather than reading — found 5 more in code the earlier passes had just
  reviewed. Reading finds the defect you can imagine. Nothing establishes where the bottom is, and
  the same argument applies to every further pass.
- **Two of round 26's guards are heuristics with stated residual risk.** `check_round_figures.py`
  decides "is this markdown a quotation" by inspecting a match's immediate context; it handles every
  construct these documents currently use and may be wrong on one nobody has written yet. And its
  findings record is a *snapshot* — any round that files an issue after refreshing it goes stale, as
  round 26 did three times. Both are recorded in that round's scope limits rather than implied closed.
- **`d_FSC_model` still rests on one verified extreme.** 10BU is an outlier by every criterion tried — **3.24×
  the next-largest degradation**, which needs no distributional assumption, and above the 1.5 × IQR
  fence under all three quartile conventions (3.017 / 2.370 / 1.724, on n = 8). It also reproduces
  byte-identically. Round 40 answered whether it is explicable: the excursion is **real model
  movement, not estimator jitter** (a controlled perturbation moves the crossing 2–2900× less than
  refinement did), and crossing determinacy predicts excursion magnitude — so 10BU's outlier status is
  genuine, and the band stays where it is.

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
