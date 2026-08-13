#!/usr/bin/env python3
"""Gate: no committed QDS rests a gradeable task on cctbx-only evidence (#315).

The emitter enforces this at emission time (`_check_trust_invariant`); this
check covers the other road into the repo — a hand-edited or historical QDS
file. For every committed `QDS_*.yaml`: a coverage row whose gap is cctbx-only
or unknown-family must either carry its WAIVED annotation (with the matching
waiver block present) or belong to a sheet issued before the invariant existed
(CUTOVER, printed as a named grandfather — history is history, but it is
listed, not silent).

Network-free. `--root` exists for the tests.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

CUTOVER = "2026-08-13"          # the date the invariant became enforceable


def check_sheet(path: Path, qds: dict, failures: list[str],
                grandfathered: list[str]) -> None:
    issued = str(qds.get("issued_at", ""))[:10]
    waived_tasks = {w.get("catalog_task_ref")
                    for w in qds.get("cross_tool_waivers", [])}
    for row in (qds.get("cross_tool_coverage") or {}).get("task_coverage", []):
        gap = row.get("gap_status", "")
        if not (gap.startswith("open — cctbx only") or gap.startswith("unknown")):
            continue
        task = row.get("catalog_task_ref")
        if "WAIVED" in gap and task in waived_tasks:
            continue
        if issued and issued < CUTOVER:
            grandfathered.append(f"{path.name}: {task} ({gap[:40]}…) — "
                                 f"issued {issued}, predates the invariant")
            continue
        failures.append(f"{path.name}: task {task} is {gap!r} with no "
                        f"matching waiver (#315)")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=str(Path(__file__).resolve().parent.parent))
    args = ap.parse_args()
    root = Path(args.root)
    failures: list[str] = []
    grandfathered: list[str] = []

    for path in sorted((root / "data").rglob("QDS_*.yaml")):
        try:
            doc = yaml.safe_load(path.read_text()) or {}
        except (yaml.YAMLError, OSError) as exc:
            failures.append(f"{path.name}: unreadable ({type(exc).__name__})")
            continue
        for qds in doc.get("quality_data_sheets", []) or []:
            check_sheet(path, qds, failures, grandfathered)

    for note in grandfathered:
        print(f"  grandfathered: {note}")
    if failures:
        for f in failures:
            print(f"FAIL  {f}")
        print(f"{len(failures)} trust-invariant failure(s)")
        return 1
    print(f"QDS trust invariant holds "
          f"({len(grandfathered)} grandfathered row(s) listed above)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
