# Driving example — T07 Predicted-model processing

Standalone per-task driver for **T07 (predicted-model processing)**. Follows the structure of
`ref/driving_example.md`. Graded by **cross-tool agreement** against independent AlphaFold parsers and
PAE-clustering, with the experimental structure (where one exists) as tiebreaker.

> **Thresholds are defined once** in `ref/thresholds_and_standards.md`; the `[provenance]` tags below
> point into it.

## Scenario

The agent is handed an AlphaFold/RoseTTAFold prediction (PDB/mmCIF with pLDDT in the B-factor column,
optional PAE JSON) and asked to process it: trim low-confidence residues, split domains, and — where
an experimental structure exists — report RMSD to it.

## Dataset — concrete IDs

- **Primary:** `AF-P00698-F1` (lysozyme AF2 model) vs experimental PDB `2LYZ`.
- **Multimer:** `AF-P0DTC2-F1` (SARS-CoV-2 spike) vs `6VXX`.

## What the agent must do

1. Run `phenix.process_predicted_model` (trim by pLDDT, optional PAE-based domain split).
2. Record fraction retained after trim, mean pLDDT pre/post, domain count, and RMSD to the
   experimental structure where available.
3. Expected artefacts: the processed model + report.

## Independent cross-checks (harness, not agent)

- **biotite AF parsers** — independent pLDDT read and mean pLDDT before/after.
- **`pae_to_domains.py`** (Croll/Tronrud) — independent PAE-clustering domain count.
- **TM-align / OpenStructure** — independent RMSD/lDDT to the experimental structure.

## Scoring rubric

Each bullet is pass/fail; all must pass for green.

1. **pLDDT trim threshold.** Residues trimmed as low-confidence are those with **pLDDT < 70**; the
   retained set is confident (≥ 70). `[literature — pLDDT confidence cutoff]`
2. **pLDDT read agrees.** Mean pLDDT (pre and post) agrees with the biotite AF-parser read within
   **± 1.0** pLDDT unit. `[template]`
3. **Domain count agrees.** The agent's domain count matches the `pae_to_domains.py` clustering; a
   differing count must be explained by a stated PAE cutoff, not passed silently. `[template]`
4. **RMSD to experimental is TM-align-corroborated.** Where an experimental structure exists, the
   processed-model RMSD/TM-score agrees with TM-align (fold-level: TM-score > 0.5 = same fold).
   `[literature — TM-score fold call]`

## Notes

- pLDDT lives in the B-factor column post-conversion; confirm the `B ↔ (1/pLDDT²)` convention the
  agent used, or the "mean pLDDT" numbers are not comparable across tools.
