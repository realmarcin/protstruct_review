# Driving example — T12 Map quality assessment (cryo-EM)

Standalone per-task driver for **T12 (cryo-EM map quality assessment)**. Follows the structure of
`ref/driving_example.md`. Graded by **cross-tool agreement**: an independent FSC / local-resolution
estimate must corroborate PHENIX `mtriage`, with the EMDB-deposited resolution as tiebreaker.

> **Thresholds are defined once** in `ref/thresholds_and_standards.md`; the `[provenance]` tags below
> point into it.

## Scenario

The agent is handed two half-maps (optional mask, optional model) and asked to report global
resolution at the gold-standard FSC threshold, the local-resolution distribution, and (if a model is
given) model-map FSC.

## Dataset — concrete IDs

- **Primary:** EMDB-`11668` half-maps (apoferritin).
- **Second:** EMDB-`20646` half-maps.

## What the agent must do

1. Run `phenix.mtriage half_map_1.mrc half_map_2.mrc [mask] [model]`.
2. Record global FSC resolution at 0.143 (masked + unmasked), local-resolution mean/stdev/10th-90th,
   d_FSC_model (if model), B-factor sharpening estimate.
3. Expected artefacts: the mtriage report + FSC curve.

## Independent cross-checks (harness, not agent)

- **RELION `postprocess`** — the community reference for masked/unmasked global FSC resolution.
- **ResMap** — independent local-resolution estimate.
- EMDB-deposited resolution — the tiebreaker.

## Scoring rubric

Each bullet is pass/fail; all must pass for green.

1. **Gold-standard FSC threshold.** Global resolution is quoted at **FSC = 0.143** on the two
   independent half-maps; a resolution quoted at any other threshold (e.g. 0.5) is not comparable.
   `[literature — cryo-EM map resolution (FSC)]`
2. **Cross-tool resolution agreement.** PHENIX `mtriage` and RELION `postprocess` masked resolution on
   the same half-maps agree within **± 0.1 Å**. `[template]`
3. **Deposition sanity.** Reported global resolution is within **± 0.1 Å** of the EMDB-header value.
   `[calibration]`
4. **Masking disclosed.** Masked vs unmasked resolution differ substantially; the mask used must be
   recorded, or the two tools' numbers are not comparable.

## Notes

- Masking is the dominant source of cryo-EM resolution disagreement — over-masking inflates
  resolution. Rule 2 compares *masked* to *masked*; rule 4 forces the mask to be stated.
