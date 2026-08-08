#!/usr/bin/env python3
"""Tests for the flip-set confident-conflict measure (#287, round 48).

A genuine conflict counts only when `reduce` is confident (category F/K) and `reduce2`
disagrees on the flip; `reduce` categories X (uncertain) / C (clashes either way) are one
builder declining to commit, not a conflict, and must be excluded from the load-bearing
count while staying in the raw diagnostic.

Run directly: `python3 scripts/test_bench_t14_flip_sets.py` (no network, no builders).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bench_t14_flip_sets import confident_conflicts  # noqa: E402

FAILS: list[str] = []


def check(name: str, got, want) -> None:
    if got != want:
        FAILS.append(f"{name}: got {got!r}, want {want!r}")


# reduce calls: (flipped_bool, category). reduce2 calls: (flipped_bool, "F"/"K").
REDUCE = {
    ("A", 1, "ASN"): (True, "F"),    # confident flip
    ("A", 2, "GLN"): (False, "K"),   # confident keep
    ("A", 3, "HIS"): (True, "X"),    # uncertain
    ("A", 4, "ASN"): (False, "C"),   # clashes either way
    ("A", 5, "GLN"): (True, "F"),    # confident flip, agrees below
}
REDUCE2 = {
    ("A", 1, "ASN"): (False, "K"),   # disagrees with confident F -> CONFLICT
    ("A", 2, "GLN"): (True, "F"),    # disagrees with confident K -> CONFLICT
    ("A", 3, "HIS"): (False, "K"),   # disagrees but reduce was X -> not a conflict
    ("A", 4, "ASN"): (True, "F"),    # disagrees but reduce was C -> not a conflict
    ("A", 5, "GLN"): (True, "F"),    # agrees -> not a disagreement at all
}


def test_confident_conflicts_only_F_K_disagreements() -> None:
    cc = confident_conflicts(REDUCE, REDUCE2)
    check("only the two confident disagreements count", cc, [("A", 1, "ASN"), ("A", 2, "GLN")])


def test_uncertain_and_clash_excluded() -> None:
    cc = confident_conflicts(REDUCE, REDUCE2)
    check("X-category disagreement excluded", ("A", 3, "HIS") not in cc, True)
    check("C-category disagreement excluded", ("A", 4, "ASN") not in cc, True)


def test_agreement_is_not_a_conflict() -> None:
    cc = confident_conflicts(REDUCE, REDUCE2)
    check("agreeing residue not counted", ("A", 5, "GLN") not in cc, True)


def test_only_shared_residues() -> None:
    cc = confident_conflicts({("A", 9, "ASN"): (True, "F")}, REDUCE2)
    check("residue only in reduce is not compared", cc, [])


def main() -> int:
    for fn in sorted(k for k in globals() if k.startswith("test_")):
        globals()[fn]()
    if FAILS:
        print("bench_t14 flip-set tests FAILED:")
        for f in FAILS:
            print("  -", f)
        return 1
    print("bench_t14 flip-set tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
