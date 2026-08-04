#!/usr/bin/env python3
"""Measure `d_FSC_model_pre / d_min` for cached EM entries, before any refinement.

Round 22 found that the two entries whose model-map FSC crossing sits furthest past
their map's own stated resolution are the two largest `d_FSC_model` excursions in the
benchmark -- 9H7U (ratio 1.372, -36.15 %) and 10BU (1.360, +4.786 %). That is n = 2,
so it is a hypothesis (round 8's rule).

The reason it is testable at all is that the ratio is a **pre-refinement** quantity:
it needs only `mtriage` on the deposited model against its own map. A set can
therefore be SELECTED on it and then refined, without the selection being downstream
of the outcome. This script is that selection step.

It reuses `bench_refinement_deltas_em.measure()` rather than reimplementing the
crossing, so the screen and the benchmark compute the identical quantity -- including
the sustained-crossing rule (20 consecutive shells below 0.143) that round 9 had to
introduce because mtriage's own reported value is defeated by one anomalous shell.

The base rate matters as much as the hits: 2 of 36 on record, ~5.6 %. Every screened
entry is written out, hit or miss, so the denominator cannot go missing the way
rounds 16-18 found it had elsewhere.

Usage:
    python3 scripts/screen_dfsc_ratio.py --cache DIR --json screened.json
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import statistics
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parent.parent

# The ratio above which round 22 saw both large excursions. It is a POST-HOC cut
# from n = 2 -- chosen because the ratio distribution has a clean gap there
# (1.372, 1.360, then 1.076) -- and this round tests it rather than assuming it.
HIGH_RATIO = 1.3


def load_bench():
    """Import the EM benchmark so the screen measures the identical quantity."""
    spec = importlib.util.spec_from_file_location(
        "bench_em", REPO / "scripts" / "bench_refinement_deltas_em.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def screen(entries: list[dict], cache: Path) -> tuple[list[dict], list[dict]]:
    """Measure the pre-refinement crossing for each entry. No refinement is run."""
    bench = load_bench()
    rows, skipped = [], []
    for entry in entries:
        pdb_id = entry["pdb_id"].lower()
        resolution = float(entry["resolution"])
        model, map_file = cache / f"{pdb_id}.cif", cache / f"{pdb_id}.map"
        print(f"[{pdb_id.upper()}]", file=sys.stderr)
        if not model.exists() or not map_file.exists():
            skipped.append({"pdb_id": pdb_id.upper(), "reason": "model or map missing"})
            continue
        pre = bench.measure(model, map_file, resolution, cache, f"{pdb_id}_pre")
        crossing = pre["d_fsc_model_masked"]
        if crossing is None or not pre["d_fsc_model_plausible"]:
            reason = ("no sustained crossing" if crossing is None
                      else f"crossing {crossing:.2f} A implausible for a {resolution} A map")
            print(f"  ! {reason}", file=sys.stderr)
            skipped.append({"pdb_id": pdb_id.upper(), "reason": reason})
            continue
        ratio = crossing / resolution
        rows.append({
            "pdb_id": pdb_id.upper(), "resolution": resolution,
            "d_fsc_model_pre": crossing, "ratio": round(ratio, 4),
            "cc_mask_pre": pre["cc_mask"],
            "high_ratio": bool(ratio > HIGH_RATIO),
        })
        print(f"  crossing {crossing:.3f} A / {resolution} A = ratio {ratio:.3f}"
              f"{'   <-- HIGH' if ratio > HIGH_RATIO else ''}", file=sys.stderr)
    return rows, skipped


def summarize(rows: list[dict]) -> dict[str, Any]:
    if not rows:
        return {"n": 0}
    ratios = [r["ratio"] for r in rows]
    hits = [r for r in rows if r["high_ratio"]]
    return {
        "n_screened": len(rows),
        "n_high_ratio": len(hits),
        "base_rate_pct": round(100.0 * len(hits) / len(rows), 1),
        "high_ratio_ids": [r["pdb_id"] for r in hits],
        "ratio_median": round(statistics.median(ratios), 4),
        "ratio_min": round(min(ratios), 4), "ratio_max": round(max(ratios), 4),
        "cut": HIGH_RATIO,
        # On record before this round: 2 of 36 = 5.6 %.
        "prior_base_rate_pct": 5.6,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cache", required=True)
    ap.add_argument("--entries", help="JSON: [{pdb_id, resolution}, ...]; default <cache>/entries.json")
    ap.add_argument("--json", dest="json_out")
    args = ap.parse_args()

    cache = Path(args.cache)
    entries_path = Path(args.entries) if args.entries else cache / "entries.json"
    entries = json.loads(entries_path.read_text())

    rows, skipped = screen(entries, cache)
    summary = summarize(rows)
    if args.json_out:
        Path(args.json_out).write_text(
            json.dumps({"rows": rows, "skipped": skipped, "summary": summary}, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    return 0 if rows else 1


if __name__ == "__main__":
    raise SystemExit(main())
