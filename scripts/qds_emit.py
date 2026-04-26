#!/usr/bin/env python3
"""Emit a QualityDataSheet YAML from one or more EvaluationRun YAMLs.

A QDS is the citable, dated, immutable snapshot of cross-tool findings for one
structure. It joins headline-level facts (R-factors, geometry, map quality)
across the EvaluationRuns it derives from, plus a `cross_tool_coverage`
section that records which oracle families confirmed each task.

Usage:
    python scripts/qds_emit.py \\
        data/examples/eval/EVAL_1sar_cdba2c07_2026-04-24.yaml \\
        --qds-id QDS_1sar_cdba2c07_2026-04-24 \\
        --structure-id 1sar \\
        -o data/examples/qds/QDS_1sar_cdba2c07_2026-04-24.yaml

The picker that chooses which MeasurementValue feeds each QDS slot is
deliberately small and explicit: pattern-match the metric_definition_ref name,
prefer non_cctbx oracle_family, fall back to cctbx.
"""
from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path
from typing import Any

import yaml


def yaml_dump(obj: Any) -> str:
    return yaml.safe_dump(obj, sort_keys=False, default_flow_style=False, allow_unicode=True)


def _final_measurements(eval_run: dict[str, Any]) -> list[dict[str, Any]]:
    return [m for m in eval_run.get("measurements", []) if m.get("stage") == "final"]


def _pick_strongest(
    measurements: list[dict[str, Any]],
    metric_substrings: tuple[str, ...],
    exclude_substrings: tuple[str, ...] = (),
) -> dict[str, Any] | None:
    """Return the MeasurementValue whose metric_definition_ref contains any of
    `metric_substrings` (case-insensitive) and none of `exclude_substrings`,
    preferring non_cctbx oracles, then preferring rows whose oracle_measure
    has a numeric value (over text)."""
    def matches(m: dict[str, Any]) -> bool:
        ref = (m.get("metric_definition_ref") or "").lower()
        if not any(s.lower() in ref for s in metric_substrings):
            return False
        if any(s.lower() in ref for s in exclude_substrings):
            return False
        return True

    candidates = [m for m in measurements if matches(m)]
    if not candidates:
        return None

    def rank(m: dict[str, Any]) -> tuple[int, int]:
        fam_score = 0 if m.get("oracle_family") == "non_cctbx" else 1
        oracle = m.get("oracle_measure") or {}
        type_score = 0 if oracle.get("value_numeric") is not None else 1
        return (fam_score, type_score)

    candidates.sort(key=rank)
    return candidates[0]


def _wrap_value(m: dict[str, Any] | None, key: str = "oracle_measure") -> dict[str, Any] | None:
    """Pull the TypedMeasurementValue dict out of a MeasurementValue, copy
    it shallow, and add a small `id` so it can serialise as an inlined object."""
    if m is None:
        return None
    v = dict(m.get(key) or {})
    if not v:
        return None
    return v


def build_geometry_summary(qds_id: str, measurements: list[dict[str, Any]]) -> dict[str, Any] | None:
    rows = {
        "clashscore": _pick_strongest(measurements, ("clashscore",), exclude_substrings=("atoms_used", "clashes_unique")),
        "ramachandran_outliers_pct": _pick_strongest(measurements, ("ramachandran_outliers",), exclude_substrings=("count",)),
        "ramachandran_favored_pct": _pick_strongest(measurements, ("ramachandran_favored",)),
        "rotamer_outliers_pct": _pick_strongest(measurements, ("rotamer_outliers",)),
        "molprobity_score": _pick_strongest(measurements, ("molprobity_score",)),
        "bond_rmsd_a": _pick_strongest(measurements, ("bond_rmsd",)),
        "angle_rmsd_deg": _pick_strongest(measurements, ("angle_rmsd",)),
    }
    populated = {k: _wrap_value(v) for k, v in rows.items() if v is not None}
    populated = {k: v for k, v in populated.items() if v}
    if not populated:
        return None
    populated["id"] = f"{qds_id}_geometry"
    # Re-order so id comes first.
    return {"id": populated.pop("id"), **populated}


def build_refinement_summary(qds_id: str, measurements: list[dict[str, Any]]) -> dict[str, Any] | None:
    r_work = _pick_strongest(measurements, ("r-work",), exclude_substrings=("r-free", "gap"))
    r_free = _pick_strongest(measurements, ("r-free",), exclude_substrings=("gap", "δ", "delta"))
    gap = _pick_strongest(measurements, ("gap",))
    populated: dict[str, Any] = {}
    if r_work:
        populated["r_work"] = _wrap_value(r_work)
    if r_free:
        populated["r_free"] = _wrap_value(r_free)
    if gap:
        populated["r_free_gap"] = _wrap_value(gap)
    populated = {k: v for k, v in populated.items() if v}
    if not populated:
        return None
    return {"id": f"{qds_id}_refinement", **populated}


def build_map_summary(qds_id: str, measurements: list[dict[str, Any]]) -> dict[str, Any] | None:
    cc_mask = _pick_strongest(measurements, ("cc_mask", "cc-mask"))
    d_fsc = _pick_strongest(measurements, ("d_fsc_model", "d-fsc"))
    populated: dict[str, Any] = {}
    if cc_mask:
        populated["cc_mask"] = _wrap_value(cc_mask)
    if d_fsc:
        populated["d_fsc_model_a"] = _wrap_value(d_fsc)
    populated = {k: v for k, v in populated.items() if v}
    if not populated:
        return None
    return {"id": f"{qds_id}_map", **populated}


def build_cross_tool_coverage(qds_id: str, measurements: list[dict[str, Any]]) -> dict[str, Any]:
    by_task: dict[str, dict[str, set[str]]] = {}
    for m in measurements:
        t = m.get("catalog_task_ref")
        if not t:
            continue
        bucket = by_task.setdefault(t, {"cctbx": set(), "non_cctbx": set()})
        fam = m.get("oracle_family") or ""
        tool = m.get("oracle_tool_ref") or ""
        if fam == "cctbx":
            bucket["cctbx"].add(tool)
        elif fam == "non_cctbx":
            bucket["non_cctbx"].add(tool)
    rows = []
    for t in sorted(by_task):
        cctbx = sorted(x for x in by_task[t]["cctbx"] if x)
        non_cctbx = sorted(x for x in by_task[t]["non_cctbx"] if x)
        if non_cctbx:
            gap = "closed" if cctbx else "non-cctbx only"
        else:
            gap = "open — cctbx only"
        rows.append({
            "id": f"{qds_id}_coverage_{t}",
            "catalog_task_ref": t,
            "cctbx_oracles": cctbx,
            "non_cctbx_oracles": non_cctbx,
            "gap_status": gap,
        })
    return {"id": f"{qds_id}_coverage", "task_coverage": rows}


def build_identity_block(qds_id: str, structure_id: str) -> dict[str, Any]:
    # v0: only the id field is filled. Resolution / method / space group are
    # left for future enrichment from a structure registry.
    block: dict[str, Any] = {"id": f"{qds_id}_identity"}
    sid = structure_id.lower()
    if sid.startswith("emdb"):
        block["emdb_id"] = structure_id
    elif sid.startswith("af-") or sid.startswith("af_"):
        block["alphafold_id"] = structure_id
    else:
        block["pdb_id"] = structure_id
    return block


def main() -> None:
    p = argparse.ArgumentParser(description="EvaluationRun → QualityDataSheet emitter.")
    p.add_argument("eval_yaml", type=Path, nargs="+", help="One or more EvaluationRun YAML files.")
    p.add_argument("--qds-id", required=True)
    p.add_argument("--structure-id", required=True)
    p.add_argument("-o", "--output", type=Path)
    args = p.parse_args()

    runs: list[dict[str, Any]] = []
    for path in args.eval_yaml:
        doc = yaml.safe_load(path.read_text())
        for r in doc.get("evaluation_runs", []):
            runs.append(r)

    final_measurements = [m for r in runs for m in _final_measurements(r)]

    qds_id = args.qds_id
    qds: dict[str, Any] = {
        "id": qds_id,
        "structure_ref": args.structure_id,
        "derived_from_evaluation_run_refs": [r["id"] for r in runs],
        "issued_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "identity_block": build_identity_block(qds_id, args.structure_id),
    }
    geom = build_geometry_summary(qds_id, final_measurements)
    if geom:
        qds["geometry_summary"] = geom
    refn = build_refinement_summary(qds_id, final_measurements)
    if refn:
        qds["refinement_summary"] = refn
    mp = build_map_summary(qds_id, final_measurements)
    if mp:
        qds["map_summary"] = mp
    qds["cross_tool_coverage"] = build_cross_tool_coverage(qds_id, final_measurements)

    headline_lines = []
    for r in runs:
        if r.get("headline_verdict"):
            headline_lines.append(r["headline_verdict"])
    if headline_lines:
        qds["headline_verdict"] = "\n\n".join(headline_lines)

    container = {"quality_data_sheets": [qds]}
    out_text = yaml_dump(container)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(out_text)
        import sys
        sys.stderr.write(f"wrote {args.output}\n")
    else:
        import sys
        sys.stdout.write(out_text)


if __name__ == "__main__":
    main()
