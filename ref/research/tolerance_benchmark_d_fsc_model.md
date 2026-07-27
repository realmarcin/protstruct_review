# `d_FSC_model` — the mechanism, and the clause is not ungateable after all

Rounds 5–8 carried `d_FSC_model_post ≤ d_FSC_model_pre + 0.05 Å` as **unmeasurable**. Round 6 said
mtriage's crossings were degenerate; round 7 blamed model-to-map coverage; round 8 withdrew that
explanation, leaving "1 of 6 entries fails, cause unknown".

The cause is now identified, and it makes the clause measurable.

```bash
python3 scripts/bench_refinement_deltas_em.py --cache <dir> --json <out.json>
```

## The mechanism

`phenix.mtriage` writes the model-map FSC curve to `fsc_model.masked.mtriage.log`. Reading it
directly for the failing entry (9VJD) and a working one (21BQ):

| | 9VJD (2.86 Å) | 21BQ (2.7 Å) |
|---|---|---|
| Shells in the curve | 18567 | 18217 |
| FSC at lowest resolution | 0.995 | 0.997 |
| FSC minimum where d > 15 Å | **0.073** | 0.225 |
| First shell with FSC < 0.143 | **23.11 Å** | 2.62 Å |
| …does it recover above 0.5 afterwards? | **yes** | — |

**9VJD's curve dips to FSC 0.073 in a single shell at 23.11 Å and then recovers.** mtriage's
`d_fsc_model` reports the **first** shell whose FSC falls below the threshold, scanning from low
resolution, so one anomalous low-resolution shell defeats it: the tool returns 23.11 Å for a 2.86 Å
map. 21BQ has no such dip (its minimum above 15 Å is 0.225), so its first crossing is the real one.

Neither coverage (round 7's explanation, refuted in round 8) nor missing half-maps (round 6's,
refuted in round 7) is involved. It is a **curve artefact at very low resolution plus a
first-crossing search that does not require the crossing to be terminal.**

## The fix

Take the **last** crossing — the resolution beyond which FSC never recovers above the threshold —
computed from the curve file mtriage already writes:

| Entry | threshold | mtriage (first crossing) | last crossing | map resolution |
|---|---|---:|---:|---:|
| 9VJD | 0.143 | **23.11 Å** | **2.77 Å** | 2.86 |
| 9VJD | 0.5 | 29.22 Å | 3.01 Å | 2.86 |
| 21BQ | 0.143 | 2.62 Å | 2.62 Å | 2.70 |
| 21BQ | 0.5 | **36.11 Å** | **2.69 Å** | 2.70 |

The 0.5 row for 21BQ shows the bug is not confined to entries whose 0.143 value looks wrong — 21BQ
was one of the "working" entries in round 8 and its FSC = 0.5 figure was nonsense too. The same
signature explains 27WR's `FSC = 0.5 at 29.79 Å`, noticed in round 6 and never explained.

`scripts/bench_refinement_deltas_em.py` now computes `d_fsc_from_curve()` instead of parsing
mtriage's summary line, and runs each measurement in its own directory because mtriage writes the
curve under a fixed filename.

## The band, on the entries measured so far

With the crossing computed correctly, a **null** real-space refinement barely moves `d_FSC_model`:

| Entry | resolution | d_FSC_model pre → post | Δ |
|---|---:|---|---:|
| 27WR | 2.70 Å | 2.2448 → 2.2455 Å | **+0.0007** |
| 9VJD | 2.86 Å | 2.7661 → 2.7660 Å | −0.0001 |
| 10GX | 3.20 Å | 2.6797 → 2.6797 Å | **0.0000** |

Max |Δ| **0.0007 Å** against a ±0.05 Å band — roughly 70× headroom.

**This is 3 entries, not 6.** The run was stopped with 10QT (78 939 atoms), 21BQ and 24UM still in
`real_space_refine`; the two small ones would have completed quickly behind 10QT, which did not. The
band is therefore **not** tightened on this evidence — three null refinements are enough to show the
clause works and nowhere near enough to set a number. `± 0.05 Å` is retained.

## Applied

> **`d_FSC_model` is gateable, using the last FSC crossing rather than mtriage's reported value.**
> The `± 0.05 Å` band is **retained unchanged** — a null refinement moved it by at most 0.0007 Å on
> the 3 entries measured, but 3 is too few to tighten on.
> Do not read `d_fsc_model` from the mtriage summary table: it reports the first shell below the
> threshold and a single anomalous low-resolution shell — present in 1 of 6 EM entries at the 0.143
> threshold, and more often at 0.5 — makes it report a value an order of magnitude too large.
> Compute the crossing from `fsc_model.masked.mtriage.log` instead.

## Scope limits

- The last-crossing rule assumes the FSC curve is monotonic in its tail, which it is for every entry
  examined here, but it is a heuristic: a curve that genuinely oscillates near the threshold at high
  resolution would give a value biased towards higher resolution.
- The low-resolution dip in 9VJD is itself unexplained. It is plausibly a masking or box artefact,
  but that was not established — only that it is what defeats the tool's search.
- The mechanism is verified on 6 EM entries at 2.7–3.4 Å (all six have curves read and crossings
  computed); the **Δ band rests on only 3**, because `real_space_refine` on the largest model
  (10QT, 78 939 atoms) did not finish. Completing those three is the obvious next step.
