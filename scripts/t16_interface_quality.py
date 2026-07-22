#!/usr/bin/env python3
"""Compute the T16 interface-quality metrics with DockQ.

Runs DockQ (Basu & Wallner 2016) on a model complex against a native/reference
complex and reports the DockQ score plus its CAPRI quality class. DockQ is
non-cctbx and non-PHENIX; the deposited biological assembly is the reference,
which is the trust model's tiebreaker for T16 (there is no PHENIX interface
scorer, so this is oracle-only).

Emits two pasteable EvaluationMeasurement rows:
  - T16_interface_dockq_score        (value_numeric = DockQ, the gradeable metric)
  - T16_capri_interface_quality_class (value_text = High/Medium/Acceptable/Incorrect,
                                       informational — derived from the score)

Buried surface area (T16_interface_buried_surface_area) is NOT produced here; it
needs PISA/PDBePISA or a SASA calculator and remains future work (issue #3).

Degrades loudly: if the `DockQ` CLI is not on PATH, exits non-zero with a clear
message rather than fabricating a score.

Usage:
    python3 scripts/t16_interface_quality.py model.pdb native.pdb --eval-id EVAL_...
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import yaml

REPO = Path(__file__).resolve().parent.parent

# CAPRI quality classes by DockQ score. Basu & Wallner, "DockQ: A Quality Measure
# for Protein-Protein Docking Models", PLOS ONE 2016; 11(8):e0161879.
# High >= 0.80; Medium [0.49, 0.80); Acceptable [0.23, 0.49); Incorrect < 0.23.
_CAPRI_BANDS = ((0.80, "High"), (0.49, "Medium"), (0.23, "Acceptable"))


def _fail(msg: str) -> None:
    """Exit non-zero with a clear oracle-status message (never a fabricated value)."""
    raise SystemExit(f"t16_interface_quality: {msg}")


def capri_class(dockq: float) -> str:
    """Map a DockQ score to its CAPRI quality class."""
    for threshold, label in _CAPRI_BANDS:
        if dockq >= threshold:
            return label
    return "Incorrect"


def run_dockq(model: Path, native: Path, mapping: str | None = None) -> dict[str, Any]:
    """Run DockQ(model, native) and return the parsed JSON. Requires DockQ on PATH."""
    exe = shutil.which("DockQ")
    if exe is None:
        _fail("DockQ not found on PATH — install it (`pip install DockQ`).")
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        json_path = Path(tmp.name)
    try:
        cmd = [exe, "--json", str(json_path), str(model), str(native)]
        if mapping:
            cmd += ["--mapping", mapping]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if not json_path.stat().st_size:
            _fail(f"DockQ produced no output: {proc.stderr.strip() or proc.stdout.strip()}")
        return json.loads(json_path.read_text())
    finally:
        json_path.unlink(missing_ok=True)


def extract(result: dict[str, Any]) -> dict[str, Any]:
    """Pull the global DockQ score and per-interface breakdown from DockQ JSON."""
    dockq = result.get("GlobalDockQ", result.get("best_dockq"))
    if dockq is None:
        _fail("DockQ JSON has no GlobalDockQ/best_dockq field — cannot score.")
    interfaces = {
        name: {
            "dockq": round(iface.get("DockQ", 0.0), 4),
            "irmsd": round(iface.get("iRMSD", 0.0), 3),
            "lrmsd": round(iface.get("LRMSD", 0.0), 3),
            "fnat": round(iface.get("fnat", 0.0), 4),
        }
        for name, iface in (result.get("best_result") or {}).items()
    }
    return {
        "dockq": round(float(dockq), 4),
        "capri": capri_class(float(dockq)),
        "mapping": result.get("best_mapping_str", ""),
        "interfaces": interfaces,
    }


def render_yaml(summary: dict[str, Any], eval_id: str, model: Path) -> str:
    """Emit the two T16 measurement rows (numeric score + informational class)."""
    n_iface = len(summary["interfaces"])
    score_row = {
        "id": f"{eval_id}_M_T16_dockq",
        "catalog_task_ref": "T16",
        "stage": "final",
        "scope": "interface",
        "scope_selector": summary["mapping"] or model.stem,
        "metric_definition_ref": "T16_interface_dockq_score",
        "oracle_tool_ref": "DockQ",
        "oracle_family": "non_cctbx",
        "oracle_measure": {"value_numeric": summary["dockq"]},
        "pass_status": "informational",
        "notes": f"DockQ vs reference over {n_iface} interface(s), mapping {summary['mapping']}.",
    }
    class_row = {
        "id": f"{eval_id}_M_T16_capri",
        "catalog_task_ref": "T16",
        "stage": "final",
        "scope": "interface",
        "scope_selector": summary["mapping"] or model.stem,
        "metric_definition_ref": "T16_capri_interface_quality_class",
        "oracle_tool_ref": "DockQ",
        "oracle_family": "non_cctbx",
        "oracle_measure": {"value_text": summary["capri"]},
        "pass_status": "informational",
        "notes": "CAPRI class derived from DockQ score (Basu & Wallner 2016 bands).",
    }
    return yaml.safe_dump([score_row, class_row], sort_keys=False, allow_unicode=True, width=100)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("model", type=Path, help="model complex (PDB/mmCIF)")
    ap.add_argument("native", type=Path, help="native / deposited reference complex")
    ap.add_argument("--eval-id", default="EVAL_T16", help="eval id prefix for emitted rows")
    ap.add_argument("--mapping", default=None, help="DockQ chain map MODELCHAINS:NATIVECHAINS")
    args = ap.parse_args(argv)

    for p in (args.model, args.native):
        if not p.exists():
            _fail(f"file not found: {p}")

    result = run_dockq(args.model, args.native, args.mapping)
    summary = extract(result)
    print(render_yaml(summary, args.eval_id, args.model))
    return 0


if __name__ == "__main__":
    sys.exit(main())
