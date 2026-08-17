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
stratum, band, initial, collisions = sel.d7_draw(clusters)
check("D7': unique members draw with no collisions", collisions, [])
check("D7': stratum/band split", (len(stratum), len(band)), (40, 30))
check("D7': draws exactly 30", len(initial), 30)
check("D7': oversized stratum falls back to a spread, not the head (#243)",
      [r["pdb_id"] for r in initial[:3]], ["S000", "S001", "S002"])
check("D7': oversized stratum leaves no band slots",
      sum(1 for r in initial if not r["stratum"]), 0)

# The registered D7' shape: stratum fits the scope -> ALL stratum reps + band
# top-up ascending (the measured round-2 case is 26 + 4).
small = clusters[:26] + [{"cluster": f"b{i}",
                          "members": [entry(f"B{i:03d}", 0.91 + i * 0.003)]}
                         for i in range(30)]
_, _, initial2, _ = sel.d7_draw(small)
check("D7': whole stratum drawn when it fits",
      sum(1 for r in initial2 if r["stratum"]), 26)
check("D7': band top-up is ascending d_min",
      [r["pdb_id"] for r in initial2[26:]], ["B000", "B001", "B002", "B003"])

# --- #323: cluster collisions are recorded and resolved, never silent -------------

dup = [{"cluster": "c1", "members": [entry("SAME", 0.5), entry("ALT1", 0.6)]},
       {"cluster": "c2", "members": [entry("SAME", 0.55)]},
       {"cluster": "c3", "members": [entry("SAME", 0.58), entry("ALT3", 0.7)]}]
_, _, drawn3, coll3 = sel.d7_draw(dup)
check("#323: duplicate rep falls through to the next member",
      [r["pdb_id"] for r in drawn3], ["SAME", "ALT3"])
check("#323: collisions recorded with resolution",
      [(c["cluster"], c["resolved_to"]) for c in coll3],
      [("c2", None), ("c3", "ALT3")])

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

# Thin gemmi side (3 structures) but 9 UNIQUE structures on the pooled
# worsening side -> pooled fallback.
rows2 = [row(f"P{i}", 0.001 * (i + 1), -0.0001) for i in range(6)]
rows2 += [row(f"Q{i}", 0.0005 * (i + 1), 0.0005 * (i + 1)) for i in range(3)]
stats2 = scr.d6_statistics(rows2)
check("D6: thin side triggers pooled fallback", stats2["fallback"], "pooled")
check("D6: pooled n counts unique structures (#318)",
      stats2["pooled_worsening_unique_structures"], 9)

# 8 pooled VALUES from only 4 unique structures (both paths worsening) must
# STOP: the paths are paired, not independent (#318).
rows2b = [row(f"U{i}", 0.001 * (i + 1), 0.0011 * (i + 1)) for i in range(4)]
stats2b = scr.d6_statistics(rows2b)
check("D6: 8 correlated values from 4 structures still stop (#318)",
      stats2b["fallback"], "stop")

# Pooled still thin -> registered stop, no verdicts.
rows3 = [row("X1", -0.02, -0.02), row("X2", -0.03, -0.01)]
stats3 = scr.d6_statistics(rows3)
check("D6: still-thin pool stops the round", stats3["fallback"], "stop")
check("D6: stop emits no enrollment verdicts", "n_enrolled" in stats3, False)

# A degenerate (constant) worsening side gets the registered S floor instead
# of a zero-width tolerance (#318): with S = 0.0005, -0.001 survives
# (-3S = -0.0015) and -0.0016 is excluded.
rows4 = [row(f"C{i}", 0.002, 0.002) for i in range(8)]
rows4.append(row("NEAR", -0.001, -0.001))
rows4.append(row("PAST", -0.0016, -0.0016))
stats4 = scr.d6_statistics(rows4)
check("D6: constant sample triggers the S floor", stats4["s_floor_applied"], True)
check("D6: floored S is not zero-width",
      stats4["noise_scale"], {"phenix": 0.0005, "gemmi": 0.0005})
check("D6: jointly small-negative delta survives the floor",
      next(r for r in rows4 if r["pdb_id"] == "NEAR")["enrolled"], True)
check("D6: jointly past-floor delta is excluded",
      next(r for r in rows4 if r["pdb_id"] == "PAST")["enrolled"], False)

# --- round-2 observation-label rule ------------------------------------------------

check("labels: amplitude pair preferred over intensities",
      scr.pick_obs_labels(["H", "K", "L", "I-obs", "SIGI-obs", "F-obs",
                           "SIGF-obs"]), ("F-obs", "SIGF-obs"))
check("labels: filtered amplitudes outrank plain (phenix-refined MTZs)",
      scr.pick_obs_labels(["F-obs", "SIGF-obs", "F-obs-filtered",
                           "SIGF-obs-filtered"]),
      ("F-obs-filtered", "SIGF-obs-filtered"))
check("labels: intensities accepted when no amplitudes",
      scr.pick_obs_labels(["H", "K", "L", "IOBS", "SIGIOBS"]),
      ("IOBS", "SIGIOBS"))
check("labels: F without its sigma does not match",
      scr.pick_obs_labels(["F", "SIGI"]), None)
check("labels: no registered pair -> None (named data defect)",
      scr.pick_obs_labels(["H", "K", "L", "FC", "PHIC"]), None)
check("flags: canonical name wins over its -1 twin (the 9YGW case)",
      scr.pick_flag_label(["R-free-flags", "R-free-flags-1", "FOBS"]),
      "R-free-flags")
check("flags: -1 twin used when it is all there is",
      scr.pick_flag_label(["R-free-flags-1", "FOBS"]), "R-free-flags-1")
check("flags: none present -> no selector (phenix's own detection)",
      scr.pick_flag_label(["FOBS", "SIGFOBS"]), None)

# --- #320: input identity and hash-verified caching --------------------------------

import tempfile

with tempfile.TemporaryDirectory() as tmp:
    f = Path(tmp) / "input.mtz"
    f.write_bytes(b"reflections")
    digest = scr.sha256_file(f)
    check("#320: sha256 is stable", digest, scr.sha256_file(f))
    check("#320: first sight records the sidecar",
          scr.verify_or_record_hash(f), None)
    check("#320: unchanged reuse verifies", scr.verify_or_record_hash(f), None)
    f.write_bytes(b"reflections MUTATED")
    problem = scr.verify_or_record_hash(f)
    check("#320: mutated cache file is a named defect",
          problem is not None and "cache corruption" in problem, True)

versions = scr.tool_versions()
check("#320: manifest tool identity carries the required keys",
      {"phenix_bin", "gemmi_cli", "gemmi_python", "python"} <= set(versions),
      True)


# --- round-6 G2: the three-class column rule ---------------------------------------

check("G2: observation kept", scr.classify_column("FOBS"), "keep")
check("G2: second-dataset observation kept", scr.classify_column("FOBS-1"), "keep")
check("G2: anomalous pair kept", scr.classify_column("F(+)"), "keep")
check("G2: DANO kept", scr.classify_column("DANO"), "keep")
check("G2: numbered flag kept", scr.classify_column("R-free-flags-3"), "keep")
check("G2: HL coefficient dropped", scr.classify_column("HLA"), "drop")
check("G2: map coefficient dropped", scr.classify_column("2FOFCWT"), "drop")
check("G2: F-model dropped", scr.classify_column("F-model"), "drop")
try:
    scr.classify_column("MYSTERY_COL")
    check("G2: unknown label refuses loudly", "no exception", "SystemExit")
except SystemExit:
    check("G2: unknown label refuses loudly", "SystemExit", "SystemExit")

# strip round-trip on a synthetic MTZ with derived columns
import gemmi as _gemmi
import numpy as _np
import tempfile as _tf
_m = _gemmi.Mtz(with_base=True)
_m.spacegroup = _gemmi.find_spacegroup_by_name("P 1")
_m.set_cell_for_all(_gemmi.UnitCell(10, 10, 10, 90, 90, 90))
_ds = _m.add_dataset("d")
_ds.wavelength = 0.9795
for lab, typ in (("R-free-flags", "I"), ("FOBS", "F"), ("SIGFOBS", "Q"),
                 ("FC", "F"), ("PHIFC", "P"), ("HLA", "A"), ("FWT", "F")):
    _m.add_column(lab, typ)
_rows = _np.array([[h, 0, 0, h % 2, 10.0 + h, 1.0, 9.0, 45.0, 0.1, 8.0]
                   for h in range(1, 21)], dtype=_np.float32)
_m.set_data(_rows)
with _tf.TemporaryDirectory() as _tmp:
    _pth = Path(_tmp) / "t.mtz"
    _m.write_to_file(str(_pth))
    _dropped = scr.strip_mtz(_pth)
    check("G2: strip removes exactly the derived columns",
          sorted(_dropped), ["FC", "FWT", "HLA", "PHIFC"])
    _back = _gemmi.read_mtz_file(str(_pth))
    check("G2: stripped file keeps obs+flags",
          [c.label for c in _back.columns],
          ["H", "K", "L", "R-free-flags", "FOBS", "SIGFOBS"])
    _a = _np.array(_back, copy=False)
    check("G2: observation values preserved",
          bool(_np.array_equal(_a[:, 4], _rows[:, 4])), True)
    check("G2: dataset wavelength survives the strip (#361)",
          round(_back.datasets[-1].wavelength, 4), 0.9795)
    check("G2: clean file untouched", scr.strip_mtz(_pth), [])

# --- mad ---------------------------------------------------------------------------

check("mad of a constant list is 0", scr.mad([0.5, 0.5, 0.5]), 0)
check("mad hand value", scr.mad([1.0, 2.0, 4.0]), 1.0)

print(f"\n{PASSED} checks passed")
