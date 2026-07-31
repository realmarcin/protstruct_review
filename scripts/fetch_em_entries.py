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
import os
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


def entry_metadata(pdb_id: str) -> tuple[float | None, str | None, str]:
    """(resolution, EMDB accession digits, publication key) for one entry.

    The publication key exists because a resolution window does not sample
    independent depositions. Round 15 pulled 10 entries in 3.0-4.0 A and got two
    3-entry series (one protein at three conformations; one kinetochore paper's three
    complexes) -- 10 entries, 6 independent units. The historical set is worse: 22
    entries came from 12 publications, and the four largest CC_mask degradations ever
    recorded came from just TWO papers, in near-duplicate pairs (9UPM -0.0475 with
    9UPO -0.0402; 10SD -0.0421 with 10SF -0.0371).

    That matters because a null-refinement Delta is a property of the model, the map
    and the depositor's protocol together. Two entries from one paper share all three,
    so they are close to one observation counted twice -- and the two tightest pairs
    in the set (myoglobin fibrils, spread 0.0005; spectral tuning, spread 0.0073) are
    exactly the pairs that anchor the bands.

    DOI is preferred over title: the same study can vary its title string across
    entries, but the DOI is a stable identifier. Unpublished entries fall back to
    their own id, which keeps them independent rather than silently merging them.
    """
    raw = _get(RCSB_ENTRY.format(pdb_id=pdb_id.upper()), timeout=120)
    if raw is None:
        return None, None, ""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None, None, ""
    resolutions = data.get("rcsb_entry_info", {}).get("resolution_combined") or []
    resolution = float(resolutions[0]) if resolutions else None
    accession = None
    for related in data.get("rcsb_entry_container_identifiers", {}).get(
            "emdb_ids", []) or []:
        accession = related.split("-")[-1]      # "EMD-12345" -> "12345"
        break
    citation = data.get("rcsb_primary_citation") or {}
    pub_key = (citation.get("pdbx_database_id_DOI")
               or citation.get("title")
               or f"unpublished:{pdb_id.upper()}")
    return resolution, accession, pub_key


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


# PHENIX aborts `map_correlations` with "The model contains atoms which are not in the
# scattering table 'electron'" on entries carrying formal charges. The mechanism is
# read from cctbx rather than guessed: the electron table
# (`cctbx.eltbx.e_scattering.ito_vol_c_2011_table_4_3_2_2_elements`) holds **98 neutral
# elements and no ions at all** -- there is no O1-, N1+, or Fe3+ entry to find.
#
# Empirically 10EN and 10FL both failed here and both carry charges (10FL: 264 O1-,
# 252 N1+), while every entry that processed cleanly carries none. PHENIX names only
# the ANION in its message, so anions are the confirmed fatal case; whether cations
# alone would abort is untested, and this screen therefore refuses on a negative
# charge and merely reports positive ones.
#
# Screening happens before the map download because a map is 200-300 MB and the model
# is ~1 MB: the whole cost of this failure is avoidable.
def charge_screen(model: Path) -> tuple[str | None, dict[str, int]]:
    """(refusal reason, charge inventory) for a model, via gemmi.

    Returns (None, inventory) when the model is usable. The inventory is returned
    either way so a caller can record what was seen rather than only what was fatal.
    """
    try:
        import gemmi
        structure = gemmi.read_structure(str(model))
    except Exception as exc:                     # unreadable model: not a charge problem
        return None, {"unreadable": 1, "error": str(exc)[:40]}
    counts: dict[str, int] = {}
    for mdl in structure:
        for chain in mdl:
            for residue in chain:
                for atom in residue:
                    if atom.charge:
                        sign = "+" if atom.charge > 0 else "-"
                        key = f"{atom.element.name}{abs(atom.charge)}{sign}"
                        counts[key] = counts.get(key, 0) + 1
    anions = {k: v for k, v in counts.items() if k.endswith("-")}
    if anions:
        named = ", ".join(f"{k}×{v}" for k, v in sorted(anions.items()))
        return (f"formal charges absent from the electron scattering table: {named}",
                counts)
    return None, counts


# `real_space_refine` aborts on a residue it has no restraints for, reporting "Number
# of atoms with unknown nonbonded energy type symbols: N". That was 3 of the 6 skips
# across rounds 14-16, and unlike the charge case it cost a model download, a 200-300 MB
# map download and a refinement attempt before failing -- all of it avoidable, because
# whether a component has restraints is a property of the model alone.
#
# PHENIX resolves restraints from two libraries shipped under `chem_data`: GeoStd
# (`geostd/<c>/data_<CODE>.cif`, ~44 000 components) and the CCP4 monomer library
# (`mon_lib/<c>/<CODE>.cif`, ~220). A component in neither has no restraints.
#
# Standard polymer residues are exempted via gemmi's own residue table rather than a
# hand-written list, because they are NOT in either library under their PDB names --
# DT, DA, DC and DG are all absent, and cctbx resolves them through a separate
# nucleic-acid path. Checking file existence alone therefore flags every DNA chain,
# which on 28JV means 1431 atoms instead of the 38 that actually failed.
#
# VALIDATED AGAINST THE AUTHORITATIVE CODE PATH. This screen is a reimplementation, so
# it was checked against `phenix.pdb_interpretation` -- the same cctbx interpretation
# `real_space_refine` runs -- over all 37 cached models from rounds 14-16. The two
# agree on every model, including the exact atom counts on the three known failures
# (11MR 128, 10EG 195, 28JV 38) and on four never-benchmarked entries (10GJ/GK/GL/GM,
# 23 each). Zero disagreements. Re-run that comparison if the screen is ever changed:
# an in-repo reimplementation that silently drifts from the tool it stands in for is
# worse than no screen, because it rejects entries that would have refined.
CHEM_DATA_GLOB = "phenix-2.0-5936/lib/python3*/site-packages/chem_data"


def _monomer_libraries() -> tuple[Path, Path] | None:
    """(geostd, mon_lib) roots, or None if PHENIX is not installed here."""
    root = Path(os.environ["PHENIX"]) if os.environ.get("PHENIX") else None
    candidates = [root / "lib"] if root else []
    for chem_data in list(Path.home().glob(CHEM_DATA_GLOB)) + candidates:
        geostd, mon_lib = chem_data / "geostd", chem_data / "mon_lib"
        if geostd.is_dir() and mon_lib.is_dir():
            return geostd, mon_lib
    return None


def ligand_screen(model: Path) -> tuple[str | None, dict[str, int]]:
    """(refusal reason, {component: atom count}) for components with no restraints.

    Returns (None, {}) when the model is usable. When PHENIX's libraries cannot be
    found the screen is **skipped rather than guessed** — refusing an entry on a
    library that is not there would drop good entries silently.
    """
    libs = _monomer_libraries()
    if libs is None:
        return None, {}
    geostd, mon_lib = libs
    try:
        import gemmi
        structure = gemmi.read_structure(str(model))
    except Exception:                 # unreadable model: not a restraint problem
        return None, {}

    def parameterised(code: str) -> bool:
        code = code.strip().upper()
        if not code:
            return True
        try:
            info = gemmi.find_tabulated_residue(code)
            if info is not None and info.is_standard():
                return True
        except Exception:
            pass
        bucket = code[0].lower()
        return ((geostd / bucket / f"data_{code}.cif").exists()
                or (mon_lib / bucket / f"{code}.cif").exists())

    missing: dict[str, int] = {}
    for chain in structure[0] if len(structure) else []:
        for residue in chain:
            if not parameterised(residue.name):
                missing[residue.name] = missing.get(residue.name, 0) + len(residue)
    if missing:
        total = sum(missing.values())
        named = ", ".join(f"{k}×{v}" for k, v in sorted(missing.items()))
        return (f"unparameterised ligand: {total} atoms with no monomer-library "
                f"restraints ({named})", missing)
    return None, missing


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


def collect(pdb_ids: list[str], cache: Path, max_map_mb: float, max_model_mb: float,
            seen_pubs: set[str] | None = None,
            max_per_pub: int = 0) -> tuple[list[dict], list[dict]]:
    """Fetch entries, keeping at most `max_per_pub` from any one publication.

    `max_per_pub=0` means no limit, and that is the default **because the limit was
    tested and did not earn its place**. Round 15 keyed this on citation DOI after
    noticing that 22 historical entries came from 12 publications, with the four
    largest CC_mask degradations arriving as two same-paper pairs. Two registered
    predictions then tested whether cluster-mates actually behave alike:

        P5  peptidase, ONE protein: 10EQ +0.0603, 10ET -0.0351, 10EO -0.0221
        P6  kinetochore, one paper: 10EH +0.1268, 10DQ +0.0151

    Both failed, P5 with opposite signs on the same protein. A permutation test over
    every labelled entry then put it beyond doubt: within-cluster pairs differ by a
    mean 0.0318 against 0.0354 between clusters, ratio 0.897, **p = 0.38**. Shared
    publication -- and even shared protein -- does not predict a similar null Delta.
    The tight historical pairs (myoglobin 0.0005) were coincidence among 21
    within-cluster pairs.

    The key is still computed and recorded on every entry, because knowing the
    provenance is useful, and a future round may find it predicts something else. It
    just no longer filters anything unless asked.
    """
    cache.mkdir(parents=True, exist_ok=True)
    pub_counts: dict[str, int] = {}
    if seen_pubs and max_per_pub:
        pub_counts = {k: max_per_pub for k in seen_pubs}
    entries, skipped = [], []
    for pdb_id in pdb_ids:
        print(f"[{pdb_id}]", file=sys.stderr)
        resolution, accession, pub_key = entry_metadata(pdb_id)
        if resolution is None or accession is None:
            skipped.append({"pdb_id": pdb_id, "reason": "no resolution or EMDB accession"})
            continue
        if max_per_pub and pub_counts.get(pub_key, 0) >= max_per_pub:
            reason = f"publication already represented ({pub_key})"
            skipped.append({"pdb_id": pdb_id, "reason": reason})
            print(f"  ! {reason}", file=sys.stderr)
            continue
        model, reason = fetch_model(pdb_id, cache, max_model_mb)
        if model is None:
            skipped.append({"pdb_id": pdb_id, "reason": reason})
            print(f"  ! {reason}", file=sys.stderr)
            continue
        charge_reason, charges = charge_screen(model)
        if charge_reason is not None:
            skipped.append({"pdb_id": pdb_id, "reason": charge_reason,
                            "charges": charges})
            print(f"  ! {charge_reason}", file=sys.stderr)
            model.unlink(missing_ok=True)
            continue
        ligand_reason, unparameterised = ligand_screen(model)
        if ligand_reason is not None:
            skipped.append({"pdb_id": pdb_id, "reason": ligand_reason,
                            "unparameterised": unparameterised})
            print(f"  ! {ligand_reason}", file=sys.stderr)
            model.unlink(missing_ok=True)
            continue
        map_file, reason = fetch_map(pdb_id, accession, cache, max_map_mb)
        if map_file is None:
            skipped.append({"pdb_id": pdb_id, "reason": reason})
            print(f"  ! {reason}", file=sys.stderr)
            continue
        pub_counts[pub_key] = pub_counts.get(pub_key, 0) + 1
        entries.append({"pdb_id": pdb_id, "resolution": resolution,
                        "emdb": f"EMD-{accession}", "publication": pub_key,
                        "charges": charges or None})
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
    ap.add_argument("--max-per-pub", type=int, default=0,
                    help="entries to keep from any one publication (0 = no limit, the "
                         "default: clustering was tested and does not predict a "
                         "similar null delta, permutation p = 0.38)")
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
    seen_pubs: set[str] = set()
    pub_counts: dict[str, int] = {}
    for pdb_id in candidates:
        if len(entries) >= args.limit:
            break
        got, miss = collect([pdb_id], cache, args.max_map_mb, args.max_model_mb,
                            seen_pubs=seen_pubs, max_per_pub=args.max_per_pub)
        for row in got:
            key = row["publication"]
            pub_counts[key] = pub_counts.get(key, 0) + 1
            if args.max_per_pub and pub_counts[key] >= args.max_per_pub:
                seen_pubs.add(key)
        entries.extend(got)
        skipped.extend(miss)

    (cache / "entries.json").write_text(json.dumps(entries, indent=2) + "\n")
    report = {"entries": entries, "skipped": skipped,
              "window": [args.min_res, args.max_res], "excluded": sorted(exclude),
              "n_publications": len({e["publication"] for e in entries})}
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"n_entries": len(entries), "n_skipped": len(skipped),
                      "n_publications": report["n_publications"]}, indent=2))
    return 0 if entries else 1


if __name__ == "__main__":
    raise SystemExit(main())
