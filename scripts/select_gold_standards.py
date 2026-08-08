#!/usr/bin/env python3
"""Phase 0 of the negative-control benchmark: gold-standard feasibility scout (#295).

`ref/research/negative_control_benchmark_plan.md` proposes using near-perfect
structures as negative tests for refinement methods. Its first open question is
whether anything survives the curation: how many entries sit in each candidate
resolution window once validation cuts and redundancy clustering are applied, and
is the survivor pool diverse or a handful of lysozyme-likes? This script answers
exactly that and nothing more — it produces COUNTS for the window decision, not an
enrolled set. Enrollment criteria are preregistered at phase 2 (#297 records why
they must not be borrowed from scouting cuts).

WHAT THE TIERS ARE AND ARE NOT
------------------------------
The validation tiers below are scouting instruments: cheap, searchable proxies for
"top validation quality" used to size the pool. They are NOT the enrollment
criteria. Two of the plan's requirements are not searchable at all and are
deliberately deferred: residue-level masking (phase 1) and the empirical headroom
screen (phase 2). A count here is an upper bound on the enrollable pool.

WHAT WAS VERIFIED LIVE (2026-08-08)
-----------------------------------
- `pdbx_vrpt_summary_geometry.clashscore`, `.percent_ramachandran_outliers`,
  `.percent_rotamer_outliers` and `refine.ls_R_factor_R_free` are accepted as
  search attributes (rejected attributes make the API return an error, not zero
  hits — a typo fails loudly).
- `group_by` sequence-identity clustering at 30 % works with
  `return_type: polymer_entity` and reports `group_by_count` (clusters) plus
  `ungrouped_count` (entities the clustering could not place — reported, never
  silently dropped).
- The wwPDB percentile RANKS are absent from both the search and data APIs; only
  the validation XML carries them (`absolute-percentile-clashscore`, …). They are
  therefore harvested for a SAMPLE of survivors and reported as a sample.

Resolution attribute: `rcsb_entry_info.diffrn_resolution_high.value`, scalar, for
the #238 reason documented in `select_xray_entries.py` — `resolution_combined` is
an array for X-ray and range-matches on ANY element.

Usage:
    python3 scripts/select_gold_standards.py --json ref/research/data/negative_control_phase0_counts.json
    python3 scripts/select_gold_standards.py --windows 0.9,1.0 --xml-sample 6
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
RCSB_SEARCH = "https://search.rcsb.org/rcsbsearch/v2/query"
RCSB_ENTRY = "https://data.rcsb.org/rest/v1/core/entry/{pdb_id}"
VALIDATION_XML = "https://www.ebi.ac.uk/pdbe/entry-files/download/{pdb_id}_validation.xml"

RES_ATTR = "rcsb_entry_info.diffrn_resolution_high.value"

# Candidate windows from the plan: sub-0.9 (subatomic), sub-1.0 (the plan's headline
# criterion), sub-1.2 (the fallback if sub-A survivors lack diversity).
DEFAULT_WINDOWS = (0.9, 1.0, 1.2)

# Scouting tiers, cumulative. Values are proxies, chosen to be defensible rather than
# preregistered: clashscore <= 2 is deep in the archive's best tail; zero Ramachandran
# outliers is Top2018's spirit at file level; rotamer <= 0.3 % allows one outlier in a
# ~300-residue chain (which phase 1 would protect, not penalize, if density-supported);
# R-free <= 0.18 is looser than the d/10 rule of thumb at 1.0 A on purpose — the rule
# is aspirational at subatomic resolution and the headroom screen, not a header cut,
# decides enrollment.
TIER_NODES: list[tuple[str, list[tuple[str, float]]]] = [
    ("base", []),
    ("geom", [("pdbx_vrpt_summary_geometry.clashscore", 2.0),
              ("pdbx_vrpt_summary_geometry.percent_ramachandran_outliers", 0.0)]),
    ("strict", [("pdbx_vrpt_summary_geometry.percent_rotamer_outliers", 0.3),
                ("refine.ls_R_factor_R_free", 0.18)]),
]

# The percentile attributes on the validation report's <Entry> tag, exact names.
# Anchored matching for the #281-adjacent reason in bench_vs_deposited.py: a tail
# match on "clashscore" happily returns a percentile where a score was wanted.
XML_PERCENTILES = ("absolute-percentile-clashscore",
                  "absolute-percentile-percent-rama-outliers",
                  "absolute-percentile-percent-rota-outliers",
                  "absolute-percentile-DCC_Rfree",
                  "absolute-percentile-percent-RSRZ-outliers")


def _upper_bound_node(attribute: str, value: float) -> dict:
    return {"type": "terminal", "service": "text", "parameters": {
        "attribute": attribute, "operator": "range",
        "value": {"to": value, "include_upper": True}}}


def build_query_nodes(max_res: float, tier: str) -> list[dict]:
    """All terminal nodes for a window x tier cell; tiers are cumulative."""
    nodes = [
        {"type": "terminal", "service": "text", "parameters": {
            "attribute": "exptl.method", "operator": "exact_match",
            "value": "X-RAY DIFFRACTION"}},
        _upper_bound_node(RES_ATTR, max_res),
        # No structure factors -> no headroom screen, no bench. Same cheap filter as
        # select_xray_entries.py.
        {"type": "terminal", "service": "text", "parameters": {
            "attribute": "rcsb_accession_info.has_released_experimental_data",
            "operator": "exact_match", "value": "Y"}},
        {"type": "terminal", "service": "text", "parameters": {
            "attribute": "rcsb_entry_info.polymer_entity_count_protein",
            "operator": "range", "value": {"from": 1, "include_lower": True}}},
    ]
    for name, cut_nodes in TIER_NODES:
        nodes.extend(_upper_bound_node(attr, val) for attr, val in cut_nodes)
        if name == tier:
            return nodes
    raise SystemExit(f"select_gold: unknown tier {tier!r}")


def _post(query: dict) -> dict:
    req = urllib.request.Request(RCSB_SEARCH, data=json.dumps(query).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            return json.load(r)
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError,
            json.JSONDecodeError) as exc:
        # An unknown attribute surfaces here as HTTP 400 — loud, per the docstring.
        raise SystemExit(f"select_gold: RCSB search failed: {exc}")


def count_entries(max_res: float, tier: str, fetch=_post) -> int:
    payload = fetch({
        "query": {"type": "group", "logical_operator": "and",
                  "nodes": build_query_nodes(max_res, tier)},
        "return_type": "entry",
        "request_options": {"paginate": {"start": 0, "rows": 1}}})
    return int(payload.get("total_count", 0))


def cluster_stats(max_res: float, tier: str, identity: int = 30,
                  fetch=_post) -> dict:
    """Protein-entity clusters at `identity` % for a cell.

    `ungrouped_count` is entities RCSB's precomputed clustering has no group for;
    they are extra diversity of unknown degree, so they are carried in the output
    rather than folded into either number.
    """
    nodes = build_query_nodes(max_res, tier)
    nodes.append({"type": "terminal", "service": "text", "parameters": {
        "attribute": "entity_poly.rcsb_entity_polymer_type",
        "operator": "exact_match", "value": "Protein"}})
    payload = fetch({
        "query": {"type": "group", "logical_operator": "and", "nodes": nodes},
        "return_type": "polymer_entity",
        "request_options": {
            "group_by": {"aggregation_method": "sequence_identity",
                         "similarity_cutoff": identity},
            "group_by_return_type": "representatives",
            "paginate": {"start": 0, "rows": 1}}})
    return {"protein_entities": int(payload.get("total_count", 0)),
            "clusters": int(payload.get("group_by_count", 0)),
            "unclustered_entities": int(payload.get("ungrouped_count", 0))}


def survivor_ids(max_res: float, tier: str, fetch=_post) -> list[str]:
    """Every entry id in a cell, paginated; the committed record of the pool."""
    ids: list[str] = []
    query = {
        "query": {"type": "group", "logical_operator": "and",
                  "nodes": build_query_nodes(max_res, tier)},
        "return_type": "entry",
        "request_options": {"paginate": {"start": 0, "rows": 1000},
                            "sort": [{"sort_by": RES_ATTR, "direction": "asc"}]},
    }
    while True:
        payload = fetch(query)
        hits = [h["identifier"].upper() for h in payload.get("result_set", [])]
        ids.extend(hits)
        if not hits or len(ids) >= int(payload.get("total_count", 0)):
            return ids
        query["request_options"]["paginate"]["start"] = len(ids)


def spread_sample(items: list[str], want: int) -> list[str]:
    """Deterministic even spread. The pool is sorted by d_min, so taking the head
    would sample only the extreme-resolution end — the same shape as #243's
    oldest-N defect, on a different axis."""
    if want >= len(items):
        return list(items)
    if want <= 0:
        return []
    step = len(items) / want
    return [items[int(i * step)] for i in range(want)]


def entry_check(pdb_id: str, max_res: float) -> tuple[float | None, str | None, str]:
    """d_min from the ENTRY record plus the title, the #238 spot-check."""
    try:
        with urllib.request.urlopen(RCSB_ENTRY.format(pdb_id=pdb_id), timeout=60) as r:
            data = json.load(r)
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError,
            json.JSONDecodeError):
        return None, "entry record not retrievable", ""
    info = data.get("rcsb_entry_info") or {}
    d_min = (info.get("diffrn_resolution_high") or {}).get("value")
    title = (data.get("struct") or {}).get("title", "")
    if d_min is None:
        return None, "no d_min on the entry record", title
    if d_min > max_res:
        return d_min, f"d_min {d_min} above the window bound {max_res}", title
    return d_min, None, title


def xml_percentiles(pdb_id: str) -> dict[str, float | None]:
    """Percentile ranks from the validation report's <Entry> tag (sampled entries
    only — the report help pins these to a dated archive snapshot)."""
    try:
        with urllib.request.urlopen(VALIDATION_XML.format(pdb_id=pdb_id.lower()),
                                    timeout=120) as r:
            head = r.read(200_000).decode("utf-8", "replace")
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
        return {}
    out: dict[str, float | None] = {}
    for name in XML_PERCENTILES:
        m = re.search(r'(?:^|[\s])' + re.escape(name) + r'="([^"]*)"', head)
        try:
            out[name] = float(m.group(1)) if m else None
        except ValueError:
            out[name] = None
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--windows", default=",".join(str(w) for w in DEFAULT_WINDOWS),
                    help="comma-separated d_min upper bounds (default %(default)s)")
    ap.add_argument("--identity", type=int, default=30,
                    help="sequence-identity clustering cutoff, %% (default 30)")
    ap.add_argument("--spot-checks", type=int, default=10,
                    help="entries per window re-verified against the entry record")
    ap.add_argument("--xml-sample", type=int, default=12,
                    help="survivors sampled for wwPDB percentile ranks (0 disables)")
    ap.add_argument("--json", dest="json_out")
    args = ap.parse_args()

    windows = sorted(float(w) for w in args.windows.split(",") if w.strip())
    if not windows:
        raise SystemExit("select_gold: no windows given")

    report: dict = {"attribute": RES_ATTR, "identity_pct": args.identity,
                    "tiers": {name: dict(nodes) for name, nodes in TIER_NODES},
                    "windows": {}}

    for max_res in windows:
        cells = {}
        for tier, _ in TIER_NODES:
            n = count_entries(max_res, tier)
            clusters = cluster_stats(max_res, tier, args.identity)
            cells[tier] = {"entries": n, **clusters}
            print(f"  <= {max_res:.1f} A  {tier:<7} {n:>6} entries  "
                  f"{clusters['clusters']:>5} clusters "
                  f"(+{clusters['unclustered_entities']} unclustered entities)",
                  file=sys.stderr)
        strict_ids = survivor_ids(max_res, "strict")
        cells["strict"]["ids"] = strict_ids

        # Spot-verify the search result against entry records (#238 discipline: the
        # search finds candidates; it is not trusted to have filtered them).
        checks = []
        for pdb_id in spread_sample(strict_ids, args.spot_checks):
            d_min, problem, title = entry_check(pdb_id, max_res)
            checks.append({"pdb_id": pdb_id, "d_min": d_min,
                           "problem": problem, "title": title[:70]})
            if problem:
                print(f"  ! {pdb_id}: {problem}", file=sys.stderr)
        cells["strict"]["spot_checks"] = checks
        report["windows"][f"{max_res:.1f}"] = cells

    # Percentile ranks for a SAMPLE of the middle window's strict survivors. A full
    # harvest is deliberately out of scope: the ranks live only in per-entry XML.
    if args.xml_sample:
        mid = f"{windows[len(windows) // 2]:.1f}"
        pool = report["windows"][mid]["strict"]["ids"]
        sample = spread_sample(pool, args.xml_sample)
        # Canary before the rest: one entry, parsed, non-empty — or say so and stop.
        first = xml_percentiles(sample[0]) if sample else {}
        if sample and not any(v is not None for v in first.values()):
            print(f"  ! percentile canary {sample[0]} returned nothing; "
                  f"skipping the sample rather than fetching {len(sample)} blanks",
                  file=sys.stderr)
            report["percentile_sample"] = {"window": mid, "sampled": [],
                                           "sample_of": len(pool),
                                           "failed_canary": sample[0]}
        else:
            rows = [{"pdb_id": sample[0], **first}]
            rows += [{"pdb_id": p, **xml_percentiles(p)} for p in sample[1:]]
            report["percentile_sample"] = {"window": mid, "sampled": rows,
                                           "sample_of": len(pool)}
            print(f"  percentiles sampled for {len(rows)} of {len(pool)} "
                  f"strict survivors at <= {mid} A", file=sys.stderr)

    if args.json_out:
        Path(args.json_out).write_text(json.dumps(report, indent=2) + "\n")
    summary = {w: {t: {"entries": c[t]["entries"], "clusters": c[t]["clusters"]}
                   for t in c if t in dict(TIER_NODES)}
               for w, c in report["windows"].items()}
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
