#!/usr/bin/env python3
"""Benchmark what DockQ's chain-mapping precondition is worth.

The `DockQ score` tolerance in `ref/thresholds_and_standards.md` is `|Δ| ≤ 0.01`
**after fixing/verifying the chain mapping**, and names "chain-mapping ambiguity in
multimers" as the *presumed (not proven)* main variance source. No second DockQ
implementation is installed, so a cross-tool benchmark is unavailable — but the
presumption itself is testable: score the same structure against itself under every
chain mapping that is chemically plausible, and report the spread.

A mapping is plausible when it pairs chains of the same sequence: those are the
assignments a tool (or an agent) could legitimately get wrong. Mapping a chain onto a
different sequence is not ambiguity, it is an error, and is excluded.

Model and native are the **same file**, so a perfect mapping scores 1.0 by
construction and everything below that is mapping cost alone — no modelling error is
mixed in.

Usage:
    python3 scripts/bench_t16_dockq_mapping.py 4HHB 1VFB --cache DIR --json out.json
"""
from __future__ import annotations

import argparse
import itertools
import json
import statistics
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

RCSB_PDB = "https://files.rcsb.org/download/{pdb_id}.pdb"

# Homo-oligomers and antibody complexes: the cases where equivalent chains exist.
DEFAULT_SET = ["4HHB", "1VFB", "3HFM", "1BRS", "2SIC"]

_THREE_TO_ONE = {
    "ALA": "A", "ARG": "R", "ASN": "N", "ASP": "D", "CYS": "C", "GLN": "Q", "GLU": "E",
    "GLY": "G", "HIS": "H", "ILE": "I", "LEU": "L", "LYS": "K", "MET": "M", "PHE": "F",
    "PRO": "P", "SER": "S", "THR": "T", "TRP": "W", "TYR": "Y", "VAL": "V",
}


def fetch(pdb_id: str, cache: Path) -> Path | None:
    """Deposited PDB-format coordinates."""
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


def chain_sequences(model: Path) -> dict[str, str]:
    """One-letter sequence per chain, from CA atoms."""
    seqs: dict[str, list[str]] = {}
    seen: set[tuple[str, str]] = set()
    for line in model.read_text(errors="ignore").splitlines():
        if not line.startswith("ATOM") or line[12:16].strip() != "CA":
            continue
        chain, resname, resseq = line[21], line[17:20].strip(), line[22:27]
        if (chain, resseq) in seen:
            continue
        seen.add((chain, resseq))
        seqs.setdefault(chain, []).append(_THREE_TO_ONE.get(resname, "X"))
    return {c: "".join(v) for c, v in seqs.items()}


def plausible_mappings(seqs: dict[str, str], limit: int = 8) -> list[tuple[str, str]]:
    """Mappings that pair each model chain with a same-sequence native chain.

    Returns (model_chains, native_chains) label pairs, identity first.
    """
    chains = sorted(seqs)
    if len(chains) < 2:
        return []
    # Group chains by sequence; only within-group swaps are legitimate ambiguity.
    groups: dict[str, list[str]] = {}
    for chain in chains:
        groups.setdefault(seqs[chain], []).append(chain)

    per_chain_options = [groups[seqs[c]] for c in chains]
    mappings = []
    for combo in itertools.product(*per_chain_options):
        if len(set(combo)) != len(combo):        # each native chain used once
            continue
        mappings.append(("".join(chains), "".join(combo)))
        if len(mappings) >= limit:
            break
    return mappings


def run_dockq(model: Path, mapping: tuple[str, str], cache: Path) -> float | None:
    """DockQ of a structure against itself under one chain mapping."""
    tag = f"{model.stem}_{mapping[0]}_{mapping[1]}"
    out = cache / f"dq_{tag}.json"
    if not out.exists():
        subprocess.run(
            ["bash", "-c",
             f"DockQ {model} {model} --mapping {mapping[0]}:{mapping[1]} "
             f"--json {out} > /dev/null 2>&1"],
            capture_output=True, text=True, timeout=3600)
    if not out.exists() or not out.stat().st_size:
        return None
    try:
        return float(json.load(out.open()).get("GlobalDockQ"))
    except (ValueError, TypeError, json.JSONDecodeError):
        return None


def collect(pdb_ids: list[str], cache: Path) -> tuple[list[dict], list[dict]]:
    """Score every plausible mapping for each complex."""
    rows, skipped = [], []
    for pdb_id in pdb_ids:
        pdb_id = pdb_id.upper()
        print(f"[{pdb_id}]", file=sys.stderr)
        model = fetch(pdb_id, cache)
        if model is None:
            skipped.append({"pdb_id": pdb_id, "reason": "no PDB-format model"})
            continue
        seqs = chain_sequences(model)
        mappings = plausible_mappings(seqs)
        if len(mappings) < 2:
            print("  ! only the identity mapping is plausible — no ambiguity to measure",
                  file=sys.stderr)
            skipped.append({"pdb_id": pdb_id,
                            "reason": "no equivalent chains; mapping is unambiguous"})
            continue
        scores = {}
        for mapping in mappings:
            score = run_dockq(model, mapping, cache)
            if score is not None:
                scores[f"{mapping[0]}:{mapping[1]}"] = round(score, 4)
                print(f"  {mapping[0]}:{mapping[1]} → {score:.4f}", file=sys.stderr)
        if len(scores) < 2:
            skipped.append({"pdb_id": pdb_id, "reason": "DockQ failed on the alternatives"})
            continue
        values = list(scores.values())
        rows.append({
            "pdb_id": pdb_id,
            "n_chains": len(seqs),
            "n_mappings_scored": len(scores),
            "scores": scores,
            "best": max(values),
            "worst": min(values),
            "spread": round(max(values) - min(values), 4),
        })
    return rows, skipped


def summarize(rows: list[dict]) -> dict[str, Any]:
    """How far the score moves across plausible mappings, against the ±0.01 band."""
    if not rows:
        return {"n": 0}
    spreads = [r["spread"] for r in rows]
    return {
        "n_complexes": len(rows),
        "spread_median": round(statistics.median(spreads), 4),
        "spread_max": round(max(spreads), 4),
        "n_exceeding_tolerance": sum(1 for s in spreads if s > 0.01),
        "tolerance_band": 0.01,
    }


def main() -> int:
    from benchmark_environment import announce_benchmark_environment

    announce_benchmark_environment()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("pdb_ids", nargs="*")
    ap.add_argument("--cache")
    ap.add_argument("--json", dest="json_out")
    args = ap.parse_args()

    ids = args.pdb_ids or DEFAULT_SET
    cache = Path(args.cache) if args.cache else Path(tempfile.gettempdir()) / "bench_cache_t16map"
    rows, skipped = collect(ids, cache)
    summary = summarize(rows)
    if args.json_out:
        Path(args.json_out).write_text(
            json.dumps({"rows": rows, "skipped": skipped, "summary": summary}, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    return 0 if rows else 1


if __name__ == "__main__":
    raise SystemExit(main())
