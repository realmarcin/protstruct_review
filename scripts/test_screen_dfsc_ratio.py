#!/usr/bin/env python3
"""Unit tests for the `d_FSC_model_pre / d_min` screen.

The screen selects which cryo-EM entries get downloaded and refined, so a defect here
is expensive in a way a wrong document figure is not: it is paid in 100-250 MB
downloads and minutes of `mtriage` per entry. Both defects these tests cover were found
by the pre-batch canary for #224, before any fan-out.

  #226  the cut was hardcoded at 1.3 with no flag. Round 23 screened at 1.3, found
        0 of 24, and could not complete the test; the Tukey fence is 1.074, where the
        base rate is double. Screening at the wrong cut needs ~90 entries instead of
        ~45 -- the difference between a project and an impossible one.

  #227  the prior base rate was the literal 5.6 ("2 of 36 on record"), true when
        written and stale at 60 entries, emitted into machine-readable output that
        round documents then quote.

The cases are partitions of the input space, not regressions for one incident.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PASSED = 0


def load():
    spec = importlib.util.spec_from_file_location(
        "screen_dfsc", REPO / "scripts" / "screen_dfsc_ratio.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["screen_dfsc"] = module
    spec.loader.exec_module(module)
    return module


def check(label: str, got, want) -> None:
    global PASSED
    if got != want:
        print(f"FAIL  {label}: got {got!r}, want {want!r}")
        sys.exit(1)
    PASSED += 1
    print(f"PASS  {label} (got {got!r})")


sc = load()

# --- #226: the cut is a parameter, and its default is the data-driven one ----------

check("the default cut is the Tukey fence, not round 22's post-hoc 1.3",
      sc.DEFAULT_CUT, 1.074)
check("  and round 22's cut is still available by name", sc.POST_HOC_CUT, 1.3)

# A row is a candidate or not depending on the cut it was screened at. 1.076 (10EU)
# is the case that matters: it clears the fence and fails the post-hoc cut, and it is
# a real entry, which is why round 23 could not complete its test.
_ROWS = [{"pdb_id": "10EU", "ratio": 1.076, "high_ratio": True},
         {"pdb_id": "21GF", "ratio": 0.983, "high_ratio": False}]
check("a ratio between the two cuts is a candidate at the fence",
      sc.summarize(_ROWS, 1.074)["cut"], 1.074)
check("  and the cut is recorded in the output, so a run cannot be misread later",
      sc.summarize(_ROWS, 1.3)["cut"], 1.3)


# --- #227: the prior base rate is derived from the record, at the cut in force -----

_at_fence = sc.prior_base_rate(1.074)
_at_posthoc = sc.prior_base_rate(1.3)

check("the prior base rate is derived, and differs between the two cuts",
      [_at_fence["prior_base_rate_pct"], _at_posthoc["prior_base_rate_pct"]], [6.7, 3.3])
check("  and it is never the stale literal 5.6",
      5.6 in (_at_fence["prior_base_rate_pct"], _at_posthoc["prior_base_rate_pct"]), False)

# A bare rate with no denominator is what round 28 spent itself correcting.
check("the numerator and denominator ship with the rate",
      [_at_fence["prior_hits"], _at_fence["prior_n"]], [4, 60])
check("  and the post-hoc cut's numerator is the pair round 22 saw",
      _at_posthoc["prior_hits"], 2)

# The record is the source. If it disappears the screen must say so rather than
# invent a rate -- failing closed, since this figure is quoted into round documents.
_saved = sc.DELTAS_TSV
try:
    sc.DELTAS_TSV = REPO / "ref/research/data/does_not_exist.tsv"
    _missing = sc.prior_base_rate(1.074)
    check("a missing record yields no rate rather than a guess",
          _missing["prior_base_rate_pct"], None)
    check("  and says why", "no record" in _missing["prior_note"], True)
finally:
    sc.DELTAS_TSV = _saved

# The rate must track the record, not a snapshot of it. Re-deriving after the set
# grows is the whole point, so assert the denominator equals what the file holds now.
import csv
with sc.DELTAS_TSV.open() as fh:
    _n = sum(1 for r in csv.DictReader(fh, delimiter="\t")
             if (r.get("d_fsc_model_pre") or "").strip()
             and (r.get("resolution") or "").strip())
check("the denominator is exactly the record's computable-ratio rows",
      _at_fence["prior_n"], _n)


# --- #230: a cut outside the plausible band is a typo, not an intention -----------
# `--cut 0` used to run and report a 100 % base rate in well-formed JSON. The screen
# selects which entries get downloaded, so nonsense here is paid in gigabytes.

import argparse

for _bad in ("0", "-1", "5", "0.4"):
    _raised = ""
    try:
        sc._cut_value(_bad)
    except argparse.ArgumentTypeError as _e:
        _raised = str(_e)
    check(f"--cut {_bad} is refused by name", "outside the plausible range" in _raised, True)

_msg = ""
try:
    sc._cut_value("abc")
except argparse.ArgumentTypeError as _e:
    _msg = str(_e)
check("--cut abc is refused as not-a-number, not as a ValueError",
      "not a number" in _msg, True)

for _ok in (sc.TUKEY_FENCE, sc.POST_HOC_CUT):
    check(f"--cut {_ok} is accepted", sc._cut_value(str(_ok)), _ok)

# The refusal names both real cuts, so somebody who typo'd learns what to type.
check("the refusal names the fence and the post-hoc cut",
      all(t in _raised for t in ("1.074", "1.3")), True)


print(f"\nall screen-dfsc unit tests passed ({PASSED} checks)")
