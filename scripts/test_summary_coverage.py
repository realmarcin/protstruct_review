#!/usr/bin/env python3
"""Unit tests for the summary-file coverage and count checks.

These checks previously lived in `scripts/validate.sh` as embedded python, where they
could not be tested — and that is exactly how #157 shipped: both matched any `| ... |`
line anywhere in the file, so an unrelated table with a numeric cell, or a fenced
documentation example, silently satisfied coverage for a round that was genuinely
missing. A gate whose failure modes cannot be exercised is a gate nobody has checked.

Every case below is a PARTITION of the input space, not a regression test for one
incident. Rounds 25 and 26 established that a guard tested only against the case that
motivated it fails the next construct; the false-pass cases are listed first because a
gate that declines to fail is worse than one that complains.
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
        print(f"FAIL  {label}: got {got!r}, want {want!r}")
        sys.exit(1)
    PASSED += 1
    print(f"PASS  {label} (got {got!r})")


cov = load("check_summary_coverage")

TASKS = (REPO / cov.NEXT_TASKS).read_text()
LESSONS = (REPO / cov.LESSONS).read_text()
FINDINGS = cov.load_findings(REPO / cov.FINDINGS)
ROUNDS = cov.rounds_on_disk(REPO)
# A round that does not and will not exist, used to prove the checks can fail at all.
# This was "27" and round 27 was then created, which turned every negative case into a
# false pass -- a fixture that depended on a number staying unused. 999 cannot collide.
ABSENT_ROUND = "999"
ABSENT = ROUNDS + [ABSENT_ROUND]


# --- the committed state passes ----------------------------------------------------

check("NEXT_TASKS covers every round", cov.next_tasks_coverage(TASKS, ROUNDS)["status"], "OK")
check("lessons.md covers every round", cov.lessons_coverage(LESSONS, ROUNDS)["status"], "OK")
check("and both can fail — an absent round is reported",
      [cov.next_tasks_coverage(TASKS, ABSENT)["status"],
       cov.lessons_coverage(LESSONS, ABSENT)["status"]], ["MISSING", "MISSING"])


# --- #157: the two false passes that shipped ---------------------------------------
# Both were verified against the merged gate before this fix: each returned "no rounds
# missing" for a round that had no row at all.

_UNRELATED_TABLE = "\n\n## Priority\n\n| Item | Note |\n|---|---|\n| 999 | unrelated |\n"
check("an unrelated table with a numeric first cell does not satisfy coverage",
      cov.next_tasks_coverage(TASKS + _UNRELATED_TABLE, ABSENT)["status"], "MISSING")

_FENCED_ROW = "\n\n```\n| 999 | [#1](x) | example row for the docs |\n```\n"
check("a fenced example row does not satisfy coverage",
      cov.next_tasks_coverage(TASKS + _FENCED_ROW, ABSENT)["status"], "MISSING")

check("nor does a ~~~ fenced one",
      cov.next_tasks_coverage(TASKS + _FENCED_ROW.replace("```", "~~~"), ABSENT)["status"],
      "MISSING")

# The sibling was exploitable the same way, from the opposite end of the row.
check("an unrelated table's LAST cell does not satisfy lessons coverage",
      cov.lessons_coverage(
          LESSONS + "\n\n## Citations\n\n| Paper | Year |\n|---|---|\n| Some paper | 999 |\n",
          ABSENT)["status"], "MISSING")
check("nor does a fenced example in lessons.md",
      cov.lessons_coverage(LESSONS + "\n\n```\n| A quoted rule | 999 |\n```\n",
                           ABSENT)["status"], "MISSING")

# A round mentioned in prose is not a row.
check("a round named only in prose does not satisfy coverage",
      cov.next_tasks_coverage(TASKS + "\n\nRound 999 did some things.\n", ABSENT)["status"],
      "MISSING")


# --- counts: #155 (a PR counted as a finding) and the rewrite contract --------------

check("the committed defect counts match the record",
      [r["status"] for r in cov.defect_counts(TASKS, FINDINGS)], ["OK", "OK"])

check("a count that includes the round's own PR is caught",
      cov.defect_counts(TASKS.replace("**14 defects** (#139–#153)",
                                      "**15 defects** (#139–#153)"), FINDINGS)[-1]["status"],
      "STALE")

# The docstring promises a reworded claim fails too. It did NOT, in the first draft of
# this script: the claim simply vanished from the results and nothing complained.
check("a reworded claim goes MISSING rather than disappearing",
      cov.defect_counts(TASKS.replace("**14 defects** (#139–#153)", "fourteen defects"),
                        FINDINGS)[-1]["status"], "MISSING")
check("and a claim inside a fence is not counted as the claim",
      cov.defect_counts(TASKS.replace("**14 defects** (#139–#153)", "fourteen defects")
                        + "\n\n```\n**14 defects** (#139–#153)\n```\n",
                        FINDINGS)[-1]["status"], "MISSING")


# --- the spelled-out round count ----------------------------------------------------
# DERIVED, not hardcoded. These tests originally substituted the literal string
# "twenty-six rounds of", and this round changed the file to twenty-seven -- so every
# negative case silently became a no-op substitution and passed. Second fixture in this
# file to break that way, after ABSENT_ROUND; both hardcoded a value the round itself
# moved.
CURRENT = f"{cov.spell(int(ROUNDS[-1]))} rounds of"
STALE_PHRASE = f"{cov.spell(int(ROUNDS[-1]) - 2)} rounds of"

check("the current round count is what the file says", CURRENT in cov.prose(TASKS), True)
check("the round count matches", cov.round_count_claim(TASKS, ROUNDS)["status"], "OK")
check("a stale round count is caught",
      cov.round_count_claim(TASKS.replace(CURRENT, STALE_PHRASE), ROUNDS)["status"], "STALE")
check("and it reports the HIGHEST round, not the number of trail files",
      f"highest round on disk is {ROUNDS[-1]}" in
      cov.round_count_claim(TASKS.replace(CURRENT, STALE_PHRASE), ROUNDS)["detail"], True)
# #160: _WORDS held only {20, 30}, so spell() raised a bare KeyError at 40 and below 20
# -- a gate crashing without a diagnosis thirteen rounds out. Tested across the whole
# supported range, not just the value the repo happens to sit on.
check("spell covers every round from 20 to 99",
      [cov.spell(n) for n in (20, 27, 30, 40, 41, 99)],
      ["twenty", "twenty-seven", "thirty", "forty", "forty-one", "ninety-nine"])
for _bad in (19, 100):
    _raised = False
    try:
        cov.spell(_bad)
    except ValueError as _e:
        _raised = str(_bad) in str(_e)
    check(f"  and refuses {_bad} by name rather than a bare KeyError", _raised, True)

check("a removed round count goes MISSING",
      cov.round_count_claim(TASKS.replace(CURRENT, "many rounds of"),
                            ROUNDS)["status"], "MISSING")


# --- table scoping ------------------------------------------------------------------

check("a table is located by its header, and its rows end at the first non-row",
      len(cov.table_rows("| Round | PR | Settled |\n|---|---|---|\n| 1 | a | b |\n\ntext\n",
                         ["Round", "PR", "Settled"])), 1)
check("a missing table yields no rows rather than raising",
      cov.table_rows("no tables here", ["Round", "PR", "Settled"]), [])
check("round numbers are de-duplicated across a round's several files",
      len(ROUNDS), len(set(ROUNDS)))


print(f"\nall summary-coverage unit tests passed ({PASSED} checks)")
