#!/usr/bin/env python3
"""Unit tests for the round-5 machinery (#295).

Pinned: E1 (positive evidence always — the all-three rule with REFMAC, the
two-path rule standing alone without it, never None), the W4
contradiction check, and that the round-4 judge's default fit behavior is
untouched by the fit_fn parameterization (its own suite re-runs green).
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PASSED = 0


def load(name):
    spec = importlib.util.spec_from_file_location(
        name, REPO / "scripts" / f"{name}.py")
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


b5 = load("bench_round5")
T = {"d_phenix": 0.01220, "d_gemmi": 0.01090, "d_refmac": 0.00540}

check("E1: all three past -> degraded",
      b5.e1_fit_degraded({"d_phenix": 0.02, "d_gemmi": 0.02,
                          "d_refmac": 0.01}, T), True)
check("E1: REFMAC inside blocks the all-three rule",
      b5.e1_fit_degraded({"d_phenix": 0.02, "d_gemmi": 0.02,
                          "d_refmac": 0.001}, T), False)
check("E1: two-path stands alone when REFMAC absent (the 9YGW case)",
      b5.e1_fit_degraded({"d_phenix": 0.0333, "d_gemmi": 0.0335,
                          "d_refmac": None}, T), True)
check("E1: two-path split verdict stays clean without REFMAC",
      b5.e1_fit_degraded({"d_phenix": 0.02, "d_gemmi": 0.005,
                          "d_refmac": None}, T), False)
check("E1: never None",
      b5.e1_fit_degraded({"d_phenix": 0.001, "d_gemmi": 0.001,
                          "d_refmac": None}, T), False)

check("W4: a clean success has no contradiction",
      b5.w4_contradiction({"numbers": {"d_phenix": 0.001, "d_gemmi": 0.001,
                                       "d_refmac": 0.001}}, T, True), False)
check("W4: success with a residual past 2x threshold contradicts",
      b5.w4_contradiction({"numbers": {"d_phenix": 0.03, "d_gemmi": 0.001,
                                       "d_refmac": 0.001}}, T, True), True)
check("W4: no success, no contradiction",
      b5.w4_contradiction({"numbers": {"d_phenix": 0.03, "d_gemmi": 0.03,
                                       "d_refmac": 0.03}}, T, False), False)

# The round-4 default is untouched: its own suite re-runs green under the
# parameterized judge.
import subprocess
proc = subprocess.run([sys.executable,
                       str(REPO / "scripts/test_bench_recover.py")],
                      capture_output=True, text=True)
# The count is a floor, not a pin — an exact literal goes stale the moment
# the recover suite legitimately grows (it did in round 9: 9 -> 12).
import re as _re
_m = _re.search(r"(\d+) checks passed", proc.stdout)
check("round-4 suite still green under the fit_fn parameterization",
      proc.returncode == 0 and _m is not None and int(_m.group(1)) >= 9, True)

print(f"\n{PASSED} checks passed")
