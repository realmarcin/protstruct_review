#!/usr/bin/env python3
"""Unit tests for t17_nmr_ensemble pure logic (no biotite/ensemble needed).

The end-to-end ensemble run is exercised manually against a real NMR ensemble;
this covers the precision arithmetic so it runs anywhere.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import t17_nmr_ensemble as t17  # noqa: E402


def _check(cond: bool, msg: str) -> None:
    if not cond:
        print(f"FAIL  {msg}")
        raise SystemExit(1)
    print(f"PASS  {msg}")


def test_mean_precision() -> None:
    _check(t17.mean_precision([0.1, 0.2, 0.3]) == 0.2,
           f"mean precision of per-residue RMSF (got {t17.mean_precision([0.1, 0.2, 0.3])})")
    _check(t17.mean_precision([0.139, 5.927, 0.4]) == round((0.139 + 5.927 + 0.4) / 3, 3),
           "flexible termini raise the mean")


def test_empty_fails() -> None:
    try:
        t17.mean_precision([])
    except SystemExit:
        print("PASS  empty RMSF list fails loudly")
        return
    print("FAIL  empty RMSF list did not fail")
    raise SystemExit(1)


def main() -> int:
    test_mean_precision()
    test_empty_fails()
    print("\nall t17_nmr_ensemble unit tests passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
