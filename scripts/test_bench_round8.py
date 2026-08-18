#!/usr/bin/env python3
"""Unit tests for the round-8 machinery (#295).

Pinned: the I2 patch invariant (observation bytes byte-identical through
the wavelength edit; the single-dataset id-0 case the canary caught; a
failed proof or missing go-ahead leaves the store untouched) and the
deposition-wavelength parser. Network-free."""
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


b8 = load("bench_round8")


def _make_store(durable: Path, lid: str, wl_cif: str | None):
    """A stripped-shape store MTZ (single dataset, id 0, wavelength 0.0)
    plus its deposition cif."""
    import gemmi
    import numpy as np
    m = gemmi.Mtz(with_base=False)
    m.spacegroup = gemmi.find_spacegroup_by_name("P 1")
    m.set_cell_for_all(gemmi.UnitCell(10, 10, 10, 90, 90, 90))
    m.add_dataset("stripped")          # id 0 — the case the canary caught
    for lab, typ in (("H", "H"), ("K", "H"), ("L", "H"),
                     ("FOBS", "F"), ("SIGFOBS", "Q")):
        m.add_column(lab, typ)
    rows = np.array([[h, 0, 0, 10.0 + h, 1.0] for h in range(1, 11)],
                    dtype=np.float32)
    m.set_data(rows)
    m.write_to_file(str(durable / f"{lid}.mtz"))
    cif = "data_x\n"
    if wl_cif is not None:
        cif += f"_diffrn_radiation_wavelength.wavelength   {wl_cif} \n"
    (durable / f"{lid}.cif").write_text(cif)


with tempfile.TemporaryDirectory() as _tmp:
    durable = Path(_tmp) / "store"
    work = Path(_tmp) / "work"
    durable.mkdir()
    work.mkdir()
    _make_store(durable, "zzzz", "0.9793")
    before = (durable / "zzzz.mtz").read_bytes()

    check("I2: deposition wavelength parses",
          b8.deposition_wavelength(durable / "zzzz.cif"), 0.9793)

    # proof-only: the candidate is proved, the store is untouched
    rec = b8.patch_entry("ZZZZ", durable, work, staged_wl=0.9793)
    check("I2: single id-0 dataset gets the wavelength (canary class)",
          rec["patched_wavelength"], 0.9793)
    check("I2: observation fingerprints survive the edit",
          rec["fingerprints_identical"], True)
    check("I2: staged cross-check agrees inside 1e-3",
          rec["staged_crosscheck"]["agrees"], True)
    check("I2: passing proof without go-ahead does not write",
          rec["status"], "proof_ok_awaiting_user_go_ahead")
    check("I2:   store byte-identical",
          (durable / "zzzz.mtz").read_bytes() == before, True)

    # a placeholder staged value is a named divergence, not agreement
    rec2 = b8.patch_entry("ZZZZ", durable, work, staged_wl=1.0)
    check("I2: placeholder staged value diverges",
          rec2["staged_crosscheck"]["agrees"], False)
    check("I2:   but the deposition value still proves",
          rec2["status"], "proof_ok_awaiting_user_go_ahead")

    # no deposition wavelength -> named refusal
    _make_store(durable, "yyyy", None)
    rec3 = b8.patch_entry("YYYY", durable, work, staged_wl=0.9)
    check("I2: missing deposition wavelength is a named refusal",
          rec3["status"], "no_deposition_wavelength_store_untouched")

    # write=True with a passing proof replaces and re-baselines
    rec4 = b8.patch_entry("ZZZZ", durable, work, staged_wl=0.9793, write=True)
    check("I2: write=True patches", rec4["status"], "patched")
    import gemmi as _g
    check("I2:   store wavelength restored",
          round(_g.read_mtz_file(str(durable / "zzzz.mtz"))
                .datasets[-1].wavelength, 4), 0.9793)
    check("I2:   sidecar re-baseline cites the ruling",
          "I2" in rec4["rebaseline_ruling"], True)
    check("I2:   observation bytes identical through the write",
          b8._b6.obs_fingerprint(durable / "zzzz.mtz")
          == b8._b6.obs_fingerprint(work / "patched_zzzz.mtz"), True)

print(f"\n{PASSED} checks passed")
