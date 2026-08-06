#!/usr/bin/env python3
"""Unit tests for check_selection_deltas.py — the #255 guard (#261).

Each test must FAIL if the guard's logic is broken; a test that passes either way is
the same class of hole the guard exists to close (round 27). No network, no PHENIX.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PASSED = 0


def load(name: str):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def check(label: str, got, want) -> None:
    global PASSED
    if got != want:
        print(f"FAIL  {label}: got {got!r}, want {want!r}", file=sys.stderr)
        raise SystemExit(1)
    print(f"PASS  {label} (got {got!r})")
    PASSED += 1


def _sel(*ids):
    return {"selected": [{"pdb_id": i, "d_min": 2.5} for i in ids]}


def _deltas(rows, skipped):
    return {"rows": [{"pdb_id": i} for i in rows],
            "skipped": [{"pdb_id": i} for i in skipped]}


def main() -> int:
    m = load("check_selection_deltas")

    # A refined row missing from the selection is reported -- the #255 shape exactly.
    check("a refined id absent from selection is flagged",
          m.reconcile(_sel("A", "B"), _deltas(["A", "1A0C"], [])),
          ["1A0C"])

    # A skipped (refine-failure) id missing from selection is ALSO flagged: it entered
    # the benchmark, so the selection must list it.
    check("a skipped id absent from selection is flagged",
          m.reconcile(_sel("A"), _deltas(["A"], ["FAIL1"])),
          ["FAIL1"])

    # The converse is allowed: selection legitimately holds MORE ids than the deltas,
    # because fetch rejects are selected but never reach the benchmark. This must NOT
    # be reported, or the guard fires on every real round (round 37 has 3 fetch rejects).
    check("fetch rejects in selection but not deltas are NOT flagged",
          m.reconcile(_sel("A", "B", "REJECT1"), _deltas(["A"], ["B"])),
          [])

    # A fully consistent pair is clean.
    check("a complete record reconciles",
          m.reconcile(_sel("A", "B", "C"), _deltas(["A", "B"], ["C"])),
          [])

    # deltas_ids unions rows and skipped.
    check("deltas_ids unions rows and skipped",
          sorted(m.deltas_ids(_deltas(["A"], ["B", "C"]))),
          ["A", "B", "C"])

    # The committed round-37 and round-38 records must pass (they reconcile post-#255).
    import json
    for rnd in ("round37", "round38"):
        sel = json.loads((REPO / f"ref/research/data/{rnd}_xray_selection.json").read_text())
        dl = json.loads((REPO / f"ref/research/data/{rnd}_xray_deltas.json").read_text())
        check(f"committed {rnd} record reconciles", m.reconcile(sel, dl), [])

    print(f"\nall selection/deltas guard tests passed ({PASSED} checks)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
