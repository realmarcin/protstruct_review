#!/usr/bin/env python3
"""Check that the two summary files cover every round, and that their counts are real.

`NEXT_TASKS.md` and `ref/research/lessons.md` summarise work recorded elsewhere. Both
drift, and both have drifted repeatedly:

  * NEXT_TASKS has needed six manual reconciles (#58, #64, #68 and two earlier, then
    #154). #68 was titled "...and gate the gap that keeps recurring" and gated
    lessons.md -- the NEIGHBOURING file -- so the one it was named for went on drifting.
  * The counts these files quote have been wrong eight times (#130, #135, #147, #150,
    #155, #156, and the two in #158), every time because a number was restated from
    memory when the source was committed and one command away.

TWO KINDS OF CHECK, and the difference matters:

  COVERAGE -- every round with an audit trail has a row. Representation only: a pass
  means the round is not missing, NOT that what the row says is right.

  COUNTS -- a figure the file quotes is re-derived from the record and compared, the
  same contract as `check_registry_figures.py`: a changed value AND a reworded claim
  both fail, because a gate that only compares numbers is defeated by a rewrite.

WHY THIS IS A SCRIPT AND NOT SHELL. The coverage checks lived in `validate.sh` as
embedded python and were un-testable, which is exactly how #157 shipped: both matched
any table anywhere in the file, so an unrelated table with the right cell shape -- or a
fenced example row -- silently satisfied coverage for a round that was genuinely
missing. Scoping a table by its header and ignoring fenced blocks is a few lines; being
able to unit-test it is the point.

Usage:
    python3 scripts/check_summary_coverage.py          # exits 1 on any divergence
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parent.parent
NEXT_TASKS = "NEXT_TASKS.md"
LESSONS = "ref/research/lessons.md"
FINDINGS = "ref/research/data/round_findings.tsv"
ROUND_GLOB = "ref/research/tolerance_benchmark_round*.md"

# Any GFM fence, and an unclosed one runs to end of document. Same rule as
# check_round_figures.py: text inside a fence is an EXAMPLE, not a claim, and a
# documentation example that satisfies a coverage check is #157.
_FENCED = re.compile(r"^(```|~~~).*?(^\1|\Z)", re.MULTILINE | re.DOTALL)

# A markdown table separator: pipes, dashes, colons and space, nothing else.
_SEPARATOR = re.compile(r"^\s*\|[\s:|-]+\|\s*$")


def prose(text: str) -> str:
    return _FENCED.sub("", text)


def table_rows(text: str, header_cells: list[str]) -> list[list[str]]:
    """Rows of the ONE table whose header matches `header_cells`.

    Scoped deliberately. The predecessors matched every `| ... |` line in the file, so
    any unrelated table with a numeric cell in the right position satisfied coverage for
    a round that had no row at all (#157). A table is identified by its header and ends
    at the first line that is not a row.
    """
    lines = prose(text).splitlines()
    want = [c.strip().lower() for c in header_cells]
    for i, line in enumerate(lines):
        cells = [c.strip().lower() for c in line.strip().strip("|").split("|")]
        if cells != want:
            continue
        # The separator is CHECKED, not assumed. Skipping `i+1` unconditionally meant a
        # table whose separator row was missing lost its first data row, and the round
        # in that row was reported missing when it was present (#161).
        if i + 1 >= len(lines) or not _SEPARATOR.match(lines[i + 1]):
            continue
        rows = []
        for row in lines[i + 2:]:            # +2 skips the |---|---| separator
            if not row.strip().startswith("|"):
                break
            rows.append([c.strip() for c in row.strip().strip("|").split("|")])
        return rows
    return []


def rounds_on_disk(repo: Path) -> list[str]:
    """Round numbers that have an audit TRAIL, de-duplicated.

    A round can have several files -- round 26 has its trail and its pre-registration --
    and without the set the failure message names it once per file.

    Pre-registrations are excluded (#206). A pre-registration is defined as a commit
    containing NO results; the round table and the lessons entry are summaries OF
    results. Counting one as an audit trail made the gate demand the conclusion before
    the measurement, so landing round 31's pre-registration alone turned validate.sh red
    -- two of this repo's own rules in direct conflict, with the gate insisting on the
    one that says write the answer first.

    Excluding them is strictly STRICTER: a round whose trail is missing can no longer be
    covered by its pre-registration standing in for it.
    """
    return sorted({re.search(r"round(\d+)", p.name).group(1)
                   for p in repo.glob(ROUND_GLOB)
                   if not p.name.endswith("_preregistration.md")}, key=int)


def load_findings(path: Path) -> list[dict[str, str]]:
    lines = path.read_text().splitlines()
    header = lines[0].split("\t")
    return [dict(zip(header, l.split("\t"))) for l in lines[1:] if l.strip()]


# --- coverage -----------------------------------------------------------------------

def next_tasks_coverage(tasks: str, rounds: list[str]) -> dict[str, Any]:
    """Every round needs a row in NEXT_TASKS' round table (first cell = the round)."""
    covered = {r[0] for r in table_rows(tasks, ["Round", "PR", "Settled"])
               if r and r[0].isdigit()}
    missing = [r for r in rounds if r not in covered]
    return {
        "check": "NEXT_TASKS round coverage",
        "status": "OK" if not missing else "MISSING",
        "detail": (f"all {len(rounds)} rounds have a row"
                   if not missing else f"no round-table row for round(s): {missing}"),
    }


def round_tokens(cell: str) -> set[str]:
    """Round numbers named in a lessons index cell.

    The cell is prose as often as not -- "11, back-tested 13" -- so rounds are matched
    as tokens rather than as the whole cell. But NOT every digit: an issue or PR
    reference inside the cell used to credit that round with no entry behind it, so
    `#NNN` is removed first (#161). A `N-M` range is expanded, since "1-5" names five
    rounds rather than two.
    """
    cell = re.sub(r"#\d+", "", cell)
    covered: set[str] = set()
    for a, b in re.findall(r"(\d+)\s*[–-]\s*(\d+)", cell):
        # Endpoints are ORDERED before expanding. `range(5, 2)` is empty, and the range
        # text is stripped before the fallback digit scan, so a descending "5-1" covered
        # NOTHING -- strictly less than the bare digit scan this replaced, which at least
        # found both endpoints (#162). A descending range is a typo; reading it as the
        # range its author meant is the useful interpretation and is never less safe.
        lo, hi = sorted((int(a), int(b)))
        covered.update(str(n) for n in range(lo, hi + 1))
    covered.update(re.findall(r"\d+", re.sub(r"\d+\s*[–-]\s*\d+", "", cell)))
    return covered


def lessons_coverage(lessons: str, rounds: list[str]) -> dict[str, Any]:
    """Every round needs an index entry in lessons.md (round(s) in the LAST cell).

    The last cell is prose as often as not -- "11, back-tested 13" -- so the round is
    matched as a token within it rather than as the whole cell.
    """
    covered: set[str] = set()
    for row in table_rows(lessons, ["Rule", "Round"]):
        if row:
            covered.update(round_tokens(row[-1]))
    missing = [r for r in rounds if r not in covered]
    return {
        "check": "lessons.md round coverage",
        "status": "OK" if not missing else "MISSING",
        "detail": (f"all {len(rounds)} rounds have an index entry"
                   if not missing else f"no index entry for round(s): {missing}"),
    }


# --- counts -------------------------------------------------------------------------

# "**14 defects** (#139–#153)" -- the claim carries the range it counts, so the check
# needs no hardcoded round-to-issue map that could itself drift. The en-dash is what
# these documents use; the hyphen is accepted so a plain-ASCII edit is not a silent miss.
_DEFECT_CLAIM = re.compile(r"\*\*(\d+) defects?\*\* \(#(\d+)[–-]#(\d+)\)")


# The ranges that MUST carry a defect count. Scanning for whatever claims happen to be
# present is not enough: rewording "**14 defects** (#139–#153)" to "fourteen defects"
# made the check silently disappear rather than fail, which is precisely the "a gate that
# only compares numbers is defeated by a rewrite" lesson this repo already learned once.
EXPECTED_DEFECT_CLAIMS = [(116, 127), (139, 153)]


def defect_counts(tasks: str, findings: list[dict]) -> list[dict[str, Any]]:
    """Every expected "**N defects** (#A–#B)" must be present AND match the record.

    #155: a round row said 15 where the record holds 14, because the round's own PR
    number sits inside the range and was counted as a finding. The record contains
    issues only, so deriving from it cannot make that mistake.
    """
    # EVERY occurrence per range, not the last one. A dict comprehension keyed by range
    # let a later restatement overwrite an earlier wrong claim silently -- so a wrong
    # round-table figure passed because a correct sentence appeared further down, which
    # is a style these documents use constantly (#161).
    found: dict[tuple[int, int], list[int]] = {}
    for m in _DEFECT_CLAIM.finditer(prose(tasks)):
        found.setdefault((int(m.group(2)), int(m.group(3))), []).append(int(m.group(1)))
    results = []
    for lo, hi in EXPECTED_DEFECT_CLAIMS:
        actual = sum(1 for f in findings if lo <= int(f["issue"]) <= hi)
        claims = found.get((lo, hi), [])
        if len(set(claims)) > 1:
            results.append({
                "check": f"defect count #{lo}-#{hi}", "status": "CONFLICT",
                "detail": (f"the file claims #{lo}–#{hi} holds {sorted(set(claims))} in "
                           f"different places; the record holds {actual}")})
            continue
        claimed = claims[0] if claims else None
        if claimed is None:
            status, detail = "MISSING", (
                f"no '**N defects** (#{lo}–#{hi})' claim in the file — reworded or "
                f"removed, so there is nothing to compare; the record holds {actual}")
        elif claimed != actual:
            status, detail = "STALE", (
                f"the file claims {claimed} defects in #{lo}–#{hi}; the record "
                f"holds {actual}")
        else:
            status, detail = "OK", f"**{claimed} defects** (#{lo}–#{hi})"
        results.append({"check": f"defect count #{lo}-#{hi}", "status": status,
                        "detail": detail})
    return results


# Covers 20-99. The first version held only {20, 30} -- exactly the range the repo
# occupied -- and raised a bare KeyError at 40 and below 20 (#160). A lookup sized to
# today's values is a fixture pretending to be a function, which is the same instinct
# this round had to correct twice in its own test fixtures.
_TENS = {2: "twenty", 3: "thirty", 4: "forty", 5: "fifty", 6: "sixty", 7: "seventy",
         8: "eighty", 9: "ninety"}
_UNITS = {0: "", 1: "-one", 2: "-two", 3: "-three", 4: "-four", 5: "-five", 6: "-six",
          7: "-seven", 8: "-eight", 9: "-nine"}


def spell(n: int) -> str:
    """The spelled-out form of a round number, 20-99.

    Below 20 the summary file's phrasing ("twenty-six rounds of rules") does not apply,
    and above 99 nothing here is meaningful. Both raise with the number named rather
    than a bare KeyError, because this runs inside a gate and a crash without a
    diagnosis is one somebody disables rather than debugs.
    """
    if not 20 <= n <= 99:
        raise ValueError(
            f"cannot spell round {n}: this covers 20-99, which is the range the "
            f"summary file's phrasing applies to")
    return _TENS[n // 10] + _UNITS[n % 10]


def round_count_claim(tasks: str, rounds: list[str],
                      where: str = NEXT_TASKS) -> dict[str, Any]:
    """The spelled-out round count in a summary file must match the rounds on
    disk. NEXT_TASKS read "twenty-four rounds of rules" for two rounds after
    the fact (#154); lessons.md's title said "thirty rounds" at round 48
    (#467) because only NEXT_TASKS was checked — gate consolidation step (c)
    runs the same rendered comparison on both files.
    """
    expected = f"{spell(int(rounds[-1]))} rounds of"
    check = f"round count ({where})"
    # Alternation derived from _TENS, not hardcoded: this regex was `(twenty|thirty)` and
    # went MISSING at round 40 -- spell() was fixed for 40 (#160) but this sibling search
    # was not, so the gate could not find "forty rounds of" and failed the round that
    # crossed 40. Deriving it from the same table spell() uses keeps them in step
    # (round-40 PR #265; #244 is the sibling MISSING-on-correct-prose defect in
    # check_round_figures --refresh).
    found = re.search(rf"({'|'.join(_TENS.values())})(-\w+)? rounds of", prose(tasks))
    if not found:
        return {"check": check, "status": "MISSING",
                "detail": f"no spelled-out round count found; expected {expected!r}"}
    if found.group(0) != expected:
        return {"check": check, "status": "STALE",
                # `rounds[-1]`, not len(rounds): the claim counts ROUNDS RUN, and rounds
                # 1-5 and 9 have no separate trail file, so the file count is 20 while
                # the highest round is 26. Reporting len() here said "there are 20
                # rounds, so it should say twenty-six", which is incoherent.
                "detail": f"the file says {found.group(0)!r}; the highest round on disk "
                          f"is {rounds[-1]}, so it should say {expected!r}"}
    return {"check": check, "status": "OK", "detail": expected}


def run(repo: Path) -> list[dict[str, Any]]:
    tasks = (repo / NEXT_TASKS).read_text()
    lessons = (repo / LESSONS).read_text()
    rounds = rounds_on_disk(repo)
    findings = load_findings(repo / FINDINGS)
    if not rounds:
        return [{"check": "rounds on disk", "status": "MISSING",
                 "detail": f"no files matched {ROUND_GLOB} — nothing to check against"}]
    return ([next_tasks_coverage(tasks, rounds), lessons_coverage(lessons, rounds),
             round_count_claim(tasks, rounds, NEXT_TASKS),
             round_count_claim(lessons, rounds, LESSONS)] + defect_counts(tasks, findings))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", default=str(REPO))
    args = ap.parse_args()
    results = run(Path(args.repo))
    bad = [r for r in results if r["status"] != "OK"]
    for r in results:
        print(f"  {r['status']:<8} {r['check']:<26} {r['detail']}",
              file=sys.stderr if r["status"] != "OK" else sys.stdout)
    if bad:
        print(f"\n{len(bad)} summary-file claim(s) do not match the record.", file=sys.stderr)
        return 1
    print(f"\nall {len(results)} summary-file claims match the record")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
