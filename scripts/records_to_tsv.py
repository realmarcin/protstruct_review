#!/usr/bin/env python3
"""Schema-compliant YAML records → TSV (the reverse of tsv_to_records.py).

v0 supports the catalog kind only — that's the round-trip we sanity-check
against the existing `ref/tasks_and_evaluations.tsv`. Eval metrics/headline
TSV emission can be added when needed; the QDS is YAML-native and not a TSV.

Usage:
    python scripts/records_to_tsv.py ref/catalog.yaml --kind catalog -o /tmp/catalog_export.tsv
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Any

import yaml


def join_pipe(items: list[str] | None) -> str:
    return "|".join(items or [])


def emit_catalog(doc: dict[str, Any], out) -> None:
    cols = [
        "id",
        "task",
        "phenix_tools",
        "phenix_doc_paths",
        "independent_oracles",
        "inputs",
        "metrics",
        "gold_standard",
        "example_dataset",
    ]
    w = csv.writer(out, delimiter="\t", lineterminator="\n")
    w.writerow(cols)
    metric_def_by_id = {m["id"]: m for m in doc.get("metric_definitions", [])}
    for rec in doc.get("catalog_tasks", []):
        # Metric ids back to labels using the canonical metric_definitions block.
        metric_labels: list[str] = []
        for ref in rec.get("metric_definition_refs", []):
            md = metric_def_by_id.get(ref)
            metric_labels.append(md["name"] if md else ref)
        w.writerow([
            rec["id"],
            rec.get("task_name", ""),
            join_pipe(rec.get("phenix_tool_refs")),
            join_pipe(rec.get("phenix_doc_paths")),
            join_pipe(rec.get("oracle_tool_refs")),
            rec.get("inputs_description", ""),
            join_pipe(metric_labels),
            rec.get("gold_standard", ""),
            rec.get("example_dataset", ""),
        ])


def main() -> None:
    p = argparse.ArgumentParser(description="Records → TSV emitter (catalog only at v0).")
    p.add_argument("yaml_path", type=Path)
    p.add_argument("--kind", choices=["catalog"], default="catalog")
    p.add_argument("-o", "--output", type=Path)
    args = p.parse_args()

    doc = yaml.safe_load(args.yaml_path.read_text())
    out_stream = args.output.open("w") if args.output else sys.stdout
    try:
        if args.kind == "catalog":
            emit_catalog(doc, out_stream)
        else:
            raise SystemExit(f"Unsupported kind: {args.kind}")
    finally:
        if args.output:
            out_stream.close()
            sys.stderr.write(f"wrote {args.output}\n")


if __name__ == "__main__":
    main()
