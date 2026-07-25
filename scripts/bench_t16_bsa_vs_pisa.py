#!/usr/bin/env python3
"""Benchmark the T16 interface-BSA agreement tolerance: biotite SASA vs PDBePISA.

De-provisionalizes the `Interface buried surface area | |Δ| ≤ 10 %` tolerance in
`ref/thresholds_and_standards.md` / `ref/structural_criteria.yaml` (GitHub #18) by
measuring the actual inter-program spread on a set of deposited complexes instead
of asserting a magnitude.

Method (matched configuration, per the tolerance's own precondition):
  - biotite  : Shrake-Rupley SASA, 1.4 Å probe, ProtOr radii, protein atoms only
               (`struc.filter_amino_acids` — no waters, no hetero), exactly the
               recipe `scripts/t16_interface_quality.py` uses. Total buried area
               ΣSASA(chains) − SASA(complex), i.e. *both* sides of the interface.
  - PDBePISA : `interface_area` from the PDBe PISA REST API for biological
               assembly 1. PISA reports the area buried on *one* side (the mean of
               the two), so the matched quantity is 2 × interface_area. PISA uses a
               Lee & Richards surface and includes ligand/hetero atoms in the
               molecule surface; those are the residual definitional differences.

Comparison is per interface, restricted to protein-protein interfaces between two
distinct author chains present in the asymmetric unit (symmetry-mate interfaces are
skipped: the ASU coordinates cannot reproduce them without applying the operator).

Usage:
    python3 scripts/bench_t16_bsa_vs_pisa.py                 # default test set
    python3 scripts/bench_t16_bsa_vs_pisa.py 1brs 2ptc ...   # explicit entries
    python3 scripts/bench_t16_bsa_vs_pisa.py --cache DIR --json out.json
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

PISA_API = "https://www.ebi.ac.uk/pdbe/api/pisa/interfaces/{pdb_id}/1"
RCSB_PDB = "https://files.rcsb.org/download/{pdb_id}.pdb"

# Test set spanning interface size and complex type: protease-inhibitor and other
# transient complexes (~600-900 Å² per side), antibody-antigen, obligate/large
# interfaces (> 1500 Å²), and a multi-interface oligomer (4HHB, haemoglobin).
DEFAULT_SET = [
    "1brs",  # barnase-barstar (transient, the canonical case)
    "2ptc",  # trypsin-BPTI
    "1cho",  # alpha-chymotrypsin-OMTKY3
    "3sgb",  # S. griseus protease B-OMTKY3
    "2sic",  # subtilisin-SSI
    "1avx",  # trypsin-soybean trypsin inhibitor
    "1ay7",  # barnase-SD-barstar
    "1vfb",  # Fv D1.3-lysozyme (antibody-antigen)
    "3hfm",  # HyHEL-10 Fab-lysozyme (antibody-antigen, 3 chains)
    "1fss",  # acetylcholinesterase-fasciculin (large)
    "1dfj",  # RNase A-RNase inhibitor (very large)
    "1e96",  # Rac-p67phox
    "1gla",  # glycerol kinase-IIA(Glc)
    "4hhb",  # haemoglobin (multi-interface oligomer, alpha2beta2)
]


def fetch(url: str, dest: Path, binary: bool = False) -> Path:
    """Download `url` to `dest` unless already cached. Returns `dest`."""
    if dest.exists() and dest.stat().st_size:
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=60) as resp:
        data = resp.read()
    dest.write_bytes(data)
    return dest


def pisa_interfaces(pdb_id: str, cache: Path) -> list[dict[str, Any]]:
    """PISA assembly-1 interface records for `pdb_id` (empty if PISA has no entry)."""
    dest = cache / f"pisa_{pdb_id}.json"
    try:
        fetch(PISA_API.format(pdb_id=pdb_id), dest)
    except urllib.error.HTTPError as exc:
        print(f"  ! PISA API {exc.code} for {pdb_id} — skipped", file=sys.stderr)
        return []
    payload = json.loads(dest.read_text()).get(pdb_id, {})
    return payload.get("assembly", {}).get("interfaces", []) or []


def biotite_bsa(model: Path, chain_a: str, chain_b: str) -> float | None:
    """Total buried area for the `chain_a`/`chain_b` pair, by the t16 script's recipe.

    Returns None when either chain has no protein atoms in the deposited ASU.
    """
    import numpy as np
    import biotite.structure as struc
    import biotite.structure.io.pdb as pdb

    arr = pdb.get_structure(pdb.PDBFile.read(str(model)), model=1)
    arr = arr[struc.filter_amino_acids(arr)]
    pair = arr[np.isin(arr.chain_id, [chain_a, chain_b])]
    a = pair[pair.chain_id == chain_a]
    b = pair[pair.chain_id == chain_b]
    if not a.array_length() or not b.array_length():
        return None
    complex_sasa = float(np.nansum(struc.sasa(pair)))
    separated = float(np.nansum(struc.sasa(a))) + float(np.nansum(struc.sasa(b)))
    return separated - complex_sasa


def collect(pdb_ids: list[str], cache: Path, pause: float = 0.5) -> list[dict[str, Any]]:
    """Run both oracles over every eligible protein-protein interface in `pdb_ids`."""
    rows: list[dict[str, Any]] = []
    for pdb_id in pdb_ids:
        pdb_id = pdb_id.lower()
        print(f"[{pdb_id}]", file=sys.stderr)
        interfaces = pisa_interfaces(pdb_id, cache)
        if not interfaces:
            continue
        try:
            model = fetch(RCSB_PDB.format(pdb_id=pdb_id.upper()), cache / f"{pdb_id}.pdb")
        except urllib.error.HTTPError as exc:
            print(f"  ! RCSB {exc.code} for {pdb_id} — skipped", file=sys.stderr)
            continue
        for iface in interfaces:
            mols = iface.get("molecules", [])
            if len(mols) != 2 or any(m.get("molecule_class") != "Protein" for m in mols):
                continue
            ca, cb = mols[0].get("chain_id"), mols[1].get("chain_id")
            if not ca or not cb or ca == cb:
                continue  # symmetry mate — not reproducible from the ASU alone
            bsa = biotite_bsa(model, ca, cb)
            if bsa is None:
                print(f"  ! {pdb_id} {ca}/{cb}: chain missing from ASU — skipped", file=sys.stderr)
                continue
            pisa_total = 2.0 * float(iface["interface_area"])
            mean = (bsa + pisa_total) / 2.0
            rows.append(
                {
                    "pdb_id": pdb_id,
                    "interface": f"{ca}/{cb}",
                    "biotite_bsa_total": round(bsa, 1),
                    "pisa_interface_area": round(float(iface["interface_area"]), 1),
                    "pisa_bsa_total": round(pisa_total, 1),
                    "delta": round(bsa - pisa_total, 1),
                    "rel_delta_pct": round(100.0 * (bsa - pisa_total) / mean, 2),
                    "abs_rel_delta_pct": round(abs(100.0 * (bsa - pisa_total) / mean), 2),
                    "pisa_n_interface_residues": iface.get("number_interface_residues"),
                }
            )
            print(f"  {ca}/{cb}: biotite {bsa:8.1f}  PISA×2 {pisa_total:8.1f}"
                  f"  Δ {bsa - pisa_total:+7.1f} ({rows[-1]['rel_delta_pct']:+.1f} %)",
                  file=sys.stderr)
        time.sleep(pause)
    return rows


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Signed-bias and |Δ| distribution over all measured interfaces."""
    signed = [r["rel_delta_pct"] for r in rows]
    absolute = sorted(r["abs_rel_delta_pct"] for r in rows)
    if not rows:
        return {"n": 0}

    def pct(p: float) -> float:
        idx = min(len(absolute) - 1, max(0, round(p / 100.0 * (len(absolute) - 1))))
        return absolute[idx]

    return {
        "n_interfaces": len(rows),
        "n_entries": len({r["pdb_id"] for r in rows}),
        "signed_median_pct": round(statistics.median(signed), 2),
        "signed_mean_pct": round(statistics.fmean(signed), 2),
        "abs_median_pct": round(statistics.median(absolute), 2),
        "abs_p90_pct": round(pct(90), 2),
        "abs_max_pct": round(absolute[-1], 2),
        "abs_min_pct": round(absolute[0], 2),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("pdb_ids", nargs="*", default=None, help="PDB IDs (default: built-in set)")
    ap.add_argument("--cache", default=None, help="download cache directory")
    ap.add_argument("--json", dest="json_out", default=None, help="write full results here")
    args = ap.parse_args()

    cache = Path(args.cache) if args.cache else Path.cwd() / ".bench_cache_t16"
    rows = collect(args.pdb_ids or DEFAULT_SET, cache)
    summary = summarize(rows)
    out = {"rows": rows, "summary": summary}
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    return 0 if rows else 1


if __name__ == "__main__":
    raise SystemExit(main())
