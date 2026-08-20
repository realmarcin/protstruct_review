#!/usr/bin/env python3
"""Guard: NEXT_TASKS milestone dates match the git merge trail (#387 class).

The date/attribution-precision class recurred in consecutive
reconciliations (#372, #386) — a milestone row stating a date that matches
neither end of its PRs' actual merge range. Per the repo's own lesson
("the signal to build the guard is the second recurrence"), this check
mechanizes it: every NC-table row that states both PR numbers and a date
(or date range) is verified against the squash-merge commits on the
current branch — each cited PR's commit date must fall inside the stated
range, padded by one day on each side for timezone skew (rows may state
local dates; commits carry their own zone).

Offline by design: the arbiter is `git log`, not the GitHub API — the
reconciliation rule already falls back to git log when there is no
network, so the guard must hold to the same source.

Scope: the NEGATIVE-CONTROL table only. The tolerance table's dates are
round dates under the pre-squash convention (its rows 17/18 cite one PR
from two rounds, and several rows have no PR at all), so a merge-trail
check there would enforce a convention that table never used. The guard's
first live run proved the scoping: it flagged the two #69 tolerance rows
as false positives while catching a real NC-5 drift (#346 merged
2026-08-15, row said 2026-08-17).

Kept importable (`parse_rows`, `within`) so `test_next_tasks_dates.py`
drives the parsing and range logic on synthetic rows.

    python3 scripts/check_next_tasks_dates.py     # exits 1 on any drift
"""
from __future__ import annotations

import datetime as dt
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
NEXT_TASKS = REPO / "NEXT_TASKS.md"

# A dated milestone row: PR refs in the second cell, a parenthesized date
# or date range beside them. Rows without a date are not checked.
_ROW = re.compile(r"^\|[^|]*\|(?P<prs>[^|]*)\|")
_DATE_SPAN = re.compile(
    r"\((?:merged\s+)?(?P<a>\d{4}-\d{2}-\d{2})"
    r"(?:\s*(?:→|\.\.|–|-)\s*(?:(?P<b>\d{4}-\d{2}-\d{2})|(?P<bday>\d{1,2})))?"
    r"(?:\s*UTC)?\)")
_PR_REF = re.compile(r"#(\d{2,5})")

SKEW = dt.timedelta(days=1)


def nc_section(text: str) -> str:
    """The negative-control table's section, by its heading."""
    m = re.search(r"^## The negative-control track.*?(?=^## )", text,
                  re.M | re.S)
    return m.group(0) if m else ""


def parse_rows(text: str) -> list[dict]:
    """Every table row that states PR refs AND a date (range)."""
    out = []
    for line in text.splitlines():
        m = _ROW.match(line.strip())
        if not m:
            continue
        cell = m.group("prs")
        span = _DATE_SPAN.search(cell)
        prs = [int(x) for x in _PR_REF.findall(cell)]
        if not span or not prs:
            continue
        a = dt.date.fromisoformat(span.group("a"))
        if span.group("b"):
            b = dt.date.fromisoformat(span.group("b"))
        elif span.group("bday"):
            day = int(span.group("bday"))
            # #391: a short-form range crossing a month boundary
            # ("2026-08-30→2") ends in the NEXT month.
            if day >= a.day:
                b = a.replace(day=day)
            else:
                nxt = (a.replace(day=1) + dt.timedelta(days=32)).replace(day=1)
                b = nxt.replace(day=day)
        else:
            b = a
        out.append({"line": line.strip()[:60], "prs": prs,
                    "start": a, "end": b})
    return out


def within(commit_date: dt.date, start: dt.date, end: dt.date) -> bool:
    return start - SKEW <= commit_date <= end + SKEW


def merge_dates() -> dict[int, dt.date]:
    """PR number -> commit date, from squash-merge subjects `... (#N)`."""
    proc = subprocess.run(
        ["git", "-C", str(REPO), "log", "--format=%cs %s"],
        capture_output=True, text=True)
    out: dict[int, dt.date] = {}
    for line in proc.stdout.splitlines():
        m = re.match(r"(\d{4}-\d{2}-\d{2}) .*\(#(\d+)\)\s*$", line)
        if m:
            out.setdefault(int(m.group(2)), dt.date.fromisoformat(m.group(1)))
    return out


def main() -> int:
    rows = parse_rows(nc_section(NEXT_TASKS.read_text()))
    merged = merge_dates()
    failures = []
    checked = 0
    for row in rows:
        for pr in row["prs"]:
            if pr not in merged:
                continue          # not a squash-merge on this branch
            checked += 1
            if not within(merged[pr], row["start"], row["end"]):
                failures.append(
                    f"#{pr} merged {merged[pr]} but its row states "
                    f"{row['start']}..{row['end']} — {row['line']}…")
    if failures:
        print("NEXT_TASKS dates are out of step with the merge trail "
              "(#372/#386 class):")
        for f in failures:
            print(f"  - {f}")
        return 1
    print(f"NEXT_TASKS milestone dates match the merge trail "
          f"({checked} PR dates over {len(rows)} dated rows)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
