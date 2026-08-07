# Partial-record triage (P3b, Codex review action plan)

Round 42 established a *third* route out of a `⚠ partial record` — beyond round 21's "re-measure on a
committed subset" (works only when the lost members were unremarkable) and round 22's "closed as
unfixable" — namely **retire the lost estimator and re-base the figure on a coverage/distribution bound
over named data.** This document triages the **6 remaining** marked rows (round 42 resolved the ΔRMSD
row) into one of three routes:

- **REPLACE** — re-base on named data now (a round-42-style move); resolves the mark, changes the
  registry, so needs pre-registration + approval.
- **REMEASURE** — a small re-run on a freshly committed set to record what the lost set didn't; each is
  a mini-round.
- **RETAIN** — the mark is honest and not resolvable by re-measurement; keep it as a disclosed limit.

Every figure below was checked against the committed data before classifying.

## The six rows

| # | row | what is partial | route | resolvable now? |
|---|---|---|---|---|
| 1 | Geometry Δ clause — **clashscore** | the 4.26× null ratio and 17.2 starting clashscore come from the lost ~11 entries | **REPLACE** | **yes** — verified |
| 2 | **L-test** ⟨\|L\|⟩ | only 5 of 27 datasets named; set uncommitted | **REPLACE (cite round 21)** | likely |
| 3 | Ramachandran/rotamer **favored %** | aggregate median/p90/max sound, but no per-entry value recorded | REMEASURE | small round |
| 4 | Ramachandran/rotamer **outlier %** | only the nonzero entries named; input set uncommitted | REMEASURE | small round |
| 5 | **H-placement** agreement | "worst 16.4 %" from an uncommitted 17-model set; 0 % members unnamed | REMEASURE | small round |
| 6 | Map-model fit (EM **CC_mask + d_FSC_model**) | publishes its uncertainty as a *range* (17–22) rather than a point | **RETAIN** | already honest |

## Detail and evidence

**#1 clashscore — REPLACE, verified resolvable now.** The geometry row's last partial figures are the
clashscore null ratio (4.26×) and the "starting clashscore up to 17.2", both from the lost set. Over the
**45 fresh named entries** (rounds 37/38/41, `clashscore_pre ≥ 1`) the max null ratio is **4.25×** —
essentially the same value, now on named data, and still under the 5× degradation gate; the fresh
starting clashscore reaches **38.70**, so the named basis is *more* comprehensive than the lost "17.2".
Re-basing exactly as round 42 did the favored figure would **fully resolve the geometry row** (backed
14 → 15, marked 6 → 5). **This is the strongest candidate for a round 44** — a registry change, so
pre-registered and approved like round 42.

**#2 L-test — REPLACE by citing round 21.** The mark records that only 5 of the old 27 datasets were
named. But **round 21 already re-derived the L-test on a committed 24-dataset set** (the row itself
notes this). The partial mark is about the *old* uncommitted 27-set; the live tolerance can be stated as
resting on round 21's committed set instead, which likely resolves the mark without new measurement.
Verify the round-21 set fully backs the quoted figure before flipping it.

**#3 favored % / #4 outlier % / #5 H-placement — REMEASURE.** Each has a *sound aggregate* but an
*uncommitted input set* whose unremarkable members (the zeros / the un-tabulated majority) were never
named. Round 21's caveat applies: re-measuring helps *only if the lost members were unremarkable* — and
here they are (zeros and near-zeros), so a small re-run on a freshly committed named set records the
per-entry values and names all members. Each is a bounded mini-round (a `bench_vs_deposited` /
`bench_t14` / `bench_t05_clashscore_h` re-run on a committed set), not a project.

**#6 EM map-model — RETAIN.** This mark is different in kind: the row **publishes its own uncertainty as
a range** (17–22 degradations, denominators stated) rather than pretending completeness. It is not
hiding a lost extreme; it is honest about a genuinely uncertain count. Re-measuring on a fresh EM set
would *tighten* it (a real EM round, ~GB of downloads) but the mark is not a defect to erase — it is a
disclosed limit. Lowest priority; retain unless a fresh EM round is being run for other reasons.

## Recommended order

1. **#1 clashscore (round 44)** — verified resolvable, extends round 42, one registry change. Highest
   value, lowest cost. Needs a pre-registration + approval.
2. **#2 L-test** — likely a documentation flip onto round 21's committed set; verify first.
3. **#3/#4/#5** — three small remeasure rounds, bundleable if a fresh X-ray/validation set is run.
4. **#6** — retain; revisit only alongside a fresh EM round.

No registry value is changed by this document; it is the plan. Executing #1 (or any REPLACE) changes a
`[benchmark]` row and requires the round-42 discipline: pre-register the method, compute from a committed
re-runnable script, and get explicit approval before the mark is flipped.
