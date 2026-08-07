# Tolerance benchmark — round 44: the geometry row's clashscore figures re-based on named data; the row resolves

**No band value changes.** Round 44 finishes what round 42 began: it re-bases the §4 geometry row's last
`⚠ partial record` figures — the clashscore null-ratio maximum and the starting-clashscore ceiling,
both from the lost ~11 low-resolution entries — onto the **44 fresh named entries** (rounds 37/38/41).
With that, the geometry row is **fully backed** and the registry moves to **15 backed / 5 marked**.

Pre-registered in [`tolerance_benchmark_round44_preregistration.md`](tolerance_benchmark_round44_preregistration.md)
before the figures were re-based; re-derivable by
[`scripts/analyze_xray_band_coverage.py`](../../scripts/analyze_xray_band_coverage.py) from the committed
`round{37,38,41}_xray_deltas.json`. This is **P3(b) triage item #1** (`partial_record_triage.md`).

## Result

| prediction | verdict |
|---|---|
| **P1** — the fresh named max null ratio stays below 5× | **confirmed** — **4.25×** over 37 gate-valid entries (none ≥ 5×) |
| **P2** — the fresh starting clashscore exceeds the lost 17.2 | **confirmed** — **38.70**, with 7 entries above pre = 20 |

## What was re-based

The clashscore degradation gate is unchanged: `clashscore_post / clashscore_pre ≥ 5×` is degradation,
valid while `1 ≲ clashscore_pre ≲ 20`, the absolute §2 bar used outside that range. Only the **evidence**
moved from the lost set to named entries:

| figure | was (lost set) | now (named) |
|---|---|---|
| max null clashscore ratio (gate-valid, `1 ≤ pre ≤ 20`) | 4.26× over 19 | **4.25× over 37** |
| starting-clashscore ceiling | "17.2, not reproducible" | **38.70** (7 entries > pre 20) |

The near-identity of the ratio maximum (4.25× vs 4.26×) is the point: the figure that established the
5× gate reproduces on a fully named, committed set, so the gate no longer rests on a number that could
not be recounted. And the lost "17.2 starting clashscore, not reproducible" is now **exceeded** on named
data (38.70) — the same shape as round 37's finding that 17.2 was unremarkable, not an unrecoverable
extreme.

## The row resolves

The geometry row's `⚠ partial record` had two halves: the favored band width (resolved round 42, re-based
as a coverage bound) and these clashscore figures (resolved here). With both re-based on named data, the
row is fully backed. Registry accounting, checked not assumed: **14 → 15 fully backed, 6 → 5 marked** —
the geometry row was the only one round 42 left half-resolved, and round 44 completes it. The remaining
five marked rows are triaged in `partial_record_triage.md` (three REMEASURE, one REPLACE-by-citation, one
RETAIN).

## Scope limits

- **No tolerance changed** — the 5× gate, its `1 ≲ pre ≲ 20` bounds, and the absolute-bar fallback are
  all unchanged; this is a record-integrity re-basing of the evidence, not a re-fit.
- **Same-binary** — `phenix-2.0-5936` pinned; round 43 registers the cross-version test.
- **The ratio is only defined for `pre ≥ 1`**, and the gate only valid to `pre ≈ 20`; the 44-entry
  figure uses the 37 entries in that range, and the 7 above pre = 20 are why the absolute-bar fallback
  exists.
- **The clashscore *difference* is still unbanded** — it moves both ways on a null re-refinement; only
  the ratio maximum and the starting ceiling were partial, and only they were re-based.
