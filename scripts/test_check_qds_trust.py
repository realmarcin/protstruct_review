#!/usr/bin/env python3
"""Unit tests for the QDS trust-invariant gate (#315).

Fixture-driven: post-cutover sheets with unwaived cctbx-only rows must fail;
waived rows and pre-cutover history must pass (history is listed, not silent).
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
GUARD = REPO / "scripts" / "check_qds_trust_invariant.py"
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


def sheet(issued, gap, waived=False):
    q = {"id": "QDS_x", "issued_at": issued,
         "cross_tool_coverage": {"id": "c", "task_coverage": [
             {"id": "r", "catalog_task_ref": "T06", "gap_status": gap}]}}
    if waived:
        q["cross_tool_waivers"] = [{"id": "w", "catalog_task_ref": "T06",
                                    "reason": "x", "as_of_date": "2026-08-13"}]
    return {"quality_data_sheets": [q]}


def write(root: Path, doc):
    d = root / "data" / "x"
    d.mkdir(parents=True, exist_ok=True)
    (d / "QDS_fixture.yaml").write_text(yaml.safe_dump(doc, sort_keys=False))


with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    write(root, sheet("2026-09-01", "open — cctbx only"))
    code, out = run_guard(root)
    check("post-cutover unwaived cctbx-only fails", code, 1)
    check("failure names task and rule", "T06" in out and "#315" in out, True)

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    write(root, sheet("2026-09-01",
                      "open — cctbx only — WAIVED 2026-08-13: no gemmi path",
                      waived=True))
    code, out = run_guard(root)
    check("waived row passes", code, 0)

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    write(root, sheet("2026-09-01",
                      "open — cctbx only — WAIVED 2026-08-13: annotation only"))
    code, out = run_guard(root)
    check("WAIVED annotation without the waiver block fails", code, 1)

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    write(root, sheet("2026-05-01", "open — cctbx only"))
    code, out = run_guard(root)
    check("pre-cutover history passes", code, 0)
    check("history is listed, not silent", "grandfathered" in out, True)

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    write(root, sheet("2026-09-01", "non-cctbx only"))
    code, out = run_guard(root)
    check("non-cctbx-only is not gated (nothing to distrust)", code, 0)

print(f"\n{PASSED} checks passed")
