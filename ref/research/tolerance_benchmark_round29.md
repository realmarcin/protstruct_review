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

Round 28's hand sweep recorded itself as *"a lower bound, not a total"*. **Over the registry's
derivable per-entry figures it was in fact complete**, which is a stronger statement than that round
was willing to make about itself and could only be established by checking.

The pre-registration said this outcome *"would argue against extending mechanical coverage further"*.
It does, and the round follows its own instruction rather than building the thing it set out to build.

## P2 — "underivable per-entry figures outnumber derivable ones": **confirmed**

Of **29** claims pairing a real entry id with a number in the §4 map-model row, **9 are derivable and
20 are not** — roughly two to one.

The underivable ones are not oversights. They are quantities the TSV was never designed to hold:
mtriage internals (`9VJD's curve dips to FSC 0.073 at 23.11 Å`), band values that happen to sit beside
an id, resolution splits, and figures from `LOST` and `delta-only` rows whose per-entry values were
never published — 9VAM's 6.10 Å among them, which #167 already established cannot be checked.

**Both counts are approximate.** Extracting claims from prose by regex is crude: the first attempt
counted `0311`, `9843` and `0115` — fragments of numbers like `−0.0311` — as entry ids and reported
30 underivable. Filtering to ids that exist as entries gives 20. What is robust is the **direction**,
not the digits.

## What was built, and what was deliberately not

Five per-entry checks now ship, covering the figures #167 corrected plus the three most load-bearing
extremes. They pass. **They are not extended further**, because P1 says there is nothing more to find
and P2 says most of what remains cannot be checked at all.

The gate now **states its own coverage** rather than implying completeness:

```
all 19 checked registry figures match the data (5 per-entry; most per-entry figures
the registry quotes are NOT derivable and are not checked — see round 29)
```

That line exists because of #116: a gate reporting *"all figures match"* while covering a third of
them overstates what it verified. Round 24 built a gate that could not fail; this one says out loud
what it does not reach.

**And the coverage figure was itself wrong on the first attempt.** It counted per-entry checks with
`"." in check`, which matches `refinement attempts incl. LOST` — a wrong coverage number inside the
statement written to stop overstating coverage. Fixed by tagging the results explicitly rather than
sniffing their names.

## Scope limits

- **The five checks are a sample, not the derivable set.** Nine figures are derivable; five are
  gated. The remaining four are pinned only by the aggregate checks that already existed.
- **The 9/20 split is approximate**, for the extraction reason above, and is a lower bound on
  underivable in the sense that a crude regex misses claim forms nobody anticipated.
- **§3's rows are out of scope.** They quote per-entry values from sets that are committed but not in
  this TSV.
- **P1's falsification is about the registry only.** It says round 28's sweep was complete *there*;
  it says nothing about the round trails, where that same sweep found five wrong figures.
