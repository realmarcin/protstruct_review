#!/usr/bin/env python3
"""Unit tests for t16_interface_quality pure logic (no DockQ binary needed).

The end-to-end DockQ run is exercised manually against real structures; these
tests cover the CAPRI band boundaries and DockQ-JSON extraction so they run
anywhere.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import t16_interface_quality as t16  # noqa: E402


def _check(cond: bool, msg: str) -> None:
    if not cond:
        print(f"FAIL  {msg}")
        raise SystemExit(1)
    print(f"PASS  {msg}")


def test_capri_bands() -> None:
    # Boundaries from Basu & Wallner 2016: High>=0.80, Medium[0.49,0.80),
    # Acceptable[0.23,0.49), Incorrect<0.23.
    cases = {
        1.0: "High", 0.80: "High", 0.799: "Medium", 0.49: "Medium",
        0.489: "Acceptable", 0.23: "Acceptable", 0.229: "Incorrect", 0.0: "Incorrect",
    }
    for score, expected in cases.items():
        got = t16.capri_class(score)
        _check(got == expected, f"DockQ {score} -> {expected} (got {got})")


def test_extract() -> None:
    fake = {
        "GlobalDockQ": 0.5123,
        "best_mapping_str": "AB:AB",
        "best_result": {"AB": {"DockQ": 0.5123, "iRMSD": 2.1, "LRMSD": 4.4, "fnat": 0.6}},
    }
    s = t16.extract(fake)
    _check(s["dockq"] == 0.5123, f"extract global DockQ (got {s['dockq']})")
    _check(s["capri"] == "Medium", f"extract derives CAPRI class (got {s['capri']})")
    _check(s["mapping"] == "AB:AB" and "AB" in s["interfaces"],
           "extract carries mapping + per-interface breakdown")


def main() -> int:
    test_capri_bands()
    test_extract()
    print("\nall t16_interface_quality unit tests passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
