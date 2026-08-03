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

## Results

**16 of 16 processed, no skips.** Cache built by `bench_t06_r_offset.py`, refined by
`bench_refinement_deltas.py` falling back to its committed `DEFAULT_SET` — the round-18 mechanism
working on live data.

| entry | d_min | clashscore pre → post | ratio | rotamer % pre → post | rise |
|---|---:|---|---:|---|---:|
| 12LO | 1.37 Å | 1.18 → 0.00 | 0.00 | 0.00 → 0.00 | 0.00 |
| 9LLR | 1.45 Å | 1.94 → 1.55 | 0.80 | 0.00 → 0.00 | 0.00 |
| 30TW | 1.70 Å | 1.17 → 4.99 | **4.26** | 0.26 → 0.00 | −0.26 |
| 9LLN | 1.72 Å | 6.28 → 4.43 | 0.71 | 0.00 → 0.00 | 0.00 |
| **9LLO** | 1.80 Å | **0.00 → 0.67** | **undefined** | 0.00 → 0.00 | 0.00 |
| 37AP | 1.82 Å | 2.49 → 2.22 | 0.89 | 0.00 → 0.00 | 0.00 |
| 9LLP | 1.82 Å | 2.06 → 1.38 | 0.67 | 0.00 → 0.00 | 0.00 |
| 37AS | 1.91 Å | 3.68 → 2.83 | 0.77 | 0.26 → 0.53 | +0.27 |
| 32CR | 1.98 Å | 4.19 → 6.14 | 1.47 | 8.48 → 3.86 | −4.62 |
| 30IZ | 2.02 Å | 1.83 → 3.82 | 2.09 | 0.70 → 1.00 | +0.30 |
| 43SK | 2.03 Å | 3.42 → 6.52 | 1.91 | 1.20 → 0.90 | −0.30 |
| 24MR | 2.47 Å | 13.61 → 10.91 | 0.80 | 5.92 → 3.07 | −2.85 |
| 31LC | 2.52 Å | 11.27 → 10.86 | 0.96 | 9.80 → 4.08 | −5.72 |
| 28SX | 2.59 Å | 4.24 → 14.63 | 3.45 | 1.18 → 1.18 | 0.00 |
| 11AF | 2.60 Å | 6.65 → 6.46 | 0.97 | 6.64 → 4.55 | −2.09 |
| 28SW | 2.92 Å | 11.53 → 13.27 | 1.15 | 0.00 → **3.60** | **+3.60** |

| # | Prediction | Outcome |
|---|---|---|
| P1 | rotamer band holds | ✅ worst rise **+3.60 pp** (28SW) against +4 pp |
| P2 | 5× clashscore gate holds | ✅ **for every defined ratio** — max 4.26× (30TW). One ratio is **not defined**; see below |
| P3 | the original 8 reproduce round 5 | ✅ **8 of 8, exactly** |
| **P4** | a new entry exceeds 4.26× | ❌ **falsified** — the 8 additions top out at 1.91× (43SK) |
| P5 | no entry starts above clashscore 17.2 | ✅ max start **13.61** (24MR) |

## The finding: the ratio gate has an unguarded singularity

**9LLO starts at clashscore 0.00 and ends at 0.67.** `clashscore_post / clashscore_pre` is a division
by zero. The clause reads:

> **Clashscore: gate on the ratio, not the difference, while `clashscore_pre ≲ 20`** — `post / pre ≥ 5×`
> is evidence of degradation … **Above pre ≈ 20 the gate fails**: compare the absolute post-clashscore
> against §2's bar there instead.

**It guards the top end and not the bottom.** At `pre = 0` the ratio is undefined, and under any
reading that treats "0 → anything" as infinite, the gate **fires on an entry whose post-refinement
clashscore is 0.67** — comfortably inside §2's own quality bar of ≤ 4. That is a false positive on a
model which is, by the registry's other standard, excellent.

It is not an isolated edge case. The trip point of a 5× ratio gate is `5 × pre`, so:

| entry | starting clashscore | post that trips the gate |
|---|---:|---:|
| **9LLO** | **0.00** | **any clash at all** |
| 30TW | 1.17 | 5.85 |
| 12LO | 1.18 | 5.90 |

**Three of 16 entries trip within 2× §2's quality bar of 4.** A model can sit near the absolute
standard the registry itself sets and still be called degraded by the relative one.

**And the fragility is systematically high-resolution**, which is the direction registered in P2:

| regime | median starting clashscore |
|---|---:|
| `d_min < 2.5 Å` | **2.49** |
| `d_min ≥ 2.5 Å` | **11.27** |

Well-ordered high-resolution models start near zero, so their ratios are the unstable ones — while
the clause's only stated caveat concerns models starting above 20, i.e. the opposite end. **The gate
is documented against the failure mode it does not have here and silent about the one it does.**

> **Recommended, and applied below:** mirror the existing high-end guard. The ratio is meaningful only
> while `clashscore_pre` is large enough for it to mean anything; below that, compare the **absolute**
> post-clashscore against §2's bar, exactly as the clause already instructs above pre ≈ 20.

## What the round confirms about the published figures

Both quoted maxima are **reproduced exactly by the entries that produced them** — 28SW's +3.60 pp and
30TW's 4.26× — and **neither is exceeded by the 8 entries added since round 5** (P4 falsified: the
additions top out at 1.91×, and no addition raises rotamer outliers at all beyond 37AS's +0.27 pp).

So the two clauses, untested for eleven rounds, **hold on the recoverable half of their set**. That is
weaker than a re-validation and stronger than nothing: the figures come from a set that cannot be
reconstructed, but the half that can be is consistent with them.

**P5 confirms round 18's diagnosis directly.** The clause cites "starting clashscores up to 17.2";
the highest in the recoverable 16 is **13.61**. That figure came from one of the ~21 entries whose
identity was lost, exactly as round 18 inferred — and it therefore cannot be checked by anyone, ever.

## `phenix.refine` is deterministic too

**All 8 of the original entries reproduce round 5's published values exactly** — Cα shift, clashscore,
favored % and rotamer % — across roughly fifteen rounds and a PHENIX upgrade.

Rounds 16 and 17 established determinism for `real_space_refine` on cryo-EM. This extends it to a
**different program on different data**, and it retires a live risk: had P3 failed, every Δ in the §4
X-ray row would have been version-dependent, which would have mattered more than either clause.

## A registration error, recorded rather than quietly fixed

The registered scope limit said this round **"cannot test the `d_min ≥ 2.5 Å` regime"**. That was
wrong: **4 of the 16 sit at ≥ 2.5 Å** (31LC 2.52, 28SX 2.59, 11AF 2.60, 28SW 2.92). I wrote it from
the trails without checking the resolutions, which were one command away in the cache the round then
built.

It does not change a verdict — the set is still skewed high-resolution, 12 of 16 below 2.5 Å — but
the specific claim was false when registered, and this file's standard is that a registration is
checkable or it is decoration.

## Applied

> **No band changed.** Rotamer `+4 pp` holds (worst +3.60 pp) and the 5× clashscore gate holds on
> every defined ratio (max 4.26×). Both figures are the same worst cases round 5 published, now
> reproduced exactly and not exceeded by 8 further entries.
>
> **The clashscore clause gains a low-end guard**, mirroring its existing high-end one, because the
> ratio is undefined at `clashscore_pre = 0` and 9LLO is such an entry.
>
> **Determinism now covers `phenix.refine`**, 8 of 8 exact.

## Scope limits

- **This is a new measurement on 16 identified entries, not a re-validation of the published 19.**
  The `0/19` and `max 4.26×` figures are not confirmed by it; the recoverable half is consistent
  with them, which is a different and weaker statement.
- **No rate claim.** Round 20's breach count is not compared with round 7's — the denominators are
  not commensurable and round 17 established the power problem regardless.
- **The singularity is one entry.** 9LLO is the only `pre = 0` case here, so the *frequency* of the
  failure mode is unmeasured; what is established is that the gate is undefined there and that the
  set contains an instance.
- The low-end guard's exact threshold is **not measured** — the recommendation mirrors the existing
  high-end caveat in form, and the evidence supports "there must be a floor", not a specific value.

## Not claimed

No comparison of this round's breach *rate* with round 7's. Round 17 established that rate questions
need ~20 entries per arm; this has 16, against a round-7 denominator that cannot be reconstructed
anyway.
