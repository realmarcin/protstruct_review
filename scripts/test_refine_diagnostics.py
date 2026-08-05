#!/usr/bin/env python3
"""Unit tests for why a refinement failed.

Round 37 lost **7 of 18** entries and recorded each as `phenix.refine failed`, while the
refinement log said exactly what was wrong: the deposited data carry no R-free flags
PHENIX will accept (#242). A 39 % failure rate that reports no reason is
indistinguishable from a broken pipeline, and cost an hour of hand-diagnosis.

The cases below are partitions of what a log can say, including the one that matters
most: an **unrecognised** failure must still be quoted rather than swallowed, because a
cause nobody anticipated is exactly the one a reader needs to see.
"""
from __future__ import annotations

import importlib.util
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PASSED = 0


def load():
    spec = importlib.util.spec_from_file_location(
        "bench_rd", REPO / "scripts" / "bench_refinement_deltas.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["bench_rd"] = module
    spec.loader.exec_module(module)
    return module


def check(label: str, got, want) -> None:
    global PASSED
    if got != want:
        print(f"FAIL  {label}: got {got!r}, want {want!r}")
        sys.exit(1)
    PASSED += 1
    print(f"PASS  {label}")


b = load()


def reason_for(text: str) -> str:
    with tempfile.TemporaryDirectory() as d:
        log = Path(d) / "refine.log"
        log.write_text(text)
        return b.refine_failure_reason(log)


# --- the case that shipped ---------------------------------------------------------

_RFREE = """Starting job
Sorry: R-free flags not compatible with F-obs array.
run this command again with the additional definition:
  xray_data.r_free_flags.generate=True
Please try again.
"""
check("the R-free case is named, not reported as a bare failure",
      "no usable R-free flags" in reason_for(_RFREE), True)

# The reason must say why generate=True is NOT set, because a reader whose batch just
# lost 39 % of its entries will reach for it, and it changes the experiment.
_r = reason_for(_RFREE)
check("  and it says the obvious fix would change the experiment",
      "different experiment" in _r, True)
check("  naming the flag so the reader can find it", "r_free_flags.generate=True" in _r, True)


# --- other causes worth naming -----------------------------------------------------

check("an unknown scattering type is named",
      "scattering type" in reason_for("Sorry: Unknown scattering type: Xx\n"), True)
check("a symmetry mismatch is named",
      "symmetry" in reason_for("Sorry: Crystal symmetry mismatch between model and data\n"), True)


# --- the partition that matters most: an UNRECOGNISED failure ----------------------
# Swallowing this is how #242 happened. A cause nobody anticipated is precisely the
# one a reader needs quoted.

_novel = reason_for("Starting job\nsome unanticipated explosion\nfinal line of the log\n")
check("an unrecognised failure quotes the log rather than swallowing it",
      "final line of the log" in _novel, True)
check("  and is still marked as a refinement failure",
      _novel.startswith("phenix.refine failed"), True)


# --- absent and empty logs ---------------------------------------------------------

with tempfile.TemporaryDirectory() as d:
    check("a missing log is distinguished from a failing one",
          b.refine_failure_reason(Path(d) / "nope.log"),
          "phenix.refine produced no output and no log")
check("an empty log does not raise", reason_for(""), "phenix.refine failed")
check("a whitespace-only log does not raise", reason_for("\n\n   \n"), "phenix.refine failed")


# --- the reason reaches the caller, which is the whole point -----------------------
# refine() returning None must carry the diagnosis, or collect() has nothing to record.

import inspect
_src = inspect.getsource(b.refine)
check("refine() returns the reason alongside the failure",
      'return None, {"failure_reason": refine_failure_reason(log)}' in _src, True)
_csrc = inspect.getsource(b.collect)
check("  and collect() records it rather than a fixed string",
      'r_stats.get("failure_reason"' in _csrc, True)


print(f"\nall refine-diagnostic unit tests passed ({PASSED} checks)")
