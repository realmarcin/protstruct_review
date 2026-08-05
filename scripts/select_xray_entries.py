#!/usr/bin/env python3
"""Select X-ray entries by QUERY for the §4 refinement benchmark.

This is the missing half of `bench_refinement_deltas.py`, and the reason its set was
never pinned. That script's own comment says so:

    `find_pairs()` globs whatever `<id>.pdb` + `<id>_g_obs.mtz` sit in `--cache`, which
    is why the set was never pinned in the first place: the script's input was a
    directory someone had populated by hand.

`fetch_em_entries.py` closed exactly this gap for cryo-EM. The X-ray side never got the
same treatment, which is how the ~11 entries producing BOTH quoted low-resolution null
maxima (0.285 Å and 5.26 pp) came to be named nowhere -- `SET_SHORTFALL` in
`bench_refinement_deltas.py` records the loss but nothing could prevent a repeat.

WHICH RESOLUTION ATTRIBUTE, AND WHY IT MATTERS (#238)
-----------------------------------------------------
Do NOT select on `rcsb_entry_info.resolution_combined`. For X-ray it is an ARRAY, and a
range query matches if ANY element falls in the window. Queried at 2.5-3.2 A, 12 of the
first 12 hits were multi-valued and 9 of 12 had a primary refinement resolution outside
the window -- including 3VXF, selected as low-resolution while its header reads
`REMARK 2 RESOLUTION. 1.60 ANGSTROMS`.

`rcsb_entry_info.diffrn_resolution_high.value` is scalar and agrees with the header and
with every downstream script. Verified: 12 of 12 in-window on the same query.

Cryo-EM is unaffected -- all 14 round-35 EM entries carry a single-valued
`resolution_combined` -- which is why `fetch_em_entries.py` is left alone.

THE BRANCH THIS EXISTS TO FEED (#237)
--------------------------------------
The under-evidenced band is `d_min >= 2.5 A`, NOT below it. Both unrecoverable maxima
belong to that branch; the `< 2.5 A` branch's sizing case (43SK, 0.1011 A) is named and
was re-measured by round 20. The default window reflects that.

Selection is by query, so a later round reproduces or extends the set by re-running with
the same window rather than trusting a list transcribed into prose.

Usage:
    python3 scripts/select_xray_entries.py --min-res 2.5 --max-res 3.2 --limit 20
    python3 scripts/select_xray_entries.py --limit 20 --exclude 12LO,37AP --json sel.json
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
RCSB_SEARCH = "https://search.rcsb.org/rcsbsearch/v2/query"
RCSB_ENTRY = "https://data.rcsb.org/rest/v1/core/entry/{pdb_id}"

# Scalar, matches the PDB header, and the reason for it is in the module docstring.
RES_ATTR = "rcsb_entry_info.diffrn_resolution_high.value"

# The set bench_refinement_deltas.py can still name, so a fresh selection does not
# silently re-measure entries already on record. Imported rather than retyped.
def known_ids() -> set[str]:
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "bench_rd", REPO / "scripts" / "bench_refinement_deltas.py")
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
        return {i.upper() for i in getattr(module, "DEFAULT_SET", [])}
    except Exception:
        # Failing closed here would block selection entirely; failing OPEN risks a
        # duplicate, which the caller can see in the output. Named, not silent.
        print("select_xray: could not import DEFAULT_SET; no ids excluded by default",
              file=sys.stderr)
        return set()


def search(min_res: float, max_res: float, rows: int) -> list[str]:
    """X-ray entries with RELEASED structure factors in a d_min window."""
    query = {
        "query": {"type": "group", "logical_operator": "and", "nodes": [
            {"type": "terminal", "service": "text", "parameters": {
                "attribute": "exptl.method", "operator": "exact_match",
                "value": "X-RAY DIFFRACTION"}},
            {"type": "terminal", "service": "text", "parameters": {
                "attribute": RES_ATTR, "operator": "range",
                "value": {"from": min_res, "to": max_res,
                          "include_lower": True, "include_upper": True}}},
            # Without this the entry has no structure factors and cannot be re-refined
            # at all -- a cheap filter that removes an expensive dead end.
            {"type": "terminal", "service": "text", "parameters": {
                "attribute": "rcsb_accession_info.has_released_experimental_data",
                "operator": "exact_match", "value": "Y"}},
        ]},
        "return_type": "entry",
        "request_options": {"paginate": {"start": 0, "rows": rows},
                            "sort": [{"sort_by": RES_ATTR, "direction": "asc"}]},
    }
    req = urllib.request.Request(RCSB_SEARCH, data=json.dumps(query).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            payload = json.load(r)
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError,
            json.JSONDecodeError) as exc:
        raise SystemExit(f"select_xray: RCSB search failed: {exc}")
    return [hit["identifier"].upper() for hit in payload.get("result_set", [])]


def stratified(min_res: float, max_res: float, strata: int, per: int) -> list[str]:
    """Round-robin across equal d_min sub-bands, so a truncated run stays spread.

    The ascending sort piles hits at the window's low edge -- at 2.5-3.2 A the first
    twelve were all exactly 2.5 A. Without stratification a `--limit 20` set would be
    twenty 2.5 A structures and would say nothing about 3 A.
    """
    width = (max_res - min_res) / strata
    buckets: list[list[str]] = []
    for i in range(strata):
        lo, hi = min_res + i * width, min_res + (i + 1) * width
        hits = search(lo, hi, per)
        print(f"  {lo:.2f}-{hi:.2f} A: {len(hits)} candidates", file=sys.stderr)
        buckets.append(hits)
    out: list[str] = []
    for i in range(per):
        for b in buckets:
            if i < len(b):
                out.append(b[i])
    return out


def verify(pdb_id: str, min_res: float, max_res: float) -> tuple[float | None, str | None]:
    """Re-check d_min against the ENTRY record, not the search index (#238).

    The search is trusted to find candidates and not trusted to have filtered them:
    this is the check that would have caught 3VXF.
    """
    try:
        with urllib.request.urlopen(RCSB_ENTRY.format(pdb_id=pdb_id), timeout=60) as r:
            data = json.load(r)
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError,
            json.JSONDecodeError):
        return None, "entry record not retrievable"
    info = data.get("rcsb_entry_info") or {}
    d_min = (info.get("diffrn_resolution_high") or {}).get("value")
    if d_min is None:
        refine = data.get("refine") or [{}]
        d_min = refine[0].get("ls_d_res_high") if refine else None
    if d_min is None:
        return None, "no d_min on the entry record"
    if not (min_res <= d_min <= max_res):
        return d_min, f"d_min {d_min} outside the requested {min_res}-{max_res}"
    return d_min, None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--min-res", type=float, default=2.5,
                    help="lower d_min bound (default 2.5, the under-evidenced branch)")
    ap.add_argument("--max-res", type=float, default=3.2)
    ap.add_argument("--strata", type=int, default=4)
    ap.add_argument("--per-stratum", type=int, default=25)
    ap.add_argument("--limit", type=int, default=20)
    ap.add_argument("--exclude", default="", help="extra ids, comma-separated")
    ap.add_argument("--json", dest="json_out")
    args = ap.parse_args()

    if args.min_res > args.max_res:
        raise SystemExit(f"select_xray: --min-res {args.min_res} exceeds "
                         f"--max-res {args.max_res}")

    excluded = known_ids() | {i.strip().upper() for i in args.exclude.split(",") if i.strip()}
    print(f"excluding {len(excluded)} ids already on record or named", file=sys.stderr)

    selected: list[dict] = []
    rejected: list[dict] = []
    for pdb_id in stratified(args.min_res, args.max_res, args.strata, args.per_stratum):
        if len(selected) >= args.limit:
            break
        if pdb_id in excluded:
            continue
        excluded.add(pdb_id)                       # never propose the same id twice
        d_min, reason = verify(pdb_id, args.min_res, args.max_res)
        if reason:
            rejected.append({"pdb_id": pdb_id, "d_min": d_min, "reason": reason})
            print(f"  ! {pdb_id}: {reason}", file=sys.stderr)
            continue
        selected.append({"pdb_id": pdb_id, "d_min": d_min})
        print(f"  {pdb_id}: d_min {d_min}", file=sys.stderr)

    report = {"selected": selected, "rejected": rejected,
              "window": [args.min_res, args.max_res], "attribute": RES_ATTR}
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"n_selected": len(selected), "n_rejected": len(rejected),
                      "ids": [e["pdb_id"] for e in selected]}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
