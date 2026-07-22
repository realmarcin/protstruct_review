#!/usr/bin/env python3
"""Unit tests for t15_ss_agreement pure logic (no mkdssp/biotite needed).

The end-to-end run is exercised manually against real oracles; these tests cover
the parsing, three-state collapse, and agreement math so they run anywhere.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import t15_ss_agreement as t15  # noqa: E402


def _check(cond: bool, msg: str) -> None:
    if not cond:
        print(f"FAIL  {msg}")
        raise SystemExit(1)
    print(f"PASS  {msg}")


# A tiny slice of real legacy-DSSP output (header + three residue lines).
_DSSP_SAMPLE = """\
  #  RESIDUE AA STRUCTURE BP1 BP2  ACC     N-H-->O
    1    1 A D              0   0  148      0, 0.0
    2    2 A V  E     -a   89   0A  71      1,-0.1
    8    8 A L  H  > S+     0   0   14     88,-1.0
"""


def test_parse_dssp() -> None:
    parsed = t15._parse_dssp(_DSSP_SAMPLE)
    _check(parsed == {("A", "1", ""): "C", ("A", "2", ""): "E", ("A", "8", ""): "H"},
           f"_parse_dssp collapses to HEC keyed on (chain,resnum,icode) (got {parsed})")


def test_collapse_maps() -> None:
    _check(t15._DSSP_TO_HEC.get("G") == "H" and t15._DSSP_TO_HEC.get("B") == "E",
           "DSSP 3-10 helix -> H and bridge -> E")
    _check(t15._DSSP_TO_HEC.get("T", "C") == "C", "DSSP turn -> C via default")
    _check(t15._BIOTITE_TO_HEC == {"a": "H", "b": "E", "c": "C"}, "biotite a/b/c -> HEC")


def test_agreement() -> None:
    a = {("A", "1", ""): "C", ("A", "2", ""): "E", ("A", "3", ""): "H", ("A", "4", ""): "H"}
    b = {("A", "1", ""): "C", ("A", "2", ""): "E", ("A", "3", ""): "C", ("A", "9", ""): "H"}
    r = t15.agreement(a, b)
    # shared residues: 1,2,3 → 2 of 3 agree; residue 4 (dssp-only) and 9 (biotite-only) excluded.
    _check(r["n_scored"] == 3, f"agreement scores only shared residues (got {r['n_scored']})")
    _check(r["n_agree"] == 2 and r["fraction"] == round(2 / 3, 4),
           f"agreement fraction = 2/3 (got {r['fraction']})")
    _check(r["n_dssp"] == 4 and r["n_biotite"] == 4 and r["n_dropped"] == 2,
           f"per-assigner + dropped counts reported (got dssp={r['n_dssp']} "
           f"biotite={r['n_biotite']} dropped={r['n_dropped']})")


def test_insertion_code_not_conflated() -> None:
    # 10 and 10A must be distinct residues, not merged.
    a = {("A", "10", ""): "H", ("A", "10", "A"): "E"}
    b = {("A", "10", ""): "H", ("A", "10", "A"): "E"}
    r = t15.agreement(a, b)
    _check(r["n_scored"] == 2 and r["n_agree"] == 2,
           f"insertion code keeps 10 and 10A distinct (got n_scored={r['n_scored']})")


def main() -> int:
    test_parse_dssp()
    test_collapse_maps()
    test_agreement()
    test_insertion_code_not_conflated()
    print("\nall t15_ss_agreement unit tests passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
