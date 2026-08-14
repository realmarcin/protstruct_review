#!/usr/bin/env python3
"""Unit tests for the round-3 bench verdict machinery (#295).

The B3 rules are the registered content, so they are pinned hardest: the
bounded clashscore clause on a pool selected at clashscore <= 2 (the review's
load-bearing catch), flag stand-down on cross-tool conflict, the >= 2-family
verdict, and the mask-key/verdict-key reconciliation. PHENIX- and
network-free.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PASSED = 0


def load():
    spec = importlib.util.spec_from_file_location(
        "bnc", REPO / "scripts" / "bench_negative_control.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules["bnc"] = m
    spec.loader.exec_module(m)
    return m


def check(label, got, want):
    global PASSED
    if got != want:
        print(f"FAIL  {label}: got {got!r}, want {want!r}")
        sys.exit(1)
    PASSED += 1
    print(f"PASS  {label}")


b = load()
S = {"phenix": 0.00275, "gemmi": 0.0026}


def nums(**kw):
    base = {"d_phenix": 0.0, "d_gemmi": 0.0, "d_refmac": 0.0,
            "clash_pre": 2.0, "clash_post": 2.0, "d_favored_pp": 0.0,
            "d_rota_pp": 0.0, "d_zbond": 0.0, "n_protected_fixed": 0,
            "shift_unmasked": 0.01}
    base.update(kw)
    return base


# --- F-data ------------------------------------------------------------------------

flags, con = b.family_flags(nums(d_phenix=0.01, d_gemmi=0.01, d_refmac=0.004), S)
check("F-data: two-path past 3S with REFMAC agreeing flags", flags["F-data"], True)
flags, con = b.family_flags(nums(d_phenix=0.01, d_gemmi=0.001), S)
check("F-data: one path inside tolerance does not flag", flags["F-data"], False)
flags, con = b.family_flags(nums(d_phenix=0.01, d_gemmi=0.01, d_refmac=-0.002), S)
check("F-data: REFMAC sign conflict stands the flag down", flags["F-data"], False)
check("the conflict is named", len(con) == 1 and "REFMAC" in con[0], True)

# --- F-geom: the bounded clashscore clause -----------------------------------------

flags, _ = b.family_flags(nums(clash_pre=2.0, clash_post=11.0, d_zbond=0.1), S)
check("clash ratio >= 5x inside the bounds flags", flags["F-geom"], True)
flags, _ = b.family_flags(nums(clash_pre=0.0, clash_post=0.7, d_zbond=0.1), S)
check("pre=0 (9LLO class): 0.7 post does NOT flag (bounded form)",
      flags["F-geom"], False)
flags, _ = b.family_flags(nums(clash_pre=0.0, clash_post=6.0, d_zbond=0.1), S)
check("pre=0 with post past the §2 bar flags", flags["F-geom"], True)
flags, _ = b.family_flags(nums(clash_pre=0.5, clash_post=2.6, d_zbond=0.1), S)
check("pre below 1: 5.2x ratio alone does NOT flag", flags["F-geom"], False)
flags, _ = b.family_flags(nums(d_favored_pp=-0.6, d_zbond=0.1), S)
check("favored drop past 0.5 pp flags", flags["F-geom"], True)
flags, con = b.family_flags(nums(d_favored_pp=-0.6, d_zbond=-0.2), S)
check("REFMAC zBOND improvement stands F-geom down", flags["F-geom"], False)

# --- F-protected / F-shift / verdict -----------------------------------------------

flags, _ = b.family_flags(nums(n_protected_fixed=1), S)
check("a protected fix flags", flags["F-protected"], True)
flags, _ = b.family_flags(nums(shift_unmasked=0.13), S)
check("unmasked shift past 0.12 A flags", flags["F-shift"], True)

check("one flag is not a verdict",
      b.verdict({"F-data": True, "F-geom": False,
                 "F-protected": False, "F-shift": False}), "not-degraded")
check("two flags are",
      b.verdict({"F-data": True, "F-geom": False,
                 "F-protected": True, "F-shift": False}), "DEGRADED")

# --- key reconciliation ------------------------------------------------------------

mask = {"residues": [
    {"chain": "A", "resnum": 10, "icode": "", "masked": ["altconf"], "protected": []},
    {"chain": "A", "resnum": 11, "icode": "", "masked": [], "protected": ["rota_outlier"]},
    {"chain": "B", "resnum": 5, "icode": "A", "masked": [], "protected": ["clash"]}]}
check("masked keys in ca form", b.mask_key_set(mask, "masked"), {("A", "10")})
check("protected keys incl. icode", b.mask_key_set(mask, "protected"),
      {("A", "11"), ("B", "5A")})
check("verdict-key reconciliation handles icodes",
      b._residue_verdict({("B", 5, "A"): {"rota": "OUTLIER"}}, ("B", "5A")),
      {"rota": "OUTLIER"})

print(f"\n{PASSED} checks passed")
