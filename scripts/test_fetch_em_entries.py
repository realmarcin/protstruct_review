#!/usr/bin/env python3
"""Unit tests for the EM fetch cache bookkeeping.

`entries.json` is the screen's input, so it is the screen's DENOMINATOR. #231 was
found running the #224 batch: a second fetch into the same cache OVERWROTE the file,
erasing the canary entry while its 84 MB map sat on disk — paid for and dropped from
the count. `screen_dfsc_ratio.py` would have reported `n_screened: 13` against 14
cached entries, which is a base rate divided by the wrong number.

These call the real `write_entries`. The first draft of this file re-implemented the
merge and would have passed against a broken one — a second copy of a rule, which is
#153 and #190 in this repo, and the reason the function was lifted out of its closure.
"""
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PASSED = 0


def load():
    spec = importlib.util.spec_from_file_location(
        "fetch_em", REPO / "scripts" / "fetch_em_entries.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["fetch_em"] = module
    spec.loader.exec_module(module)
    return module


def check(label: str, got, want) -> None:
    global PASSED
    if got != want:
        print(f"FAIL  {label}: got {got!r}, want {want!r}")
        sys.exit(1)
    PASSED += 1
    print(f"PASS  {label} (got {got!r})")


fe = load()


def ids(cache: Path) -> list[str]:
    return sorted(e["pdb_id"] for e in json.loads((cache / "entries.json").read_text()))


with tempfile.TemporaryDirectory() as d:
    cache = Path(d)
    (cache / "aaaa.map").write_bytes(b"x")
    (cache / "bbbb.map").write_bytes(b"x")

    # --- #231: the defect exactly as observed --------------------------------------
    fe.write_entries(cache, [{"pdb_id": "AAAA", "resolution": 3.0}])
    fe.write_entries(cache, [{"pdb_id": "BBBB", "resolution": 3.1}])
    check("a second fetch into the same cache keeps the first entry",
          ids(cache), ["AAAA", "BBBB"])

    # entries.json must describe the CACHE, not the history of fetches into it.
    # Resurrecting an entry whose map is gone would break the screen the other way:
    # it would try to measure a file that is not there.
    (cache / "aaaa.map").unlink()
    (cache / "cccc.map").write_bytes(b"x")
    fe.write_entries(cache, [{"pdb_id": "CCCC", "resolution": 3.2}])
    check("a prior entry whose map is gone is dropped, not resurrected",
          ids(cache), ["BBBB", "CCCC"])

    # Re-fetching an id must update it, not append a duplicate -- a duplicate would
    # inflate n_screened, which is the same denominator failure from the other side.
    fe.write_entries(cache, [{"pdb_id": "BBBB", "resolution": 9.9}])
    rows = json.loads((cache / "entries.json").read_text())
    check("re-fetching an id updates it rather than duplicating",
          [len([r for r in rows if r["pdb_id"] == "BBBB"]),
           [r for r in rows if r["pdb_id"] == "BBBB"][0]["resolution"]], [1, 9.9])

    # A corrupt file must not poison every later run. Replaced, not propagated.
    (cache / "entries.json").write_text("{ this is not json")
    (cache / "dddd.map").write_bytes(b"x")
    fe.write_entries(cache, [{"pdb_id": "DDDD", "resolution": 3.3}])
    check("a corrupt entries.json is replaced rather than propagated",
          ids(cache), ["DDDD"])

    # The return value is what was written, so a caller need not re-read the file.
    (cache / "eeee.map").write_bytes(b"x")
    check("the written set is returned",
          sorted(e["pdb_id"] for e in
                 fe.write_entries(cache, [{"pdb_id": "EEEE"}])), ["DDDD", "EEEE"])

    # An empty fetch must not erase the cache's record of itself. This is the
    # interrupted-run case: flush() is called after every candidate, including
    # before the first one succeeds.
    check("an empty fetch preserves what is already recorded",
          sorted(e["pdb_id"] for e in fe.write_entries(cache, [])), ["DDDD", "EEEE"])


print(f"\nall fetch-cache unit tests passed ({PASSED} checks)")
