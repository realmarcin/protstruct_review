# protstruct_review

Quality-assessment harness for agent-refined or generated protein structures.

## Read first

These sources have decreasing precedence:

1. `CODING_STANDARDS.md` — enforceable repository invariants.
2. `.claude/skills/protstruct-eval/SKILL.md` — domain workflow, tool assumptions, and rationale.
3. `NEXT_TASKS.md` — current work only; verify it against GitHub before relying on it.

When the first two disagree, treat the drift as a defect and reconcile it in the same change.

## Environment

Python 3.11–3.12 is supported; `.python-version` selects 3.12. Bootstrap the locked development
environment from a clean checkout with:

```bash
uv sync --locked
```

Use `uv sync --locked --extra benchmark` for the open-source Python benchmark tools. PHENIX 2.0-5936
and CCP4 9.0.015 are separate licensed installations; their configuration and oracle-specific tools
are documented in `ref/oracle_tools.md`. Configure them through the `PROTSTRUCT_*` variables routed
by `scripts/toolchain.py`; do not add per-runner path constants.

## Sources of truth

- `ref/catalog.yaml` → generated `ref/tasks_and_evaluations.tsv`
- `schemas/protstruct_review.yaml` → generated `protstruct_review/models.py`
- Do not hand-edit either generated file. The hermetic gate checks both byte-for-byte.

## Validation

- Focused/fast: run the relevant `uv run --locked -- python scripts/test_<area>.py` scripts while
  iterating.
- Required hermetic gate: `uv run --locked -- bash scripts/validate.sh`
- The core gate uses no network and invokes no PHENIX/CCP4 tools.
- External PHENIX/CCP4 benchmarks and online data fetches are opt-in; read each benchmark module's
  requirements before running it.

## Trust model

Never grade PHENIX solely with PHENIX/cctbx. Re-measure quantitative claims with an independent
oracle; use deposition or publication evidence as the tiebreaker when available.

## Repository map

- `ref/` — catalog, drivers, thresholds, oracle guidance, and research records
- `schemas/` — canonical LinkML schemas
- `protstruct_review/` — generated Pydantic models
- `scripts/` — validation, emitters, focused tests, and opt-in benchmarks
- `data/` — examples and committed evaluation/QDS records
- `prompts/` — repository workflows

## Workflow

Use `prompts/backlog-loop-goal.md` for the full survey→branch→PR→review cycle. Branch before editing,
run the hermetic gate before proposing a merge, and never merge without explicit user approval in
the current conversation.
