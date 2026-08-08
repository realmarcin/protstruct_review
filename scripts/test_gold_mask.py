#!/usr/bin/env python3
"""Unit tests for the phase-1 mask builder (#295).

The mask decides which residues the negative-control bench scores and which
deposited outliers are protected, so a rule defect silently reshapes every
verdict downstream. Pinned hardest: the ordering finding from #298 — protection
applies AFTER masking, so a deposited outlier on a masked residue is masked, not
protected. Also pinned: altloc-row merging (a residue with two conformers is one
residue, aggregated worst-case), water exclusion, and the relative B tail.

Network-free and gemmi-free: rows come from an inline XML string, lattice keys
are injected into classify().
"""
from __future__ import annotations

import importlib.util
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PASSED = 0


def load():
    spec = importlib.util.spec_from_file_location(
        "gold_mask", REPO / "scripts" / "gold_mask.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["gold_mask"] = module
    spec.loader.exec_module(module)
    return module


def check(label: str, got, want) -> None:
    global PASSED
    if got != want:
        print(f"FAIL  {label}: got {got!r}, want {want!r}")
        sys.exit(1)
    PASSED += 1
    print(f"PASS  {label} (got {got!r})")


gm = load()

XML = """<?xml version="1.0"?>
<wwPDB-validation-information>
 <Entry attempted_validation_steps="x"/>
 <ModelledSubgroup chain="A" resnum="1" icode=" " resname="MET" altcode=" "
   rsrz="0.1" owab="10.0" rama="Favored" rota="m-10"/>
 <ModelledSubgroup chain="A" resnum="2" icode=" " resname="VAL" altcode="A"
   rsrz="0.5" owab="12.0" rama="Favored" rota="t"/>
 <ModelledSubgroup chain="A" resnum="2" icode=" " resname="VAL" altcode="B"
   rsrz="-3.1" owab="30.0" rama="Favored" rota="t"/>
 <ModelledSubgroup chain="A" resnum="3" icode=" " resname="ARG" altcode=" "
   rsrz="0.2" owab="11.0" rama="Favored" rota="OUTLIER"/>
 <ModelledSubgroup chain="A" resnum="4" icode=" " resname="GLY" altcode=" "
   rsrz="2.5" owab="10.0" rama="OUTLIER" rota="gly"/>
 <ModelledSubgroup chain="A" resnum="5" icode=" " resname="LEU" altcode=" "
   rsrz="0.3" owab="50.0" rama="Favored" rota="mt"/>
 <ModelledSubgroup chain="A" resnum="6" icode=" " resname="PHE" altcode=" "
   rsrz="0.0" owab="10.5" rama="Favored" rota="m-80">
   <clash cid="1" clashmag="0.6" dist="2.1"/>
 </ModelledSubgroup>
 <ModelledSubgroup chain="A" resnum="7" icode=" " resname="ASP" altcode=" "
   rsrz="0.1" owab="10.2" rama="Favored" rota="t70"/>
 <ModelledSubgroup chain="S" resnum="101" icode=" " resname="HOH" altcode=" "
   rsrz="4.0" owab="90.0"/>
</wwPDB-validation-information>
"""

with tempfile.NamedTemporaryFile("w", suffix=".xml", delete=False) as f:
    f.write(XML)
    xml_path = Path(f.name)

rows = gm.parse_residue_rows(xml_path)
xml_path.unlink()

check("water excluded from the universe",
      any(r["resname"] == "HOH" for r in rows), False)
check("one row per altloc before merging",
      sum(1 for r in rows if r["resnum"] == 2), 2)

residues = gm.merge_rows(rows)
check("altloc rows merge to one residue", len(residues), 7)

r2 = residues[("A", 2, "")]
check("merged residue is flagged altconf", r2["altconf"], True)
check("merged rsrz is the worst |value|", r2["rsrz"], -3.1)
check("merged owab is the max", r2["owab"], 30.0)

# median owab over merged residues: [10.0, 30.0, 11.0, 10.0, 50.0, 10.5, 10.2]
# -> median 10.5, B cut = 21.0; residue 5 (owab 50) is the tail. Residue 2 (30.0)
# is also above the cut but already altconf-masked — reasons accumulate.
classified = gm.classify(residues, lattice={("A", 7, "")})

check("clean residue unmasked, unprotected",
      classified[("A", 1, "")], {"resname": "MET", "masked": [],
                                 "protected": []})
check("altconf residue masked with both applicable reasons",
      classified[("A", 2, "")]["masked"], ["altconf", "rsrz_outlier", "high_b"])
check("rota outlier on a clean residue is PROTECTED",
      classified[("A", 3, "")]["protected"], ["rota_outlier"])
check("rama outlier on an RSRZ-outlier residue is MASKED, not protected (#298)",
      classified[("A", 4, "")], {"resname": "GLY", "masked": ["rsrz_outlier"],
                                 "protected": []})
check("relative B tail masks the high-B residue",
      classified[("A", 5, "")]["masked"], ["high_b"])
check("clash on a clean residue is protected",
      classified[("A", 6, "")]["protected"], ["clash"])
check("injected lattice key is masked",
      classified[("A", 7, "")]["masked"], ["lattice_contact"])

# Threshold sensitivity is a re-run, not a rewrite: loosening the B factor to 5x
# unmasks residue 5 (50 < 5 x 10.5).
loose = gm.classify(residues, lattice=set(), b_tail_factor=5.0)
check("B tail factor is a parameter", loose[("A", 5, "")]["masked"], [])

# Density coverage is recorded, not inferred (#306): full here, and zero when the
# report carries no EDS data — the case where the density rules go inert.
check("full density coverage recorded",
      gm.density_coverage(residues), {"rsrz": 1.0, "owab": 1.0})
no_eds = {k: dict(r, rsrz=None, owab=None) for k, r in residues.items()}
check("EDS-absent coverage is zero, recorded (#306)",
      gm.density_coverage(no_eds), {"rsrz": 0.0, "owab": 0.0})

print(f"\n{PASSED} checks passed")
