# Tolerance benchmark — round 39 (arm 1): the favored-band breach is an unrestrained artefact; the band is kept

**No band is widened.** The §4 `d_min ≥ 2.5 Å` favored band stays at **−6 pp**. Round 39 arm 1 settles
the decision round 38 deferred (**#253**): 6LE5's breach — the first null-refinement breach of the
−6 pp favored band, which had held since round 7 — **does not survive the restraints that
low-resolution refinement actually uses**, so the
operational band is not breached and does not need widening. The §4 caveat is strengthened to record
this (below), which is the outcome the
[pre-registration](tolerance_benchmark_round39_preregistration.md) registered for P1 holding.

Arm 1 re-refined the **round-38 set with NCS + secondary-structure restraints** — no new downloads,
the 17 pairs were already cached — and compared each entry's favored drop against round 38's
unrestrained value. Results are committed in
[`ref/research/data/round39_xray_restrained_deltas.json`](data/round39_xray_restrained_deltas.json),
paired against [`round38_xray_deltas.json`](data/round38_xray_deltas.json). Same 14 usable entries,
same 3 failures (1RD7, 3VDD, 4UDM — data/symmetry faults restraints cannot touch), so the comparison
is fully paired.

## Result

| prediction | verdict |
|---|---|
| **P1** — 6LE5's restrained favored drop falls below 6 pp | **confirmed** — **−2.21 pp** (was −6.28 unrestrained) |
| **P2** — restraints reduce the favored drop across the set | **confirmed** — 11 of 14 improve; no restrained entry breaches −6 pp |

## The paired comparison (favored Δ, pp)

| entry | unrestrained | restrained | change |
|---|---:|---:|---:|
| **6LE5** | **−6.28** | **−2.21** | **+4.07** |
| 7P4U | −2.97 | 0.00 | +2.97 |
| 12OC | −2.61 | −0.17 | +2.44 |
| 4DYT | −1.90 | +4.98 | +6.88 |
| 6TPW | −1.63 | −1.63 | 0.00 |
| 7PLN | −0.44 | +4.77 | +5.21 |
| 4MH1 | −0.10 | +1.60 | +1.70 |
| 14ZZ | +0.17 | +1.02 | +0.85 |
| 2QTU | +0.47 | +1.41 | +0.94 |
| 6ABT | +0.53 | −0.52 | −1.05 |
| 4NJD | +2.44 | +2.09 | −0.35 |
| 1VYJ | +2.53 | +3.83 | +1.30 |
| 1RH7 | +2.74 | +7.17 | +4.43 |
| 1B9B | +3.58 | +4.57 | +0.99 |

- **Worst drop**: unrestrained **−6.28 pp** (6LE5, a breach) → restrained **−2.21 pp** (6LE5, within band).
- **Median favored Δ**: unrestrained **+0.035 pp** → restrained **+1.505 pp** — restraints systematically
  move favored the *right* way.
- **No restrained entry breaches the −6 pp band.** The one unrestrained breach is removed by restraints,
  and no new one appears.

## Why this settles #253

The §4 favored band is quoted *for unrestrained refinement*, and the registry already recorded that
restraints shrink the low-resolution favored null spread (5.26 → 3.35 pp). Round 38 found a null
re-refinement (6LE5) that breached the unrestrained band at 6.28 pp. Round 39 arm 1 shows that breach
is **specific to running unrestrained**: with the NCS + secondary-structure restraints a crystallographer
applies at 3 Å, 6LE5 drops only 2.21 pp and the band holds with room to spare.

So the decision registered for "P1 holds" applies: **keep −6 pp; do not widen.** Widening the
unrestrained band to clear 6.28 pp would loosen a check by re-fitting to a single worst case produced
by a protocol no one uses at this resolution — exactly the "band set just above one worst case" the
registry warns to avoid. What changes is not the number but the **caveat**: the unrestrained null
maximum is now known to reach 6.28 pp, and restraints bring it back to 2.21 pp.

## §4 change

The favored row's restraint clause is updated to record round 39: the unrestrained null max is **6.28 pp**
(6LE5, round 39) rather than 5.26 pp, and restraints bring it to **2.21 pp** rather than 3.35 pp. The
band value is unchanged. This is a documentation strengthening, not a tolerance change, and it is the
registered consequence of P1 holding.

## Arm 2 is now a lower-priority follow-up, not a blocker

The pre-registration ran arm 1 first precisely because it could settle the decision alone if P1 held.
It did. **Arm 2** — a fresh unrestrained set (excluding the 37 round-37/38 ids) to test P3, whether the
*unrestrained* maximum rises past 6.28 pp on new data — would sharpen the unrestrained caveat but
cannot change the decision to keep the operational band, since that rests on the restrained result. It
is left registered and unrun; the fresh-X-ray-set project (#225) subsumes it.

## Scope limits

- **This is same-binary evidence.** `phenix-2.0-5936` pinned; whether a PHENIX upgrade moves the
  restrained values is untested.
- **The decision rests on the restrained result**, which is the protocol low-resolution refinement
  uses. The unrestrained band *is* breached (6LE5, 6.28 pp); the round's claim is that this is the
  wrong protocol to size the operational band against, not that no breach exists.
- **Nothing about the Cα or `d_min < 2.5 Å` bands changes.** Out of scope.
- **Arm 2 unrun**, so P3 (does the unrestrained maximum rise on fresh data) is untested; the caveat's
  6.28 pp is a lower bound on the unrestrained max, as any maximum is.
