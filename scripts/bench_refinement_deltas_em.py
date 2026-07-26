#!/usr/bin/env python3
"""Benchmark the map-model half of the §4 refinement Δ-tolerances (cryo-EM).

`ref/thresholds_and_standards.md` §4 asserts:

  - Map-model fit did not degrade   CC_mask_post ≥ CC_mask_pre − 0.01;
                                    d_FSC_model_post ≤ d_FSC_model_pre + 0.05 Å

Neither quantity exists for X-ray data — `phenix.refine` reports no CC_mask, and
`d_FSC_model` is a map-model FSC measure — so this row cannot be covered by
`scripts/bench_refinement_deltas.py` and needs cryo-EM entries with released maps.

Method, per entry: real-space refine the deposited model against its own deposited
map, and measure CC_mask and d_FSC_model before and after. As in the X-ray case this
is the **null case** — the deposited model is already at its optimum, so whatever
spread remains is the floor a Δ band has to clear.

  - `phenix.map_correlations model map resolution=R` → CC_mask, CC_volume, CC_peaks.
    (`phenix.map_model_cc` is deprecated and refuses to run without `--force`.)
  - `phenix.mtriage model map` → d_FSC_model at FSC = 0 / 0.143 / 0.5, masked and
    unmasked.
  - `phenix.real_space_refine model map resolution=R` → the refined model.

Usage:
    python3 scripts/bench_refinement_deltas_em.py --cache DIR --json out.json
    # cache holds <pdb_id>.cif and its map as <pdb_id>.map, plus resolutions.json
"""
from __future__ import annotations

import argparse
import json
import os
import re
import statistics
import subprocess
import sys
from pathlib import Path
from typing import Any

PHENIX_BIN = Path.home() / "phenix-2.0-5936" / "phenix_bin"

_CC_MASK = re.compile(r"CC_mask\s*:\s*([\d.]+)")
# mtriage prints masked and unmasked columns; FSC=0.143 is the conventional model-map
# figure, so take that row's masked value.
_D_FSC_MODEL = re.compile(r"FSC\(map,\s*model map\)=0\.143\s*:\s*([\d.]+)\s+([\d.]+)")


def run(cmd: str, log: Path, pattern: re.Pattern, work: Path) -> str | None:
    """Run a command in `work`, caching on the log containing `pattern`."""
    if not log.exists() or not pattern.search(log.read_text(errors="ignore")):
        subprocess.run(["bash", "-c", f"cd {work} && {cmd} > {log} 2>&1"],
                       capture_output=True, text=True, timeout=7200, env=dict(os.environ))
    return log.read_text(errors="ignore") if log.exists() else None


def measure(model: Path, map_file: Path, resolution: float, work: Path,
            tag: str) -> dict[str, Any]:
    """CC_mask and masked d_FSC_model(0.143) for one model against one map."""
    cc_log = work / f"mc_{tag}.log"
    cc_text = run(f"{PHENIX_BIN / 'phenix.map_correlations'} {model} {map_file} "
                  f"resolution={resolution}", cc_log, _CC_MASK, work)
    mt_log = work / f"mt_{tag}.log"
    mt_text = run(f"{PHENIX_BIN / 'phenix.mtriage'} {model} {map_file}",
                  mt_log, _D_FSC_MODEL, work)
    cc = _CC_MASK.search(cc_text) if cc_text else None
    dfsc = _D_FSC_MODEL.search(mt_text) if mt_text else None
    d_value = float(dfsc.group(1)) if dfsc else None
    # mtriage's model-map FSC crossings are degenerate without half-maps: 27WR reports
    # FSC=0.5 at 29.79 Å for a 2.7 Å map, and 9VJD reports FSC=0.143 at 29.65 Å for a
    # 2.86 Å map (passing resolution= explicitly does not fix it, and the log shows
    # "d99 (half map 1): None"). A crossing far outside the map's own resolution is a
    # failed curve, not a measurement, so it is reported as unreliable rather than
    # differenced into a tolerance.
    plausible = d_value is not None and d_value <= 2.5 * resolution
    return {
        "cc_mask": float(cc.group(1)) if cc else None,
        "d_fsc_model_masked": d_value,
        "d_fsc_model_plausible": plausible,
    }


def refine(model: Path, map_file: Path, resolution: float, work: Path,
           tag: str) -> Path | None:
    """Real-space refine the model against its map; returns the refined coordinates."""
    prefix = f"rs_{tag}"
    cached = sorted(work.glob(f"{prefix}_real_space_refined_*.cif"))
    if cached:                       # real_space_refine takes minutes; do not repeat it
        return cached[-1]
    subprocess.run(
        ["bash", "-c",
         f"cd {work} && {PHENIX_BIN / 'phenix.real_space_refine'} {model} {map_file} "
         f"resolution={resolution} output.prefix={prefix} --overwrite "
         f"> {work / f'rsr_{tag}.log'} 2>&1"],
        capture_output=True, text=True, timeout=14400, env=dict(os.environ))
    hits = sorted(work.glob(f"{prefix}_real_space_refined_*.cif"))
    return hits[-1] if hits else None


def collect(entries: list[dict], cache: Path) -> tuple[list[dict], list[dict]]:
    """Refine and re-measure each EM entry."""
    rows, skipped = [], []
    for entry in entries:
        pdb_id, resolution = entry["pdb_id"].lower(), float(entry["resolution"])
        model, map_file = cache / f"{pdb_id}.cif", cache / f"{pdb_id}.map"
        print(f"[{pdb_id.upper()}]", file=sys.stderr)
        if not model.exists() or not map_file.exists():
            skipped.append({"pdb_id": pdb_id.upper(), "reason": "model or map missing"})
            continue
        pre = measure(model, map_file, resolution, cache, f"{pdb_id}_pre")
        if pre["cc_mask"] is None:
            skipped.append({"pdb_id": pdb_id.upper(), "reason": "map_correlations failed"})
            continue
        refined = refine(model, map_file, resolution, cache, pdb_id)
        if refined is None:
            print("  ! real_space_refine failed", file=sys.stderr)
            skipped.append({"pdb_id": pdb_id.upper(), "reason": "real_space_refine failed"})
            continue
        post = measure(refined, map_file, resolution, cache, f"{pdb_id}_post")
        if post["cc_mask"] is None:
            skipped.append({"pdb_id": pdb_id.upper(), "reason": "post map_correlations failed"})
            continue
        row = {"pdb_id": pdb_id.upper(), "resolution": resolution,
               "cc_mask_pre": pre["cc_mask"], "cc_mask_post": post["cc_mask"],
               "cc_mask_delta": round(post["cc_mask"] - pre["cc_mask"], 4),
               "d_fsc_model_pre": pre["d_fsc_model_masked"],
               "d_fsc_model_post": post["d_fsc_model_masked"],
               "d_fsc_model_reliable": pre["d_fsc_model_plausible"]
                                       and post["d_fsc_model_plausible"]}
        if (pre["d_fsc_model_plausible"] and post["d_fsc_model_plausible"]):
            row["d_fsc_model_delta"] = round(
                post["d_fsc_model_masked"] - pre["d_fsc_model_masked"], 4)
        rows.append(row)
        print(f"  CC_mask {pre['cc_mask']}→{post['cc_mask']} (Δ {row['cc_mask_delta']:+.4f})"
              f" | d_FSC_model {pre['d_fsc_model_masked']}→{post['d_fsc_model_masked']}",
              file=sys.stderr)
    return rows, skipped


def summarize(rows: list[dict]) -> dict[str, Any]:
    """Δ distributions against the asserted bands."""
    if not rows:
        return {"n": 0}

    def stats(key: str) -> dict[str, Any]:
        values = [r[key] for r in rows if r.get(key) is not None]
        if not values:
            return {"n": 0}
        return {"n": len(values), "median": round(statistics.median(values), 4),
                "min": round(min(values), 4), "max": round(max(values), 4)}

    return {
        "n_entries": len(rows),
        "cc_mask_delta": stats("cc_mask_delta"),
        "d_fsc_model_delta": stats("d_fsc_model_delta"),
        "n_d_fsc_model_reliable": sum(1 for r in rows if r.get("d_fsc_model_reliable")),
        "asserted_bands": {"cc_mask": "post >= pre - 0.01", "d_fsc_model": "post <= pre + 0.05"},
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

    rows, skipped = collect(entries, cache)
    summary = summarize(rows)
    if args.json_out:
        Path(args.json_out).write_text(
            json.dumps({"rows": rows, "skipped": skipped, "summary": summary}, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    return 0 if rows else 1


if __name__ == "__main__":
    raise SystemExit(main())
