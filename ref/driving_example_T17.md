# Driving example — T17 NMR ensemble/restraint validation

Standalone per-task driver for **T17 (NMR ensemble/restraint validation)**. Follows the structure of
`ref/driving_example.md`. T17 is oracle-only (no PHENIX NMR validator); the deposited ensemble and its
wwPDB validation report are the reference.

> **Thresholds are defined once** in `ref/thresholds_and_standards.md`; the `[provenance]` tags below
> point into it. The **precision metric is runnable now** via `scripts/t17_nmr_ensemble.py`; the
> restraint-violation summary still needs the wwPDB report (open — issue #3).

## Scenario

The agent is handed a multi-model NMR ensemble (and, where available, the deposited restraints) and
asked to report ensemble precision — how tightly the models agree — and, informationally, a summary
of restraint violations.

## Dataset — concrete IDs

- **Primary:** PDB `1D3Z` (ubiquitin, 10-model NMR ensemble, deposited restraints + wwPDB NMR
  validation report). Committed as `data/pdb_mtz/1d3z.pdb`.
- **Demonstrated calibration:** `scripts/t17_nmr_ensemble.py data/pdb_mtz/1d3z.pdb` → mean Cα RMSF
  **0.428 Å** over 10 models (range 0.139–5.927 Å; flexible termini raise the max).

## What the agent must do

1. Compute ensemble precision — the mean per-residue Cα fluctuation about the ensemble mean, after
   superposing every model onto a reference model.
2. Where restraints are available, summarise distance/angle restraint violations (informational).
3. Report the precision as a single RMSF value in Å.

## Independent cross-checks (harness, not agent)

- **`scripts/t17_nmr_ensemble.py`** superposes all models with **biotite** and reports the mean Cα
  RMSF about the ensemble mean (non-cctbx, from the ensemble alone — no restraints needed).
- **wwPDB NMR validation report** is the deposition-grade source for both precision and restraint
  statistics, and is the tiebreaker where the local computation and the agent disagree.

## Scoring rubric

Each bullet is pass/fail; all must pass for green.

1. **Precision reproduces.** The agent's mean Cα RMSF agrees with the harness recomputation within
   **± 0.05 Å**. `[template — NMR ensemble precision]`
2. **Ordered-region sanity.** After excluding flexible termini/loops (per-residue RMSF > 2 Å), the
   ordered core precision is sub-Ångström for a well-determined ensemble; a whole-chain mean inflated
   by disordered tails must be reported *with* the ordered-core figure, not instead of it.
   `[calibration]`
3. **Superposition reference disclosed.** The reference model and atom selection used for
   superposition are recorded — RMSF depends on both, so an undisclosed superposition makes the
   number uninterpretable.
4. **Restraint summary is informational.** Restraint-violation counts carry
   `pass_status: informational` and are cross-checked against the wwPDB report when present; they are
   never the sole pass criterion (the gradeable metric is the numeric precision). `[schema/handbook]`

## Notes

- Precision is computed from the ensemble alone, so the numeric metric runs today without the wwPDB
  report. The **restraint-violation summary** does need the deposited restraints + report and is the
  remaining T17 piece (issue #3).
- Flexible termini dominate a naïve whole-chain RMSF (1D3Z: 0.14 Å core vs 5.9 Å tail). Always
  separate ordered-core precision from the disordered tails when reporting.
