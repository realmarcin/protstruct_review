#!/usr/bin/env python3
"""Check a round document's claims about its OWN findings against a committed record.

Round 25 shipped two miscounts of its own work -- #130 ("three high" when four were
labelled high) and #135 ("a 20-file audit round" that was 19). Both were caught by
review rather than by a check, and both came from the same habit: recounting from
memory instead of from the command. Both were also wrong in the direction that
flatters, which is the direction this repo says to check hardest.

The rule already existed -- *every figure a document quotes must come from a committed,
re-runnable script* -- and had simply never been applied to a round document's claims
about itself. The registry has had that gate since round 24
(`scripts/check_registry_figures.py`); this is the same idea pointed at the audit
trails.

WHY A COMMITTED TSV AND NOT A LIVE `gh` CALL. `scripts/validate.sh` is offline and stays
offline. A gate that silently skips when `gh` is unavailable or unauthenticated is a
guard that does not guard -- the exact class round 25 spent itself on. So the
issue-derived facts are committed as data, exactly as `em_refinement_deltas.tsv` is, and
refreshed deliberately:

    python3 scripts/check_round_figures.py --refresh     # needs `gh`; rewrites the TSV
    python3 scripts/check_round_figures.py               # offline; exits 1 on mismatch

ONE RULE, ONE COPY. The refresh and the check share `severity_of()` and `load()` rather
than each carrying their own parsing. Two copies of a rule falling out of step is what
#136 was, and writing this file with the same defect it exists to discourage would be a
poor joke.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parent.parent
RECORD = REPO / "ref/research/data/round_findings.tsv"
HEADER = "issue\tseverity\tstate\ttitle\n"

# The severity line every issue body in this repo carries, e.g. "**Severity: medium-high**".
#
# ANCHORED to the start of a line, and that anchor is load-bearing. Unanchored, `.search`
# took the FIRST occurrence anywhere in the body -- and #130's body opens by QUOTING the
# label it is reporting on ("Four of the twelve are labelled `**Severity: high**`"), so
# the record said `high` for an issue that declares `medium` twelve lines further down.
# That is #121 exactly -- keying on the first match when the meaningful one is elsewhere
# -- reproduced inside the round whose subject is fragile rules. The declaration is
# always its own line; a mention never is.
_SEVERITY = re.compile(r"^\*\*Severity:\s*([a-z-]+)", re.MULTILINE)


def severity_of(body: str) -> str:
    """The severity an issue body declares, or `unstated`.

    Deliberately NOT defaulted to a level. An issue with no severity line is a real
    thing (the wontfix ones often have one anyway) and recording it as `unstated` keeps
    it visible; defaulting it to `low` would quietly shrink whatever count uses it.
    """
    m = _SEVERITY.search(body or "")
    return m.group(1) if m else "unstated"


def issue_numbers(lo: int, hi: int) -> list[int]:
    """Real issue numbers in [lo, hi] — PRs excluded.

    `gh issue view <n>` happily resolves a PULL REQUEST number and returns it looking
    like an issue, so iterating a numeric range pulled #128 and #129 (this round's own
    PRs) into the record with severity `unstated`. `gh issue list` returns issues only,
    so the range is intersected with it rather than walked blindly.
    """
    out = subprocess.run(
        ["gh", "issue", "list", "--state", "all", "--limit", "500", "--json", "number"],
        capture_output=True, text=True)
    if out.returncode != 0:
        raise SystemExit(f"gh issue list failed: {out.stderr.strip()}")
    return sorted(n for n in (d["number"] for d in json.loads(out.stdout))
                  if lo <= n <= hi)


def refresh(lo: int, hi: int) -> list[dict[str, str]]:
    """Pull each issue from `gh` and reduce it to the row we keep.

    NOTE what is deliberately absent: the PR that fixed each issue. It cannot be derived
    reliably — `closedByPullRequestsReferences` is empty for an issue auto-closed by a
    `Fix #NNN` commit keyword, and the workflow's "Fixed in #NNN" close comment is absent
    for exactly those same issues. A column that is right for some rows and silently
    empty for others is worse than no column in a record meant to be authoritative, so
    `state` — which is reliable — is kept instead.
    """
    rows = []
    for n in issue_numbers(lo, hi):
        out = subprocess.run(
            ["gh", "issue", "view", str(n), "--json", "number,title,body,state"],
            capture_output=True, text=True)
        if out.returncode != 0:
            print(f"  ! #{n}: {out.stderr.strip().splitlines()[-1:]}", file=sys.stderr)
            continue
        d = json.loads(out.stdout)
        rows.append({
            "issue": str(d["number"]),
            "severity": severity_of(d.get("body", "")),
            "state": (d.get("state") or "").lower(),
            # Tabs would break the column layout; the title is free text from a human.
            "title": (d.get("title") or "").replace("\t", " "),
        })
        print(f"  #{d['number']}  {rows[-1]['severity']:<12} {rows[-1]['state']}",
              file=sys.stderr)
    return rows


def load(path: Path) -> list[dict[str, str]]:
    lines = path.read_text().splitlines()
    header = lines[0].split("\t")
    return [dict(zip(header, l.split("\t"))) for l in lines[1:] if l.strip()]


def write(rows: list[dict[str, str]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    body = "".join("\t".join(r[c] for c in HEADER.strip().split("\t")) + "\n"
                   for r in sorted(rows, key=lambda r: int(r["issue"])))
    path.write_text(HEADER + body)


# --- the checks ---------------------------------------------------------------------
# Each pairs a literal that must appear in the round document with a derivation from the
# record. Same contract as check_registry_figures.py: a changed figure AND a reworded
# claim both fail, because a gate that only compares numbers is defeated by a rewrite.

ROUND25 = REPO / "ref/research/tolerance_benchmark_round25.md"


def _pass1(rows):
    """The twelve first-pass findings: issues 116-127, all fixed in PR #129."""
    return [r for r in rows if 116 <= int(r["issue"]) <= 127]


def round25_checks(rows: list[dict]) -> list[tuple[str, str, str]]:
    """(label, literal required in the doc, value derived from the record)."""
    p1 = _pass1(rows)
    high = [r for r in p1 if r["severity"] == "high"]
    return [
        ("pass-1 finding count",
         f"Twelve defects, filed as #116–#127.",
         f"{_word(len(p1))} defects, filed as #{min(int(r['issue']) for r in p1)}–"
         f"#{max(int(r['issue']) for r in p1)}."),
        ("pass-1 high count",
         "Four high (#116, #117, #118, #127).",
         f"{_word(len(high))} high ("
         + ", ".join(f"#{r['issue']}" for r in sorted(high, key=lambda r: int(r["issue"])))
         + ")."),
    ]


_WORDS = {1: "One", 2: "Two", 3: "Three", 4: "Four", 5: "Five", 6: "Six", 7: "Seven",
          8: "Eight", 9: "Nine", 10: "Ten", 11: "Eleven", 12: "Twelve", 13: "Thirteen"}


def _word(n: int) -> str:
    return _WORDS.get(n, str(n))


def severity_claims(doc: str, rows: list[dict]) -> list[dict[str, Any]]:
    """Every "#NNN (severity)" the document asserts must match the record.

    Round 25's self-review section names its findings inline -- "#136 (high)",
    "#130 (medium)", "#135 (low)". Those are exactly the figures that were wrong
    before, so they are checked individually rather than only in aggregate.
    """
    by_issue = {r["issue"]: r for r in rows}
    results = []
    for m in re.finditer(r"#(\d+) \((high|medium|low|medium-high|low-medium)\)", doc):
        issue, claimed = m.group(1), m.group(2)
        actual = by_issue.get(issue, {}).get("severity")
        if actual is None:
            status, detail = "MISSING", (
                f"the document cites #{issue} but the record has no such issue — "
                f"refresh with --refresh, or the citation is wrong")
        elif actual != claimed:
            status, detail = "STALE", (
                f"the document calls #{issue} {claimed!r}; the issue says {actual!r}")
        else:
            status, detail = "OK", f"#{issue} ({claimed})"
        results.append({"check": f"severity of #{issue}", "status": status,
                        "detail": detail})
    return results


def run(doc: str, rows: list[dict]) -> list[dict[str, Any]]:
    results = []
    for label, literal, derived in round25_checks(rows):
        if literal not in doc:
            status, detail = "MISSING", (
                f"the document does not contain the expected literal {literal!r} — the "
                f"figure was edited or the claim reworded, so there is nothing to "
                f"compare; the record gives {derived!r}")
        elif derived != literal:
            status, detail = "STALE", f"document says {literal!r}; record gives {derived!r}"
        else:
            status, detail = "OK", derived
        results.append({"check": label, "status": status, "detail": detail})
    results += severity_claims(doc, rows)
    return results


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--refresh", action="store_true",
                    help="re-pull the findings from `gh` and rewrite the record")
    ap.add_argument("--from-issue", type=int, default=116)
    ap.add_argument("--to-issue", type=int, default=138)
    ap.add_argument("--doc", default=str(ROUND25))
    ap.add_argument("--record", default=str(RECORD))
    args = ap.parse_args()

    record = Path(args.record)
    if args.refresh:
        rows = refresh(args.from_issue, args.to_issue)
        if not rows:
            print("refresh produced no rows — is `gh` authenticated?", file=sys.stderr)
            return 1
        write(rows, record)
        # `relative_to` raises for a path outside the repo, which --record makes easy to
        # do and which a canary run does by design. Reporting a successful write must
        # not be able to fail; the write already happened.
        try:
            shown = record.relative_to(REPO)
        except ValueError:
            shown = record
        print(f"wrote {len(rows)} findings to {shown}")
        return 0

    results = run(Path(args.doc).read_text(), load(record))
    bad = [r for r in results if r["status"] != "OK"]
    for r in results:
        print(f"  {r['status']:<8} {r['check']:<24} {r['detail']}",
              file=sys.stderr if r["status"] != "OK" else sys.stdout)
    if bad:
        print(f"\n{len(bad)} round-document figure(s) do not match the findings record.",
              file=sys.stderr)
        return 1
    print(f"\nall {len(results)} round-document figures match the findings record")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
