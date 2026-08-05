#!/usr/bin/env python3
"""Harvest the ORIGINAL text of every PR and issue body in a number range.

Round 32's scope limit called this population "not diffable" and was wrong (#219):
GraphQL `userContentEdits` returns every prior version of a body with an `editedAt`
stamp, and `totalCount == 0` means a body was never edited, so its current text IS
its original. That makes **wrong-at-write directly determinable** for PR and issue
prose -- the property rounds 31 and 32 had to reconstruct from commit diffs.

This is a HARVESTER, not a gate. It enforces nothing and is not wired into
validate.sh. It exists so round 33's population can be rebuilt by anyone rather
than living in one session's /tmp.

Usage:
    python3 scripts/harvest_bodies.py --range 110-219 --out bodies.jsonl
    python3 scripts/harvest_bodies.py --range 110-219 --stats
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys

REPO_OWNER, REPO_NAME = "realmarcin", "protstruct_review"

QUERY = """
{ repository(owner: "%s", name: "%s") {
    issueOrPullRequest(number: %d) {
      __typename
      ... on Issue { number title body
        userContentEdits(first: 50) { totalCount nodes { editedAt diff } } }
      ... on PullRequest { number title body merged
        userContentEdits(first: 50) { totalCount nodes { editedAt diff } } }
    } } }
"""


def fetch(n: int) -> dict | None:
    res = subprocess.run(["gh", "api", "graphql", "-f",
                          "query=" + QUERY % (REPO_OWNER, REPO_NAME, n)],
                         capture_output=True, text=True)
    if res.returncode:
        return None
    d = (json.loads(res.stdout).get("data") or {}).get("repository") or {}
    d = d.get("issueOrPullRequest")
    if not d:
        return None
    edits = d.get("userContentEdits") or {}
    nodes = edits.get("nodes") or []
    # The OLDEST edit node carries the text as it stood before the first edit.
    # With no edits the current body is the original. Getting this backwards would
    # silently measure the corrected text and report it as wrong-at-write.
    original = nodes[-1]["diff"] if nodes else d.get("body")
    return {"n": d["number"], "type": d["__typename"], "merged": d.get("merged"),
            "title": d.get("title"), "edits": edits.get("totalCount", 0),
            "original": original or "", "current": d.get("body") or ""}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--range", required=True, metavar="LO-HI")
    ap.add_argument("--out")
    ap.add_argument("--stats", action="store_true")
    a = ap.parse_args()
    try:
        lo, hi = (int(x) for x in a.range.split("-"))
    except ValueError:
        raise SystemExit(f"harvest_bodies: --range {a.range!r} is not LO-HI")
    if lo > hi:
        raise SystemExit(f"harvest_bodies: --range {a.range!r} is reversed")

    rows, missing = [], []
    for n in range(lo, hi + 1):
        r = fetch(n)
        (rows.append(r) if r else missing.append(n))

    if a.out:
        with open(a.out, "w") as fh:
            for r in rows:
                fh.write(json.dumps(r) + "\n")
    if a.stats or not a.out:
        pop = [r for r in rows if r["type"] == "Issue" or r["merged"]]
        print(f"fetched            : {len(rows)} of {hi - lo + 1}")
        print(f"population         : {len(pop)}  "
              f"({sum(1 for r in pop if r['type']=='Issue')} issues, "
              f"{sum(1 for r in pop if r['type']=='PullRequest')} merged PRs)")
        print(f"bodies ever edited : {sum(1 for r in pop if r['edits'])}")
        if missing:
            # Named, not dropped: a gap is usually an unmerged PR, and silently
            # shrinking a population is how a denominator goes wrong (#155, #208).
            print(f"  not resolved     : {missing}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
