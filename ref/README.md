# `ref/` — reference material for the protstruct-review harness

This directory holds offline reference material and the key **task × evaluation** catalog that defines what the harness grades agents on.

## Contents

| File / dir | What it is |
|---|---|
| `phenix_docs/` | Mirrored PHENIX documentation (HTML, offline). Populated by `download_phenix_docs.sh`. |
| `download_phenix_docs.sh` | Re-runnable `wget` mirror script for the PHENIX docs. |
| `tasks_and_evaluations.md` | **Key doc.** 17-row catalog of rote structural-biology tasks, each paired with PHENIX tool(s), independent-oracle tool(s), inputs, evaluation metrics, gold standard, and an example dataset. Hand-written prose; `scripts/validate.sh` checks that every catalog task has a section here. |
| `tasks_and_evaluations.tsv` | Machine-loadable version of the same table (pipe-separated lists within tab-separated columns). **Generated** from `catalog.yaml`; `scripts/validate.sh` fails if it drifts. |
| `driving_example.md` | Worked end-to-end example (**compare → refine → RMSD**) that exercises tasks T01 + T04 + T05 + T06 together. Template for the per-task driving examples. |
| `driving_example_T<NN>.md` | Per-task drivers for T01 (superposition+RMSD), T05 (geometry), T13 (X-ray data quality), T15 (classification), T16 (interface quality), T17 (NMR ensemble). Each grades cross-tool agreement and tags every threshold with its provenance; T15/T16/T17 correspond to the runnable `scripts/t1{5,6,7}_*.py` wrappers. Remaining tasks tracked in issue #2. |
| `thresholds_and_standards.md` | **Single source of truth** for every numeric threshold the harness scores against — outlier definitions, literature values, cross-tool agreement tolerances, calibration checks — each with a `[provenance]` tag. The driving examples cite it rather than restating values. |
| `oracle_tools.md` | Install status of independent (non-cctbx) oracle tools the catalog requires (gemmi, TM-align, probe + reduce, Servalcat); per-task oracle assignment. |
| `eval_naming.md` | Filename convention for `EVAL_*` evaluation reports (`EVAL_<structure>_<artifact-short-id>_<YYYY-MM-DD>.{md,tsv}`). |
| `catalog.yaml` | Canonical machine-readable catalog (LinkML-validated). The `tasks_and_evaluations.tsv` above is regenerated from this YAML by `scripts/records_to_tsv.py`. Schema lives at `schemas/protstruct_review.yaml`. |
| `tool_recommendations.yaml` | Canonical per-metric oracle recommendations (LinkML-validated, schema-class `ToolRecommendation`). Consumed by `scripts/qds_emit.py` to build the QDS tool-recommendations block. |
| `tool_assumptions.yaml` | Per-tool implicit/explicit assumptions (LinkML-validated). Feeds the QDS assumptions report. |
| `protein_structure_quality_refinement_indicators.md` | Survey of quality/refinement indicators behind the T15–T17 tasks and the newer QDS summary blocks (classification, interface, prediction-ensemble, NMR). |
| `quality_reporting.md` | Synthesis of community consensus on the smallest defensible quality report (single-structure, X-ray / cryo-EM / predicted) and pair-of-structures (TM-score, lDDT, GDT-TS, RMSD, Δ model-vs-data). Evidence base for the QualityDataSheet schema. ~18 citations. |

## Regenerating the PHENIX docs mirror

```bash
bash ref/download_phenix_docs.sh
```

Output lands in `ref/phenix_docs/phenix-online.org/documentation/`. Re-runs are idempotent — `wget --mirror` only re-downloads changed files. Expected footprint: ~50 MB, 550+ files (of which ~250 are HTML reference pages; the rest are images, CSS, and index assets).

Sanity check after a run:

```bash
find ref/phenix_docs -name '*.html' | wc -l   # should be >= 100
```

## Loading the task catalog programmatically

```python
import pandas as pd
df = pd.read_csv("ref/tasks_and_evaluations.tsv", sep="\t")
# List-valued columns are pipe-separated
df["phenix_tools"] = df["phenix_tools"].str.split("|")
df["independent_oracles"] = df["independent_oracles"].str.split("|")
```

## Philosophy

The harness evaluates agents that **refine or generate protein structures**. The trust model is deliberate: we do **not** grade PHENIX output with PHENIX alone. Every task row in the catalog lists at least one **independent oracle** (MolProbity, ChimeraX, REFMAC, Servalcat, TM-align, RELION, …) whose output the harness cross-checks against PHENIX's. Cross-tool agreement is the primary pass signal; the gold-standard source (deposited PDB/EMDB entry, publication Table 1, held-out reference loop) is the tiebreaker.

The driving example (`driving_example.md`) shows how a single evaluation run threads this together: the agent performs the task with PHENIX, and the harness re-runs critical metrics with the independent oracle(s) before scoring.
