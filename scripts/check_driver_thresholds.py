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

REPO = Path(__file__).resolve().parent.parent
REGISTRY = REPO / "ref/thresholds_and_standards.md"

# Lines that legitimately show a retired value as HISTORY, not as a live threshold.
HISTORY_MARKERS = ("pre-benchmark", "originally", "round-5", "round 5", "catalog's",
                   "was a ", "was the", "were the", "were round", "retired")

# One entry per metric: the current value, a regex that finds it in the registry (to
# prove the `current` literal is not itself stale), the consumers that quote it, and the
# retired literals that must not appear as a live threshold.
CHECKS = [
    {
        "metric": "NC FIT threshold d_refmac, ANIS (§6)",
        "current": "0.01150",
        "registry": r"\(unchanged[^)]*\), d_refmac \*\*([\d.]+)\*\* from the round-9 null",
        "consumers": ["scripts/bench_recover_leg.py", "scripts/bench_round10.py",
                      "scripts/bench_round11.py"],
        "retired": ["0.01220", "0.01090", "0.00540"],
    },
    {
        "metric": "CA RMSD agreement (§3)",
        "current": "0.03",
        "registry": r"\| CA RMSD \| \\\|Δ\\\| ≤ \*\*([\d.]+) Å\*\*",
        "consumers": ["ref/driving_example.md", "ref/driving_example_T01.md",
                      "scripts/bench_t01_superposition.py"],
        "retired": ["≤ 0.10 Å", "≤ **0.10 Å**", "≤0.10 Å"],
    },
    {
        "metric": "ΔRMSD band, d_min >= 2.5 (§4)",
        "current": "0.25",
        "registry": r"`d_min ≥ 2\.5 Å`: \+ \*\*([\d.]+) Å\*\*",
        "consumers": ["ref/driving_example.md", "scripts/bench_refinement_deltas.py"],
        "retired": ["RMSD_pre + 0.05 Å", "RMSD_pre + **0.05"],
    },
    {
        "metric": "CC_mask band, d_min < 3.0 (§4)",
        "current": "0.04",
        "registry": r"`d_min < 3\.0 Å`: CC_mask_post ≥ CC_mask_pre − \*\*([\d.]+)\*\*",
        "consumers": ["ref/driving_example.md", "ref/driving_example_T04.md",
                      "scripts/bench_refinement_deltas_em.py"],
        "retired": ["CC_mask_pre − 0.01", "CC_mask_pre − **0.01**"],
    },
    {
        "metric": "d_FSC_model band (§4)",
        "current": "1.05",
        "registry": r"d_FSC_model_post ≤ d_FSC_model_pre × ([\d.]+)",
        "consumers": ["ref/driving_example.md", "ref/driving_example_T04.md",
                      "scripts/bench_refinement_deltas_em.py"],
        # the absolute +0.05 A form is retired (the band is now relative ×1.05); the
        # calibration "within 0.10 A of the EMDB header" is a DIFFERENT quantity (§5).
        "retired": ["d_FSC_model_pre + 0.05 Å", "d_FSC_model_pre + **0.05"],
    },
]


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
    registry = REGISTRY.read_text()
    failures = []
    for c in CHECKS:
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
    print(f"\nall {len(CHECKS)} registry-governed thresholds are current in their consumers")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
