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
#
#    The provider is globbed, not hardcoded. This loop used to name `coscientists`
#    while the comment above promised `data/<provider>/<system>/`, so records under any
#    other provider would never have been schema-checked -- silently, because
#    `nullglob` makes a glob that matches nothing contribute no iterations rather than
#    an error. The count is asserted below for the same reason: zero files validated
#    used to be indistinguishable from all files valid (#123).
shopt -s nullglob globstar
# The generic provider globs also match data/examples/{eval,qds}/, so the list is
# deduplicated before validating rather than schema-checking those files twice.
record_globs=( "${REPO_ROOT}"/data/examples/eval/*.yaml
               "${REPO_ROOT}"/data/examples/qds/*.yaml
               "${REPO_ROOT}"/data/examples/catalog/*.yaml
               "${REPO_ROOT}"/data/*/**/EVAL_*.yaml
               "${REPO_ROOT}"/data/*/**/QDS_*.yaml )
# Deduplicated in-loop rather than by piping through `sort -u`: a crash in the
# producer of a `< <(...)` process substitution is invisible to `set -e`, which is the
# trap this script already documents at the catalog-id enumeration below.
n_records=0
seen_records=""
for f in "${record_globs[@]+"${record_globs[@]}"}"; do
  case " ${seen_records} " in *" ${f} "*) continue ;; esac
  seen_records="${seen_records} ${f}"
  validate_one "${f}"
  n_records=$((n_records + 1))
done

if [[ "${n_records}" -eq 0 ]]; then
  fail "no records matched under data/ — the record globs found nothing, which is a
        gate failure, not a pass. Check data/ has not been moved or renamed."
fi

if [[ "${QUIET}" == "0" ]]; then
  echo "all ${n_records} records valid"
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

# 4g. The guards' own tests. check_registry_figures.py and
#     check_referential_integrity.py exist to catch other scripts' mistakes, and both
#     shipped with a hole (#116, #118) — one comparing four counts it derived itself
#     and never reading the registry, the other promising a structure_ref check in its
#     docstring that was never written. A guard needs a guard.
if ! python3 "${REPO_ROOT}/scripts/test_guards.py"; then
  fail "guard unit tests"
fi

# 4h. Record-tool parsing tests (ctruncate twin operators, TSV unit conversion).
if ! python3 "${REPO_ROOT}/scripts/test_record_tools.py"; then
  fail "record tool unit tests"
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
#
# This checks REPRESENTATION, not completeness -- a round that yielded four lessons
# and recorded one still passes. There is no ground truth for how many lessons a round
# should have produced, so representation is the strongest mechanisable check; do not
# read a pass as "no lesson was lost".
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

# De-duplicated: a round can have several files (round 26 has both its trail and its
# pre-registration), and without this the failure message names it once per file.
rounds = sorted(
    {re.search(r"round(\d+)", p.name).group(1)
     for p in (repo / "ref/research").glob("tolerance_benchmark_round*.md")},
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

# ...and in NEXT_TASKS.md, which is a different file and was not covered.
#
# The gate above was added by #68, whose title was "Reconcile NEXT_TASKS after round 16
# -- and gate the gap that keeps recurring". It reconciled NEXT_TASKS BY HAND and gated
# its NEIGHBOUR. Ten rounds later NEXT_TASKS was two rounds stale again, for the sixth
# reconcile in this repo's history (#58, #64, #68, and two earlier). A guard aimed one
# file to the left of the problem is the round-24/25 lesson: state a gate's scope as
# carefully as its result, and check that it covers the thing it was named for.
#
# REPRESENTATION only, exactly like the lessons check: a round needs a row in the round
# table, not a particular description. There is no ground truth for what a round's
# summary should say, so a pass here does NOT mean the summary is accurate.
if ! missing_tasks="$(python3 -c '
import pathlib, re, sys

repo = pathlib.Path(sys.argv[1])
tasks = (repo / "NEXT_TASKS.md").read_text()

# The round table rows open with "| <n> |". Matched on the leading cell rather than
# anywhere in the line, so a round MENTIONED in prose does not satisfy the check.
covered = set(re.findall(r"^\|\s*(\d+)\s*\|", tasks, re.M))

# De-duplicated: a round can have several files (round 26 has both its trail and its
# pre-registration), and without this the failure message names it once per file.
rounds = sorted(
    {re.search(r"round(\d+)", p.name).group(1)
     for p in (repo / "ref/research").glob("tolerance_benchmark_round*.md")},
    key=int)
print(" ".join(r for r in rounds if r not in covered))
' "${REPO_ROOT}")"; then
  fail "could not check NEXT_TASKS round coverage"
fi
if [[ -n "${missing_tasks// /}" ]]; then
  fail "NEXT_TASKS.md has no round-table row for round(s): ${missing_tasks}"
fi
if [[ "${QUIET}" == "0" ]]; then
  echo "every benchmark round is represented in NEXT_TASKS.md"
fi

# Every bench_*.py must commit the entry set it ran on. The round-17 audit found that
# 7 of the registry's 20 `[benchmark]` rows quote a figure from a set that cannot be
# reconstructed, and the cause was systemic rather than per-row: only four scripts
# hardcoded their entries, the rest took an uncommitted `--ids-file` or globbed a cache,
# and no `ids.json` was committed anywhere in the repo. A `[benchmark]` provenance
# claims the number can be regenerated by re-running -- which is false unless the set
# ships with the script.
#
# This checks a set is DECLARED, not that it is complete: several are knowingly partial
# and say so via SET_IS_COMPLETE = False. A declared-but-incomplete set is the honest
# state and passes; an undeclared one does not.
if ! setless="$(python3 -c '
import ast, pathlib, re, sys

repo = pathlib.Path(sys.argv[1])
missing = []
# SET_RECORD is written with double quotes. The pattern is assembled from chr() calls
# because this whole program sits inside a single-quoted shell string, so it cannot
# contain an apostrophe -- and a character class covering both quote styles would.
SET_RECORD_RE = ("^SET_RECORD" + chr(92) + "s*=" + chr(92) + "s*"
                 + chr(34) + "([^" + chr(34) + "]+)" + chr(34))
for script in sorted((repo / "scripts").glob("bench_*.py")):
    text = script.read_text()
    # DEFAULT_PAIRS covers the superposition benchmark, whose unit is a pair of ids;
    # KNOWN_IDS covers benchmarks whose set is recorded but not runnable as a default.
    declared = re.search(r"^(DEFAULT_SET|DEFAULT_PAIRS|KNOWN_IDS)\s*=", text, re.M)
    if declared:
        # A DECLARED set is not a USED one. bench_refinement_deltas.py declared its
        # set, mentioned it only inside a warning string, and went on globbing the
        # cache -- so the guarantee this gate exists to enforce was false for the one
        # script behind the most expensive partial record in the registry (#78).
        # Require at least one reference outside the assignment and outside a print().
        name = declared.group(1)
        tree = ast.parse(text)
        prints = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "print":
                prints.update(id(n) for n in ast.walk(node))
        used = any(isinstance(n, ast.Name) and n.id == name
                   and isinstance(n.ctx, ast.Load) and id(n) not in prints
                   for n in ast.walk(tree))
        if used:
            continue
        # Two benchmarks record a set they cannot run from: the L-test has no id
        # argument at all (it reads a prior run logs), and the ordered-core script
        # takes file paths. They opt out via SET_NOT_RUNNABLE, which carries the
        # reason in the file rather than as a special case hidden in this gate.
        if re.search(r"^SET_NOT_RUNNABLE\s*=\s*" + chr(34), text, re.M):
            continue
        missing.append(script.name + " (" + name + " declared but never used)")
        continue
    # SET_RECORD names a committed data file holding the set instead -- the EM
    # benchmark keeps its entries in a cumulative TSV, which is stronger than a
    # hardcoded list because it also records what was skipped. The file must exist,
    # or the declaration is a promise rather than a record.
    record = re.search(SET_RECORD_RE, text, re.M)
    if record and (repo / record.group(1)).exists():
        continue
    missing.append(script.name + ("" if not record else " (SET_RECORD file missing)"))
print(" ".join(missing))
' "${REPO_ROOT}")"; then
  fail "could not check benchmark entry sets"
fi
if [[ -n "${setless// /}" ]]; then
  fail "bench script(s) do not commit the entry set they run on: ${setless}"
fi
if [[ "${QUIET}" == "0" ]]; then
  echo "every bench_*.py commits its entry set"
fi

# The external tool paths are written independently in nine files -- PHENIX_BIN in five,
# CCP4_SETUP in four (#140). A PHENIX or CCP4 upgrade updates whichever script the author
# is touching and not the others, which is the class this repo already recorded in #105:
# "Round 21 fixed exactly this ... and did not check the sibling script."
#
# The bad case is the quiet one. If the old install is REMOVED the stale scripts crash,
# which is harmless. If it is left on disk -- installers do not remove the previous
# version -- they keep running against an older build, and benchmark numbers get computed
# with mismatched tool versions with nothing to say so. §4 claims same-binary
# reproducibility against `phenix-2.0-5936` pinned since round 5; that pin is only as
# good as its nine copies agreeing.
#
# Gated rather than refactored: these are standalone scripts run as `python3 scripts/x.py`
# from the repo root, so `scripts/` is not on sys.path and sharing a constant would need
# importlib in nine files -- more machinery than the risk warrants.
if ! divergent="$(python3 -c '
import pathlib, re, sys

repo = pathlib.Path(sys.argv[1])
problems = []
for const in ("PHENIX_BIN", "CCP4_SETUP"):
    seen = {}
    for script in sorted((repo / "scripts").glob("*.py")):
        m = re.search("^" + const + r"\s*=\s*(.+)$", script.read_text(), re.M)
        if m:
            seen.setdefault(m.group(1).strip(), []).append(script.name)
    if len(seen) > 1:
        for value, files in sorted(seen.items()):
            problems.append(const + " = " + value + "  <- " + ", ".join(files))
print(" | ".join(problems))
' "${REPO_ROOT}")"; then
  fail "could not check external tool paths"
fi
if [[ -n "${divergent// /}" ]]; then
  fail "external tool paths disagree between scripts: ${divergent}"
fi
if [[ "${QUIET}" == "0" ]]; then
  echo "external tool paths agree across scripts"
fi

# The registry quotes figures computed from ref/research/data/em_refinement_deltas.tsv,
# and that file grows every round -- so those figures age silently. Three instances were
# caught (#72, #107, #113), all three by accident during reviews of unrelated work.
# Catching a class three times by luck is not a process.
#
# This recomputes each one and fails if the registry's text no longer matches. It also
# fails if the quoted literal has been REWORDED, because a gate that only compares
# numbers is defeated by a rewrite -- which is exactly how a figure escapes notice.
if ! python3 "${REPO_ROOT}/scripts/check_registry_figures.py" > /dev/null 2>&1; then
  python3 "${REPO_ROOT}/scripts/check_registry_figures.py" >&2 || true
  fail "registry figures no longer match ref/research/data/em_refinement_deltas.tsv"
fi
if [[ "${QUIET}" == "0" ]]; then
  echo "registry figures match the per-entry data"
fi

# A round document's claims about its OWN findings age and mis-state the same way the
# registry's did. #130 ("three high" when four were labelled high) and #135 ("a 20-file
# audit round" that was 19) were both caught by review rather than by a check, and both
# were wrong in the direction that flatters the round.
#
# The findings themselves live in a committed TSV rather than being fetched at gate
# time: `gh` is not available or authenticated everywhere, and a check that silently
# skips is a guard that does not guard. Refresh it deliberately with
# `python3 scripts/check_round_figures.py --refresh`.
if ! python3 "${REPO_ROOT}/scripts/check_round_figures.py" > /dev/null 2>&1; then
  python3 "${REPO_ROOT}/scripts/check_round_figures.py" >&2 || true
  fail "a round document's figures no longer match ref/research/data/round_findings.tsv"
fi
if [[ "${QUIET}" == "0" ]]; then
  echo "round-document figures match the findings record"
fi
