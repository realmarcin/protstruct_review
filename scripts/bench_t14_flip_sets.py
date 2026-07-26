#!/usr/bin/env python3
"""Benchmark the Asn/Gln/His flip-set half of the H-placement tolerance.

`ref/thresholds_and_standards.md` requires the two H builders to agree on the
"same Asn/Gln/His flip set". PR #28 measured H count and clashscore but not flips,
because `phenix.clashscore` does not emit flip records. **`reduce` does**: both
builders write `USER  MOD` lines into the output PDB recording, per residue, whether
the amide/imidazole was flipped and how confident the call was.

Record format (Richardson `reduce`):

    USER  MOD Single : A  32 GLN     :FLIP  amide:sc=   0.435  F(o=-0.2,f=0.44)
    USER  MOD Single : A   2 GLN     :      amide:sc=   1.61   X(o=1.6,f=1.2)

The single-letter code before `(o=...` is the flip category: `F` = flipped,
`K` = keep, `C` = clashes either way, `X` = uncertain. Both the decision and the
category are compared, because an `X`-vs-`K` disagreement is a weaker signal than
`F`-vs-`K`: the first is two builders hedging differently on an ambiguous residue,
the second is a genuine conflict about the model.

It also compares the **H-atom count** between the two builders, which is the other
half of the H-placement tolerance and the comparison that tolerance actually names.
(PR #28 measured H count between two *conventions* of one builder instead, which is
a different quantity — see `ref/research/tolerance_benchmark_flip_sets.md`.)

Usage:
    python3 scripts/bench_t14_flip_sets.py 1ABC 2DEF --cache DIR --json out.json
    python3 scripts/bench_t14_flip_sets.py --ids-file ids.json --cache DIR
"""
from __future__ import annotations

import argparse
import json
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
PHENIX_REDUCE = str(Path.home() / "phenix-2.0-5936" / "phenix_bin" / "phenix.reduce")
REDUCE = str(Path.home() / "tools" / "reduce-src" / "build" / "reduce_src" / "reduce")

# USER  MOD Single : A  32 GLN     :FLIP  amide:sc=   0.435  F(o=-0.2,f=0.44)
_FLIP = re.compile(
    r"^USER  MOD \S+\s*:\s*(?P<chain>.)\s*(?P<resseq>\d+)\s+(?P<resname>\S+)\s*:"
    r"(?P<decision>FLIP|\s*)\s*(?P<kind>amide|his)\s*:sc=\s*(?P<score>\S+)\s+"
    r"(?P<category>[A-Z])\(")

FLIPPABLE = {"ASN", "GLN", "HIS"}


def hydrogen_count(model_h: Path) -> int:
    """Hydrogens in a built model (element column, not name heuristics)."""
    return sum(1 for line in model_h.read_text(errors="ignore").splitlines()
               if line.startswith(("ATOM", "HETATM")) and line[76:78].strip() == "H")


def het_components(model: Path) -> set[str]:
    """Non-water hetero components present — the ones a het dictionary must cover."""
    return {line[17:20].strip() for line in model.read_text(errors="ignore").splitlines()
            if line.startswith("HETATM") and line[17:20].strip() != "HOH"}


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


def build(model: Path, cache: Path, phenix: bool) -> Path | None:
    """Add hydrogens with one of the two builders; returns the output PDB."""
    tag = "phx" if phenix else "std"
    out = cache / f"{model.stem}_h_{tag}.pdb"
    exe = PHENIX_REDUCE if phenix else REDUCE
    if not out.exists() or not out.stat().st_size:
        subprocess.run(["bash", "-c", f"{exe} -quiet -build {model} > {out} 2>/dev/null"],
                       capture_output=True, text=True, timeout=3600)
        if not out.exists() or not out.stat().st_size:
            return None
    return out


def flip_calls(model_h: Path) -> dict[tuple[str, int, str], tuple[bool, str]]:
    """Map each flippable residue to (was_flipped, category) from its USER MOD line."""
    calls = {}
    for line in model_h.read_text(errors="ignore").splitlines():
        if not line.startswith("USER  MOD"):
            continue
        match = _FLIP.match(line)
        if not match:
            continue
        resname = match.group("resname").upper()
        if resname not in FLIPPABLE:
            continue
        key = (match.group("chain"), int(match.group("resseq")), resname)
        calls[key] = (match.group("decision").strip() == "FLIP", match.group("category"))
    return calls


def collect(pdb_ids: list[str], cache: Path) -> tuple[list[dict], list[dict]]:
    """Compare the two builders' flip calls on every entry."""
    rows, skipped = [], []
    for pdb_id in pdb_ids:
        pdb_id = pdb_id.upper()
        print(f"[{pdb_id}]", file=sys.stderr)
        model = fetch(pdb_id, cache)
        if model is None:
            skipped.append({"pdb_id": pdb_id, "reason": "no PDB-format model"})
            continue
        phx, std = build(model, cache, phenix=True), build(model, cache, phenix=False)
        if phx is None or std is None:
            skipped.append({"pdb_id": pdb_id, "reason": "an H builder failed"})
            continue
        n_h_phx, n_h_std = hydrogen_count(phx), hydrogen_count(std)
        het = het_components(model)
        a, b = flip_calls(phx), flip_calls(std)
        if not a and not b:
            print("  ! no flippable residues with USER MOD records — skipped", file=sys.stderr)
            skipped.append({"pdb_id": pdb_id, "reason": "no flip records"})
            continue

        shared = sorted(set(a) & set(b))
        decision_diffs = [k for k in shared if a[k][0] != b[k][0]]
        category_diffs = [k for k in shared if a[k][1] != b[k][1] and a[k][0] == b[k][0]]
        rows.append({
            "pdb_id": pdb_id,
            "n_flippable_phenix": len(a),
            "n_flippable_standalone": len(b),
            "n_shared": len(shared),
            "n_only_phenix": len(set(a) - set(b)),
            "n_only_standalone": len(set(b) - set(a)),
            "n_flipped_phenix": sum(1 for v in a.values() if v[0]),
            "n_flipped_standalone": sum(1 for v in b.values() if v[0]),
            "n_h_phenix": n_h_phx,
            "n_h_standalone": n_h_std,
            "h_count_delta_pct": round(100.0 * (n_h_phx - n_h_std) / n_h_std, 3) if n_h_std else None,
            "het_components": sorted(het),
            "has_het": bool(het),
            "n_decision_disagreements": len(decision_diffs),
            "n_category_only_disagreements": len(category_diffs),
            "decision_disagreements": [f"{c}{r} {n}" for c, r, n in decision_diffs],
            "identical": not decision_diffs and not category_diffs
                         and set(a) == set(b),
        })
        print(f"  {len(shared)} shared residues, {rows[-1]['n_flipped_phenix']}/"
              f"{rows[-1]['n_flipped_standalone']} flipped, "
              f"{len(decision_diffs)} decision diffs, {len(category_diffs)} category-only diffs"
              f" | H {n_h_phx}/{n_h_std} ({rows[-1]['h_count_delta_pct']:+.3f} %)"
              f"{' het:' + ','.join(sorted(het)) if het else ''}", file=sys.stderr)
    return rows, skipped


def summarize(rows: list[dict]) -> dict[str, Any]:
    """How often the two builders make identical flip calls."""
    if not rows:
        return {"n": 0}
    shared = sum(r["n_shared"] for r in rows)

    def h_stats(subset: list[dict]) -> dict[str, Any]:
        values = sorted(abs(r["h_count_delta_pct"]) for r in subset
                        if r["h_count_delta_pct"] is not None)
        if not values:
            return {"n": 0}
        idx = min(len(values) - 1, max(0, round(0.9 * (len(values) - 1))))
        return {"n": len(values), "abs_median": round(statistics.median(values), 3),
                "abs_p90": round(values[idx], 3), "abs_max": round(values[-1], 3),
                "n_exceeding_0.1_pct": sum(1 for v in values if v > 0.1)}

    return {
        "n_models": len(rows),
        "h_count_all": h_stats(rows),
        "h_count_protein_only": h_stats([r for r in rows if not r["has_het"]]),
        "h_count_with_het": h_stats([r for r in rows if r["has_het"]]),
        "n_flippable_residues_compared": shared,
        "n_models_identical": sum(1 for r in rows if r["identical"]),
        "total_decision_disagreements": sum(r["n_decision_disagreements"] for r in rows),
        "total_category_only_disagreements": sum(r["n_category_only_disagreements"] for r in rows),
        "total_residues_only_one_builder": sum(
            r["n_only_phenix"] + r["n_only_standalone"] for r in rows),
        "total_flipped_phenix": sum(r["n_flipped_phenix"] for r in rows),
        "total_flipped_standalone": sum(r["n_flipped_standalone"] for r in rows),
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

    cache = Path(args.cache) if args.cache else Path(tempfile.gettempdir()) / "bench_cache_t14"
    rows, skipped = collect(ids, cache)
    summary = summarize(rows)
    if args.json_out:
        Path(args.json_out).write_text(
            json.dumps({"rows": rows, "skipped": skipped, "summary": summary}, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    return 0 if rows else 1


if __name__ == "__main__":
    raise SystemExit(main())
