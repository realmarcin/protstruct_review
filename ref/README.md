# `ref/` — reference material for the protstruct-review harness

This directory holds offline reference material and the key **task × evaluation** catalog that defines what the harness grades agents on.

## Contents

| File / dir | What it is |
|---|---|
| `phenix_docs/` | Mirrored PHENIX documentation (HTML, offline). Populated by `download_phenix_docs.sh`. |
| `download_phenix_docs.sh` | Re-runnable `wget` mirror script for the PHENIX docs. |
| `tasks_and_evaluations.md` | **Key doc.** 14-row catalog of rote structural-biology tasks, each paired with PHENIX tool(s), independent-oracle tool(s), inputs, evaluation metrics, gold standard, and an example dataset. |
| `tasks_and_evaluations.tsv` | Machine-loadable version of the same table (pipe-separated lists within tab-separated columns). |
| `driving_example.md` | Worked end-to-end example (**compare → refine → RMSD**) that exercises tasks T01 + T04 + T05 + T06 together. Template for future per-task driving examples. |
| `oracle_tools.md` | Install status of independent (non-cctbx) oracle tools the catalog requires (gemmi, TM-align, probe + reduce, Servalcat); per-task oracle assignment. |
| `eval_naming.md` | Filename convention for `EVAL_*` evaluation reports (`EVAL_<structure>_<artifact-short-id>_<YYYY-MM-DD>.{md,tsv}`). |
| `catalog.yaml` | Canonical machine-readable catalog (LinkML-validated). The `tasks_and_evaluations.tsv` above is regenerated from this YAML by `scripts/records_to_tsv.py`. Schema lives at `schemas/protstruct_review.yaml`. |

## Regenerating the PHENIX docs mirror

```bash
bash ref/download_phenix_docs.sh
```

Output lands in `ref/phenix_docs/phenix-online.org/documentation/`. Re-runs are idempotent — `wget --mirror` only re-downloads changed files. Expected footprint: 20–50 MB, ~200–300 HTML pages.

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
