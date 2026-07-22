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
           "flexible termini raise the whole-chain mean")


def test_ordered_core_precision() -> None:
    # 5.9 Å flexible tail excluded (> 2 Å); core = the three ordered residues.
    core_mean, n_core = t17.ordered_core_precision([0.14, 0.20, 0.30, 5.9])
    _check(n_core == 3 and core_mean == round((0.14 + 0.20 + 0.30) / 3, 3),
           f"ordered-core excludes flexible residues (got mean={core_mean}, n={n_core})")
    # The core figure is insensitive to the flexible tail that dominates the whole-chain mean.
    _check(t17.ordered_core_precision([0.2, 0.2, 8.0])[0] == 0.2,
           "ordered-core is insensitive to a large flexible tail")


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
    test_ordered_core_precision()
    test_empty_fails()
    print("\nall t17_nmr_ensemble unit tests passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
