#!/usr/bin/env python3
"""Unit tests for check_driver_thresholds.py — the registry→consumer drift gate.

Each test must FAIL if the guard's logic is broken (round 27). No network, no PHENIX.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PASSED = 0


def load(name: str):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / f"{name}.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


def check(label, got, want) -> None:
    global PASSED
    if got != want:
        print(f"FAIL  {label}: got {got!r}, want {want!r}", file=sys.stderr)
        raise SystemExit(1)
    print(f"PASS  {label} (got {got!r})")
    PASSED += 1


def main() -> int:
    m = load("check_driver_thresholds")

    # A retired value stated on a live (non-history) line is a defect.
    check("retired value on a live line is flagged",
          m.stale_hits("agreement |Δ| ≤ 0.10 Å.", ["≤ 0.10 Å"]),
          ["≤ 0.10 Å"])

    # The same value shown as history is exempt (each marker).
    for mark in ("pre-benchmark", "originally", "round-5", "catalog's", "was a "):
        check(f"history marker {mark!r} exempts the line",
              m.stale_hits(f"({mark} template) ≤ 0.10 Å", ["≤ 0.10 Å"]),
              [])

    # A clean consumer has no hits.
    check("clean consumer has no hits",
          m.stale_hits("|Δ| ≤ 0.03 Å per §3", ["≤ 0.10 Å"]),
          [])

    # registry_value extracts the current figure, and detects a changed one.
    check("registry_value extracts the current CA RMSD",
          m.registry_value(m.CHECKS[0]["registry"], "| CA RMSD | \\|Δ\\| ≤ **0.03 Å**"),
          "0.03")
    check("registry_value sees a changed value",
          m.registry_value(m.CHECKS[0]["registry"], "| CA RMSD | \\|Δ\\| ≤ **0.05 Å**"),
          "0.05")
    check("registry_value returns None on a reworded row",
          m.registry_value(m.CHECKS[0]["registry"], "| CA RMSD | agreement is tight"),
          None)

    # Every CHECKS metric must still be derivable from the LIVE registry, and match.
    registry = (REPO / "ref/thresholds_and_standards.md").read_text()
    for c in m.CHECKS:
        check(f"live registry still yields {c['metric']}",
              m.registry_value(c["registry"], registry), c["current"])

    print(f"\nall driver-threshold guard tests passed ({PASSED} checks)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
