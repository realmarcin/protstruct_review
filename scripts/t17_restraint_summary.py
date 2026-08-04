#!/usr/bin/env python3
"""Summarise NMR restraint violations from a wwPDB validation report.

The second T17 metric (T17_nmr_restraint_violation_summary, informational) reports
how well the deposited NMR ensemble satisfies its experimental restraints. The
wwPDB validation report is the deposition-grade source (the T17 catalog oracle),
so this reads that report rather than re-deriving violations from raw restraint
files (whose formats are heterogeneous). Non-PHENIX, non-cctbx.

Not every report carries restraint data: older entries (e.g. 1D3Z, 1998) predate
restraint-violation validation and their reports have none — this tool exits
loudly in that case rather than emitting an empty summary. A modern entry with
deposited restraints (e.g. 2N54) has the full section.

Emits one pasteable EvaluationMeasurement row:
  - T17_nmr_restraint_violation_summary (value_text, informational)

Usage:
    python3 scripts/t17_restraint_summary.py data/pdb_mtz/2n54_validation.xml.gz --eval-id EVAL_...
"""
from __future__ import annotations

import argparse
import gzip
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import yaml

REPO = Path(__file__).resolve().parent.parent


def _fail(msg: str) -> None:
    """Exit non-zero with a clear oracle-status message (never a fabricated value)."""
    raise SystemExit(f"t17_restraint_summary: {msg}")


def load_report(path: Path) -> ET.Element:
    """Parse a wwPDB validation report (.xml or .xml.gz) into its root element."""
    data = gzip.decompress(path.read_bytes()) if path.suffix == ".gz" else path.read_bytes()
    try:
        return ET.fromstring(data)
    except ET.ParseError as e:
        _fail(f"could not parse validation report {path}: {e}")


def _required_float(el: ET.Element, attr: str, tag: str) -> float:
    """Read a numeric attribute that must be present; fail rather than default it."""
    raw = el.attrib.get(attr)
    if raw is None:
        _fail(f"<{tag}> carries no {attr!r} attribute (found: "
              f"{sorted(el.attrib)}) — this report's schema is not the one this "
              f"tool parses; refusing to report a fabricated 0.0.")
    try:
        return float(raw)
    except ValueError:
        _fail(f"<{tag}> {attr}={raw!r} is not a number.")


def summarize(root: ET.Element) -> dict[str, Any]:
    """Extract the restraint-violation headline from a parsed report.

    Fails loudly when the report carries no restraint data (older entries).
    """
    summary = {
        el.attrib.get("description", ""): el.attrib.get("value", "")
        for el in root.iter("restraint_summary")
    }
    if not summary:
        _fail("this validation report has no restraint data — use a modern NMR entry "
              "with deposited restraints (e.g. 2N54); older entries (1D3Z) predate it.")

    # No numeric defaults here. `.get(attr, 0.0)` turned a report whose schema names
    # these attributes differently into a summary reading "0.0 in 0.1-0.2 Å; 0.0 in
    # 0.2-0.5 Å; 0.0 in >0.5 Å" -- a fabricated value, not a missing one, and
    # fabricated in the flattering direction, since zero violations is the best
    # possible answer (#122). A missing attribute is a parse failure.
    bins = [
        {"band": b.attrib.get("bins", ""),
         "per_model": _required_float(b, "violations_per_model", "residual_distance_violation")}
        for b in root.iter("residual_distance_violation")
    ]
    per_model = [
        _required_float(m, "mean_violation", "distance_violations_in_model")
        for m in root.iter("distance_violations_in_model")
    ]
    mean_viol = round(sum(per_model) / len(per_model), 3) if per_model else None
    return {"summary": summary, "bins": bins, "mean_distance_violation": mean_viol}


def _headline(result: dict[str, Any]) -> str:
    s = result["summary"]
    dist = s.get("Total distance restraints", "?")
    lr = s.get("Long range (|i-j|>=5)", "?")
    dih = s.get("Total dihedral-angle restraints", "?")
    band_txt = "; ".join(f"{b['per_model']} in {b['band']} Å" for b in result["bins"]) or "none reported"
    mean_txt = f"mean per-model {result['mean_distance_violation']} Å" if result["mean_distance_violation"] is not None else ""
    return (f"{dist} distance restraints ({lr} long-range), {dih} dihedral; "
            f"distance violations per model: {band_txt}"
            + (f"; {mean_txt}" if mean_txt else "") + ".")


def render_yaml(result: dict[str, Any], eval_id: str, structure_id: str) -> str:
    """Emit the T17 restraint-violation-summary measurement row."""
    row = {
        "id": f"{eval_id}_M_T17_restraints",
        "catalog_task_ref": "T17",
        "stage": "final",
        "scope": "ensemble",
        "scope_selector": structure_id,
        "metric_definition_ref": "T17_nmr_restraint_violation_summary",
        "oracle_tool_ref": "wwPDB NMR validation",
        "oracle_family": "non_cctbx",
        "oracle_measure": {"value_text": _headline(result)},
        "pass_status": "informational",
        "notes": "parsed from the deposited wwPDB validation report restraint-analysis section.",
    }
    return yaml.safe_dump([row], sort_keys=False, allow_unicode=True, width=100)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("report", type=Path, help="wwPDB validation report (.xml or .xml.gz)")
    ap.add_argument("--eval-id", default="EVAL_T17", help="eval id prefix for the emitted row")
    ap.add_argument("--structure-id", default=None, help="structure id for scope_selector")
    args = ap.parse_args(argv)

    if not args.report.exists():
        _fail(f"file not found: {args.report}")
    sid = args.structure_id or args.report.stem.split("_")[0]
    result = summarize(load_report(args.report))
    print(render_yaml(result, args.eval_id, sid), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
