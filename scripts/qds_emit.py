#!/usr/bin/env python3
"""Emit a QualityDataSheet YAML from one or more EvaluationRun YAMLs.

A QDS is the citable, dated, immutable snapshot of cross-tool findings for one
structure. It joins headline-level facts (R-factors, geometry, map quality)
across the EvaluationRuns it derives from, plus a `cross_tool_coverage`
section, plus per-residue / site / ligand / pairwise / predicted-confidence /
tool-recommendations blocks when the source eval carries that content.

Routing is driven by an explicit `METRIC_TO_QDS_SLOT` table keyed on the
canonical metric ids declared in `ref/catalog.yaml`. Substring matching is
not used. Strongest-oracle picking (prefer non_cctbx; prefer numeric over
text) is the tie-breaker when multiple measurements share a metric id.

After building, a fail-hard consistency pass rejects QDS that would hide
load-bearing local content: a scope=site measurement implies a
SiteQuality block, a residue_outliers/density_peaks/per_residue_values
list on the eval implies a PerResidueQuality block, etc.

Usage:
    python scripts/qds_emit.py \\
        data/examples/eval/EVAL_1sar_cdba2c07_2026-04-24.yaml \\
        --qds-id QDS_1sar_cdba2c07_2026-04-26 \\
        --structure-id 1sar \\
        -o data/examples/qds/QDS_1sar_cdba2c07_2026-04-26.yaml
"""
from __future__ import annotations

import argparse
import datetime as dt
import statistics
import sys
from pathlib import Path
from typing import Any

import yaml


REPO = Path(__file__).resolve().parent.parent
CATALOG_PATH = REPO / "ref" / "catalog.yaml"
TOOL_RECS_PATH = REPO / "ref" / "tool_recommendations.yaml"
TOOL_ASSUMPTIONS_PATH = REPO / "ref" / "tool_assumptions.yaml"


# ---------------------------------------------------------------------------
# Metric-id → QDS-block routing table
#
# Every metric_definition_ref the harness records routes through this table.
# Adding a new metric ⇒ add a new row here. Validated against the catalog
# at startup so a typo is caught before a QDS is emitted.
# ---------------------------------------------------------------------------

METRIC_TO_QDS_SLOT: dict[str, tuple[str, str]] = {
    # Geometry summary
    "T05_clashscore":              ("geometry_summary", "clashscore"),
    "T05_ramachandran_outlier":    ("geometry_summary", "ramachandran_outliers_pct"),
    "T05_ramachandran_favored":    ("geometry_summary", "ramachandran_favored_pct"),
    "T05_rotamer_outlier":         ("geometry_summary", "rotamer_outliers_pct"),
    "T05_molprobity_composite":    ("geometry_summary", "molprobity_score"),
    "T05_bond-length_rmsd":        ("geometry_summary", "bond_rmsd_a"),
    "T05_bond-angle_rmsd":         ("geometry_summary", "angle_rmsd_deg"),
    "T05_bond-length_rmsz":        ("geometry_summary", "bond_rmsz"),
    "T05_bond-angle_rmsz":         ("geometry_summary", "angle_rmsz"),
    "T05_cbeta_outliers":          ("geometry_summary", "cbeta_deviations_count"),
    "T05_rama_z_score":            ("geometry_summary", "ramachandran_z_score"),
    "T05_packing_z_score":         ("geometry_summary", "packing_z_score"),
    "T05_unsatisfied_buried_hbond_count": ("geometry_summary", "unsatisfied_buried_hbond_count"),
    "T05_b_factor_outlier_z":      ("packing_summary", "b_factor_outlier_z"),

    # Refinement summary (X-ray)
    "T03_r-work":                  ("refinement_summary", "r_work"),
    "T03_r-free":                  ("refinement_summary", "r_free"),
    "T03_r-free_r-work_gap":       ("refinement_summary", "r_free_gap"),
    "T06_r-work":                  ("refinement_summary", "r_work"),
    "T06_r-free":                  ("refinement_summary", "r_free"),
    "T06_diffraction_precision_index": ("refinement_summary", "diffraction_precision_index"),

    # Data-quality summary (X-ray)
    "T13_completeness_overall_outer": ("data_quality_summary", "completeness_overall_pct"),
    "T13_i_σ_i":                      ("data_quality_summary", "mean_i_over_sigma_outer"),
    "T13_cc½":                        ("data_quality_summary", "cc_half_outer"),
    "T13_r-merge_r-meas":             ("data_quality_summary", "r_merge"),
    "T13_wilson_b":                   ("data_quality_summary", "wilson_b"),

    # Map summary (cryo-EM)
    "T06_d_fsc_model":             ("map_summary", "d_fsc_model_a"),
    "T12_cc_box":                  ("map_summary", "cc_box"),
    "T12_cc_volume":               ("map_summary", "cc_volume"),
    "T12_emringer":                ("map_summary", "emringer_score"),
    "T12_q_score":                 ("map_summary", "mean_q_score"),
    "T12_global_fsc_0143":         ("map_summary", "global_fsc_0143_a"),
    "T12_local_resolution_mean":   ("map_summary", "local_resolution_mean_a"),
    "T12_local_resolution_std":    ("map_summary", "local_resolution_std_a"),
    "T12_directional_resolution_anisotropy": ("map_summary", "directional_resolution_anisotropy"),
    "T12_local_model_map_fsc_q":   ("map_summary", "local_model_map_fsc_q"),
    "T06_rscc_outlier_fraction":   ("map_summary", "rscc_outlier_fraction"),

    # Predicted confidence summary
    "T07_predicted_tm_score":      ("predicted_confidence_summary", "predicted_tm_score"),
    "T07_interface_predicted_tm_score": ("predicted_confidence_summary", "interface_predicted_tm_score"),
    "T07_prediction_ensemble_convergence": ("predicted_confidence_summary", "prediction_ensemble_convergence"),

    # Structured optional summary blocks
    "T15_secondary_structure_assignment": ("classification_summary", "secondary_structure_assignment"),
    "T15_structural_domain_assignment": ("classification_summary", "structural_domain_assignment"),
    "T15_fold_classification":     ("classification_summary", "fold_classification"),
    "T16_interface_buried_surface_area": ("interface_quality_summary", "interface_buried_surface_area"),
    "T16_interface_dockq_score":   ("interface_quality_summary", "interface_dockq_score"),
    "T16_capri_interface_quality_class": ("interface_quality_summary", "capri_interface_quality_class"),
    "T17_nmr_restraint_violation_summary": ("nmr_validation_summary", "nmr_restraint_violation_summary"),
    "T17_nmr_ensemble_precision_rmsd": ("nmr_validation_summary", "nmr_ensemble_precision_rmsd"),
}


# Some high-value indicators intentionally appear both in an existing
# headline summary and a newer specialized block. Keep the canonical primary
# route above, then mirror these values into the optional block.
EXTRA_METRIC_TO_QDS_SLOTS: dict[str, list[tuple[str, str]]] = {
    "T05_packing_z_score": [("packing_summary", "packing_z_score")],
    "T05_unsatisfied_buried_hbond_count": [("packing_summary", "unsatisfied_buried_hbond_count")],
    "T07_prediction_ensemble_convergence": [
        ("prediction_ensemble_summary", "prediction_ensemble_convergence")
    ],
}


# Metric ids that, when a measurement carries them, force the QDS to populate
# `predicted_confidence_summary`. Predicted-model evals also typically have
# `Structure.method == predicted_model`; either trigger fires the block.
PREDICTED_MARKER_METRIC_IDS: set[str] = {
    "T07_predicted_tm_score",
    "T07_interface_predicted_tm_score",
    "T07_prediction_ensemble_convergence",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def yaml_dump(obj: Any) -> str:
    return yaml.safe_dump(obj, sort_keys=False, default_flow_style=False, allow_unicode=True)


def _load_catalog_metric_ids() -> set[str]:
    doc = yaml.safe_load(CATALOG_PATH.read_text())
    return {m["id"] for m in doc.get("metric_definitions", [])}


def _validate_routing_table() -> None:
    """Every key in METRIC_TO_QDS_SLOT must exist in ref/catalog.yaml."""
    catalog_ids = _load_catalog_metric_ids()
    routed_ids = set(METRIC_TO_QDS_SLOT) | set(EXTRA_METRIC_TO_QDS_SLOTS)
    bad = [mid for mid in routed_ids if mid not in catalog_ids]
    if bad:
        raise SystemExit(
            "qds_emit: QDS routing references metric ids not in ref/catalog.yaml:\n  "
            + "\n  ".join(bad)
        )


def _final_or_all_measurements(eval_run: dict[str, Any]) -> list[dict[str, Any]]:
    return [m for m in eval_run.get("measurements", []) if m.get("stage") in ("final", "all")]


def _strongest(measurements: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Pick the strongest measurement: prefer non_cctbx, then numeric > text."""
    if not measurements:
        return None

    def rank(m: dict[str, Any]) -> tuple[int, int]:
        fam_score = 0 if m.get("oracle_family") == "non_cctbx" else 1
        oracle = m.get("oracle_measure") or {}
        type_score = 0 if oracle.get("value_numeric") is not None else 1
        return (fam_score, type_score)

    return sorted(measurements, key=rank)[0]


def _wrap_value(m: dict[str, Any] | None) -> dict[str, Any] | None:
    if m is None:
        return None
    v = dict(m.get("oracle_measure") or {})
    return v or None


# ---------------------------------------------------------------------------
# Routing: walk every measurement once, deposit each at its QDS slot
# ---------------------------------------------------------------------------


def _route_measurements(measurements: list[dict[str, Any]]) -> dict[str, dict[str, dict[str, Any]]]:
    """Return {block_name: {slot_name: <strongest measurement>}}.

    The strongest measurement for a (block, slot) pair is the one
    `_strongest` selects across all measurements that route to the same
    slot via METRIC_TO_QDS_SLOT.
    """
    by_slot: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for m in measurements:
        mid = m.get("metric_definition_ref")
        if mid not in METRIC_TO_QDS_SLOT:
            continue
        slots = [METRIC_TO_QDS_SLOT[mid], *EXTRA_METRIC_TO_QDS_SLOTS.get(mid, [])]
        for slot in slots:
            by_slot.setdefault(slot, []).append(m)

    out: dict[str, dict[str, dict[str, Any]]] = {}
    for (block, slot), candidates in by_slot.items():
        winner = _strongest(candidates)
        if winner is None:
            continue
        out.setdefault(block, {})[slot] = winner
    return out


# ---------------------------------------------------------------------------
# Block builders driven by the routing table
# ---------------------------------------------------------------------------


def _build_block_from_routed(qds_id: str, slot: str, routed: dict[str, dict[str, Any]] | None) -> dict[str, Any] | None:
    if not routed:
        return None
    populated: dict[str, Any] = {}
    for slot_name, meas in routed.items():
        v = _wrap_value(meas)
        if v:
            populated[slot_name] = v
    if not populated:
        return None
    return {"id": f"{qds_id}_{slot}", **populated}


# ---------------------------------------------------------------------------
# Identity, cross-tool coverage
# ---------------------------------------------------------------------------


def build_identity_block(qds_id: str, structure_id: str) -> dict[str, Any]:
    block: dict[str, Any] = {"id": f"{qds_id}_identity"}
    sid = structure_id.lower()
    if sid.startswith("emdb"):
        block["emdb_id"] = structure_id
    elif sid.startswith("af-") or sid.startswith("af_"):
        block["alphafold_id"] = structure_id
    else:
        block["pdb_id"] = structure_id
    return block


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


# ---------------------------------------------------------------------------
# Per-residue, site, ligand, pairwise, predicted, tool-recs
# ---------------------------------------------------------------------------


def _summary_stats(values: list[float]) -> dict[str, Any] | None:
    if not values:
        return None
    return {
        "value_numeric": statistics.fmean(values),
        "mean": statistics.fmean(values),
        "std_dev": statistics.pstdev(values) if len(values) > 1 else 0.0,
        "min_value": min(values),
        "max_value": max(values),
        "count": len(values),
    }


def _per_residue_values_by_metric(eval_runs: list[dict[str, Any]]) -> dict[str, list[float]]:
    """Group EvaluationRun.per_residue_values[] by underlying metric id."""
    out: dict[str, list[float]] = {}
    for r in eval_runs:
        for prv in r.get("per_residue_values", []) or []:
            mid = (prv.get("value") or {}).get("metric_definition_ref") or prv.get("metric_definition_ref")
            v = (prv.get("value") or {}).get("value_numeric")
            if mid is None or v is None:
                continue
            out.setdefault(mid, []).append(v)
    return out


PER_RESIDUE_METRIC_TO_SLOT: dict[str, str] = {
    "T01_per_residue_lddt":         "lddt_per_residue",
    "T01_per_residue_displacement": "displacement_per_residue_a",
    "T05_per_residue_rsrz":         "rsrz_per_residue",
    "T05_ramachandran_z_per_residue": "ramachandran_z_per_residue",
    "T06_residue_rscc":             "rscc_per_residue",
    "T05_b_factor_outlier_z":       "b_factor_z_per_residue",
    "T15_secondary_structure_assignment": "secondary_structure_per_residue",
    "T12_local_model_map_fsc_q":    "fsc_q_per_residue",
}


def build_per_residue_quality(qds_id: str, eval_runs: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Aggregate per-residue content from all eval_runs into one block.

    Source: EvaluationRun.{residue_outliers, density_peaks, flagged_regions,
    per_residue_values}. The PerResidueValue.metric_definition_ref routes
    each value to its array via PER_RESIDUE_METRIC_TO_SLOT — no substring
    matching.
    """
    outliers: list[dict[str, Any]] = []
    density_peaks: list[dict[str, Any]] = []
    flagged_regions: list[dict[str, Any]] = []
    arrays: dict[str, list[dict[str, Any]]] = {slot: [] for slot in PER_RESIDUE_METRIC_TO_SLOT.values()}

    for r in eval_runs:
        outliers.extend(r.get("residue_outliers", []) or [])
        density_peaks.extend(r.get("density_peaks", []) or [])
        flagged_regions.extend(r.get("flagged_regions", []) or [])

        for prv in r.get("per_residue_values", []) or []:
            mid = prv.get("metric_definition_ref")
            slot = PER_RESIDUE_METRIC_TO_SLOT.get(mid or "")
            if slot:
                arrays[slot].append(prv)

    has_arrays = any(arrays[slot] for slot in arrays)
    if not any([outliers, density_peaks, flagged_regions, has_arrays]):
        return None

    block: dict[str, Any] = {"id": f"{qds_id}_per_residue"}
    for slot, items in arrays.items():
        if items:
            block[slot] = items
    if outliers:
        block["outliers"] = outliers
    if density_peaks:
        block["density_peaks"] = density_peaks
    if flagged_regions:
        block["flagged_regions"] = flagged_regions
    return block


def build_site_qualities(
    qds_id: str,
    eval_runs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """For each Site declared on any eval run, build a SiteQuality.

    Site-scoped measurements (scope=site, scope_selector matching the
    site id) populate site_clashscore, site_ramachandran_outlier_count,
    site_rmsd_to_reference_a, mean_per_residue_lddt, mean_b_factor.
    Ligand-scoped measurements via the bound ligand populate
    ligand_quality.
    """
    sites: list[dict[str, Any]] = [s for r in eval_runs for s in (r.get("sites") or [])]
    ligands: dict[str, dict[str, Any]] = {
        lig["id"]: lig for r in eval_runs for lig in (r.get("ligands") or [])
    }

    if not sites:
        return []

    # Index measurements by (scope, scope_selector or referenced site id).
    site_measurements: dict[str, list[dict[str, Any]]] = {}
    ligand_measurements: dict[str, list[dict[str, Any]]] = {}
    for r in eval_runs:
        for m in r.get("measurements", []):
            scope = m.get("scope")
            sel = m.get("scope_selector") or ""
            if scope == "site":
                site_measurements.setdefault(sel, []).append(m)
            elif scope == "ligand":
                ligand_measurements.setdefault(sel, []).append(m)

    site_metric_to_slot: dict[str, str] = {
        "T05_clashscore": "site_clashscore",
        "T05_ramachandran_outlier": "site_ramachandran_outlier_count",
        # Per-pair RMSD for sites uses the shared T01 metric ids.
        "T01_ca_rmsd_å": "site_rmsd_to_reference_a",
    }
    ligand_metric_to_slot: dict[str, str] = {
        "T10_ligand_rscc":                  "rscc",
        "T10_ligand_rsr":                   "rsr",
        "T10_ligand_b_vs_surroundings":     "ligand_b_factor_vs_surroundings",
        "T10_protein-ligand_hbond_count":   "protein_ligand_hbond_count",
        "T10_rmsd_to_deposited_ligand_pose": "pose_rmsd_to_deposited_a",
    }

    out: list[dict[str, Any]] = []
    for site in sites:
        sq: dict[str, Any] = {
            "id": f"{qds_id}_site_quality_{site['id']}",
            "site_ref": site["id"],
        }
        # Site-scoped measurements.
        for m in site_measurements.get(site["id"], []):
            mid = m.get("metric_definition_ref") or ""
            slot = site_metric_to_slot.get(mid)
            if slot:
                v = _wrap_value(m)
                if v:
                    sq[slot] = v

        # Ligand quality (when the site has a bound ligand).
        lig_ref = site.get("ligand_ref")
        if lig_ref and lig_ref in ligand_measurements:
            lq: dict[str, Any] = {
                "id": f"{qds_id}_ligand_quality_{lig_ref}",
                "ligand_ref": lig_ref,
            }
            for m in ligand_measurements[lig_ref]:
                mid = m.get("metric_definition_ref") or ""
                slot = ligand_metric_to_slot.get(mid)
                if slot:
                    v = _wrap_value(m)
                    if v:
                        lq[slot] = v
            if len(lq) > 2:  # more than just id + ligand_ref
                sq["ligand_quality"] = lq

        out.append(sq)
    return out


def build_pairwise_comparisons(eval_runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Pass-through any PairwiseComparison records on the eval runs."""
    return [pc for r in eval_runs for pc in (r.get("pairwise_comparisons") or [])]


def build_predicted_confidence_summary(
    qds_id: str,
    eval_runs: list[dict[str, Any]],
    structure_method: str | None = None,
) -> dict[str, Any] | None:
    """Emit when method is `predicted_model` or pLDDT/PAE metrics appear.

    The catalog now declares pTM/ipTM/convergence metric ids, so populate
    those fields directly from final/all measurements instead of emitting an
    id-only placeholder.
    """
    measurements = [
        m
        for r in eval_runs
        for m in r.get("measurements", []) or []
        if m.get("stage") in ("final", "all")
        and m.get("metric_definition_ref") in PREDICTED_MARKER_METRIC_IDS
    ]
    has_predicted_metrics = bool(measurements)
    if structure_method != "predicted_model" and not has_predicted_metrics:
        return None
    routed = _route_measurements(measurements).get("predicted_confidence_summary")
    block = _build_block_from_routed(qds_id, "predicted_confidence", routed)
    if block:
        return block
    if structure_method == "predicted_model":
        return {"id": f"{qds_id}_predicted_confidence"}
    return None


def build_classification_summary(
    qds_id: str,
    routed: dict[str, dict[str, Any]] | None,
    eval_runs: list[dict[str, Any]],
) -> dict[str, Any] | None:
    block = _build_block_from_routed(qds_id, "classification", routed) or {
        "id": f"{qds_id}_classification"
    }
    ss = [x for r in eval_runs for x in (r.get("secondary_structure_assignments") or [])]
    domains = [x for r in eval_runs for x in (r.get("domain_assignments") or [])]
    if ss:
        block["secondary_structure_assignments"] = ss
    if domains:
        block["domain_assignments"] = domains
    return block if len(block) > 1 else None


def build_interface_quality_summary(
    qds_id: str,
    routed: dict[str, dict[str, Any]] | None,
    eval_runs: list[dict[str, Any]],
) -> dict[str, Any] | None:
    block = _build_block_from_routed(qds_id, "interface_quality", routed) or {
        "id": f"{qds_id}_interface_quality"
    }
    rows = [x for r in eval_runs for x in (r.get("interface_qualities") or [])]
    if rows:
        block["interface_qualities"] = rows
    return block if len(block) > 1 else None


def build_prediction_ensemble_summary(
    qds_id: str,
    routed: dict[str, dict[str, Any]] | None,
    eval_runs: list[dict[str, Any]],
) -> dict[str, Any] | None:
    block = _build_block_from_routed(qds_id, "prediction_ensemble", routed) or {
        "id": f"{qds_id}_prediction_ensemble"
    }
    rows = [x for r in eval_runs for x in (r.get("prediction_ensemble_qualities") or [])]
    if rows:
        block["prediction_ensemble_qualities"] = rows
    return block if len(block) > 1 else None


def build_nmr_validation_summary(
    qds_id: str,
    routed: dict[str, dict[str, Any]] | None,
    eval_runs: list[dict[str, Any]],
) -> dict[str, Any] | None:
    block = _build_block_from_routed(qds_id, "nmr_validation", routed) or {
        "id": f"{qds_id}_nmr_validation"
    }
    rows = [x for r in eval_runs for x in (r.get("nmr_ensemble_qualities") or [])]
    if rows:
        block["nmr_ensemble_qualities"] = rows
    return block if len(block) > 1 else None


def build_assumptions_report(eval_runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Aggregate per-tool, per-measurement, per-run assumptions into a flat list.

    Source order (and the order surfaced in the QDS):
      1. Tool-level: every distinct oracle_tool_ref in the eval's measurements
         is looked up in ref/tool_assumptions.yaml; the matching tool's
         assumptions[] are emitted.
      2. Measurement-level: assumptions[] attached directly to a
         MeasurementValue (or HeadlineFinding).
      3. Run-level: EvaluationRun.assumptions[] (typically the agentic-
         framework's reporting / interpretation / aggregation conventions).

    Duplicate assumption ids are dropped on the second-and-later occurrence
    so the QDS doesn't repeat a tool-level assumption per measurement.
    """
    out: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    # Load tool_assumptions.yaml once and index by tool_ref.
    tool_assumptions_by_tool: dict[str, list[dict[str, Any]]] = {}
    if TOOL_ASSUMPTIONS_PATH.exists():
        ta_doc = yaml.safe_load(TOOL_ASSUMPTIONS_PATH.read_text()) or {}
        for a in ta_doc.get("assumptions", []) or []:
            tref = a.get("tool_ref")
            if tref:
                tool_assumptions_by_tool.setdefault(tref, []).append(a)

    # 1. Tool-level (distinct oracle_tool_ref values used in the eval).
    distinct_tools: list[str] = []
    seen_tools: set[str] = set()
    for r in eval_runs:
        for m in r.get("measurements", []) or []:
            t = m.get("oracle_tool_ref")
            if t and t not in seen_tools:
                seen_tools.add(t)
                distinct_tools.append(t)
    for t in distinct_tools:
        for a in tool_assumptions_by_tool.get(t, []):
            if a["id"] in seen_ids:
                continue
            seen_ids.add(a["id"])
            out.append(a)

    # 2. Measurement-level assumptions.
    for r in eval_runs:
        for m in r.get("measurements", []) or []:
            for a in m.get("assumptions", []) or []:
                if a["id"] in seen_ids:
                    continue
                seen_ids.add(a["id"])
                out.append(a)

    # 3. Run-level (agent-framework) assumptions.
    for r in eval_runs:
        for a in r.get("assumptions", []) or []:
            if a["id"] in seen_ids:
                continue
            seen_ids.add(a["id"])
            out.append(a)

    return out


def build_tool_recommendations_applied(eval_runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Snapshot of recommendations whose metric was actually measured here.

    Loaded from ref/tool_recommendations.yaml. The QDS embeds them inline
    so the published artifact is self-contained — recommendations evolve
    over time, this freezes the ones active at QDS issue time.
    """
    if not TOOL_RECS_PATH.exists():
        return []
    doc = yaml.safe_load(TOOL_RECS_PATH.read_text()) or {}
    recs = doc.get("tool_recommendations", []) or []
    measured_ids: set[str] = set()
    for r in eval_runs:
        for m in r.get("measurements", []) or []:
            mid = m.get("metric_definition_ref")
            if mid:
                measured_ids.add(mid)
    return [rec for rec in recs if rec.get("metric_definition_ref") in measured_ids]


# ---------------------------------------------------------------------------
# Fail-hard implied-content check
# ---------------------------------------------------------------------------


class QdsCompletenessError(SystemExit):
    pass


def _check_implied_blocks(qds: dict[str, Any], eval_runs: list[dict[str, Any]]) -> None:
    """Reject QDS that hide content the source eval implies must be present."""
    errors: list[str] = []

    for r in eval_runs:
        # scope=site implies SiteQuality.
        site_scope_ms = [m for m in (r.get("measurements") or []) if m.get("scope") == "site"]
        if site_scope_ms and not qds.get("site_qualities"):
            errors.append(
                f"eval {r['id']}: {len(site_scope_ms)} measurement(s) have scope=site "
                f"but the QDS has no site_qualities. Declare Sites on the eval or "
                f"correct the scope."
            )
        # scope=ligand implies LigandQuality nested inside a SiteQuality.
        ligand_scope_ms = [m for m in (r.get("measurements") or []) if m.get("scope") == "ligand"]
        ligand_qualities_present = any(
            sq.get("ligand_quality") for sq in qds.get("site_qualities", []) or []
        )
        if ligand_scope_ms and not ligand_qualities_present:
            errors.append(
                f"eval {r['id']}: {len(ligand_scope_ms)} measurement(s) have scope=ligand "
                f"but no LigandQuality is present in any SiteQuality. Declare Ligands "
                f"on the eval and bind them to a Site."
            )
        # scope=residue implies PerResidueQuality.
        residue_scope_ms = [m for m in (r.get("measurements") or []) if m.get("scope") == "residue"]
        if residue_scope_ms and not qds.get("per_residue_quality"):
            errors.append(
                f"eval {r['id']}: {len(residue_scope_ms)} measurement(s) have scope=residue "
                f"but the QDS has no per_residue_quality."
            )
        # scope=domain implies explicit domain/classification rows.
        domain_scope_ms = [m for m in (r.get("measurements") or []) if m.get("scope") == "domain"]
        domain_rows_present = bool(
            (qds.get("classification_summary") or {}).get("domain_assignments")
        )
        if domain_scope_ms and not domain_rows_present:
            errors.append(
                f"eval {r['id']}: {len(domain_scope_ms)} measurement(s) have scope=domain "
                f"but classification_summary.domain_assignments is absent. Declare "
                f"DomainAssignment rows or correct the scope."
            )
        # scope=interface implies explicit interface rows.
        interface_scope_ms = [m for m in (r.get("measurements") or []) if m.get("scope") == "interface"]
        interface_rows_present = bool(
            (qds.get("interface_quality_summary") or {}).get("interface_qualities")
        )
        if interface_scope_ms and not interface_rows_present:
            errors.append(
                f"eval {r['id']}: {len(interface_scope_ms)} measurement(s) have scope=interface "
                f"but interface_quality_summary.interface_qualities is absent. Declare "
                f"InterfaceQuality rows or correct the scope."
            )
        # scope=ensemble implies an NMR or prediction ensemble row.
        ensemble_scope_ms = [m for m in (r.get("measurements") or []) if m.get("scope") == "ensemble"]
        prediction_ensemble_ms = [
            m for m in ensemble_scope_ms if m.get("catalog_task_ref") == "T07"
        ]
        nmr_ensemble_ms = [
            m for m in ensemble_scope_ms if m.get("catalog_task_ref") == "T17"
        ]
        other_ensemble_ms = [
            m for m in ensemble_scope_ms if m.get("catalog_task_ref") not in ("T07", "T17")
        ]
        prediction_rows_present = bool(
            (qds.get("prediction_ensemble_summary") or {}).get("prediction_ensemble_qualities")
        )
        nmr_rows_present = bool(
            (qds.get("nmr_validation_summary") or {}).get("nmr_ensemble_qualities")
        )
        if prediction_ensemble_ms and not prediction_rows_present:
            errors.append(
                f"eval {r['id']}: {len(prediction_ensemble_ms)} T07 measurement(s) have "
                f"scope=ensemble but prediction_ensemble_qualities is absent."
            )
        if nmr_ensemble_ms and not nmr_rows_present:
            errors.append(
                f"eval {r['id']}: {len(nmr_ensemble_ms)} T17 measurement(s) have "
                f"scope=ensemble but nmr_ensemble_qualities is absent."
            )
        if other_ensemble_ms and not (prediction_rows_present or nmr_rows_present):
            errors.append(
                f"eval {r['id']}: {len(other_ensemble_ms)} measurement(s) have "
                f"scope=ensemble but no ensemble quality row is present."
            )
        # Residue-level lists on the eval imply PerResidueQuality.
        residue_content_present = any([
            r.get("residue_outliers"),
            r.get("density_peaks"),
            r.get("flagged_regions"),
            r.get("per_residue_values"),
        ])
        if residue_content_present and not qds.get("per_residue_quality"):
            errors.append(
                f"eval {r['id']}: residue-level lists present (residue_outliers / "
                f"density_peaks / flagged_regions / per_residue_values) but the QDS "
                f"has no per_residue_quality. Emitter is silently dropping content."
            )
        # pairwise_comparisons on eval imply pairwise_comparisons on QDS.
        if r.get("pairwise_comparisons") and not qds.get("pairwise_comparisons"):
            errors.append(
                f"eval {r['id']}: pairwise_comparisons declared but absent from QDS."
            )
        # sites on eval but no site_qualities.
        if r.get("sites") and not qds.get("site_qualities"):
            errors.append(
                f"eval {r['id']}: sites declared ({[s['id'] for s in r['sites']]}) "
                f"but the QDS has no site_qualities."
            )
        if (r.get("secondary_structure_assignments") or r.get("domain_assignments")) and not qds.get("classification_summary"):
            errors.append(
                f"eval {r['id']}: classification rows declared but absent from QDS."
            )
        if r.get("interface_qualities") and not qds.get("interface_quality_summary"):
            errors.append(
                f"eval {r['id']}: interface_qualities declared but absent from QDS."
            )
        if r.get("prediction_ensemble_qualities") and not qds.get("prediction_ensemble_summary"):
            errors.append(
                f"eval {r['id']}: prediction_ensemble_qualities declared but absent from QDS."
            )
        if r.get("nmr_ensemble_qualities") and not qds.get("nmr_validation_summary"):
            errors.append(
                f"eval {r['id']}: nmr_ensemble_qualities declared but absent from QDS."
            )

    if errors:
        msg = "QDS completeness check failed:\n  - " + "\n  - ".join(errors)
        raise QdsCompletenessError(msg)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def emit_qds(
    eval_paths: list[Path],
    qds_id: str,
    structure_id: str,
    structure_method: str | None = None,
) -> dict[str, Any]:
    _validate_routing_table()

    runs: list[dict[str, Any]] = []
    for path in eval_paths:
        doc = yaml.safe_load(path.read_text())
        for r in doc.get("evaluation_runs", []):
            runs.append(r)

    qds_measurements = [m for r in runs for m in _final_or_all_measurements(r)]
    final_only = [m for m in qds_measurements if m.get("stage") == "final"]
    all_only = [m for m in qds_measurements if m.get("stage") == "all"]

    # Route every measurement once via METRIC_TO_QDS_SLOT.
    routed_final = _route_measurements(final_only)
    routed_all = _route_measurements(all_only)
    routed_qds = _route_measurements(qds_measurements)

    qds: dict[str, Any] = {
        "id": qds_id,
        "structure_ref": structure_id,
        "derived_from_evaluation_run_refs": [r["id"] for r in runs],
        "issued_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "identity_block": build_identity_block(qds_id, structure_id),
    }

    # Routed blocks — final-stage measurements.
    geom = _build_block_from_routed(qds_id, "geometry", routed_final.get("geometry_summary"))
    if geom:
        qds["geometry_summary"] = geom
    refn = _build_block_from_routed(qds_id, "refinement", routed_final.get("refinement_summary"))
    if refn:
        qds["refinement_summary"] = refn
    mp = _build_block_from_routed(qds_id, "map", routed_final.get("map_summary"))
    if mp:
        qds["map_summary"] = mp

    packing = _build_block_from_routed(qds_id, "packing", routed_qds.get("packing_summary"))
    if packing:
        qds["packing_summary"] = packing

    classification = build_classification_summary(
        qds_id, routed_qds.get("classification_summary"), runs
    )
    if classification:
        qds["classification_summary"] = classification

    interface_quality = build_interface_quality_summary(
        qds_id, routed_qds.get("interface_quality_summary"), runs
    )
    if interface_quality:
        qds["interface_quality_summary"] = interface_quality

    prediction_ensemble = build_prediction_ensemble_summary(
        qds_id, routed_qds.get("prediction_ensemble_summary"), runs
    )
    if prediction_ensemble:
        qds["prediction_ensemble_summary"] = prediction_ensemble

    nmr_validation = build_nmr_validation_summary(
        qds_id, routed_qds.get("nmr_validation_summary"), runs
    )
    if nmr_validation:
        qds["nmr_validation_summary"] = nmr_validation

    # Data-quality summary — dataset-wide measurements (stage=all).
    dq = _build_block_from_routed(qds_id, "data_quality", routed_all.get("data_quality_summary"))
    if dq:
        qds["data_quality_summary"] = dq

    # Pairwise comparisons.
    pcs = build_pairwise_comparisons(runs)
    if pcs:
        qds["pairwise_comparisons"] = pcs

    # Per-residue quality.
    prq = build_per_residue_quality(qds_id, runs)
    if prq:
        qds["per_residue_quality"] = prq

    # Site qualities.
    sqs = build_site_qualities(qds_id, runs)
    if sqs:
        qds["site_qualities"] = sqs

    # Predicted-confidence summary.
    pcs_block = build_predicted_confidence_summary(qds_id, runs, structure_method)
    if pcs_block:
        qds["predicted_confidence_summary"] = pcs_block

    # Cross-tool coverage uses every measurement that informed the QDS.
    qds["cross_tool_coverage"] = build_cross_tool_coverage(qds_id, qds_measurements)

    # Snapshot of recommendations active at issue time.
    recs = build_tool_recommendations_applied(runs)
    if recs:
        qds["tool_recommendations_applied"] = recs

    # Aggregated tool / measurement / framework assumptions.
    assumptions = build_assumptions_report(runs)
    if assumptions:
        qds["assumptions_report"] = assumptions

    # Headline verdict — stitch together any per-run verdicts.
    headline_lines = [r["headline_verdict"] for r in runs if r.get("headline_verdict")]
    if headline_lines:
        qds["headline_verdict"] = "\n\n".join(headline_lines)

    # Fail-hard implied-content check.
    _check_implied_blocks(qds, runs)

    return qds


def main() -> int:
    p = argparse.ArgumentParser(description="EvaluationRun → QualityDataSheet emitter.")
    p.add_argument("eval_yaml", type=Path, nargs="+", help="One or more EvaluationRun YAML files.")
    p.add_argument("--qds-id", required=True)
    p.add_argument("--structure-id", required=True)
    p.add_argument(
        "--structure-method",
        choices=["xray", "cryo_em", "predicted_model", "nmr"],
        default=None,
        help="Set the structure's method to enable modality-specific block emission.",
    )
    p.add_argument("-o", "--output", type=Path)
    args = p.parse_args()

    qds = emit_qds(
        args.eval_yaml, args.qds_id, args.structure_id, args.structure_method
    )
    container = {"quality_data_sheets": [qds]}
    out_text = yaml_dump(container)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(out_text)
        sys.stderr.write(f"wrote {args.output}\n")
    else:
        sys.stdout.write(out_text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
