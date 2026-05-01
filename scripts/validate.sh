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
