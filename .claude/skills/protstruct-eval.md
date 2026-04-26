# Protstruct Eval Skill

Support work on the **protstruct_review** harness — a quality-assessment framework for agentically refined or generated protein structures, built around PHENIX with cross-tool oracles for trust.

## Usage

When the user invokes `/protstruct-eval` or asks about:

- Adding/editing entries in the task × evaluation catalog
- Authoring or extending a per-task driving example (`driving_example_T<NN>.md`)
- Picking the right PHENIX tool + independent oracle pair for a structural-biology operation
- Wiring an evaluation run that respects the cross-tool trust model
- Sanity-checking the PHENIX docs mirror

…follow the conventions documented below. The repo lives at `/Users/marcin/Documents/VIMSS/ontology/protstruct_review/`.

## Trust model (load-bearing — do not violate)

Every task in the catalog is graded by **cross-tool agreement**, not by PHENIX alone. The harness re-runs critical metrics with at least one independent oracle (MolProbity, ChimeraX, REFMAC/Servalcat, TM-align, RELION, gemmi, …) and compares. The deposited PDB/EMDB entry or publication Table 1 is the tiebreaker.

If you are about to add a task whose only oracle is another PHENIX tool, stop — find an external oracle or call out explicitly that none exists.

## Repo layout (the parts that matter for this skill)

```
ref/
├── README.md                       # Index + how to regen the docs mirror
├── download_phenix_docs.sh         # wget --mirror script (idempotent)
├── phenix_docs/                    # Offline PHENIX doc mirror (~250 HTML pages)
├── tasks_and_evaluations.md        # Human-readable task catalog (T01–T14)
├── tasks_and_evaluations.tsv       # Machine-loadable, pipe-separated lists
└── driving_example.md              # Worked end-to-end (T01+T04+T05+T06)
                                    # Template for future driving_example_T<NN>.md
```

## Catalog schema — both files must stay in sync

`ref/tasks_and_evaluations.tsv` columns (tab-separated; lists inside columns are pipe-separated):

| Column | Content |
|---|---|
| `id` | `T01`, `T02`, … (zero-padded, immutable once assigned) |
| `task` | One-line operation name |
| `phenix_tools` | `phenix.<tool>` entry points, pipe-separated |
| `phenix_doc_paths` | Paths under `phenix_docs/phenix-online.org/documentation/` |
| `independent_oracles` | Non-PHENIX tools that compute the same metric |
| `inputs` | Required and optional inputs |
| `metrics` | Numeric deliverables the harness records |
| `gold_standard` | Source of truth (deposition, paper, cross-tool consensus) |
| `example_dataset` | Concrete PDB/EMDB IDs so a run is reproducible |

The Markdown file (`tasks_and_evaluations.md`) is the same rows in prose form. Anything you change in one, change in the other in the same edit. There is no auto-generation script.

**Pass criteria do NOT live in this catalog** — they live in the per-task driving-example files. The catalog is metric-shape, not thresholds.

## Existing tasks (don't reinvent these — extend them)

| ID | Task |
|---|---|
| T01 | Structure superposition + RMSD |
| T02 | Per-residue structural comparison |
| T03 | Reciprocal-space refinement (X-ray) |
| T04 | Real-space refinement (map-based) |
| T05 | Geometry validation |
| T06 | Model-vs-data statistics |
| T07 | Predicted-model processing |
| T08 | Docking predicted/homology model into a map |
| T09 | Molecular replacement |
| T10 | Ligand fitting |
| T11 | Loop / missing-region fitting |
| T12 | Map quality assessment (cryo-EM) |
| T13 | X-ray data quality assessment |
| T14 | Hydrogen placement / protonation |

## Driving-example convention

`ref/driving_example.md` is the template — a worked end-to-end run that exercises **T01 + T04 + T05 + T06** on apoferritin (PDB `7a4m` / EMDB-`11668`). Per-task drivers follow the filename pattern `driving_example_T<NN>.md` and the same internal structure:

1. **Scenario** — what the agent receives and is asked to do
2. **Dataset — concrete IDs** — exact PDB/EMDB/MTZ IDs (no hand-waving)
3. **What the agent must do** — numbered steps with the exact CLI invocations expected
4. **Independent cross-checks** — what the harness re-runs (NOT the agent)
5. **Scoring rubric** — pass/fail bullets with numeric tolerances; all must pass for green

Note the canonical order in the template: **compare baseline → refine → re-compare → validate geometry → model-vs-data**. The pre-refinement baseline is essential — without it ΔRMSD / ΔCC / Δclashscore are uncomputable.

## Adding a new task — exact steps

1. Pick the next free `T<NN>` ID.
2. Identify the PHENIX tool(s). Verify each name exists by `find ref/phenix_docs -name '*<tool>*'` (typo-check) and record the doc path(s) relative to `phenix_docs/phenix-online.org/documentation/`.
3. Find at least one **non-PHENIX** oracle that computes the same metric. If none exists, say so in the row and flag it for follow-up.
4. List concrete inputs (file types + optional flags), metrics (numeric only — no "good fit"), gold-standard source, and a real example dataset (PDB/EMDB ID, not "any structure").
5. Add the row to `tasks_and_evaluations.tsv` (tab-separated; pipe-separate lists within a cell).
6. Add the matching prose section `### T<NN> — <task>` to `tasks_and_evaluations.md` in the same commit.
7. If this task is going to be exercised on its own, draft `ref/driving_example_T<NN>.md` using `driving_example.md` as the template.

## Loading the catalog programmatically

```python
import pandas as pd
df = pd.read_csv("ref/tasks_and_evaluations.tsv", sep="\t")
list_cols = ["phenix_tools", "phenix_doc_paths", "independent_oracles",
             "inputs", "metrics"]
for c in list_cols:
    df[c] = df[c].str.split("|")
```

## Maintaining the PHENIX docs mirror

```bash
bash ref/download_phenix_docs.sh
find ref/phenix_docs -name '*.html' | wc -l   # sanity: should be ≥ 100 (currently 252)
```

The script is idempotent (`wget --mirror` skips unchanged files). Re-run if you suspect doc paths in the catalog are stale.

## PHENIX availability

PHENIX is **not** in conda-forge or Homebrew (verified). It must be installed from <https://phenix-online.org/download/> after academic registration. The catalog and driving examples can be authored, reviewed, and committed without a working PHENIX install — actually executing a run obviously requires one.

If a task needs a tool the agent doesn't have, the agent should declare the gap explicitly rather than fall back to a PHENIX-only oracle.

## Picking an oracle for a new measurement

When the user asks for a metric measurement (e.g. "what's the clashscore?"):

1. **Check `ref/tool_recommendations.yaml`** for the metric's `top_considered` and `top_performing` recommendations. The schema class is `ToolRecommendation` (`schemas/protstruct_review.yaml`).
2. **Run the recommended tool** (verify it's installed via `ref/oracle_tools.md`). If it's missing, run the next-ranked alternative and flag the gap.
3. **Record in the eval** which tool was used (`MeasurementValue.oracle_tool_ref`). It should match the recommendation, or the discrepancy should be noted.
4. **Cross-check against a tool from a different family.** Never let the only oracle for a measurement be a cctbx tool. The trust model in `ref/quality_reporting.md` §3 is the principle, not a courtesy.
5. If a recommendation is wrong (a tool consistently disagrees with consensus, or a new tool outperforms the recommended one), **update `ref/tool_recommendations.yaml`** — bump `as_of_date` and add a new row, don't mutate in place. Re-run `bash scripts/validate.sh` after edits.

## Quality Data Sheet — when to emit and what goes in it

A `QualityDataSheet` (schema class `QualityDataSheet`, emitter `scripts/qds_emit.py`) is the **citable, dated, immutable snapshot** of cross-tool findings for one structure. Emit one when:

- A structure has been evaluated against the catalog and you want a one-page summary downstream consumers can cite.
- A new oracle has been added and you want to publish the now-hardened findings.

The QDS holds these summary blocks (use only the ones the modality needs):

| Block | Class | When to populate |
|---|---|---|
| `identity_block` | `IdentityBlock` | always |
| `geometry_summary` | `GeometrySummary` | always (clashscore, Ramachandran, rotamer, MolProbity score, RMSZ) |
| `data_quality_summary` | `DataQualitySummary` | X-ray only — populated from `stage: all` measurements (completeness, ⟨I/σ⟩ outer, CC½ outer, R-merge/R-meas) |
| `refinement_summary` | `RefinementSummary` | X-ray only (R-work, R-free, gap) |
| `map_summary` | `MapSummary` | cryo-EM only (CC_mask, d_FSC_model) |
| `predicted_confidence_summary` | `PredictedConfidenceSummary` | predicted models only (mean pLDDT + distribution shape, PAE max, multimer-block min) |
| `pairwise_comparisons[]` | `PairwiseComparison` | one per relevant reference (deposited / starting / AlphaFold / truth) — TM-score AND lDDT mandatory pair, RMSD reported additionally |
| `per_residue_quality` | `PerResidueQuality` | populate when local/per-residue measurements exist (per-residue lDDT, displacement, RSRZ; outlier residue list; difference-density peaks; flagged regions) |
| `site_qualities[]` | `SiteQuality` | one per active site / binding site / interface / metal site. Required when a functional site or bound ligand is present |
| `cross_tool_coverage` | `CrossToolCoverage` | always — surfaces which tool families confirmed each task |
| `tool_recommendations_applied[]` | `ToolRecommendation` | snapshot of recommendations active at issue time |
| `headline_verdict` | string | always |

## Metric scope and per-residue summary discipline

Every `MeasurementValue` declares a `scope` (overriding the canonical scope on its `MetricDefinition` if needed). The `MeasurementScope` enum has values: `complex`, `chain`, `site`, `residue`, `atom`, `dataset`, `ligand`.

For non-`complex` scopes, also set `scope_selector` (free text) so the reader can locate what was measured: e.g. `"chain A"`, `"chain A residues 30-45"`, `"Asn A 39"`, `"Ca²⁺ A 33"`, `"active site 1"`.

For per-residue / per-atom / per-chain measurements, the discipline is **store everything, surface the summary**:

- Store the full array under `PerResidueQuality.lddt_per_residue[]` (or `displacement_per_residue_a[]`, `rsrz_per_residue[]`, ...) — one `PerResidueValue` per residue.
- Surface mean / std / min / max / count on the matching scalar MeasurementValue via `TypedMeasurementValue.mean`, `std_dev`, `min_value`, `max_value`, `count`. The `value_numeric` slot conventionally holds the mean.

This way a downstream consumer can read the QDS as a one-page summary AND drill into the per-residue details when needed.

What's load-bearing per modality is documented with citations in `ref/quality_reporting.md`.

Filename: `QDS_<structure>_<artifact-short-id>_<YYYY-MM-DD>.yaml`. Same convention as `EVAL_*` per `ref/eval_naming.md`.

## QDS emitter contract (v3)

`scripts/qds_emit.py` follows two hard rules:

1. **Routing is by canonical metric id, not substring.** A single `METRIC_TO_QDS_SLOT` table at the top of the file maps every metric id to a `(block, slot)` pair. The table is validated against `ref/catalog.yaml` at startup; a typo is a hard error. Adding a new metric → add a new row in the table. Do NOT extend with substring matching.
2. **Fail-hard on implied content.** If the source eval has any of these, the QDS MUST surface the corresponding block or the emitter exits non-zero with a specific error:
   - `scope=site` measurement → `SiteQuality` block required (declare a `Site` on the eval)
   - `scope=ligand` measurement → `LigandQuality` nested in a `SiteQuality` required
   - `scope=residue` measurement OR any `residue_outliers[]` / `density_peaks[]` / `flagged_regions[]` / `per_residue_values[]` on the eval → `PerResidueQuality` block required
   - `pairwise_comparisons[]` on the eval → must surface in QDS

Regression tests at `scripts/test_qds_emit.py` enforce that the 1SAR example has every expected geometry slot populated, the synthetic active-site eval (`data/examples/eval/EVAL_synth_active_site_*.yaml`) populates per_residue_quality / site_qualities / ligand_quality / pairwise_comparisons / tool_recommendations_applied, and the negative test confirms the fail-hard behaviour. `scripts/validate.sh` runs all of this in sequence.

## Common pitfalls

- **Inverting the trust model.** MolProbity is the geometry oracle; it is not a PHENIX tool. `phenix.holton_geometry_validation` and MolProbity are *both* run, and the harness compares them.
- **Naming drift.** It's `phenix.superpose_models`, not `phenix.superpose_pdbs`. Verify in `ref/phenix_docs/phenix-online.org/documentation/reference/` before adding a new row.
- **Adding pass thresholds to the catalog.** Don't. They go in `driving_example_T<NN>.md`.
- **Skipping the baseline.** Pre-refinement metrics are required to compute Δ-anything. The driving example shows this; per-task drivers should follow.
- **Vague example datasets.** "Any high-resolution structure" is not reproducible. Use a PDB/EMDB ID.
- **Reporting RMSD alone for pair comparisons.** TM-score and lDDT are the mandatory pair (`ref/quality_reporting.md` §2.1); RMSD is reported additionally for legibility, never as the basis of the verdict.
- **Quoting R-work alone.** Always with R-free and the gap. The R-free expectation rule of thumb is `≤ resolution_Å / 10` (Brünger 1992; Evans & Murshudov 2013).
- **Mean pLDDT without distribution.** A bimodal-sharp distribution (confident core + disordered tails) is normal; a broad distribution centred on 70 is a different story. Always report distribution shape via the `PlddtDistributionShape` enum.

## Reference materials

- PHENIX docs: `ref/phenix_docs/`
- Task catalog: `ref/catalog.yaml` (canonical, LinkML-validated) + `ref/tasks_and_evaluations.{md,tsv}` (denormalized export)
- Quality reporting consensus: `ref/quality_reporting.md` — what to report and why, with citations
- Tool recommendations: `ref/tool_recommendations.yaml` — `top_considered` vs `top_performing` per metric
- Oracle install status: `ref/oracle_tools.md`
- Schema: `schemas/protstruct_review.yaml`; validate with `bash scripts/validate.sh`
- Eval filename convention: `ref/eval_naming.md`
- Driving example: `ref/driving_example.md`
- Project overview: `ref/README.md`
