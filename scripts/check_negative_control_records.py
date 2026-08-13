#!/usr/bin/env python3
"""Guard: the negative-control series' committed records reconcile (#312).

The tolerance series has round-figure guards; the negative-control series
shipped without them, and its very first round doc carried a provenance error
(#311) of exactly the class a guard catches mechanically. This checker runs
from `validate.sh` and fails loudly when:

  - a screen record's rows are internally inconsistent (duplicate ids, unknown
    statuses, screened rows missing a path delta, d6 counts that disagree with
    the rows they summarize)
  - a screen record carries a diagnostic-run manifest — committed records come
    from full runs only (#319); records predating manifests (round 1) are
    exempt from the manifest requirement but not from row checks
  - an enrolled record lists an entry its screen record does not show as
    enrolled
  - a reps record's initial representatives are not unique, or name a cluster
    the record does not rank
  - a round doc `negative_control_round<N>.md` exists whose screen record's
    headline counts (attempted / floor / data defects / screened) do not all
    appear as literal figures in the doc — the #311 drift, mechanized

Network-free; reads only committed files. `--root` exists for the tests.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

KNOWN_STATUSES = {"screened", "floor", "data_defect", "cluster_collision"}


def fail(msg: str, failures: list[str]) -> None:
    print(f"FAIL  {msg}")
    failures.append(msg)


def check_screen(path: Path, failures: list[str]) -> dict | None:
    doc = json.loads(path.read_text())
    rows = doc.get("rows", [])
    ids = [r["pdb_id"] for r in rows]
    if len(ids) != len(set(ids)):
        fail(f"{path.name}: duplicate pdb_ids in rows", failures)
    for r in rows:
        if r["status"] not in KNOWN_STATUSES:
            fail(f"{path.name}: {r['pdb_id']} has unknown status "
                 f"{r['status']!r}", failures)
        if r["status"] == "screened":
            for p in ("phenix", "gemmi"):
                if r.get("paths", {}).get(p, {}).get("delta") is None:
                    fail(f"{path.name}: screened {r['pdb_id']} missing "
                         f"{p} delta", failures)
    run = doc.get("run")
    if run is not None and run.get("run_mode") != "full":
        fail(f"{path.name}: committed record carries a "
             f"{run.get('run_mode')!r} run manifest — full runs only (#319)",
             failures)
    d6 = doc.get("d6", {})
    n_screened = sum(1 for r in rows if r["status"] == "screened")
    if "n_screened" in d6 and d6["n_screened"] != n_screened:
        fail(f"{path.name}: d6.n_screened={d6['n_screened']} but rows hold "
             f"{n_screened}", failures)
    if "n_enrolled" in d6:
        enrolled_rows = sum(1 for r in rows if r.get("enrolled"))
        if d6["n_enrolled"] != enrolled_rows:
            fail(f"{path.name}: d6.n_enrolled={d6['n_enrolled']} but rows "
                 f"hold {enrolled_rows}", failures)
    return doc


def check_enrolled(path: Path, screen: dict | None, failures: list[str]) -> None:
    doc = json.loads(path.read_text())
    entries = {e["pdb_id"] for e in doc.get("entries", [])}
    if doc.get("n_enrolled") != len(entries):
        fail(f"{path.name}: n_enrolled={doc.get('n_enrolled')} but "
             f"{len(entries)} entries listed", failures)
    if screen is not None:
        screen_enrolled = {r["pdb_id"] for r in screen.get("rows", [])
                           if r.get("enrolled")}
        extra = entries - screen_enrolled
        if extra:
            fail(f"{path.name}: entries not enrolled in the screen record: "
                 f"{sorted(extra)}", failures)


def check_reps(path: Path, failures: list[str]) -> None:
    doc = json.loads(path.read_text())
    initial = [r["pdb_id"] for r in doc.get("initial_representatives", [])]
    if len(initial) != len(set(initial)):
        fail(f"{path.name}: duplicate initial representatives", failures)
    known_clusters = {c["cluster"] for c in doc.get("clusters", [])}
    for r in doc.get("initial_representatives", []):
        if r.get("cluster") not in known_clusters:
            fail(f"{path.name}: representative {r['pdb_id']} names unknown "
                 f"cluster {r.get('cluster')!r}", failures)


def check_round_doc(md: Path, screen: dict, failures: list[str]) -> None:
    """Each headline count must appear NEAR its keyword — a bare
    number-presence check passes whenever another identical digit exists
    anywhere in the doc (the guard's own test caught that weakness)."""
    text = md.read_text()
    rows = screen.get("rows", [])
    from collections import Counter
    counts = Counter(r["status"] for r in rows)
    figures = {"attempt": len(rows), "floor": counts.get("floor", 0),
               "defect": counts.get("data_defect", 0),
               "screened": counts.get("screened", 0)}
    for keyword, value in figures.items():
        # A 20-char window: wide enough for "attempted **71 entries**" and
        # "1 fully screened", narrow enough that a neighboring figure's digit
        # cannot satisfy the wrong keyword (the guard's test caught an 80-char
        # window doing exactly that).
        near = (rf"\*{{0,2}}\b{value}\b[^.\n]{{0,20}}{keyword}|"
                rf"{keyword}[^.\n]{{0,20}}\*{{0,2}}\b{value}\b")
        if not re.search(near, text, re.IGNORECASE):
            fail(f"{md.name}: figure {value} not found near {keyword!r} — "
                 f"record and prose have drifted (#311 class)", failures)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=str(Path(__file__).resolve().parent.parent))
    args = ap.parse_args()
    root = Path(args.root)
    research = root / "ref" / "research"
    data = research / "data"
    failures: list[str] = []

    def guarded(fn, path, *fn_args):
        """A malformed committed record is a NAMED failure, not a traceback —
        the gate must say which file and why (inner review r1)."""
        try:
            return fn(path, *fn_args)
        except (json.JSONDecodeError, KeyError, TypeError, OSError) as exc:
            fail(f"{path.name}: unreadable or malformed record "
                 f"({type(exc).__name__}: {exc})", failures)
            return None

    screens: dict[str, dict] = {}
    for path in sorted(data.glob("negative_control_round*_screen.json")):
        match = re.match(r"negative_control_round(\d+)_screen\.json", path.name)
        screen = guarded(check_screen, path, failures)
        if screen is not None and match:
            screens[match.group(1)] = screen
    for path in sorted(data.glob("negative_control_round*_enrolled.json")):
        match = re.match(r"negative_control_round(\d+)_enrolled\.json", path.name)
        guarded(check_enrolled, path,
                screens.get(match.group(1)) if match else None, failures)
    for path in sorted(data.glob("negative_control_round*_reps.json")):
        guarded(check_reps, path, failures)
    for md in sorted(research.glob("negative_control_round*.md")):
        match = re.match(r"negative_control_round(\d+)\.md", md.name)
        if match and match.group(1) in screens:
            guarded(check_round_doc, md, screens[match.group(1)], failures)

    if failures:
        print(f"{len(failures)} negative-control record failure(s)")
        return 1
    print("negative-control records reconcile")
    return 0


if __name__ == "__main__":
    sys.exit(main())
