#!/usr/bin/env python3
"""Unit tests for `round_figures.py`.

The tool is not a gate, which is exactly why it needs these: a gate that breaks stops
the build, and a helper that breaks prints a plausible number that somebody pastes into
a round document. #196 was precisely that — the classifier failed, every real issue was
explained away as "not in the record", and the headline read `: 0` with exit 0.

Every case below is a PARTITION of the failure space, not a regression test for one
incident. The cases where the tool returns a WRONG number quietly come first, because
this file's entire subject is that a confident wrong count is worse than no count.

Network-free by construction: ranges are chosen to sit wholly inside the committed
findings record, and the one path that would reach `gh` is exercised by substituting the
sibling loader rather than by breaking real credentials.
"""
from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PASSED = 0


def load():
    spec = importlib.util.spec_from_file_location("rf", REPO / "scripts" / "round_figures.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["rf"] = module
    spec.loader.exec_module(module)
    return module


def check(label: str, got, want) -> None:
    global PASSED
    if got != want:
        print(f"FAIL  {label}: got {got!r}, want {want!r}")
        sys.exit(1)
    PASSED += 1
    print(f"PASS  {label}")


def raises(fn) -> str:
    try:
        fn()
    except SystemExit as e:
        return str(e)
    except BaseException as e:  # noqa: BLE001 -- a traceback is itself the defect
        return f"UNCAUGHT {type(e).__name__}: {e}"
    return "no exception"


rf = load()

# A range wholly inside the committed record: no gap, so no `gh`, so no network.
IN_RECORD = "149-151"


# --- #196: the classifier failing must not look like a fact about the numbers -------

def _break_sibling(exc):
    rf._sibling = lambda: (_ for _ in ()).throw(exc)


_saved_sibling = rf._sibling
# The gap must be real for the fallback to run at all, so this range deliberately
# straddles the end of the record.
GAP = "186-188"

_break_sibling(RuntimeError("boom"))
_broken = rf.issues(GAP)
check("a broken sibling does not silently report a count",
      any(l.lstrip().startswith("!! UNRESOLVED") for l in _broken), True)
check("  and the headline says the number is a lower bound, not the answer",
      "LOWER BOUND" in _broken[0], True)
check("  and the unresolved numbers are NOT explained away as PRs",
      any("not in the record" in l for l in _broken), False)

# #197: SystemExit subclasses BaseException, so `except Exception` did not catch the
# sibling's `gh issue list` failure and the whole tool aborted -- printing nothing at
# all, including the part that needed no network.
_break_sibling(SystemExit("gh: HTTP 401"))
check("a SystemExit from the sibling degrades instead of aborting",
      any(l.lstrip().startswith("!! UNRESOLVED") for l in rf.issues(GAP)), True)
check("  and _real_issue_numbers reports 'could not tell' as None, not as an empty set",
      rf._real_issue_numbers(186, 188), None)

rf._sibling = _saved_sibling


# --- the record-only path is unaffected by any of the above -------------------------

_clean = rf.issues(IN_RECORD)
check("a range wholly in the record needs no classifier at all",
      [l.lstrip().startswith("!!") for l in _clean], [False] * len(_clean))
check("  and reports the issues it holds", _clean[0].split(":")[1].split()[0], "3")

# The same range under a broken sibling must still be answered in full -- this is the
# "degrades to the record alone" promise, and #197 broke it for exactly this case.
_break_sibling(SystemExit("gh: HTTP 401"))
check("the record-only answer survives a dead classifier", rf.issues(IN_RECORD), _clean)
rf._sibling = _saved_sibling


# --- #199: the annotation must claim only what was checked --------------------------

_never = rf.issues("9990-9995")
check("numbers that were never issued are not asserted to be PRs",
      any("filed since the last --refresh" in l for l in _never), False)
check("  and the count is still 0", _never[0].rstrip().endswith(": 0   ()"), True)


# --- #198: a user-supplied regex fails like every other user input -------------------

check("a malformed --commits regex exits with a diagnosis, not a traceback",
      "not a valid regex" in raises(lambda: rf.commits("[unclosed")), True)
check("  and a valid one still matches",
      rf.commits("Reconcile NEXT_TASKS")[0].startswith("commits matching regex"), True)


# --- the input guards that already existed, kept under test -------------------------

for bad, want in [("186-183", "reversed"), ("abc", "not a number"),
                  ("183-", "trailing"), ("", "not a number"), ("1-2-3", "not a number")]:
    check(f"--issues {bad!r} exits cleanly", want in raises(lambda b=bad: rf.issues(b)), True)


# --- #200: int vs str made the gh-missing path re-report resolved issues -------------
# Structural rather than behavioural: the branch is now unreachable (a missing `gh`
# fails in the sibling first, so `real` is None), and a test that cannot reach the code
# it names is a test of nothing. Asserting the comparison is well-typed is honest about
# what is being checked.
_src = (REPO / "scripts" / "round_figures.py").read_text()
check("the gh-missing path compares ints to ints",
      bool(re.search(r'failed\.extend\(m for m in missing if m not in \{int\(', _src)), True)


print(f"\nall round_figures unit tests passed ({PASSED} checks)")
