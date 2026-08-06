#!/usr/bin/env python3
"""Every id a round refined must appear in that round's committed selection record.

#255 was a selection id (1A0C) that reached the refinement benchmark -- it is a refined,
usable row in `round37_xray_deltas.json` -- but was missing from
`round37_xray_selection.json`. The write-up's "21 selected" was right; the selection
JSON had silently dropped one, so the count could not be checked against its own artefact.
`scripts/validate.sh` passed for the whole life of round 37 with the record inconsistent,
because nothing reconciled the two files. #261.

The invariant is one-directional and cheap: everything that entered the deltas
(`rows` + `skipped`) must be in `selection.selected`. The converse is NOT required --
`selection.selected` legitimately holds MORE ids than the deltas, because fetch rejects
(no amplitudes / no FREE column) are selected but never reach the benchmark. So this
checks `selected superset (rows union skipped)`, not equality.

    python3 scripts/check_selection_deltas.py          # exits 1 on any missing id

Kept importable (`reconcile`) so `test_selection_deltas.py` can drive it on synthetic
records without touching the committed files -- a guard that cannot be tested has not
been checked (round 27).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "ref" / "research" / "data"
SELECTION_GLOB = "*_xray_selection.json"


def deltas_ids(deltas: dict) -> set[str]:
    """Every id that entered the refinement benchmark: rows AND skipped."""
    return ({r["pdb_id"] for r in deltas.get("rows", [])}
            | {s["pdb_id"] for s in deltas.get("skipped", [])})


def reconcile(selection: dict, deltas: dict) -> list[str]:
    """Ids present in the deltas but absent from `selection.selected`, sorted.

    Empty means the selection record accounts for every refined entry. A non-empty
    return is the #255 defect: the round refined an entry its selection record does not
    list, so the selection count is unverifiable against the deltas.
    """
    selected = {e["pdb_id"] for e in selection.get("selected", [])}
    return sorted(deltas_ids(deltas) - selected)


def _deltas_path_for(selection_path: Path) -> Path:
    return selection_path.with_name(
        selection_path.name.replace("_selection.json", "_deltas.json"))


def main() -> int:
    pairs = []
    for sel_path in sorted(DATA.glob(SELECTION_GLOB)):
        dl_path = _deltas_path_for(sel_path)
        if dl_path.exists():
            pairs.append((sel_path, dl_path))
    if not pairs:
        print("check_selection_deltas: no selection/deltas pairs found", file=sys.stderr)
        return 0
    failed = False
    for sel_path, dl_path in pairs:
        missing = reconcile(json.loads(sel_path.read_text()),
                            json.loads(dl_path.read_text()))
        round_name = sel_path.name.split("_")[0]
        if missing:
            failed = True
            print(f"  {round_name}: {len(missing)} id(s) in {dl_path.name} but not in "
                  f"{sel_path.name}: {', '.join(missing)}", file=sys.stderr)
        else:
            print(f"  {round_name}: selection record accounts for every refined entry")
    if failed:
        print("\na round refined an entry its selection record does not list (#261).",
              file=sys.stderr)
        return 1
    print(f"selection records account for every refined entry ({len(pairs)} rounds)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
