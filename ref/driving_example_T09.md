# Driving example — T09 Molecular replacement

Standalone per-task driver for **T09 (molecular replacement)**. Follows the structure of
`ref/driving_example.md`. Phaser's own scores (TFZ/LLG) have **no independent oracle**
(`ref/oracle_tools.md`); T09 is therefore graded at the **outcome** level — the placed pose and the
post-MR R-free — cross-checked independently.

> **Thresholds are defined once** in `ref/thresholds_and_standards.md`; the `[provenance]` tags below
> point into it.

## Scenario

The agent is handed a search model + reflection data and asked to solve the structure by molecular
replacement and report solution confidence, the placed pose, and the post-MR R-free.

## Dataset — concrete IDs

- **Primary:** any deposited structure with a suitable homolog search model + public MTZ (PDB-REDO
  supplies both), where the deposited pose is the reference.

## What the agent must do

1. Run `phenix.phaser` MR.
2. Record TFZ, LLG, the placed pose, and R-free after a short refinement.
3. Expected artefacts: the MR solution + refinement log.

## Independent cross-checks (harness, not agent)

- **MOLREP / MoRDa / ARCIMBOLDO** — an *independent* MR program; a genuinely independent second
  solution confirms the placement (Phaser standalone does **not** — same lineage as `phenix.phaser`).
- **`gemmi align`** — RMSD of the placed pose to the deposited structure.
- **REFMAC5** — independent post-MR R-free after a short re-refinement.

## Scoring rubric

Each bullet is pass/fail; all must pass for green.

1. **Confident Phaser solution.** TFZ **> 8** (McCoy 2007 — "definitely solved"); 5–8 is ambiguous and
   must be corroborated by an independent MR program before passing. `[literature — Phaser MR solution]`
2. **Correct pose vs deposited.** RMSD of the placed model to the deposited structure is within
   **± 0.10 Å** of an independent `gemmi align` superposition. `[template — CA RMSD]`
3. **Post-MR R-free sane.** After a short refinement, R-free is within **± 0.02** of a REFMAC5
   re-refinement and drops toward the deposited value. `[catalog — R-free vs deposited]`
4. **TFZ/LLG recorded, not graded alone.** Phaser scores are method-specific and have no independent
   oracle — they are reported, but the pass turns on the outcome checks above.

## Notes

- A high TFZ with a *wrong* pose (rule 2 fails) is a mispackable solution — the outcome checks, not the
  score, are load-bearing, which is why T09 is graded at the outcome level.
