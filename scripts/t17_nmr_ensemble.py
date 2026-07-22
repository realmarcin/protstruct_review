#!/usr/bin/env python3
"""Compute the T17 NMR ensemble precision metric from a multi-model PDB.

The gradeable T17 metric (T17_nmr_ensemble_precision_rmsd) is how tightly the
deposited NMR models agree: the mean per-residue Cα fluctuation (RMSF) about the
ensemble mean, after superposing every model onto the first. This is computed
locally from the ensemble alone — no restraints or wwPDB report needed — via
biotite (non-cctbx, non-PHENIX). T17 is oracle-only; there is no PHENIX NMR
validator, so this is a genuine independent measurement.

The second T17 metric, T17_nmr_restraint_violation_summary (informational),
needs the deposited restraints + the wwPDB NMR validation report and is NOT
produced here — it remains future work (issue #3).

Emits one pasteable EvaluationMeasurement row:
  - T17_nmr_ensemble_precision_rmsd (value_numeric, Å)

Degrades loudly: if biotite is unavailable or the input is not a multi-model
ensemble, exits non-zero rather than fabricating a value.

Usage:
    python3 scripts/t17_nmr_ensemble.py data/pdb_mtz/1d3z.pdb --eval-id EVAL_...
"""
from __future__ import annotations

import argparse
import sys
import warnings
from pathlib import Path
from typing import Any

import yaml

REPO = Path(__file__).resolve().parent.parent


def _fail(msg: str) -> None:
    """Exit non-zero with a clear oracle-status message (never a fabricated value)."""
    raise SystemExit(f"t17_nmr_ensemble: {msg}")


def mean_precision(rmsf: list[float]) -> float:
    """Mean per-residue RMSF = the scalar ensemble-precision figure."""
    if not rmsf:
        _fail("no per-residue RMSF values — cannot compute precision.")
    return round(sum(rmsf) / len(rmsf), 3)


def run_precision(model: Path) -> dict[str, Any]:
    """Ensemble precision from a multi-model PDB via biotite superpose + RMSF."""
    try:
        import numpy as np
        import biotite.structure as struc
        import biotite.structure.io.pdb as pdb
    except ImportError:
        _fail("biotite not importable — install it (`pip install biotite`).")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        stack = pdb.get_structure(pdb.PDBFile.read(str(model)))
        if stack.shape[0] < 2:
            _fail(f"input has {stack.shape[0]} model(s); an NMR ensemble needs ≥ 2.")
        ca = stack[:, struc.filter_amino_acids(stack) & (stack.atom_name == "CA")]
        if ca.shape[1] == 0:
            _fail("no Cα atoms found — is this a protein ensemble?")
        superposed, _ = struc.superimpose(ca[0], ca)          # onto model 1
        rmsf = struc.rmsf(struc.average(superposed), superposed)
        vals = [float(v) for v in rmsf if not np.isnan(v)]
    return {
        "mean_rmsf": mean_precision(vals),
        "min_rmsf": round(min(vals), 3),
        "max_rmsf": round(max(vals), 3),
        "n_models": int(ca.shape[0]),
        "n_ca": len(vals),
    }


def render_yaml(result: dict[str, Any], eval_id: str, model: Path) -> str:
    """Emit the T17 ensemble-precision measurement row."""
    row = {
        "id": f"{eval_id}_M_T17_precision",
        "catalog_task_ref": "T17",
        "stage": "final",
        "scope": "ensemble",
        "scope_selector": model.stem,
        "metric_definition_ref": "T17_nmr_ensemble_precision_rmsd",
        "oracle_tool_ref": "biotite ensemble",
        "oracle_family": "non_cctbx",
        "oracle_measure": {"value_numeric": result["mean_rmsf"], "unit": "Å"},
        "pass_status": "informational",
        "notes": (
            f"mean per-residue Cα RMSF about the ensemble mean over {result['n_models']} models "
            f"({result['n_ca']} residues; range {result['min_rmsf']}–{result['max_rmsf']} Å, "
            f"flexible termini/loops raise the max)."
        ),
    }
    return yaml.safe_dump([row], sort_keys=False, allow_unicode=True, width=100)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("model", type=Path, help="multi-model NMR ensemble (PDB)")
    ap.add_argument("--eval-id", default="EVAL_T17", help="eval id prefix for the emitted row")
    args = ap.parse_args(argv)

    if not args.model.exists():
        _fail(f"file not found: {args.model}")
    print(render_yaml(run_precision(args.model), args.eval_id, args.model), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
