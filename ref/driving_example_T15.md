# Driving example — T15 Structural/domain classification

Standalone per-task driver for **T15 (structural/domain classification)**. Follows the structure of
`ref/driving_example.md`. T15 is oracle-only (no PHENIX classifier) and is graded by **cross-tool
agreement** between two independent secondary-structure assigners — the trust model applied to
categorical data (`CODING_STANDARDS.md` rule 9).

> **Thresholds are defined once** in `ref/thresholds_and_standards.md`; the `[provenance]` tags below
> point into it. This task is **runnable now** via `scripts/t15_ss_agreement.py` (DSSP + biotite
> P-SEA).

## Scenario

The agent is handed a model (PDB/mmCIF) and asked to assign secondary structure — a three-state
(H/E/C) label per residue — and, where a classification exists, domain boundaries and a fold id. The
harness independently re-assigns secondary structure with two non-cctbx tools and scores agreement.

## Dataset — concrete IDs

- **Primary:** PDB `1AKE` (adenylate kinase, multi-domain, CATH-classified) — exercises both SS and
  domain assignment.
- **Single-domain control:** PDB `2LYZ` (hen lysozyme).
- **Demonstrated calibration:** verified RCSB download `data/pdb_mtz/1sar_deposited.pdb` A/B →
  DSSP-vs-biotite three-state agreement **0.8646** over 192 residues
  (`scripts/t15_ss_agreement.py`).

## What the agent must do

1. Assign three-state secondary structure per residue (via DSSP, or its own method, stated).
2. Where available, report domain boundaries and a CATH/SCOPe/ECOD fold id (informational).
3. Report the secondary-structure agreement against an independent assigner as a single fraction.

## Independent cross-checks (harness, not agent)

- **`scripts/t15_ss_agreement.py`** runs **DSSP** (`mkdssp`, H-bond energetics) and **biotite P-SEA**
  (Cα geometry) — two non-cctbx, algorithmically distinct assigners — and reports the three-state
  agreement fraction plus per-residue labels.
- **CATH / SCOPe / ECOD** lookups corroborate the domain/fold labels where a deposited classification
  exists (informational).

## Scoring rubric

Each bullet is pass/fail; all must pass for green.

1. **Agent SS vs DSSP.** The agent's three-state labels agree with DSSP on **≥ 0.85** of the residues
   DSSP assigns. `[template — secondary-structure agreement]`
2. **Two-assigner floor.** DSSP-vs-biotite agreement on the same model is **≥ 0.80**; below this the
   structure is unusually disordered — flag in `notes`, do not silently pass a low number as quality.
   `[template]`
3. **Agreement number reproduces.** The agent's reported agreement fraction matches the harness
   recomputation within **± 0.02**. `[template]`
4. **Labels are informational.** Domain/fold labels carry `pass_status: informational`; they are
   recorded and cross-checked against CATH/SCOPe/ECOD but are never the sole pass criterion (the
   gradeable metric is the numeric agreement). `[schema/handbook]`
5. **Assigner disclosed.** The method the agent used to assign SS is recorded — DSSP and STRIDE and
   P-SEA disagree at loop/turn boundaries, so an undisclosed assigner makes the agreement number
   uninterpretable.

## Notes

- T15 grades **agreement**, not correctness of a single labelling: two independent assigners rarely
  hit 1.0 because H-bond and Cα-geometry methods draw helix/strand ends differently. The floor
  (rule 2) exists to catch genuinely disordered models, not to reward perfect agreement.
- STRIDE is the catalog-preferred second assigner but is not currently installable via Homebrew;
  biotite P-SEA is the runnable stand-in (`ref/oracle_tools.md`).
