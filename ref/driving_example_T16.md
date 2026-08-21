# Driving example — T16 Interface and assembly quality

Standalone per-task driver for **T16 (interface and assembly quality)**. Follows the structure of
`ref/driving_example.md`. T16 is oracle-only (no PHENIX interface scorer); the deposited biological
assembly is the reference, which is the trust model's tiebreaker.

> **Thresholds are defined once** in `ref/thresholds_and_standards.md`; the `[provenance]` tags below
> point into it. This task is **runnable now** via `scripts/t16_interface_quality.py` (DockQ + biotite
> SASA).

## Scenario

The agent is handed a complex/assembly model — for a predicted or refined interface, plus the
deposited reference assembly — and asked to report interface quality: buried surface area, the DockQ
score against the reference, and its CAPRI class.

## Dataset — concrete IDs

- **Primary:** PDB `1BRS` (barnase–barstar, a canonical tight complex).
- **Second complex:** PDB `2SIC` (subtilisin–SSI).
- **Demonstrated calibration:** identity DockQ on the verified RCSB download
  `data/pdb_mtz/1sar_deposited.pdb` A/B → **1.000, class High**; its interface buries
  **442.1 Å²** (`scripts/t16_interface_quality.py`).

## What the agent must do

1. Compute the interface buried surface area (Å²) for the model complex.
2. Score the model interface against the deposited reference with DockQ; report the DockQ score and
   the CAPRI quality class.
3. Expected artefacts: the DockQ JSON and a parsed metrics table.

## Independent cross-checks (harness, not agent)

- **`scripts/t16_interface_quality.py`** runs **DockQ** (model vs native → DockQ score, CAPRI class
  derived from the Basu & Wallner 2016 bands) and **biotite SASA** (Shrake-Rupley buried surface
  area from the model alone — an installable stand-in for PISA). Both are non-cctbx.
- **PISA/PDBePISA** corroborates buried surface area and biological-assembly inference where the web
  service is reachable (the deposition-grade reference).

## Scoring rubric

Each bullet is pass/fail; all must pass for green.

1. **DockQ reproduces.** With the **same chain mapping**, the agent's DockQ agrees with the harness
   DockQ within **± 0.01** (same-implementation noise floor ≈ 0.004); the **CAPRI class matches**,
   except it is not flagged when either score is within **± 0.03** of a class boundary
   (0.23 / 0.49 / 0.80). `[template — DockQ score]`
2. **Buried surface area agrees.** The agent's BSA agrees with the biotite-SASA (or PISA) value within
   **± 10 %**. `[template — interface buried surface area]`
3. **CAPRI class matches the score.** The reported class is consistent with the DockQ score under the
   standard bands (High ≥ 0.80; Medium ≥ 0.49; Acceptable ≥ 0.23; Incorrect < 0.23).
   `[literature — CAPRI class from DockQ]`
4. **Identity calibration.** Scoring the deposited reference against itself gives DockQ **1.000** and
   class **High**; anything else exposes a chain-mapping or parsing bug, not a model defect.
   `[calibration]`
5. **Chain mapping disclosed.** The model→native chain mapping used by DockQ is recorded — a wrong
   mapping silently deflates the score.

## Notes

- BSA is a property of the model alone (no reference needed) and is always computable; DockQ needs the
  deposited reference. `scripts/t16_interface_quality.py` reflects this — BSA always, DockQ only with
  `--native`.
- PISA remains the `top_considered` BSA oracle (deposition-grade); biotite SASA is the runnable
  `top_performing` stand-in when the web service is unreachable.
