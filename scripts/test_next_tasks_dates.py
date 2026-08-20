#!/usr/bin/env python3
"""Unit tests for the NEXT_TASKS date guard (#372/#386 class).

Pinned: NC-section scoping (the tolerance table's round-date convention
must not be checked), the row grammar (single date, arrow range,
short-form range, 'merged' prefix, UTC suffix), and the skew window.
Network- and git-free: the git lookup is integration, exercised by the
guard's own run in validate.sh."""
from __future__ import annotations

import datetime as dt
import importlib.util
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PASSED = 0


def load(name):
    spec = importlib.util.spec_from_file_location(
        name, REPO / "scripts" / f"{name}.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


def check(label, got, want):
    global PASSED
    if got != want:
        print(f"FAIL  {label}: got {got!r}, want {want!r}")
        sys.exit(1)
    PASSED += 1
    print(f"PASS  {label}")


g = load("check_next_tasks_dates")

DOC = """\
# Next tasks

## The negative-control track (x)

| Milestone | PR | Outcome |
|---|---|---|
| A | [#294](url) (2026-08-08) | planned |
| B | #299, #305 | undated — skipped |
| C | #373/#376/#378 (merged 2026-08-17→19) | range |
| D | #379/#383 (merged 2026-08-19→20 UTC) | short range, UTC |

## Where the tolerance work stands

| 17 | [#69](url) (2026-07-30) | outside the NC section |
"""

sec = g.nc_section(DOC)
check("NC section excludes the tolerance table", "#69" in sec, False)
rows = g.parse_rows(sec)
check("dated NC rows parsed", len(rows), 3)
check("single date is a degenerate range",
      (rows[0]["start"], rows[0]["end"]),
      (dt.date(2026, 8, 8), dt.date(2026, 8, 8)))
check("arrow range parses", (rows[1]["start"], rows[1]["end"]),
      (dt.date(2026, 8, 17), dt.date(2026, 8, 19)))
check("short-form day + UTC suffix parses",
      (rows[2]["start"], rows[2]["end"]),
      (dt.date(2026, 8, 19), dt.date(2026, 8, 20)))
check("all PR refs collected", rows[1]["prs"], [373, 376, 378])
check("undated rows are skipped",
      any(299 in r["prs"] for r in rows), False)

# #391: a short-form range crossing a month boundary rolls forward.
rows_mb = g.parse_rows(g.nc_section(
    "## The negative-control track (x)\n\n"
    "| E | #400 (merged 2026-08-30→2) | month boundary |\n\n## Next\n"))
check("short-form range crosses the month boundary",
      (rows_mb[0]["start"], rows_mb[0]["end"]),
      (dt.date(2026, 8, 30), dt.date(2026, 9, 2)))

d = dt.date(2026, 8, 18)
check("inside the range passes", g.within(d, d, d), True)
check("one-day skew passes", g.within(d, dt.date(2026, 8, 19),
                                      dt.date(2026, 8, 19)), True)
check("two days out fails", g.within(d, dt.date(2026, 8, 20),
                                     dt.date(2026, 8, 21)), False)

print(f"\n{PASSED} checks passed")
