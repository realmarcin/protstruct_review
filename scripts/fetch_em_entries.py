#!/usr/bin/env python3
"""Populate a cryo-EM benchmark cache for `bench_refinement_deltas_em.py`.

Rounds 5 and 9-13 built their EM caches by hand, in a temporary directory. That made
every EM result in `ref/research/` unreproducible from a clean checkout the moment the
directory was cleared - which is exactly what happened before round 14. This script is
the missing half of that benchmark: given a resolution window, it selects entries,
downloads the model and its primary EMDB map, and writes the `entries.json` the
benchmark reads.

Selection is by **query, not by hand**, so a later round can reproduce or extend a set
by re-running with the same window rather than trusting a list transcribed into prose.

  - RCSB search API -> PDB entries with `ELECTRON MICROSCOPY` in a resolution range,
    each with an associated EMDB accession.
  - RCSB -> `<pdb_id>.cif` (the deposited model).
  - EMDB -> `emd_NNNNN.map.gz` (the primary map), decompressed to `<pdb_id>.map`.

Entries whose map is missing, gzip-truncated, or larger than `--max-map-mb` are
skipped and reported: `real_space_refine` on a multi-GB map takes hours and would
dominate a round without adding a distinct resolution point.

Usage:
    python3 scripts/fetch_em_entries.py --cache DIR --min-res 2.4 --max-res 3.2 \
        --limit 8 --exclude 9O9K,21BQ --json fetched.json
"""
from __future__ import annotations

import argparse
import gzip
import json
import shutil
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

RCSB_SEARCH = "https://search.rcsb.org/rcsbsearch/v2/query"
RCSB_MODEL = "https://files.rcsb.org/download/{pdb_id}.cif"
RCSB_ENTRY = "https://data.rcsb.org/rest/v1/core/entry/{pdb_id}"
EMDB_MAP = "https://ftp.ebi.ac.uk/pub/databases/emdb/structures/EMD-{acc}/map/emd_{acc}.map.gz"

DEFAULT_MAX_MAP_MB = 400.0
DEFAULT_MAX_MODEL_MB = 8.0


def _get(url: str, timeout: int = 300) -> bytes | None:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return r.read()
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
        return None


def search(min_res: float, max_res: float, limit: int) -> list[str]:
    """PDB ids for cryo-EM entries in a resolution window, best-resolution first."""
    query = {
        "query": {
            "type": "group", "logical_operator": "and", "nodes": [
                {"type": "terminal", "service": "text", "parameters": {
                    "attribute": "exptl.method", "operator": "exact_match",
                    "value": "ELECTRON MICROSCOPY"}},
                {"type": "terminal", "service": "text", "parameters": {
                    "attribute": "rcsb_entry_info.resolution_combined",
                    "operator": "range",
                    "value": {"from": min_res, "to": max_res,
                              "include_lower": True, "include_upper": True}}},
            ],
        },
        "return_type": "entry",
        "request_options": {
            "paginate": {"start": 0, "rows": limit},
            "sort": [{"sort_by": "rcsb_entry_info.resolution_combined",
                      "direction": "asc"}],
        },
    }
    req = urllib.request.Request(
        RCSB_SEARCH, data=json.dumps(query).encode(),
        headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            payload = json.load(r)
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError,
            json.JSONDecodeError):
        return []
    return [hit["identifier"].upper() for hit in payload.get("result_set", [])]


def stratified_search(min_res: float, max_res: float, strata: int,
                      per_stratum: int) -> list[str]:
    """Sample candidates evenly across a resolution window.

    A single sorted query does not do this. Asking for the 40 best-resolution entries
    in 2.4-3.2 Å returns 40 entries at **2.40 Å** — the PDB holds far more structures
    at the fine end of any window than the coarse end, so an ascending sort collapses
    the whole range onto its lower bound. Sorting descending has the same failure at
    the other edge, and sorting by release date samples whatever was deposited most
    recently, which is uncorrelated with resolution.

    Splitting the window into equal sub-bands and querying each one separately is the
    only form here that actually spans the range — which matters because the tolerance
    under test is *resolution-conditional*, so a set clustered at one resolution
    cannot test it.

    Returned round-robin across strata, so a caller that stops early at `--limit`
    still gets a spread rather than the contents of the first band.
    """
    width = (max_res - min_res) / strata
    per_band: list[list[str]] = []
    for i in range(strata):
        lo = min_res + i * width
        hi = min_res + (i + 1) * width
        hits = search(lo, hi, per_stratum)
        print(f"  {lo:.2f}-{hi:.2f} Å: {len(hits)} candidates", file=sys.stderr)
        per_band.append(hits)
    ordered = []
    for rank in range(max(len(b) for b in per_band) if per_band else 0):
        for band in per_band:
            if rank < len(band):
                ordered.append(band[rank])
    return ordered


def entry_metadata(pdb_id: str) -> tuple[float | None, str | None]:
    """(resolution, EMDB accession digits) for one entry."""
    raw = _get(RCSB_ENTRY.format(pdb_id=pdb_id.upper()), timeout=120)
    if raw is None:
        return None, None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None, None
    resolutions = data.get("rcsb_entry_info", {}).get("resolution_combined") or []
    resolution = float(resolutions[0]) if resolutions else None
    accession = None
    for related in data.get("rcsb_entry_container_identifiers", {}).get(
            "emdb_ids", []) or []:
        accession = related.split("-")[-1]      # "EMD-12345" -> "12345"
        break
    return resolution, accession


def fetch_model(pdb_id: str, cache: Path,
                max_model_mb: float) -> tuple[Path | None, str | None]:
    """Download the deposited model. Returns (path, skip_reason).

    Size-capped for the same reason as the map, but the threshold is much lower: model
    size drives `real_space_refine` cost far harder than map size does. A 28 MB mmCIF
    is a ribosome-scale assembly whose refinement runs for hours and contributes one
    resolution point, the same as a 1 MB entry.
    """
    dest = cache / f"{pdb_id.lower()}.cif"
    if dest.exists() and dest.stat().st_size:
        return dest, None
    raw = _get(RCSB_MODEL.format(pdb_id=pdb_id.upper()))
    if raw is None:
        return None, "model not retrievable"
    size_mb = len(raw) / 1e6
    if size_mb > max_model_mb:
        return None, f"model {size_mb:.0f} MB exceeds --max-model-mb {max_model_mb:.0f}"
    dest.write_bytes(raw)
    return dest, None


def fetch_map(pdb_id: str, accession: str, cache: Path,
              max_map_mb: float) -> tuple[Path | None, str | None]:
    """Download and decompress the primary EMDB map. Returns (path, skip_reason)."""
    dest = cache / f"{pdb_id.lower()}.map"
    if dest.exists() and dest.stat().st_size:
        return dest, None
    gz = cache / f"emd_{accession}.map.gz"
    if not (gz.exists() and gz.stat().st_size):
        raw = _get(EMDB_MAP.format(acc=accession), timeout=1800)
        if raw is None:
            return None, f"EMDB map EMD-{accession} not retrievable"
        gz.write_bytes(raw)
    size_mb = gz.stat().st_size / 1e6
    if size_mb > max_map_mb:
        gz.unlink()
        return None, f"map {size_mb:.0f} MB exceeds --max-map-mb {max_map_mb:.0f}"
    try:
        with gzip.open(gz, "rb") as src, dest.open("wb") as out:
            shutil.copyfileobj(src, out)
    except (OSError, EOFError) as exc:          # truncated download
        dest.unlink(missing_ok=True)
        return None, f"map decompression failed: {exc}"
    finally:
        gz.unlink(missing_ok=True)
    return dest, None


def collect(pdb_ids: list[str], cache: Path, max_map_mb: float,
            max_model_mb: float) -> tuple[list[dict], list[dict]]:
    cache.mkdir(parents=True, exist_ok=True)
    entries, skipped = [], []
    for pdb_id in pdb_ids:
        print(f"[{pdb_id}]", file=sys.stderr)
        resolution, accession = entry_metadata(pdb_id)
        if resolution is None or accession is None:
            skipped.append({"pdb_id": pdb_id, "reason": "no resolution or EMDB accession"})
            continue
        model, reason = fetch_model(pdb_id, cache, max_model_mb)
        if model is None:
            skipped.append({"pdb_id": pdb_id, "reason": reason})
            print(f"  ! {reason}", file=sys.stderr)
            continue
        map_file, reason = fetch_map(pdb_id, accession, cache, max_map_mb)
        if map_file is None:
            skipped.append({"pdb_id": pdb_id, "reason": reason})
            print(f"  ! {reason}", file=sys.stderr)
            continue
        entries.append({"pdb_id": pdb_id, "resolution": resolution,
                        "emdb": f"EMD-{accession}"})
        print(f"  {resolution} Å, EMD-{accession}, "
              f"{map_file.stat().st_size / 1e6:.0f} MB", file=sys.stderr)
    return entries, skipped


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cache", required=True)
    ap.add_argument("--min-res", type=float, default=2.4)
    ap.add_argument("--max-res", type=float, default=3.2)
    ap.add_argument("--limit", type=int, default=8, help="entries to keep")
    ap.add_argument("--strata", type=int, default=8,
                    help="equal resolution sub-bands to sample across the window; "
                         "a single sorted query collapses onto one edge")
    ap.add_argument("--per-stratum", type=int, default=6,
                    help="candidates to pull from each sub-band")
    ap.add_argument("--max-model-mb", type=float, default=DEFAULT_MAX_MODEL_MB,
                    help="skip models larger than this; model size drives refinement "
                         "cost harder than map size")
    ap.add_argument("--max-map-mb", type=float, default=DEFAULT_MAX_MAP_MB,
                    help="skip maps larger than this; real_space_refine on a multi-GB "
                         "map takes hours without adding a resolution point")
    ap.add_argument("--exclude", default="",
                    help="comma-separated PDB ids already in the benchmark set")
    ap.add_argument("--ids", default="", help="explicit ids, bypassing the search")
    ap.add_argument("--json", dest="json_out")
    args = ap.parse_args()

    exclude = {i.strip().upper() for i in args.exclude.split(",") if i.strip()}
    if args.ids:
        candidates = [i.strip().upper() for i in args.ids.split(",") if i.strip()]
    else:
        candidates = stratified_search(args.min_res, args.max_res,
                                       args.strata, args.per_stratum)
        if not candidates:
            print("search returned nothing", file=sys.stderr)
            return 1
    candidates = [c for c in candidates if c not in exclude]

    cache = Path(args.cache)
    entries: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    for pdb_id in candidates:
        if len(entries) >= args.limit:
            break
        got, miss = collect([pdb_id], cache, args.max_map_mb, args.max_model_mb)
        entries.extend(got)
        skipped.extend(miss)

    (cache / "entries.json").write_text(json.dumps(entries, indent=2) + "\n")
    report = {"entries": entries, "skipped": skipped,
              "window": [args.min_res, args.max_res], "excluded": sorted(exclude)}
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"n_entries": len(entries), "n_skipped": len(skipped)}, indent=2))
    return 0 if entries else 1


if __name__ == "__main__":
    raise SystemExit(main())
