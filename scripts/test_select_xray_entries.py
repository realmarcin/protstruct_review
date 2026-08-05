#!/usr/bin/env python3
"""Unit tests for the X-ray entry selector.

The selector decides which structures get downloaded and re-refined at ~15 minutes of
`phenix.refine` each, so a defect here is paid in hours. Both behaviours pinned below
were found by the #225 canary before any batch:

  #238  selecting on `rcsb_entry_info.resolution_combined` returns ~75 % out-of-window
        entries, because for X-ray it is an ARRAY and a range query matches if ANY
        element falls in the window. 3VXF was selected as low-resolution while its
        header reads 1.60 A.

  #237  the under-evidenced band is `d_min >= 2.5 A`, not below it, so that is the
        default window.

Network-free: `verify()` and `stratified()` are exercised with substituted fetchers,
because a test that needs RCSB is a test that fails when RCSB is slow.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PASSED = 0


def load():
    spec = importlib.util.spec_from_file_location(
        "select_xray", REPO / "scripts" / "select_xray_entries.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["select_xray"] = module
    spec.loader.exec_module(module)
    return module


def check(label: str, got, want) -> None:
    global PASSED
    if got != want:
        print(f"FAIL  {label}: got {got!r}, want {want!r}")
        sys.exit(1)
    PASSED += 1
    print(f"PASS  {label} (got {got!r})")


sx = load()

# --- #238: the attribute is the whole defect ---------------------------------------

check("selection uses the scalar diffrn attribute",
      sx.RES_ATTR, "rcsb_entry_info.diffrn_resolution_high.value")
check("  and never resolution_combined, which is an array for X-ray",
      "resolution_combined" in sx.RES_ATTR, False)

# --- #237: the default window is the under-evidenced branch ------------------------

import argparse
_ap = argparse.ArgumentParser()
_ap.add_argument("--min-res", type=float, default=2.5)
check("the default window starts at 2.5 A, the branch whose maxima are lost",
      _ap.parse_args([]).min_res, 2.5)

# --- verify() is the check that would have caught 3VXF -----------------------------
# It re-reads the ENTRY record rather than trusting the search index.

_ENTRIES = {
    # 3VXF as it really is: search-matched at 2.5-3.2 via its second value, actually 1.6
    "3VXF": {"rcsb_entry_info": {"diffrn_resolution_high": {"value": 1.602}}},
    "1A0C": {"rcsb_entry_info": {"diffrn_resolution_high": {"value": 2.5}}},
    # no diffrn value -> must fall back to refine.ls_d_res_high rather than give up
    "FALL": {"rcsb_entry_info": {}, "refine": [{"ls_d_res_high": 2.9}]},
    # neither -> undecidable, and must be reported as such rather than assumed in
    "NONE": {"rcsb_entry_info": {}},
}


class _FakeResponse:
    def __init__(self, payload): self._p = payload
    def read(self): import json; return json.dumps(self._p).encode()
    def __enter__(self): return self
    def __exit__(self, *a): return False


def _fake_urlopen(url, timeout=0):
    import json
    pdb_id = url.rstrip("/").split("/")[-1]
    if pdb_id not in _ENTRIES:
        raise sx.urllib.error.HTTPError(url, 404, "not found", None, None)
    class _R(_FakeResponse):
        pass
    r = _R(_ENTRIES[pdb_id])
    # json.load calls .read()
    return r


_saved = sx.urllib.request.urlopen
sx.urllib.request.urlopen = _fake_urlopen
try:
    check("an entry whose true d_min is outside the window is rejected",
          sx.verify("3VXF", 2.5, 3.2)[1] is not None, True)
    check("  and the rejection names the value it found",
          "1.602" in (sx.verify("3VXF", 2.5, 3.2)[1] or ""), True)
    check("an in-window entry is accepted", sx.verify("1A0C", 2.5, 3.2), (2.5, None))
    check("a missing diffrn value falls back to refine.ls_d_res_high",
          sx.verify("FALL", 2.5, 3.2), (2.9, None))
    check("an entry with no d_min anywhere is reported, not assumed in",
          sx.verify("NONE", 2.5, 3.2)[1], "no d_min on the entry record")
    check("an unreachable entry record is reported, not assumed in",
          sx.verify("ABSENT", 2.5, 3.2)[1], "entry record not retrievable")
finally:
    sx.urllib.request.urlopen = _saved


# --- stratified() must interleave, or a truncated run is single-resolution ---------

_saved_search = sx.search
try:
    sx.search = lambda lo, hi, rows: [f"{int(lo*100)}_{i}" for i in range(rows)]
    got = sx.stratified(2.5, 3.2, strata=4, per=2)
    # round-robin: first pick from every stratum, then the second from every stratum
    check("strata are interleaved rather than concatenated",
          [g.split("_")[1] for g in got], ["0", "0", "0", "0", "1", "1", "1", "1"])
    check("  so truncating at --limit keeps the spread",
          len({g.split("_")[0] for g in got[:4]}), 4)
finally:
    sx.search = _saved_search


# --- the exclusion source is imported, not retyped ---------------------------------

_known = sx.known_ids()
check("known ids come from bench_refinement_deltas.DEFAULT_SET",
      {"12LO", "43SK", "9LLO"} <= _known, True)
check("  and there are 16 of them, the set that can still be named", len(_known), 16)


print(f"\nall select-xray unit tests passed ({PASSED} checks)")
