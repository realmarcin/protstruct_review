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
| `[benchmark]` | An agreement tolerance **measured in this repo** by running both tools over a test set (audit trail under `ref/research/`, script under `scripts/bench_*.py`). | Change by re-running the benchmark, not by argument. |

`[template]` and `[calibration]` values are engineering tolerances, not scientific claims — tune them
as the harness accumulates evidence. `[schema]`, `[MolProbity]`, and `[literature]` values track
external standards — change them only when the standard does, and update the citation.
`[benchmark]` is the strongest tag available for a cross-tool tolerance: unlike `[template]`, the
magnitude was observed rather than inferred.

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
| CA RMSD | \|Δ\| ≤ **0.03 Å**, and **only when both aligners report the same aligned-residue count** — if the counts differ, even by one, the RMSDs are over different atom sets and must not be compared; report both with their counts. Benchmarked on 20 deposited pairs incl. homologs: on matched selections max \|Δ\| **0.02 Å** (13/20 pairs); on unmatched, up to **0.66 Å**. A single-residue difference (1MBN/1MBO, 153 vs 152) alone moved RMSD by 0.15 Å. Run `phenix.superpose_models` with `morph=False trim=False` — its defaults deform the moving model, and TM-align is rigid-body | PHENIX `superpose_models` vs TM-align (`-ter 0`) | `[benchmark]` (`ref/research/tolerance_benchmark_superposition.md`) |
| Aligned-residue count | ± **2 residues**, **only within one aligner class** (both structure-based, or both sequence-based; TM-align/US-align drop distant Cα pairs by design while LSQ aligners keep the full alignment) **and with matched chain handling** — TM-align stops at the first `TER` and aligns the **first chain only** unless given `-ter 0`, which on 1A2P/1BNI is the difference between ΔN = 185 and ΔN = 31. Confirmed on 20 pairs: 13 exact, 2 off by one, 1 off by two. A larger difference is a real disagreement about the alignment — inspect it, do not widen the band | same class only, matched chain handling | `[benchmark]` (`ref/research/tolerance_benchmark_superposition.md`) |
| Clashscore | \|Δ\| ≤ **1.0**, or **20 % of the mean, whichever is larger**, **with a matched H-build convention**. Benchmarked on 10 models (clashscore 1.2–13.6): matched, median \|Δ\| **0.115**, max 2.27 (17 % on the worst model). **Mismatched** (nuclear vs electron-cloud H), median **9.95**, max **22.97** — 10–23× the tolerance, so that comparison is **void, not failed** | PHENIX/cctbx vs MolProbity standalone (`reduce` + `probe`) | `[benchmark]` (`ref/research/tolerance_benchmark_clashscore_h.md`) |
| Ramachandran / rotamer favored % | ± **1.0 pp** | same | `[template]` |
| Ramachandran / rotamer outlier % | ± **0.5 pp** | same | `[template]` |
| Bond-length RMSD | \|Δ\| ≤ **0.008 Å** across **differing** restraint libraries, and only when both tools restrain the **same number of bonds** (only 6/17 benchmark models did; where counts differ ~2×, Δ reached 0.0667 Å — report both figures, not a Δ). The retired ±0.003 Å was exceeded by the *typical* case: median \|Δ\| 0.0040 Å on matched counts, gemmi higher in **17/17**. Same mechanism as bond angle — PHENIX scores against CDL, gemmi against the CCP4 monomer library. With **matched** libraries the floor is far tighter and is not measured here. Note the recipe: the gemmi validator is **`gemmi rmsz`** (its `rmsD` line, in Å), not `gemmi validate` | PHENIX `model_statistics` vs `gemmi rmsz` | `[benchmark]` (`ref/research/tolerance_benchmark_bond_rmsd.md`) |
| Bond-angle RMSD | **matched restraint library required**; ± **0.1°** when both tools use the same library, ± **0.4°** when they differ | PHENIX (CDL default since ~2016) vs `gemmi validate` (CCP4 monomer library / Engh & Huber) | `[template]` `[literature]` |
| Wilson B | \|Δ\| ≤ **25 %** of the mean **or 2.5 Å², whichever is larger** — and **void when `xtriage` reports ΔB_cart ≥ 25 Å²** (strong anisotropy: the ML and straight-line estimators then diverge without bound and in either direction). Benchmarked on 24 datasets, same MTZ and same intensity columns: median \|Δ\| 13.7 %, p90 27 %. The retired ±**5 Å²** was the wrong *shape* — absolute disagreement scales with B itself (r = 0.81), so a fixed Å² band is vacuous below 1.5 Å (where B ≈ 5 Å²) and violated by 8/24 datasets overall. Treat as **weak corroboration**; for a precise value compare like-method or use the deposition's Table 1 | `xtriage` (ML) vs `ctruncate` (classic) | `[benchmark]` (`ref/research/tolerance_benchmark_wilson_b.md`) |
| L-test ⟨\|L\|⟩ | ± **0.02**, same twin/no-twin call, **matched resolution range** (auto-selected range differs between programs). Note the full scale is only 0.125 (untwinned 0.500 → perfect twin 0.375), so ±0.02 is ~16 % of range; and `xtriage`/`ctruncate` share the Padilla–Yeates *method*, so agreement checks consistent computation, not method-independence | `xtriage` vs `ctruncate` | `[template]` |
| Completeness (overall) | ± **1 pp** vs deposition Table 1 | `xtriage` vs deposition | `[calibration]` |
| Secondary-structure agreement | agent-vs-DSSP three-state ≥ **0.85** over DSSP-assigned residues; two independent assigners floor ≥ **0.80** on a well-ordered model | agent vs DSSP; DSSP vs biotite P-SEA (`t15_ss_agreement.py`) | `[template]` |
| DockQ score | **after fixing/verifying the chain mapping**, \|Δ\| ≤ **0.01** (same-implementation noise floor ≈ 0.004; the old ±0.05 was ~12× too loose). The CAPRI-class match is **waived within ±0.03 of a class boundary** (0.23 / 0.49 / 0.80) to avoid spurious boundary flips. Chain-mapping ambiguity is the presumed (not proven) main variance source in multimers | agent vs `t16_interface_quality.py` (DockQ) | `[template]` |
| Interface buried surface area | \|Δ\| ≤ **3 %** of the mean **or 30 Å², whichever is larger**, with matched 1.4 Å probe, protein-only atom selection, and **PISA's per-side `interface_area` doubled** (biotite reports both sides). Measured on 25 interfaces / 17 entries: median \|Δ\| 1.2 %, p90 2.4 %, max 3.7 %. The disagreement is **one-sided** — biotite reads high in 25/25 — so a *negative* Δ is off-distribution and worth investigating. Relative error is size-driven (median 0.9 % above 1200 Å² total vs 2.3 % below), which is why the absolute floor exists. Chain pairs that are **fragments of one molecule** must be excluded before comparing — they are not interfaces | agent vs biotite SASA (`t16_interface_quality.py`); PISA via the PDBe API | `[benchmark]` (`ref/research/tolerance_benchmark_interface_bsa.md`) |
| NMR ensemble precision (mean Cα RMSF) | \|Δ\| ≤ **0.05 Å only on a matched ordered-core selection** (OLDERADO / PSVS FindCore); precision is dominated by the superposition selection, so a whole-chain mean must be reported *alongside* an ordered-core figure, not instead of it | agent vs `t17_nmr_ensemble.py` | `[template]` |
| R-free vs deposited | \|Δ\| ≤ **0.02** (REFMAC re-refinement vs deposited/PHENIX) | REFMAC5 vs PHENIX vs deposited | `[catalog]` |
| Independent-code-path R offset | \|Δ R\| ≤ **0.02**, with **matched mask radii** (`gemmi sfcalc --radii-set=cctbx`) and the same work set. Benchmarked on 15 entries (1.20–2.92 Å): median **0.0069**, p90 0.0116, max 0.0151, and **one-sided** — gemmi reads high in 15/15, because PHENIX refits k_iso/k_aniso/k_mask **per resolution bin** while gemmi applies one global scale. Using gemmi's default `vdw` mask instead adds a further median +0.0043 (max +0.014), as much again as the offset itself. gemmi is *not* categorically "simpler" — same flat-mask bulk-solvent and anisotropic scaling model | `gemmi sfcalc` vs `phenix.model_vs_data` | `[benchmark]` (`ref/research/tolerance_benchmark_r_offset.md`) |
| H-placement agreement | H-atom count within **± 0.1 %** (benchmarked max **0.013 %** — the retired ±2 % was ~150× too loose); same Asn/Gln/His flip set; clashscore delta within the clashscore tolerance above. **H-count agreement does not imply H-position agreement**: the count is nearly insensitive to the electron-cloud/nuclear convention that dominates the clashscore, so it must not be reported as evidence that two H builds match | standalone `reduce` vs `phenix.reduce` | `[benchmark]` (`ref/research/tolerance_benchmark_clashscore_h.md`) |

> **Method-dependence preconditions (from the domain-expert review — see
> `ref/research/template_tolerance_review.md`).** Two agreement tolerances only hold under a matched
> tool configuration, and comparing without matching will fail for reasons unrelated to a real
> disagreement:
> - **Bond-angle RMSD** depends on the restraint library: PHENIX (CDL) vs gemmi (Engh & Huber / CCP4
>   monomer library) differ by 0.3–0.4° for library reasons alone. Match the restraint library, or use
>   the widened ±0.4° band. **Record the restraint-library and tool versions** with any geometry
>   measurement.
> - **Clashscore** requires a matched hydrogen-build convention (electron-cloud-center for X-ray vs
>   nuclear for neutron/NMR); a mismatch shifts the score (≈ 0.5 on the repo's 1SAR: 3.13 cctbx vs 3.63 standalone — an in-repo observation, not a general benchmark).
>
> **All `[template]` tolerances have now been reviewed** (`ref/research/template_tolerance_review.md`).
> Confirmed defects were fixed: bond-angle (library-conditional), CC½ (citation + 0.1–0.2 floor),
> RSCC (RSZD/RSZO, matched-radius only), aligned-residue count (class-conditional), NMR RMSF
> (matched ordered-core), and the R offset (rationale corrected). Preconditions were added to CA RMSD
> (same selection) and DockQ (fixed chain mapping); Wilson B was loosened to ±5 Å²; L-test, SS
> agreement, bond-length, clashscore, and the Ramachandran/rotamer pp tolerances were kept.
> An independent verified research pass cross-checked all seven of the second batch and confirmed
> these verdicts, additionally tightening **DockQ** to ±0.01 (same-implementation noise floor ≈ 0.004).
>
> **No tolerance is provisional any more.** The two that were — interface BSA and Wilson B — could
> only be settled by running the tools, and now have been (`scripts/bench_t16_bsa_vs_pisa.py`,
> `scripts/bench_t13_wilson_b.py`; audit trails under `ref/research/`). Both changed *shape*, not just
> magnitude: each is now a relative band with an absolute floor, because in both cases the
> disagreement scales with the quantity being measured. **Interface BSA ±10 % → max(3 %, 30 Å²)**
> (~3× tighter on real interfaces; the disagreement is one-sided, biotite high in 25/25).
> **Wilson B ±5 Å² → max(25 %, 2.5 Å²), void under strong anisotropy** — the old band was vacuous
> below 1.5 Å resolution and violated by 8/24 datasets overall.

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
