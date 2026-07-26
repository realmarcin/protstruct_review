#!/usr/bin/env python3
"""Pure-logic unit tests for the two tolerance-benchmark scripts.

Covers the parts that decide what a tolerance becomes — the summary statistics and
the log parsing — without touching the network, PISA, PHENIX or CCP4, so this is
safe to run anywhere (`scripts/validate.sh` runs it).

The oracle calls themselves (biotite SASA, xtriage, ctruncate) are deliberately not
mocked: a fake oracle would only test the mock.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PASSED = 0


def load(name: str):
    """Import a benchmark script by path (they are scripts, not a package)."""
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check(label: str, got, want) -> None:
    global PASSED
    if got != want:
        print(f"FAIL  {label}: got {got!r}, want {want!r}")
        sys.exit(1)
    PASSED += 1
    print(f"PASS  {label} (got {got!r})")


t16 = load("bench_t16_bsa_vs_pisa")
t13 = load("bench_t13_wilson_b")


# --- T16: BSA summary statistics ------------------------------------------------

def t16_row(rel_pct: float) -> dict:
    return {"pdb_id": "test", "rel_delta_pct": rel_pct, "abs_rel_delta_pct": abs(rel_pct)}


summary = t16.summarize([t16_row(p) for p in (1.0, 2.0, 3.0, 4.0, 10.0)])
check("t16 counts interfaces", summary["n_interfaces"], 5)
check("t16 abs median", summary["abs_median_pct"], 3.0)
check("t16 abs max", summary["abs_max_pct"], 10.0)

# A signed median far from the absolute median is the signal that the disagreement
# is one-sided — the finding that made the BSA tolerance asymmetric in practice.
mixed = t16.summarize([t16_row(p) for p in (-5.0, -1.0, 1.0, 5.0)])
check("t16 signed median cancels on a two-sided set", mixed["signed_median_pct"], 0.0)
check("t16 abs median survives sign cancellation", mixed["abs_median_pct"], 3.0)

check("t16 empty input reports n=0", t16.summarize([]), {"n": 0})


# --- T16: the fragment guard (issue #25) ----------------------------------------
# A cleaved molecule deposited as several chains presents intramolecular pairs that
# PISA lists as interfaces. Counting them as interfaces loosened the tolerance once
# already, so pin both halves of the rule.

def pdb(ssbonds: list[tuple[str, str]], chains: dict[str, tuple[int, int]]) -> str:
    lines = []
    for a, b in ssbonds:
        # PDB SSBOND is fixed-column: the two chain ids sit at columns 15 and 29
        # (0-based). Place them explicitly rather than counting spaces in an
        # f-string — miscounting here would silently weaken the test.
        record = list("SSBOND   1 CYS  " + " " * 54)
        record[15], record[29] = a, b
        lines.append("".join(record))
    for chain, (lo, hi) in chains.items():
        for resi in (lo, hi):
            lines.append(f"ATOM      1  CA  ALA {chain}{resi:>4}      0.000   0.000   0.000")
    return "\n".join(lines) + "\n"


def fragments(text: str, tmp_name: str) -> set:
    path = Path(f"/tmp/{tmp_name}.pdb")
    path.write_text(text)
    try:
        return {tuple(sorted(pair)) for pair in t16.fragment_pairs(path)}
    finally:
        path.unlink(missing_ok=True)


# 1CHO shape: E-F and F-G disulfides, three disjoint residue ranges. E/G has no
# direct bond but reaches G through F, so component-wise reachability must catch it.
check("cleaved chain: all three fragment pairs flagged, including the indirect one",
      fragments(pdb([("E", "F"), ("F", "G")],
                    {"E": (1, 10), "F": (16, 146), "G": (149, 245)}), "test_frag_cleaved"),
      {("E", "F"), ("E", "G"), ("F", "G")})

# Fab shape: light/heavy are disulfide-linked but both number from 1 — a genuine
# two-molecule interface that must survive.
check("disulfide-linked chains with overlapping numbering are kept",
      fragments(pdb([("L", "H")], {"L": (1, 214), "H": (1, 215)}), "test_frag_fab"),
      set())

# Disjoint numbering alone is not enough: two uncleaved molecules can be numbered
# in different ranges and still form a real interface.
check("disjoint numbering without a covalent link is kept",
      fragments(pdb([], {"A": (1, 100), "B": (200, 300)}), "test_frag_disjoint"),
      set())


# --- T13: Wilson-B stratification -----------------------------------------------

def t13_row(delta: float, d_min: float, aniso: float) -> dict:
    return {"pdb_id": "test", "d_min": d_min, "aniso_delta_b": aniso,
            "delta": delta, "abs_delta": abs(delta), "rel_delta_pct": 0.0,
            "xtriage_ml_wilson_b": 20.0, "ctruncate_wilson_b": 20.0 - delta}


rows = [
    t13_row(1.0, 1.0, 2.0),    # high resolution, near-isotropic
    t13_row(2.0, 1.2, 3.0),
    t13_row(-4.0, 2.0, 6.0),   # mid resolution
    t13_row(-12.0, 3.0, 40.0),  # low resolution, strongly anisotropic
]
strat = t13.summarize(rows)
check("t13 overall n", strat["overall"]["n"], 4)
check("t13 high-res bin isolates the small deltas",
      strat["by_resolution"]["d_min < 1.5 A"], {"n": 2, "signed_median": 1.5,
                                                "abs_median": 1.5, "abs_p90": 2.0,
                                                "abs_max": 2.0})
check("t13 low-res bin carries the worst case",
      strat["by_resolution"]["d_min >= 2.5 A"]["abs_max"], 12.0)
check("t13 anisotropy split counts", strat["by_anisotropy"]["delta_B_cart >= 5"]["n"], 2)
check("t13 empty input reports n=0", t13.summarize([]), {"n": 0})


# --- T13: log parsing ------------------------------------------------------------
# Both estimators are read out of program logs, so a silently-changed log format
# would fabricate a "no disagreement" result rather than fail. Pin the formats.

XTRIAGE_LOG = """
Resolution range: 82.7475 3.45002

 ML estimate of overall B value:
   130.62 A**2

Eigen analyses of B-cart:
  | 1           |  95.10 | ( 0.99, 0.00, -0.16) |
  | 2           |  70.00 | (0.00,  1.00, 0.00)  |
  | 3           |  52.91 | ( 0.16, 0.00,  0.99) |
"""
CTRUNCATE_LOG = "Estimate of Wilson B factor: 109.185 A^(-2), with sigma  2.604"

check("xtriage Wilson B parsed", float(t13._XT_WILSON.search(XTRIAGE_LOG).group(1)), 130.62)
check("xtriage d_min parsed", float(t13._XT_RESO.search(XTRIAGE_LOG).group(2)), 3.45002)
check("xtriage B_cart eigenvalues parsed",
      [float(v) for v in t13._XT_EIGEN.findall(XTRIAGE_LOG)[:3]], [95.10, 70.00, 52.91])
check("ctruncate Wilson B parsed", float(t13._CT_WILSON.search(CTRUNCATE_LOG).group(1)), 109.185)
check("a log missing the Wilson line yields no match — never a default value",
      t13._XT_WILSON.search("Sorry: Multiple equally suitable arrays"), None)



# --- T06: free-flag convention (the bug that computed R-free and called it R-work) ---
# Reading this backwards is worth ~+0.06 in R, four times the offset being measured,
# so both conventions and the refusal case are pinned.

t06 = load("bench_t06_r_offset")

check("two-valued flags: the minority value is the test set",
      t06.free_test_value([0] * 90 + [1] * 10), 1)
check("two-valued flags, inverted convention (PHENIX-style) is handled too",
      t06.free_test_value([1] * 90 + [0] * 10), 0)
check("CCP4 multi-bin flags: bin 0 is the test set",
      t06.free_test_value([i % 20 for i in range(2000)]), 0)
check("an even two-way split is refused, not guessed",
      t06.free_test_value([0] * 50 + [1] * 50), None)
check("a single-valued flag column is refused",
      t06.free_test_value([0] * 100), None)
check("multi-bin flags with no bin 0 are refused",
      t06.free_test_value([i % 5 + 1 for i in range(500)]), None)


# --- T05 / T01: log parsing. A format change must fail loudly, not default. ---

t05cs = load("bench_t05_clashscore_h")
t05geom = load("bench_t05_bond_rmsd")
t01 = load("bench_t01_superposition")

check("phenix clashscore parsed", float(t05cs._CLASHSCORE.search("clashscore = 32.59").group(1)),
      32.59)
check("gemmi rmsD (Å) parsed, not rmsZ",
      float(t05geom._GEMMI_RMSD.search(
          "Model rmsZ: bond: 1.709, angle: 1.204\nModel rmsD: bond: 0.020, angle: 2.134"
      ).group(1)), 0.020)
check("phenix covalent-geometry bond line parsed with its count",
      t05geom._PHENIX_COVALENT_BOND.search(
          "  covalent geometry    : bond        0.01826 ( 1532)").groups(), ("0.01826", "1532"))
check("TM-align aligned length and RMSD parsed",
      t01._TM.search("Aligned length= 129, RMSD=   0.76, Seq_ID=n_identical/n_aligned= 0.605"
                     ).groups(), ("129", "0.76"))
check("phenix superpose final line parsed",
      t01._PHENIX_FINAL.search("Final 1LZ1.pdb RMSD: 0.78 N: 129 of 129").groups(),
      ("0.78", "129", "129"))
check("a superpose log that crashed yields no match — never a default RMSD",
      t01._PHENIX_FINAL.search("AttributeError: 'NoneType' object has no attribute"), None)



# --- Round 3: L-test, flip-record and restraint-library parsing ------------------

t13l = load("bench_t13_l_test")
t14 = load("bench_t14_flip_sets")
t05lib = load("bench_t05_restraint_library")

check("xtriage <|L|> parsed",
      float(t13l._XT_L.search("  <|L|>       : 0.483  (untwinned: 0.500; perfect twin: 0.375)"
                              ).group(1)), 0.483)
check("ctruncate L statistic parsed",
      float(t13l._CT_L.search("L statistic =  0.497  (untwinned 0.5 perfect twin 0.375)"
                              ).group(1)), 0.497)
check("ctruncate analysis range parsed",
      t13l._CT_RANGE.search("Data has used to  40.01 -   1.69 A resolution").groups(),
      ("40.01", "1.69"))
# The twin call is the load-bearing half of this tolerance, so pin the boundary.
check("untwinned call", t13l.twin_call(0.497), "untwinned")
check("twinned call", t13l.twin_call(0.400), "possibly_twinned")

FLIPPED = "USER  MOD Single : A  32 GLN     :FLIP  amide:sc=   0.435  F(o=-0.2,f=0.44)"
KEPT = "USER  MOD Single : A   2 GLN     :      amide:sc=   1.61   X(o=1.6,f=1.2)"
m = t14._FLIP.match(FLIPPED)
check("flip record: residue identified", (m.group("chain"), int(m.group("resseq")),
                                          m.group("resname")), ("A", 32, "GLN"))
check("flip record: FLIP decision and category", (m.group("decision").strip(),
                                                  m.group("category")), ("FLIP", "F"))
m2 = t14._FLIP.match(KEPT)
check("non-flip record: empty decision, X category", (m2.group("decision").strip(),
                                                      m2.group("category")), ("", "X"))
check("a non-USER-MOD line does not parse as a flip", t14._FLIP.match("ATOM      1  N   MET A   1"),
      None)

check("phenix bond+count parsed for library toggle",
      t05lib._PHENIX_BOND.search("  covalent geometry    : bond        0.00510 (  440)").groups(),
      ("0.00510", "440"))
check("gemmi bond and angle rmsD parsed together",
      t05lib._GEMMI_RMSD.search("Model rmsD: bond: 0.020, angle: 2.134, torsion: 27.1").groups(),
      ("0.020", "2.134"))

print(f"\nall bench tolerance unit tests passed ({PASSED} checks)")
