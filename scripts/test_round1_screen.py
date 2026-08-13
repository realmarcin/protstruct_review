#!/usr/bin/env python3
"""Unit tests for the round-1 selector and screen logic (#295).

These two scripts execute a REGISTERED document, so the pinned behaviours are the
registered rules themselves: the D4 rank key (missing values must lose
tie-breaks), the D7 draw composition (20 spread + 10 ascending, clusters not
entries), and the D6 statistics (worsening-side MAD, the pooled fallback, the
stop rule, and both-path-agreement exclusion). Network-free and PHENIX-free.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PASSED = 0


def load(name):
    spec = importlib.util.spec_from_file_location(
        name, REPO / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def check(label, got, want):
    global PASSED
    if got != want:
        print(f"FAIL  {label}: got {got!r}, want {want!r}")
        sys.exit(1)
    PASSED += 1
    print(f"PASS  {label} (got {got!r})")


sel = load("select_round1_reps")
scr = load("screen_round1")

# --- D4 rank key -------------------------------------------------------------------


def entry(pdb_id, d_min=None, clash=None, rfree=None):
    return {"pdb_id": pdb_id, "d_min": d_min, "clashscore": clash,
            "r_free_reported": rfree, "deposit_year": 2020}


members = [entry("BBBB", 0.9, 1.0, 0.15), entry("AAAA", 0.9, 1.0, 0.15),
           entry("CCCC", 0.8, 2.0, 0.17), entry("DDDD", 0.9, 0.5, 0.16),
           entry("EEEE", None, 0.1, 0.10)]
ranked = sorted(members, key=sel.d4_rank_key)
check("D4: best d_min wins", ranked[0]["pdb_id"], "CCCC")
check("D4: clashscore breaks d_min ties", ranked[1]["pdb_id"], "DDDD")
check("D4: id breaks full ties", [ranked[2]["pdb_id"], ranked[3]["pdb_id"]],
      ["AAAA", "BBBB"])
check("D4: missing d_min ranks last", ranked[-1]["pdb_id"], "EEEE")

# --- D7 draw -----------------------------------------------------------------------

clusters = [{"cluster": f"c{i}", "members": [entry(f"S{i:03d}", 0.5 + i * 0.005)]}
            for i in range(40)]                                   # 40 stratum
clusters += [{"cluster": f"b{i}", "members": [entry(f"B{i:03d}", 0.91 + i * 0.003)]}
             for i in range(30)]                                  # 30 band, all <= 1.0
stratum, band, initial = sel.d7_draw(clusters)
check("D7: stratum/band split", (len(stratum), len(band)), (40, 30))
check("D7: draws exactly 30", len(initial), 30)
check("D7: 20 from the stratum", sum(1 for r in initial if r["stratum"]), 20)
check("D7: stratum draw is a spread, not the head",
      [r["pdb_id"] for r in initial[:3]], ["S000", "S002", "S004"])
check("D7: band draw is ascending d_min head",
      [r["pdb_id"] for r in initial[20:23]], ["B000", "B001", "B002"])

# --- D6 statistics -----------------------------------------------------------------


def row(pdb_id, d_phenix, d_gemmi):
    return {"pdb_id": pdb_id, "status": "screened",
            "paths": {"phenix": {"delta": d_phenix},
                      "gemmi": {"delta": d_gemmi}}}


# 10 on the worsening side per path (S = MAD around their median), one clear
# both-path improver, one single-path improver.
rows = [row(f"W{i}", 0.001 * i, 0.0012 * i) for i in range(10)]
rows.append(row("BOTH", -0.05, -0.05))
rows.append(row("ONEP", -0.05, 0.001))
stats = scr.d6_statistics(rows)
check("D6: no fallback with 10 per side", stats["fallback"], "none")
check("D6: both-path improver excluded",
      next(r for r in rows if r["pdb_id"] == "BOTH")["headroom_both_paths"], True)
check("D6: one-path improver enrolled but named",
      next(r for r in rows if r["pdb_id"] == "ONEP")["headroom_one_path_only"],
      ["phenix"])
check("D6: enrolled count", stats["n_enrolled"], 11)
check("D6: excluded count", stats["n_excluded_headroom"], 1)

# Thin one side (3 worsening on gemmi) but pooled >= 8 -> pooled fallback.
rows2 = [row(f"P{i}", 0.001 * (i + 1), -0.0001) for i in range(3)]
rows2 += [row(f"Q{i}", 0.001 * (i + 1), 0.0005) for i in range(3)]
stats2 = scr.d6_statistics(rows2)
check("D6: thin side triggers pooled fallback", stats2["fallback"], "pooled")

# Pooled still thin -> registered stop, no verdicts.
rows3 = [row("X1", -0.02, -0.02), row("X2", -0.03, -0.01)]
stats3 = scr.d6_statistics(rows3)
check("D6: still-thin pool stops the round", stats3["fallback"], "stop")
check("D6: stop emits no enrollment verdicts", "n_enrolled" in stats3, False)

# --- mad ---------------------------------------------------------------------------

check("mad of a constant list is 0", scr.mad([0.5, 0.5, 0.5]), 0)
check("mad hand value", scr.mad([1.0, 2.0, 4.0]), 1.0)

print(f"\n{PASSED} checks passed")
