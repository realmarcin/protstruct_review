# Lessons from twenty-six rounds of tolerance benchmarking

The reusable output of the benchmarking series in `ref/research/tolerance_benchmark_*.md`. Extracted
from `NEXT_TASKS.md` (#65), which had become 49 % preamble before its first task — these are reference
material, not a backlog.

**Record new lessons here**, one paragraph each, newest first, naming the round and the specific
mistake that produced it. A lesson with no incident behind it is a maxim, and this file is not for
maxims.

## Index

| Rule | Round |
|---|---|
| A default bucket makes "unrecognised" and "miscounted" independent | 26 |
| Register the consequence you will check, not one you assume follows | 26 |
| A guard must assert against the artefact it polices | 25 |
| Review the code that makes the number, not only the number | 25 |
| Catching a class three times by luck is not a process | 24 |
| A gate that only compares numbers is defeated by a rewrite | 24 |
| Price the sampling before promising the test | 23 |
| An interval on an observed rate is not a test of that rate | 23 |
| Whether a subset re-run helps depends on which members were lost | 22 |
| A failed mechanism hunt can still leave a testable successor | 22 |
| A lost set can sometimes be replaced instead of recovered | 21 |
| Worst-case tabulation predictably keeps the breaches and loses the denominator | 21 |
| A relative gate needs bounds at both ends | 20 |
| A clause nobody re-tests is not a clause that held | 20 |
| A reproduced extreme is binding, not disposable | 19 |
| A prediction confirmed once describes the round that confirmed it | 19 |
| Confirm a suspected gap by running, not by reading | 18 |
| When the set grows, re-test every clause it backs | 18 |
| An attrition rate needs its denominator, so record what passed | 18 |
| Check the power before hunting the mechanism | 17 |
| Registering a prediction does not protect you from registering a bad test | 17 |
| Recoverability is an accident unless the script commits its input set | 17 |
| A reimplementation must be validated against the tool it stands in for | 17 |
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
hypothesis, and in this repo the hypothesis lost 21 times out of 21 — that 21 is the count of
benchmarked *tolerances*, which is one more than the 20 `[benchmark]` *rows* because the map-model
row carries both CC_mask and `d_FSC_model`. Round 6 adds a corollary —
**a "blocked" item is also a hypothesis**. Two of the three blockers dissolved on re-examination:
`reduce2` reports flips once `add_flip_movers=True` is passed (it defaults off), and the §4
false-negative side was testable all along by damaging models rather than refining them.

Round 7 adds the third: **a band this repo measured is a hypothesis too, outside the regime it was
measured in.** Round 8 adds the fourth, and it is about explanations rather than numbers: **a
mechanism inferred from two data points is a hypothesis.** Round 7 explained a degenerate
`d_FSC_model` as a coverage problem on n = 2; round 8 refuted it with four more entries. The number
(1 of 6 entries fails) survived; the story did not.

Round 26 tested three of round 25's parting claims and the interesting result was a prediction that
failed in a way I had not allowed for: **a default bucket makes "unrecognised" and "miscounted"
independent.** The `status` column of the EM per-entry file had no declaration anywhere — it existed
only as prefixes tested by four predicates in the reader, while the writer that produces the values
lived in another file. 28 of its 97 rows match none of those prefixes. Every published denominator is
nonetheless correct, because `attempted` is defined by *subtraction* (`not startswith("skipped")`), so
an unrecognised status joins it by default and for those rows that is genuinely right. The count is
correct by luck of the default, and stays correct until a status arrives that does not belong there.
A vocabulary is now declared once, beside the writer, and imported by the reader.

Its companion is about the pre-registration itself: **register the consequence you will check, not one
you assume follows.** The prediction read "0 rows outside the vocabulary — and if violated, at least
one published denominator is wrong today". Those are two claims, and the second does not follow from
the first; I registered them as one. The falsification criterion was therefore untestable as written,
and a prediction whose failure condition is wrong cannot be falsified honestly. Round 17 taught this
series to check power before hunting a mechanism; this adds that the *consequence clause* of a
prediction deserves the same scrutiny as its point estimate.

Round 25 audited the scripts rather than a tolerance, and found the guard round 24 had just built
could not fail. **A guard must assert against the artefact it polices.** `nesting_check()` derived
four counts from the per-entry TSV and compared them *to each other*; both sides came from one file,
and the inclusions hold by construction of the writer that produces it — `append_results` gives every
`skipped:` row an empty delta and every `measured` row a value — so no run of the pipeline could
produce a file that failed the check. It could fire only on a hand-edit. Meanwhile the three figures
it recomputed were pinned to no literal in the registry at all, so any one of them could drift alone
while the ordering survived. The test that matters now asserts the *old* behaviour explicitly: drift
59 → 61 and the ordering check still reports `OK`. When writing a check, ask what it reads and what
it compares against — if both come from the same place, it is a tautology with a status field.

Its companion is why the defect survived twenty-four rounds: **review the code that makes the number,
not only the number.** Every round re-read the registry adversarially and re-derived its figures; the
scripts computing them were read once each, when written. The first systematic pass over `scripts/`
found twelve defects, four of them high: the guard above, a `structure_ref` check promised in a
docstring and never written, a truncated DSSP run accepted because a guard said `and` where it meant
`or`, and a benchmark that dropped entries whenever a third-party API faltered and recorded nothing.
A fifth, only medium, had a wwPDB parser fabricating `0.0` violations where the real figure is 17.4.
None of these is subtle; they were simply never looked for. Note also what the round did *not* earn: three of the six silent-failure paths fail
in the flattering direction, one in the alarming one, two neither — a tendency, not the rule it would
have been satisfying to report.

Round 24 is about when to stop fixing instances: **catching a class three times by luck is not a
process.** The registry quotes figures derived from a per-entry file that grows every round, and three
times one of them was found to have aged — #72 (ρ over "44 entries", round-16 vintage), #107 (the
CC_mask statistics still at n = 25 after the set reached 35), #113 (a count whose stated definition
yielded 93 rather than the 69 it claimed). **Every one was found while reviewing something else.**
Each was fixed as an instance; nothing was added that would find the fourth. The round's output is
therefore a gate — `scripts/check_registry_figures.py`, wired into `validate.sh` — that recomputes
each dataset-dependent figure and fails when the text no longer matches. By this repo's own triage
ranking a defect class with no guard outranks the defects themselves, because it hides them; the
signal to build the guard is the second recurrence, not the third.

A gate's scope is narrower than it sounds, and round 24 proved it on itself: the round built the
staleness guard and then **shipped a fourth instance of a neighbouring class the guard did not
cover** (#115 — nested counts that do not nest, since 63 counted 4 rows the 69 excluded). Every
figure passed its own check because every figure was individually right against the data; nothing
compared them to *each other*. When adding a guard, state what it does **not** cover as carefully as
what it does, and expect the next instance to arrive just outside that line.

Its companion is about how such a gate gets defeated: **a gate that only compares numbers is defeated
by a rewrite.** The check therefore fails in two ways — when the recomputed value differs, and when
the quoted literal has *disappeared* from the registry. A reworded claim cannot be silently correct,
because nothing verified it; it is flagged for a human instead. This makes the gate brittle on
purpose, and rewording a covered figure will fail the build — which is the cost of the guarantee, and
cheaper than the alternative that has already happened three times.

Round 23 adds the cost half of round 17's power lesson: **price the sampling before promising the
test.** Round 22 specified a successor test and called it cheap because the selector was measurable
before refinement — which was true and beside the point. The candidates it needs occur at a **3.3 %**
base rate, and screening **24** entries (24 map downloads, hours of `mtriage`) found **none**, which
is a one-in-four outcome at that rate and tells you nothing you did not already know. Getting three
candidates needs ~60–90 screened entries. Round 17 taught this series to check the *statistical* power
before hunting a mechanism; round 23 adds that the *sampling* cost deserves the same arithmetic, and
that "the selector is cheap to measure" is not the same as "the experiment is cheap to run".

Its companion is a smaller methodological point that cost this round its gate: **an interval on an
observed rate is not a test of that rate.** P0 predicted the base rate would land in 3–15 %; it came
out at 0 %, so P0 was falsified — and 0/24 is *entirely consistent* with the 5.6 % prior (Fisher
p = 0.512, 95 % CI [0 %, 14.2 %], and a 25 % chance of seeing zero). The prediction was falsified while
the thing it was meant to detect was not. That is round 17's "registering a prediction does not
protect you from registering a bad test", recurring in a new shape: predict the *comparison* you
care about, not an interval around a point estimate whose sampling variance you have not accounted
for.

Round 22 qualifies round 21's route with the question that decides whether it works: **whether a
subset re-run helps depends on *which* members were lost, not how many.** The L-test's missing
datasets were unremarkable middle-of-distribution ones, so re-running the committed subset reproduced
the published figures closely. The flip-set row looks similar — 12 of 17 committed — and is the
opposite case: the five missing models are exactly those with **zero** disagreements, so they
contribute nothing to the numerator and everything they have to the denominator. Re-running the 12
would reproduce all 48 disagreements over fewer than 639 residues and report a **higher** rate than
the published 7.5 %, and anyone comparing the two would see a discrepancy that is purely an artefact
of which models survived the record. So that row keeps its mark and does not get a re-run — a result
rather than a deferral. Before applying round 21's trick, ask what the lost members contributed: if
they are the denominator, the trick manufactures a contradiction instead of resolving one.

Round 22's second is about what a failed hunt is worth: **a failed mechanism hunt can still leave a
testable successor.** The fourth hunt in this series failed like the first three — the proposed
predictor for 10BU's excursion (how far the FSC crossing starts beyond the map's own resolution)
correlates at ρ = +0.346, p = 0.039 over 36 entries and **fails on removing either of the top two**.
That is n = 2, and round 8's rule applies by name. But unlike rounds 7, 15 and 17, this one ends with
a **sharp, pre-specifiable test**: the predictor is measurable *before* refinement, so a future round
can select entries on it without circularity and check whether they move more. The difference is not
that the hypothesis is better — it is that the quantity is observable in advance, which is what makes
a hypothesis cheap to kill. When a hunt fails, ask whether it leaves something selectable; that is
worth more than the correlation would have been.

Round 21 adds the cheerful counterpart to three rounds of record-loss lessons: **a lost set can
sometimes be replaced instead of recovered.** The L-test row reported 27 datasets and named 5, and
round 18's proposal was to *retire* the unverifiable half. But the script's inputs are whatever a
prior Wilson B run leaves in a cache, and **Wilson B's set had been committed in round 18** — so
re-running it and then the L-test over the same cache produced a **24-dataset measurement anyone can
regenerate from a clean checkout**, returning the historical figures (median 0.0065 vs 0.006, 22/24
vs 25/27 inside the band, max 0.047 vs 0.047, twin call unanimous both times). Read that as
**reproducibility, not corroboration** — the 24 is almost certainly a subset of the 27, so it is the
same structures through the same deterministic programs, and this round's first draft wrongly called
it an independent measurement. The original 27 are still gone; what changed is that anyone can now
regenerate the numbers the row quotes. Before
retiring an unverifiable figure, check whether the measurement can simply be made again — the answer
here depended on a fix made three rounds earlier for an unrelated reason.

Its companion sharpens three rounds of record-loss lessons rather than softening them: **worst-case
tabulation predictably keeps the breaches and loses the denominator.** The L-test's two breaching
datasets are named outright in the old trail — *"2 / 27 (30IZ +0.030, 9PLC −0.047)"* — and all five it
tabulated reproduce to the published digit. That looks like luck until you notice it is forced:
breaches are by construction the largest-magnitude entries and a worst-cases table is sorted by
magnitude, so **any worst-N table contains every breach whenever breaches ≤ N**. For a one-sided
band, whose evidence *is* its breach count, the surviving half is therefore the half that matters —
predictably, and without anyone intending it. The denominator is what reliably dies, which is why the
*rate* still cannot be checked while the *breaches* can.

Round 20 adds a rule about the *shape* of a gate rather than its size: **a relative gate needs bounds
at both ends.** §4 gates clashscore degradation on the ratio `post / pre ≥ 5×`, and the clause
carefully documents that it fails *above* `pre ≈ 20`, where damage drives clashscore to ~100 whatever
it started at. It says nothing about the bottom. Round 20 found the limiting case on its first pass
through the recoverable set: **9LLO starts at clashscore 0.00**, so the ratio is undefined and any
clash at all reads as infinite degradation — on a model whose post-refinement clashscore is **0.67**,
comfortably inside the registry's own ≤ 4 quality bar. Three of 16 entries are fragile enough to trip the gate at a
post-clashscore within 2× that bar, and the fragility is **systematically high-resolution** (median
starting clashscore 2.28 below 2.5 Å against 8.96 above), so the models the gate mis-serves are the
good ones. A ratio is only meaningful over the range where its denominator is; when a quantity's
floor is zero, the gate needs a floor too. Note the asymmetry that hid this: the clause was written
from experience with *bad* models, and its author guarded the end they had seen.

Its companion is about how long an untested clause keeps its credit: **a clause nobody re-tests is
not a clause that held.** The rotamer band and the clashscore gate went **eleven rounds** without an
entry added, while the set they were quoted against grew 19 → 37 and every round re-validated only
the two clauses it happened to be working on. When round 20 finally ran them, both held and both
published worst cases reproduced exactly — so the outcome was benign. That is luck, not process: the
same eleven rounds of silence would have looked identical if one had been breached at entry 20.
Round 18's rule says re-test every clause the set backs; this is the reason it is worth the cost.

Round 19 adds the rule that decides what to do with an inconvenient number: **a reproduced extreme is
binding, not disposable.** `d_FSC_model`'s band exists for one entry — 10BU, +4.786 % — which now
stands **3.24× above the next-largest degradation ever recorded and 30.6× the median**, and whose own
3.0–3.5 Å window has since been sampled 22 times with a second-worst of +0.277 %, seventeen times
smaller. Every instinct says outlier, drop it, tighten the band. **Round 17 had already re-run 10BU
from a clean directory and got a byte-identical refined model**, so it is not an estimator artefact
or a bad run: it is a real degradation that a tighter band would fail on immediately. Reproducibility
is what converts an inconvenient observation from *suspect* into *binding*. The useful output is not
a smaller band but a precisely located one — `× 1.05` sits 1.0448× above one verified extreme and
~18× above everything else, and knowing that is worth more than pretending the extreme away.

Its companion is about how long a confirmation lasts: **a prediction confirmed once describes the
round that confirmed it.** Round 16 registered "the largest `d_FSC_model` degradation exceeds 1.1 %",
confirmed it at +1.476 %, and concluded that the large-degradation tail **"was sampled thinly rather
than being thin"**. Round 19 registered the identical threshold, sampled the same low-resolution
regime with ten fresh entries from ten distinct publications, and **falsified it** — both degradations
came in at +0.012 % and +0.277 %. Pooled, the answer is both halves at once: 2 of 8 recorded
degradations exceed 1.1 %, so the tail was under-sampled *and* it is thin. This is the "a band is only
as good as the last entry added to its set" rule applied to a *finding* rather than a tolerance — and
the fix is the same, re-register rather than cite.

Round 18 adds a correction to round 17's own audit, and it points the opposite way from everything
else here: **confirm a suspected gap by running, not by reading.** The audit marked the DockQ row a
partial record because the script's `plausible_mappings(..., limit=8)` could score eight mappings per
complex while the trail showed six — so two looked computed and unpublished. Re-running on the
now-committed set shows `limit` is a cap that was never reached: 4HHB has 4 plausible mappings and
1BRS has 2, `n_mappings_scored` equals what was published in both, and every value reproduces
exactly. The row is a full record and the mark is withdrawn. Inferring a gap from a bound in the
*code* is the same error as inferring a distribution from a published *extreme* — reading an upper
limit as a quantity. This series is well practised at doubting numbers; it should doubt its own
suspicions on the same terms, and it was cheap to check.

Round 18's second is about coverage when a benchmark grows: **when the set grows, re-test every
clause it backs, not just the one you are working on.** Round 17 spotted that the §4 geometry row
says 19 entries where the ΔRMSD row above it says 37 and could not tell which was stale. Tracing the
*rounds* rather than the *rows* answered it: the ΔRMSD figure is right, and rounds 8, 10 and 11 grew
the set 19 → 26 → 32 → 37 while re-testing **only the Cα-shift and favored clauses**. So the
rotamer-outlier band and the 5× clashscore gate have not been checked since round 7, against a set
that has since nearly doubled — and the tempting reading that "19" is really the `< 2.5 Å` branch is
ruled out, because neither clause was ever resolution-split. What looked like a stale *count* is
actually two *untested clauses*, which is a materially different claim. Each round naturally
re-validates the band it is widening; the siblings sharing that set go quietly unchecked, and nothing
in the file says how long it has been.

Round 18's third is about which half of a record to keep: **an attrition rate needs its denominator,
so record what passed, not only what failed.** Fetch-stage rejections were landing in a JSON inside a
temporary cache, so the two screens — which now reject most entries *before* any refinement — were
producing evidence that did not survive the round. Recording only the rejections would have fixed
half of it and left the rate unrecoverable, which is the numerator-without-denominator shape that
round 16's biased prior already demonstrated. `em_fetch_attrition.tsv` records kept and rejected
alike, with the charge and ligand inventories the screens actually saw. Six models found on disk in
old caches are backfilled as `unrecorded` rather than as rejections: the screen verdicts on them were
computed in round 18 and are not the reason they were dropped at the time, and writing a plausible
reason into a record is how a record stops being one.

Round 17 adds the rule that should run *before* any of the others about mechanisms: **check the power
before hunting the mechanism.** The backlog asked why round 15 degraded CC_mask in 4 of 8 entries and
round 16 in 1 of 9 — a four-fold rate difference across two adjacent windows. Registered as the gate
on that item, **P0 asked whether the difference was real at all, and it is not: Fisher's exact test
gives p = 0.131.** Holding those rates, the comparison first clears 0.05 at **20 entries per round**;
rounds carry 8–9. The question was unanswerable before any predictor was chosen, and the two earlier
mechanism hunts (round 7's coverage story, round 15's clustering story) were also launched at a
phenomenon nobody had first shown to exist. The score for mechanism hunts here is **0 for 3**. When a
round proposes to explain something, size the effect and the sample first; if the phenomenon is not
established, the mechanism cannot be.

Its companion is uncomfortable, because it is a limit on this file's own favourite rule:
**registering a prediction does not protect you from registering a bad test.** Round 17's P2 —
that CC_mask Δ correlates negatively with the starting CC_mask — was registered in advance and
**held**, at ρ = −0.445, p = 0.026. It is still wrong. Correlating a *change* against its own
*baseline* is negatively biased by construction, because the baseline sits on both sides of the
comparison with opposite signs. Under Oldham's correction (change against the *mean* of the two
measurements) it collapses to p = 0.18; ρ(post, Δ) is −0.05; and it fails leave-one-out. Registration
stops you fitting a story to the data. It does nothing about a test that was the wrong test when you
wrote it down — so state the test's known artefacts in the registration, where they can be checked
against the result rather than invented after it.

Round 17's audit of every `[benchmark]` row generalises round 16's record lesson one level up:
**recoverability is an accident unless the script commits its input set.** Of the 20 `[benchmark]`
rows — §3 and §4 hold 21 tolerance rows, but §4's absolute geometry floors are `[literature]` — eleven
were fully backed, two recoverable, and **seven quoted a figure from a set that cannot be
reconstructed** —
not because anyone chose to record less, but because only four bench scripts hardcode the entries
they ran on. The rest take `--ids-file <ids.json>` or glob an uncommitted cache, and no `ids.json` is
committed anywhere in this repo. Where a row *is* recoverable it is because an author happened to
paste a table into the audit trail. The most expensive instance is the two §4 X-ray bands: **+0.35 Å**
and **−6 pp** are each set just above a null maximum (0.285 Å, 5.26 pp) produced by ~11
low-resolution entries that are named nowhere. Round 16 fixed this for the EM benchmark's *values*;
the *inputs* of every other benchmark are still in the position round 13's entries were in.

And one about building tools rather than measuring with them: **a reimplementation must be validated
against the tool it stands in for.** Round 17 moved the unparameterised-ligand skip off the expensive
path by checking components against PHENIX's monomer libraries at fetch time — a reimplementation of
what cctbx does at refinement. A file-existence check alone looked right and was not: DT, DA, DC and
DG are in neither library under those names, so it flagged every DNA chain, reporting 1431 atoms on
28JV where 38 had actually failed. Checked against `phenix.pdb_interpretation` over all 37 cached
models the corrected screen agrees exactly, including atom counts. A screen that silently drifts from
the tool it replaces is worse than no screen, because it rejects entries that would have refined.

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
deposited model sits at its optimum, but 10DP gained **+0.1476** on a null re-refinement (round 19; 10EH's +0.1268 in round 15 was the previous worst) — more than twice the
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
