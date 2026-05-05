#!/usr/bin/env python3
"""Regression tests for scripts/qds_emit.py.

Closes the regression hole Codex flagged: previously the QDS emitter used
substring matching that silently dropped half the geometry slots from the
1SAR example, and had no builders for per_residue_quality, site_qualities,
pairwise_comparisons, or tool_recommendations_applied.

Three tests:

  1. 1SAR example → assert all expected geometry slots are present (the
     specific regression Codex named).
  2. Synthetic eval (data/examples/eval/EVAL_synth_active_site_*.yaml) →
     assert per_residue_quality, site_qualities (with ligand_quality),
     pairwise_comparisons, and tool_recommendations_applied all populated.
  3. Negative test: mutate the synthetic eval to drop the Site declaration
     while keeping a scope=site measurement, assert the emitter raises a
     QdsCompletenessError with a clear message.

Exits non-zero on the first failure; prints PASS for each test that passes.
Wired into scripts/validate.sh.
"""
from __future__ import annotations

import copy
import sys
import tempfile
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

import qds_emit  # noqa: E402


EVAL_1SAR = REPO / "data/coscientists/openscientist/EVAL_1sar_cdba2c07_2026-04-24.yaml"
EVAL_SYNTH = REPO / "data/examples/eval/EVAL_synth_active_site_2026-04-26.yaml"
EVAL_QUALITY = REPO / "data/examples/eval/EVAL_synth_quality_indicators_2026-05-04.yaml"

EXPECTED_GEOMETRY_SLOTS_1SAR = {
    "clashscore",
    "ramachandran_outliers_pct",
    "ramachandran_favored_pct",
    "rotamer_outliers_pct",
    "molprobity_score",
    "bond_rmsd_a",
    "angle_rmsd_deg",
}


def _check(condition: bool, msg: str) -> None:
    if not condition:
        print(f"FAIL: {msg}", file=sys.stderr)
        sys.exit(1)


def test_1sar_geometry_slots_all_present() -> None:
    qds = qds_emit.emit_qds(
        [EVAL_1SAR], qds_id="QDS_1sar_test", structure_id="1sar"
    )
    _check("geometry_summary" in qds, "geometry_summary missing from 1SAR QDS")
    geom = qds["geometry_summary"]
    present = set(geom.keys()) - {"id"}
    missing = EXPECTED_GEOMETRY_SLOTS_1SAR - present
    _check(
        not missing,
        f"1SAR geometry_summary missing slots: {sorted(missing)}. "
        f"Codex regression — substring matching dropped these silently.",
    )
    print(f"PASS  test_1sar_geometry_slots_all_present  ({len(present)} slots populated)")


def test_synth_local_blocks_present() -> None:
    qds = qds_emit.emit_qds(
        [EVAL_SYNTH], qds_id="QDS_synth_test", structure_id="synth1"
    )

    _check("per_residue_quality" in qds, "synthetic QDS missing per_residue_quality")
    prq = qds["per_residue_quality"]
    _check(prq.get("outliers"), "per_residue_quality.outliers empty (eval has 2 ResidueOutliers)")
    _check(prq.get("density_peaks"), "per_residue_quality.density_peaks empty (eval has 1 peak)")
    _check(prq.get("lddt_per_residue"), "per_residue_quality.lddt_per_residue empty (eval has 5 values)")

    _check("site_qualities" in qds and qds["site_qualities"], "synthetic QDS missing site_qualities")
    sq = qds["site_qualities"][0]
    _check(sq["site_ref"] == "synth1_active_site", f"site_ref != synth1_active_site, got {sq.get('site_ref')!r}")
    _check("ligand_quality" in sq, "SiteQuality.ligand_quality missing (eval has scope=ligand measurements)")
    lq = sq["ligand_quality"]
    _check("rscc" in lq, "ligand_quality.rscc missing")
    _check("protein_ligand_hbond_count" in lq, "ligand_quality.protein_ligand_hbond_count missing")

    _check("pairwise_comparisons" in qds and qds["pairwise_comparisons"], "synthetic QDS missing pairwise_comparisons")
    pc = qds["pairwise_comparisons"][0]
    _check(pc.get("reference_kind") == "starting_model", f"pairwise reference_kind unexpected: {pc.get('reference_kind')!r}")

    _check(
        "tool_recommendations_applied" in qds and qds["tool_recommendations_applied"],
        "synthetic QDS missing tool_recommendations_applied",
    )

    print("PASS  test_synth_local_blocks_present  (per_residue + sites + ligand + pairwise + tool_recs)")


def test_negative_site_scope_without_site_decl_fails() -> None:
    """Drop the Site declaration but keep a scope=site measurement; expect failure."""
    doc = yaml.safe_load(EVAL_SYNTH.read_text())
    bad = copy.deepcopy(doc)
    # Strip Site declarations and ligands; keep the measurements.
    for r in bad["evaluation_runs"]:
        r["sites"] = []
        r["ligands"] = []

    with tempfile.TemporaryDirectory() as tmpdir:
        bad_path = Path(tmpdir) / "eval_bad_no_sites.yaml"
        bad_path.write_text(yaml.safe_dump(bad, sort_keys=False))

        try:
            qds_emit.emit_qds(
                [bad_path], qds_id="QDS_bad_test", structure_id="synth1"
            )
        except qds_emit.QdsCompletenessError as e:
            msg = str(e)
            _check(
                "scope=site" in msg or "site_qualities" in msg,
                f"emitter raised but message lacks scope-site context: {msg!r}",
            )
            print("PASS  test_negative_site_scope_without_site_decl_fails")
            return
        except SystemExit as e:
            # QdsCompletenessError is a SystemExit subclass — accept either.
            msg = str(e)
            _check(
                "scope=site" in msg or "site_qualities" in msg,
                f"emitter exited but message lacks scope-site context: {msg!r}",
            )
            print("PASS  test_negative_site_scope_without_site_decl_fails")
            return
    _check(False, "emit_qds did not fail when site-scope measurement had no Site declared")


def test_quality_indicator_extensions_present() -> None:
    qds = qds_emit.emit_qds(
        [EVAL_QUALITY], qds_id="QDS_quality_test", structure_id="synth_quality"
    )

    geom = qds.get("geometry_summary") or {}
    _check("ramachandran_z_score" in geom, "Rama-Z missing from geometry_summary")
    _check("packing_z_score" in geom, "packing Z missing from geometry_summary")
    _check("unsatisfied_buried_hbond_count" in geom, "buried H-bond count missing from geometry_summary")

    packing = qds.get("packing_summary") or {}
    _check("packing_z_score" in packing, "packing_summary.packing_z_score missing")
    _check("unsatisfied_buried_hbond_count" in packing, "packing_summary.unsatisfied_buried_hbond_count missing")

    refn = qds.get("refinement_summary") or {}
    _check("diffraction_precision_index" in refn, "DPI missing from refinement_summary")

    mp = qds.get("map_summary") or {}
    _check("directional_resolution_anisotropy" in mp, "3DFSC anisotropy missing from map_summary")
    _check("local_model_map_fsc_q" in mp, "local FSC-Q missing from map_summary")
    _check("rscc_outlier_fraction" in mp, "RSCC outlier fraction missing from map_summary")

    pred = qds.get("predicted_confidence_summary") or {}
    _check("predicted_tm_score" in pred, "pTM missing from predicted_confidence_summary")
    _check("interface_predicted_tm_score" in pred, "ipTM missing from predicted_confidence_summary")
    _check("prediction_ensemble_convergence" in pred, "prediction convergence missing from predicted_confidence_summary")

    prq = qds.get("per_residue_quality") or {}
    _check(prq.get("rscc_per_residue"), "rscc_per_residue array missing")
    _check(prq.get("b_factor_z_per_residue"), "b_factor_z_per_residue array missing")
    _check(prq.get("secondary_structure_per_residue"), "secondary_structure_per_residue array missing")
    _check(prq.get("fsc_q_per_residue"), "fsc_q_per_residue array missing")

    cls = qds.get("classification_summary") or {}
    _check(cls.get("secondary_structure_assignments"), "secondary_structure_assignments missing")
    _check(cls.get("domain_assignments"), "domain_assignments missing")
    _check("fold_classification" in cls, "fold_classification missing")

    iface = qds.get("interface_quality_summary") or {}
    _check(iface.get("interface_qualities"), "interface_qualities missing")
    _check("interface_buried_surface_area" in iface, "interface BSA missing")
    _check("interface_dockq_score" in iface, "DockQ score missing")
    _check("capri_interface_quality_class" in iface, "CAPRI class missing")

    pens = qds.get("prediction_ensemble_summary") or {}
    _check(pens.get("prediction_ensemble_qualities"), "prediction ensemble rows missing")
    _check("prediction_ensemble_convergence" in pens, "prediction ensemble convergence missing")

    nmr = qds.get("nmr_validation_summary") or {}
    _check(nmr.get("nmr_ensemble_qualities"), "NMR ensemble rows missing")
    _check("nmr_restraint_violation_summary" in nmr, "NMR restraint summary missing")
    _check("nmr_ensemble_precision_rmsd" in nmr, "NMR precision RMSD missing")

    print("PASS  test_quality_indicator_extensions_present  (new scalar + structured blocks)")


def test_negative_structured_scopes_without_rows_fail() -> None:
    doc = yaml.safe_load(EVAL_QUALITY.read_text())
    bad = copy.deepcopy(doc)
    for r in bad["evaluation_runs"]:
        r["domain_assignments"] = []
        r["interface_qualities"] = []
        r["prediction_ensemble_qualities"] = []
        r["nmr_ensemble_qualities"] = []

    with tempfile.TemporaryDirectory() as tmpdir:
        bad_path = Path(tmpdir) / "eval_bad_no_structured_scopes.yaml"
        bad_path.write_text(yaml.safe_dump(bad, sort_keys=False))

        try:
            qds_emit.emit_qds(
                [bad_path], qds_id="QDS_bad_structured_test", structure_id="synth_quality"
            )
        except qds_emit.QdsCompletenessError as e:
            msg = str(e)
            _check("scope=domain" in msg, f"missing domain-scope error context: {msg!r}")
            _check("scope=interface" in msg, f"missing interface-scope error context: {msg!r}")
            _check("scope=ensemble" in msg, f"missing ensemble-scope error context: {msg!r}")
            print("PASS  test_negative_structured_scopes_without_rows_fail")
            return
        except SystemExit as e:
            msg = str(e)
            _check("scope=domain" in msg, f"missing domain-scope error context: {msg!r}")
            _check("scope=interface" in msg, f"missing interface-scope error context: {msg!r}")
            _check("scope=ensemble" in msg, f"missing ensemble-scope error context: {msg!r}")
            print("PASS  test_negative_structured_scopes_without_rows_fail")
            return
    _check(False, "emit_qds did not fail when structured-scope rows were missing")


def main() -> int:
    test_1sar_geometry_slots_all_present()
    test_synth_local_blocks_present()
    test_negative_site_scope_without_site_decl_fails()
    test_quality_indicator_extensions_present()
    test_negative_structured_scopes_without_rows_fail()
    print("\nall qds_emit regression tests passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
