#!/usr/bin/env python3
"""Round-1 representative selection for the negative-control enrollment screen.

Executes D2, D4 and D7 of `negative_control_round1_preregistration.md`, and nothing
of its own invention: the criteria, the ranking rule, and the draw are all quoted
from the registered document. The output JSON is the committed record the screen
(`screen_round1.py`) consumes, including each cluster's FULL ranked member list so
a D4 within-cluster replacement is a lookup, not a new query.

D2 criteria: X-ray, d_min <= 1.0 A, structure factors released, >= 1 protein
entity, clashscore <= 2, Ramachandran outliers <= 0.5 %, rotamer outliers
<= 1.0 %, reported R-free <= 0.18.

D4 rank within a cluster: best d_min, then lower clashscore, then lower reported
R-free, then lexicographic id. Missing values rank last (a tie-break that cannot
be read must not win one).

D7 draw: 20 spread across the <= 0.9 A stratum's d_min-sorted cluster list —
spread per `select_gold_standards.spread_sample`, imported, not re-implemented —
plus 10 from (0.9, 1.0] by ascending representative d_min. A cluster is in the
stratum iff its representative's d_min is <= 0.9 (equivalent to any-member, since
the representative has the cluster's best d_min).

Usage:
    python3 scripts/select_round1_reps.py --json ref/research/data/negative_control_round1_reps.json
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
RCSB_SEARCH = "https://search.rcsb.org/rcsbsearch/v2/query"
RCSB_GRAPHQL = "https://data.rcsb.org/graphql"

STRATUM_D_MIN = 0.9
N_STRATUM, N_BAND = 20, 10


def _load(name: str):
    spec = importlib.util.spec_from_file_location(
        name, REPO / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# The D2 pool is the phase-0 query machinery with the registered relaxed cuts; the
# spread is the exact function the preregistration names. Imported so a drift
# between this script and the registered text is a diff, not a divergence.
_sg = _load("select_gold_standards")
spread_sample = _sg.spread_sample

D2_NODES = [
    {"type": "terminal", "service": "text", "parameters": {
        "attribute": "exptl.method", "operator": "exact_match",
        "value": "X-RAY DIFFRACTION"}},
    {"type": "terminal", "service": "text", "parameters": {
        "attribute": _sg.RES_ATTR, "operator": "range",
        "value": {"to": 1.0, "include_upper": True}}},
    {"type": "terminal", "service": "text", "parameters": {
        "attribute": "rcsb_accession_info.has_released_experimental_data",
        "operator": "exact_match", "value": "Y"}},
    {"type": "terminal", "service": "text", "parameters": {
        "attribute": "rcsb_entry_info.polymer_entity_count_protein",
        "operator": "range", "value": {"from": 1, "include_lower": True}}},
    {"type": "terminal", "service": "text", "parameters": {
        "attribute": "pdbx_vrpt_summary_geometry.clashscore",
        "operator": "range", "value": {"to": 2.0, "include_upper": True}}},
    {"type": "terminal", "service": "text", "parameters": {
        "attribute": "pdbx_vrpt_summary_geometry.percent_ramachandran_outliers",
        "operator": "range", "value": {"to": 0.5, "include_upper": True}}},
    {"type": "terminal", "service": "text", "parameters": {
        "attribute": "pdbx_vrpt_summary_geometry.percent_rotamer_outliers",
        "operator": "range", "value": {"to": 1.0, "include_upper": True}}},
    {"type": "terminal", "service": "text", "parameters": {
        "attribute": "refine.ls_R_factor_R_free",
        "operator": "range", "value": {"to": 0.18, "include_upper": True}}},
    {"type": "terminal", "service": "text", "parameters": {
        "attribute": "entity_poly.rcsb_entity_polymer_type",
        "operator": "exact_match", "value": "Protein"}},
]


def fetch_clusters(fetch=_sg._post) -> dict[str, list[str]]:
    """group_id -> member ENTRY ids (deduped), from the 30 %-identity grouping.

    Entities the clustering has no group for come back under synthetic singleton
    ids ("ungrouped:<entity>") — carried, not dropped, per the phase-0 convention.
    """
    clusters: dict[str, list[str]] = {}
    start = 0
    while True:
        payload = fetch({
            "query": {"type": "group", "logical_operator": "and",
                      "nodes": D2_NODES},
            "return_type": "polymer_entity",
            "request_options": {
                "group_by": {"aggregation_method": "sequence_identity",
                             "similarity_cutoff": 30},
                "group_by_return_type": "groups",
                "paginate": {"start": start, "rows": 100}}})
        groups = payload.get("group_set", [])
        for group in groups:
            members = [item["identifier"] for item in
                       group.get("result_set", [])]
            entries = []
            for entity_id in members:
                entry = entity_id.split("_")[0].upper()
                if entry not in entries:
                    entries.append(entry)
            clusters[str(group["identifier"])] = entries
        start += len(groups)
        if not groups or start >= payload.get("group_by_count", 0):
            break

    # Entities the clustering has no group for do NOT appear in group_set (the
    # canary showed ungrouped_count > 0 with no matching groups). Fetch the whole
    # pool and give each missing entity a singleton cluster — carried, not
    # dropped, per the phase-0 convention.
    grouped_entities = {m for g in clusters.values() for m in g}
    start = 0
    while True:
        payload = fetch({
            "query": {"type": "group", "logical_operator": "and",
                      "nodes": D2_NODES},
            "return_type": "polymer_entity",
            "request_options": {"paginate": {"start": start, "rows": 1000}}})
        hits = [h["identifier"] for h in payload.get("result_set", [])]
        for entity_id in hits:
            entry = entity_id.split("_")[0].upper()
            if entry not in grouped_entities and \
                    not any(entry in v for v in clusters.values()):
                clusters[f"ungrouped:{entity_id}"] = [entry]
        start += len(hits)
        if not hits or start >= payload.get("total_count", 0):
            break
    return clusters


def fetch_entry_data(entry_ids: list[str], chunk: int = 200) -> dict[str, dict]:
    """d_min / clashscore / R-free / deposit year per entry, batched GraphQL."""
    out: dict[str, dict] = {}
    for i in range(0, len(entry_ids), chunk):
        ids = entry_ids[i:i + chunk]
        query = ("{ entries(entry_ids: [" +
                 ",".join(f'"{e}"' for e in ids) + "]) { rcsb_id "
                 "rcsb_entry_info { diffrn_resolution_high { value } } "
                 "pdbx_vrpt_summary_geometry { clashscore } "
                 "refine { ls_R_factor_R_free } "
                 "rcsb_accession_info { deposit_date } } }")
        req = urllib.request.Request(
            RCSB_GRAPHQL, data=json.dumps({"query": query}).encode(),
            headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                payload = json.load(r)
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError,
                json.JSONDecodeError) as exc:
            raise SystemExit(f"select_round1: GraphQL failed: {exc}")
        for entry in payload.get("data", {}).get("entries", []) or []:
            info = entry.get("rcsb_entry_info") or {}
            vrpt = (entry.get("pdbx_vrpt_summary_geometry") or [{}])[0] or {}
            refine = (entry.get("refine") or [{}])[0] or {}
            acc = entry.get("rcsb_accession_info") or {}
            out[entry["rcsb_id"].upper()] = {
                "d_min": (info.get("diffrn_resolution_high") or {}).get("value"),
                "clashscore": vrpt.get("clashscore"),
                "r_free_reported": refine.get("ls_R_factor_R_free"),
                "deposit_year": int(acc["deposit_date"][:4])
                if acc.get("deposit_date") else None,
            }
    return out


def d4_rank_key(entry: dict) -> tuple:
    """D4: best d_min, then clashscore, then reported R-free, then id.
    Missing values rank last."""
    inf = float("inf")
    return (entry["d_min"] if entry["d_min"] is not None else inf,
            entry["clashscore"] if entry["clashscore"] is not None else inf,
            entry["r_free_reported"] if entry["r_free_reported"] is not None
            else inf,
            entry["pdb_id"])


def rank_clusters(clusters: dict[str, list[str]],
                  data: dict[str, dict]) -> list[dict]:
    """One record per cluster: D4-ranked members, representative first."""
    ranked = []
    for group_id, entries in clusters.items():
        members = [{"pdb_id": e, **data.get(e, {"d_min": None, "clashscore": None,
                                               "r_free_reported": None,
                                               "deposit_year": None})}
                   for e in entries]
        members.sort(key=d4_rank_key)
        ranked.append({"cluster": group_id, "members": members})
    return ranked


def d7_draw(ranked: list[dict]) -> tuple[list[dict], list[dict], list[dict]]:
    """(stratum_clusters_sorted, band_clusters_sorted, initial_30). The draw is
    over CLUSTERS; each contributes its D4 representative."""
    def rep_d_min(cluster):
        d = cluster["members"][0]["d_min"]
        return d if d is not None else float("inf")

    stratum = sorted((c for c in ranked if rep_d_min(c) <= STRATUM_D_MIN),
                     key=lambda c: (rep_d_min(c), c["cluster"]))
    band = sorted((c for c in ranked
                   if STRATUM_D_MIN < rep_d_min(c) <= 1.0),
                  key=lambda c: (rep_d_min(c), c["cluster"]))
    drawn = spread_sample(stratum, N_STRATUM) + band[:N_BAND]
    initial = [{"cluster": c["cluster"],
                "stratum": rep_d_min(c) <= STRATUM_D_MIN,
                **c["members"][0]} for c in drawn]
    return stratum, band, initial


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", dest="json_out",
                    default="ref/research/data/negative_control_round1_reps.json")
    args = ap.parse_args()

    clusters = fetch_clusters()
    print(f"clusters (incl. ungrouped singletons): {len(clusters)}",
          file=sys.stderr)
    all_entries = sorted({e for members in clusters.values() for e in members})
    data = fetch_entry_data(all_entries)
    missing = [e for e in all_entries if e not in data]
    if missing:
        print(f"  ! {len(missing)} entries missing from GraphQL: "
              f"{missing[:5]}...", file=sys.stderr)

    ranked = rank_clusters(clusters, data)
    stratum, band, initial = d7_draw(ranked)
    print(f"stratum clusters (<= {STRATUM_D_MIN} A): {len(stratum)}; "
          f"band clusters: {len(band)}; drawn: {len(initial)}", file=sys.stderr)

    report = {"criteria": "D2 of negative_control_round1_preregistration.md",
              "stratum_d_min": STRATUM_D_MIN,
              "n_clusters": len(clusters),
              "n_stratum_clusters": len(stratum),
              "n_band_clusters": len(band),
              "initial_representatives": initial,
              "clusters": ranked}
    Path(args.json_out).write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"initial": [r["pdb_id"] for r in initial]}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
