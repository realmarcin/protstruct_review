# Tolerance benchmark — round 20: the two §4 clauses nobody re-tested

Round 18 traced the §4 geometry row's "19 entries" against the ΔRMSD row's "37" and found it was not
a stale count. Rounds 8, 10 and 11 grew the X-ray set **19 → 26 → 32 → 37 while re-testing only the
Cα-shift and favored clauses.** Two clauses have been untested since round 7:

| clause | quoted evidence | headroom |
|---|---|---:|
| `rotamer outliers_post ≤ outliers_pre + 4 pp` | 0/19 breaches, worst null rise **3.60 pp** | **1.11×** |
| `clashscore_post / clashscore_pre ≥ 5×` is degradation | max **4.26×**, starting clashscores up to 17.2 | **1.17×** |

Both worst cases come from the **original 8 entries**, not from the 19: 28SW rose 0.00 → 3.60 pp, and
30TW went 1.17 → 4.99 (4.26×). Eleven rounds later, neither clause has seen an entry added since.

Both are also **thin bands sitting just above a single worst case**, which this repo's own record says
is the base case for a break: *"Each new band is again set just above a single worst case, so treat a
further break as the base case."*

## What this round can and cannot do

**It is a new measurement on a smaller set, not a re-validation.** Only **16 of the 37** entries are
identifiable (round 18); the other ~21 are the ones whose ids were never recorded, and they include
the low-resolution batch round 7 added. So:

- The 16 are **disproportionately high-resolution** — round 10's six sit at 1.45–1.98 Å, 43SK at
  2.03 Å, 31LC at 2.52 Å, and the original 8 span the rest.
- **This round cannot test the `d_min ≥ 2.5 Å` regime**, which is where the lost entries live and
  where the null spread is widest.
- Whatever it reports gets its **own denominator**. The published `0/19` and `max 4.26×` are not
  confirmed by it and must not be restated as though they were.

That is the honest shape of the thing, and it is registered before the data rather than discovered
in the discussion.

## Method

```bash
python3 scripts/bench_t06_r_offset.py <the 16> --cache <dir>       # builds <id>.pdb + <id>_g_obs.mtz
python3 scripts/bench_refinement_deltas.py --cache <dir> --json out.json
```

The set is the committed `DEFAULT_SET` in `bench_refinement_deltas.py` (round 18), so this run is
reproducible from a clean checkout — which is exactly what rounds 17–18 were for. **One entry is
canaried end to end before the rest launch**, verified on side effects rather than exit code.

## Predictions, registered before the data

| # | Prediction | Falsified if | P |
|---|---|---|---|
| **P1** | The rotamer band **holds**: no entry rises more than 4 pp. | Any entry rises > 4 pp. | 75 % |
| **P2** | The **5× clashscore gate holds**: no entry reaches a ratio of 5×. | Any entry does. | **55 %** |
| **P3** | The original 8 **reproduce their round-5 values** to reported precision. | Any of the 8 differs beyond the printed precision. | 70 % |
| **P4** | At least one of the 8 entries added since round 5 produces a clashscore ratio **above 4.26×**. | All 8 stay below it. | 50 % |
| **P5** | **No entry starts above clashscore 17.2** — confirming that figure came from one of the ~21 lost entries. | Some entry starts above 17.2. | 80 % |

**P2 is the one at risk, and the reason is mechanical.** The gate is a *ratio*, so its denominator is
the starting clashscore — and the eight entries added since round 5 are the **high-resolution** ones,
which have the lowest starting clashscores in the set. A model starting at 0.5 needs only to reach
2.5 to trip a 5× gate, while 24MR starting at 13.61 would have to reach 68. **The gate is most
fragile exactly where this round adds entries.** The registry already knows the gate fails at the
*top* end (`above pre ≈ 20 the ratio collapses`); this predicts nothing about that, and everything
about the bottom.

**P3 tests determinism on a different tool.** Rounds 16 and 17 established that
`real_space_refine` reproduces byte-identically. `phenix.refine` is a different program on different
data, and the round-5 values were produced by an older PHENIX. If P3 fails, every Δ in the §4 X-ray
row is version-dependent, which would matter more than either clause.

**P5 tests round 18's diagnosis** rather than a tolerance: it predicts the quoted "starting
clashscores up to 17.2" is *not* reproducible from the recoverable set, because it came from an entry
whose identity was lost. The original 8 top out at 13.61.

## Not claimed

No comparison of this round's breach *rate* with round 7's. Round 17 established that rate questions
need ~20 entries per arm; this has 16, against a round-7 denominator that cannot be reconstructed
anyway.
