# protstruct_review

Quality-assessment harness for agent-refined or generated protein structures. It records
cross-tool measurements, applies independent-oracle checks, and emits LinkML-validated evaluation
and Quality Data Sheet records.

## Setup

Install [uv](https://docs.astral.sh/uv/), then bootstrap a clean checkout with one command:

```bash
uv sync --locked
```

The checked-in `.python-version` selects Python 3.12 (the supported range is Python 3.11–3.12), and
`uv.lock` fixes the complete development environment used for validation, tests, linting, and
LinkML model generation. To add the open-source Python benchmark tools:

```bash
uv sync --locked --extra benchmark
```

PHENIX and CCP4 are separate licensed installations and are not installed by `uv`; see
[`ref/oracle_tools.md`](ref/oracle_tools.md) for pinned versions and activation rules.

External-tool discovery is centralized in `scripts/toolchain.py`. Its defaults preserve the pinned
macOS toolchain; override them without editing runners:

| Variable | Meaning |
|---|---|
| `PROTSTRUCT_PHENIX_BIN` | directory containing the PHENIX entry points |
| `PROTSTRUCT_CCP4_SETUP` | CCP4 `ccp4.setup-sh` file |
| `PROTSTRUCT_TMALIGN` | TM-align executable |
| `PROTSTRUCT_DSSP` | `mkdssp` executable |
| `PROTSTRUCT_PROBE` | Richardson-lab `probe` executable |
| `PROTSTRUCT_REDUCE` | Richardson-lab `reduce` executable |

Benchmark runners emit the resolved paths and version evidence as their first stderr JSON record.
Only the fixed CCP4 environment adapter sources a vendor shell file; model/data paths and all tool
arguments are passed directly as subprocess argument vectors.

## Validation

The hermetic gate needs no network, PHENIX, or CCP4:

```bash
uv run --locked -- bash scripts/validate.sh
```

External-tool and online benchmarks are opt-in. Each benchmark's module documentation identifies
its required binaries, data downloads, and command line.

## Sources of truth

- `ref/catalog.yaml` generates `ref/tasks_and_evaluations.tsv`; never hand-edit the TSV.
- `schemas/protstruct_review.yaml` generates `protstruct_review/models.py`; never hand-edit the
  generated model.
- `CODING_STANDARDS.md` defines enforceable repository invariants.
- `.claude/skills/protstruct-eval/SKILL.md` explains the scientific workflow and trust rationale.

See [`ref/README.md`](ref/README.md) for the reference-material map and [`schemas/README.md`](schemas/README.md)
for schema authoring and regeneration details.
