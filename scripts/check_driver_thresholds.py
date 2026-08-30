#!/usr/bin/env python3
"""Keep the driving examples and benchmark docstrings in step with the registry.

`ref/thresholds_and_standards.md` is the single source of truth, and CODING_STANDARDS
rule 2 says a driving example must CITE it rather than restate a number. A Codex
conceptual review (2026-08-06) found the rule had quietly lapsed: `ref/driving_example.md`
and the per-task drivers graded cross-tool CA RMSD agreement at 0.10 A where §3 now says
0.03 A, and used ΔRMSD +0.05, CC_mask −0.01 and d_FSC_model +0.05 A — round-5 values the
benchmarks had since made resolution-conditional or relative (rounds 7/13/42). Several
`bench_*.py` docstrings carried the same retired numbers. Nothing reconciled the registry
against its consumers, so an evaluator following a driver would apply a different standard
from the one the registry documents. #269-followup / Codex review action plan.

This gate does two things per metric, both re-derivable offline:

  1. CURRENCY. Re-derive the metric's current value from the registry row and assert the
     table below still matches it. So if a future round changes a §-value, this check
     fails until the table (and therefore the consumers) are revisited — the registry
     change cannot silently outrun its consumers.
  2. NO STALE RESTATEMENT. Assert none of the metric's RETIRED literals appear in a
     consumer, EXCEPT on a line explicitly marked as history (a "was …", "originally",
     "pre-benchmark", "round-5", "catalog's" note). A retired value stated as current is
     the defect; the same value shown as history is fine.

    python3 scripts/check_driver_thresholds.py        # exits 1 on any drift

Kept importable (`registry_value`, `stale_hits`) so `test_driver_thresholds.py` drives it
on synthetic inputs — a guard that cannot be tested has not been checked (round 27).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
REGISTRY = REPO / "ref/thresholds_and_standards.md"

# Lines that legitimately show a retired value as HISTORY, not as a live threshold.
HISTORY_MARKERS = ("pre-benchmark", "originally", "round-5", "round 5", "catalog's",
                   "was a ", "was the", "were the", "were round", "retired")

SIDECAR = REPO / "ref/thresholds_and_standards.yaml"
REQUIRED_KEYS = ("metric", "section", "current", "registry_pattern", "consumers",
                 "retired")


def load_checks(path: Path = SIDECAR) -> list[dict]:
    """The governed-threshold table, from the YAML sidecar next to the registry
    (gate consolidation step b). Validated on load: a malformed table is a
    named failure, never a silently shorter one. Each entry is normalised to
    the historical in-code shape (``registry`` = the pattern) so callers and
    tests keep one vocabulary."""
    try:
        doc = yaml.safe_load(path.read_text())
    except (OSError, yaml.YAMLError) as exc:
        raise ValueError(f"{path.name}: unreadable sidecar ({type(exc).__name__}: "
                         f"{exc})") from exc
    if not isinstance(doc, dict) or not isinstance(doc.get("governed"), list) \
            or not doc["governed"]:
        raise ValueError(f"{path.name}: expected a non-empty 'governed' list")
    out, seen = [], set()
    for i, entry in enumerate(doc["governed"]):
        where = f"{path.name}: governed[{i}]"
        if not isinstance(entry, dict):
            raise ValueError(f"{where}: not a mapping")
        missing = [k for k in REQUIRED_KEYS if k not in entry]
        if missing:
            raise ValueError(f"{where}: missing {missing}")
        unknown = sorted(set(entry) - set(REQUIRED_KEYS))
        if unknown:
            raise ValueError(f"{where}: unknown key(s) {unknown}")
        if not isinstance(entry["metric"], str) or not entry["metric"].strip():
            raise ValueError(f"{where}: metric must be a non-empty string")
        if entry["metric"] in seen:
            raise ValueError(f"{where}: duplicate metric {entry['metric']!r}")
        seen.add(entry["metric"])
        if type(entry["section"]) is not int or entry["section"] < 1:
            raise ValueError(f"{where}: section must be a positive integer")
        if not isinstance(entry["current"], str) or not entry["current"].strip():
            raise ValueError(f"{where}: current must be a non-empty string "
                             f"(quote it — YAML would otherwise turn 0.03 into a float)")
        if not isinstance(entry["registry_pattern"], str):
            raise ValueError(f"{where}: registry_pattern must be a string")
        try:
            groups = re.compile(entry["registry_pattern"]).groups
        except re.error as exc:
            raise ValueError(f"{where}: registry_pattern does not compile: {exc}")
        if groups != 1:
            raise ValueError(f"{where}: registry_pattern must have exactly one "
                             f"capture group, has {groups}")
        for key in ("consumers", "retired"):
            if (not isinstance(entry[key], list) or not entry[key]
                    or not all(isinstance(x, str) and x for x in entry[key])):
                raise ValueError(f"{where}: {key} must be a non-empty list of strings")
        out.append({"metric": entry["metric"], "section": entry["section"],
                    "current": entry["current"], "registry": entry["registry_pattern"],
                    "consumers": list(entry["consumers"]),
                    "retired": list(entry["retired"])})
    return out


def section_spans(registry_text: str) -> dict[int, tuple[int, int]]:
    """{section number: (start, end)} character spans of the registry's
    '## N.' sections, so a governed value can be required to be read from
    inside the section its entry names (#527)."""
    heads = list(re.finditer(r"^## (\d+)\..*$", registry_text, re.M))
    spans = {}
    for i, m in enumerate(heads):
        nxt = re.search(r"^## ", registry_text[m.end():], re.M)
        end = m.end() + nxt.start() if nxt else len(registry_text)
        spans[int(m.group(1))] = (m.start(), end)
    return spans


def section_headings(registry_text: str) -> set[int]:
    return set(section_spans(registry_text))


try:
    CHECKS = load_checks()
    _LOAD_ERROR = None
except ValueError as exc:  # surfaced by main() as a named failure, not a traceback
    CHECKS, _LOAD_ERROR = [], str(exc)
CHECKS_BY_METRIC = {c["metric"]: c for c in CHECKS}


def registry_value(pattern: str, text: str) -> str | None:
    m = re.search(pattern, text)
    return m.group(1) if m else None


def stale_hits(consumer_text: str, retired: list[str]) -> list[str]:
    """Retired literals that appear on a non-history line of a consumer."""
    hits = []
    for line in consumer_text.splitlines():
        if any(mark in line for mark in HISTORY_MARKERS):
            continue
        for lit in retired:
            if lit in line:
                hits.append(lit)
    return sorted(set(hits))


def main() -> int:
    if _LOAD_ERROR:
        print(f"FAIL  {_LOAD_ERROR}", file=sys.stderr)
        return 1
    registry = REGISTRY.read_text()
    failures = []
    spans = section_spans(registry)
    for c in CHECKS:
        span = spans.get(c["section"])
        if span is None:
            failures.append(f"{c['metric']}: sidecar names section {c['section']}, "
                            f"which is not a '## N.' heading of the registry")
        else:
            hit = re.search(c["registry"], registry)
            if hit and not (span[0] <= hit.start() < span[1]):
                failures.append(f"{c['metric']}: its value was read outside section "
                                f"{c['section']} — the pattern matches a restatement "
                                f"elsewhere in the registry")
        derived = registry_value(c["registry"], registry)
        if derived is None:
            failures.append(f"{c['metric']}: cannot find its value in the registry — the "
                            f"row was reworded; update this check's regex")
        elif derived != c["current"]:
            failures.append(f"{c['metric']}: registry now says {derived!r} but this check "
                            f"expects {c['current']!r} — a round changed the value; update "
                            f"the CHECKS table AND every consumer")
        for rel in c["consumers"]:
            path = REPO / rel
            if not path.exists():
                failures.append(f"{c['metric']}: consumer {rel} is missing")
                continue
            hits = stale_hits(path.read_text(), c["retired"])
            if hits:
                failures.append(f"{c['metric']}: {rel} still states retired value(s) "
                                f"{hits} as a live threshold (current is {c['current']})")
        print(f"  {c['metric']:32} registry {derived}  ({len(c['consumers'])} consumers)",
              file=sys.stderr if any(c['metric'] in f for f in failures) else sys.stdout)
    if failures:
        print("\ndriver/docstring thresholds are out of step with the registry:",
              file=sys.stderr)
        for f in failures:
            print(f"  - {f}", file=sys.stderr)
        return 1
    print(f"\nall {len(CHECKS)} registry-governed thresholds (ref/thresholds_and_standards.yaml) "
          f"are current in their consumers")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
