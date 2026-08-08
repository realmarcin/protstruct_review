# Negative-control benchmark, phase 1: residue-level masks

**Built 2026-08-08** by `scripts/gold_mask.py` (#295, phase 1 of
`negative_control_benchmark_plan.md`), demonstrated on the 12 percentile-sample
entries from phase 0. Committed masks: `ref/research/data/masks/<ID>_mask.json`,
one reason per residue. Reproduce with:

```
python3 scripts/gold_mask.py --ids-json ref/research/data/negative_control_phase0_counts.json
```

Window context: the project owner approved ≤ 1.0 Å, one representative per 30 %
cluster, ≤ 0.9 Å as a stratum label (#295, 2026-08-08).

## Rules applied

Masked (excluded from scoring): **altconf** (any alternate conformation —
Top2018 precedent), **rsrz_outlier** (|RSRZ| > 2, the wwPDB definition),
**high_b** (owab > 2× entry median — relative tail; an absolute Top2018-style
B ≤ 40 is vacuous at sub-Å), **lattice_contact** (any atom within 4.0 Å of a
symmetry-mate non-water atom — CASP14 precedent). Protected (kept, inverted):
deposited rama/rota/clash outliers on residues that survived masking — protection
applies AFTER masking (#298), so every protected outlier is density-supported by
construction. |RSRZ| > 2 has wwPDB provenance; the B tail factor, contact cutoff,
and clash protection are scouting values the phase-2 preregistration finalizes
(#297 discipline). Known limitation: ASU-internal chain interfaces are ambiguous
(biological vs packing) and are NOT masked; the preregistration must decide them.

## Measured on the 12 sample entries

| entry | residues | masked | fraction | unmasked | protected |
|---|---:|---:|---:|---:|---:|
| 1EJG | 46 | 29 | 63 % | 17 | 0 |
| 1UG6 | 430 | 82 | 19 % | 348 | 13 |
| 2VXN | 257 | 101 | 39 % | 156 | 2 |
| 3AGN | 116 | 54 | 47 % | 62 | 0 |
| 5DGJ | 169 | 86 | 51 % | 83 | 1 |
| 5OAV | 134 | 98 | 73 % | 36 | 0 |
| 5RC3 | 339 | 74 | 22 % | 265 | 3 |
| 6UWW | 167 | 53 | 32 % | 114 | 2 |
| 6Y0H | 189 | 58 | 31 % | 131 | 4 |
| 7A2Y | 73 | 47 | 64 % | 26 | 0 |
| 7HFO | 338 | 193 | 57 % | 145 | 1 |
| 9YGW | 394 | 142 | 36 % | 252 | 9 |

Mask fraction 0.19–0.73, median 0.43 — squarely in Top2018's 35–45 % residue-level
removal band, with small proteins skewing high (lattice contacts dominate: 629
lattice-contact reasons vs 385 altconf, 133 high_b, 132 rsrz_outlier across the
set; a residue can carry several reasons).

## Findings for the phase-2 preregistration

1. **The strict selection tier starves the protection mechanism.** All 35
   protected outliers are clash-protected; zero rama/rota protections exist in
   the sample — by construction, because the strict tier demands zero
   Ramachandran outliers and ≤ 0.3 % rotamer outliers, which removes exactly the
   entries carrying density-supported genuine outliers (the Arg126-guanidinium
   class the plan's confound section names). The preregistration must choose:
   accept clash-only protection, or relax the rama/rota cuts slightly so the
   genuine-outlier population survives selection.
2. **Small entries may need an unmasked-residue floor.** 1EJG keeps 17 scoring
   residues, 7A2Y keeps 26; a degradation verdict on 17 residues is noisy.
   Candidate rule: enroll only entries with ≥ N unmasked residues (N set at
   preregistration).
3. **Scoring universes are otherwise viable**: unmasked residues range 17–348,
   with 9 of 12 entries above 60.
