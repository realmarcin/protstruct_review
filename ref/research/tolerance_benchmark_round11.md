# Round 11 — both "edge of evidence" bands broke, immediately

Round 10 flagged two bands as sitting at the edge of their evidence and predicted one was "one entry
away from not holding". Adding entries broke **both**, on the first try. A third result closes the
rotamer question that three rounds had called a dead end.

```bash
python3 scripts/bench_refinement_deltas.py --cache <hi-res cache> --json <out.json>
python3 scripts/bench_refinement_deltas_em.py --cache <em cache> --json <out.json>
python3 scripts/bench_vs_deposited.py --ids-file <ids.json> --cache <dir> --json <out.json>
```

## 1. §4 `< 2.5 Å` Cα shift — breached

Round 10: 14 entries, largest null shift 0.0867 Å against a 0.10 Å band, **1.15× headroom**, "one
entry away from not holding". Five more sub-2.5 Å entries later:

| | round 10 | round 11 |
|---|---:|---:|
| Entries < 2.5 Å | 14 | **19** |
| Entries < 2.0 Å | 9 | 11 |
| Largest null Cα shift | 0.0867 Å | **0.1011 Å** |
| Breaches of the 0.10 Å band | 0 | **1** (43SK, 2.03 Å) |

The prediction was right and the margin was gone. **Band widened to 0.12 Å.**

## 2. Map-model CC_mask — breached again, and it is resolution-dependent

Round 10 widened CC_mask from −0.01 to −0.02 after one breach on 6 EM entries, and recorded it as
"the thinnest evidence base of any band in the file". Seven more entries (13 total):

| Entry | resolution | CC_mask Δ |
|---|---:|---:|
| **9UPM** | 3.21 Å | **−0.0475** |
| **10SD** | 3.11 Å | **−0.0421** |
| **10SF** | 3.08 Å | **−0.0371** |
| 21BQ | 2.70 Å | −0.0139 |
| 27WR | 2.70 Å | −0.0065 |
| 24UM | 2.70 Å | −0.0060 |
| 10SG | 2.84 Å | −0.0019 |
| 10SE | 2.41 Å | +0.0024 |
| 10GX | 3.20 Å | +0.0041 |
| 9V35 | 2.97 Å | +0.0061 |
| 9VJD | 2.86 Å | +0.0084 |
| 9V4D | 3.07 Å | +0.0115 |
| 10QT | 3.40 Å | +0.0118 |

**Three entries breach −0.02**, the worst by more than 2×. And the split is by resolution, exactly as
the X-ray §4 bands turned out to be:

| Subset | n | CC_mask Δ min | median |
|---|---:|---:|---:|
| < 3.0 Å | 7 | **−0.0139** | −0.0019 |
| ≥ 3.0 Å | 6 | **−0.0475** | −0.0165 |

A null real-space refinement costs a ≥ 3.0 Å map more than 3× as much CC_mask as a < 3.0 Å one.
The band becomes resolution-conditional, mirroring §4's Cα-shift and favored-% bands.

`d_FSC_model` also tightened: with 12 measured entries the max |Δ| is **0.0322 Å** against ± 0.05 Å —
**1.55× headroom**, not the 5× that 6 entries suggested.

## 3. Rotamer library — there *is* an independent second opinion

Rounds 8 and 10 recorded "no non-cctbx rotamer library is installed" and closed the item as a dead
end. That was true of *rotamer classifiers* and false of *libraries*: the **CCP4 monomer library**
carries its own chi torsion targets, e.g.

```
LEU chi1 N CA CB CG -60.000 10.0 3     # target, sigma, periodicity
```

and `gemmi rmsz` scores every sidechain torsion against them. That is genuinely different **data**,
not merely different code — which is what the question had lacked.

Median CCP4 torsion |Z| grouped by MolProbity's verdict, over **8054 sidechains** in 17 entries:

| MolProbity verdict | n | median CCP4 torsion \|Z\| |
|---|---:|---:|
| Favored | 7141 | **1.50** |
| Allowed | 803 | **3.30** |
| OUTLIER | 110 | **4.33** |

The ordering is monotonic and well separated. Two independent libraries — MolProbity's Top8000
density and the CCP4 monomer library's torsion targets — agree about which sidechains are unusual,
which is the corroboration the ± 1.0 pp band never had.

This does not measure favored % directly: the two answer different questions (density percentile vs
deviation from a target torsion), so they cannot be differenced. But "no independent path" was
wrong, and the tolerance is no longer resting on an untested shared-library assumption.

## Applied

> **§4 `< 2.5 Å` Cα shift: `RMSD_post ≤ RMSD_pre + 0.12 Å`** (was 0.10, breached by 43SK at
> 0.1011 Å over 19 entries).
>
> **Map-model CC_mask is resolution-conditional**: `< 3.0 Å` → `CC_mask_post ≥ CC_mask_pre − 0.02`
> (null min −0.0139); `≥ 3.0 Å` → **− 0.06** (null min −0.0475). The single −0.02 band from round 10
> was breached by 3 of 13 entries, all at ≥ 3.0 Å.
>
> **`d_FSC_model` ± 0.05 Å retained**, but headroom is now **1.55×** (max |Δ| 0.0322 Å over 12
> entries), not the 5× that 6 entries suggested. Expect this to be the next band to break.
>
> **Rotamer favored % ± 1.0 pp** is corroborated, not merely assumed: an independent library agrees
> monotonically on sidechain quality (median torsion |Z| 1.50 / 3.30 / 4.33 for Favored / Allowed /
> OUTLIER).

## Scope limits

- 13 EM entries with 2 `real_space_refine` failures (9VXE, 13GH) reported rather than dropped. The
  ≥ 3.0 Å CC_mask band rests on 6 entries — thin, and the same shape of thinness that has now broken
  twice in a row.
- The 3.0 Å split for CC_mask is chosen to separate the observed groups, not measured; nothing lies
  between 2.97 and 3.07 Å.
- The cross-library comparison is ordinal. It shows the libraries agree on ranking, not that they
  would agree on a favored-% figure, which remains unmeasurable.
- All refinements 3 macro-cycles, default weights.
