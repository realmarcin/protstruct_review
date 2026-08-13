#!/usr/bin/env python3
"""Unit tests for the promoted gemmi R-factor path (#296).

This script is the non-cctbx half of every R-factor cross-check, so a defect here
poisons the independent side of the trust model — the side that exists to catch the
other's defects. The behaviour that motivated the promotion is pinned hardest:

  free-flag conventions. The eval-artifact original hardcoded `free = (flag != 0)`,
  which is right for PHENIX-style 0/1 columns and silently calls 95 % of a
  CCP4-style `FreeR_flag` column (0-19, free = 0) "free". The promoted script
  infers the convention, prints the inference, and refuses free fractions outside
  1-30 %.

Math checks are pure-numpy (no files); the end-to-end checks build synthetic MTZs
with gemmi in a temp dir. Network-free throughout.
"""
from __future__ import annotations

import importlib.util
import sys
import tempfile
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
PASSED = 0


def load():
    spec = importlib.util.spec_from_file_location(
        "gemmi_rfactor", REPO / "scripts" / "gemmi_rfactor.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["gemmi_rfactor"] = module
    spec.loader.exec_module(module)
    return module


def check(label: str, got, want) -> None:
    global PASSED
    if got != want:
        print(f"FAIL  {label}: got {got!r}, want {want!r}")
        sys.exit(1)
    PASSED += 1
    print(f"PASS  {label} (got {got!r})")


def check_raises(label: str, fn) -> None:
    global PASSED
    try:
        fn()
    except SystemExit:
        PASSED += 1
        print(f"PASS  {label} (refused)")
        return
    print(f"FAIL  {label}: expected SystemExit, got none")
    sys.exit(1)


gr = load()

# --- free-flag convention inference (the promotion's reason to exist) ---------------

check("PHENIX 0/1, 1 is the minority -> free is 1",
      gr.infer_free_value(np.array([0] * 95 + [1] * 5)), 1)
check("inverted 0/1, 0 is the minority -> free is 0",
      gr.infer_free_value(np.array([1] * 95 + [0] * 5)), 0)
check("CCP4 0..19 multi-valued -> free is 0",
      gr.infer_free_value(np.tile(np.arange(20), 10)), 0)
check_raises("single-valued flag column refused",
             lambda: gr.infer_free_value(np.zeros(50, dtype=int)))
check_raises("multi-valued column without 0 refused",
             lambda: gr.infer_free_value(np.tile(np.arange(1, 21), 10)))

# --- hkl join -----------------------------------------------------------------------

hkl_obs = np.array([[1, 2, 3], [-4, 5, 6], [7, 8, 9], [0, 0, 1]])
hkl_calc = np.array([[7, 8, 9], [1, 2, 3], [-4, 5, 6]])   # shuffled, one missing
io, ic = gr.join_on_hkl(hkl_obs, hkl_calc)
check("join finds every shared reflection", len(io), 3)
check("join pairs the right rows",
      [tuple(hkl_calc[j]) for j in ic], [tuple(hkl_obs[i]) for i in io])
check("negative h joins correctly (int64 key packing)",
      any((hkl_obs[i] == [-4, 5, 6]).all() for i in io), True)

# --- bin-wise scaling and R --------------------------------------------------------

fcalc = np.array([10.0, 10.0, 10.0, 20.0, 20.0, 20.0])
fobs = np.array([20.0, 20.0, 20.0, 60.0, 60.0, 60.0])   # x2 low bin, x3 high bin
s2 = np.array([0.1, 0.1, 0.1, 0.9, 0.9, 0.9])
scaled = gr.binwise_scale(fobs, fcalc, s2, nbins=2)
check("bin-wise scale recovers a different scale per bin",
      np.allclose(scaled, fobs), True)

# --- #316: the free set is held out of the scale fit -------------------------------

# One bin; work reflections sit at fobs = 2 x fcalc, free at 3 x fcalc. A leaky
# all-reflection fit absorbs part of the free-set mismatch; the work-only fit
# must not (scale exactly 2, free residual fully visible).
fcalc_l = np.full(10, 10.0)
fobs_l = np.array([20.0] * 8 + [30.0, 30.0])
s2_l = np.linspace(0.1, 0.2, 10)
work_l = np.array([True] * 8 + [False, False])
scaled_work_only = gr.binwise_scale(fobs_l, fcalc_l, s2_l, nbins=1,
                                    fit_mask=work_l)
scaled_leaky = gr.binwise_scale(fobs_l, fcalc_l, s2_l, nbins=1)
check("#316: work-only fit reproduces the work scale exactly",
      np.allclose(scaled_work_only[:8], 20.0), True)
check("#316: free residual survives the work-only fit",
      gr.r_factor(fobs_l, scaled_work_only, ~work_l) >
      gr.r_factor(fobs_l, scaled_leaky, ~work_l), True)
check("#316: work R is exact under the work-only fit",
      gr.r_factor(fobs_l, scaled_work_only, work_l), 0.0)

# A bin with no work reflections falls back to the global work scale, not to a
# leaky local fit.
work_none_in_high = np.array([True] * 5 + [False] * 5)
scaled_fb = gr.binwise_scale(np.array([20.0] * 5 + [30.0] * 5),
                             np.full(10, 10.0), s2_l, nbins=2,
                             fit_mask=work_none_in_high)
check("#316: empty-fit bin uses the global work scale",
      np.allclose(scaled_fb[5:], 20.0), True)
check_raises("#316 r1: an all-empty fit selection is refused",
             lambda: gr.binwise_scale(fobs_l, fcalc_l, s2_l, 1,
                                      np.zeros(10, dtype=bool)))

fobs_r = np.array([10.0, 10.0])
fcalc_r = np.array([9.0, 12.0])
check("R on hand values: (1+2)/20", gr.r_factor(fobs_r, fcalc_r,
      np.array([True, True])), 0.15)
check_raises("R on an empty selection refused",
             lambda: gr.r_factor(fobs_r, fcalc_r, np.array([False, False])))

# --- end-to-end on synthetic MTZs ---------------------------------------------------

import gemmi


def write_mtz(path: Path, columns: list[tuple[str, str]], rows: np.ndarray) -> None:
    mtz = gemmi.Mtz(with_base=True)
    mtz.spacegroup = gemmi.find_spacegroup_by_name("P 1")
    mtz.set_cell_for_all(gemmi.UnitCell(10, 10, 10, 90, 90, 90))
    mtz.add_dataset("synthetic")
    for label, ctype in columns:
        mtz.add_column(label, ctype)
    mtz.set_data(rows.astype(np.float32))
    mtz.write_to_file(str(path))


hkls = [(h, k, l) for h in range(1, 6) for k in range(5) for l in range(5)]
f_true = np.array([10.0 + h + k + l for h, k, l in hkls])
flags = np.array([1 if i % 20 == 0 else 0 for i in range(len(hkls))])  # 5 % free
hkl_arr = np.array(hkls, dtype=float)

with tempfile.TemporaryDirectory() as tmp:
    obs = Path(tmp) / "obs.mtz"
    calc = Path(tmp) / "calc.mtz"
    write_mtz(obs, [("F-obs", "F"), ("SIGF-obs", "Q"), ("R-free-flags", "I")],
              np.column_stack([hkl_arr, f_true, np.ones(len(hkls)), flags]))
    # Fcalc = 2 x Fobs everywhere: the bin scale must absorb the factor exactly,
    # leaving R-work = R-free = 0. A join or scaling defect shows up as R > 0.
    write_mtz(calc, [("FC", "F"), ("PHIC", "P")],
              np.column_stack([hkl_arr, 2.0 * f_true, np.zeros(len(hkls))]))

    result = gr.compute(str(obs), str(calc), None, None, None, None, 20)
    check("end-to-end matches every reflection", result["n_matched"], len(hkls))
    check("free set is the flagged 5 %", result["n_free"],
          int((flags == 1).sum()))
    check("free value inferred as the 0/1 minority", result["free_value"], 1)
    check("exact-model R-work is 0", result["r_work"], 0.0)
    check("exact-model R-free is 0", result["r_free"], 0.0)
    check("column autodetection picked the phenix labels",
          result["obs_columns"], ["F-obs", "SIGF-obs"])

    # A wrong --free-value that marks the 95 % side as free must be refused, not
    # silently accepted — this is the defect the promotion exists to prevent.
    check_raises("majority-side free value refused",
                 lambda: gr.compute(str(obs), str(calc), None, None, None, 0, 20))

    # A sub-1 % free set is legitimate (large datasets cap the test set at
    # ~1000-2000 reflections); the 0.1 % floor must accept it (#302).
    tiny_free = np.zeros(len(hkls))
    tiny_free[60] = 1                                    # 1 of 125 = 0.8 %
    obs_tiny = Path(tmp) / "obs_tiny.mtz"
    write_mtz(obs_tiny, [("F-obs", "F"), ("SIGF-obs", "Q"), ("R-free-flags", "I")],
              np.column_stack([hkl_arr, f_true, np.ones(len(hkls)), tiny_free]))
    tiny = gr.compute(str(obs_tiny), str(calc), None, None, None, None, 20)
    check("0.8 % free set accepted with the widened floor", tiny["n_free"], 1)
    check("0.8 % free set still yields exact-model R-free 0", tiny["r_free"], 0.0)

print(f"\n{PASSED} checks passed")
