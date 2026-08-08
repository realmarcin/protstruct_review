#!/usr/bin/env python3
"""Unit tests for the phase-0 gold-standard scout (#295).

The scout's numbers feed the resolution-window decision for the negative-control
benchmark, so a query-shape defect here becomes a wrong decision quietly. The
behaviours pinned:

  - tiers are CUMULATIVE (strict implies geom implies base); a tier that silently
    dropped the geometry cuts would inflate the strict pool
  - the resolution attribute is the scalar `diffrn_resolution_high.value` (#238:
    `resolution_combined` is an array for X-ray and range-matches on ANY element)
  - pagination walks the whole result set and stops (both on total_count and on an
    empty page, whichever comes first)
  - the percentile sample is an even SPREAD of a d_min-sorted pool, not its head
    (#243's oldest-N defect, on the resolution axis)

Network-free: fetchers are substituted, because a test that needs RCSB is a test
that fails when RCSB is slow.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PASSED = 0


def load():
    spec = importlib.util.spec_from_file_location(
        "select_gold", REPO / "scripts" / "select_gold_standards.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["select_gold"] = module
    spec.loader.exec_module(module)
    return module


def check(label: str, got, want) -> None:
    global PASSED
    if got != want:
        print(f"FAIL  {label}: got {got!r}, want {want!r}")
        sys.exit(1)
    PASSED += 1
    print(f"PASS  {label} (got {got!r})")


sg = load()

# --- tier cumulativity and the #238 attribute --------------------------------------

base = sg.build_query_nodes(1.0, "base")
geom = sg.build_query_nodes(1.0, "geom")
strict = sg.build_query_nodes(1.0, "strict")

check("base node count", len(base), 4)
check("geom adds exactly its two cuts", len(geom), len(base) + 2)
check("strict adds exactly its two cuts", len(strict), len(geom) + 2)


def attrs(nodes):
    return [n["parameters"]["attribute"] for n in nodes]


check("strict contains geom's clashscore cut",
      "pdbx_vrpt_summary_geometry.clashscore" in attrs(strict), True)
check("strict contains geom's rama cut",
      "pdbx_vrpt_summary_geometry.percent_ramachandran_outliers" in attrs(strict),
      True)
check("resolution attribute is the #238 scalar",
      sg.RES_ATTR in attrs(base), True)
check("the array attribute is nowhere in the query",
      any("resolution_combined" in a for a in attrs(strict)), False)

res_node = next(n for n in base
                if n["parameters"]["attribute"] == sg.RES_ATTR)
check("window is an upper bound with the bound included",
      res_node["parameters"]["value"], {"to": 1.0, "include_upper": True})

try:
    sg.build_query_nodes(1.0, "nonesuch")
    check("unknown tier refused", "no exception", "SystemExit")
except SystemExit:
    check("unknown tier refused", "SystemExit", "SystemExit")

# --- counting from substituted fetchers --------------------------------------------

check("count_entries reads total_count",
      sg.count_entries(1.0, "strict", fetch=lambda q: {"total_count": 482}), 482)

payload = {"total_count": 504, "group_by_count": 172, "ungrouped_count": 35}
check("cluster_stats carries all three counts",
      sg.cluster_stats(1.0, "strict", fetch=lambda q: payload),
      {"protein_entities": 504, "clusters": 172, "unclustered_entities": 35})


def grouped_query_nodes():
    seen = {}
    sg.cluster_stats(1.2, "geom", fetch=lambda q: seen.update(q) or {})
    return seen


q = grouped_query_nodes()
check("cluster query is per polymer entity", q["return_type"], "polymer_entity")
check("cluster query restricts entities to protein",
      any(n["parameters"].get("value") == "Protein"
          for n in q["query"]["nodes"]), True)

# --- pagination --------------------------------------------------------------------

pages = [
    {"total_count": 5, "result_set": [{"identifier": f"1ab{i}"} for i in range(3)]},
    {"total_count": 5, "result_set": [{"identifier": f"2cd{i}"} for i in range(2)]},
]
calls = []


def paged_fetch(query):
    calls.append(query["request_options"]["paginate"]["start"])
    return pages[len(calls) - 1]


ids = sg.survivor_ids(1.0, "strict", fetch=paged_fetch)
check("pagination collects every page", ids,
      ["1AB0", "1AB1", "1AB2", "2CD0", "2CD1"])
check("second page starts where the first ended", calls, [0, 3])

empty_after_one = iter([{"total_count": 99, "result_set": [{"identifier": "1xyz"}]},
                        {"total_count": 99, "result_set": []}])
ids = sg.survivor_ids(1.0, "strict", fetch=lambda q: next(empty_after_one))
check("an empty page ends pagination even below total_count", ids, ["1XYZ"])

# --- spread sampling ---------------------------------------------------------------

pool = [f"E{i:03d}" for i in range(100)]
sample = sg.spread_sample(pool, 4)
check("spread sample is deterministic and even",
      sample, ["E000", "E025", "E050", "E075"])
check("spread sample is not the head of the pool",
      sample == pool[:4], False)
check("want >= pool returns the whole pool",
      sg.spread_sample(pool[:3], 10), pool[:3])
check("want 0 returns nothing", sg.spread_sample(pool, 0), [])

print(f"\n{PASSED} checks passed")
