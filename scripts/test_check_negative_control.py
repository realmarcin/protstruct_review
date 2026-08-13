#!/usr/bin/env python3
"""Unit tests for the negative-control record guard (#312).

Each check builds a synthetic ref/research tree in a temp dir and runs the
guard against it — the guard must both pass a clean tree and fail each drift
class it exists to catch (the #311 provenance error was caught by hand; this
is the mechanization).
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
GUARD = REPO / "scripts" / "check_negative_control_records.py"
PASSED = 0


def check(label: str, got, want) -> None:
    global PASSED
    if got != want:
        print(f"FAIL  {label}: got {got!r}, want {want!r}")
        sys.exit(1)
    PASSED += 1
    print(f"PASS  {label}")


def run_guard(root: Path) -> tuple[int, str]:
    proc = subprocess.run([sys.executable, str(GUARD), "--root", str(root)],
                          capture_output=True, text=True)
    return proc.returncode, proc.stdout + proc.stderr


def make_tree(root: Path, screen=None, enrolled=None, reps=None, doc=None):
    data = root / "ref" / "research" / "data"
    data.mkdir(parents=True, exist_ok=True)
    if screen is not None:
        (data / "negative_control_round9_screen.json").write_text(
            json.dumps(screen))
    if enrolled is not None:
        (data / "negative_control_round9_enrolled.json").write_text(
            json.dumps(enrolled))
    if reps is not None:
        (data / "negative_control_round9_reps.json").write_text(json.dumps(reps))
    if doc is not None:
        (root / "ref" / "research" / "negative_control_round9.md").write_text(doc)


def row(pdb_id, status="screened", enrolled=True):
    r = {"pdb_id": pdb_id, "status": status}
    if status == "screened":
        r["paths"] = {"phenix": {"delta": 0.001}, "gemmi": {"delta": 0.001}}
        r["enrolled"] = enrolled
    return r


CLEAN_SCREEN = {"run": {"run_mode": "full"},
                "rows": [row("1AAA"), row("2BBB", "floor")],
                "d6": {"n_screened": 1, "n_enrolled": 1}}

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    make_tree(root, screen=CLEAN_SCREEN,
              enrolled={"n_enrolled": 1, "entries": [{"pdb_id": "1AAA"}]},
              reps={"initial_representatives": [{"pdb_id": "1AAA",
                                                 "cluster": "c1"}],
                    "clusters": [{"cluster": "c1"}]},
              doc="Attempted 2: 1 floor, 0 data defects, 1 screened.")
    code, out = run_guard(root)
    check("clean tree passes", code, 0)

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    bad = {**CLEAN_SCREEN, "rows": [row("1AAA"), row("1AAA", "floor")]}
    make_tree(root, screen=bad)
    code, out = run_guard(root)
    check("duplicate row ids fail", code, 1)
    check("duplicate message names the file", "duplicate pdb_ids" in out, True)

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    make_tree(root, screen={**CLEAN_SCREEN,
                            "run": {"run_mode": "diagnostic"}})
    code, out = run_guard(root)
    check("diagnostic manifest in a committed record fails", code, 1)
    check("manifest message cites #319", "#319" in out, True)

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    make_tree(root, screen=CLEAN_SCREEN,
              enrolled={"n_enrolled": 1, "entries": [{"pdb_id": "9ZZZ"}]})
    code, out = run_guard(root)
    check("enrolled entry absent from screen fails", code, 1)

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    make_tree(root, screen=CLEAN_SCREEN,
              doc="Attempted 2: 1 floor, 0 data defects — screened count lost.")
    code, out = run_guard(root)
    check("round doc missing a headline figure fails", code, 1)
    check("drift message cites the #311 class", "#311" in out, True)

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    make_tree(root, reps={"initial_representatives":
                          [{"pdb_id": "1AAA", "cluster": "ghost"}],
                          "clusters": [{"cluster": "c1"}]})
    code, out = run_guard(root)
    check("representative naming an unknown cluster fails", code, 1)

# The screened-row-missing-delta class: a screened row with a dead path.
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    broken = {"rows": [{"pdb_id": "1AAA", "status": "screened",
                        "paths": {"phenix": {"delta": 0.001},
                                  "gemmi": {"delta": None}}}]}
    make_tree(root, screen=broken)
    code, out = run_guard(root)
    check("screened row with a missing delta fails", code, 1)

# Malformed committed JSON must be a NAMED failure, not a traceback (r1).
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    data = root / "ref" / "research" / "data"
    data.mkdir(parents=True)
    (data / "negative_control_round9_screen.json").write_text("{truncated…")
    code, out = run_guard(root)
    check("malformed record fails by name", code, 1)
    check("malformed message names the file",
          "negative_control_round9_screen.json" in out and
          "malformed" in out, True)
    check("no traceback leaks", "Traceback" in out, False)

print(f"\n{PASSED} checks passed")
