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


# A residue is keyed on (chain, resnum, insertion-code) so that e.g. 10 and 10A
# are never conflated. Residue *name* is deliberately not part of the key: DSSP
# reports a one-letter code and biotite a three-letter name, so cross-checking
# names across the two formats is fragile; chain+num+icode uniquely locates the
# residue within one model, which is what the alignment needs.
ResKey = tuple[str, str, str]


def run_dssp(model: Path) -> dict[ResKey, str]:
    """Return {(chain, resnum, icode): HEC} from DSSP. Requires `mkdssp` on PATH."""
    exe = shutil.which("mkdssp")
    if exe is None:
        _fail("mkdssp not found on PATH — install DSSP (e.g. `brew install brewsci/bio/dssp`).")
    with tempfile.NamedTemporaryFile(suffix=".dssp", delete=False) as tmp:
        out_path = Path(tmp.name)
    normalised = _normalise_for_dssp(model)
    try:
        proc = subprocess.run(
            [exe, "--output-format", "dssp", str(normalised), str(out_path)],
            capture_output=True, text=True,
        )
        if proc.returncode != 0 and not out_path.stat().st_size:
            _fail(f"mkdssp failed: {proc.stderr.strip() or proc.stdout.strip()}")
        return _parse_dssp(out_path.read_text())
    finally:
        out_path.unlink(missing_ok=True)
        if normalised != model:
            normalised.unlink(missing_ok=True)


def _normalise_for_dssp(model: Path) -> Path:
    """Rewrite the model through `gemmi convert` so mkdssp will read it.

    mkdssp 4.x sniffs the input format and gets it wrong on PDB files downloaded
    from RCSB — it tries to parse them as mmCIF and dies with "This file does not
    seem to be an mmCIF file", followed by a cif-validator error naming a category
    from the entry's own header. It is not specific to one entry: 1UBQ, 12LO and
    every other RCSB `.pdb` tested fails, while the same coordinates rewritten by
    `gemmi convert` are accepted. This script previously only ever ran on a
    PHENIX-written file in `data/`, which is why the failure went unnoticed.

    Falls back to the original path when gemmi is unavailable, so the failure mode
    is mkdssp's own error rather than a missing-tool error from here.
    """
    if shutil.which("gemmi") is None:
        return model
    with tempfile.NamedTemporaryFile(suffix=".pdb", delete=False) as tmp:
        converted = Path(tmp.name)
    proc = subprocess.run(["gemmi", "convert", str(model), str(converted)],
                          capture_output=True, text=True)
    if proc.returncode != 0 or not converted.stat().st_size:
        converted.unlink(missing_ok=True)
        return model
    return converted


def _parse_dssp(text: str) -> dict[ResKey, str]:
    """Parse the legacy DSSP residue table (fixed-width columns)."""
    lines = text.splitlines()
    start = next(
        (i + 1 for i, ln in enumerate(lines) if ln.lstrip().startswith("#  RESIDUE")),
        None,
    )
    if start is None:
        _fail("could not locate the DSSP residue table header.")
    out: dict[ResKey, str] = {}
    for ln in lines[start:]:
        if len(ln) < 17 or ln[13] == "!":  # chain-break marker
            continue
        resnum = ln[5:10].strip()
        icode = ln[10].strip()  # insertion code column
        chain = ln[11].strip()
        if not resnum or not chain:
            continue
        ss = ln[16]
        out[(chain, resnum, icode)] = _DSSP_TO_HEC.get(ss, "C")
    return out


def run_biotite(model: Path) -> dict[ResKey, str]:
    """Return {(chain, resnum, icode): HEC} from biotite annotate_sse (per chain)."""
    try:
        import biotite.structure as struc
        import biotite.structure.io.pdb as pdb
    except ImportError:
        _fail("biotite not importable — install it (`pip install biotite`).")
    pdb_file = pdb.PDBFile.read(str(model))
    arr = pdb.get_structure(pdb_file, model=1)
    prot = arr[struc.filter_amino_acids(arr)]
    has_icode = "ins_code" in prot.get_annotation_categories()
    out: dict[ResKey, str] = {}
    for chain_id in sorted(set(prot.chain_id)):
        chain = prot[prot.chain_id == chain_id]
        sse = struc.annotate_sse(chain)  # one 'a'/'b'/'c' per residue, in order
        starts = struc.get_residue_starts(chain)  # first-atom index per residue, in order
        if len(sse) != len(starts):
            continue  # assignment/residue mismatch on this chain; skip rather than misalign
        for idx, code in zip(starts, sse):
            resnum = str(chain.res_id[idx])
            icode = str(chain.ins_code[idx]).strip() if has_icode else ""
            out[(chain_id, resnum, icode)] = _BIOTITE_TO_HEC.get(code, "C")
    return out


def agreement(a: dict[ResKey, str], b: dict[ResKey, str]) -> dict[str, Any]:
    """Three-state agreement fraction over residues both assigners scored."""
    shared = sorted(set(a) & set(b))
    if not shared:
        _fail("no residues in common between the two assigners — cannot compute agreement.")
    matches = sum(1 for k in shared if a[k] == b[k])
    per_residue = [
        {"chain": c, "resnum": r, "icode": i, "dssp": a[k], "biotite": b[k], "agree": a[k] == b[k]}
        for k in shared
        for (c, r, i) in [k]
    ]
    return {
        "n_dssp": len(a),
        "n_biotite": len(b),
        "n_scored": len(shared),
        "n_dropped": len(set(a) ^ set(b)),  # residues assigned by only one tool
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
        "oracle_tool_ref": "DSSP + biotite P-SEA",
        "oracle_family": "non_cctbx",
        "oracle_measure": {"value_numeric": result["fraction"]},
        "pass_status": "informational",
        "notes": (
            f"three-state (H/E/C) agreement between two independent non-cctbx assigners, "
            f"DSSP (H-bond) and biotite P-SEA (Cα geometry): "
            f"{result['n_agree']}/{result['n_scored']} concordant over residues scored by both "
            f"(DSSP {result['n_dssp']}, biotite {result['n_biotite']}, "
            f"{result['n_dropped']} scored by only one and excluded)."
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
        print("# chain resnum icode dssp biotite agree")
        for r in result["per_residue"]:
            print(f"#  {r['chain']:>2} {r['resnum']:>5} {r['icode'] or '-':>1} "
                  f"{r['dssp']}   {r['biotite']}    {r['agree']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
