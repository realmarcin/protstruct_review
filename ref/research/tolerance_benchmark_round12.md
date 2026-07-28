# Round 12 — CC_mask holds, `d_FSC_model` breaks exactly as predicted

Round 11 predicted `d_FSC_model` would be "the next band to break" and flagged the CC_mask
`≥ 3.0 Å` branch as resting on 6 entries. Ten more EM entries settle both: the CC_mask split
survives and is now located, and `d_FSC_model` breaks by 5×.

```bash
python3 scripts/bench_refinement_deltas_em.py --cache <em cache> --json <out.json>
```

## 1. CC_mask — both branches hold, and the split point is located

The EM set goes 13 → **22 entries**, with the 2.88–3.16 Å window deliberately sampled because
round 11 had nothing between 2.97 and 3.07 Å.

| Entry | resolution | CC_mask Δ | | Entry | resolution | CC_mask Δ |
|---|---:|---:|---|---|---:|---:|
| 10SE | 2.41 | +0.0024 | | 9ELS | 3.02 | +0.0061 |
| 27WR | 2.70 | −0.0065 | | 9V4D | 3.07 | +0.0115 |
| **21BQ** | 2.70 | **−0.0139** | | **10SF** | **3.08** | **−0.0371** |
| 24UM | 2.70 | −0.0060 | | 9OIF | 3.10 | −0.0217 |
| 10SG | 2.84 | −0.0019 | | 10SD | 3.11 | −0.0421 |
| 9VJD | 2.86 | +0.0084 | | 10GX | 3.20 | +0.0041 |
| 9V35 | 2.97 | +0.0061 | | 9PGD | 3.20 | +0.0155 |
| 10SH | 2.97 | +0.0001 | | **9UPM** | 3.21 | **−0.0475** |
| 9VTW | 3.00 | +0.0154 | | 10QT | 3.40 | +0.0118 |
| 9OID | 3.00 | +0.0595 | | 9UPO | 3.71 | −0.0402 |
| | | | | 9V3C | 3.82 | +0.0139 |
| | | | | 9VAM | 3.88 | +0.0085 |

| Branch | n | min | median | band | breaches |
|---|---:|---:|---:|---:|---:|
| < 3.0 Å | 8 | −0.0139 | −0.0009 | −0.02 | **0** |
| ≥ 3.0 Å | 14 | −0.0475 | +0.0073 | −0.06 | **0** |

**Both branches survive**, the first band in four rounds to do so. The `≥ 3.0 Å` branch now rests on
14 entries rather than 6.

**The transition is located more precisely than the split assumes.** Every entry from 2.97 to 3.07 Å
is positive; the first excursion past −0.02 is **10SF at 3.08 Å**. So the boundary lies between 3.07
and 3.08 Å in this sample, and the 3.0 Å split is **conservative** — it places 3.00–3.07 Å entries in
the loose branch when they behave like the tight one. Left at 3.0 rather than moved to 3.05: the
transition is located to within 0.01 Å by *two* entries, which is exactly the kind of precision this
series has learned not to trust.

Round 11's finding that resolution **bounds but does not predict** the excursion is unchanged and
reinforced: the ≥ 3.0 Å group still splits into entries that degrade (−0.0475 to −0.0217) and
entries that improve (up to +0.0595), with 9OID at 3.00 Å the single largest *improvement* in the
whole set.

## 2. `d_FSC_model` — broken, and the band was the wrong shape

Round 11 measured headroom falling from 5× to 1.55× and said "expect it to breach on the next
widening". It did, by 5×:

| Entry | resolution | d_FSC_model pre → post | Δ | relative |
|---|---:|---|---:|---:|
| **9VAM** | 3.88 Å | 6.1020 → 6.3629 | **+0.2609** | 4.28 % |
| **9ELS** | 3.02 Å | 2.7163 → 2.5967 | **−0.1196** | 4.40 % |
| **9OID** | 3.00 Å | 2.8993 → 2.8290 | **−0.0704** | 2.43 % |

Three of 21 entries breach ± 0.05 Å. These are **not** the estimator artefact found in round 10 —
measuring local shell spacing at each crossing, the moves are 124, 399 and 117 shells respectively,
i.e. genuine curve movement.

**The band was the wrong shape.** `d_FSC_model` ranges 2.2–6.1 Å across the set, so a fixed
absolute band is simultaneously too tight at the top of that range and too loose at the bottom. In
relative terms the same data is well behaved:

| | median | p90 | max |
|---|---:|---:|---:|
| \|Δ\| absolute | 0.0093 Å | — | 0.2609 Å |
| \|Δ\| relative | **0.31 %** | 2.43 % | **4.40 %** |

| Candidate band | violations / 21 |
|---|---:|
| ± 0.05 Å (current) | **3** |
| ± 0.15 Å | 1 |
| ± 0.30 Å | 0 |
| **≤ 5 % relative** | **0** |
| ≤ 6 % relative | 0 |

An absolute band wide enough to cover the data (0.30 Å) would permit an 11 % change on a 2.7 Å
measurement. **5 % relative covers all 21 with the largest observation at 4.40 %.**

**The range argument rests on one entry.** 9VAM is the only entry above 4 Å — its `d_FSC_model` is
6.10 Å and the next largest is 3.62 Å. Remove it and the range collapses to 2.25–3.62 Å (a factor of
1.6), the largest |Δ| falls to 0.1196 Å, and a widened *absolute* band of 0.15 Å has zero violations
on the remaining 20. So on 20 of 21 entries an absolute band works as well as a relative one, and
"no absolute band serves both ends" is carried entirely by 9VAM. That is the n = 1 generalisation
this series has spent eleven rounds catching elsewhere, so it is stated rather than glossed.

The relative band is still the better choice — it extends to maps outside the sampled range, and
9VAM is a genuine entry rather than an artefact (its Δ is 124 shells of real curve movement) — but
the evidence for the *shape* is thinner than the evidence for the *number*.

**A physically-motivated alternative was tested and rejected.** mtriage samples the FSC curve
uniformly in **1/d**, so a fixed shell shift implies Δd ∝ d², suggesting a `|Δd| / d²` band. Measured
across the set by how far the worst case sits above the median:

| Band shape | median | max | max / median |
|---|---:|---:|---:|
| \|Δd\| absolute | 0.00930 | 0.26090 | 28.1 |
| **\|Δd\| / d (relative)** | 0.00315 | 0.04403 | **14.0** |
| \|Δd\| / d² (≈ Δ(1/d)) | 0.00105 | 0.01621 | 15.4 |

The plain relative form is the tightest of the three, so the d² scaling that the sampling suggests
does **not** fit better and the relative band stands on its own.

This is the same conclusion rounds 1 and 2 reached for interface BSA and Wilson B: when the
underlying quantity spans a wide range, the band has to be relative.

## Applied

> **Map-model CC_mask: bands unchanged and now supported** — `< 3.0 Å` → `− 0.02` (8 entries, min
> −0.0139); `≥ 3.0 Å` → `− 0.06` (14 entries, min −0.0475). 0 breaches over 22 entries. The 3.0 Å
> split is conservative: the observed transition is between 3.07 and 3.08 Å.
>
> **`d_FSC_model`: `|Δ| ≤ 5 % of d_FSC_model_pre`**, replacing ± 0.05 Å, which was breached by 3 of
> 21 entries. Observed median 0.31 %, max 4.40 %. The quantity ranges 2.2–6.1 Å across the set, so
> an absolute band cannot serve both ends.

## Scope limits

- 22 EM entries, 3 `real_space_refine` failures across the series (9VXE, 13GH, 9TZY) reported rather
  than dropped.
- The `< 3.0 Å` CC_mask branch has 8 entries and its worst case (−0.0139) is a single observation
  from 21BQ; on this series' record that is exactly the configuration that breaks next.
- The 5 % relative band for `d_FSC_model` rests on 21 entries with 3 above 2 %. The tail is thin, and
  the argument for a relative *shape* rests on a single entry (9VAM) — the only one above 4 Å.
- The transition location (3.07–3.08 Å) is set by two adjacent entries and should not be treated as
  a measured inflection.
