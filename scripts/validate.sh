#!/usr/bin/env bash
# Validate every schema-governed record in the repo against schemas/protstruct_review.yaml.
# Exits non-zero on the first failure.
#
# Usage:
#   bash scripts/validate.sh
#   bash scripts/validate.sh --quiet   # suppress per-file "OK" lines

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCHEMA="${REPO_ROOT}/schemas/protstruct_review.yaml"

QUIET=0
if [[ "${1:-}" == "--quiet" ]]; then
  QUIET=1
fi

fail() {
  echo "FAIL: $1" >&2
  exit 1
}

validate_one() {
  local path="$1"
  if ! out="$(linkml-validate --schema "${SCHEMA}" "${path}" 2>&1)"; then
    echo "${out}"
    fail "${path}"
  fi
  if echo "${out}" | grep -qE '^\[(ERROR|WARN)\]'; then
    echo "${out}"
    fail "${path}"
  fi
  if [[ "${QUIET}" == "0" ]]; then
    echo "OK   ${path#${REPO_ROOT}/}"
  fi
}

# 1. Canonical catalog + tool recommendations + tool assumptions
validate_one "${REPO_ROOT}/ref/catalog.yaml"
validate_one "${REPO_ROOT}/ref/tool_recommendations.yaml"
validate_one "${REPO_ROOT}/ref/tool_assumptions.yaml"

# 1b. Structural-criteria registry against its own schema (separate schema).
if ! out="$(linkml-validate --schema "${REPO_ROOT}/schemas/structural_criteria.yaml" \
                            "${REPO_ROOT}/ref/structural_criteria.yaml" 2>&1)"; then
  echo "${out}"; fail "ref/structural_criteria.yaml"
fi
if echo "${out}" | grep -qE '^\[(ERROR|WARN)\]'; then echo "${out}"; fail "ref/structural_criteria.yaml"; fi
if [[ "${QUIET}" == "0" ]]; then echo "OK   ref/structural_criteria.yaml (structural_criteria schema)"; fi

# 2. Every record under data/ — both synthetic test fixtures
#    (data/examples/) and real per-artefact evals + QDS in
#    data/<provider>/<system>/.
shopt -s nullglob globstar
for f in "${REPO_ROOT}"/data/examples/eval/*.yaml \
         "${REPO_ROOT}"/data/examples/qds/*.yaml \
         "${REPO_ROOT}"/data/examples/catalog/*.yaml \
         "${REPO_ROOT}"/data/coscientists/**/EVAL_*.yaml \
         "${REPO_ROOT}"/data/coscientists/**/QDS_*.yaml; do
  validate_one "${f}"
done

if [[ "${QUIET}" == "0" ]]; then
  echo "all records valid"
fi

# 3. Referential integrity (metric_definition_ref / oracle_tool_ref /
#    catalog_task_ref must resolve in ref/catalog.yaml)
if ! python3 "${REPO_ROOT}/scripts/check_referential_integrity.py"; then
  fail "referential integrity"
fi

# 4. QDS emitter regression tests (geometry-slot completeness, site/ligand/
#    per-residue/pairwise/tool-recs builder coverage, fail-hard negative test)
if ! python3 "${REPO_ROOT}/scripts/test_qds_emit.py"; then
  fail "qds_emit regression"
fi

# 4b. T15 SS-agreement pure-logic unit tests (parsing/collapse/agreement; no
#     mkdssp/biotite needed, so safe to run anywhere).
if ! python3 "${REPO_ROOT}/scripts/test_t15_ss_agreement.py"; then
  fail "t15_ss_agreement unit tests"
fi

# 4c. T16 interface-quality pure-logic unit tests (CAPRI bands / DockQ-JSON
#     extraction; no DockQ binary needed, so safe to run anywhere).
if ! python3 "${REPO_ROOT}/scripts/test_t16_interface_quality.py"; then
  fail "t16_interface_quality unit tests"
fi

# 4d. T17 NMR ensemble-precision pure-logic unit tests (mean-RMSF arithmetic;
#     no biotite/ensemble needed, so safe to run anywhere).
if ! python3 "${REPO_ROOT}/scripts/test_t17_nmr_ensemble.py"; then
  fail "t17_nmr_ensemble unit tests"
fi

# 4e. T17 restraint-summary pure-logic unit tests (wwPDB-report parsing;
#     no network / real report needed, so safe to run anywhere).
if ! python3 "${REPO_ROOT}/scripts/test_t17_restraint_summary.py"; then
  fail "t17_restraint_summary unit tests"
fi

# 4f. Tolerance-benchmark pure-logic unit tests (summary statistics + xtriage /
#     ctruncate log parsing; no network, PISA, PHENIX or CCP4 needed).
if ! python3 "${REPO_ROOT}/scripts/test_bench_tolerances.py"; then
  fail "bench tolerance unit tests"
fi

# 5. Published-view drift. ref/tasks_and_evaluations.{tsv,md} are views of
#    ref/catalog.yaml. Nothing else here compares them, so a task added to the
#    catalog alone used to ship silently (T15-T17 did exactly that).
#    The TSV is generated, so it must match byte-for-byte. The .md is
#    hand-written prose, so only check that every catalog task has a section.
TSV="${REPO_ROOT}/ref/tasks_and_evaluations.tsv"
MD="${REPO_ROOT}/ref/tasks_and_evaluations.md"
TSV_REGEN="$(mktemp)"
trap 'rm -f "${TSV_REGEN}"' EXIT

if ! python3 "${REPO_ROOT}/scripts/records_to_tsv.py" \
       "${REPO_ROOT}/ref/catalog.yaml" --kind catalog -o "${TSV_REGEN}" >/dev/null; then
  fail "tasks_and_evaluations.tsv could not be regenerated"
fi
if ! diff -q "${TSV}" "${TSV_REGEN}" >/dev/null; then
  diff "${TSV}" "${TSV_REGEN}" >&2 || true
  fail "ref/tasks_and_evaluations.tsv is stale — regenerate with: python3 scripts/records_to_tsv.py ref/catalog.yaml --kind catalog -o ref/tasks_and_evaluations.tsv"
fi

# Enumerate task ids into a variable BEFORE the loop. A crash inside a
# `< <(...)` process substitution is NOT caught by `set -e` (it's a subshell),
# so reading the ids inline would let a malformed catalog yield zero ids and
# pass silently — the very drift this section guards against. Capturing first,
# with an explicit status check, makes an enumeration failure loud.
if ! TASK_IDS="$(python3 -c '
import sys, yaml
doc = yaml.safe_load(open(sys.argv[1]))
tasks = doc.get("catalog_tasks", [])
if not tasks:
    sys.exit("no catalog_tasks found in " + sys.argv[1])
for task in tasks:
    print(task["id"])
' "${REPO_ROOT}/ref/catalog.yaml")"; then
  fail "could not enumerate catalog task ids from ref/catalog.yaml"
fi

missing=""
while IFS= read -r task_id; do
  [[ -z "${task_id}" ]] && continue
  grep -q "^### ${task_id} " "${MD}" || missing="${missing} ${task_id}"
done <<< "${TASK_IDS}"
if [[ -n "${missing}" ]]; then
  fail "ref/tasks_and_evaluations.md has no section for:${missing}"
fi

if [[ "${QUIET}" == "0" ]]; then
  echo "published views in sync with ref/catalog.yaml"
fi

# Every benchmark round must leave its lesson in ref/research/lessons.md. Two
# consecutive reconciliations found rounds 14-15 and then round 16 missing from it:
# the lesson gets written into the round's own audit trail, where nothing later reads
# it, and the round closes. That is a process gap, not an oversight, so it is checked
# rather than remembered.
if ! missing_lessons="$(python3 -c '
import pathlib, re, sys

repo = pathlib.Path(sys.argv[1])
lessons = (repo / "ref/research/lessons.md").read_text()

# The index rows end with the round(s) a lesson came from. That column is prose as
# often as not -- "11, back-tested 13" -- so the round is matched as a token in the
# final cell rather than as a whole cell, which would miss every multi-round entry.
covered = set()
for row in re.findall(r"^\|.*\|\s*$", lessons, re.M):
    cells = [c.strip() for c in row.strip("|").split("|")]
    if len(cells) >= 2:
        covered.update(re.findall(r"\d+", cells[-1]))

rounds = sorted(
    (re.search(r"round(\d+)", p.name).group(1)
     for p in (repo / "ref/research").glob("tolerance_benchmark_round*.md")),
    key=int)
print(" ".join(r for r in rounds if r not in covered))
' "${REPO_ROOT}")"; then
  fail "could not check lessons coverage"
fi
if [[ -n "${missing_lessons// /}" ]]; then
  fail "ref/research/lessons.md has no index entry for round(s): ${missing_lessons}"
fi
if [[ "${QUIET}" == "0" ]]; then
  echo "every benchmark round is represented in ref/research/lessons.md"
fi
