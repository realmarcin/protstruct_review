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
import os
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



# --- Round 4: validation-report parsing, and the hyphenated-attribute trap ---------

dep = load("bench_vs_deposited")

ENTRY = ('<Entry DCC_R="0.1739" DCC_Rfree="0.2358" PDB-Rfree="0.2340" '
         'absolute-percentile-DCC_Rfree="47.6" high-resol-relative-percentile-DCC_Rfree="1.36" '
         'clashscore="1.18" absolute-percentile-clashscore="95.0" DataCompleteness="98.50">')

# The trap: a (\w+)="..." scan matches the TAIL of the prefixed attributes and returns
# a percentile where an R-free was wanted. These pin the exact-name behaviour.
check("DCC_Rfree read exactly, not the percentile variant",
      dep.entry_attribute(ENTRY, "DCC_Rfree"), 0.2358)
check("PDB-Rfree (deposited) read separately from DCC_Rfree",
      dep.entry_attribute(ENTRY, "PDB-Rfree"), 0.2340)
check("clashscore not confused with its percentile",
      dep.entry_attribute(ENTRY, "clashscore"), 1.18)
check("DataCompleteness read", dep.entry_attribute(ENTRY, "DataCompleteness"), 98.50)
check("a missing attribute yields None, never a stray match",
      dep.entry_attribute(ENTRY, "Rwork"), None)

check("ramalyze outlier SUMMARY parsed",
      float(dep._RAMA_OUT.search("SUMMARY: 0.00% outliers (Goal: < 0.2%)").group(1)), 0.0)
check("ramalyze favored SUMMARY parsed",
      float(dep._RAMA_FAV.search("SUMMARY: 98.15% favored (Goal: > 98%)").group(1)), 98.15)
check("model_vs_data completeness parsed",
      float(dep._MVD_COMPLETENESS.search("  Completeness in resolution range: 0.984612"
                                         ).group(1)), 0.984612)


# --- Round 4: SS-agreement and DockQ-mapping helpers ------------------------------

t15b = load("bench_t15_ss_agreement")
t16map = load("bench_t16_dockq_mapping")

check("t15 agreement value parsed", float(t15b._AGREEMENT.search("    value_numeric: 0.7500"
                                                                 ).group(1)), 0.75)
check("t15 concordant counts parsed",
      t15b._COUNTS.search("57/76 concordant over residues").groups(), ("57", "76"))

# Only same-sequence chains may be swapped: a different sequence is an error, not
# ambiguity, and scoring it would inflate the measured mapping cost.
HOMO = {"A": "AAAA", "B": "BBBB", "C": "AAAA", "D": "BBBB"}
maps = t16map.plausible_mappings(HOMO)
check("homo-oligomer: identity mapping is offered first", maps[0], ("ABCD", "ABCD"))
check("homo-oligomer: only same-sequence swaps are enumerated",
      all(all(HOMO[m] == HOMO[n] for m, n in zip(*pair)) for pair in maps), True)
check("hetero-complex: no ambiguity to measure",
      t16map.plausible_mappings({"A": "AAAA", "B": "BBBB"}), [("AB", "AB")])
check("single chain: nothing to map", t16map.plausible_mappings({"A": "AAAA"}), [])



# --- Round 5: refinement deltas and the favored-% counting ------------------------

refdel = load("bench_refinement_deltas")
refem = load("bench_refinement_deltas_em")

# Cα shift is deliberately computed WITHOUT superposition — refinement preserves the
# frame, so superposing first would absorb part of what is being measured.
import tempfile as _tf


def _pdb(coords):
    lines = []
    for i, (chain, resseq, x, y, z) in enumerate(coords, 1):
        lines.append(
            f"ATOM  {i:5d}  CA  ALA {chain}{resseq:>4}    "
            f"{x:8.3f}{y:8.3f}{z:8.3f}  1.00 20.00           C")
    path = Path(_tf.mkstemp(suffix=".pdb")[1])
    path.write_text("\n".join(lines) + "\n")
    return path


a = _pdb([("A", 1, 0.0, 0.0, 0.0), ("A", 2, 1.0, 0.0, 0.0)])
b = _pdb([("A", 1, 0.0, 0.0, 0.0), ("A", 2, 1.0, 0.0, 0.0)])
c = _pdb([("A", 1, 3.0, 0.0, 0.0), ("A", 2, 4.0, 0.0, 0.0)])   # rigid 3 Å translation
try:
    check("identical models give zero shift", refdel.ca_shift_rmsd(a, b), (0.0, 2))
    # A rigid translation must NOT be superposed away: it is real movement.
    check("a rigid 3 Å translation is reported, not superposed away",
          refdel.ca_shift_rmsd(a, c), (3.0, 2))
    check("no shared residues yields None", refdel.ca_shift_rmsd(a, _pdb([("B", 9, 0., 0., 0.)])),
          (None, 0))
finally:
    for path in (a, b, c):
        path.unlink(missing_ok=True)

check("phenix.refine R-factor pair parsed",
      refdel._R_WORK.search("r_work=0.1740 r_free=0.2360").groups(), ("0.1740", "0.2360"))
check("mtriage d_FSC_model(0.143) masked column parsed",
      refem._D_FSC_MODEL.search(
          "    FSC(map,model map)=0.143       :     2.62    29.79").groups(), ("2.62", "29.79"))
check("map_correlations CC_mask parsed",
      float(refem._CC_MASK.search("  CC_mask  : 0.8071").group(1)), 0.8071)

# The favored-% counter: the report has no entry-level figure, and the rotamer
# attribute is a rotamer NAME, not a verdict — so it must yield None rather than a
# number that would look like a measurement.
RAMA_XML = ' rama="Favored" rama="Favored" rama="Allowed" rama="OUTLIER" '
check("Ramachandran favored % counted from per-residue verdicts",
      dep.favored_pct(RAMA_XML, dep._RES_RAMA), 50.0)
check("rotamer names are not verdicts — None, not a confident 0.0 %",
      dep.favored_pct(' rota="m-10" rota="mp" rota="mt-10" ', dep._RES_ROTA), None)
check("no verdicts at all yields None", dep.favored_pct("<Entry/>", dep._RES_RAMA), None)



# --- Round 6: reduce2 flip poses, report rotamers, perturbation ------------------

REDUCE2_REPORT = """
 Added MoverAmideFlip 2 to chain A GLN 2
   AmideFlip at chain A GLN 2 NE2 Initial score: 13.30 final score: 13.30 pose Unflipped . . . .
   HisFlip at chain A HIS 55 ND1 Initial score: 1.00 final score: 9.00 pose Flipped . . . .
   NH3Rotator at chain A LYS 4 NZ Initial score: 6.81 final score: 6.82 pose Angle 178.0 deg . .
"""
calls = {}
for m in t14._REDUCE2_FLIP.finditer(REDUCE2_REPORT):
    calls[(m.group("chain"), int(m.group("resseq")), m.group("resname").upper())] = (
        m.group("pose") == "Flipped")
check("reduce2 Unflipped pose parsed", calls.get(("A", 2, "GLN")), False)
check("reduce2 Flipped pose parsed", calls.get(("A", 55, "HIS")), True)
check("a rotator is not a flip", ("A", 4, "LYS") in calls, False)

SUBGROUP = ('<ModelledSubgroup rota="mmm" model="1" chain="A" resnum="1" resname="MET"/>'
            '<ModelledSubgroup rscc="0.9" model="1" chain="A" resnum="2" resname="GLY"/>')
check("report rotamer assignment keyed by residue",
      dep.report_rotamers(SUBGROUP), {("A", 1, "MET"): "mmm"})
check("rotalyze per-residue line parsed",
      dep.local_rotamers(" A   1  MET:1.00:79.0:306.4:300.1:284.6::Favored:mmm"),
      {("A", 1, "MET"): ("mmm", "Favored")})
check("agreement computed over shared residues only",
      dep.rotamer_agreement(SUBGROUP, " A   1  MET:1.00:79.0::::Favored:mmm")["rotamer_agreement"],
      1.0)

# The perturbation used for the detection test must actually move atoms, and must
# move them by about the requested sigma — a no-op would make the bands look blind.
_p = _pdb([("A", i, 0.0, 0.0, 0.0) for i in range(1, 201)])
try:
    moved = refdel.perturb(_p, 0.5, Path(_tf.mkdtemp()))
    shift, n = refdel.ca_shift_rmsd(_p, moved)
    check("perturbation moves atoms by ~sigma*sqrt(3)", 0.6 < shift < 1.1, True)
    check("perturbation keeps every residue", n, 200)
finally:
    _p.unlink(missing_ok=True)



# --- Round 7: rotalyze score parsing and boundary exposure ------------------------

# The score column is what makes the favored/allowed boundary measurable at all, and
# it sits between two other numeric fields — an off-by-one here would silently
# produce a boundary-exposure figure from the wrong column.
ROTA_LINE = " A   1  MET:1.00:79.0:306.4:300.1:284.6::Favored:mmm"
_m = dep._ROTALYZE_RESIDUE.search(ROTA_LINE)
check("rotalyze occupancy and score columns not transposed",
      (_m.group("occ"), _m.group("score")), ("1.00", "79.0"))

# Exposure counts residues whose score is within a factor m of the 2 % cutoff.
EXPOSED = "\n".join([
    " A   1  ALA:1.00:1.80:0:::" + ":Allowed:t",     # 1.80 -> within x1.25 (1.6-2.5)
    " A   2  ALA:1.00:2.40:0:::" + ":Favored:t",     # 2.40 -> within x1.25
    " A   3  ALA:1.00:79.0:0:::" + ":Favored:t",     # far above
    " A   4  ALA:1.00:0.10:0:::" + ":OUTLIER:t",     # far below
])
exposure = dep.boundary_exposure(EXPOSED, margins=(1.25,))
check("boundary exposure counts only residues near the cutoff",
      (exposure["n_scored"], exposure["exposed_x1.25"]), (4, 2))
check("boundary exposure as a percentage", exposure["exposed_pct_x1.25"], 50.0)
check("no scored residues yields an empty result", dep.boundary_exposure("no residues here"), {})



# --- Round 8: restrained refinement mode ----------------------------------------

# The restrained and unrestrained runs must not collide in the cache, or the second
# would silently read the first's output and report a zero difference between them.
check("restrained and unrestrained refinements use distinct prefixes",
      refdel.refine_prefix("12lo", True) != refdel.refine_prefix("12lo", False), True)
check("low-resolution restraints request NCS and secondary structure",
      ("ncs_search.enabled=True" in refdel.LOW_RES_RESTRAINTS
       and "secondary_structure.enabled=True" in refdel.LOW_RES_RESTRAINTS), True)
# reference_model restraints would restrain the model to itself here, so they must
# NOT be in the recipe.
check("reference_model restraints excluded", "reference_model" in refdel.LOW_RES_RESTRAINTS, False)



# --- Round 9: the FSC last-crossing rule -----------------------------------------

# mtriage reports the FIRST shell below the threshold, which a single anomalous
# low-resolution shell defeats (9VJD: dips to 0.073 at 23.11 Å, recovers, so mtriage
# returns 23.11 Å for a 2.86 Å map). These pin the last-crossing behaviour.
CURVE = [(30.0, 0.99), (23.0, 0.07), (20.0, 0.95), (10.0, 0.90),
         (3.0, 0.60), (2.8, 0.10), (2.6, 0.08), (2.4, 0.05)]
# With sustain=1 the rule degenerates to "first crossing" and the low-resolution dip
# wins — which is precisely mtriage's bug, pinned here so the guard cannot regress.
check("sustain=1 reproduces mtriage's bug (first crossing wins)",
      refem.d_fsc_from_curve(CURVE, 0.143, sustain=1), 23.0)
# Requiring 2 consecutive shells rejects the single-shell dip.
check("a sustained crossing rejects a one-shell dip",
      refem.d_fsc_from_curve(CURVE, 0.143, sustain=2), 2.8)
check("a curve that never crosses yields None",
      refem.d_fsc_from_curve([(30.0, 0.99), (3.0, 0.80)], 0.143, sustain=2), None)
check("a run shorter than `sustain` does not count",
      refem.d_fsc_from_curve([(30.0, 0.10), (20.0, 0.99), (3.0, 0.99)], 0.143, sustain=2), None)
check("default sustain is stated, not incidental", refem.FSC_SUSTAIN_SHELLS, 20)

# The curve file stores 1/d in column 1; reading it as d would inverte the whole
# analysis and still produce plausible-looking numbers.
import tempfile as _tf2
_cp = Path(_tf2.mkstemp(suffix=".log")[1])
try:
    _cp.write_text("    0.010000000     0.990000000\n    0.500000000     0.100000000\n")
    check("curve reader converts 1/d to d", refem.read_fsc_curve(_cp), [(100.0, 0.99), (2.0, 0.10)])
finally:
    _cp.unlink(missing_ok=True)



# --- Round 10: chi1 geometry check ------------------------------------------------

# chi1 comes from the 4th colon-separated field of a rotalyze line. Taking the wrong
# field would compare an occupancy or a score against a dihedral and still produce
# numbers, so pin the extraction.
_m10 = dep._ROTALYZE_RESIDUE.search(" A   1  MET:1.00:79.0:306.4:300.1:284.6::Favored:mmm")
check("chi1 is the first field after the score",
      _m10.group("rest").split(":")[0], "306.4")

# Angles are compared modulo 360 with wraparound, so 359° and 1° are 2° apart, not 358.
def _wrapped(a, b):
    return min(abs(a - b), 360.0 - abs(a - b))
check("chi1 comparison wraps around 360°", _wrapped(359.0, 1.0), 2.0)
check("chi1 comparison unaffected mid-range", _wrapped(180.0, 176.0), 4.0)



# --- Round 11: cross-library sidechain comparison ---------------------------------

# gemmi rmsz emits both backbone and sidechain torsions. Counting backbone ones as
# chi would mix in phi/psi deviations and destroy the comparison, so the filter is
# pinned.
TORSIONS = """A 7(LEU) torsion CA-CB-CG-CD1: |Z|=3.8
A 7(LEU)-8(ASN) torsion C-N-CA-C: |Z|=3.0
A 7(LEU) torsion N-CA-CB-CG: |Z|=1.2
"""
worst = {}
for line in TORSIONS.splitlines():
    m = dep._GEMMI_TORSION.match(line.strip())
    if not m or m.group("atoms") in dep._BACKBONE_TORSIONS:
        continue
    key = (m.group("chain"), int(m.group("resseq")), m.group("resname"))
    worst[key] = max(worst.get(key, 0.0), float(m.group("z")))
check("sidechain torsions kept, backbone excluded", worst, {("A", 7, "LEU"): 3.8})
# Inter-residue backbone torsions are written "7(LEU)-8(ASN)" and do not match the
# single-residue pattern at all, so they are excluded before the name filter even
# applies. That is the stronger guarantee, so assert it directly.
check("an inter-residue backbone torsion line does not match at all",
      dep._GEMMI_TORSION.match("A 7(LEU)-8(ASN) torsion C-N-CA-C: |Z|=3.0"), None)
check("the worst chi per residue is kept, not the first", worst[("A", 7, "LEU")], 3.8)



# --- Round 12: d_FSC_model relative band ------------------------------------------

# The band became relative because the quantity spans 2.2-6.1 Å. A 0.26 Å change on
# a 6.1 Å value and a 0.12 Å change on a 2.7 Å value are the same 4.3 % — an absolute
# band cannot treat them alike, which is what broke ±0.05 Å.
def _rel(pre, post):
    return round(100.0 * (post - pre) / pre, 2)


check("a large absolute change on a large value is a small relative one",
      _rel(6.1020, 6.3629), 4.28)
check("a smaller absolute change on a small value is the same relative size",
      _rel(2.7163, 2.5967), -4.40)
check("both breach an absolute 0.05 Å band",
      (abs(6.3629 - 6.1020) > 0.05, abs(2.5967 - 2.7163) > 0.05), (True, True))
check("neither breaches a 5 % relative band",
      (abs(_rel(6.1020, 6.3629)) <= 5.0, abs(_rel(2.7163, 2.5967)) <= 5.0), (True, True))



# --- Round 13: d_FSC_model is one-sided -------------------------------------------

# d_FSC_model is a resolution, so LARGER is worse and the §4 clause is "did not
# degrade". Measuring it two-sided counts a better fit as a failure — which is
# exactly what happened to 9H7U (4.0604 -> 2.5924, a 36 % improvement).
def _degradation_pct(pre, post):
    return max(0.0, round(100.0 * (post - pre) / pre, 2))


check("a large improvement registers as zero degradation",
      _degradation_pct(4.0604, 2.5924), 0.0)
check("a genuine degradation is reported at its size",
      _degradation_pct(6.1020, 6.3629), 4.28)
check("the 36 % improvement would fail a two-sided 5 % band",
      abs(100.0 * (2.5924 - 4.0604) / 4.0604) > 5.0, True)
check("but passes the one-sided band the clause specifies",
      _degradation_pct(4.0604, 2.5924) <= 5.0, True)


# --- Round 14: EM entry selection -------------------------------------------------

fetchem = load("fetch_em_entries")

# A single sorted RCSB query does NOT sample a resolution window: asking for the 40
# best-resolution entries in 2.4-3.2 A returned 40 entries at exactly 2.40 A, because
# the PDB holds far more structures at the fine end of any window. That matters here
# because the tolerance under test is resolution-conditional, so a set collapsed onto
# one resolution cannot test it. `stratified_search` queries equal sub-bands instead.
_BANDS: list[tuple[float, float]] = []


def _fake_search(lo: float, hi: float, rows: int) -> list[str]:
    """Stand-in for the RCSB call, labelling each hit with the band it came from."""
    _BANDS.append((round(lo, 4), round(hi, 4)))
    return [f"B{len(_BANDS)}_{i}" for i in range(rows)]


_real_search = fetchem.search
fetchem.search = _fake_search
try:
    _BANDS.clear()
    ordered = fetchem.stratified_search(2.4, 3.2, strata=4, per_stratum=3)
finally:
    fetchem.search = _real_search

check("the window is split into equal sub-bands that tile it exactly",
      _BANDS, [(2.4, 2.6), (2.6, 2.8), (2.8, 3.0), (3.0, 3.2)])
# The round-robin is the point: a caller that stops at --limit must still get a
# spread. Taking the first 4 of a concatenated (not interleaved) list would return
# four entries from the finest band alone -- the exact failure being corrected.
check("results are interleaved across bands, so an early stop still spans the window",
      ordered[:4], ["B1_0", "B2_0", "B3_0", "B4_0"])
check("every candidate is returned, not just the first of each band",
      len(ordered), 12)

# Size caps. 8RJC (255 550 atoms) reached the round-14 cache before the model cap
# existed; real_space_refine on it would have run for hours and contributed a single
# resolution point, so the cap is a cost gate, not a quality judgement.
_CALLS: list[str] = []


def _fake_get(url: str, timeout: int = 300) -> bytes:
    _CALLS.append(url)
    return b"x" * 20_000_000          # 20 MB model


_real_get = fetchem._get
fetchem._get = _fake_get
try:
    _tmp = Path(__import__("tempfile").mkdtemp())
    over, reason = fetchem.fetch_model("TEST", _tmp, max_model_mb=8.0)
    under, _ = fetchem.fetch_model("TES2", _tmp, max_model_mb=25.0)
finally:
    fetchem._get = _real_get

check("an oversized model is refused", over, None)
check("and the refusal names the measured size and the cap",
      reason, "model 20 MB exceeds --max-model-mb 8")
check("an oversized model is not left on disk to look like a cache hit",
      (_tmp / "test.cif").exists(), False)
check("a model under the cap is kept", under is not None, True)


# --- Round 14: refinement skips must explain themselves ---------------------------

# 11MR failed with 128 atoms of an unparameterised ligand (A1C9W). Recorded as
# "real_space_refine failed", that is indistinguishable from a bug in this script; it
# is actually a property of the entry, and belongs in the scope limits.
import tempfile as _tf

_logdir = Path(_tf.mkdtemp())


def _reason(text: str) -> str:
    p = _logdir / "one.log"
    p.write_text(text)
    return refem.refine_failure_reason(p)


check("an unparameterised ligand is named, with its atom count",
      _reason("Number of atoms with unknown nonbonded energy type symbols: 128\n"
              "Sorry: Fatal problems interpreting model file:"),
      "unparameterised ligand: 128 atoms with unknown nonbonded energy types "
      "(no monomer-library restraints)")
# The ligand cause is checked first because cctbx reports it alongside a generic
# `Sorry:` line; matching the Sorry first would report the vague half of the message.
check("a plain Sorry: is carried through verbatim",
      _reason("Sorry: Map and model do not overlap."),
      "real_space_refine: Map and model do not overlap.")
check("a crash is distinguished from a user-actionable stop",
      _reason("Traceback (most recent call last):\n  File x\nValueError: boom"),
      "real_space_refine crashed (traceback in log)")
check("an empty log is not reported as success",
      _reason(""), "real_space_refine produced no usable result")
# 10EN failed inside map_correlations, whose skip printed nothing at all -- the entry
# vanished between two bracketed ids in the log. The reason extractor is shared across
# steps so no step can fail invisibly.
(_logdir / "sc.log").write_text(
    'Sorry: The model contains atoms which are not in the scattering table '
    '"electron".\n    Unknown atom types:\n    O1- \n')
check("an unknown scattering type is named, with the offending atom",
      refem.failure_reason(_logdir / "sc.log", "map_correlations"),
      "atom type absent from the electron scattering table: O1-")
check("the step name is carried into a generic failure",
      refem.failure_reason(_logdir / "one.log", "map_correlations"),
      "map_correlations produced no usable result")
check("a missing log is reported as such",
      refem.refine_failure_reason(_logdir / "absent.log"),
      "real_space_refine produced no log")


# --- Round 14: entry count is not evidence for a one-sided band --------------------

# Round 14 ran 8 EM entries and every one improved, so it added 8 to the entry count
# and 0 to the evidence. summarize() must make that visible rather than reporting a
# healthy-looking n.
_r14 = [{"pdb_id": i, "resolution": r, "cc_mask_pre": 0.8, "cc_mask_post": 0.8 + d,
         "cc_mask_delta": d, "d_fsc_model_delta_pct": pct,
         "d_fsc_model_degradation_pct": max(0.0, pct), "d_fsc_model_reliable": True}
        for i, r, d, pct in [("11NJ", 2.40, 0.0195, -0.135), ("11QC", 2.40, 0.0004, 0.0),
                             ("10XZ", 2.60, 0.0001, 0.0), ("10YA", 2.70, 0.0016, 0.0),
                             ("11JF", 2.85, 0.0099, -0.112), ("21AO", 2.85, 0.0006, 0.0),
                             ("10ES", 3.00, 0.0418, -1.229), ("10IJ", 3.10, 0.0244, -0.665)]]
_s14 = refem.summarize(_r14)

check("round 14's entry count is 8", _s14["n_entries"], 8)
check("but no entry degraded: the CC_mask minimum is positive",
      _s14["cc_mask_delta"]["min"] > 0, True)
check("and the worst d_FSC_model degradation is zero",
      _s14["d_fsc_model_degradation_pct"]["max"], 0.0)
# The trap this guards: a two-sided |delta| summary would report a 1.229 % "change"
# on 10ES and make the round look like it stressed the band. It did not -- 10ES
# improved.
check("the largest d_FSC_model movement is an improvement, not a stressor",
      min(r["d_fsc_model_delta_pct"] for r in _r14), -1.229)
check("so a one-sided read of this round yields no evidence at all",
      sum(1 for r in _r14 if r["cc_mask_delta"] < 0
          or r["d_fsc_model_degradation_pct"] > 0), 0)


# --- Round 15: a resolution window does not sample independent depositions --------

# 22 historical entries came from 12 publications, and the four largest CC_mask
# degradations ever recorded came from TWO papers as near-duplicate pairs
# (9UPM -0.0475 / 9UPO -0.0402; 10SD -0.0421 / 10SF -0.0371). One entry per
# publication is the default so a band cannot be anchored by one lab twice.
_ENTRY_META = {
    "AAAA": (3.1, "111", "10.1/dup"), "BBBB": (3.2, "222", "10.1/dup"),
    "CCCC": (3.3, "333", "10.2/other"), "DDDD": (3.4, "444", None),
    "EEEE": (3.5, "555", None),
}


def _fake_meta(pdb_id):
    res, acc, doi = _ENTRY_META[pdb_id.upper()]
    return res, acc, doi or f"unpublished:{pdb_id.upper()}"


_real_meta, _real_model, _real_map = (
    fetchem.entry_metadata, fetchem.fetch_model, fetchem.fetch_map)
fetchem.entry_metadata = _fake_meta
def _stub(path: Path) -> Path:
    """collect() stats the map to report its size, so the stub must leave a file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"stub")
    return path


fetchem.fetch_model = lambda pid, cache, mm: (_stub(cache / f"{pid.lower()}.cif"), None)
fetchem.fetch_map = lambda pid, acc, cache, mm: (_stub(cache / f"{pid.lower()}.map"), None)
try:
    _c = Path(__import__("tempfile").mkdtemp())
    default_all, _ = fetchem.collect(["AAAA", "BBBB", "CCCC"], _c, 300.0, 8.0)
    kept, dropped = fetchem.collect(["AAAA", "BBBB", "CCCC"], _c, 300.0, 8.0,
                                    max_per_pub=1)
    both, _ = fetchem.collect(["AAAA", "BBBB"], _c, 300.0, 8.0, max_per_pub=2)
    unpub, _ = fetchem.collect(["DDDD", "EEEE"], _c, 300.0, 8.0, max_per_pub=1)
finally:
    fetchem.entry_metadata, fetchem.fetch_model, fetchem.fetch_map = (
        _real_meta, _real_model, _real_map)

# The default keeps everything: P5 and P6 both failed and a permutation test put
# within-cluster agreement at p = 0.38, so filtering by publication would discard
# real evidence from a benchmark that has too little of it.
check("by default no entry is dropped for sharing a publication",
      [e["pdb_id"] for e in default_all], ["AAAA", "BBBB", "CCCC"])
check("the limit still works when asked for explicitly",
      [e["pdb_id"] for e in kept], ["AAAA", "CCCC"])
check("and the skip says why, naming the publication",
      dropped[0]["reason"], "publication already represented (10.1/dup)")
check("the publication key is recorded on every kept entry",
      kept[0]["publication"], "10.1/dup")
check("--max-per-pub sets the cap when a cluster limit is wanted deliberately",
      len(both), 2)
# Unpublished entries must stay independent: keying them all to one empty string
# would collapse them into a single unit and drop every one but the first.
check("unpublished entries are independent, not merged",
      [e["pdb_id"] for e in unpub], ["DDDD", "EEEE"])


# --- Round 16: per-entry results must survive the cache ---------------------------

# Round 13 measured 6 entries, named 2, and wrote results only to a JSON in a
# temporary cache. Clearing it destroyed the other 4 entries' IDENTITIES, not just
# their values -- they cannot be re-run because nothing records what they were, so the
# CC_mask degradation count is permanently a range. append_results() is the fix.
_tsv_dir = Path(__import__("tempfile").mkdtemp())
_tsv = _tsv_dir / "deltas.tsv"


def _row(pid, delta, pct=None):
    return {"pdb_id": pid, "resolution": 3.2, "cc_mask_pre": 0.80,
            "cc_mask_post": round(0.80 + delta, 4), "cc_mask_delta": delta,
            "d_fsc_model_pre": 3.0, "d_fsc_model_post": 3.1,
            "d_fsc_model_delta_pct": pct}


refem.append_results([_row("AAAA", -0.03, 1.5)], [], _tsv)
_first = _tsv.read_text()
check("a header is written once", _first.splitlines()[0].split("\t")[0], "pdb_id")
check("the entry's delta is recorded", "-0.03" in _first, True)

# A second run appends rather than truncating -- the whole point is cumulative history.
refem.append_results([_row("BBBB", 0.01)], [{"pdb_id": "CCCC", "reason": "no restraints"}],
                     _tsv)
_second = _tsv.read_text()
check("a later run appends instead of replacing", "AAAA" in _second and "BBBB" in _second, True)
check("only one header line exists after two runs",
      sum(1 for l in _second.splitlines() if l.startswith("pdb_id")), 1)
check("a skipped entry is recorded with its reason, not omitted",
      "CCCC\t\t\t\t\t\t\t\t\tskipped: no restraints" in _second, True)

# Round 17: the round label. Without it, a cross-round analysis has to reconstruct
# which round measured what by matching prose in the audit trails against row order in
# the TSV -- which is the same "prose is not a record" failure one level up.
_r17 = _tsv_dir / "labelled.tsv"
refem.append_results([_row("EEEE", -0.01)], [{"pdb_id": "FFFF", "reason": "ligand"}],
                     _r17, "17")
_labelled = _r17.read_text()
check("the header carries the round column",
      _labelled.splitlines()[0].split("\t")[1], "round")
check("a measured row records which round measured it",
      _labelled.splitlines()[1].split("\t")[1], "17")
check("and so does a skipped one -- attrition is per-round evidence too",
      _labelled.splitlines()[2].split("\t")[1], "17")

# Re-running an entry must not duplicate it: the benchmark caches and re-runs freely,
# so without dedup the file would accumulate copies and inflate every count taken
# from it -- the same failure mode as counting entries instead of degradations.
refem.append_results([_row("AAAA", -0.03, 1.5), _row("DDDD", 0.02)], [], _tsv)
_third = _tsv.read_text()
check("an already-recorded entry is not duplicated",
      sum(1 for l in _third.splitlines() if l.startswith("AAAA")), 1)
check("while a genuinely new entry is still added", "DDDD" in _third, True)


# --- Round 16: screen out charged models before downloading a 300 MB map ----------

# cctbx's electron scattering table holds 98 NEUTRAL elements and no ions, so any
# formal charge aborts map_correlations. 10EN and 10FL both died there; every entry
# that processed cleanly carries no charges. PHENIX names only the anion, so anions
# are the confirmed fatal case and cations are reported but not refused.
# The model is built with gemmi's own API rather than hand-written: a minimal cif
# string parses without error but yields zero atoms, which would make the screen look
# like it passed when it never saw anything.
def _screen(charge: int):
    import gemmi
    st = gemmi.Structure()
    st.cell = gemmi.UnitCell(50, 50, 50, 90, 90, 90)
    st.spacegroup_hm = "P 1"
    model = gemmi.Model("1")
    chain = gemmi.Chain("A")
    residue = gemmi.Residue()
    residue.name, residue.seqid = "ALA", gemmi.SeqId("1")
    for name, element, chg in (("N", "N", charge), ("CA", "C", 0)):
        atom = gemmi.Atom()
        atom.name, atom.element = name, gemmi.Element(element)
        atom.charge, atom.occ, atom.b_iso = chg, 1.0, 20.0
        atom.pos = gemmi.Position(1.0, 2.0, 3.0)
        residue.add_atom(atom)
    chain.add_residue(residue)
    model.add_chain(chain)
    st.add_model(model)
    st.setup_entities()
    path = _tsv_dir / f"m_{charge}.cif"
    st.make_mmcif_document().write_file(str(path))
    return fetchem.charge_screen(path)


_neutral_reason, _neutral_counts = _screen(0)
_anion_reason, _anion_counts = _screen(-1)
_cation_reason, _cation_counts = _screen(1)

check("a neutral model passes the screen", _neutral_reason, None)
check("and reports no charges", _neutral_counts, {})

check("an anion is refused", _anion_reason is not None, True)
check("and the refusal names the type and count",
      _anion_reason, "formal charges absent from the electron scattering table: N1-×1")
check("the inventory records it", _anion_counts, {"N1-": 1})

# A cation alone is NOT refused: PHENIX named only the anion in both real failures, so
# whether cations abort on their own is untested. Refusing them would discard entries
# on an unverified rule, in a benchmark whose problem is too little evidence.
check("a cation alone is reported, not refused", _cation_reason, None)
check("but it is still recorded for a future round to test", _cation_counts, {"N1+": 1})

# --- Round 17: the ligand screen moves that skip off the expensive path -------------

# The three ligand skips in rounds 14-16 each cost a model download, a 200-300 MB map
# download and a `real_space_refine` attempt before failing. Whether a component has
# restraints is a property of the model alone, so the screen runs at fetch time.
#
# These are logic tests. The screen's *agreement with PHENIX* is not testable here --
# it needs the monomer libraries and real entries -- and was established separately
# against `phenix.pdb_interpretation` on 37 cached models with zero disagreements
# (`ref/research/tolerance_benchmark_round17.md`).

def _ligand_model(residue_name: str, n_atoms: int, hetero: bool = True):
    """A one-residue model carrying `residue_name`."""
    import gemmi
    st = gemmi.Structure()
    model, chain = gemmi.Model("1"), gemmi.Chain("A")
    residue = gemmi.Residue()
    residue.name = residue_name
    residue.seqid = gemmi.SeqId("1")
    residue.het_flag = "H" if hetero else "A"
    for i in range(n_atoms):
        atom = gemmi.Atom()
        atom.name = f"C{i}"
        atom.element = gemmi.Element("C")
        atom.pos = gemmi.Position(float(i), 0.0, 0.0)
        residue.add_atom(atom)
    chain.add_residue(residue)
    model.add_chain(chain)
    st.add_model(model)
    path = _tsv_dir / f"lig_{residue_name}.cif"
    st.make_mmcif_document().write_file(str(path))
    return fetchem.ligand_screen(path)


if fetchem._monomer_libraries() is None:
    print("SKIP  ligand screen: PHENIX monomer libraries not installed here")
else:
    check("a standard amino acid passes", _ligand_model("ALA", 5, hetero=False)[0], None)
    # The regression that motivates using gemmi's residue table rather than file
    # existence alone: DT, DA, DC and DG are in NEITHER library under those names, so a
    # bare file check flags every DNA chain -- 1431 atoms on 28JV instead of the 38
    # that actually failed.
    check("a DNA residue passes despite being absent from both libraries",
          _ligand_model("DT", 20, hetero=False)[0], None)
    check("a library ligand passes", _ligand_model("ATP", 31)[0], None)

    # The refusal case points the screen at empty stub libraries rather than picking a
    # code that happens to be missing: GeoStd ships ~44 000 components, so almost any
    # three-letter code exists, and a test keyed on one that does not would start
    # failing the day PHENIX adds it.
    _stub = Path(_tf.mkdtemp())
    (_stub / "geostd").mkdir()
    (_stub / "mon_lib").mkdir()
    _real_libs = fetchem._monomer_libraries
    fetchem._monomer_libraries = lambda: (_stub / "geostd", _stub / "mon_lib")
    try:
        _unk_reason, _unk_counts = _ligand_model("LIG", 7)
        check("a component in neither library is refused", _unk_reason is not None, True)
        check("and the refusal names the component and its atom count",
              _unk_reason, "unparameterised ligand: 7 atoms with no monomer-library "
                           "restraints (LIG×7)")
        check("the inventory records what was missing", _unk_counts, {"LIG": 7})
        # Standard residues are exempted by gemmi's table, not by the libraries, so
        # they still pass when the libraries hold nothing at all.
        check("a standard residue still passes with empty libraries",
              _ligand_model("ALA", 5, hetero=False)[0], None)
    finally:
        fetchem._monomer_libraries = _real_libs

    # The library RESOLUTION itself, not just the screen that consumes it. Every test
    # above monkeypatches `_monomer_libraries` wholesale, which is exactly why a broken
    # $PHENIX branch survived review once (#75): the escape hatch tested
    # `$PHENIX/lib/geostd` when the libraries live at
    # `$PHENIX/lib/python3*/site-packages/chem_data/geostd`, so it never matched and the
    # only working lookup was one hardcoded version in one home directory.
    _fake_phenix = Path(_tf.mkdtemp())
    _cd = _fake_phenix / "lib" / "python3.9" / "site-packages" / "chem_data"
    (_cd / "geostd").mkdir(parents=True)
    (_cd / "mon_lib").mkdir(parents=True)
    _saved_env = os.environ.get("PHENIX")
    _saved_glob = fetchem.CHEM_DATA_GLOB
    os.environ["PHENIX"] = str(_fake_phenix)
    fetchem.CHEM_DATA_GLOB = "phenix-does-not-exist/lib/python3*/site-packages/chem_data"
    try:
        _found = fetchem._monomer_libraries()
        check("$PHENIX locates the libraries when the home glob cannot",
              _found is not None and _found[0] == _cd / "geostd", True)
    finally:
        fetchem.CHEM_DATA_GLOB = _saved_glob
        if _saved_env is None:
            os.environ.pop("PHENIX", None)
        else:
            os.environ["PHENIX"] = _saved_env

    # A screen that cannot find the libraries must not refuse anything: dropping good
    # entries silently is worse than the download it would have saved.
    fetchem._monomer_libraries = lambda: None
    try:
        check("with no libraries installed the screen refuses nothing",
              _ligand_model("LIG", 7)[0], None)
    finally:
        fetchem._monomer_libraries = _real_libs

    check("a passing model reports an empty inventory",
          _ligand_model("ATP", 31)[1], {})


# --- Round 18: every benchmark commits the entry set it ran on ---------------------

# The round-17 audit found 7 of the registry's 20 `[benchmark]` rows quoting a figure
# from a set that could not be reconstructed, and the cause was systemic: the scripts
# took their entries from an uncommitted `--ids-file` or globbed a cache. These pin the
# recovered sets so a later edit cannot silently change what a tolerance was measured
# on. `scripts/validate.sh` separately gates that a set is DECLARED at all.
#
# The counts are the published denominators. Where a set is short of its denominator the
# script says so via SET_IS_COMPLETE = False, and that shortfall is asserted too --
# an incomplete set quietly promoted to complete is exactly the failure being guarded.

_SETS = {
    #  script                        published n   recovered   complete
    "bench_t05_bond_rmsd":          (17, 17, True),
    "bench_t05_restraint_library":  (17, 17, True),
    "bench_t05_clashscore_h":       (10, 10, True),
    "bench_t06_r_offset":           (15, 15, True),
    "bench_t13_wilson_b":           (24, 24, True),
    "bench_t17_ordered_core":       (5, 5, True),
    "bench_t14_flip_sets":          (17, 12, False),
    "bench_vs_deposited":           (17, 11, False),
    "bench_refinement_deltas":      (37, 16, False),
}

for _name, (_published, _recovered, _complete) in _SETS.items():
    _mod = load(_name)
    _set = _mod.DEFAULT_SET
    check(f"{_name}: set has the recovered size", len(_set), _recovered)
    check(f"{_name}: no duplicate ids", len(set(_set)), len(_set))
    check(f"{_name}: completeness is declared honestly", _mod.SET_IS_COMPLETE, _complete)
    if not _complete:
        # A partial set must say how far short it falls, in the script, where whoever
        # re-runs it will see it -- not only in an audit trail they may never open.
        check(f"{_name}: shortfall is stated", bool(getattr(_mod, "SET_SHORTFALL", "")), True)
        check(f"{_name}: shortfall names the denominator",
              str(_published) in _mod.SET_SHORTFALL, True)

# The L-test is the one benchmark whose set was never expressible: the script has no id
# argument at all, it reads whatever logs a prior Wilson B run left behind. It records
# what is known rather than pretending to a default.
_lt = load("bench_t13_l_test")
check("bench_t13_l_test: published denominator recorded", _lt.PUBLISHED_N, 27)
check("bench_t13_l_test: only the 5 named datasets are claimed", len(_lt.KNOWN_IDS), 5)
check("bench_t13_l_test: not claimed complete", _lt.SET_IS_COMPLETE, False)

# Two benchmarks are documented as sharing one set. If that stops being true the
# bond-angle row loses its only route to recovery, so it is asserted rather than trusted.
check("bond-length and restraint-library share one set",
      sorted(load("bench_t05_bond_rmsd").DEFAULT_SET),
      sorted(load("bench_t05_restraint_library").DEFAULT_SET))

# 9LK0 is in the flip-set benchmark and in neither sibling 17-model set. The audit found
# this by hand; pinning it stops a future round "tidying" the sets into one list.
check("the flip-set benchmark is not interchangeable with its siblings",
      "9LK0" in load("bench_t14_flip_sets").DEFAULT_SET
      and "9LK0" not in load("bench_t05_bond_rmsd").DEFAULT_SET, True)


# --- Round 18: fetch-stage attrition must outlive the cache too --------------------

# `em_refinement_deltas.tsv` records attrition from the refinement attempt onward, which
# is now the smaller half: both screens reject entries BEFORE any refinement, so their
# rejections were landing only in a JSON inside a temporary cache. Round 17 found four
# models in round 14's cache carrying an unparameterised ligand and appearing in no
# durable record at all.
_fetch_tsv = _tsv_dir / "fetch.tsv"
fetchem.append_fetch_record(
    [{"pdb_id": "1AAA", "resolution": 3.2, "emdb": "EMD-1", "publication": "10.1/x",
      "charges": {"N1+": 4}}],
    [{"pdb_id": "2BBB", "reason": "unparameterised ligand: 38 atoms",
      "unparameterised": {"VM6": 38}}],
    _fetch_tsv, "18")
_ft = _fetch_tsv.read_text()

check("a kept entry is recorded, not only the rejected ones",
      _ft.splitlines()[1].split("\t")[0], "1AAA")
check("and its outcome says so", _ft.splitlines()[1].split("\t")[4], "kept")
# The charge inventory is the specific thing round 16 said it was storing "so a future
# round can test it" and then stored in a file that does not survive the round.
check("the charge inventory survives the cache",
      _ft.splitlines()[1].split("\t")[5], "N1+×4")
check("a rejected entry keeps its reason",
      _ft.splitlines()[2].split("\t")[4],
      "rejected: unparameterised ligand: 38 atoms")
check("and what the screen actually saw", _ft.splitlines()[2].split("\t")[6], "VM6×38")
check("both rows carry the round", [l.split("\t")[1] for l in _ft.splitlines()[1:]],
      ["18", "18"])

# Same dedup contract as the refinement record: the fetcher is re-run freely, and
# duplicate rows would inflate any attrition count taken from the file.
fetchem.append_fetch_record([{"pdb_id": "1AAA", "resolution": 3.2}],
                            [{"pdb_id": "3CCC", "reason": "map too large"}],
                            _fetch_tsv, "18")
_ft2 = _fetch_tsv.read_text()
check("re-fetching an entry does not duplicate it",
      sum(1 for l in _ft2.splitlines() if l.startswith("1AAA")), 1)
check("while a new rejection is still added", "3CCC" in _ft2, True)
check("only one header after two runs",
      sum(1 for l in _ft2.splitlines() if l.startswith("pdb_id")), 1)

# A reason containing a tab or newline would silently shift every later column.
_cells = fetchem._cell("a\treason\nwith control chars")
check("a reason cannot break the column layout",
      "\t" not in _cells and "\n" not in _cells, True)


print(f"\nall bench tolerance unit tests passed ({PASSED} checks)")
