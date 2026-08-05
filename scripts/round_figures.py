#!/usr/bin/env python3
"""Print the figures a round can honestly claim, so nobody has to remember them.

Round 30 classified every figure found wrong across rounds 24-29 and found the dominant
cause exactly: **15 of 24 wrong-at-write figures (62 %) were counts restated from memory
when the source was one command away** (#185). Round 30 declined to add a third
convention -- the gap is adherence, not invention -- so this does not add one either.

It is not a gate. It enforces nothing, is not wired into `validate.sh`, and has nothing
to keep in sync. It exists to remove the reason the existing rule gets broken: that
deriving *felt* more expensive than remembering. Run it before writing a round's
figures, and paste what it prints.

WHAT IT DELIBERATELY DOES NOT DO. There is no round-to-issue mapping. Building one would
create a hand-maintained artefact that drifts -- which is the trap round 26 recorded for
its findings record and round 29 for `EXPECTED_DEFECT_CLAIMS`. Instead the caller says
which range or pattern they mean, and each derivation answers only what it can see.

Usage:
    python3 scripts/round_figures.py --issues 183-186      # counts + severity split
    python3 scripts/round_figures.py --diff main..HEAD      # files, insertions, deletions
    python3 scripts/round_figures.py --suite                # checks per test suite
    python3 scripts/round_figures.py --commits 'Reconcile NEXT_TASKS'
    python3 scripts/round_figures.py --issues 183-186 --diff main..HEAD --suite
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
FINDINGS = REPO / "ref/research/data/round_findings.tsv"


def _run(cmd: list[str]) -> str:
    out = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO)
    if out.returncode != 0:
        raise SystemExit(f"round_figures: `{' '.join(cmd)}` failed: {out.stderr.strip()}")
    return out.stdout


def _sibling():
    """`check_round_figures`, loaded once, for the rules this tool must not re-copy.

    Two defects in this file came from copying that module's parsing WITHOUT its
    fixes: #189 (`gh issue view` resolves pull requests) and #190 (a fenced block
    defeats the severity regex, which is #149). Both were already solved next door.
    Importing is the only version of "one rule, one copy" that survives contact.
    """
    import importlib.util
    spec_ = importlib.util.spec_from_file_location(
        "crf", REPO / "scripts" / "check_round_figures.py")
    mod = importlib.util.module_from_spec(spec_)
    spec_.loader.exec_module(mod)
    return mod


def _real_issue_numbers(lo: int, hi: int) -> set[int]:
    """Numbers in [lo, hi] that are ISSUES, via the same rule as check_round_figures.

    Imported rather than reimplemented: one rule, one copy. If that module cannot be
    loaded the fallback returns an empty set, so unknown numbers are reported as
    unresolved rather than guessed at -- failing closed, since a wrong count is the
    thing this tool exists to prevent.
    """
    try:
        return set(_sibling().issue_numbers(lo, hi))
    except Exception:
        return set()


def issues(spec: str) -> list[str]:
    """Issue count and severity split over a range, from the committed findings record.

    Seven of the fifteen memory-miscounts were counts of issues or their severities --
    the largest single category (#130, #155, #164, #173, #174, #176, #179). The record
    holds issues only, so a count derived here cannot repeat #155's mistake of counting
    a pull request.
    """
    lo_s, sep, hi_s = spec.partition("-")
    if sep and not hi_s.strip():
        raise SystemExit(f"round_figures: --issues {spec!r} has a trailing '-' with no "
                         f"upper bound; write {lo_s.strip()!r} or {lo_s.strip()}-N")
    try:
        lo, hi = int(lo_s), int(hi_s or lo_s)
    except ValueError:
        raise SystemExit(f"round_figures: --issues {spec!r} is not a number or LO-HI range")
    if lo > hi:
        # A transposed range used to return 0 silently, which is indistinguishable from
        # a legitimately empty result -- in a tool whose whole purpose is not printing
        # wrong counts (#190).
        raise SystemExit(f"round_figures: --issues {spec!r} is reversed (lo > hi); "
                         f"did you mean {hi}-{lo}?")
    if not FINDINGS.exists():
        return [f"issues {spec}: no findings record at {FINDINGS.relative_to(REPO)}"]
    lines = FINDINGS.read_text().splitlines()
    header = lines[0].split("\t")
    rows = [dict(zip(header, l.split("\t"))) for l in lines[1:] if l.strip()]
    hit = [r for r in rows if lo <= int(r["issue"]) <= hi]
    missing = sorted({n for n in range(lo, hi + 1)} - {int(r["issue"]) for r in hit})
    # The record is a SNAPSHOT, so the issues of the round being written are never in
    # it -- which is precisely when this tool is wanted. Fall back to `gh` for the gap.
    # Safe here in a way it would not be in a gate: this is a helper, so a missing or
    # unauthenticated `gh` degrades to the record alone and says so.
    if missing:
        # REUSE the sibling's rule rather than writing a second copy of it. Round 26 hit
        # this exact trap in check_round_figures.issue_numbers: `gh issue view <n>`
        # resolves a PULL REQUEST number and returns it looking like an issue. Writing
        # the fallback without applying that fix made this tool count its own PR and
        # report 3 issues for a range holding 2 (#189) -- the very defect (#155) the
        # --issues flag exists to prevent, laundered as derived output.
        real, failed = _real_issue_numbers(min(missing), max(missing)), []
        live = []
        for n in missing:
            if n not in real:
                failed.append(n); continue
            try:
                res = subprocess.run(["gh", "issue", "view", str(n), "--json",
                                      "number,title,body,state"],
                                     capture_output=True, text=True)
            except FileNotFoundError:
                # The docstring promises degrading "to the record alone and says so".
                # That held for an unauthenticated `gh` and not for a missing one (#190).
                failed.extend(m for m in missing if m not in [x["issue"] for x in live])
                break
            if res.returncode:
                failed.append(n); continue
            import json as _json
            d = _json.loads(res.stdout)
            # The sibling's parser, not a second regex: it strips fenced blocks first,
            # which #149 established a bare MULTILINE anchor does not (#190).
            try:
                sev = _sibling().severity_of(d.get("body") or "")
            except Exception:
                sev = "unresolved"
            live.append({"issue": str(d["number"]), "severity": sev})
        hit += live
        missing = failed
    sev = Counter(r["severity"] for r in hit)
    out = [f"issues #{lo}-#{hi}      : {len(hit)}   ({', '.join('#'+r['issue'] for r in hit)})",
           "  by severity      : " + (", ".join(f"{k} {v}" for k, v in sorted(sev.items()))
                                      or "none stated")]
    if missing:
        # Not silently ignored: a gap is usually a PR number, which is exactly the
        # confusion that produced #155, so it is named rather than dropped.
        out.append(f"  not in the record: {', '.join('#'+str(n) for n in missing)}"
                   f"  (PRs, or issues filed since the last --refresh)")
    return out


def diff(spec: str) -> list[str]:
    """Files changed and lines added/removed over a revision range.

    #135 said "a 20-file audit round" of a 19-file diff.
    """
    names = [l for l in _run(["git", "diff", "--name-only", spec]).splitlines() if l]
    stat = _run(["git", "diff", "--shortstat", spec]).strip()
    # `git diff` cannot see UNTRACKED files, so a round whose new files are not yet
    # added reports 0 -- the tool built to stop miscounts producing one. Untracked
    # files are counted separately and named, rather than folded in silently: they are
    # not part of the range yet, and pretending otherwise would be its own wrong number.
    untracked = [l for l in _run(["git", "ls-files", "--others", "--exclude-standard"]
                                 ).splitlines() if l]
    out = [f"diff {spec}", f"  files changed    : {len(names)}",
           f"  shortstat        : {stat or '(no changes)'}"]
    if untracked:
        out.append(f"  UNTRACKED        : {len(untracked)} untracked in the WORKING TREE "
                   f"(repo-wide, not scoped to {spec}) "
                   f"({', '.join(untracked[:4])}{' …' if len(untracked) > 4 else ''})"
                   f" — `git add` them before quoting a file count")
    return out


def suite() -> list[str]:
    """Check counts reported by each self-counting test suite.

    #147 said "42 guard checks" when the suite reported a different number.
    """
    out = []
    for script in sorted((REPO / "scripts").glob("test_*.py")):
        res = subprocess.run([sys.executable, str(script)], capture_output=True,
                             text=True, cwd=REPO)
        m = re.search(r"\((\d+) checks?\)", res.stdout)
        status = "FAILED" if res.returncode else (m.group(1) + " checks" if m
                                                  else "passed, no count reported")
        out.append(f"  {script.name:<32} {status}")
    return ["test suites"] + out


def commits(pattern: str) -> list[str]:
    """Commits on the current branch whose subject matches a pattern.

    #156 said "and three earlier" where `git log` showed two.
    """
    subs = _run(["git", "log", "--format=%s"]).splitlines()
    hit = [s for s in subs if re.search(pattern, s)]
    # Both scopes stated: this walks the WHOLE branch history and the pattern is a
    # REGEX. `--commits "round 1."` matched round 19/16/15/13 via `.` as a wildcard and
    # said nothing about either (#190).
    return [f"commits matching regex {pattern!r} over all {len(subs)} commits on this "
            f"branch: {len(hit)}"] + [f"  {s[:76]}" for s in hit[:8]]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--issues", metavar="LO-HI")
    ap.add_argument("--diff", metavar="REVRANGE")
    ap.add_argument("--suite", action="store_true")
    ap.add_argument("--commits", metavar="PATTERN")
    args = ap.parse_args()

    blocks = []
    if args.issues:
        blocks.append(issues(args.issues))
    if args.diff:
        blocks.append(diff(args.diff))
    if args.suite:
        blocks.append(suite())
    if args.commits:
        blocks.append(commits(args.commits))
    if not blocks:
        ap.print_help()
        return 2
    for b in blocks:
        print("\n".join(b))
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
