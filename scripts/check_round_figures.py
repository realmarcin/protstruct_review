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


# Any GFM fence, ``` or ~~~, and an UNCLOSED fence runs to end of document. `~~~` is
# what an author reaches for when the quoted text itself contains backticks -- exactly
# this repo's situation -- and an unclosed fence is a routine copy-paste artefact. Both
# previously bypassed stripping and reproduced #121's shape a fourth time (#151).
_FENCED = re.compile(r"^(```|~~~).*?(^\1|\Z)", re.MULTILINE | re.DOTALL)


def _fenced_spans(doc: str) -> list[tuple[int, int]]:
    return [(m.start(), m.end()) for m in _FENCED.finditer(doc)]


def _is_quoted(doc: str, start: int, end: int, spans: list[tuple[int, int]]) -> bool:
    """Is the match at [start, end) a quotation rather than a claim?

    Classifies the match IN PLACE instead of stripping the document first. Destructive
    stripping meant one unbalanced backtick earlier in a paragraph swallowed everything
    to the next one -- including a genuinely wrong severity claim, which then vanished
    from the gate's output entirely (#151). A false negative on a real defect is worse
    than the false positives this stripping was introduced to fix, so the rule is now
    local: a stray backtick can mis-classify the match it touches, never delete another.

    Quotation means any of: inside a fence; wrapped in backticks on its own line; on an
    indented (4-space) or blockquoted line.
    """
    if any(s <= start < e for s, e in spans):
        return True
    line_start = doc.rfind("\n", 0, start) + 1
    line_end = doc.find("\n", end)
    line_end = len(doc) if line_end == -1 else line_end
    line = doc[line_start:line_end]
    if line[:4] == "    " or line.lstrip().startswith(">"):
        return True
    # Backticks immediately around the match, on this line only. The claim pattern does
    # not consume the closing `**`, so skip it before looking for the backtick --
    # otherwise `` `**#130 (High)**` `` reads as unquoted because the character after the
    # match is `*`.
    before = doc[line_start:start]
    after = doc[end:line_end].lstrip("*")
    return before.rstrip().endswith("`") and after.lstrip().startswith("`")


def severity_of(body: str) -> str:
    """The severity an issue body declares, or `unstated`.

    Deliberately NOT defaulted to a level. An issue with no severity line is a real
    thing (the wontfix ones often have one anyway) and recording it as `unstated` keeps
    it visible; defaulting it to `low` would quietly shrink whatever count uses it.
    """
    # Fenced blocks are stripped first. Anchoring to line start fixed the INLINE-quote
    # case, but a fenced block sits at column 0 too, and this repo's issues routinely
    # quote prior text that way -- #130 does. Without this, an issue quoting another
    # issue's severity reports the QUOTED value, which is #121's shape a third time
    # (#149).
    m = _SEVERITY.search(_FENCED.sub("", body or ""))
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
    if not p1:
        # Reachable via a botched partial --refresh. Report it; do not raise a traceback
        # from min() over an empty sequence and lose the diagnostic (#149).
        return [("pass-1 finding count", "Twelve defects, filed as #116–#127.",
                 "<the record contains no issues in #116–#127; re-run --refresh>")]
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


# A severity CLAIM is bolded: `**#136 (high) — the #119 fix ...`. A severity quoted as
# an EXAMPLE is not -- round 26's proof-of-failure table contains "`#136 (high)` →
# `#136 (medium)`", which is the document demonstrating that the gate catches a wrong
# severity. Matching both made the gate report STALE on correct prose describing what
# the gate does (#144), and a guard that fires on correct input trains people to ignore
# it. The bold marker is the convention every real claim already follows.
# Captures ANY parenthesised token, not only the known severities. Restricting the
# alternation meant a citation the regex did not anticipate -- `**#130 (High)** -- produced
# NO result item at all: not MISSING, not STALE, simply unchecked and unmentioned. A gate
# that silently declines to look is worse than one that complains (#149).
_SEVERITY_CLAIM = re.compile(r"\*\*#(\d+) \(([^)]{1,20})\)")
_KNOWN_SEVERITIES = {"high", "medium", "low", "medium-high", "low-medium"}
# Code formatting marks a QUOTATION, not a claim. #144 fixed one instance of this by
# requiring the bolded form -- and then this round quoted `**#130 (High)**` inside
# backticks, as the counter-example illustrating that very defect, and the gate reported
# it. Bold cannot discriminate, because a quoted example carries its own bold. Stripping
# fenced blocks and inline code spans can, and it is the same rule `severity_of` uses on
# issue bodies, so the two agree instead of each having their own idea of a quotation.
_CODE_SPAN = re.compile(r"`[^`\n]*`")


def _prose_only(doc: str) -> str:
    """The document with fenced blocks and inline code spans removed."""
    return _CODE_SPAN.sub("", _FENCED.sub("", doc))


def severity_claims(doc: str, rows: list[dict]) -> list[dict[str, Any]]:
    """Every bolded "**#NNN (severity)" the document asserts must match the record.

    Round 25's self-review section names its findings inline -- "**#136 (high)",
    "**#130 (medium)", "**#135 (low)". Those are exactly the figures that were wrong
    before, so they are checked individually rather than only in aggregate.

    The alternation is longest-first. It does not need to be -- the trailing paren
    forces backtracking, so `medium-high` captures correctly either way -- but it stops
    depending on that, and an ordering that is right for a reason is cheaper than one
    that is right by rescue.
    """
    by_issue = {r["issue"]: r for r in rows}
    results = []
    spans = _fenced_spans(doc)
    for m in re.finditer(_SEVERITY_CLAIM, doc):
        if _is_quoted(doc, m.start(), m.end(), spans):
            continue
        issue, claimed = m.group(1), m.group(2)
        if claimed.lower() not in _KNOWN_SEVERITIES:
            results.append({
                "check": f"severity of #{issue}", "status": "UNRECOGNISED",
                "detail": (f"the document writes #{issue} ({claimed!r}), which is not one "
                           f"of {sorted(_KNOWN_SEVERITIES)} — fix the citation or add the "
                           f"level; it is not being checked")})
            continue
        claimed = claimed.lower()
        actual = by_issue.get(issue, {}).get("severity")
        if actual == "unstated":
            # The issue carries no `**Severity:` line. That convention starts at #116;
            # rounds 20-23 assigned severities in their write-ups only, so there is no
            # machine-readable source to compare against. Reported, not failed: the
            # document may well be right, and failing on correct prose is exactly the
            # defect #144 was (a guard that fires on valid input gets ignored).
            status, detail = "UNCHECKABLE", (
                f"#{issue} predates the `**Severity:` convention (starts at #116), so "
                f"the document's {claimed!r} cannot be checked against the issue")
        elif actual is None:
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


ROUND_DOCS = "ref/research/tolerance_benchmark_round*.md"


def run_all(repo: Path, rows: list[dict]) -> list[dict[str, Any]]:
    """Check EVERY round document, not only the one the gate was written for.

    #143: the record shipped omitting #139/#140/#142 -- this round's own findings -- and
    that stayed invisible because the gate was only ever pointed at round 25. A guard
    aimed away from the work that introduced it is the round-24 lesson repeating.

    Per-document literal checks are still round-25-specific (its phrasings are its own).
    The severity claims apply to any document, so every round is checked for those.
    """
    results = []
    for path in sorted(repo.glob(ROUND_DOCS)):
        doc = path.read_text()
        name = path.name.replace("tolerance_benchmark_", "").replace(".md", "")
        claims = severity_claims(doc, rows)
        for r in claims:
            r["check"] = f"{name}: {r['check']}"
        results += claims
    return results


def run(doc: str, rows: list[dict]) -> list[dict[str, Any]]:
    results = []
    # Literal checks read the document with fences removed, for the same reason the
    # claim checks do: a document that QUOTES the canonical phrasing while its prose
    # states something else satisfied this check (#151), and this is the gate's default
    # target.
    prose = _FENCED.sub("", doc)
    for label, literal, derived in round25_checks(rows):
        if literal not in prose:
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
    # 87 is the lowest severity claim in any round document; the record must span
    # every issue the documents cite or the gate reports MISSING on correct prose.
    ap.add_argument("--from-issue", type=int, default=87)
    ap.add_argument("--to-issue", type=int, default=200)
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

    rows = load(record)
    results = run(Path(args.doc).read_text(), rows)
    # Plus the severity claims of every OTHER round document (#143).
    results += [r for r in run_all(REPO, rows)
                if not r["check"].startswith(Path(args.doc).stem.replace(
                    "tolerance_benchmark_", "") + ":")]
    # UNCHECKABLE is a coverage statement, not a failure.
    # UNCHECKABLE is a coverage statement (no source to check against).
    # UNRECOGNISED is a defect: the document wrote something unparseable.
    bad = [r for r in results if r["status"] not in ("OK", "UNCHECKABLE")]
    for r in results:
        print(f"  {r['status']:<12} {r['check']:<26} {r['detail']}",
              file=sys.stderr if r["status"] not in ("OK", "UNCHECKABLE") else sys.stdout)
    if bad:
        print(f"\n{len(bad)} round-document figure(s) do not match the findings record.",
              file=sys.stderr)
        return 1
    unchecked = [r for r in results if r["status"] == "UNCHECKABLE"]
    print(f"\nall {len(results) - len(unchecked)} checkable round-document figures match "
          f"the findings record"
          + (f"; {len(unchecked)} predate the severity convention and are NOT checked"
             if unchecked else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
