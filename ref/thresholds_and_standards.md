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
| CC½ resolution-cutoff floor | high-resolution shell is usable down to **CC½ ≈ 0.1–0.2** (significance is sample-size-dependent: CC > 0.3 significant at n > 100, CC > 0.08 at n > 1000 — prefer a per-shell significance test or paired refinement over a fixed floor) | CC½/CC\* definition: Karplus & Diederichs. *Science* 2012; 336(6084):1030–1033. Cutoff value: **Diederichs & Karplus. *Acta Cryst.* D 2013; 69(7):1215–1222** ("Better models by discarding data?"). `[literature]` |
| L-test twinning | untwinned ⟨\|L\|⟩ ≈ **0.5**; perfect twin ≈ **0.375** | Padilla JE, Yeates TO. *Acta Cryst.* D 2003; 59:1124–1130. `[literature]` |
| CAPRI class from DockQ | High **≥ 0.80**; Medium **[0.49, 0.80)**; Acceptable **[0.23, 0.49)**; Incorrect **< 0.23** | Basu S, Wallner B. *PLOS ONE* 2016; 11(8):e0161879. `[literature]` |
| pLDDT confidence cutoff | per-residue **pLDDT ≥ 70** = confident (trim below); ≥ 90 = very high | Jumper J et al. *Nature* 2021; 596:583–589. `[literature]` |
| Phaser MR solution | translation-function **TFZ > 8** = confident/definitely-solved; 5–8 ambiguous | McCoy AJ et al. *J. Appl. Cryst.* 2007; 40:658–674. `[literature]` |
| Real-space density fit (ligand/loop) | **Accuracy: RSZD** significant at **±3σ** (misplaced atoms / unexplained density); **precision: RSZO** floor **~1σ**. RSCC/RSR have *no B-factor-independent significance criterion* (radius convention alone shifts them "wildly"), so use RSCC only as a corroboration signal with a **matched limiting-radius convention**, not as a fixed ≥0.8 bar or a fixed ±0.05 agreement tolerance | RSZD/RSZO via EDSTATS / PDB-REDO `density-fitness`; RSCC only matched-radius | Tickle IJ. *Acta Cryst.* D 2012; 68(4):454–467. `[literature]` |
| Cryo-EM map resolution (FSC) | gold-standard FSC threshold **0.143** (half-maps); model-map FSC **0.5** | Rosenthal PB, Henderson R. *J. Mol. Biol.* 2003; 333(4):721–745. `[literature]` |

## 3. Cross-tool agreement tolerances

How close the agent's tool and the independent oracle must land on the **same** input. These grade
agreement, not quality.

| Metric | Tolerance | Tools | Provenance |
|---|---|---|---|
| CA RMSD | \|Δ\| ≤ **0.10 Å** **on the same residue selection** (RMSD is over aligned Cα pairs only; different aligners align different subsets, so match the selection first) | PHENIX `superpose_models` vs TM-align / ChimeraX / `gemmi align` | `[catalog]` `[template]` |
| Aligned-residue count | ± **2 residues** **only within one aligner class** (both structure-based, or both sequence-based); **not comparable across classes** — TM-align/US-align drop distant Cα pairs by design while LSQ aligners keep the full alignment | same class only | `[template]` |
| Clashscore | ± **1.0** | PHENIX vs MolProbity standalone | `[template]` |
| Ramachandran / rotamer favored % | ± **1.0 pp** | same | `[template]` |
| Ramachandran / rotamer outlier % | ± **0.5 pp** | same | `[template]` |
| Bond-length RMSD | ± **0.003 Å** | PHENIX vs `gemmi validate` | `[template]` |
| Bond-angle RMSD | **matched restraint library required**; ± **0.1°** when both tools use the same library, ± **0.4°** when they differ | PHENIX (CDL default since ~2016) vs `gemmi validate` (CCP4 monomer library / Engh & Huber) | `[template]` `[literature]` |
| Wilson B | ± **5 Å²** (loosened from ±2: `xtriage` uses an ML anisotropy-aware estimate less sensitive to resolution truncation, `ctruncate`/`truncate` a classic straight-line Wilson plot; ML-vs-classic can differ by several Å², more at low resolution / under anisotropy — prefer like-method comparison) | `xtriage` (ML) vs `ctruncate` (classic) | `[template]` |
| L-test ⟨\|L\|⟩ | ± **0.02**, same twin/no-twin call, **matched resolution range** (the auto-selected range differs between programs) | `xtriage` vs `ctruncate` | `[template]` |
| Completeness (overall) | ± **1 pp** vs deposition Table 1 | `xtriage` vs deposition | `[calibration]` |
| Secondary-structure agreement | agent-vs-DSSP three-state ≥ **0.85** over DSSP-assigned residues; two independent assigners floor ≥ **0.80** on a well-ordered model | agent vs DSSP; DSSP vs biotite P-SEA (`t15_ss_agreement.py`) | `[template]` |
| DockQ score | \|Δ\| ≤ **0.05** and identical CAPRI class, **after fixing/verifying the chain mapping** (DockQ is deterministic given a mapping; chain-mapping ambiguity in multimers is the only real variance) | agent vs `t16_interface_quality.py` (DockQ) | `[template]` |
| Interface buried surface area | \|Δ\| ≤ **10 %** (provisional — magnitude unbenchmarked; corroboration-only until a matched-configuration same-probe-radius / same-atom-selection comparison exists) | agent vs biotite SASA (`t16_interface_quality.py`); PISA when available | `[template]` |
| NMR ensemble precision (mean Cα RMSF) | \|Δ\| ≤ **0.05 Å only on a matched ordered-core selection** (OLDERADO / PSVS FindCore); precision is dominated by the superposition selection, so a whole-chain mean must be reported *alongside* an ordered-core figure, not instead of it | agent vs `t17_nmr_ensemble.py` | `[template]` |
| R-free vs deposited | \|Δ\| ≤ **0.02** (REFMAC re-refinement vs deposited/PHENIX) | REFMAC5 vs PHENIX vs deposited | `[catalog]` |
| Independent-code-path R offset | an independent R re-derivation may differ **by a small amount** from scaling / resolution-binning differences (magnitude **unbenchmarked**; gemmi uses the same flat-mask bulk-solvent + anisotropic scaling as PHENIX, so it is *not* categorically "simpler") | `gemmi sfcalc` vs `phenix.model_vs_data` | `[template]` |
| H-placement agreement | H-atom count within **± 2 %**; same Asn/Gln/His flip set; clashscore delta within **± 1.0** | standalone `reduce` vs `phenix.reduce` | `[template]` |

> **Method-dependence preconditions (from the domain-expert review — see
> `ref/research/template_tolerance_review.md`).** Two agreement tolerances only hold under a matched
> tool configuration, and comparing without matching will fail for reasons unrelated to a real
> disagreement:
> - **Bond-angle RMSD** depends on the restraint library: PHENIX (CDL) vs gemmi (Engh & Huber / CCP4
>   monomer library) differ by 0.3–0.4° for library reasons alone. Match the restraint library, or use
>   the widened ±0.4° band. **Record the restraint-library and tool versions** with any geometry
>   measurement.
> - **Clashscore** requires a matched hydrogen-build convention (electron-cloud-center for X-ray vs
>   nuclear for neutron/NMR); a mismatch systematically shifts the score by ~0.5.
>
> **All `[template]` tolerances have now been reviewed** (`ref/research/template_tolerance_review.md`).
> Confirmed defects were fixed: bond-angle (library-conditional), CC½ (citation + 0.1–0.2 floor),
> RSCC (RSZD/RSZO, matched-radius only), aligned-residue count (class-conditional), NMR RMSF
> (matched ordered-core), and the R offset (rationale corrected). Preconditions were added to CA RMSD
> (same selection) and DockQ (fixed chain mapping); Wilson B was loosened to ±5 Å²; L-test, SS
> agreement, bond-length, clashscore, and the Ramachandran/rotamer pp tolerances were kept.
> Interface BSA ±10 % remains the one **provisional** value (mechanism real, magnitude unbenchmarked).

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
