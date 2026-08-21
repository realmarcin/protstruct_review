#!/usr/bin/env python3
"""Unit tests for the round-7 machinery (#295).

Pinned: the H3 repair's rename-only invariant (only anisotrop rows whose
atom is CSO and whose comp says CYS are touched; genuine CYS rows and all
numeric values survive), and the H4 proof gate (a fingerprint mismatch or a
zero wavelength leaves the store untouched; a passing proof without the
user's go-ahead still leaves the store untouched). Network-free: the gate
tests pre-populate the staging cache so fetch_pair returns it."""
from __future__ import annotations

import importlib.util
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PASSED = 0


def load(name):
    spec = importlib.util.spec_from_file_location(
        name, REPO / "scripts" / f"{name}.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


def check(label, got, want):
    global PASSED
    if got != want:
        print(f"FAIL  {label}: got {got!r}, want {want!r}")
        sys.exit(1)
    PASSED += 1
    print(f"PASS  {label}")


b7 = load("bench_round7")

# --- H3: the rename-only invariant --------------------------------------------------

_SYNTH_CIF = """\
data_synth
loop_
_atom_site.group_PDB
_atom_site.id
_atom_site.type_symbol
_atom_site.label_atom_id
_atom_site.label_comp_id
_atom_site.label_asym_id
_atom_site.label_seq_id
_atom_site.Cartn_x
_atom_site.Cartn_y
_atom_site.Cartn_z
_atom_site.occupancy
_atom_site.B_iso_or_equiv
ATOM 1 S SG CSO A 9 1.0 2.0 3.0 1.00 10.5
ATOM 2 S SG CYS A 12 4.0 5.0 6.0 1.00 11.5
loop_
_atom_site_anisotrop.id
_atom_site_anisotrop.pdbx_label_comp_id
_atom_site_anisotrop.U[1][1]
_atom_site_anisotrop.U[2][2]
_atom_site_anisotrop.U[3][3]
1 CYS 0.11 0.22 0.33
2 CYS 0.44 0.55 0.66
"""

with tempfile.TemporaryDirectory() as _tmp:
    src = Path(_tmp) / "synth.cif"
    out = Path(_tmp) / "synth_fix.cif"
    src.write_text(_SYNTH_CIF)
    rep = b7.repair_9ygw(src, out)
    check("H3: exactly the CSO atom's mislabeled row renamed",
          rep["n_anisotrop_rows_renamed"], 1)
    check("H3: the CSO atom-site census", rep["n_cso_atom_sites"], 1)
    from gemmi import cif as _cif
    blk = _cif.read(str(out)).sole_block()
    aniso = {r[0]: (r[1], r[2]) for r in blk.find(
        "_atom_site_anisotrop.", ["id", "pdbx_label_comp_id", "U[1][1]"])}
    check("H3: renamed row says CSO with its tensor untouched",
          aniso["1"], ("CSO", "0.11"))
    check("H3: the genuine CYS row is NOT renamed",
          aniso["2"], ("CYS", "0.44"))
    xyz = [(r[0], r[1]) for r in blk.find("_atom_site.", ["id", "Cartn_x"])]
    check("H3: coordinates survive byte-for-byte",
          xyz, [("1", "1.0"), ("2", "4.0")])

# On the REAL 9YGW file the registered rename matches ZERO rows — the
# deposited anisotrop block is internally consistent (CYS-altA/CSO-altB
# microheterogeneity); that result is round-7 data, recorded in the round
# record, not pinned here.

# --- H4: the proof gate -------------------------------------------------------------


def _make_mtz(path: Path, fobs_seed: float, wavelength: float):
    import gemmi
    import numpy as np
    m = gemmi.Mtz(with_base=True)
    m.spacegroup = gemmi.find_spacegroup_by_name("P 1")
    m.set_cell_for_all(gemmi.UnitCell(10, 10, 10, 90, 90, 90))
    ds = m.add_dataset("d")
    ds.wavelength = wavelength
    for lab, typ in (("FOBS", "F"), ("SIGFOBS", "Q")):
        m.add_column(lab, typ)
    rows = np.array([[h, 0, 0, fobs_seed + h, 1.0] for h in range(1, 11)],
                    dtype=np.float32)
    m.set_data(rows)
    m.write_to_file(str(path))


with tempfile.TemporaryDirectory() as _tmp:
    durable = Path(_tmp) / "store"
    staging = Path(_tmp) / "staging"
    durable.mkdir()
    staging.mkdir()
    _make_mtz(durable / "zzzz.mtz", 100.0, 0.0)
    (staging / "zzzz.pdb").write_text("CRYST1\n")   # fetch_pair cache hit

    # mismatched staged data -> proof fails, store byte-identical after
    _make_mtz(staging / "zzzz.mtz", 200.0, 0.98)
    before = (durable / "zzzz.mtz").read_bytes()
    rec = b7.remediate_entry("ZZZZ", durable, staging)
    check("H4: fingerprint mismatch fails the proof",
          rec["status"], "proof_failed_store_untouched")
    check("H4:   and names the mismatched column",
          rec["mismatched_columns"], ["FOBS"])
    check("H4:   and the store is untouched",
          (durable / "zzzz.mtz").read_bytes() == before, True)

    # identical data, restored wavelength -> proof passes but write=False
    # STILL leaves the store alone (the user's go-ahead is a separate gate)
    _make_mtz(staging / "zzzz.mtz", 100.0, 0.98)
    rec = b7.remediate_entry("ZZZZ", durable, staging)
    check("H4: passing proof without go-ahead does not write",
          rec["status"], "proof_ok_awaiting_user_go_ahead")
    check("H4:   store still byte-identical",
          (durable / "zzzz.mtz").read_bytes() == before, True)
    check("H4:   no sidecar appears",
          (durable / "zzzz.mtz.sha256").exists(), False)

    # identical data, zero wavelength -> named refusal
    _make_mtz(staging / "zzzz.mtz", 100.0, 0.0)
    rec = b7.remediate_entry("ZZZZ", durable, staging)
    check("H4: zero wavelength is a named refusal",
          rec["status"], "wavelength_still_zero_store_untouched")

    # write=True with a passing proof replaces and re-baselines
    _make_mtz(staging / "zzzz.mtz", 100.0, 0.98)
    rec = b7.remediate_entry("ZZZZ", durable, staging, write=True)
    check("H4: write=True remediates", rec["status"], "remediated")
    check("H4:   sidecar re-baseline cites the ruling",
          "H4" in rec["rebaseline_ruling"], True)
    import gemmi as _g
    check("H4:   store wavelength restored",
          round(_g.read_mtz_file(str(durable / "zzzz.mtz"))
                .datasets[-1].wavelength, 2), 0.98)

# --- #369: the flag-diff diagnosis's NaN and asymmetry behavior ---------------------


def _make_flag_mtz(path: Path, flags):
    import gemmi
    import numpy as np
    m = gemmi.Mtz(with_base=True)
    m.spacegroup = gemmi.find_spacegroup_by_name("P 1")
    m.set_cell_for_all(gemmi.UnitCell(10, 10, 10, 90, 90, 90))
    m.add_dataset("d")
    for lab, typ in (("FOBS", "F"), ("SIGFOBS", "Q"), ("R-free-flags", "I")):
        m.add_column(lab, typ)
    # rows: h, k, l, FOBS, SIGFOBS, flag — FOBS is NaN on rows 3 and 4
    rows = []
    for h in range(1, 6):
        fobs = float("nan") if h >= 3 else 10.0 + h
        rows.append([h, 0, 0, fobs, 1.0, flags[h - 1]])
    m.set_data(np.array(rows, dtype=np.float32))
    m.write_to_file(str(path))


with tempfile.TemporaryDirectory() as _tmp:
    nan = float("nan")
    a = Path(_tmp) / "a.mtz"
    b = Path(_tmp) / "b.mtz"
    # rows 1,2 measured and identical; row 3 unmeasured and differing;
    # rows 4,5: flag NaN in BOTH files (4) and flag differing on a measured
    # row is impossible here (5 identical) — so n_differing must be exactly 1
    _make_flag_mtz(a, [0.0, 1.0, 1.0, nan, 1.0])
    _make_flag_mtz(b, [0.0, 1.0, 0.0, nan, 1.0])
    diag = b7._diagnose_flag_diff(a, b, ["R-free-flags"])
    check("#369: both-NaN positions are identical, not differing",
          diag["R-free-flags"]["n_differing"], 1)
    check("#369:   and the one real diff sits on the unmeasured row",
          diag["R-free-flags"]["n_differing_on_unmeasured"], 1)
    diag2 = b7._diagnose_flag_diff(a, b, ["R-free-flags-9"])
    check("#369: a column absent from both joins is named, not a crash",
          "asymmetry" in diag2["R-free-flags-9"], True)

print(f"\n{PASSED} checks passed")
