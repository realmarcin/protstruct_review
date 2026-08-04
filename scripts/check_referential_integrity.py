#!/usr/bin/env python3
"""Check that every reference in committed YAML records resolves.

`linkml-validate` enforces type and enum constraints but does not enforce
that string-typed references point at declared instances. This script
walks every YAML record under `ref/` and `data/examples/` and verifies:

  - every `metric_definition_ref` resolves in `ref/catalog.yaml::metric_definitions`
  - every `oracle_tool_ref` / `tool_ref` resolves in `ref/catalog.yaml::tools`
  - every `catalog_task_ref` / `catalog_tasks_applied[]` is a known T0NN id
  - every `structure_ref` resolves in `ref/catalog.yaml::structures` or the same
    record's structures[] WHEN either exists; neither does today, so it falls back
    to requiring every nested `structure_ref` to match its own record's. See
    `check_structure_refs` — this bullet described a check that was never
    implemented until #118.

Exits non-zero with a per-violation report on the first miss. Wired into
`scripts/validate.sh` so `linkml-validate` and the integrity check both
run before any commit.

Closes Codex finding #3 (medium): "Metric references are not enforced,
and the committed example already drifts from the canonical catalog."
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Iterable

import yaml


REPO = Path(__file__).resolve().parent.parent
CATALOG = REPO / "ref" / "catalog.yaml"

KNOWN_TASK_IDS = {f"T{n:02d}" for n in range(1, 18)}


def load_catalog_indices() -> dict[str, set[str]]:
    """Return {kind: set_of_known_ids} indices from the canonical catalog."""
    doc = yaml.safe_load(CATALOG.read_text())
    return {
        "metric": {m["id"] for m in doc.get("metric_definitions", [])},
        "tool": {t["id"] for t in doc.get("tools", [])},
        "task": KNOWN_TASK_IDS,
        # Empty today -- ref/catalog.yaml declares no `structures:` collection. The
        # index is built anyway so `check_structure_refs` starts resolving against it
        # the moment one is added, rather than needing to be remembered then.
        "structure": {s["id"] for s in doc.get("structures", []) or []},
    }


def walk(node: Any, path: str = "$") -> Iterable[tuple[str, str, Any]]:
    """Yield (json-pointer-style path, key, value) tuples for every leaf."""
    if isinstance(node, dict):
        for k, v in node.items():
            yield from walk(v, f"{path}.{k}")
            if not isinstance(v, (dict, list)):
                yield path, k, v
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from walk(v, f"{path}[{i}]")


def check_record(yaml_path: Path, indices: dict[str, set[str]]) -> list[str]:
    """Return a list of human-readable violation messages for one record."""
    doc = yaml.safe_load(yaml_path.read_text())
    if doc is None:
        return []
    violations: list[str] = []
    rel = yaml_path.relative_to(REPO)

    # Local indices for refs that may resolve within the same document.
    local_metric_ids = {m["id"] for m in doc.get("metric_definitions", []) or []}
    local_tool_ids = {t["id"] for t in doc.get("tools", []) or []}
    local_structure_ids = {s["id"] for s in doc.get("structures", []) or []}

    metric_ok = indices["metric"] | local_metric_ids
    tool_ok = indices["tool"] | local_tool_ids
    task_ok = indices["task"]

    # The schema declares `agent_claim`, `oracle_measure`, `delta` as
    # TypedMeasurementValue (not refs), so checking by-key is naive but
    # safe — the keys we look for are unambiguous in this schema.
    REF_KEYS = {
        "metric_definition_ref": ("metric", metric_ok),
        "oracle_tool_ref": ("tool", tool_ok),
        "tool_ref": ("tool", tool_ok),
        "catalog_task_ref": ("task", task_ok),
    }
    LIST_REF_KEYS = {
        "catalog_tasks_applied": ("task", task_ok),
        "catalog_task_refs": ("task", task_ok),
        "phenix_tool_refs": ("tool", tool_ok),
        "oracle_tool_refs": ("tool", tool_ok),
        "metric_definition_refs": ("metric", metric_ok),
    }

    def check(node: Any, path: str = "$") -> None:
        if isinstance(node, dict):
            for k, v in node.items():
                if k in REF_KEYS and isinstance(v, str):
                    kind, allowed = REF_KEYS[k]
                    if v not in allowed:
                        violations.append(f"{rel}: {path}.{k} = {v!r} not in known {kind} ids")
                if k in LIST_REF_KEYS and isinstance(v, list):
                    kind, allowed = LIST_REF_KEYS[k]
                    for i, item in enumerate(v):
                        if isinstance(item, str) and item not in allowed:
                            violations.append(
                                f"{rel}: {path}.{k}[{i}] = {item!r} not in known {kind} ids"
                            )
                check(v, f"{path}.{k}")
        elif isinstance(node, list):
            for i, v in enumerate(node):
                check(v, f"{path}[{i}]")

    check(doc)
    violations += check_structure_refs(doc, rel, indices["structure"] | local_structure_ids)
    return violations


# Top-level collections whose members each carry their own `structure_ref`, under which
# every nested `structure_ref` must agree.
RECORD_COLLECTIONS = ("evaluation_runs", "quality_data_sheets", "agent_artifacts")


def check_structure_refs(doc: Any, rel: Path, declared: set[str]) -> list[str]:
    """Check `structure_ref` — the one ref this script's docstring promised and skipped.

    The promise was "resolves either in `ref/catalog.yaml::structures` or in the same
    record's structures[]". Neither collection exists anywhere in the repo: the schema
    declares `structure_ref: {range: Structure}` but nothing instantiates a `Structure`,
    so the check as written had no index to resolve against and was silently never
    implemented (#118) -- while `local_structure_ids` sat computed and unused above.

    So it resolves against those collections WHEN they exist, and otherwise falls back
    to the invariant that does hold today and catches the same typo: within one record
    (one evaluation_run, one QDS), every nested `structure_ref` must equal that record's
    own. An EVAL is about one structure; `ligands[].structure_ref` naming a different
    one is a defect whether or not a `structures:` collection is ever added.
    """
    violations: list[str] = []
    if not isinstance(doc, dict):
        return violations

    def nested_refs(node: Any, path: str) -> Iterable[tuple[str, str]]:
        if isinstance(node, dict):
            for k, v in node.items():
                if k == "structure_ref" and isinstance(v, str):
                    yield f"{path}.{k}", v
                else:
                    yield from nested_refs(v, f"{path}.{k}")
        elif isinstance(node, list):
            for i, v in enumerate(node):
                yield from nested_refs(v, f"{path}[{i}]")

    for collection in RECORD_COLLECTIONS:
        for i, record in enumerate(doc.get(collection) or []):
            if not isinstance(record, dict):
                continue
            base = f"$.{collection}[{i}]"
            own = record.get("structure_ref")
            for path, value in nested_refs(record, base):
                if declared and value not in declared:
                    violations.append(
                        f"{rel}: {path} = {value!r} not in known structure ids")
                elif not declared and own and value != own:
                    violations.append(
                        f"{rel}: {path} = {value!r} does not match the record's own "
                        f"structure_ref {own!r}")
    return violations


def main() -> int:
    indices = load_catalog_indices()
    targets = [
        CATALOG,
        REPO / "ref" / "tool_recommendations.yaml",
        REPO / "ref" / "tool_assumptions.yaml",
    ]
    # Every provider, not just `coscientists`. Naming one provider here was the same
    # defect as #123 in scripts/validate.sh, in its sibling -- records under any other
    # provider resolved no references and said nothing about it.
    targets += sorted((REPO / "data").rglob("*.yaml"))
    targets = sorted({t for t in targets})

    failed = False
    for path in targets:
        if not path.exists():
            continue
        try:
            violations = check_record(path, indices)
        except yaml.YAMLError as e:
            print(f"FAIL: {path.relative_to(REPO)}: YAML parse error: {e}", file=sys.stderr)
            failed = True
            continue
        if violations:
            failed = True
            for v in violations:
                print(f"FAIL: {v}", file=sys.stderr)
        else:
            print(f"OK   {path.relative_to(REPO)}")

    if failed:
        print("\nrefs unresolved — fix the violations above or extend ref/catalog.yaml", file=sys.stderr)
        return 1
    print("all references resolve")
    return 0


if __name__ == "__main__":
    sys.exit(main())
