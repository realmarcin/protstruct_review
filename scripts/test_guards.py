#!/usr/bin/env python3
"""Unit tests for the two scripts that exist to catch other scripts' mistakes.

`check_registry_figures.py` and `check_referential_integrity.py` are guards. This
repo's own triage ranks "a guard that does not guard" second only to a wrong published
claim, because a guard with a hole hides the whole class beneath it -- and both of
these had one:

  #116  `nesting_check()` compared four counts it derived ITSELF from the TSV and never
        read the registry. Those inclusions hold by construction of `append_results`,
        so no run of the pipeline could fail them; meanwhile the registry's 59, 35 and
        63 were pinned to no literal at all.
  #118  the docstring promised a `structure_ref` check that was never implemented --
        `local_structure_ids` sat computed and unused -- so a dangling structure_ref
        passed silently through the gate that exists to catch dangling refs.

Every test below must FAIL if its fix is reverted; a test that passes either way is
the same defect one level up. No network, no PHENIX; safe to run anywhere.
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


figures = load("check_registry_figures")
integrity = load("check_referential_integrity")

REGISTRY_TEXT = (REPO / figures.REGISTRY).read_text()
ROWS = figures.load(REPO / figures.TSV)


def statuses(registry: str, rows=None) -> dict[str, str]:
    return {r["check"]: r["status"] for r in figures.run(registry, rows or ROWS)}


# --- check_registry_figures: the live registry is the baseline --------------------

_live = statuses(REGISTRY_TEXT)
check("every registry figure matches the data as committed",
      sorted({v for v in _live.values()}), ["OK"])
check("the nested denominators are among the figures checked",
      all(k in _live for k in ["refinement-attempt count", "full pre/post count",
                               "refinement attempts incl. LOST", "stated counts nest"]),
      True)


# --- #116: a figure that drifts while the ordering survives must be caught --------
# This is the precise case the old check passed: 69 >= 61 >= 58 >= 35 still nests, so
# nothing fired, while the registry's stated 59 had become wrong.

_drift = REGISTRY_TEXT.replace("of which **59** reached a refinement attempt",
                               "of which **61** reached a refinement attempt")
check("a drifted attempt count is caught even though the ordering still nests",
      statuses(_drift)["refinement-attempt count"] != "OK", True)
check("and the ordering check alone would NOT have caught it",
      statuses(_drift)["stated counts nest"], "OK")

_measured = REGISTRY_TEXT.replace("**35** have full pre/post values",
                                  "**34** have full pre/post values")
check("a drifted pre/post count is caught", statuses(_measured)["full pre/post count"] != "OK", True)

_lost = REGISTRY_TEXT.replace("(**63** entries reached a refinement attempt in total",
                              "(**64** entries reached a refinement attempt in total")
check("so is the LOST-inclusive attempt count",
      statuses(_lost)["refinement attempts incl. LOST"] != "OK", True)


# --- #115, restated: the relationship must be checked in the PROSE ----------------

_broken = REGISTRY_TEXT.replace("of which **59** reached a refinement attempt",
                                "of which **70** reached a refinement attempt")
check("a stated relationship that does not nest is BROKEN",
      statuses(_broken)["stated counts nest"], "BROKEN")

_reworded = REGISTRY_TEXT.replace("of which **59** reached a refinement attempt, ",
                                  "of these, **59** were attempted; ")
check("rewording the sentence goes MISSING rather than silently passing",
      statuses(_reworded)["stated counts nest"], "MISSING")


# --- the data side, for completeness ----------------------------------------------

check("the five denominators derive from the file as the registry states them",
      [len(figures._named(ROWS)), len(figures._attempted(ROWS)),
       len(figures._with_delta(ROWS)), len(figures._measured(ROWS)),
       len(figures._attempted_incl_lost(ROWS))],
      [69, 59, 58, 35, 63])
check("`screened only` rows are outside every one of them",
      any(r["status"].startswith("screened only") for r in figures._named(ROWS)), False)


# --- #118: structure_ref resolves, or it is reported ------------------------------

_eval = {"evaluation_runs": [{
    "id": "EVAL_x", "structure_ref": "1sar",
    "ligands": [{"id": "1sar:A:CA98", "structure_ref": "1sar"}],
}]}
check("a record whose nested structure_refs agree is clean",
      integrity.check_structure_refs(_eval, Path("EVAL_x.yaml"), set()), [])

_typo = {"evaluation_runs": [{
    "id": "EVAL_x", "structure_ref": "1sar",
    "ligands": [{"id": "1sar:A:CA98", "structure_ref": "1srn"}],
}]}
_v = integrity.check_structure_refs(_typo, Path("EVAL_x.yaml"), set())
check("a nested structure_ref naming a different structure is a violation", len(_v), 1)
check("and the message locates it", "ligands[0].structure_ref" in _v[0], True)

check("with a declared structure index, refs resolve against it instead",
      len(integrity.check_structure_refs(_typo, Path("EVAL_x.yaml"), {"1sar", "1srn"})), 0)
check("and an unknown id fails against that index",
      len(integrity.check_structure_refs(_typo, Path("EVAL_x.yaml"), {"1sar"})), 1)

# The committed records must pass the check that was just switched on -- a new guard
# that fails on the existing corpus is a guard nobody will keep.
_real = sorted((REPO / "data").rglob("EVAL_*.yaml")) + sorted((REPO / "data").rglob("QDS_*.yaml"))
check("the committed records satisfy it", _real != [], True)
for _p in _real:
    import yaml
    _doc = yaml.safe_load(_p.read_text())
    check(f"  {_p.relative_to(REPO)}",
          integrity.check_structure_refs(_doc, _p.relative_to(REPO), set()), [])


print(f"\nall guard unit tests passed ({PASSED} checks)")
