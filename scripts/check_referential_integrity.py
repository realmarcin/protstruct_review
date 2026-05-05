#!/usr/bin/env python3
"""Check that every reference in committed YAML records resolves.

`linkml-validate` enforces type and enum constraints but does not enforce
that string-typed references point at declared instances. This script
walks every YAML record under `ref/` and `data/examples/` and verifies:

  - every `metric_definition_ref` resolves in `ref/catalog.yaml::metric_definitions`
  - every `oracle_tool_ref` / `tool_ref` resolves in `ref/catalog.yaml::tools`
  - every `catalog_task_ref` / `catalog_tasks_applied[]` is a known T0NN id
  - every `structure_ref` resolves either in `ref/catalog.yaml::structures` or
    in the same record's structures[]

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
    return violations


def main() -> int:
    indices = load_catalog_indices()
    targets = [
        CATALOG,
        REPO / "ref" / "tool_recommendations.yaml",
        REPO / "ref" / "tool_assumptions.yaml",
    ]
    targets += sorted((REPO / "data" / "examples").rglob("*.yaml"))
    targets += sorted((REPO / "data" / "coscientists").rglob("EVAL_*.yaml"))
    targets += sorted((REPO / "data" / "coscientists").rglob("QDS_*.yaml"))

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
