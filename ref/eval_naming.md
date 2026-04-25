# `EVAL_*` filename convention

Evaluation reports produced by the protstruct_review harness sit next to the artifact they evaluate (typically under `data/<provider>/<system>/`). To keep them sortable, groupable, and traceable to a specific input, all eval files use the same name shape.

## Format

```
EVAL_<structure>_<artifact-short-id>_<YYYY-MM-DD>.md
EVAL_<structure>_<artifact-short-id>_<YYYY-MM-DD>_metrics.tsv
```

| Field | Definition | Example |
|---|---|---|
| `<structure>` | The PDB / EMDB / target identifier the agent was asked to refine or generate. Lowercase, no spaces. | `1sar`, `7a4m`, `af-p00698-f1` |
| `<artifact-short-id>` | First 8 hex characters of the agent run's UUID (or any other stable, short, unique tag for the agent run). Disambiguates multiple agent runs on the same structure. | `cdba2c07` |
| `<YYYY-MM-DD>` | Date the evaluation was *run*, ISO 8601. Sorts chronologically when an artifact is re-evaluated (e.g. after a new oracle is added). | `2026-04-24` |

The `_metrics.tsv` suffix marks the machine-loadable companion to the markdown report. They share the same stem so a single glob (`EVAL_1sar_cdba2c07_2026-04-24*`) returns the pair.

## Example

```
data/coscientists/openscientist/
├── cdba2c07-...-artifacts.zip                    # input artifact (UUID-named by agent)
├── cdba2c07-...-report.pdf                       # input artifact
├── EVAL_1sar_cdba2c07_2026-04-24.md              # human-readable eval report
├── EVAL_1sar_cdba2c07_2026-04-24_metrics.tsv     # machine-loadable metrics
└── gemmi_rfactor.py                              # eval helper script (not date-stamped — reused)
```

## Why this shape

- **Structure first** — within an agent-run directory, all evals of the same target cluster together. `ls EVAL_1sar*` returns every 1SAR eval at a glance.
- **Artifact short-id second** — when the same structure is refined by multiple independent agent runs (different seeds, different prompt variants, different agent versions), each run's eval is unambiguous without reading file contents.
- **Date last** — when an existing eval is **re-run** because a new oracle was installed (e.g. CCP4/REFMAC5 finally available), the new file gets a later date and lives alongside the older one. Don't overwrite — append.

## When to bump the date

Re-run produces a new file (don't overwrite) if:

- A new oracle was added to the catalog and re-running closes a previously-open gap.
- The agent re-ran and produced a new artifact (different `<artifact-short-id>` — separate file pair, no collision).
- A bug in an oracle invocation was fixed.

Re-run **may overwrite the same date** if:

- Just fixing typos or formatting in the same eval.
- Adding a section to a still-fresh report on the same day.

## When the convention doesn't apply

- `EVAL_metrics.tsv` aggregated across many runs (e.g. a leaderboard) → use a separate name like `LEADERBOARD_*.tsv` or put it in a top-level `results/` directory. Don't reuse the `EVAL_` prefix for cross-run summaries.
- Catalog-level documents (`tasks_and_evaluations.md`, `oracle_tools.md`) → `ref/`, no date stamp; they evolve under git history.

## Loading by glob

```python
from pathlib import Path
import pandas as pd

for tsv in Path("data").rglob("EVAL_*_metrics.tsv"):
    df = pd.read_csv(tsv, sep="\t")
    structure, run_id, run_date = tsv.stem.replace("_metrics", "").split("_")[1:]
    df["structure"], df["run_id"], df["run_date"] = structure, run_id, run_date
    # ... aggregate / leaderboard ...
```
