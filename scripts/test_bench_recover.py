#!/usr/bin/env python3
"""Unit tests for the round-4 recover-leg machinery (#295).

Pinned: the C1 record-vs-registration assertion (thresholds recomputed from
the committed round-3 record must equal the registered table), the
FIT-DEGRADED rule incl. the REFMAC-unmeasurable fallback, and the verdict
precedence. PHENIX- and network-free except reading the committed record.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PASSED = 0


def load():
    spec = importlib.util.spec_from_file_location(
        "brl", REPO / "scripts" / "bench_recover_leg.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules["brl"] = m
    spec.loader.exec_module(m)
    return m


def check(label, got, want):
    global PASSED
    if got != want:
        print(f"FAIL  {label}: got {got!r}, want {want!r}")
        sys.exit(1)
    PASSED += 1
    print(f"PASS  {label}")


b = load()

# C1: the committed record must reproduce the registered table exactly.
thr = b.fit_thresholds_from_record()
check("C1 thresholds reproduce the registered table",
      thr, b.REGISTERED_FIT_THRESHOLDS)

T = b.REGISTERED_FIT_THRESHOLDS
check("fit: all three past thresholds",
      b.fit_degraded({"d_phenix": 0.02, "d_gemmi": 0.02, "d_refmac": 0.01}, T),
      True)
check("fit: one tool inside stays clean",
      b.fit_degraded({"d_phenix": 0.02, "d_gemmi": 0.005, "d_refmac": 0.01}, T),
      False)
check("fit: REFMAC unmeasurable -> None (fallback, not verdict)",
      b.fit_degraded({"d_phenix": 0.02, "d_gemmi": 0.02, "d_refmac": None}, T),
      None)
check("fit: a null-typical drift stays clean",
      b.fit_degraded({"d_phenix": 0.0035, "d_gemmi": 0.0039,
                      "d_refmac": 0.0018}, T), False)

flags2 = {"F-data": True, "F-shift": True, "F-geom": False, "F-protected": False}
flags1 = {"F-data": True, "F-shift": False, "F-geom": False, "F-protected": False}
flags0 = {k: False for k in flags1}
big = {"d_phenix": 0.3, "d_gemmi": 0.3, "d_refmac": 0.3}
small = {"d_phenix": 0.001, "d_gemmi": 0.001, "d_refmac": 0.001}
check("precedence: >= 2 families is DEGRADED even when fit also fires",
      b.combined_verdict(flags2, big, T), "DEGRADED")
check("precedence: fit alone is FIT-DEGRADED",
      b.combined_verdict(flags1, big, T), "FIT-DEGRADED")
check("precedence: nothing fires -> not-degraded",
      b.combined_verdict(flags0, small, T), "not-degraded")
check("precedence: REFMAC-unmeasurable + one family -> not-degraded",
      b.combined_verdict(flags1, {"d_phenix": 0.3, "d_gemmi": 0.3,
                                  "d_refmac": None}, T), "not-degraded")

print(f"\n{PASSED} checks passed")
