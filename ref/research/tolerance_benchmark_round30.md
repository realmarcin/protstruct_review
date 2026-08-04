# Tolerance benchmark — round 30: the proposed convention addresses one failure in five

Round 28 measured the round trails at ~6.2 % wrong against the registry's ~1.1 %, proposed a
convention — *a figure in a finished trail is a historical snapshot and should be written as one* —
and deliberately deferred it. This round asks whether that convention targets the dominant failure
**before** writing it. Predictions registered in `tolerance_benchmark_round30_preregistration.md`,
in a commit containing no results.

**It does not.** The convention addresses **6 of 30** classifiable figures — one in five.

**No tolerance, band or measurement changed.** Nothing was implemented.

## The classification

Every figure found wrong across rounds 24–29, classified against the **committed record** — the
introducing document, the data file as it stood, `git log` — with the evidence named per figure.

| | count | share of decidable |
|---|---:|---:|
| **WRONG-AT-WRITE** — never correct | **24** | **80 %** |
| **STALE** — correct when written, rotted | 6 | 20 % |
| **UNDECIDABLE** | 4 | — |
| total | 34 | |

## P1 — "stale does not reach a majority": **confirmed**

Six of thirty. The four errors round 28 found split two-two, which is what motivated predicting no
majority; the wider population is far more lopsided than that sample suggested.

The six stale ones are worth naming, because they are a coherent kind: `Twenty-four rounds` as rounds
accrued; round 26's `12 checked` as the gate's own output grew; the `2.2–6.1 Å` range as the entry set
grew; `Ten issues` as a further issue was filed during review of that very fix. **A convention would
help each of them** — they were true, and nothing marked them as of-a-moment.

One is a kind round 28 did not anticipate: **#172's header rotted because a *sibling edit* moved its
pair**, not because any data changed. A dated snapshot would not have saved it.

## P2 — "the dominant cause is a count restated from memory": **confirmed**

Of the 24 wrong-at-write figures:

| cause | count | share |
|---|---:|---:|
| a count restated from memory when the source was one command away | **15** | **62 %** |
| an incomplete edit — headline changed, body left | 9 | 38 % |

## P3 — "more than two undecidable": **confirmed**

Four, and the reason matters: **squash-merging destroyed the evidence.** Each round lands as one
commit — round 25's ~20 intermediate commits are gone, and every round branch is deleted on merge. So
for a figure written mid-round, the state it was written against cannot be recovered.

Two of the four are unanswerable for that reason (`42 guard checks`, which lived in a **PR body** —
not a file in the repo at all — and 10RI's `+0.45 %`, whose round-15 source state is unretrievable).
**The repo's own merge convention makes staleness unauditable**, which is a cost of squash-merging
nobody had priced, and it applies to every future round equally.

## What this means for the proposal

**The convention should not be written as the primary intervention.** It addresses 20 %. This is the
second consecutive round to decline the work that motivated it after measuring — round 29 on the
per-entry gate, this one on the snapshot convention.

The uncomfortable part is what the 80 % points at:

- **62 % — counts restated from memory.** The remedy already exists and is *already a stated rule of
  this repo*: **every figure a document quotes must come from a committed, re-runnable script**. It
  was not followed, fifteen times.
- **38 % — incomplete edits.** The remedy also already exists: round 28's **sweep, verified by
  absence and by quantity rather than by string** (#170, #172).

**Both dominant causes have known remedies that were simply not applied.** The gap is adherence, not
invention — which is a less satisfying finding than a new convention and a considerably more useful
one. Adding a third rule to a set already not being followed would have been motion rather than
progress.

## Scope limits

- **This classifies figures already known wrong.** It says nothing about the rate of undiscovered
  ones, which round 28 established is a lower bound regardless.
- **The stale/wrong-at-write split relies on my own judgement per figure**, recorded with its evidence
  but not independently adjudicated. Four are marked undecidable rather than forced.
- **It cannot show the convention would have worked** — only what fraction it *could* address. A
  reader still has to heed a dated snapshot.
- **Rounds before 24 are out of scope**; the issue record starts at #130.
- **The 62/38 cause split is a judgement about mechanism**, not a measurement. Some figures could be
  argued either way.
