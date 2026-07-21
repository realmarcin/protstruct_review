#!/usr/bin/env python3
"""Compute the T15 secondary-structure agreement metric from two independent assigners.

The gradeable T15 metric (`T15_secondary_structure_agreement`) is the fraction of
residues that two *independent* secondary-structure assigners place in the same
three-state class (H / E / C). Grading agreement rather than a single label is the
trust model applied to categorical data — see CODING_STANDARDS.md rule 9.

Assigner A: **DSSP** (`mkdssp`) — Kabsch & Sander H-bond energetics.
Assigner B: **biotite** `annotate_sse` — Labesse P-SEA, a Cα-geometry method.

The two are genuinely different algorithm families (H-bond vs Cα geometry), so
agreement is informative rather than tautological, and both are non-cctbx —
satisfying the trust model without either being PHENIX.

Emits a pasteable EvaluationMeasurement-shaped YAML row (the scalar agreement
metric) plus per-residue three-state labels.

Degrades loudly: if `mkdssp` is not on PATH, or biotite is not importable, exits
non-zero with a clear message rather than fabricating a number.

Usage:
    python3 scripts/t15_ss_agreement.py data/pdb_mtz/1sar.pdb --eval-id EVAL_1sar_...
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import yaml

REPO = Path(__file__).resolve().parent.parent

# Three-state collapse. DSSP 8-state -> HEC; biotite a/b/c -> HEC.
_DSSP_TO_HEC = {"H": "H", "G": "H", "I": "H", "E": "E", "B": "E"}  # else -> C
_BIOTITE_TO_HEC = {"a": "H", "b": "E", "c": "C"}


def _fail(msg: str) -> None:
    """Exit non-zero with a clear oracle-status message (never a fabricated value)."""
    raise SystemExit(f"t15_ss_agreement: {msg}")


def run_dssp(model: Path) -> dict[tuple[str, str], str]:
    """Return {(chain, resnum): HEC} from DSSP. Requires `mkdssp` on PATH."""
    exe = shutil.which("mkdssp")
    if exe is None:
        _fail("mkdssp not found on PATH — install DSSP (e.g. `brew install brewsci/bio/dssp`).")
    with tempfile.NamedTemporaryFile(suffix=".dssp", delete=False) as tmp:
        out_path = Path(tmp.name)
    try:
        proc = subprocess.run(
            [exe, "--output-format", "dssp", str(model), str(out_path)],
            capture_output=True, text=True,
        )
        if proc.returncode != 0 and not out_path.stat().st_size:
            _fail(f"mkdssp failed: {proc.stderr.strip() or proc.stdout.strip()}")
        return _parse_dssp(out_path.read_text())
    finally:
        out_path.unlink(missing_ok=True)


def _parse_dssp(text: str) -> dict[tuple[str, str], str]:
    """Parse the legacy DSSP residue table (fixed-width columns)."""
    lines = text.splitlines()
    start = next(
        (i + 1 for i, ln in enumerate(lines) if ln.lstrip().startswith("#  RESIDUE")),
        None,
    )
    if start is None:
        _fail("could not locate the DSSP residue table header.")
    out: dict[tuple[str, str], str] = {}
    for ln in lines[start:]:
        if len(ln) < 17 or ln[13] == "!":  # chain-break marker
            continue
        resnum = ln[5:10].strip()
        chain = ln[11].strip()
        if not resnum or not chain:
            continue
        ss = ln[16]
        out[(chain, resnum)] = _DSSP_TO_HEC.get(ss, "C")
    return out


def run_biotite(model: Path) -> dict[tuple[str, str], str]:
    """Return {(chain, resnum): HEC} from biotite annotate_sse (per chain)."""
    try:
        import biotite.structure as struc
        import biotite.structure.io.pdb as pdb
    except ImportError:
        _fail("biotite not importable — install it (`pip install biotite`).")
    pdb_file = pdb.PDBFile.read(str(model))
    arr = pdb.get_structure(pdb_file, model=1)
    prot = arr[struc.filter_amino_acids(arr)]
    out: dict[tuple[str, str], str] = {}
    for chain_id in sorted(set(prot.chain_id)):
        chain = prot[prot.chain_id == chain_id]
        sse = struc.annotate_sse(chain)  # one 'a'/'b'/'c' per residue, in order
        res_ids = struc.get_residues(chain)[0]
        if len(sse) != len(res_ids):
            continue  # assignment/residue mismatch on this chain; skip rather than misalign
        for res_id, code in zip(res_ids, sse):
            out[(chain_id, str(res_id))] = _BIOTITE_TO_HEC.get(code, "C")
    return out


def agreement(a: dict[tuple[str, str], str], b: dict[tuple[str, str], str]) -> dict[str, Any]:
    """Three-state agreement fraction over residues both assigners scored."""
    shared = sorted(set(a) & set(b))
    if not shared:
        _fail("no residues in common between the two assigners — cannot compute agreement.")
    matches = sum(1 for k in shared if a[k] == b[k])
    per_residue = [
        {"chain": c, "resnum": r, "dssp": a[(c, r)], "biotite": b[(c, r)],
         "agree": a[(c, r)] == b[(c, r)]}
        for (c, r) in shared
    ]
    return {
        "n_scored": len(shared),
        "n_agree": matches,
        "fraction": round(matches / len(shared), 4),
        "per_residue": per_residue,
    }


def render_yaml(result: dict[str, Any], eval_id: str, model: Path) -> str:
    """Emit a pasteable EvaluationMeasurement row for T15_secondary_structure_agreement."""
    measurement = {
        "id": f"{eval_id}_M_T15_ss_agreement",
        "catalog_task_ref": "T15",
        "stage": "final",
        "scope": "complex",
        "scope_selector": model.stem,
        "metric_definition_ref": "T15_secondary_structure_agreement",
        "oracle_tool_ref": "DSSP",
        "oracle_family": "non_cctbx",
        "oracle_measure": {"value_numeric": result["fraction"]},
        "pass_status": "informational",
        "notes": (
            f"three-state (H/E/C) DSSP vs biotite P-SEA agreement over "
            f"{result['n_scored']} residues scored by both "
            f"({result['n_agree']} concordant); independent non-cctbx assigners."
        ),
    }
    return yaml.safe_dump([measurement], sort_keys=False, allow_unicode=True, width=100)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("model", type=Path, help="protein model (PDB)")
    ap.add_argument("--eval-id", default="EVAL_T15", help="eval id prefix for the emitted row")
    ap.add_argument("--per-residue", action="store_true", help="also print the per-residue table")
    args = ap.parse_args(argv)

    if not args.model.exists():
        _fail(f"model not found: {args.model}")

    dssp = run_dssp(args.model)
    bio = run_biotite(args.model)
    result = agreement(dssp, bio)

    print(render_yaml(result, args.eval_id, args.model))
    if args.per_residue:
        print("# chain resnum dssp biotite agree")
        for r in result["per_residue"]:
            print(f"#  {r['chain']:>2} {r['resnum']:>5} {r['dssp']}   {r['biotite']}    {r['agree']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
