#!/usr/bin/env python3
"""Benchmark clashscore and H-placement agreement: cctbx vs Richardson standalone.

Settles two `[template]` tolerances in `ref/thresholds_and_standards.md` that were
backed by a single in-repo observation (1SAR: 3.13 cctbx vs 3.63 standalone):

  - Clashscore  ± 1.0
  - H-placement  H-atom count within ± 2 %, clashscore delta within ± 1.0

Both come from one run per model, because both paths are the same pipeline —
build hydrogens, then count serious overlaps — differing in implementation:

  - cctbx path:      `phenix.clashscore model.pdb` (adds H internally via reduce)
  - standalone path: Richardson `reduce -build`, then `probe`, with the clashscore
    summed here by the MolProbity definition — serious clashes (overlap ≥ 0.4 Å)
    per 1000 atoms, counting each atom pair once.

The dominant expected term is the **H-build convention**: cctbx defaults to
electron-cloud-center hydrogen positions for X-ray models, standalone `reduce`
defaults to nuclear positions. Running standalone `reduce` both ways (`-build` and
`-nuclear`) separates that convention effect from the implementation noise floor —
which is the thing the tolerance is supposed to bound.

Usage:
    python3 scripts/bench_t05_clashscore_h.py 1ABC 2DEF --cache DIR --json out.json
    python3 scripts/bench_t05_clashscore_h.py --ids-file ids.json --cache DIR
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
PHENIX_BIN = Path.home() / "phenix-2.0-5936" / "phenix_bin"
TOOLS = Path.home() / "tools"
REDUCE = TOOLS / "reduce-src" / "build" / "reduce_src" / "reduce"
PROBE = TOOLS / "probe-src" / "probe"

_CLASHSCORE = re.compile(r"clashscore\s*=\s*([\d.]+)")

# MolProbity's clash criterion: a "serious" clash is an overlap of at least 0.4 Å.
CLASH_OVERLAP = -0.4


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


def count_atoms(model: Path, hydrogens_only: bool = False) -> int:
    """Atoms in the clashscore denominator: non-water ATOM/HETATM records."""
    total = 0
    for line in model.read_text(errors="ignore").splitlines():
        if not line.startswith(("ATOM", "HETATM")) or line[17:20] == "HOH":
            continue
        if hydrogens_only and line[76:78].strip() != "H":
            continue
        total += 1
    return total


def run_phenix_clashscore(model: Path, work: Path) -> float | None:
    """cctbx clashscore (hydrogens built internally)."""
    log = work / f"pcs_{model.stem}.log"
    if not log.exists() or not _CLASHSCORE.search(log.read_text(errors="ignore")):
        subprocess.run(["bash", "-c",
                        f"cd {work} && {PHENIX_BIN / 'phenix.clashscore'} {model} > {log} 2>&1"],
                       capture_output=True, text=True, timeout=3600, env=dict(os.environ))
    if not log.exists():
        return None
    match = _CLASHSCORE.search(log.read_text(errors="ignore"))
    return float(match.group(1)) if match else None


def run_reduce(model: Path, work: Path, nuclear: bool) -> Path | None:
    """Standalone Richardson `reduce`, in nuclear or electron-cloud H geometry."""
    suffix = "nuc" if nuclear else "ec"
    out = work / f"{model.stem}_h_{suffix}.pdb"
    if not out.exists() or not out.stat().st_size:
        flags = "-build -nuclear" if nuclear else "-build"
        proc = subprocess.run(["bash", "-c", f"{REDUCE} -quiet {flags} {model} > {out} 2>/dev/null"],
                              capture_output=True, text=True, timeout=3600)
        if not out.exists() or not out.stat().st_size:
            print(f"  ! reduce failed ({suffix}): {proc.stderr[-200:]}", file=sys.stderr)
            return None
    return out


def run_probe_clashscore(model_h: Path, work: Path) -> float | None:
    """MolProbity clashscore from standalone `probe`: serious clashes per 1000 atoms."""
    out = work / f"probe_{model_h.stem}.txt"
    if not out.exists():
        cmd = (f'{PROBE} -u -q -mc -het -once "ogt33 not water" "ogt33" '
               f'{model_h} > {out} 2>/dev/null')
        subprocess.run(["bash", "-c", cmd], capture_output=True, text=True, timeout=3600)
    if not out.exists():
        return None
    pairs = set()
    for line in out.read_text(errors="ignore").splitlines():
        fields = line.split(":")
        # name:pat:type:srcAtom:targAtom:mingap:gap:... — 'bo' is a bad overlap.
        if len(fields) < 7 or fields[2] != "bo":
            continue
        try:
            mingap = float(fields[5])
        except ValueError:
            continue
        if mingap <= CLASH_OVERLAP:
            pairs.add(frozenset((fields[3], fields[4])))
    atoms = count_atoms(model_h)
    if not atoms:
        return None
    return 1000.0 * len(pairs) / atoms


def collect(pdb_ids: list[str], cache: Path) -> tuple[list[dict], list[dict]]:
    """Run both pipelines, plus both standalone H conventions, on every entry."""
    rows, skipped = [], []
    for pdb_id in pdb_ids:
        pdb_id = pdb_id.upper()
        print(f"[{pdb_id}]", file=sys.stderr)
        model = fetch(pdb_id, cache)
        if model is None:
            skipped.append({"pdb_id": pdb_id, "reason": "no PDB-format model"})
            continue
        if count_atoms(model, hydrogens_only=True):
            print("  ! model already has hydrogens — skipped", file=sys.stderr)
            skipped.append({"pdb_id": pdb_id, "reason": "deposited model already has H"})
            continue

        phenix_cs = run_phenix_clashscore(model, cache)
        h_ec = run_reduce(model, cache, nuclear=False)
        h_nuc = run_reduce(model, cache, nuclear=True)
        if phenix_cs is None or h_ec is None or h_nuc is None:
            skipped.append({"pdb_id": pdb_id, "reason": "clashscore or reduce failed"})
            continue
        cs_ec = run_probe_clashscore(h_ec, cache)
        cs_nuc = run_probe_clashscore(h_nuc, cache)
        if cs_ec is None or cs_nuc is None:
            skipped.append({"pdb_id": pdb_id, "reason": "probe failed"})
            continue

        n_h_ec = count_atoms(h_ec, hydrogens_only=True)
        n_h_nuc = count_atoms(h_nuc, hydrogens_only=True)
        rows.append({
            "pdb_id": pdb_id,
            "n_atoms": count_atoms(model),
            "phenix_clashscore": round(phenix_cs, 2),
            "standalone_clashscore_electron_cloud": round(cs_ec, 2),
            "standalone_clashscore_nuclear": round(cs_nuc, 2),
            # Matched convention: cctbx uses electron-cloud H for X-ray models.
            "delta_matched": round(cs_ec - phenix_cs, 2),
            "abs_delta_matched": round(abs(cs_ec - phenix_cs), 2),
            # Mismatched convention: the error a naive pairing would make.
            "delta_mismatched": round(cs_nuc - phenix_cs, 2),
            "abs_delta_mismatched": round(abs(cs_nuc - phenix_cs), 2),
            "n_h_electron_cloud": n_h_ec,
            "n_h_nuclear": n_h_nuc,
            "h_count_delta_pct": round(100.0 * (n_h_nuc - n_h_ec) / n_h_ec, 3) if n_h_ec else None,
        })
        print(f"  cctbx {phenix_cs:7.2f} | standalone ec {cs_ec:7.2f} nuc {cs_nuc:7.2f}"
              f" | Δmatched {cs_ec - phenix_cs:+6.2f} Δmismatched {cs_nuc - phenix_cs:+6.2f}"
              f" | H {n_h_ec}/{n_h_nuc}", file=sys.stderr)
    return rows, skipped


def summarize(rows: list[dict]) -> dict[str, Any]:
    """Agreement under matched vs mismatched H convention, and H-count agreement."""
    if not rows:
        return {"n": 0}

    def stats(values: list[float]) -> dict[str, Any]:
        ordered = sorted(abs(v) for v in values)
        idx = min(len(ordered) - 1, max(0, round(0.9 * (len(ordered) - 1))))
        return {
            "signed_median": round(statistics.median(values), 3),
            "abs_median": round(statistics.median(ordered), 3),
            "abs_p90": round(ordered[idx], 3),
            "abs_max": round(ordered[-1], 3),
        }

    return {
        "n": len(rows),
        "clashscore_matched_convention": stats([r["delta_matched"] for r in rows]),
        "clashscore_mismatched_convention": stats([r["delta_mismatched"] for r in rows]),
        "h_count_delta_pct": stats([r["h_count_delta_pct"] for r in rows
                                    if r["h_count_delta_pct"] is not None]),
        "clashscore_range": [min(r["phenix_clashscore"] for r in rows),
                             max(r["phenix_clashscore"] for r in rows)],
    }


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

    for tool in (REDUCE, PROBE):
        if not tool.exists():
            raise SystemExit(f"required tool not found: {tool}")

    cache = Path(args.cache) if args.cache else Path(tempfile.gettempdir()) / "bench_cache_t05"
    rows, skipped = collect(ids, cache)
    summary = summarize(rows)
    if args.json_out:
        Path(args.json_out).write_text(
            json.dumps({"rows": rows, "skipped": skipped, "summary": summary}, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    return 0 if rows else 1


if __name__ == "__main__":
    raise SystemExit(main())
