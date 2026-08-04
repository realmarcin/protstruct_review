# Tolerance benchmark — round 28: measuring the count class instead of gating it again

Round 27 closed by asserting *"nine miscounts across four rounds, and the gate now catches two of
their shapes."* Both halves were assertions. **Nine** was a tally of what review happened to notice;
nothing had ever swept for wrong numbers systematically, so it was a lower bound of unknown tightness.

The instinct was to add a third literal→derivation pair. Predictions were registered first
(`tolerance_benchmark_round28_preregistration.md`, in a commit containing no results), and **two of
the four were falsified — the two that would have justified building that third gate.**

**No tolerance, band or measurement changed.** Seven wrong figures were corrected.

## The measurement

Every numeric claim about the work, in seven documents, verified by hand against its source.
Excluded by the registered method: tolerance values, entry resolutions, ids, issue numbers, dates.

| documents | claims | verifiable | correct | **wrong** |
|---|---:|---:|---:|---:|
| `ref/thresholds_and_standards.md` + `lessons.md` | ~227 | ~223 | ~221 | **3** |
| `NEXT_TASKS.md` + round 24–27 trails | ~99 | ~84 | ~78 | **5** |
| **total** | **~326** | **~307** | **~299** | **8 (~2.6 %)** |

The counts are approximate by ~±3 where two sweeps overlapped on the same claim; the wrong ones are
exact and individually verified.

## P1 — "the class is not closed": **confirmed**

Eight wrong figures were sitting on `main`, none previously filed. Every one had passed through at
least one review pass at the time it was written.

## P2 — "self-contradiction is the dominant shape": **falsified**

Registered because three of the historical nine were internal contradictions, and because a
contradiction is checkable **without knowing the right answer** — which would have made a cheap,
general guard.

Of the eight found, **two** are self-contradictions. **Six are a figure that is simply wrong or stale
against its source, with no second statement anywhere to contradict it.** The registry sweep found
**zero** live self-contradictions in 227 claims.

A contradiction-checker would therefore have caught **a quarter** of what is actually there. The
shape I was about to mechanise is the minority shape.

## P3 — "the errors are in the gate-covered files": **falsified**

Registered on the reasoning that the registry has had a derivation gate since round 24 while the
summary files got theirs two commits ago, so coverage should be the constraint.

The opposite holds:

| | verifiable | wrong | rate |
|---|---:|---:|---:|
| registry (gated since round 24, re-read every round) | ~185 | 2 | **~1.1 %** |
| round trails 24–27 (written once, never revisited) | ~65 | 3 | **~4.6 %** |

**The registry is roughly four times cleaner than the round trails**, and the trails have no gate at
all. Coverage is not the constraint; **being re-read is**. The registry's figures are wrong less often
not because they are checked more, but because every round rereads that file and nobody ever rereads a
finished trail.

## P4 — "the true count is higher than nine": **confirmed**

It is **ten**, and the error is exact: **#150 carried two distinct wrong numbers and was tallied as
one**, because the list counted *issues* while calling them *miscounts*. That is #155's shape — a
count wrong because of what sat inside the range being counted — reproduced in the tally of the class
#155 belongs to (#164).

The counting rule had never been stated. Three defensible readings existed: 11 wrong numbers, 10
shipped in the 24–27 window, 8 issues filed. Round 27's text now states the rule and the number under
it.

## What was actually wrong

| | figure | truth |
|---|---|---|
| #164 | the miscount tally, "nine" | ten, counting distinct wrong numbers |
| #165 | `NEXT_TASKS` opens *"**Twenty-four** rounds"* while line 66 said twenty-seven | both now twenty-eight |
| #166 | round 27: *"only **four** figures are derived"* | three |
| #166 | round 26: *"**12** checked"* and *"**10** of 21"* | 15 |
| #167 | registry: 10RI degraded *"+0.45 %"* | **0.4441 %** — the TSV's own column says so |
| #167 | registry: *"the quantity ranges **2.2–6.1 Å**"* | 2.06–4.35 Å over the 36 benchmark crossings |
| #167 | that range's 6.1 Å ceiling, attributed to 9VAM | **unverifiable** — 9VAM is a `delta-only` row with no recorded `d_fsc_model_pre` |
| — | `lessons.md` round-9: *"held on 19/19 at 1.4–2.9 Å"* | unsupported; 19 is the widened total, only 8 sit in that range (low confidence, left filed) |

**#165 is the one worth dwelling on.** The gate built for exactly that claim is blind to it twice
over: `round_count_claim` is **case-sensitive** (line 14 begins a sentence, so it reads `Twenty-four`)
and uses **`re.search`**, checking only the first match. #149 corrected precisely this case-sensitivity
in `_SEVERITY_CLAIM` — *in the same file, days earlier* — and its sibling was never touched. Fix
applied to one function and not its neighbour, again.

## What this argues for, and what it argues against

**Against** the third gate. P2 says a contradiction-checker addresses a quarter of the problem. P3
says extending coverage addresses the wrong files. Both were the plausible next moves and both are
now measured to be poor ones — which is what the pre-registration was for.

**For** something the measurement makes obvious and no gate expresses: **a round trail is a
write-once document that nobody ever rereads.** Its figures are correct when written and rot silently
because there is no occasion to look again. The registry does not rot at the same rate because every
round opens it.

That suggests the cheap intervention is not another checker but a **convention**: a figure in a
finished trail is a historical snapshot and should be written as one — stated with its denominator and
its date, not as a live quantity — so that a later reader knows it describes the moment it was written
rather than the present. Round 26's *"12 checked, 11 not"* was true the day it was written and is now
wrong; nothing about it announced that it would age.

**That is a proposal, not a result, and it is not implemented here.** This round measured; deciding
what to build on the measurement is the next one's job, and doing both would repeat exactly the
mistake the pre-registration caught.

## Scope limits

- **One sweep, seven documents, by hand.** The same "lower bound, not a total" caveat that applies to
  the `scripts/` audit applies here. ~326 claims is what two readers found, not what exists.
- **PR bodies are excluded** because they are not files in the repo — and #147 and #150 both lived
  there, so the sweep structurally cannot see that shape. Two of the historical ten are invisible to
  the method that measured them.
- **The ~326 / ~307 / ~299 figures are approximate** where the two sweeps overlapped. The eight wrong
  ones are exact.
- **The error rates compare unequal denominators.** The registry's 185 claims are concentrated in a
  few very long rows; the trails' 65 are spread across four documents. The ~4× ratio is a real
  signal, not a precise measurement.
- **`lessons.md`'s round-9 claim is left unfixed**, marked low-confidence by the sweep and not
  independently settled here. Recorded rather than silently corrected.
