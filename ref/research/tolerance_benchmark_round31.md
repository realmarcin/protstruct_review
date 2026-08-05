# Tolerance benchmark — round 31: the correction rate could not be measured at this sample size

**No tolerance, band or measurement changed.** No registry figure is touched.

Round 31 asked whether **corrections carry a higher defect rate than the text they correct**. Seven
defects in a row — #187, #191, #194, #195, #201, #202, #204 — were all defects *in a correction*, in
a stretch of work whose entire subject was defect counts. If corrections are systematically worse,
the review-and-fix loop this repo runs is partly self-defeating.

**The answer is: not at this sample size, and the round says so rather than reporting the number it
got.** Round 23 is the precedent — a test that cannot be completed is not a test that came back
negative.

## What was measured

| | |
|---|---|
| population | **33** commits with subject `Fix #`, rounds 24–31 (PRs #114–#193) |
| claim-bearing `.md` lines those commits **added** | **155** |
| distinct numeric claims verified by hand against source | **35** |
| **wrong at write** | **0** |
| stale-by-nature (true when written, moved since) | **3** |
| wrong figures found live on `main`, **outside** the population | **2** (#210) |

The 39 `Fix #` commits across all merged PRs split 33 (rounds 24+) and 6 (rounds 7–23); only the 33
are pooled, because the comparison arm — round 28's ~2.3 % — was swept over rounds 24–27. That split
was itself #208, found reviewing the pre-registration.

**All 33 commits resolve locally**, and GitHub retains them after branch deletion — verified on #193,
whose branch is gone and whose three `Fix #` commits still resolve. The naive enumerator
(`git log main | grep '^Fix #'`) returns **3**, because squash-merging absorbs a correction made
inside a round's PR into a `Round NN:` subject. Registering the enumerator before the measurement is
what stopped this round sampling 3 of 39 and reporting a confident rate over 9 % of its population.

## The predictions

**P1 — the correction rate is higher than ~2.3 %. INDETERMINATE, underpowered.**

0 of 35 verified claims are wrong. That is **not** evidence corrections are clean: at round 28's rate
of 7/307 = 2.28 %, the expected number of wrong claims in 35 is **0.80**, and

    P(0 wrong | p = 0.0228, n = 35) = 0.446

Seeing zero is the *single most likely outcome* under the null. **130 verified claims** are needed
before observing zero would be surprising at p < 0.05, and this sweep verified 35. The measurement
does not distinguish "corrections are clean" from "the sample is too small to tell", and reporting
0 % as a rate would be exactly the error this round exists to study.

**P2 — the dominant cause is scope, not memory. INDETERMINATE.** No wrong claims were found, so there
is no cause distribution to classify. Registered as a fork on `round_figures.py`'s value; that fork
stays open.

**P3 — a correction-of-a-correction is more defective. INDETERMINATE**, same reason.

**P4 — at least one wrong claim is live on `main` in a correction commit's text. FALSIFIED on what
was swept**, with the same power caveat: 0 of 35.

## What verified, and against what

Everything below was re-derived, not read:

- **Round 28's two-arm table.** 227+99 = 326, 223+84 = 307, 220+77 = 297, 2+5 = **7**, 1+2 = 3;
  7/307 = 2.28 % → *"~2.3 %"*; 4/65 = 6.15 % → *"~6.2 %"*; 2/185 = 1.08 % → *"~1.1 %"*; and the ratio
  6.15/1.08 = **5.69** → *"~5.7×"*. My first recomputation of that ratio gave 6.86 and looked like a
  defect; it used 223 (registry **+ lessons.md**) where the claim uses 185 (registry alone). Recorded
  because *"a figure I could not re-derive"* is not the same as *"a figure that is wrong"*, and the
  difference is one grep.
- **Round 24's nesting**, against `em_refinement_deltas.tsv`: 97 rows − 4 `LOST` − 24 `screened only`
  = **69** named; measured 35 + delta-only 23 + d_FSC-only 1 = **59** attempted within the 69;
  59 + 4 `LOST` = **63**; **35** with full pre/post; **58** with a recorded Δ. Every figure in the
  sentence #115 was filed against now holds.
- **The 36-crossing range.** 36 rows carry both `d_fsc_model_pre` and `_post`; their pre values run
  **2.0565 – 4.3513** → *"2.06–4.35 Å"*, and all 60 rows with a `pre` run from **1.8679** →
  *"1.87 Å over all 60"*. 10BU's 4.3513 is the largest. The registry's corrected sentence is right.
- **The 1.074 fence.** 4 of 60 above it (6.7 %), 2 of 60 above 1.3 (3.3 %).
- **Round 30's classification**, by running the committed script: 27 + 6 + 0 = **33**; 27/33 = 82 %;
  6/33 = 18 %; 15 + 12 = 27; 15/27 = **56 %**; 12/27 = 44 %.
- **`gh pr view 129 --json commits` returns 6**, the figure #187 corrected *"~20"* to.
- **The gates' own output**: the registry check's *"19 checked … 5 per-entry"*, `spell()` covering
  20–99 and refusing 19 and 100 by name, and the enumeration `#164:1 #165:1 #166:2 #167:2 #169:1
  #170:5 #171:1 #172:1 #173:1` summing to **15**.

## The three stale-by-nature claims, and why they are not defects

| claim | when written | today |
|---|---|---|
| *"142 dangling commits present locally"* | true | **149** |
| round 26: *"12 checked, 11 not"* | true | **15 checked, 11 not** |
| round 26: *"7 of 18 severity claims checked"* | true | 26 claims, 15 checked |

None was wrong at write. All three are **self-referential counts of a quantity the work itself moves**
— which is #178's lesson (*"a count of your own defects has no fixed value while review continues"*)
arriving as data rather than as a rule. The third is explicitly flagged in its own document as having
been stale once already.

The actionable distinction: `142` and `15` are *snapshots stated without a timestamp*. Round 28's
convention — state the snapshot and its denominator, as `d_FSC_model` does with *"17 degraded — a
lower bound, not a count"* — would have made all three unfalsifiable-by-time. Nothing is gated on
that here, because a convention addressing 3 of 38 observations is the same one-in-five ratio round 30
declined to build on.

## The finding this round did not predict — and the draft it falsified

**Three live instances of the pre-#187 population survived. Two are on `main`.**

This section first read *"the one live instance of the class is in work that has not yet been
reviewed"*. Continuing the sweep found two more, both on `main`, and the sentence was wrong when
written — a claim about a search, made before the search finished. It is left recorded because it is
this round's own instance of the class it is measuring, caught by the round's own method rather than
by review.

`scripts/round_figures.py` — the tool built *specifically* to stop counts being restated from memory —
opened with *"15 of 24 wrong-at-write figures (62 %)"*. Derived: **27** and **56 %**. The 24/62 % pair
is the population from **before** #187 moved three undecidable figures into wrong-at-write (a fourth
left the population entirely) and #191
fixed the split still reading 15 + 9 = 24 against 27 — both merged in #184, *before* the file was
written. It is not a stale figure; it is a figure that had already been corrected twice and was
quoted anyway, in two places including a paragraph congratulating the tool for catching this class
(#209).

The other two are **live on `main`** (#210):

| where | says | the table or sentence beneath it |
|---|---|---|
| `tolerance_benchmark_round30.md:44` | *"Of the 24 wrong-at-write figures:"* | a table reading 15 + 12 = **27**, shares computed against 27 |
| `lessons.md:130` | *"6 stale against 24 wrong-at-write"* | *"Of the 27, 56 % were counts…"*, two lines below |

Both **were correct when written** — the classification did say 24 — and were made wrong by #187.
They are **stale**, not wrong-at-write, and both were introduced by a commit titled `Round 30:`, not
`Fix #`, so neither is in this round's population and neither changes the 0 of 35. What they change
is the reading:

> #191 corrected this figure in **one** location. Three others survived: two on `main` and one in the
> tool built to prevent exactly this. The failure is not that the correction was wrong — it is that
> its **sweep had a scope of one file**.

That is the *incomplete edit* cause — 44 % of round 30's wrong-at-write figures — and it is the third
time in this series that a fix moved a headline and left a body (after #170, #172), now measured
rather than noticed.

So the honest summary of the pairing is narrower than the draft's:

> Every one of the seven defects that motivated this round was caught by review, and the corrections
> that merged are clean on all 35 claims checked. But **review is not a sweep**: it catches the
> sentence in front of it, and three copies of one wrong figure outlived the correction that fixed
> the fourth.

Whether corrections are more defective *before* review than after is the hypothesis this suggests.
This round **cannot establish it**: no counterfactual, no measurement of pre-review text, and n = 35
against a 2.3 % base rate. Stated as a hypothesis, in the round that lacked the power to test its
predecessor.

## Scope limits

- **The sweep is 35 of 155 claim-bearing lines — 23 %.** A lower bound, not a defect density. The
  unverified 120 are not "presumed correct"; they are unmeasured.
- **The two arms are not perfectly comparable, as disclosed before the measurement.** Round 28 swept
  documents *as they stand*; this swept claims *as introduced by a commit*. A claim written wrong and
  fixed later is invisible to the first and visible to the second — an asymmetry that favours P1, and
  P1 still could not be supported.
- **Nothing causal.** If corrections were more defective, this could not say whether the cause is
  haste, narrowed attention, or harder subject matter.
- **Nothing is gated this round.** P1 is indeterminate, P2 and P3 have no data, and rounds 29 and 30
  both declined to build on a falsified or indeterminate premise. That precedent holds.
- **The population excludes PR bodies and issue text.** #204 was a defect in a *PR body*, and PR
  bodies are not in the repo. Two of the seven motivating defects (#204, and #187's in part) live
  there, so the sweep structurally cannot see the shape that produced them.
