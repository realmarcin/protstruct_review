#!/usr/bin/env python3
"""Tests for the lognormal goodness-of-fit guard (P3c).

The Ca UTL that sets the §4 `d_min >= 2.5 A` Ca band rests on log(Ca) being normal. This
guards that assumption two ways: the Filliben PPCC functions behave, and — the load-bearing
part — the guard actually PASSES on the committed round 37/38/41 data, so if future entries
break the lognormal assumption this test fails rather than the band silently going wrong.

Run directly: `python3 scripts/test_xray_band_coverage.py` (no network, no scipy).
"""
from __future__ import annotations

import math
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze_xray_band_coverage import (  # noqa: E402
    filliben_critical, filliben_ppcc, pooled)

FAILS: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    if not cond:
        FAILS.append(f"{name}{': ' + detail if detail else ''}")


def test_ppcc_high_for_normal_like() -> None:
    # A symmetric, evenly spaced sample is close to normal -> PPCC near 1.
    xs = [x / 10 for x in range(-30, 31)]  # -3.0 .. 3.0
    r = filliben_ppcc(xs)
    check("PPCC high for symmetric sample", r > 0.98, f"got {r:.4f}")


def test_ppcc_low_for_strong_skew() -> None:
    # A hard right-skewed sample (exponential-ish) is not normal -> PPCC well below 1.
    xs = [math.exp(x / 5) for x in range(0, 60)]
    r = filliben_ppcc(xs)
    check("PPCC low for skewed sample", r < 0.95, f"got {r:.4f}")


def test_log_transform_raises_ppcc_on_skew() -> None:
    xs = [math.exp(x / 5) for x in range(0, 60)]
    logxs = [math.log(x) for x in xs]
    check("log transform improves PPCC of a lognormal sample",
          filliben_ppcc(logxs) > filliben_ppcc(xs),
          f"log {filliben_ppcc(logxs):.4f} vs raw {filliben_ppcc(xs):.4f}")


def test_critical_interpolates_and_clamps() -> None:
    check("critical(44) interpolates 40..50", abs(filliben_critical(44) - 0.9735) < 1e-3,
          f"got {filliben_critical(44):.4f}")
    check("critical clamps below table", filliben_critical(5) == 0.9198)
    check("critical clamps above table", filliben_critical(500) == 0.9870)


def test_guard_passes_on_committed_data() -> None:
    """The load-bearing regression: the lognormal assumption holds on the committed set."""
    ca = pooled("ca_shift_rmsd")
    n = len(ca)
    logca = [math.log(x) for x in ca]
    ppcc_log, ppcc_raw = filliben_ppcc(logca), filliben_ppcc(ca)
    crit = filliben_critical(n)
    check("committed log(Ca) passes the PPCC critical value",
          ppcc_log >= crit, f"PPCC {ppcc_log:.4f} < critical {crit:.4f} (n={n})")
    check("committed log(Ca) beats raw (log transform justified)",
          ppcc_log > ppcc_raw, f"log {ppcc_log:.4f} !> raw {ppcc_raw:.4f}")


def main() -> int:
    for fn in sorted(k for k in globals() if k.startswith("test_")):
        globals()[fn]()
    if FAILS:
        print("xray_band_coverage GoF tests FAILED:")
        for f in FAILS:
            print("  -", f)
        return 1
    print("xray_band_coverage GoF tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
