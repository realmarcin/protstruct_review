# Thresholds and standards registry

The single source of truth for every numeric threshold the harness scores against. The per-task
driving examples (`driving_example_T<NN>.md`) and the combined `driving_example.md` cite this file
rather than restating values, so a threshold is defined once and audited once.

Each entry names its **provenance**, which also says how freely it may be changed:

| Tag | Meaning | Change policy |
|---|---|---|
| `[schema]` | A definition committed in `schemas/protstruct_review.yaml` (`ResidueOutlierKind`). | Change only with the schema. |
| `[MolProbity]` | Richardson-lab Top8000 percentile standard. | Tracks the upstream standard. |
| `[literature]` | A published threshold (cited in full below). | Tracks the cited paper. |
| `[catalog]` | A value stated in `ref/catalog.yaml`. | Change with the catalog. |
| `[template]` | A cross-tool **agreement tolerance** (how close two tools must land). | Safe to tune with evidence. |
| `[calibration]` | A sanity check against a known-good case or a deposition. | Safe to tune with evidence. |

`[template]` and `[calibration]` values are engineering tolerances, not scientific claims — tune them
as the harness accumulates evidence. `[schema]`, `[MolProbity]`, and `[literature]` values track
external standards — change them only when the standard does, and update the citation.

---

## 1. Standard outlier definitions

Committed in `schemas/protstruct_review.yaml::ResidueOutlierKind`; percentile bases are the
Richardson-lab Top8000 reference set (high-resolution ≤ 2.0 Å structures).

| Outlier | Definition | Provenance |
|---|---|---|
| Ramachandran outlier | backbone φ,ψ outside the **99.95th** percentile region | `[schema]` `[MolProbity]` |
| Rotamer outlier | side-chain χ outside the **98th** percentile favored region | `[schema]` `[MolProbity]` |
| Cβ deviation | > **0.25 Å** from ideal | `[schema]` |
| Clash | steric overlap ≥ **0.4 Å** | `[schema]` |
| Bad geometry | bond / angle / planarity > **4σ** | `[schema]` |
| Cis-peptide | non-Pro cis ω | `[schema]` |

> **Reference-set caveat.** Top8000 percentiles were built from ≤ 2.0 Å structures. Applying them to
> a lower-resolution model still computes a percentile, but the outlier bar was set against tighter
> geometry than that model can deliver — note it when a model is well below 2.0 Å.

## 2. Literature thresholds

| Quantity | Threshold | Source |
|---|---|---|
| TM-score fold call | **> 0.5** ≈ same fold; **< 0.17** ≈ random pair | Xu J, Zhang Y. *Bioinformatics* 2010; 26(7):889–895. `[literature]` |
| CC½ resolution-cutoff floor | high-resolution shell is usable while **CC½ ≳ 0.3** | Karplus PA, Diederichs K. *Science* 2012; 336(6084):1030–1033. `[literature]` |
| L-test twinning | untwinned ⟨\|L\|⟩ ≈ **0.5**; perfect twin ≈ **0.375** | Padilla JE, Yeates TO. *Acta Cryst.* D 2003; 59:1124–1130. `[literature]` |
| CAPRI class from DockQ | High **≥ 0.80**; Medium **[0.49, 0.80)**; Acceptable **[0.23, 0.49)**; Incorrect **< 0.23** | Basu S, Wallner B. *PLOS ONE* 2016; 11(8):e0161879. `[literature]` |

## 3. Cross-tool agreement tolerances

How close the agent's tool and the independent oracle must land on the **same** input. These grade
agreement, not quality.

| Metric | Tolerance | Tools | Provenance |
|---|---|---|---|
| CA RMSD | \|Δ\| ≤ **0.10 Å** | PHENIX `superpose_models` vs TM-align / ChimeraX / `gemmi align` | `[catalog]` `[template]` |
| Aligned-residue count | ± **2 residues** | same | `[template]` |
| Clashscore | ± **1.0** | PHENIX vs MolProbity standalone | `[template]` |
| Ramachandran / rotamer favored % | ± **1.0 pp** | same | `[template]` |
| Ramachandran / rotamer outlier % | ± **0.5 pp** | same | `[template]` |
| Bond-length RMSD | ± **0.003 Å** | PHENIX vs `gemmi validate` | `[template]` |
| Bond-angle RMSD | ± **0.1°** | same | `[template]` |
| Wilson B | ± **2 Å²** | `xtriage` vs `ctruncate` | `[template]` |
| L-test ⟨\|L\|⟩ | ± **0.02**, same twin/no-twin call | `xtriage` vs `ctruncate` | `[template]` |
| Completeness (overall) | ± **1 pp** vs deposition Table 1 | `xtriage` vs deposition | `[calibration]` |
| Secondary-structure agreement | agent-vs-DSSP three-state ≥ **0.85** over DSSP-assigned residues; two independent assigners floor ≥ **0.80** on a well-ordered model | agent vs DSSP; DSSP vs biotite P-SEA (`t15_ss_agreement.py`) | `[template]` |
| DockQ score | \|Δ\| ≤ **0.05** and identical CAPRI class | agent vs `t16_interface_quality.py` (DockQ) | `[template]` |
| Interface buried surface area | \|Δ\| ≤ **10 %** | agent vs biotite SASA (`t16_interface_quality.py`); PISA when available | `[template]` |
| NMR ensemble precision (mean Cα RMSF) | \|Δ\| ≤ **0.05 Å** | agent vs `t17_nmr_ensemble.py` | `[template]` |

## 4. Refinement Δ-tolerances (compare→refine flow)

Used by `driving_example.md` when a baseline exists. A refinement must not materially degrade these.

| Check | Tolerance | Provenance |
|---|---|---|
| ΔRMSD sanity | RMSD_post ≤ RMSD_pre + **0.05 Å** | `[template]` |
| Geometry did not degrade | clashscore_post ≤ max(clashscore_pre, **4**); Ramachandran favored_post ≥ min(favored_pre, **97%**); rotamer outliers_post ≤ max(outliers_pre, **2%**) | `[template]` |
| Map-model fit did not degrade | CC_mask_post ≥ CC_mask_pre − **0.01**; d_FSC_model_post ≤ d_FSC_model_pre + **0.05 Å** | `[template]` |

## 5. Calibration checks

Sanity checks against known-good cases; a failure exposes a pipeline bug, not a model defect.

| Check | Expectation | Provenance |
|---|---|---|
| Identity superposition | `1UBQ` onto itself → CA RMSD **0.00 Å**, full-length alignment | `[calibration]` |
| Clean geometry baseline | `3NIR` (0.48 Å) → clashscore ≤ **2**, Ramachandran outliers = **0** | `[calibration]` |
| Resolution calibration | reference-model d_FSC_model within **0.10 Å** of the EMDB-header resolution | `[calibration]` |
| Merged-only data honesty | CC½, ⟨I/σ⟩-outer, R-merge/R-meas reported **unavailable** (not fabricated) when unmerged intensities are absent; `T13_aimless_status` records the abort | `[oracle_tools]` `[catalog]` |

---

## Adding a threshold

1. Add the row here first, with a `[provenance]` tag and — for `[literature]` — a full citation.
2. Cite this file from the driving example that uses it; do not restate the number there.
3. A threshold with no admissible provenance is not admissible (see `CODING_STANDARDS.md` rule 10).
