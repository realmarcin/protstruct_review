# Lessons from fifteen rounds of tolerance benchmarking

The reusable output of the benchmarking series in `ref/research/tolerance_benchmark_*.md`. Extracted
from `NEXT_TASKS.md` (#65), which had become 49 % preamble before its first task — these are reference
material, not a backlog.

**Record new lessons here**, one paragraph each, newest first, naming the round and the specific
mistake that produced it. A lesson with no incident behind it is a maxim, and this file is not for
maxims.

## Index

| Rule | Round |
|---|---|
| A selectively recorded history biases the priors built on it | 16 |
| Prose in an audit trail is not a record | 16 |
| Measuring a caveat can dissolve it | 16 |
| Read the tool's data table, not its error message | 16 |
| Register the prediction before the data | 15 |
| The band you are watching is not necessarily the band at risk | 15 |
| Fixing one instance of a failure class and leaving its siblings hides the class | 15 |
| Count what the clause can actually be broken by | 14 |
| The benchmark's own premise can fail | 14 |
| Frequency and magnitude can point at opposite resolutions | 14 |
| Check the clause's direction before measuring it | 13 |
| When a band keeps breaking, check its shape before widening again | 12 |
| Low headroom is worth noting but does not predict a break | 11, back-tested 13 |
| A band is only as good as the last entry added to its set | 10 |
| "Unmeasurable" usually means "not yet read properly" | 9 |
| A mechanism inferred from two data points is a hypothesis | 8 |
| A band this repo measured is a hypothesis outside its measured regime | 7 |
| A "blocked" item is a hypothesis | 6 |
| A tolerance that has never been run is a hypothesis | 1–5 |

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

Round 16 adds the rule with the widest reach, because it is about the record rather than any
measurement: **a selectively recorded history biases the priors built on it, not just the counts.**
Round 16 registered P2 — that the `d_FSC_model` 5 % band would hold — at "nearer 60 % than 90 %",
reasoning from the three degradation magnitudes then on record, 2 of 3 above 4 %. With every value
recorded the distribution is 1 of 6 above 4 %, median 0.240 %. The old sample contained the alarming
values *because* those were the ones worth writing down, so the risk looked four times larger than it
was. Round 14's counting rule says an entry count overstates evidence; this says a *partial* record
distorts probability, which is worse, because a count that is too big is visibly too big and a prior
that is too pessimistic is invisible.

Its cause is the second lesson: **prose in an audit trail is not a record.** Round 13 measured six
entries and named two. The other four cannot be re-run because nothing anywhere records what they
were — their *identities* were lost with a temporary cache, so the CC_mask degradation count is
permanently a range. An audit trail names the entries its author found interesting, which is exactly
the subset that cannot be used to recount anything. Per-entry values now go to
`ref/research/data/em_refinement_deltas.tsv` on every run, with the unrecoverable entries listed as
`LOST` rows: a gap that is visible can still bound a claim.

Round 16's third is round 9's rule turned on this repo's own hedging: **measuring a caveat can
dissolve it.** Round 14 recorded that Δ values near zero were "separated by less than the
measurement's meaningful precision" and it stood unexamined for two rounds, quietly making every
small degradation unclassifiable. Re-running a 33-minute `real_space_refine` showed the pipeline
reproduces CC_mask *exactly* at 4 dp — so there is no noise floor, no recorded Δ is an artefact, and
the caveat was withdrawn rather than confirmed. A caveat is a claim; this file's own standard applies
to it.

And a small one with an outsized payoff: **read the tool's data table, not its error message.**
PHENIX names only `O1-` when it aborts on an unsupported atom type, from which round 16 first
inferred that `N1+` was accepted. `cctbx.eltbx.e_scattering` holds **98 neutral elements and no ions
at all** — the error was naming one example, not the rule. Reading the table turned a recurring
mid-run failure into a fetch-time screen that costs nothing.

Round 15 adds the rule this file most needed, because it is about the *method* rather than any
tolerance: **register the prediction before the data.** Round 14 had to label its own p-values as
computed after noticing the pattern they described. Round 15 committed four predictions before the
refinements finished and two more mid-run, and it changed the outcome twice. P5 and P6 — that entries
sharing a publication behave alike — were **falsified**, and a permutation test then put
within-cluster agreement at p = 0.38. The finding they tested had already been written up, committed,
and built into the fetcher's default. Unregistered, it would have survived as a plausible story with
two supporting examples and two counterexamples quietly reframed; registered, it was withdrawn inside
the same round under a decision rule fixed before the test ran.

The corollary is about which prediction to make: **the band you are watching is not necessarily the
band at risk.** P3 was registered about CC_mask, which had broken in 3 of its 4 widenings. CC_mask
came through at 1.71× headroom while `d_FSC_model` — flagged only for a thin tail — took a +4.79 %
degradation against a 5 % band and now sits at **1.045×**, the thinnest margin in the file.

Round 14 adds the counting rule: **count what the clause can actually be broken by.** A one-sided
band (`post ≥ pre − x`) can only be breached by a degradation, so improvements are not evidence at
any magnitude. 44 EM entries carry 14–19 CC_mask degradations and 10 `d_FSC_model` degradations —
that is the evidence, and round 14 added 8 entries containing none of it. A round can therefore raise
every count in the tolerance row while strengthening nothing.

Two corollaries, both found the hard way. First, the *premise* can fail: the benchmark asserts a
deposited model sits at its optimum, but 10EH gained **+0.1268** on a null re-refinement — twice the
width of the band measuring it — so Δ mixes refinement noise with deposition headroom. Second,
**frequency and magnitude can point at opposite resolutions** (#61): degradation is more common below
3.0 Å but 3–7× larger above it, and only magnitude re-fits a band. Getting that backwards inverted a
widening recommendation.

Round 15 also adds a maintenance rule, learned from 10EN vanishing from a log with no result and no
error: **fixing one instance of a failure class and leaving its siblings is how the class stays
invisible.** Round 14 added failure-reason reporting to `real_space_refine` and left the two
measurement steps bare, so an entry that died in `map_correlations` simply disappeared between two
bracketed ids.

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
