#!/usr/bin/env python3
"""Re-derive the registry's dataset-dependent figures and diff them against the text.

`ref/thresholds_and_standards.md` quotes numbers computed from
`ref/research/data/em_refinement_deltas.tsv`. That file grows every round, so those
numbers age -- silently, because nothing recomputes them. Three instances were caught,
all three by accident during reviews of unrelated work:

  #72   rho = +0.397 "over 44 entries", round-16 vintage, unlabelled, and a second
        "44" being used as a live denominator.
  #107  the CC_mask rate statistics were round-17 vintage (n = 25) after round 19
        took the set to 35. Re-deriving them confirmed the verdict and moved every
        number.
  #113  the "named entries" convention yielded 93 rather than the 69 it stated, once
        round 23 appended 24 screening-only rows.

Catching a class three times by luck is not a process. This is the gate.

HOW IT WORKS. Each check pairs a literal string that must appear in the registry with
a function that recomputes it from the TSV. A check fails if either

  - the recomputed value differs from what the registry states -- the figure aged; or
  - the literal is absent -- someone reworded the claim, so it needs re-checking by a
    human rather than silently passing.

The second half matters as much as the first. A gate that only compares numbers is
defeated by a rewrite, which is exactly how a figure escapes notice.

Deliberately NOT checked here: the §3 rows. Their sets are fixed and committed
(round 18), so those figures cannot age without someone editing a `DEFAULT_SET` --
which `scripts/validate.sh` already gates separately.

Usage:
    python3 scripts/check_registry_figures.py          # exits 1 on any divergence
    python3 scripts/check_registry_figures.py --json out.json
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path
from typing import Any, Callable

from scipy import stats

REGISTRY = "ref/thresholds_and_standards.md"
TSV = "ref/research/data/em_refinement_deltas.tsv"


def load(path: Path) -> list[dict[str, str]]:
    lines = path.read_text().splitlines()
    header = lines[0].split("\t")
    return [dict(zip(header, l.split("\t"))) for l in lines[1:] if l.strip()]


# --- the derivations, each one line of intent -------------------------------------

def _named(rows):
    """Entries that entered the refinement benchmark.

    Excludes the 4 unidentified `LOST` rows AND the `screened only` rows, which were
    measured pre-refinement to test a hypothesis and never refined (#113). Both are in
    the file; neither is part of the benchmark's denominator.
    """
    return [r for r in rows
            if not r["pdb_id"].startswith("UNKNOWN")
            and not r["status"].startswith("screened only")]


def _cc_deltas(rows):
    return [float(r["cc_mask_delta"]) for r in rows if r["cc_mask_delta"]]


def _dfsc_pcts(rows):
    return [float(r["d_fsc_model_delta_pct"]) for r in rows if r.get("d_fsc_model_delta_pct")]


def _dfsc_degradations(rows):
    return sorted(x for x in _dfsc_pcts(rows) if x > 0)


def _ratios(rows):
    return [float(r["d_fsc_model_pre"]) / float(r["resolution"])
            for r in rows if r.get("d_fsc_model_pre") and r.get("resolution")]


def _resolution_rho(rows):
    pairs = [(float(r["resolution"]), abs(float(r["cc_mask_delta"])))
             for r in rows if r["cc_mask_delta"] and r["resolution"]]
    return stats.spearmanr([a for a, _ in pairs], [b for _, b in pairs])[0], len(pairs)


# (label, literal that must be in the registry, derivation -> value to compare)
CHECKS: list[tuple[str, str, Callable[[list[dict]], Any]]] = [
    ("EM entry count",
     "**69** entries that entered the refinement benchmark",
     lambda rows: f"**{len(_named(rows))}** entries that entered the refinement benchmark"),
    ("CC_mask degradation count",
     "**17 degraded — a lower bound, not a count**",
     lambda rows: f"**{sum(1 for x in _cc_deltas(rows) if x < 0)} degraded "
                  f"— a lower bound, not a count**"),
    ("d_FSC degradation count",
     "of the **8 degradation magnitudes on record**",
     lambda rows: f"of the **{len(_dfsc_degradations(rows))} degradation magnitudes on record**"),
    ("d_FSC degradation median",
     "the median is 0.157 %",
     lambda rows: f"the median is {statistics.median(_dfsc_degradations(rows)):.3f} %"),
    ("worst d_FSC degradation",
     "the largest *degradation* is **+4.786 %**",
     lambda rows: f"the largest *degradation* is **+{max(_dfsc_degradations(rows)):.3f} %**"),
    ("resolution correlation",
     "**+0.361** over the **58** entries with a recorded Δ",
     lambda rows: (lambda rho, n: f"**{rho:+.3f}** over the **{n}** entries with a recorded Δ")
                  (*_resolution_rho(rows))),
    ("crossing-ratio median",
     "median ratio **0.9843**",
     lambda rows: f"median ratio **{statistics.median(_ratios(rows)):.4f}**"),
    ("crossing-ratio band count",
     "**50 of 60 (83 %) between 0.73 and 1.01**",
     lambda rows: (lambda r: f"**{sum(1 for x in r if 0.73 <= x <= 1.01)} of {len(r)} "
                             f"({100*sum(1 for x in r if 0.73 <= x <= 1.01)/len(r):.0f} %) "
                             f"between 0.73 and 1.01**")(_ratios(rows))),
]


def nesting_check(rows: list[dict]) -> dict[str, Any]:
    """The nested denominators must actually nest.

    #115: the registry read "69 ... of which 63 reached a refinement attempt", and 63
    was not a subset of 69 -- it counted the 4 LOST rows that 69 excludes. Every figure
    was individually right against the data, which is why the per-figure checks above
    all passed. Nothing compared them to each other.
    """
    named = _named(rows)
    attempted = [r for r in named if not r["status"].startswith("skipped")]
    with_delta = [r for r in named if r["cc_mask_delta"]]
    measured = [r for r in named if r["status"] == "measured"]
    ok = len(named) >= len(attempted) >= len(with_delta) >= len(measured)
    return {
        "check": "nested counts nest", "status": "OK" if ok else "BROKEN",
        "detail": (f"named {len(named)} >= attempted {len(attempted)} >= with-delta "
                   f"{len(with_delta)} >= measured {len(measured)}"
                   + ("" if ok else "  <- not monotonically nested")),
    }


def run(registry: str, rows: list[dict]) -> list[dict[str, Any]]:
    results = []
    for label, literal, derive in CHECKS:
        derived = derive(rows)
        if literal not in registry:
            status, detail = "MISSING", (
                f"the registry no longer contains {literal!r} — reworded or removed, "
                f"so it cannot be checked; the data currently gives {derived!r}")
        elif derived != literal:
            status, detail = "STALE", f"registry says {literal!r}; data gives {derived!r}"
        else:
            status, detail = "OK", derived
        results.append({"check": label, "status": status, "detail": detail})
    results.append(nesting_check(rows))
    return results


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--registry", default=REGISTRY)
    ap.add_argument("--tsv", default=TSV)
    ap.add_argument("--json", dest="json_out")
    args = ap.parse_args()

    results = run(Path(args.registry).read_text(), load(Path(args.tsv)))
    bad = [r for r in results if r["status"] != "OK"]
    for r in results:
        print(f"  {r['status']:<8} {r['check']:<28} {r['detail']}",
              file=sys.stderr if r["status"] != "OK" else sys.stdout)
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(results, indent=2) + "\n")
    if bad:
        print(f"\n{len(bad)} registry figure(s) no longer match the data.", file=sys.stderr)
        return 1
    print(f"\nall {len(results)} dataset-dependent registry figures match the data")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
