#!/usr/bin/env python3
"""Benchmark superposition agreement: phenix.superpose_models vs TM-align.

Settles two `[template]` tolerances in `ref/thresholds_and_standards.md` that share a
tool pair and a precondition:

  - CA RMSD               |Δ| ≤ 0.03 Å **on the same residue selection** (measured here; the
                          pre-benchmark template was 0.10 Å)
  - Aligned-residue count ± 2 residues **within one aligner class**

Both tolerances already carry the warning that different aligners align different
subsets. This measures how large that effect actually is, and what is left once the
selection agrees.

Method, on pairs of deposited structures of the same or homologous proteins:
  - PHENIX: `phenix.superpose_models fixed moving morph=False trim=False`
    → `Final <moving> RMSD: <rmsd> N: <n> of <m>`. Morphing and trimming are switched
    off deliberately: both distort the model to improve the fit, and TM-align does a
    rigid-body superposition, so leaving them on would compare a deformed model
    against a rigid one.
  - TM-align: `TMalign fixed moving` → `Aligned length= <n>, RMSD= <rmsd>`.

Both are structure-based aligners, so the aligned-residue tolerance's "one aligner
class" precondition is satisfied — this pairing is inside the class, not across it.

Usage:
    python3 scripts/bench_t01_superposition.py --pairs-file pairs.json --cache DIR
    python3 scripts/bench_t01_superposition.py 1UBQ:1UBI 1LYZ:1LZ1 --cache DIR
"""
from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from toolchain import TMALIGN, phenix, run_logged

RCSB_PDB = "https://files.rcsb.org/download/{pdb_id}.pdb"
_TM = re.compile(r"Aligned length=\s*(\d+),\s*RMSD=\s*([\d.]+)")
_TM_SCORE = re.compile(r"TM-score=\s*([\d.]+)\s*\(if normalized by length of Chain_2")
_PHENIX_FINAL = re.compile(r"Final\s+\S+\s+RMSD:\s*([\d.]+)\s+N:\s*(\d+)\s+of\s+(\d+)")

# Pairs of independently deposited structures, spanning identical protein / different
# crystal form / homolog. Each is (fixed, moving).
DEFAULT_PAIRS = [
    ("1UBQ", "1UBI"),  # ubiquitin, two depositions
    ("1LYZ", "1LZ1"),  # hen vs human lysozyme (~60 % identity)
    ("2PTN", "1TPO"),  # trypsin, two depositions
    ("4PTI", "5PTI"),  # BPTI, two depositions
    ("7RSA", "5RSA"),  # ribonuclease A
    ("1A2P", "1BNI"),  # barnase
    ("2TRX", "1XOB"),  # thioredoxin
    ("1CA2", "2CBA"),  # carbonic anhydrase II
    ("1MBN", "1MBO"),  # myoglobin, met vs oxy
    ("4INS", "1ZNI"),  # insulin
    ("1HEW", "1HEL"),  # lysozyme, complex vs free
    ("3EST", "1EST"),  # elastase
    # Homologs and cross-species pairs. Re-depositions of one protein leave the
    # aligners almost no room to disagree, so a floor measured only on those would be
    # optimistic; these span TM-score 0.93-1.00 at RMSD 0.23-1.7 Å (issue #30).
    ("1LZ1", "1LZ4"),  # human lysozyme, two forms
    ("2LYZ", "1LZ1"),  # hen vs human lysozyme
    ("1AKI", "1LZ1"),  # hen vs human lysozyme, different crystal form
    ("4LYZ", "1LZ1"),  # hen vs human lysozyme, different crystal form
    ("1BNI", "1RNB"),  # barnase vs binase
    ("2CI2", "1YPA"),  # chymotrypsin inhibitor 2
    ("1TON", "2PTN"),  # tonin vs trypsin
    ("1EST", "1BRU"),  # elastase, two forms
    ("1PPN", "9PAP"),  # papain
    ("2ACT", "9PAP"),  # actinidin vs papain
]


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


def run_tmalign(fixed: Path, moving: Path, work: Path, all_chains: bool) -> dict[str, Any] | None:
    """Rigid-body structural alignment: aligned length, RMSD and TM-score.

    `all_chains` passes `-ter 0`, which makes TM-align read every chain in the file.
    Without it TM-align stops at the first TER and aligns the **first chain only**,
    while phenix.superpose_models matches all chains — on 1A2P/1BNI that alone is the
    difference between 108 and 324 aligned residues. Comparing the default settings
    measures a tool quirk; `-ter 0` is the matched configuration.
    """
    suffix = "all" if all_chains else "first"
    log = work / f"tm_{fixed.stem}_{moving.stem}_{suffix}.log"
    if not log.exists() or not _TM.search(log.read_text(errors="ignore")):
        arguments = [TMALIGN, fixed, moving]
        if all_chains:
            arguments.extend(["-ter", "0"])
        run_logged(arguments, log, timeout=1800)
    if not log.exists():
        return None
    text = log.read_text(errors="ignore")
    match = _TM.search(text)
    if not match:
        return None
    score = _TM_SCORE.search(text)
    return {
        "n_aligned": int(match.group(1)),
        "rmsd": float(match.group(2)),
        "tm_score": float(score.group(1)) if score else None,
    }


def run_phenix(fixed: Path, moving: Path, work: Path) -> dict[str, Any] | None:
    """PHENIX superposition RMSD over its matched residues (no morph, no trim)."""
    log = work / f"sp_{fixed.stem}_{moving.stem}.log"
    if not log.exists() or not _PHENIX_FINAL.search(log.read_text(errors="ignore")):
        run_logged(
            [phenix("phenix.superpose_models"), fixed, moving, "morph=False", "trim=False"],
            log,
            cwd=work,
            timeout=3600,
        )
    if not log.exists():
        return None
    match = _PHENIX_FINAL.search(log.read_text(errors="ignore"))
    if not match:
        return None
    return {"rmsd": float(match.group(1)), "n_aligned": int(match.group(2)),
            "n_total": int(match.group(3))}


def collect(pairs: list[tuple[str, str]], cache: Path) -> tuple[list[dict], list[dict]]:
    """Run both aligners on every pair."""
    rows, skipped = [], []
    for fixed_id, moving_id in pairs:
        label = f"{fixed_id}/{moving_id}"
        print(f"[{label}]", file=sys.stderr)
        fixed, moving = fetch(fixed_id, cache), fetch(moving_id, cache)
        if fixed is None or moving is None:
            skipped.append({"pair": label, "reason": "no PDB-format coordinates"})
            continue
        tm = run_tmalign(fixed, moving, cache, all_chains=True)
        tm_first = run_tmalign(fixed, moving, cache, all_chains=False)
        ph = run_phenix(fixed, moving, cache)
        if tm is None or tm_first is None or ph is None:
            print(f"  ! failed (tmalign={tm is not None}, phenix={ph is not None})",
                  file=sys.stderr)
            skipped.append({"pair": label, "reason": "an aligner failed or was unparsable"})
            continue
        d_rmsd = ph["rmsd"] - tm["rmsd"]
        d_n = ph["n_aligned"] - tm["n_aligned"]
        rows.append({
            "pair": label,
            "tm_score": tm["tm_score"],
            "tmalign_rmsd": tm["rmsd"],
            "phenix_rmsd": ph["rmsd"],
            "tmalign_n_aligned": tm["n_aligned"],
            "phenix_n_aligned": ph["n_aligned"],
            "delta_rmsd": round(d_rmsd, 3),
            "abs_delta_rmsd": round(abs(d_rmsd), 3),
            "delta_n_aligned": d_n,
            "abs_delta_n_aligned": abs(d_n),
            "same_selection": d_n == 0,
            # Default TM-align settings (first chain only) — the unmatched configuration.
            "tmalign_rmsd_first_chain": tm_first["rmsd"],
            "tmalign_n_aligned_first_chain": tm_first["n_aligned"],
            "delta_rmsd_unmatched": round(ph["rmsd"] - tm_first["rmsd"], 3),
            "delta_n_aligned_unmatched": ph["n_aligned"] - tm_first["n_aligned"],
        })
        print(f"  TM-align {tm['rmsd']:5.2f} Å over {tm['n_aligned']:4d} | "
              f"PHENIX {ph['rmsd']:5.2f} Å over {ph['n_aligned']:4d} | "
              f"ΔRMSD {d_rmsd:+.2f}  ΔN {d_n:+d}  (TM-score {tm['tm_score']})",
              file=sys.stderr)
    return rows, skipped


def summarize(rows: list[dict]) -> dict[str, Any]:
    """RMSD and aligned-count agreement, split by whether the selections matched."""
    if not rows:
        return {"n": 0}

    def stats(values: list[float]) -> dict[str, Any]:
        if not values:
            return {"n": 0}
        ordered = sorted(abs(v) for v in values)
        idx = min(len(ordered) - 1, max(0, round(0.9 * (len(ordered) - 1))))
        return {
            "n": len(values),
            "signed_median": round(statistics.median(values), 3),
            "abs_median": round(statistics.median(ordered), 3),
            "abs_p90": round(ordered[idx], 3),
            "abs_max": round(ordered[-1], 3),
        }

    matched = [r for r in rows if r["same_selection"]]
    unmatched = [r for r in rows if not r["same_selection"]]
    return {
        "n_pairs": len(rows),
        "n_same_selection": len(matched),
        "rmsd_all": stats([r["delta_rmsd"] for r in rows]),
        "rmsd_same_selection": stats([r["delta_rmsd"] for r in matched]),
        "rmsd_different_selection": stats([r["delta_rmsd"] for r in unmatched]),
        "aligned_count": stats([float(r["delta_n_aligned"]) for r in rows]),
        "rmsd_unmatched_chain_config": stats([r["delta_rmsd_unmatched"] for r in rows]),
        "aligned_count_unmatched_chain_config": stats(
            [float(r["delta_n_aligned_unmatched"]) for r in rows]),
    }


def parse_pairs(tokens: list[str]) -> list[tuple[str, str]]:
    """Parse `FIXED:MOVING` tokens into pairs."""
    pairs = []
    for token in tokens:
        if ":" not in token:
            raise SystemExit(f"pair must be FIXED:MOVING, got {token!r}")
        a, b = token.split(":", 1)
        pairs.append((a.upper(), b.upper()))
    return pairs


def main() -> int:
    from benchmark_environment import announce_benchmark_environment

    announce_benchmark_environment()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("pairs", nargs="*", help="FIXED:MOVING tokens (default: built-in set)")
    ap.add_argument("--pairs-file", help="JSON file: [[fixed, moving], ...]")
    ap.add_argument("--cache")
    ap.add_argument("--json", dest="json_out")
    args = ap.parse_args()

    pairs = parse_pairs(args.pairs) if args.pairs else []
    if args.pairs_file:
        pairs += [tuple(p) for p in json.loads(Path(args.pairs_file).read_text())]
    if not pairs:
        pairs = DEFAULT_PAIRS

    cache = Path(args.cache) if args.cache else Path(tempfile.gettempdir()) / "bench_cache_t01"
    rows, skipped = collect(pairs, cache)
    summary = summarize(rows)
    if args.json_out:
        Path(args.json_out).write_text(
            json.dumps({"rows": rows, "skipped": skipped, "summary": summary}, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    return 0 if rows else 1


if __name__ == "__main__":
    raise SystemExit(main())
