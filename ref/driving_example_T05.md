# Driving example — T05 Geometry validation

Standalone per-task driver for **T05 (geometry validation)**. Follows the structure of
`ref/driving_example.md`. The task is graded by **cross-tool agreement**, not by an absolute
quality bar: whether a structure is "good" is resolution-dependent and belongs to that structure,
not to this task template. What the template checks is that the agent's geometry tool and the
independent oracle agree on the same model, and that outliers are counted against the standard
percentile definitions.

Every scoring threshold carries a `[provenance]` tag naming its source, so a reviewer can audit or
adjust it. Tags: `[schema]` = a threshold committed in `schemas/protstruct_review.yaml`
(`ResidueOutlierKind`); `[MolProbity]` = the Richardson-lab Top8000 percentile standard;
`[template]` = the agreement tolerance already used in `ref/driving_example.md`; `[calibration]` =
a sanity check against a deposited comparator.


> **Thresholds are defined once** in `ref/thresholds_and_standards.md`; the `[provenance]` tags below point into it.

## Scenario

The agent is handed a single model (PDB/mmCIF) and asked to validate its stereochemistry: report
clashscore, Ramachandran favored/outlier %, rotamer outlier %, Cβ deviations, and bond/angle RMSDs.
The harness independently re-runs MolProbity on the same model and checks the two agree.

## Dataset — concrete IDs

- **Primary:** PDB `3NIR` (crambin, 0.48 Å) — a clean ultra-high-resolution baseline where outlier
  counts should be near zero, so a spuriously high outlier count exposes a pipeline bug.
- **Stress model:** any moderate-resolution entry with known outliers, e.g. PDB `1SAR` (1.20 Å,
  the harness's standing test artifact), to confirm the tools agree on a model that *has* outliers.

## What the agent must do

1. Run `phenix.holton_geometry_validation model.pdb` (and/or `mmtbx.validation_summary model.pdb`).
2. Record: clashscore, Ramachandran favored %, Ramachandran outlier %, rotamer outlier %,
   Cβ outlier count, bond-length RMSD, bond-angle RMSD, MolProbity composite.
3. Expected artefacts: the validation log and a parsed metrics table.

## Independent cross-checks (harness, not agent)

- **MolProbity standalone** — the Richardson-lab `probe` + `reduce` pipeline (installed; see
  `ref/oracle_tools.md`), or `molprobity.molprobity`. Re-derives clashscore, Ramachandran, rotamer,
  and Cβ independently of cctbx's own reduce build.
- **`gemmi validate`** — independent bond/angle geometry parser.

## Scoring rubric

Each bullet is pass/fail; all must pass for green. Log the numeric delta that trips any failure.

1. **Outliers counted against the standard percentile definitions.** Ramachandran outlier = φ,ψ
   outside the 99.95th percentile of Top8000; rotamer outlier = χ outside the 98th percentile
   favored region; Cβ outlier = deviation > 0.25 Å; clash = steric overlap ≥ 0.4 Å.
   `[schema ResidueOutlierKind]` `[MolProbity]`
2. **Clashscore agreement.** PHENIX clashscore and MolProbity-standalone clashscore agree within
   **±1.0** on the same model. Disagreement signals a hydrogen-build or parameterisation difference,
   not a real geometry change. `[template check 7]`
3. **Ramachandran / rotamer agreement.** Favored % agree within **±1.0 percentage point**; outlier
   % within **±0.5 pp**. `[template check 5, tolerance direction]`
4. **Bond/angle RMSD agreement.** PHENIX vs `gemmi validate` bond-length RMSD within **±0.003 Å**.
   Bond-**angle** RMSD is restraint-library-dependent: **±0.1° only if both tools use the same
   library**, else **±0.4°** (PHENIX CDL vs gemmi Engh & Huber differ by 0.3–0.4° for library reasons
   alone). Record the restraint-library + tool versions. `[template — bond-angle RMSD]`
5. **Calibration on the clean baseline.** On `3NIR`, clashscore ≤ 2 and Ramachandran outliers = 0.
   A clean 0.48 Å structure scoring otherwise means the pipeline itself is miscalibrated, not the
   model. `[calibration — 3NIR ultra-high-res]`
6. **H-build disclosure.** If clashscore is reported, the hydrogen-addition step (`reduce -build`
   vs `phenix.reduce`) must be recorded, since clashscore shifts ~0.5 between builds. Absence of the
   disclosure is a fail. `[schema/handbook — MolProbity tool assumptions]`

## Notes

- This task grades **agreement and reproducibility**, not structure quality. An intentionally poor
  model still passes T05 if both tools agree it is poor — that is the correct behaviour.
- The absolute quality thresholds for a *specific* refinement (e.g. "clashscore must improve") live
  in the compare→refine driver `ref/driving_example.md`, not here.
- Provenance tags marked `[template]`/`[calibration]` are agreement tolerances and sanity checks,
  not scientific quality claims, and are safe to tune. Tags marked `[schema]`/`[MolProbity]` are
  standard definitions — change them only if the upstream standard changes.
