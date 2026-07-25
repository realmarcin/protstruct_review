# Tolerance benchmark — interface buried surface area (biotite SASA vs PDBePISA)

De-provisionalizes `Interface buried surface area` in `ref/thresholds_and_standards.md` and the
`T16_interface_buried_surface_area` entry in `ref/structural_criteria.yaml` (GitHub #18). The
previous `|Δ| ≤ 10 %` was `[template]`-inferred: the mechanism (different surface algorithm,
different interface-area definition) was real but the **magnitude was never measured**. This is the
measurement.

Reproduce with:

```bash
python3 scripts/bench_t16_bsa_vs_pisa.py --cache <dir> --json <out.json>
```

## Configuration (matched, per the tolerance's own precondition)

| | biotite | PDBePISA |
|---|---|---|
| Algorithm | Shrake–Rupley (numerical, 100 points/atom) | Lee & Richards (analytical rolling-sphere) |
| Probe radius | 1.4 Å | 1.4 Å |
| Radii set | ProtOr (biotite default; H excluded) | PISA internal |
| Atom selection | `struc.filter_amino_acids` — protein only, no waters, no hetero | assembly molecules incl. ligand/hetero atoms |
| Quantity reported | ΣSASA(chains) − SASA(complex) = **both** sides | `interface_area` = **one** side (the mean of the two) |

The two quantities differ by a factor of two by definition, so the comparison is
biotite BSA vs **2 × PISA `interface_area`**. Failing to halve/double is the single largest error
mode here — it produces a 100 % "disagreement" that is pure bookkeeping.

PISA values come from the PDBe REST API for **biological assembly 1**
(`https://www.ebi.ac.uk/pdbe/api/pisa/interfaces/<id>/1`), not the interactive web server — the
same PISA 2.0 computation, machine-readable. Coordinates are the deposited asymmetric unit from
RCSB. Interfaces between two copies of the same author chain (symmetry mates) are **excluded**: the
ASU cannot reproduce them without applying the operator, so they would compare different atoms.

## Test set and results

26 protein–protein interfaces across 14 entries, spanning 216 → 2853 Å² per side: protease–inhibitor
and other transient complexes, two antibody–antigen complexes, large obligate interfaces, and one
multi-interface oligomer (4HHB, haemoglobin — 5 distinct interfaces).

| Entry | Interface | biotite BSA (Å², total) | PISA area (Å², per side) | PISA × 2 (Å²) | Δ (Å²) | Δ (%) |
|---|---|---:|---:|---:|---:|---:|
| 1CHO | E/G | 472.9 | 215.9 | 431.9 | +41.0 | +9.06 |
| 4HHB | A/C | 562.7 | 274.7 | 549.5 | +13.2 | +2.37 |
| 1VFB | A/C | 697.6 | 336.2 | 672.4 | +25.2 | +3.67 |
| 1CHO | F/I | 716.5 | 345.6 | 691.2 | +25.3 | +3.59 |
| 3HFM | L/Y | 727.5 | 355.9 | 711.7 | +15.7 | +2.19 |
| 1VFB | B/C | 810.6 | 392.6 | 785.2 | +25.4 | +3.18 |
| 1CHO | E/F | 953.4 | 461.6 | 923.3 | +30.1 | +3.20 |
| 3HFM | H/Y | 994.7 | 487.1 | 974.2 | +20.5 | +2.08 |
| 1CHO | G/I | 1034.6 | 491.0 | 981.9 | +52.7 | +5.22 |
| 1E96 | A/B | 1195.9 | 590.2 | 1180.3 | +15.5 | +1.31 |
| 1AY7 | A/B | 1247.5 | 616.9 | 1233.8 | +13.7 | +1.11 |
| 3SGB | E/I | 1281.1 | 633.2 | 1266.3 | +14.7 | +1.16 |
| 1GLA | F/G | 1310.4 | 650.9 | 1301.8 | +8.6 | +0.66 |
| 4HHB | A/D | 1365.2 | 674.8 | 1349.5 | +15.6 | +1.15 |
| 4HHB | C/B | 1364.5 | 679.3 | 1358.5 | +6.0 | +0.44 |
| 2PTC | E/I | 1439.7 | 714.3 | 1428.5 | +11.2 | +0.78 |
| 1BRS | A/D | 1569.1 | 778.5 | 1557.0 | +12.1 | +0.78 |
| 1AVX | A/B | 1599.2 | 792.1 | 1584.1 | +15.1 | +0.95 |
| 1VFB | A/B | 1610.8 | 795.5 | 1590.9 | +19.9 | +1.24 |
| 2SIC | E/I | 1621.7 | 806.9 | 1613.7 | +8.0 | +0.49 |
| 4HHB | A/B | 1654.0 | 820.9 | 1641.7 | +12.3 | +0.74 |
| 4HHB | C/D | 1701.4 | 846.6 | 1693.3 | +8.1 | +0.48 |
| 1FSS | A/B | 1988.1 | 980.8 | 1961.5 | +26.6 | +1.35 |
| 1DFJ | E/I | 2622.6 | 1284.7 | 2569.5 | +53.2 | +2.05 |
| 3HFM | L/H | 3724.6 | 1838.6 | 3677.2 | +47.4 | +1.28 |
| 1CHO | F/G | 5830.4 | 2853.0 | 5706.0 | +124.4 | +2.16 |

Distribution of |Δ|: **median 1.29 %, 90th percentile 3.59 %, max 9.06 %**; in absolute terms
median 15.6 Å², max 124.4 Å².

## Findings

**1. The disagreement is one-sided, not scatter.** biotite is larger than 2 × PISA in **26 of 26**
interfaces — there is not one negative Δ. This is a systematic offset, not noise: a signed median of
+1.29 % with zero sign changes. The likely contributors are the radii set (ProtOr vs PISA's internal
radii), Shrake–Rupley's 100-point quadrature vs an analytical Lee–Richards surface, and PISA
counting ligand/hetero atoms in the molecule surface where the harness recipe counts protein atoms
only. Because the offset is one-directional, a symmetric ± tolerance is the wrong shape in
principle; it is kept only because the offset is small enough that a symmetric bound is not
misleading in practice.

**2. Relative error is dominated by interface size, not by complex type.** Split at 1200 Å² total:

| Subset | n | median \|Δ\| | max \|Δ\| |
|---|---:|---:|---:|
| < 1200 Å² total (< 600 Å² per side) | 10 | 3.19 % | 9.06 % |
| ≥ 1200 Å² total | 16 | 1.03 % | 2.16 % |

The absolute Δ does **not** scale with area (it ranges 6.0 → 124.4 Å² with no clean proportionality),
so relative error blows up on small interfaces. The worst case, 1CHO E/G at 216 Å² per side, sits
just above the harness's own "< ~200 Å² is a crystal-packing contact" anomaly threshold — i.e. the
regime where relative agreement is worst is also the regime where the measurement is least
meaningful.

**3. The provisional ±10 % was ~4× too loose for real interfaces** and, taken as a relative bound
alone, still too tight to be safe on tiny ones. A single percentage cannot express both.

## Applied tolerance

> **|Δ| ≤ 3 % of the mean, or 60 Å², whichever is larger** — biotite SASA vs PISA, matched probe
> radius (1.4 Å), protein-only atom selection, and the PISA per-side area doubled. Expect biotite to
> read **high**; a negative Δ is off-distribution and worth investigating.

This envelope covers 26/26 measured interfaces with headroom (the tightest envelope that still
covers all 26 is max(2.5 %, 55 Å²)); the round form is preferred given n = 26. On interfaces above
~1200 Å² the 3 % term binds and is ~3× tighter than the retired ±10 %; below that the 60 Å² floor
binds, which is what makes small-interface comparisons survivable.

## Scope limits

- Measures the **tool-definition noise floor on identical deposited coordinates**. It does not
  bound how much BSA moves when the *model* changes (refinement, agent edits) — that is a different
  quantity and is not benchmarked here.
- All 26 interfaces are protein–protein. Nucleic-acid and protein–ligand interfaces are unmeasured;
  the protein-only atom selection makes them out of scope for this tolerance as written.
- PISA assembly 1 only. Alternative assemblies were not tested.
- Single PISA version (2.0, as served by the PDBe API on 2026-07-24) and biotite 1.7.1.
