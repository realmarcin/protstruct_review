#!/usr/bin/env python3
"""TSV → schema-compliant YAML records.

Three input shapes are recognised by --kind (or auto-detected from columns):

  catalog   : ref/tasks_and_evaluations.tsv
              Pipe-separated lists in cells (phenix_tools, oracles, metrics, ...).
              Emits a list of CatalogTask records inside a Container.

  metrics   : EVAL_<…>_metrics.tsv (long-format per-row measurements)
              Emits one EvaluationRun with measurements[] inlined.

  headline  : EVAL_<…>_headline.tsv (collapsed top-level findings)
              Emits one EvaluationRun with headline_findings[] inlined.

Either subcommand can be invoked separately. To merge metrics + headline into
one EvaluationRun, run with --kind metrics first to produce a YAML with
measurements[], then re-run with --kind headline --merge-into <yaml> to add
headline_findings[].

Cell parser: numeric strings with optional unit (`%`, `°`, `Å`, `σ`) become
{value_numeric, unit}. `n/a` becomes {is_not_applicable: true}. Anything
else (ranges like "49.97 → 2.50", counts with annotation like "1 (Asn A 39)",
"7217 unique") becomes {value_text}.

Usage:
    python scripts/tsv_to_records.py ref/tasks_and_evaluations.tsv \\
        --kind catalog \\
        -o ref/catalog.yaml

    python scripts/tsv_to_records.py \\
        data/coscientists/openscientist/EVAL_1sar_cdba2c07_2026-04-24_metrics.tsv \\
        --kind metrics \\
        --eval-id EVAL_1sar_cdba2c07_2026-04-24 \\
        --structure-id 1sar \\
        --artifact-id cdba2c07-daff-4f60-ae96-12452b3a5fbb \\
        --run-date 2026-04-24 \\
        -o data/examples/eval/EVAL_1sar_cdba2c07_2026-04-24.yaml

    python scripts/tsv_to_records.py \\
        data/coscientists/openscientist/EVAL_1sar_cdba2c07_2026-04-24_headline.tsv \\
        --kind headline \\
        --merge-into data/examples/eval/EVAL_1sar_cdba2c07_2026-04-24.yaml
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path
from typing import Any

import yaml


_NUMERIC_WITH_UNIT = re.compile(
    r"^\s*(?P<sign>[+-]?)\s*(?P<num>\d+(?:\.\d+)?)\s*(?P<unit>%|°|Å|σ|deg|A)?\s*$"
)


def parse_cell_to_measurement(cell: str) -> dict[str, Any]:
    """Convert a TSV cell to a TypedMeasurementValue dict.

    Returns one of:
      {is_not_applicable: True}
      {value_numeric: float, unit: str?}
      {value_text: str}
    """
    s = (cell or "").strip()
    if s == "" or s.lower() in {"n/a", "na", "none", "-"}:
        return {"is_not_applicable": True}
    m = _NUMERIC_WITH_UNIT.match(s)
    if m:
        sign = m.group("sign") or ""
        num = float(sign + m.group("num"))
        unit = m.group("unit")
        out: dict[str, Any] = {"value_numeric": num}
        if unit:
            out["unit"] = unit
        return out
    return {"value_text": s}


def split_pipe(cell: str) -> list[str]:
    """Split a pipe-separated TSV cell into a clean list."""
    if not cell or not cell.strip():
        return []
    return [s.strip() for s in cell.split("|") if s.strip()]


def slugify(s: str) -> str:
    """Make a slug suitable for an id (lowercase, alnum + underscore)."""
    s = re.sub(r"[^\w\-.]+", "_", s.strip().lower())
    s = re.sub(r"_+", "_", s).strip("_")
    return s or "x"


# ---------------------------------------------------------------- catalog


def load_catalog(tsv_path: Path) -> list[dict[str, Any]]:
    """Parse the catalog TSV into a list of CatalogTask record dicts."""
    rows = list(csv.DictReader(tsv_path.open(), delimiter="\t"))
    out: list[dict[str, Any]] = []
    for r in rows:
        rec: dict[str, Any] = {
            "id": r["id"].strip(),
            "task_name": r["task"].strip(),
            "phenix_tool_refs": split_pipe(r["phenix_tools"]),
            "phenix_doc_paths": split_pipe(r["phenix_doc_paths"]),
            "oracle_tool_refs": split_pipe(r["independent_oracles"]),
            "metric_definition_refs": split_pipe(r["metrics"]),
            "inputs_description": r["inputs"].strip() or None,
            "gold_standard": r["gold_standard"].strip() or None,
            "example_dataset": r["example_dataset"].strip() or None,
        }
        # Drop None values to keep YAML clean.
        rec = {k: v for k, v in rec.items() if v not in (None, [], "")}
        out.append(rec)
    return out


def collect_tools_and_metrics(catalog_records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Derive Tool and MetricDefinition records from catalog refs.

    Tools mentioned in phenix_tool_refs are tagged family=cctbx; tools in
    oracle_tool_refs default to non_cctbx (the catalog-level convention).
    """
    tools: dict[str, dict[str, Any]] = {}
    metrics: dict[str, dict[str, Any]] = {}
    for rec in catalog_records:
        tid = rec["id"]
        for name in rec.get("phenix_tool_refs", []):
            t = tools.setdefault(name, {"id": name, "family": "cctbx", "catalog_tasks_served": []})
            if tid not in t["catalog_tasks_served"]:
                t["catalog_tasks_served"].append(tid)
        for name in rec.get("oracle_tool_refs", []):
            t = tools.setdefault(name, {"id": name, "family": "non_cctbx", "catalog_tasks_served": []})
            if tid not in t["catalog_tasks_served"]:
                t["catalog_tasks_served"].append(tid)
        for metric_label in rec.get("metric_definition_refs", []):
            mid = f"{tid}_{slugify(metric_label)}"
            m = metrics.setdefault(mid, {"id": mid, "name": metric_label, "applicable_task_refs": []})
            if tid not in m["applicable_task_refs"]:
                m["applicable_task_refs"].append(tid)
    # Rewrite catalog metric_definition_refs from labels to ids so refs resolve.
    metric_label_to_id: dict[tuple[str, str], str] = {
        (tid, m["name"]): m["id"] for m in metrics.values() for tid in m["applicable_task_refs"]
    }
    for rec in catalog_records:
        labels = rec.get("metric_definition_refs", [])
        rec["metric_definition_refs"] = [metric_label_to_id[(rec["id"], lbl)] for lbl in labels]
    return list(tools.values()), list(metrics.values())


# --------------------------------------------------------------- eval rows


_HEADLINE_TASK_SPLIT = re.compile(r"[\\/]")


def _row_id(prefix: str, idx: int) -> str:
    return f"{prefix}_{idx:03d}"


def load_metrics(
    tsv_path: Path,
    eval_id: str,
    structure_id: str,
    artifact_id: str,
    run_date: str,
) -> dict[str, Any]:
    """Parse an EVAL_*_metrics.tsv into one EvaluationRun record."""
    rows = list(csv.DictReader(tsv_path.open(), delimiter="\t"))

    measurements: list[dict[str, Any]] = []
    catalog_tasks_seen: set[str] = set()
    metric_ids_seen: set[str] = set()
    for i, r in enumerate(rows, start=1):
        task = r["catalog_task"].strip()
        catalog_tasks_seen.add(task)
        metric_label = r["metric"].strip()
        metric_id = f"{task}_{slugify(metric_label)}"
        metric_ids_seen.add(metric_id)
        rec = {
            "id": _row_id(eval_id + "_M", i),
            "catalog_task_ref": task,
            "stage": (r.get("stage") or "all").strip() or "all",
            "metric_definition_ref": metric_id,
            "oracle_tool_ref": r["oracle_tool"].strip(),
            "oracle_family": r["oracle_family"].strip().replace("-", "_"),
            "agent_claim": parse_cell_to_measurement(r["agent_claim"]),
            "oracle_measure": parse_cell_to_measurement(r["oracle_measure"]),
        }
        if r.get("delta") and r["delta"].strip():
            rec["delta"] = parse_cell_to_measurement(r["delta"])
        if r.get("pass_criterion") and r["pass_criterion"].strip():
            rec["pass_criterion"] = r["pass_criterion"].strip()
        if r.get("pass_status") and r["pass_status"].strip():
            rec["pass_status"] = r["pass_status"].strip()
        measurements.append(rec)

    return {
        "id": eval_id,
        "eval_filename_stem": eval_id,
        "structure_ref": structure_id,
        "artifact_ref": artifact_id,
        "run_date": run_date,
        "catalog_tasks_applied": sorted(catalog_tasks_seen),
        "measurements": measurements,
    }


def load_headline(
    tsv_path: Path,
    eval_id: str,
) -> list[dict[str, Any]]:
    """Parse an EVAL_*_headline.tsv into a list of HeadlineFinding dicts."""
    rows = list(csv.DictReader(tsv_path.open(), delimiter="\t"))
    out: list[dict[str, Any]] = []
    for i, r in enumerate(rows, start=1):
        # catalog_task may be e.g. "T03/T06" — split into multivalued list.
        tasks = [t for t in _HEADLINE_TASK_SPLIT.split(r["catalog_task"].strip()) if t]
        if not tasks:
            tasks = [r["catalog_task"].strip()]
        # Use the first task as the metric-id namespace.
        primary_task = tasks[0]
        metric_label = r["metric"].strip()
        metric_id = f"{primary_task}_{slugify(metric_label)}"
        rec = {
            "id": _row_id(eval_id + "_H", i),
            "catalog_task_refs": tasks,
            "metric_definition_ref": metric_id,
            "oracle_tool_ref": r["oracle_tool"].strip(),
            "oracle_family": r["oracle_family"].strip().replace("-", "_"),
            "agent_claim": parse_cell_to_measurement(r["agent_claim"]),
            "oracle_measure": parse_cell_to_measurement(r["oracle_measure"]),
            "verdict_label": r.get("verdict", "").strip() or None,
            "notes": r.get("notes", "").strip() or None,
        }
        rec = {k: v for k, v in rec.items() if v not in (None, "", [])}
        out.append(rec)
    return out


# --------------------------------------------------------------------- IO


def yaml_dump(obj: Any) -> str:
    return yaml.safe_dump(obj, sort_keys=False, default_flow_style=False, allow_unicode=True)


def detect_kind(tsv_path: Path) -> str:
    with tsv_path.open() as f:
        header = f.readline().rstrip("\n").split("\t")
    cols = set(header)
    if {"id", "task", "phenix_tools"}.issubset(cols):
        return "catalog"
    if {"catalog_task", "metric", "oracle_tool", "stage"}.issubset(cols):
        return "metrics"
    if {"catalog_task", "metric", "oracle_tool", "verdict"}.issubset(cols):
        return "headline"
    raise SystemExit(f"Cannot detect kind from columns: {header}")


def main() -> None:
    p = argparse.ArgumentParser(description="TSV → schema-compliant YAML records.")
    p.add_argument("tsv", type=Path)
    p.add_argument("--kind", choices=["catalog", "metrics", "headline"])
    p.add_argument("-o", "--output", type=Path, help="Output YAML path (default stdout).")
    p.add_argument("--merge-into", type=Path, help="(headline only) merge findings into existing EvaluationRun YAML.")
    p.add_argument("--eval-id")
    p.add_argument("--structure-id")
    p.add_argument("--artifact-id")
    p.add_argument("--run-date")
    args = p.parse_args()

    kind = args.kind or detect_kind(args.tsv)

    if kind == "catalog":
        catalog_records = load_catalog(args.tsv)
        tools, metrics = collect_tools_and_metrics(catalog_records)
        container = {
            "catalog_tasks": catalog_records,
            "tools": tools,
            "metric_definitions": metrics,
        }
        out_text = yaml_dump(container)

    elif kind == "metrics":
        for required in ("eval_id", "structure_id", "artifact_id", "run_date"):
            if getattr(args, required) is None:
                p.error(f"--{required.replace('_', '-')} is required for metrics kind")
        eval_run = load_metrics(args.tsv, args.eval_id, args.structure_id, args.artifact_id, args.run_date)
        container = {"evaluation_runs": [eval_run]}
        out_text = yaml_dump(container)

    elif kind == "headline":
        if not args.merge_into:
            if not args.eval_id:
                p.error("--eval-id required for headline kind without --merge-into")
            findings = load_headline(args.tsv, args.eval_id)
            container = {"evaluation_runs": [{"id": args.eval_id, "headline_findings": findings}]}
            out_text = yaml_dump(container)
        else:
            doc = yaml.safe_load(args.merge_into.read_text())
            assert "evaluation_runs" in doc and len(doc["evaluation_runs"]) == 1, \
                "expected exactly one EvaluationRun in --merge-into"
            eval_run = doc["evaluation_runs"][0]
            findings = load_headline(args.tsv, eval_run["id"])
            eval_run["headline_findings"] = findings
            container = doc
            out_text = yaml_dump(container)
    else:
        raise SystemExit(f"Unknown kind: {kind}")

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(out_text)
        sys.stderr.write(f"wrote {args.output}\n")
    else:
        sys.stdout.write(out_text)


if __name__ == "__main__":
    main()
