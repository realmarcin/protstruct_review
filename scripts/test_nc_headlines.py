#!/usr/bin/env python3
"""Unit tests for nc_headlines (#293 step a): the one generic rule, its three
modes, the per-entry window, and the renderers' parity with the committed
round-10 record. Hermetic."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PASSED = 0


def load(name):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / f"{name}.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


def check(label, got, want):
    global PASSED
    if got != want:
        print(f"FAIL  {label}: got {got!r}, want {want!r}")
        sys.exit(1)
    PASSED += 1
    print(f"PASS  {label}")


h = load("nc_headlines")
H = h.headline

# near: proximity, either order, bounded window, no digit in the gap
near = H("screened count", 1, "screened", window=20, between="sentence")
check("near: keyword then value", h.missing("screened 1 entry", [near]), [])
check("near: value then keyword", h.missing("**1** fully screened", [near]), [])
check("near: neighbouring digit beyond the window does not satisfy",
      len(h.missing("Attempted 2: 1 floor, 0 data defects — screened count lost.", [near])), 1)
check("near: value inside a larger number does not match",
      len(h.missing("screened 11", [H("x", 1, "screened")])), 1)
check("near: window is per entry",
      h.missing("osol_h success .................................... 2/2",
                [H("s", "2/2", "osol_h", order="keyword_first", window=80)]), [])
check("near: same text fails a 20-char window",
      len(h.missing("osol_h success .................................... 2/2",
                    [H("s", "2/2", "osol_h", order="keyword_first", window=20)])), 1)
check("near: order is enforced",
      len(h.missing("2/2 osol_h", [H("s", "2/2", "osol_h", order="keyword_first")])), 1)
check("near: nodigit gap refuses an intervening figure",
      len(h.missing("osol_h 3 then 2/2", [H("s", "2/2", "osol_h", order="keyword_first",
                                             window=80, between="nodigit")])), 1)
# present / phrase
check("present: bare substring", h.missing("Q1: 0/22 false verdicts", [H("q", "0/22", mode="present")]), [])
check("phrase: whitespace tolerant",
      h.missing("No old success was\n  lost.", [H("z", "No old success was lost", mode="phrase")]), [])
check("phrase: wording change fails",
      len(h.missing("No old success lost.", [H("z", "No old success was lost", mode="phrase")])), 1)
# validate: malformed entries are named, never silently passed
check("validate: near without keyword", h.validate(H("x", 1)) is not None, True)
check("validate: unknown mode", h.validate({"label": "x", "value": "1", "mode": "fuzzy"}) is not None, True)
check("validate: window out of range", h.validate(H("x", 1, "k", window=999)) is not None, True)
check("validate: non-object", h.validate("1/2") is not None, True)
check("missing: a malformed entry is reported, not skipped",
      any("malformed" in r for r in h.missing("anything", [{"label": "x"}])), True)

# Renderer parity with the committed round-10 record: the block a driver would
# have written reproduces the legacy #419 phrases, and the committed doc states
# every one of them.
r10 = json.loads((REPO / "ref/research/data/negative_control_round10_recover.json").read_text())
rendered = h.recover_headlines(r10["summary"])
labels = {e["label"] for e in rendered}
check("round-10 renderer covers the ten #419 headlines + lists",
      {"osol_h success", "osol comparison", "ANIS measurability", "H/D range",
       "H/D retention", "ANIS log count", "sandbox count", "PGID count",
       "unmasked reproduction", "all-residue reproduction",
       "zero-loss comparison"} <= labels, True)
check("round-10 renderer: osol_h success is the record's 15/22",
      next(e["value"] for e in rendered if e["label"] == "osol_h success"), "15/22")
doc10 = (REPO / "ref/research/negative_control_round10.md").read_text()
check("round-10 doc states every rendered headline", h.missing(doc10, rendered), [])
check("every rendered entry validates", [h.validate(e) for e in rendered].count(None), len(rendered))
r3 = json.loads((REPO / "ref/research/data/negative_control_round3_bench.json").read_text())
check("round-3 bench renderer: Q1 0/22",
      h.bench_headlines(r3["rows"])[0]["value"], "0/22")
r2 = json.loads((REPO / "ref/research/data/negative_control_round2_screen.json").read_text())
doc2 = (REPO / "ref/research/negative_control_round2.md").read_text()
check("round-2 doc states every rendered screen headline",
      h.missing(doc2, h.screen_headlines(r2["rows"])), [])

print(f"\n{PASSED} checks passed")
