# Driving example — T10 Ligand fitting

Standalone per-task driver for **T10 (ligand fitting)**. Follows the structure of
`ref/driving_example.md`. Graded by **cross-tool agreement** on the ligand's fit to density and its
pose, with the deposited ligand as tiebreaker.

> **Thresholds are defined once** in `ref/thresholds_and_standards.md`; the `[provenance]` tags below
> point into it.

## Scenario

The agent is handed a model + map/data + a ligand to fit into difference density, and asked to place
the ligand and report its fit and pose.

## Dataset — concrete IDs

- **Primary:** a deposited protein–ligand complex + its MTZ (the deposited ligand pose is the
  reference), e.g. any PDB-REDO ligand entry.

## What the agent must do

1. Run `phenix.ligandfit` / `phenix.ligand_pipeline`.
2. Record ligand RSCC, RSR, ligand-B vs surroundings, protein–ligand H-bond count, and RMSD to the
   deposited ligand pose.
3. Expected artefacts: the fitted ligand + report.

## Independent cross-checks (harness, not agent)

- **EDSTATS** — independent per-ligand real-space correlation (RSCC) and RSR.
- **`gemmi` script** — independent ligand B-factor comparison and RMSD to the deposited pose.
- **MolProbity `probe`** — independent protein–ligand contact / H-bond count.

## Scoring rubric

Each bullet is pass/fail; all must pass for green.

1. **Ligand fits the density (accuracy).** EDSTATS real-space difference-density Z-score **RSZD**
   is within **±3σ** (no significant misplaced-atom or unexplained-density outlier), and the
   observed-density Z-score **RSZO** is above **~1σ**. These are the B-factor-independent metrics;
   RSCC/RSR have no resolution-independent significance criterion (Tickle 2012). `[literature — real-space density fit]`
2. **RSCC is corroboration-only.** If RSCC is reported alongside, it must be computed with a
   **matched limiting-radius convention** between tools before any ±0.05 comparison is meaningful —
   otherwise the radius convention alone can swing it. `[literature — real-space density fit]`
3. **Correct pose vs deposited.** RMSD to the deposited ligand pose is within **± 0.10 Å** of an
   independent `gemmi` superposition. `[template — CA RMSD]`
4. **B-factor sanity.** The ligand's mean B relative to its surroundings is recorded — a ligand B far
   above its contacts signals a fit into noise even at acceptable RSCC.

## Notes

- RSCC and pose must both hold: a ligand can score acceptable RSCC in the wrong orientation (rule 3),
  or sit in a plausible pose with weak density (rule 1). Both rules together catch each failure mode.
