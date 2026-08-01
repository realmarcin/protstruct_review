#!/usr/bin/env python3
"""Benchmark bond-length RMSD agreement: phenix.model_statistics vs gemmi rmsz.

Settles the `Bond-length RMSD | ± 0.003 Å` `[template]` tolerance in
`ref/thresholds_and_standards.md`. Bond *angle* was already made library-conditional
by the domain-expert review (PHENIX's conformation-dependent library vs the CCP4
monomer library shifts angles 0.3-0.4°); bond *length* was left untested against the
same library difference, which is what this measures.

Method:
  - PHENIX: `phenix.model_statistics model.pdb` → the covalent-geometry bond RMSD,
    computed against PHENIX's restraint library (CDL by default since ~2016).
  - gemmi:  `gemmi rmsz model.pdb` → "Model rmsD: bond", computed against the CCP4
    monomer library (`$CLIBD_MON`, Engh & Huber lineage — the same library REFMAC
    uses).

Note the recipe correction: `ref/oracle_tools.md` cited `gemmi validate`, which is not
a gemmi subcommand. The geometry validator is `gemmi rmsz`, and it reports rmsD (in Å)
alongside rmsZ — only the rmsD line is comparable to PHENIX's RMSD.

PHENIX reports both a total bond RMSD (including SS bonds and other link records) and
a `covalent geometry : bond` figure. The latter is used: it matches the bond count
gemmi reports, so the two are summing over the same restraints.

Usage:
    python3 scripts/bench_t05_bond_rmsd.py 1ABC 2DEF --cache DIR --json out.json
    python3 scripts/bench_t05_bond_rmsd.py --ids-file ids.json --cache DIR
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

_PHENIX_COVALENT_BOND = re.compile(r"covalent geometry\s*:\s*bond\s+([\d.]+)\s*\(\s*(\d+)\)")
_PHENIX_TOTAL_BOND = re.compile(r"^\s*Bond\s*:\s*([\d.]+)\s+[\d.]+\s+(\d+)", re.M)
_GEMMI_RMSD = re.compile(r"Model rmsD:\s*bond:\s*([\d.]+)")
_GEMMI_BONDS = re.compile(r"(\d+)\s+of\s+(\d+)\s+bonds")


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


def run_phenix(model: Path, work: Path) -> dict[str, Any] | None:
    """Covalent-geometry bond RMSD (Å) and restraint count from PHENIX."""
    log = work / f"ms_{model.stem}.log"
    if not log.exists() or not _PHENIX_COVALENT_BOND.search(log.read_text(errors="ignore")):
        subprocess.run(["bash", "-c", f"cd {work} && {MODEL_STATISTICS} {model} > {log} 2>&1"],
                       capture_output=True, text=True, timeout=3600, env=dict(os.environ))
    if not log.exists():
        return None
    text = log.read_text(errors="ignore")
    covalent = _PHENIX_COVALENT_BOND.search(text)
    if not covalent:
        return None
    total = _PHENIX_TOTAL_BOND.search(text)
    return {
        "bond_rmsd": float(covalent.group(1)),
        "n_bonds": int(covalent.group(2)),
        "bond_rmsd_total": float(total.group(1)) if total else None,
        "n_bonds_total": int(total.group(2)) if total else None,
    }


def run_gemmi(model: Path, work: Path) -> dict[str, Any] | None:
    """Bond rmsD (Å) and restraint count from gemmi against the CCP4 monomer library."""
    log = work / f"rmsz_{model.stem}.log"
    if not log.exists() or not _GEMMI_RMSD.search(log.read_text(errors="ignore")):
        subprocess.run(
            ["bash", "-c",
             f"source {CCP4_SETUP} >/dev/null 2>&1; gemmi rmsz -q {model} > {log} 2>&1"],
            capture_output=True, text=True, timeout=3600)
    if not log.exists():
        return None
    text = log.read_text(errors="ignore")
    rmsd = _GEMMI_RMSD.search(text)
    if not rmsd:
        return None
    bonds = _GEMMI_BONDS.search(text)
    return {"bond_rmsd": float(rmsd.group(1)), "n_bonds": int(bonds.group(2)) if bonds else None}


def collect(pdb_ids: list[str], cache: Path) -> tuple[list[dict], list[dict]]:
    """Run both geometry validators on every entry."""
    rows, skipped = [], []
    for pdb_id in pdb_ids:
        pdb_id = pdb_id.upper()
        print(f"[{pdb_id}]", file=sys.stderr)
        model = fetch(pdb_id, cache)
        if model is None:
            skipped.append({"pdb_id": pdb_id, "reason": "no PDB-format model"})
            continue
        phenix, gem = run_phenix(model, cache), run_gemmi(model, cache)
        if phenix is None or gem is None:
            print(f"  ! failed (phenix={phenix is not None}, gemmi={gem is not None})",
                  file=sys.stderr)
            skipped.append({"pdb_id": pdb_id, "reason": "a validator failed or was unparsable"})
            continue
        delta = gem["bond_rmsd"] - phenix["bond_rmsd"]
        rows.append({
            "pdb_id": pdb_id,
            "phenix_bond_rmsd": phenix["bond_rmsd"],
            "gemmi_bond_rmsd": gem["bond_rmsd"],
            "phenix_n_bonds": phenix["n_bonds"],
            "gemmi_n_bonds": gem["n_bonds"],
            "bond_count_match": phenix["n_bonds"] == gem["n_bonds"],
            "delta": round(delta, 4),
            "abs_delta": round(abs(delta), 4),
        })
        print(f"  PHENIX {phenix['bond_rmsd']:.4f} ({phenix['n_bonds']} bonds)  "
              f"gemmi {gem['bond_rmsd']:.4f} ({gem['n_bonds']})  Δ {delta:+.4f}", file=sys.stderr)
    return rows, skipped


def summarize(rows: list[dict]) -> dict[str, Any]:
    """|Δ| distribution, plus how often the two libraries restrain the same bonds."""
    if not rows:
        return {"n": 0}
    absolute = sorted(r["abs_delta"] for r in rows)
    idx = min(len(absolute) - 1, max(0, round(0.9 * (len(absolute) - 1))))
    return {
        "n": len(rows),
        "signed_median": round(statistics.median(r["delta"] for r in rows), 4),
        "abs_median": round(statistics.median(absolute), 4),
        "abs_p90": round(absolute[idx], 4),
        "abs_max": round(absolute[-1], 4),
        "gemmi_higher": sum(1 for r in rows if r["delta"] > 0),
        "phenix_higher": sum(1 for r in rows if r["delta"] < 0),
        "bond_count_agrees": sum(1 for r in rows if r["bond_count_match"]),
    }


# The 17 models the published tolerance was measured on, recovered from the per-entry
# table in `ref/research/tolerance_benchmark_bond_rmsd.md` and committed here in round
# 18. Before that this script took its set from an uncommitted `--ids-file`, so the
# tolerance was reproducible only by whoever still had that file -- and the round-17
# audit found no `ids.json` committed anywhere in the repo. A `[benchmark]` provenance
# claims the number can be regenerated by re-running; that is only true if the set
# comes with the script.
#
# `bench_t05_restraint_library.py` shares this exact set (verified identical).
DEFAULT_SET = [
    "30TW", "9PLB", "28SX", "28SW", "28SV", "9LLR", "9PN7", "9HW2", "28SZ",
    "11AF", "30IZ", "12LO", "9HX9", "37BG", "24MR", "37AP", "37AS",
]
SET_IS_COMPLETE = True


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
        ids = list(DEFAULT_SET)
        print(f"using the committed benchmark set ({len(ids)} entries)", file=sys.stderr)

    cache = Path(args.cache) if args.cache else Path(tempfile.gettempdir()) / "bench_cache_t05geom"
    rows, skipped = collect(ids, cache)
    summary = summarize(rows)
    if args.json_out:
        Path(args.json_out).write_text(
            json.dumps({"rows": rows, "skipped": skipped, "summary": summary}, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    return 0 if rows else 1


if __name__ == "__main__":
    raise SystemExit(main())
