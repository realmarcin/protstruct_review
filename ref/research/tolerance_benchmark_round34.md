# Tolerance benchmark — round 34: the crossing-quality screen ran at the right cut and still found nothing

**No tolerance, band or measurement changed.** No registry figure is touched.

Round 23 ran this screen at the inherited 1.3 cut, found **0 of 24**, and could not complete the test.
Round 34 ran it at the **data-driven 1.074 fence** — the cut round 23 itself established — and found
**0 of 13**. The hypothesis remains untested, for the second time, and the reason is now precisely
priced.

## Result

| | |
|---|---|
| entries fetched | **14** (26 candidates considered, 12 rejected) |
| screened | **13** |
| skipped as unmeasurable | **1** (6ADL) |
| ratio range | **0.854 – 1.025**, median **0.969** |
| **above the 1.074 fence** | **0** |
| above the 1.3 cut | 0 |

Cumulative with the 60 on record: **4 of 73 = 5.5 %**.

## This is not evidence against the hypothesis

At the prior base rate of 4 of 60 = 6.7 %:

    P(0 candidates in 13 screened) = 0.408

Two in five runs of this size return nothing even if the fence is exactly right. Round 23 made the
same mistake available and declined it; so does this round. **0 of 13 is an underpowered draw, not a
refutation.**

Reaching the three candidates a powered comparison needs takes **~45 screened** at 6.7 %, or ~55 at
the updated 5.5 %. Rounds 23 and 34 together have screened **37**.

## What actually stopped this round, and it was not cost

The batch requested 44 entries and got 13. The reason is in the fetch log:

    2.40-2.62 Å: 6 candidates
    ... (eight strata)
    3.98-4.20 Å: 6 candidates

**48 candidates offered, against 127 ids already excluded.** `--strata` defaults to 8 and
`--per-stratum` to 6, so the query proposes 48 entries per run no matter what `--limit` asks for. The
constraint is the **search parameters**, not the download budget: 2.5 GB and roughly an hour of
`mtriage` bought 14 entries because only 26 unexcluded candidates existed to try.

That is the actionable finding. `--per-stratum 20` would offer 160, and the same money would buy
three to four times the entries. **The project is not expensive; it was under-queried.**

## Attrition, which is the other half of the cost

Derived from `ref/research/data/em_fetch_attrition.tsv`, round-34 rows — **26 distinct candidates
considered, 12 rejected before any screening**:

| reason | n |
|---|---|
| model exceeds `--max-model-mb 8` | 5 |
| map exceeds `--max-map-mb 250` | 4 |
| unparameterised ligand | 2 |
| formal charges absent from the scattering table | 1 |

So the effective yield is **14 of 26 = 54 %**, and a future run should size its query accordingly:
~85 candidates offered to land ~45 screened.

This table first read *"23 considered, 10 rejected"* — the **batch's** figures, silently excluding the
canary's own three candidates. A count attached to the wrong scope, in the round whose fetch record
was one `awk` away. It is the class rounds 31–33 measured, caught here before merge by re-deriving
against the record rather than against the batch log I happened to be reading.

## 6ADL, and the estimator bug it re-demonstrates

One entry was skipped with `crossing 21.91 A implausible for a 3.08 A map`. That is the mtriage
first-crossing failure round 9 diagnosed — a single anomalous low-resolution shell defeats the
reported value, exactly as 9VJD returns 23.11 Å for a 2.86 Å map. The screen caught it, recorded it in
the `skipped` list rather than dropping it, and **the denominator says 13 screened and 1 unmeasurable
rather than quietly saying 14**.

That is the behaviour round 23's script was written for, arriving on live data.

## Six defects, four of them before a single batch entry was downloaded

Three came from **running one entry end to end before fanning out**, one from reviewing the fix for
those three, and two only surfaced once the batch ran. None would have been caught by reading a
document.

| | defect | when |
|---|---|---|
| **#226** | the screen hardcoded the 1.3 cut with no flag — the batch would have repeated round 23's failure by construction | canary |
| **#227** | it emitted `prior_base_rate_pct: 5.6` ("2 of 36 on record") into machine-readable output; the set is 60 | canary |
| **#228** | `test_round_figures.py` had shipped with 18 checks and `validate.sh` never ran it | canary |
| **#230** | `--cut 0` ran and reported a **100 % base rate** in well-formed JSON | review |
| **#231** | a second fetch **overwrote** `entries.json`, erasing the canary entry while its 84 MB map sat on disk | batch |
| **#232** | a model rejected on map size left an orphan `.cif`; 18 models against 14 maps | batch |

**#231 is the one that matters.** `screen_dfsc_ratio.py`'s own docstring promises the denominator
*"cannot go missing the way rounds 16-18 found it had elsewhere"*. It cannot go missing downstream.
This is how it went missing upstream — and the screen would have divided by 13 with 14 entries
cached, which is the single most repeated defect in this repo, arriving in the one place its own
documentation says it cannot.

## Scope limits

- **The hypothesis is still untested**, for the second round running. Neither supported nor refuted.
- **0 of 13 is consistent with the fence being right.** Nothing here should be read as evidence the
  ratio does not predict excursions.
- **The 5.5 % cumulative rate is not an update in any strong sense** — the 13 new entries were drawn
  from the same query as the 24 before them, so they are not an independent sample of EM structures.
- **No refinement was run**, so no `d_FSC_model` delta was produced and no band was tested. This
  round is a screen and nothing else.
- **Nothing is gated.** Five consecutive rounds have now declined to build on an unresolved premise.
