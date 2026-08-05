# Tolerance benchmark — round 32: the inventory is exhausted and still cannot power the test

**No tolerance, band or measurement changed.** No registry figure is touched.

Round 31 verified 35 claims, found 0 wrong, and refused to call that an answer. Round 32 exhausted
the rest of the inventory under a stopping rule fixed in advance. **The test is still underpowered —
and it is now known that this population cannot power it at all.**

## Result

| | round 31 | round 32 adds | pooled |
|---|---:|---:|---:|
| claims verified | 35 | **23** | **58** |
| wrong at write | 0 | **2** | **2** |
| rate | 0 % | 8.7 % | **3.45 %** |

Round 28's comparison arm: **2.28 %** (7 of 307).

    P(>= 2 wrong | p = 0.0228, n = 58) = 0.382
    P(0 wrong    | p = 0.0228, n = 58) = 0.262
    n needed for a resolvable test     = 130

**3.45 % against 2.28 % is the direction P1 predicted and is not distinguishable from chance.** Two
wrong claims is what this base rate produces in 58 trials better than one time in three. The
difference is a coin landing the way you guessed.

## The two wrong claims

Both are real, both are in the population, and both were **introduced by a `Fix #` commit** — which
is the arm under test.

**1. `Fix #170` — today's range applied to round 12's set.** It wrote into `lessons.md`:

> *"…broke anyway at 3 of 21 entries — because the quantity ranges 2.06–4.35 Å over the recorded
> crossings…"*

2.06–4.35 Å is the range over **today's 36 crossings**. Round 12 had **21** entries and a range of
2.2–6.1 Å. The sentence was true of no set at the moment it was written. Filed as #171 and fixed by
`Fix #171` in the same PR. Round 31 never reached this line.

**2. `Fix #187` — the corrected rate, quoted at its old value, against the wrong denominator.** It
wrote into `lessons.md`:

> *"…measured "counts restated from memory when the source was one command away" at **62 % of all
> defects**."*

Two errors in eleven words, and the second is the interesting one:

- **62 %** is the pre-correction rate. `Fix #187` is *the commit that moved the population from 24 to
  27*, making the rate 56 %. It restated the figure its own diff invalidated.
- **"of all defects"** is the wrong denominator. The rate is of **wrong-at-write** defects (27), not
  of all classified figures (33). 15/33 is 45 %, which is neither number quoted.

Not live on `main` — corrected downstream. But wrong when written, in the population, by the arm
under test.

## P2 — the fork that this round can speak to

Round 31 registered P2: *the dominant cause is **scope**, not memory*, and could not test it with zero
wrong claims. With two:

| claim | cause |
|---|---|
| `Fix #170`'s range | **scope** — a correct figure (2.06–4.35 Å) attached to the wrong population (round 12's 21 entries) |
| `Fix #187`'s rate | **both** — 62 % is memory (the source was one command away), *"of all defects"* is scope |

So scope is implicated in **2 of 2** and memory in **1 of 2**. That is the direction P2 predicted, on
a sample of two, which settles nothing and is reported only because it was registered. **P2 remains
indeterminate.** A fork worth 2 observations does not move `round_figures.py`'s value either way.

Worth stating plainly, because it is the point: **`round_figures.py` would have caught neither.**
Deriving a count tells you the number; it does not tell you which population the sentence means. Both
failures here are of the sentence, not the arithmetic.

## P5 — registered, and it holds

**P5 predicted the exhausted inventory would yield fewer than 130 claims. It yields 58.**

155 claim-bearing lines produced 58 verifiable numeric claims — well under one every two lines, once
section numbers, code identifiers, quoted historical figures and prose without a checkable number are
excluded. Registering this in advance is what makes it a result rather than an apology.

**The consequence is the round's actual finding, and it is a stopping rule, not a number:**

> This population cannot answer the question. 33 `Fix #` commits contain 58 verifiable numeric claims;
> the test needs 130. Verifying the same lines harder cannot close a gap of 72 claims that do not
> exist. **The next round either widens the population or drops the question.**

Widening means PR bodies and issue text, which is where #204 and part of #187 lived — and which are
**not in the repo**, so they are not diffable, not gated, and recoverable only through the API. That
is a different measurement with different reliability, and it should be registered as one rather than
folded silently into this series.

## The four snapshot claims

Verified true at write, moved since. Recorded, not counted as defects:

| claim | then | now |
|---|---|---|
| *"352 backticks"* in `round26.md` | true | **380** |
| *"7 checked, 11 not"* | true | 15 checked, 11 not |
| *"12 checked, 11 not"* | true | 15 checked, 11 not |
| *"the registry has fourteen checks"* | true | **19** (14 + round 29's 5) |

Each is a count of a quantity the work itself moves. The last is the cleanest case for the snapshot
convention round 28 proposed and round 30 declined to write: `14 + 5 = 19` reconciles exactly, so
nothing was ever wrong — only undated.

## What verified correct

Beyond the pooled tally: PR #129's diff is **19 files** (so *"a 19-file audit round"* is right and
#135's *"20-file"* was the error); round 28's seven wrong claims split `2 + 2 + 2 + 1`; the severity
populations reconcile at every snapshot (`7+11=18`, `10+11=21`, `12+11=23`); #139, #140 and #142 are
all real issues; round 30's *"first version reported 24 / 6 / 4"* sums to 34 against a corrected 33,
which is right because one figure (`#177c`) left the population entirely; `6/33 = 18 %`; the
`15 + 9 = 24 against 27` description of #191; and `NEXT_TASKS`' round table is ordered 1–31, so
#178's fix still holds.

## Scope limits

- **n = 58 is the whole inventory, not a sample of it.** There is no more of this population to
  verify. That is a stronger statement than round 31's "lower bound" and a worse one for the question.
- **Single rater, no second pass.** Round 31's `#167c`/`#177c` inversion is direct evidence that
  one-reader classification drifts here. The two wrong claims were both independently checkable
  against a committed source, which is the weakest form of this concern, but the *correct* verdicts
  are not similarly protected.
- **PR bodies and issue text remain outside.** Structurally invisible to a commit-diff sweep.
- **Nothing is gated.** P1 indeterminate, P2 indeterminate, P3 has too few cases to have a chain
  depth, P5 confirmed. Rounds 29, 30 and 31 each declined to build on an unresolved premise; this
  round declines on the same grounds and additionally knows the premise cannot be resolved here.
