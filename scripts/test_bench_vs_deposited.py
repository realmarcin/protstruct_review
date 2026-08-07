#!/usr/bin/env python3
"""Tests for bench_vs_deposited's wwPDB reference selection (#281).

The rotamer/Ramachandran OUTLIER % must be counted from the validation report's own
per-residue `rama=`/`rota=` verdicts — the same source as favored % and the rotamer-name
agreement — NOT from `key_validation_stats`' `protein_sidechains.percent_outliers`, which
is a broader sidechain metric inconsistent with the per-residue rotamer verdicts.

Run directly: `python3 scripts/test_bench_vs_deposited.py` (no network, no phenix).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bench_vs_deposited import _RES_RAMA, _RES_ROTA, favored_pct, outlier_pct  # noqa: E402

FAILS: list[str] = []


def check(name: str, got, want) -> None:
    if got != want:
        FAILS.append(f"{name}: got {got!r}, want {want!r}")


# A tiny report fragment: rota= carries rotamer NAMES for non-outliers and the literal
# "OUTLIER" for the two rotamer outliers; rama= carries Favored/Allowed/OUTLIER verdicts.
XML = (
    '<ModelledSubgroup rama="Favored" rota="m-10" chain="A" resnum="1" resname="MET">'
    '<ModelledSubgroup rama="Favored" rota="OUTLIER" chain="A" resnum="2" resname="LEU">'
    '<ModelledSubgroup rama="Allowed" rota="mt" chain="A" resnum="3" resname="LYS">'
    '<ModelledSubgroup rama="OUTLIER" rota="OUTLIER" chain="A" resnum="4" resname="SER">'
    '<ModelledSubgroup rama="Favored" rota="p" chain="A" resnum="5" resname="THR">'
)


def test_rota_outlier_from_xml_verdicts() -> None:
    # 2 rota="OUTLIER" of 5 rota residues = 40.0 %
    check("rota outlier % from XML", outlier_pct(XML, _RES_ROTA), 40.0)


def test_rama_outlier_from_xml_verdicts() -> None:
    # 1 rama="OUTLIER" of 5 rama residues = 20.0 %
    check("rama outlier % from XML", outlier_pct(XML, _RES_RAMA), 20.0)


def test_zero_outliers_is_zero_not_none() -> None:
    # rota= all names, no OUTLIER -> the answer is 0.0 %, not "unmeasured" (None).
    clean = (
        '<ModelledSubgroup rota="m-10" resnum="1">'
        '<ModelledSubgroup rota="mt" resnum="2">'
        '<ModelledSubgroup rota="p" resnum="3">'
    )
    check("zero rota outliers -> 0.0", outlier_pct(clean, _RES_ROTA), 0.0)


def test_absent_attribute_is_none() -> None:
    check("no rota attr -> None", outlier_pct("<Entry/>", _RES_ROTA), None)


def test_favored_still_counts_from_xml() -> None:
    # 3 Favored of 5 rama residues = 60.0 %; unchanged by the fix.
    check("favored % from XML", favored_pct(XML, _RES_RAMA), 60.0)


def test_regression_xml_not_api_on_real_6le5() -> None:
    """The bug's canary, on the real cached report if present.

    6LE5: the per-residue XML marks 9 rota="OUTLIER" of 1763 (0.51 %, matching
    phenix.rotalyze), where key_validation_stats' protein_sidechains reports 3.35 %.
    outlier_pct MUST return the XML figure, proving it does not consult the API.
    """
    cached = Path("/tmp/round45_cache/6le5_validation.xml")
    if not cached.exists():
        print("  (skip real-6LE5 regression: cached validation.xml not present)")
        return
    xml = cached.read_text(errors="ignore")
    got = outlier_pct(xml, _RES_ROTA)
    check("6LE5 rota outlier % is XML 0.51, not API 3.35", got, 0.51)


def main() -> int:
    for fn in sorted(k for k in globals() if k.startswith("test_")):
        globals()[fn]()
    if FAILS:
        print("bench_vs_deposited tests FAILED:")
        for f in FAILS:
            print("  -", f)
        return 1
    print("bench_vs_deposited tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
