#!/usr/bin/env python3
"""Decompose geometry-RMSD disagreement into restraint library vs implementation.

PR #28 measured bond-length RMSD **across** libraries (PHENIX/CDL vs gemmi/CCP4
monomer library) and attributed the gap to the library, by analogy with the
bond-angle finding. It never separated the two causes, and left the matched-library
floor unmeasured. This does both, by toggling PHENIX's own restraint library:

  A. `phenix.model_statistics ... restraints_library.cdl=True`   — CDL (PHENIX default)
  B. `phenix.model_statistics ... restraints_library.cdl=False`  — Engh & Huber
  C. `gemmi rmsz`                                                — CCP4 monomer library

  A vs B  = **pure library effect**, one implementation, same code path.
  B vs C  = **near-matched-library floor**: Engh & Huber against the CCP4 monomer
            library, which is E&H-derived, so what remains is mostly implementation.
  A vs C  = the cross-library figure PR #28 published.

"Near-matched" is doing real work in B vs C: the CCP4 monomer library is E&H-derived
but not identical to PHENIX's non-CDL targets, and the two tools may restrain
different populations. B vs C is therefore an **upper bound** on the matched-library
floor, not the floor itself — which is the useful direction for a tolerance.

Usage:
    python3 scripts/bench_t05_restraint_library.py 1ABC 2DEF --cache DIR --json out.json
    python3 scripts/bench_t05_restraint_library.py --ids-file ids.json --cache DIR
"""
from __future__ import annotations

import argparse
import json
import os
import re
import statistics
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

RCSB_PDB = "https://files.rcsb.org/download/{pdb_id}.pdb"
MODEL_STATISTICS = str(Path.home() / "phenix-2.0-5936" / "phenix_bin" / "phenix.model_statistics")
CCP4_SETUP = "/Applications/ccp4-9.0.015-shelx-arpwarp-macosarm/ccp4-9/bin/ccp4.setup-sh"

_PHENIX_BOND = re.compile(r"covalent geometry\s*:\s*bond\s+([\d.]+)\s*\(\s*(\d+)\)")
_PHENIX_ANGLE = re.compile(r"covalent geometry\s*:\s*angle\s+([\d.]+)\s*\(\s*(\d+)\)")
_GEMMI_RMSD = re.compile(r"Model rmsD:\s*bond:\s*([\d.]+),\s*angle:\s*([\d.]+)")


def fetch(pdb_id: str, cache: Path) -> Path | None:
    """Download the deposited PDB-format coordinates; None if unavailable."""
    dest = cache / f"{pdb_id.lower()}.pdb"
    if dest.exists() and dest.stat().st_size:
        return dest
    cache.mkdir(parents=True, exist_ok=True)
    try:
        with urllib.request.urlopen(RCSB_PDB.format(pdb_id=pdb_id.upper()), timeout=180) as r:
            dest.write_bytes(r.read())
    except urllib.error.HTTPError:
        return None
    return dest


def run_phenix(model: Path, work: Path, cdl: bool) -> dict[str, Any] | None:
    """Bond and angle RMSD from PHENIX with CDL on or off."""
    tag = "cdl" if cdl else "eh"
    log = work / f"ms_{tag}_{model.stem}.log"
    if not log.exists() or not _PHENIX_BOND.search(log.read_text(errors="ignore")):
        subprocess.run(
            ["bash", "-c",
             f"cd {work} && {MODEL_STATISTICS} {model} "
             f"pdb_interpretation.restraints_library.cdl={cdl} > {log} 2>&1"],
            capture_output=True, text=True, timeout=3600, env=dict(os.environ))
    if not log.exists():
        return None
    text = log.read_text(errors="ignore")
    bond, angle = _PHENIX_BOND.search(text), _PHENIX_ANGLE.search(text)
    if not bond or not angle:
        return None
    return {"bond": float(bond.group(1)), "n_bond": int(bond.group(2)),
            "angle": float(angle.group(1)), "n_angle": int(angle.group(2))}


def run_gemmi(model: Path, work: Path) -> dict[str, Any] | None:
    """Bond and angle rmsD from gemmi against the CCP4 monomer library."""
    log = work / f"rmsz_{model.stem}.log"
    if not log.exists() or not _GEMMI_RMSD.search(log.read_text(errors="ignore")):
        subprocess.run(
            ["bash", "-c",
             f"source {CCP4_SETUP} >/dev/null 2>&1; gemmi rmsz -q {model} > {log} 2>&1"],
            capture_output=True, text=True, timeout=3600)
    if not log.exists():
        return None
    match = _GEMMI_RMSD.search(log.read_text(errors="ignore"))
    if not match:
        return None
    return {"bond": float(match.group(1)), "angle": float(match.group(2))}


def collect(pdb_ids: list[str], cache: Path) -> tuple[list[dict], list[dict]]:
    """Run all three configurations on every entry."""
    rows, skipped = [], []
    for pdb_id in pdb_ids:
        pdb_id = pdb_id.upper()
        print(f"[{pdb_id}]", file=sys.stderr)
        model = fetch(pdb_id, cache)
        if model is None:
            skipped.append({"pdb_id": pdb_id, "reason": "no PDB-format model"})
            continue
        cdl = run_phenix(model, cache, cdl=True)
        eh = run_phenix(model, cache, cdl=False)
        gem = run_gemmi(model, cache)
        if cdl is None or eh is None or gem is None:
            print("  ! a configuration failed", file=sys.stderr)
            skipped.append({"pdb_id": pdb_id, "reason": "a configuration failed or was unparsable"})
            continue
        rows.append({
            "pdb_id": pdb_id,
            "n_bond_phenix": cdl["n_bond"],
            "phenix_cdl_bond": cdl["bond"],
            "phenix_eh_bond": eh["bond"],
            "gemmi_bond": gem["bond"],
            "phenix_cdl_angle": cdl["angle"],
            "phenix_eh_angle": eh["angle"],
            "gemmi_angle": gem["angle"],
            # A vs B — pure library effect, same implementation.
            "library_effect_bond": round(eh["bond"] - cdl["bond"], 5),
            "library_effect_angle": round(eh["angle"] - cdl["angle"], 4),
            # B vs C — near-matched library, different implementations.
            "implementation_bond": round(gem["bond"] - eh["bond"], 5),
            "implementation_angle": round(gem["angle"] - eh["angle"], 4),
            # A vs C — what PR #28 published.
            "cross_library_bond": round(gem["bond"] - cdl["bond"], 5),
            "cross_library_angle": round(gem["angle"] - cdl["angle"], 4),
        })
        print(f"  bond  CDL {cdl['bond']:.5f}  E&H {eh['bond']:.5f}  gemmi {gem['bond']:.5f}"
              f"   | library {eh['bond'] - cdl['bond']:+.5f}"
              f"  implementation {gem['bond'] - eh['bond']:+.5f}", file=sys.stderr)
        print(f"  angle CDL {cdl['angle']:.4f}  E&H {eh['angle']:.4f}  gemmi {gem['angle']:.4f}"
              f"   | library {eh['angle'] - cdl['angle']:+.4f}"
              f"  implementation {gem['angle'] - eh['angle']:+.4f}", file=sys.stderr)
    return rows, skipped


def summarize(rows: list[dict]) -> dict[str, Any]:
    """Median / p90 / max of each decomposition term."""
    if not rows:
        return {"n": 0}

    def stats(values: list[float]) -> dict[str, Any]:
        ordered = sorted(abs(v) for v in values)
        idx = min(len(ordered) - 1, max(0, round(0.9 * (len(ordered) - 1))))
        return {
            "signed_median": round(statistics.median(values), 5),
            "abs_median": round(statistics.median(ordered), 5),
            "abs_p90": round(ordered[idx], 5),
            "abs_max": round(ordered[-1], 5),
        }

    out = {"n": len(rows)}
    for key in ("library_effect_bond", "implementation_bond", "cross_library_bond",
                "library_effect_angle", "implementation_angle", "cross_library_angle"):
        out[key] = stats([r[key] for r in rows])
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("pdb_ids", nargs="*")
    ap.add_argument("--ids-file")
    ap.add_argument("--cache")
    ap.add_argument("--json", dest="json_out")
    args = ap.parse_args()

    ids = list(args.pdb_ids)
    if args.ids_file:
        payload = json.loads(Path(args.ids_file).read_text())
        ids += payload if isinstance(payload, list) else [i for v in payload.values() for i in v]
    if not ids:
        ap.error("give PDB IDs or --ids-file")

    cache = Path(args.cache) if args.cache else Path(tempfile.gettempdir()) / "bench_cache_t05lib"
    rows, skipped = collect(ids, cache)
    summary = summarize(rows)
    if args.json_out:
        Path(args.json_out).write_text(
            json.dumps({"rows": rows, "skipped": skipped, "summary": summary}, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    return 0 if rows else 1


if __name__ == "__main__":
    raise SystemExit(main())
