# Driving example — T02 Per-residue structural comparison

Standalone per-task driver for **T02 (per-residue structural comparison)**. Follows the structure of
`ref/driving_example.md`. Graded by **cross-tool agreement**: an independent per-residue comparator
must corroborate the agent's PHENIX `structure_comparison`, per residue.

> **Thresholds are defined once** in `ref/thresholds_and_standards.md`; the `[provenance]` tags below
> point into it.

## Scenario

The agent is handed two or more near-identical models (crystal forms, mutants, NCS copies) and asked
to report per-residue differences: Ramachandran/rotamer outlier changes, secondary-structure changes,
B-factor deltas, ligand centre-of-mass shifts, omega (cis/trans) flips, His protonation differences.

## Dataset — concrete IDs

- **Primary:** a paired lysozyme mutant set, or NCS copies from one asymmetric unit.
- **Control:** a structure vs itself → all per-residue deltas ≈ 0 (calibration).

## What the agent must do

1. Run `phenix.structure_comparison model_A.pdb model_B.pdb`.
2. Record the per-residue deltas above and flag hotspot residues.
3. Expected artefacts: the comparison report + per-residue table.

## Independent cross-checks (harness, not agent)

- **OpenStructure** / **ProSMART** — independent per-residue Cα distance + geometry comparison.
- **`gemmi` script** — independent B-factor deltas and ligand centre-of-mass shifts (coordinate reads).
- **DSSP** — independent secondary-structure change per residue.

## Scoring rubric

Each bullet is pass/fail; all must pass for green.

1. **Per-residue Cα agreement.** PHENIX and OpenStructure per-residue Cα displacement agree within
   **± 0.10 Å** per residue (same tolerance as the T01 whole-structure RMSD). `[template — CA RMSD]`
2. **SS-change agreement.** Secondary-structure changes agree with a DSSP three-state re-assignment on
   **≥ 0.85** of residues. `[template — secondary-structure agreement]`
3. **Hotspots corroborated.** Every residue the agent flags as a hotspot is independently a per-residue
   Cα or geometry outlier in the cross-check; an un-corroborated hotspot is a fail.
4. **Identity calibration.** Comparing a model to itself gives all per-residue deltas ≈ 0; non-zero
   deltas expose an alignment/indexing bug, not a real difference. `[calibration]`

## Notes

- T02 is per-residue T01: the agreement is checked residue-by-residue, so a whole-structure RMSD that
  matches while individual residues diverge still fails rule 1.
