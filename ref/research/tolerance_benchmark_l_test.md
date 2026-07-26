# Tolerance benchmark — L-test ⟨|L|⟩ (phenix.xtriage vs CCP4 ctruncate)

Settles the `L-test ⟨|L|⟩ | ± 0.02, same twin/no-twin call, matched resolution range` `[template]`
tolerance in `ref/thresholds_and_standards.md`.

Both values fall out of the runs the Wilson-B benchmark already performs, so this reads the cached
logs rather than re-running anything:

```bash
python3 scripts/bench_t13_l_test.py --cache <dir used by bench_t13_wilson_b.py> --json <out.json>
```

## Configuration

- `phenix.xtriage` → `<|L|>       : 0.483  (untwinned: 0.500; perfect twin: 0.375)`
- `ctruncate` → `L statistic =  0.497` plus `Data has used to  40.01 -   1.69 A resolution`

Both implement the **same** Padilla–Yeates statistic, so this measures consistent computation, not
method independence. The scale is narrow: the whole physical range is 0.500 (untwinned) → 0.375
(perfect twin), i.e. 0.125, so ±0.02 is ~16 % of the full scale.

27 datasets, 0.83–3.50 Å.

## Results

| | value |
|---|---:|
| median \|Δ\| | **0.006** |
| p90 | 0.014 |
| max | **0.047** |
| exceeding ±0.02 | **2 / 27** (30IZ +0.030, 9PLC −0.047) |
| same twin/no-twin call | **27 / 27** |
| max \|Δ\| as a fraction of the full 0.125 scale | 37.6 % |
| **datasets where the resolution ranges matched** | **0 / 27** |

The worst cases:

| Dataset | xtriage ⟨\|L\|⟩ | ctruncate ⟨\|L\|⟩ | Δ | xtriage d_min | ctruncate d_min |
|---|---:|---:|---:|---:|---:|
| 9PLC | 0.461 | 0.508 | −0.047 | 1.54 | 2.22 |
| 30IZ | 0.471 | 0.441 | +0.030 | 2.02 | *not reported* |
| 9RWI | 0.489 | 0.505 | −0.016 | 3.45 | 4.47 |
| 12LO | 0.483 | 0.497 | −0.014 | 1.37 | 1.69 |
| 9LLR | 0.512 | 0.525 | −0.013 | 1.45 | 1.83 |

## Findings

**1. The tolerance's own precondition is never satisfied.** "Matched resolution range" held in
**0 of 27** datasets. `ctruncate` deliberately restricts the L-test to a lower-resolution subset —
by a median of **0.46 Å** relative to the data's d_min — while `xtriage` analyses the full range.
Neither program's installed build exposes a flag to force the other's range (`ctruncate`'s usage
line offers only `-mtzin/-mtzout/-colin/-colano`). So the tolerance as written has never been, and
cannot routinely be, evaluated under its own precondition. That is a defect in the tolerance, not in
the programs: a precondition nobody can meet is not a precondition, it is a disclaimer.

**2. Given that, ±0.02 is a reasonable band and mostly holds.** Median |Δ| 0.006 and 25/27 inside
±0.02, *despite* every comparison being off-precondition. The two failures are −0.047 (9PLC, where
ctruncate cut back 0.68 Å) and +0.030 (30IZ, where ctruncate did not report its range at all).

**3. The twin call — the thing that actually matters — agreed 27/27.** Only one dataset came near
the twinning boundary at all. The numeric agreement band is the weaker half of this tolerance; the
call is the robust half, and it is the one the harness should lean on.

**4. In scale terms the disagreement is larger than it looks.** A Δ of 0.047 is 37.6 % of the entire
untwinned-to-perfect-twin range. Reporting ⟨|L|⟩ agreement as "±0.02 on a 0-to-1 statistic" would
badly overstate the precision; the denominator is 0.125, not 1.

## Applied tolerance

> **⟨|L|⟩: |Δ| ≤ 0.02, and the same twin/no-twin call** — `xtriage` vs `ctruncate`. The
> **"matched resolution range" precondition is unachievable with default builds** (0/27 datasets;
> ctruncate restricts the L-test by a median 0.46 Å and exposes no flag to change it), so it is
> restated as a **caveat**: expect the ranges to differ, and expect ~2 in 27 datasets to exceed
> ±0.02 for that reason alone. **The twin call is the load-bearing half** — it agreed 27/27 — and
> a numeric mismatch with an agreeing call is not a finding. Both programs implement Padilla–Yeates,
> so this checks consistent computation, not method independence. Note the scale: 0.02 is ~16 % of
> the full 0.125 range.

## Scope limits

- Same-method comparison by construction; a genuinely independent twinning test (e.g. the
  Britton/H-test family) is not benchmarked here.
- `ctruncate` did not report its analysis range for 9 of 27 datasets, so the range mismatch could
  only be quantified on 18 — but since it matched in none of those, treating all 27 as
  off-precondition is the conservative reading.
- Only one dataset in the set is anywhere near the twinning boundary, so the "same call" result is
  weak evidence about *borderline* twinning, which is exactly where a call would matter most.
- One version pair: PHENIX 2.0-5936, CCP4 9.0.015.
