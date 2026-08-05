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

| | count | share |
|---|---:|---:|
| **WRONG-AT-WRITE** — never correct | **27** | **82 %** |
| **STALE** — correct when written, rotted | 6 | 18 % |
| **UNDECIDABLE** | **0** | — |
| total | 33 | |

**These are the corrected figures (#187).** The first version reported 24 / 6 / 4 and called P3
confirmed; review showed all four "undecidable" figures were recoverable and three "stale" ones were
mislabelled. See the correction section below — the mistake is more instructive than the table.

## P1 — "stale does not reach a majority": **confirmed**

Six of thirty-three — 18 %. The four errors round 28 found split two-two, which is what motivated predicting no
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
| a count restated from memory when the source was one command away | **15** | **56 %** |
| an incomplete edit — headline changed, body left | 12 | 44 % |

**These moved after #187** and the first version did not move with them: the correction pushed three
figures into wrong-at-write and left the split reading 15 + 9 = 24 against a population of 27 (#191).
That is a fix moving a headline and leaving its body — the third time in this round's history, after
#170 and #172, and this time inside the section reporting that cause. **The cause now lives in
`classify_wrong_figures.py` as a column**, so the percentages are derived rather than restated; leaving
it in prose was the reason it went stale.

## P3 — "more than two undecidable": **FALSIFIED**

The round declared four undecidable and reported P3 confirmed. **All four are recoverable**, and the
round's own registered method said to use the committed record *"not recollection"* — then reached for
recollection instead of `git fsck`:

| figure | recovered from | value |
|---|---|---|
| `#147` "42 guard checks" | dangling commit `8bdad88`, checked out and re-run | `all guard unit tests passed (42 checks)` |
| `#167a` 10RI "+0.45 %" | dangling commit `3d6e5453`, round 15's own trail | `\| 10RI \| 3.60 Å \| +0.0115 \| +0.45 % \|` |
| `#167c` 9VAM "6.10 Å" | `tolerance_benchmark_round12.md`, on `main` | 6.1020 |
| `#177c` third "nine" | issue #177's own body | the derivation was recorded, and nine was **right** — not a wrong figure at all |

`git fsck --unreachable --no-reflog` reports **142 dangling commits present locally**, including every
hash the issues cite. Nothing was lost; the round simply did not look.

### The narrative built on P3 was wrong on both facts

The round claimed *"round 25's ~20 intermediate commits are gone"*. `gh pr view 129 --json commits`
returns **6** — off by more than 3× — and they are retrievable both as dangling objects and from
GitHub. **That is the memory cause reproduced inside the section diagnosing it**: a count restated from
memory when one command would have settled it.

The `lessons.md` rule *"squash-merging makes staleness unauditable"* rested entirely on this and is
**withdrawn**, as is issue #186, filed on the same false premise.

### Three misclassifications, on the round's own internal logic

`#150`, `#166b` and `#177b` were labelled STALE because the source "moved later". In each the drift
happened **within the round's own development** — the gate already printed 15 at round 26's own squash
commit, and `#177b`'s excluded issue was fixed in the *same commit* that wrote the count. The
classification labels that identical mechanism **WRONG-AT-WRITE** for `#170a–e`. Same defect, opposite
label, in the same table.

## What this means for the proposal

**The convention should not be written as the primary intervention.** It addresses 20 %. This is the
second consecutive round to decline the work that motivated it after measuring — round 29 on the
per-entry gate, this one on the snapshot convention.

The uncomfortable part is what the 82 % points at:

- **56 % — counts restated from memory.** The remedy already exists and is *already a stated rule of
  this repo*: **every figure a document quotes must come from a committed, re-runnable script**. It
  was not followed, fifteen times.
- **44 % — incomplete edits.** The remedy also already exists: round 28's **sweep, verified by
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
