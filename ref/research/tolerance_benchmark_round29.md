# Tolerance benchmark — round 29: the per-entry gap, measured and deliberately not closed

`scripts/check_registry_figures.py` gated **12 aggregate figures** and **zero per-entry ones** — and
both registry errors round 28 found (#167) were per-entry. #180 proposed closing that gap. Predictions
were registered first (`tolerance_benchmark_round29_preregistration.md`, no results in that commit).

**Both predictions resolved, and together they argue against the work that motivated the round.**

**No tolerance, band or measurement changed.**

## P1 — "a mechanical check finds a per-entry figure the hand sweep missed": **falsified**

Every per-entry figure derivable from `em_refinement_deltas.tsv` already matches the registry:

| figure | registry | record |
|---|---|---|
| 10RI CC_mask Δ | +0.0115 | 0.0115 |
| 10RI `d_FSC_model` Δ | +0.444 % | 0.4441 |
| 10BU worst degradation | +4.786 % | 4.7856 |
| 10ME round-16 worst | +1.476 % | 1.476 |
| 9H7U largest change | 36 % improvement | −36.150 |
| 10EU near-miss | −1.084 % | −1.084 |
| 10EU crossing ratio | 1.076 | 1.0762 |
| 21AO recovered | 2.8125 Å | 2.8125 |
| 9O9K breach | −0.0311 | −0.0311 |

Round 28's hand sweep recorded itself as *"a lower bound, not a total"*. **Over the nine derivable
per-entry figures checked here, it missed none** — which is what P1 actually tests. It is *not* a
claim that the sweep was complete over the registry: nine figures is what could be derived and
checked, and the other twenty per-entry claims remain unverifiable by any means (P2). Saying "the
sweep was complete" would be the stronger version of a true result, which is the failure this repo
names most often, so the claim is stated at the size the evidence supports.

The pre-registration said this outcome *"would argue against extending mechanical coverage further"*.
It does, and the round follows its own instruction rather than building the thing it set out to build.

## P2 — "underivable per-entry figures outnumber derivable ones": **indeterminate**

**The verdict flips with the counting method, so it has none** (#182).

A regex over the §4 map-model row gave **9 derivable against 20 underivable** — roughly two to one, and
that is what this section originally claimed. It does not survive scrutiny, in **both** directions:

**It undercounted derivable.** It took only the first few numbers after each id and missed values the
round's own criteria plainly cover — 9H7U's `4.06 → 2.59 Å` and ratio 1.372, 10BU's ratio 1.360 and
its `4.35 Å` crossing, 10BU's `3.24×` above the next-largest and `30.6×` the median, 10ME's rank
"29th of 36". All are direct lookups or one division on TSV columns, and the round already counted
10EU's *computed* ratio as derivable, so the criterion was applied inconsistently. Derivable is **at
least 15**, not 9 — and all fifteen verify correct, which strengthens P1.

**It overcounted underivable.** It treated any number near an id as a claim *about* that entry. Most
were not: band values (`0.05`, `0.06`, `0.15`), the 3.0 Å resolution split, round 19's `3.05–3.45`
window. A hand classification of genuine per-entry assertions gives roughly **11** underivable —
mtriage internals (`9VJD's curve dips to FSC 0.073 at 23.11 Å`), 27WR's and 21BQ's crossings and atom
densities, 9VAM's 6.10 Å, and the `124 / 399 / 117` shell counts.

So the two reasonable methods give **9 : 20** and **≈15 : 11** — opposite directions. **A prediction
whose verdict flips with the counting method is indeterminate**, which is the call round 26 made for
its own P4 and for the same reason. Recording it as confirmed was reading the method that agreed with
the prediction.

**The decision not to extend the check rests on P1 alone**, and is unaffected: every derivable
per-entry figure already matches, so there is nothing further to find. P2 was supporting evidence for
*"most of what remains cannot be checked"* — a claim now withdrawn.

## What was built, and what was deliberately not

Five per-entry checks now ship, covering the figures #167 corrected plus the three most load-bearing
extremes. They pass. **They are not extended further**, because P1 says there is nothing more to find
and P2 says most of what remains cannot be checked at all.

The gate now **states its own coverage** rather than implying completeness:

```
all 19 checked registry figures match the data (5 per-entry; the registry quotes more
per-entry figures than are gated here, some of them not derivable at all — see round 29)
```

That line exists because of #116: a gate reporting *"all figures match"* while covering a third of
them overstates what it verified. Round 24 built a gate that could not fail; this one says out loud
what it does not reach.

**And the coverage figure was itself wrong on the first attempt.** It counted per-entry checks with
`"." in check`, which matches `refinement attempts incl. LOST` — a wrong coverage number inside the
statement written to stop overstating coverage. Fixed by tagging the results explicitly rather than
sniffing their names.

## What `UNDERIVABLE` means, stated rather than left implicit

An `UNDERIVABLE` result **fails the gate**, and that is deliberate. It is not the same as round 26's
`UNCHECKABLE`, which reports that no source exists *by convention* and passes. `UNDERIVABLE` means the
registry cites a per-entry value that the record **no longer holds** — a column emptied, or an entry
removed. A registry figure whose backing has disappeared is a real problem, not a coverage note.

Exercised in both forms, since nothing in the committed data triggers either:

| case | result |
|---|---|
| entry present, column emptied | `UNDERIVABLE`, naming the entry's status |
| entry removed from the file entirely | `UNDERIVABLE`, saying no such entry |
| value changed | `STALE`, showing registry against record |

## Scope limits


- **The derivable/underivable split has no reliable value.** 9:20 by regex, ≈15:11 by hand; the
  answer depends entirely on what counts as a per-entry *claim*, and this round did not find a
  principled way to delimit that. The count is reported as contested rather than resolved.
- **At least 15 derivable figures exist and 5 are gated.** The other ten rest on the aggregate checks.
- **§3's rows are out of scope.** They quote per-entry values from sets that are committed but not in
  this TSV.
- **P1's falsification is about the registry only.** It says round 28's sweep was complete *there*;
  it says nothing about the round trails, where that same sweep found five wrong figures.
