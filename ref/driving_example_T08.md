# Driving example — T08 Docking predicted/homology model into a map

Standalone per-task driver for **T08 (docking a model into a cryo-EM map)**. Follows the structure of
`ref/driving_example.md`. Graded by **cross-tool agreement**: an independent map-fitting tool must
corroborate the placement, with the deposited EMDB–PDB pair as tiebreaker.

> **Thresholds are defined once** in `ref/thresholds_and_standards.md`; the `[provenance]` tags below
> point into it.

## Scenario

The agent is handed a predicted/homology model + a cryo-EM map (optional mask/centre guess) and asked
to dock the model into the map and report placement quality.

## Dataset — concrete IDs

- **Primary:** EMDB-`20646` / PDB `6u42` (deposited map + placed model = the reference pose).

## What the agent must do

1. Run `phenix.dock_predicted_model` / `phenix.dock_in_map`.
2. Record placement CC, ΔCC vs a random placement, RMSD to the deposited position, translation/rotation
   error.
3. Expected artefacts: the docked model + report.

## Independent cross-checks (harness, not agent)

- **ChimeraX `fitmap`** / **Situs** — independent rigid-body map fitting → independent placement CC and
  pose.
- **`gemmi align`** — independent superposition of the docked model onto the deposited pose → RMSD and
  translation/rotation error.

## Scoring rubric

Each bullet is pass/fail; all must pass for green.

1. **Placement CC agrees.** PHENIX placement CC and ChimeraX `fitmap` CC on the same map/model agree
   within **± 0.02**. `[template — map-model CC]`
2. **Correct pose vs deposited.** RMSD of the docked model to the deposited position is within
   **± 0.10 Å** of an independent (`gemmi align`) superposition to the same reference. `[template — CA RMSD]`
3. **Better than random.** ΔCC vs a randomised placement is clearly positive — a placement no better
   than random is a fail regardless of absolute CC.
4. **LLG is PHENIX-specific.** `phenix.em_placement` LLG has no independent equivalent (see
   `ref/oracle_tools.md` deliberate no-oracle gaps); it is recorded but never the sole pass criterion.

## Notes

- A high placement CC into a low-resolution map can still be the *wrong* pose; rule 2 (RMSD to the
  deposited position) is what distinguishes a correct dock from a plausible-looking wrong one.
