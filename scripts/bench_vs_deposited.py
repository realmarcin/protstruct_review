#!/usr/bin/env python3
"""Benchmark four tolerances against the wwPDB validation report in one pass.

Settles, from `ref/thresholds_and_standards.md`:
  - Ramachandran outlier %   ± 0.5 pp
  - Rotamer outlier %        ± 0.5 pp
  - R-free vs deposited      |Δ| ≤ 0.02
  - Completeness (overall)   ± 1 pp vs deposition

The reference is the **wwPDB validation report**, which the harness's trust model
already names as the tiebreaker. Two endpoints are used per entry:

  - `https://www.ebi.ac.uk/pdbe/entry-files/download/<id>_validation.xml`
    → `DataCompleteness`, `PDB-Rfree` (deposited), `DCC_Rfree` (wwPDB-recomputed),
      `clashscore`, and the **per-residue `rama=`/`rota=` verdicts** from which the
      Ramachandran/rotamer favored and OUTLIER percentages are counted
  - `https://www.ebi.ac.uk/pdbe/api/validation/key_validation_stats/entry/<id>`
    → `protein_ramachandran` / `protein_sidechains` percentages, retained only as
      `*_api_pct` cross-checks. These are NOT the outlier reference: `protein_sidechains`
      is a broader sidechain metric inconsistent with the per-residue rotamer verdicts
      (#281), so the outlier % is counted from the XML verdicts, consistent with favored %.

This is a **pipeline** comparison, not a method-independent one: wwPDB's geometry
percentages are MolProbity-derived, as are PHENIX's. What it tests is whether a local
run reproduces the deposited reference — which is what the tolerances actually claim.

Completeness note: the PDBe *experiment* API exposes a `completeness` field but it was
null for all 10 entries checked, so the value is taken from the validation XML instead.

Usage:
    python3 scripts/bench_vs_deposited.py 1ABC 2DEF --cache DIR --json out.json
    python3 scripts/bench_vs_deposited.py --ids-file ids.json --cache DIR
"""
from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
from toolchain import phenix, run_logged

RCSB_PDB = "https://files.rcsb.org/download/{pdb_id}.pdb"
VALIDATION_XML = "https://www.ebi.ac.uk/pdbe/entry-files/download/{pdb_id}_validation.xml"
KEY_STATS = "https://www.ebi.ac.uk/pdbe/api/validation/key_validation_stats/entry/{pdb_id}"
_RAMA_OUT = re.compile(r"SUMMARY:\s*([\d.]+)%\s*outliers")
_RAMA_FAV = re.compile(r"SUMMARY:\s*([\d.]+)%\s*favored")
_ROTA_OUT = re.compile(r"SUMMARY:\s*([\d.]+)%\s*outliers")
_ROTA_FAV = re.compile(r"SUMMARY:\s*([\d.]+)%\s*favored")
_MVD_RFREE = re.compile(r"^\s*r_free:\s*([\d.]+)\s*$", re.M)
_MVD_COMPLETENESS = re.compile(r"Completeness in resolution range:\s*([\d.]+)")
# Per-residue verdicts in the validation report. There is no entry-level "favored %"
# attribute — only outlier counts — so the Ramachandran favored fraction is counted
# from `rama="Favored|Allowed|OUTLIER"`. The rotamer attribute is a HYBRID: for a
# non-outlier residue it names the rotamer (`rota="m-10"`, `rota="mp"`), but for a
# rotamer outlier it carries the literal verdict `rota="OUTLIER"`. So the rotamer
# *favored* % is unobtainable (no Favored/Allowed classification exists), but the
# rotamer *outlier* % IS — count `rota="OUTLIER"` over all rota residues. This is the
# report's own per-residue verdict, and it is what `phenix.rotalyze` reproduces. It is
# NOT the same as `key_validation_stats`' `protein_sidechains.percent_outliers`, which
# is a broader sidechain metric (see #281): on 6LE5 the per-residue XML marks 9/1763
# rotamer outliers (0.51 %, matching rotalyze) where the API reports 59 (3.35 %).
_RES_RAMA = re.compile(r'\brama="([^"]+)"')
_RES_ROTA = re.compile(r'\brota="([^"]+)"')
# Per-residue rotamer assignment from the report, with enough identity to match it
# against a local run: <ModelledSubgroup ... rota="mmm" ... chain="A" resnum="1" ...
# resname="MET" ...>. Attribute order is not guaranteed, so each is matched separately.
_XML_SUBGROUP = re.compile(r"<ModelledSubgroup ([^>]*)>")
# MolProbity's rotamer classification cutoffs on the library score (%):
#   score < 0.3   OUTLIER
#   0.3 - 2.0     Allowed
#   > 2.0         Favored
# The wwPDB report exposes no rotamer score, so the favored/allowed *classification*
# cannot be compared across pipelines. What can be measured is the exposure: how many
# residues sit close enough to the 2.0 % cutoff that a small scoring difference would
# move them across it, which bounds how far favored % could disagree.
ROTAMER_FAVORED_CUTOFF = 2.0

# phenix.rotalyze per-residue line:  A   1  MET:1.00:79.0:...:Favored:mmm
_ROTALYZE_RESIDUE = re.compile(
    r"^\s*(?P<chain>\S+)\s+(?P<resseq>-?\d+)(?P<icode>[A-Za-z]?)\s+(?P<resname>[A-Z]{3}):"
    r"(?P<occ>[\d.]+):(?P<score>[\d.]+):"
    r"(?P<rest>.*?):(?P<verdict>Favored|Allowed|OUTLIER):(?P<rotamer>\S+)\s*$", re.M)


def entry_attribute(xml: str, name: str) -> float | None:
    """Read one attribute of the report's <Entry> tag, by *exact* name.

    The attribute names are hyphenated and heavily prefixed — `DCC_Rfree`,
    `absolute-percentile-DCC_Rfree`, `high-resol-relative-percentile-DCC_Rfree` — and a
    `(\\w+)="..."` scan matches the *tail* of the prefixed ones, silently returning a
    percentile (1.36) where an R-free (0.2358) was wanted. Anchor on a non-name
    character before the attribute so only the exact name matches.
    """
    match = re.search(r'(?:^|[\s])' + re.escape(name) + r'="([^"]*)"', xml)
    if not match:
        return None
    try:
        return float(match.group(1))
    except ValueError:
        return None


def favored_pct(xml: str, pattern: re.Pattern) -> float | None:
    """Percentage of residues the report calls "Favored", counted per residue.

    `key_validation_stats` exposes outlier counts only, which is why the favored
    tolerance went unmeasured; the report XML carries a per-residue verdict instead.
    Verified against `phenix.ramalyze` on 12LO: 53 Favored + 1 Allowed = 54 → 98.15 %,
    exactly the SUMMARY line.
    """
    verdicts = pattern.findall(xml)
    if not verdicts:
        return None
    # Only count a real verdict vocabulary. The rotamer attribute holds rotamer NAMES
    # ("m-10", "mp"), and counting those would return a confident 0.0 % favored — a
    # number indistinguishable from a measurement. Require the values to look like
    # verdicts before believing them.
    vocabulary = {"favored", "allowed", "outlier"}
    if not {v.lower() for v in verdicts} & vocabulary:
        return None
    favored = sum(1 for v in verdicts if v.lower() == "favored")
    return round(100.0 * favored / len(verdicts), 2)


def outlier_pct(xml: str, pattern: re.Pattern) -> float | None:
    """Percentage of residues the report calls "OUTLIER", counted per residue.

    The wwPDB reference for the outlier tolerances (Ramachandran and rotamer). Counted
    from the report's own per-residue `rama=`/`rota=` verdicts — the same source as
    `favored_pct` — NOT from `key_validation_stats`' `percent_outliers`, whose
    `protein_sidechains` figure is a broader sidechain metric inconsistent with the
    per-residue rotamer verdicts (see #281). Verified against `phenix.rotalyze` on 6LE5:
    9 `rota="OUTLIER"` of 1763 residues = 0.51 %, exactly the SUMMARY line, where the API
    reports 3.35 %.
    """
    verdicts = pattern.findall(xml)
    if not verdicts:
        return None
    # Unlike favored_pct, no favored/allowed-vocabulary guard: "OUTLIER" is an
    # unambiguous literal (rotamer names like "m-10" are never "OUTLIER"), so counting it
    # is safe even on rota=, where non-outlier residues carry names. A zero-outlier entry
    # has only names — the correct answer is then 0.0 %, not "unmeasured", so the guard
    # must NOT trip on the absence of the "outlier" token. Denominator is every residue
    # with the attribute; numerator is the OUTLIER count.
    outliers = sum(1 for v in verdicts if v.lower() == "outlier")
    return round(100.0 * outliers / len(verdicts), 2)


def report_rotamers(xml: str) -> dict[tuple[str, int, str], str]:
    """Per-residue rotamer NAME from the validation report, keyed by residue."""
    out = {}
    for block in _XML_SUBGROUP.findall(xml):
        attrs = dict(re.findall(r'([\w-]+)="([^"]*)"', block))
        rota, chain, resnum = attrs.get("rota"), attrs.get("chain"), attrs.get("resnum")
        if not rota or not chain or resnum is None:
            continue
        icode = attrs.get("icode", "").strip()
        try:
            out[(chain, int(resnum), icode, attrs.get("resname", "").upper())] = rota
        except ValueError:
            continue
    return out


def local_rotamers(rotalyze_log: str) -> dict[tuple[str, int, str, str], tuple[str, str]]:
    """Per-residue (rotamer name, verdict) from a phenix.rotalyze log."""
    out = {}
    for m in _ROTALYZE_RESIDUE.finditer(rotalyze_log):
        key = (m.group("chain"), int(m.group("resseq")), m.group("icode").strip(),
               m.group("resname").upper())
        out[key] = (m.group("rotamer"), m.group("verdict"))
    return out


def boundary_exposure(rotalyze_log: str, margins=(1.25, 1.5, 2.0)) -> dict[str, Any]:
    """How many residues sit near the Favored/Allowed cutoff, by score ratio.

    A residue is "exposed" at margin m if its library score lies between
    cutoff/m and cutoff*m — i.e. a scoring discrepancy of up to a factor m between
    two implementations could move it across the boundary. Since favored % is just a
    count, the exposed fraction is the worst-case pp by which two pipelines could
    disagree on it, and it is the only handle available: the wwPDB report publishes
    no rotamer score to compare against directly.
    """
    scores = [float(m.group("score")) for m in _ROTALYZE_RESIDUE.finditer(rotalyze_log)]
    if not scores:
        return {}
    out: dict[str, Any] = {"n_scored": len(scores)}
    for margin in margins:
        low, high = ROTAMER_FAVORED_CUTOFF / margin, ROTAMER_FAVORED_CUTOFF * margin
        exposed = sum(1 for s in scores if low <= s <= high)
        out[f"exposed_x{margin}"] = exposed
        out[f"exposed_pct_x{margin}"] = round(100.0 * exposed / len(scores), 2)
    return out


# chi1 atom quadruple is N-CA-CB-X, where X depends on the residue type.
_CHI1_LAST_ATOM = {
    "ARG": "CG", "ASN": "CG", "ASP": "CG", "CYS": "SG", "GLN": "CG", "GLU": "CG",
    "HIS": "CG", "ILE": "CG1", "LEU": "CG", "LYS": "CG", "MET": "CG", "PHE": "CG",
    "PRO": "CG", "SER": "OG", "THR": "OG1", "TRP": "CG", "TYR": "CG", "VAL": "CG1",
}


def chi1_agreement(model: Path, rotalyze_log: str) -> dict[str, Any]:
    """Compare chi1 computed independently (gemmi) against phenix.rotalyze's value.

    The favored/allowed classification is a library lookup applied to chi angles.
    The library cannot be checked — no non-cctbx rotamer library is installed — but
    the *geometry* half can, with gemmi. If chi agrees exactly, any favored-%
    disagreement between pipelines must come from the library, which narrows the
    unverified surface from "the classification" to "the density lookup".
    """
    import math

    import gemmi

    structure = gemmi.read_structure(str(model))
    structure.remove_alternative_conformations()
    structure.remove_hydrogens()
    mine: dict[tuple[str, int, str], float] = {}
    for chain in structure[0]:
        for residue in chain:
            last = _CHI1_LAST_ATOM.get(residue.name)
            if not last:
                continue
            try:
                positions = [residue[name][0].pos for name in ("N", "CA", "CB", last)]
            except Exception:                      # noqa: BLE001 - missing atom
                continue
            angle = gemmi.calculate_dihedral(*positions) * 180.0 / math.pi
            mine[(chain.name, residue.seqid.num, residue.name)] = angle % 360.0

    theirs: dict[tuple[str, int, str], float] = {}
    for m in _ROTALYZE_RESIDUE.finditer(rotalyze_log):
        chi1 = m.group("rest").split(":")[0]
        try:
            theirs[(m.group("chain"), int(m.group("resseq")),
                    m.group("resname").upper())] = float(chi1) % 360.0
        except ValueError:
            continue

    shared = sorted(set(mine) & set(theirs))
    if not shared:
        return {}
    diffs = [min(abs(mine[k] - theirs[k]), 360.0 - abs(mine[k] - theirs[k])) for k in shared]
    return {
        "n_chi1_compared": len(shared),
        "chi1_max_abs_deg": round(max(diffs), 4),
        "chi1_median_abs_deg": round(statistics.median(diffs), 4),
        "n_chi1_above_0_1_deg": sum(1 for d in diffs if d > 0.1),
    }


# gemmi rmsz per-torsion line: "A 7(LEU) torsion CA-CB-CG-CD1: |Z|=3.8"
_GEMMI_TORSION = re.compile(
    r"^(?P<chain>\S+)\s+(?P<resseq>-?\d+)\((?P<resname>[A-Z]{3})\)\s+torsion\s+"
    r"(?P<atoms>\S+):\s*\|Z\|=(?P<z>[\d.]+)")
# Backbone torsions involve atoms of two residues; sidechain chi torsions do not.
_BACKBONE_TORSIONS = {"C-N-CA-C", "CA-C-N-CA", "N-CA-C-N", "CA-C-N-H", "O-C-N-CA"}


def sidechain_torsion_z(model: Path) -> dict[tuple[str, int, str], float]:
    """Max sidechain chi torsion |Z| per residue, from the CCP4 monomer library.

    This is the one genuinely independent opinion available on sidechain
    conformation. `phenix.rotalyze` classifies against MolProbity's Top8000 density
    library; `gemmi rmsz` scores chi torsions against the CCP4 monomer library's own
    targets (e.g. `LEU chi1 N CA CB CG -60.000 10.0 3` — target, sigma, periodicity).
    Different data, not merely different code, which is what the rotamer question has
    lacked.
    """
    log = model.with_suffix(".rmsz.log")
    if not log.exists() or "torsion" not in log.read_text(errors="ignore"):
        run_logged(
            ["gemmi", "rmsz", "--cutoff=0", model], log, timeout=3600, ccp4=True
        )
    if not log.exists():
        return {}
    worst: dict[tuple[str, int, str], float] = {}
    for line in log.read_text(errors="ignore").splitlines():
        m = _GEMMI_TORSION.match(line.strip())
        if not m or m.group("atoms") in _BACKBONE_TORSIONS:
            continue
        key = (m.group("chain"), int(m.group("resseq")), m.group("resname").upper())
        worst[key] = max(worst.get(key, 0.0), float(m.group("z")))
    return worst


def cross_library_sidechain(model: Path, rotalyze_log: str) -> dict[str, Any]:
    """Do MolProbity and the CCP4 monomer library agree on unusual sidechains?"""
    import statistics as st

    z_by_res = sidechain_torsion_z(model)
    verdicts = local_rotamers(rotalyze_log)
    shared = sorted(set(z_by_res) & set(verdicts))
    if not shared:
        return {}
    groups: dict[str, list[float]] = {}
    for key in shared:
        groups.setdefault(verdicts[key][1], []).append(z_by_res[key])
    out: dict[str, Any] = {"n_sidechains_compared": len(shared)}
    for verdict, values in groups.items():
        out[f"median_torsion_z_{verdict.lower()}"] = round(st.median(values), 3)
        out[f"n_{verdict.lower()}"] = len(values)
    return out


def rotamer_agreement(xml: str, rotalyze_log: str) -> dict[str, Any]:
    """Do the two pipelines assign the same rotamer to the same residue?

    The favored-% tolerance itself cannot be measured against the wwPDB report — the
    report carries no favored/allowed verdict. But it does carry the rotamer NAME,
    in the same MolProbity vocabulary phenix.rotalyze uses, and the favored/allowed
    classification is derived from that assignment. Agreement on the assignment is
    therefore the strongest available evidence for the tolerance.
    """
    ref, local = report_rotamers(xml), local_rotamers(rotalyze_log)
    shared = sorted(set(ref) & set(local))
    if not shared:
        return {"n_shared": 0}
    same = [k for k in shared if ref[k] == local[k][0]]
    # The OUTLIER verdict is what the outlier tolerance concerns, and it agrees whenever
    # `rota="OUTLIER"` (report) matches the phenix verdict. A name mismatch where BOTH call
    # the residue non-outlier (report "t0" vs phenix "Cg_exo", both Favored) is a finer
    # rotamer-assignment nuance, not an outlier disagreement — so each disagreement carries
    # the phenix verdict to show it.
    disagree = [{"residue": list(k), "report": ref[k], "phenix": local[k][0],
                 "phenix_verdict": local[k][1]}
                for k in shared if ref[k] != local[k][0]]
    return {
        "n_shared": len(shared),
        "n_same_rotamer": len(same),
        "rotamer_agreement": round(len(same) / len(shared), 4),
        "name_disagreements": disagree,
        "local_favored_pct": round(
            100.0 * sum(1 for k in shared if local[k][1] == "Favored") / len(shared), 2),
    }


# phenix.ramalyze per-residue line:  A   8 BLEU:9.82:-83.73:98.71:Favored:General
# The resname field may carry a leading altloc code ("BLEU" = altloc B, LEU), so the
# 3-letter name is its last three characters. An insertion code is a letter suffix on the
# residue number ("100A HIS"); it MUST be captured, or the line fails to match and the
# residue is silently dropped — and residues that share a resnum across icodes then collide
# when keyed without it (#284 review).
_RAMALYZE_RESIDUE = re.compile(
    r"^\s*(?P<chain>\S+)\s+(?P<resseq>-?\d+)(?P<icode>[A-Za-z]?)\s+(?P<resname>.{3,4}):"
    r"[\d.]+:[-\d.]+:[-\d.]+:(?P<verdict>Favored|Allowed|OUTLIER):", re.M)


def report_ramachandran(xml: str) -> dict[tuple[str, int, str], str]:
    """Per-residue Ramachandran verdict (Favored/Allowed/OUTLIER) from the report."""
    out = {}
    for block in _XML_SUBGROUP.findall(xml):
        attrs = dict(re.findall(r'([\w-]+)="([^"]*)"', block))
        rama, chain, resnum = attrs.get("rama"), attrs.get("chain"), attrs.get("resnum")
        if not rama or not chain or resnum is None:
            continue
        icode = attrs.get("icode", "").strip()
        try:
            out[(chain, int(resnum), icode, attrs.get("resname", "").upper())] = rama
        except ValueError:
            continue
    return out


def local_ramachandran(ramalyze_log: str) -> dict[tuple[str, int, str, str], str]:
    """Per-residue Ramachandran verdict from a phenix.ramalyze log."""
    out = {}
    for m in _RAMALYZE_RESIDUE.finditer(ramalyze_log):
        resname = m.group("resname").strip()[-3:].upper()
        key = (m.group("chain"), int(m.group("resseq")), m.group("icode").strip(), resname)
        out[key] = m.group("verdict")
    return out


def ramachandran_agreement(xml: str, ramalyze_log: str) -> dict[str, Any]:
    """Do the two pipelines assign the same Ramachandran verdict to the same residue?

    The denominator-robust companion to the raw favored-/outlier-% |Δ| (#284): the raw
    percentages differ when the pipelines evaluate different residue *sets* (altloc /
    completeness), but the per-shared-residue verdict agreement isolates whether they
    *classify* the residues they both see the same way. Keyed `(chain, resnum, resname)`,
    exactly like `rotamer_agreement`.
    """
    ref, local = report_ramachandran(xml), local_ramachandran(ramalyze_log)
    shared = sorted(set(ref) & set(local))
    if not shared:
        return {"n_shared": 0}
    same = [k for k in shared if ref[k] == local[k]]
    disagree = [{"residue": list(k), "report": ref[k], "phenix": local[k]}
                for k in shared if ref[k] != local[k]]
    return {
        "n_shared": len(shared),
        "n_same": len(same),
        "agreement": round(len(same) / len(shared), 4),
        "disagreements": disagree,
    }


def fetch_text(url: str, dest: Path) -> str | None:
    """Download a text resource, cached; None if the server has none."""
    if dest.exists() and dest.stat().st_size:
        return dest.read_text(errors="ignore")
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        with urllib.request.urlopen(url, timeout=180) as resp:
            body = resp.read()
    except urllib.error.HTTPError:
        return None
    dest.write_bytes(body)
    return body.decode("utf-8", errors="ignore")


def fetch_model(pdb_id: str, cache: Path) -> Path | None:
    """Deposited PDB-format coordinates."""
    dest = cache / f"{pdb_id.lower()}.pdb"
    if dest.exists() and dest.stat().st_size:
        return dest
    cache.mkdir(parents=True, exist_ok=True)
    try:
        with urllib.request.urlopen(RCSB_PDB.format(pdb_id=pdb_id.upper()), timeout=180) as r:
            dest.write_bytes(r.read())
    except urllib.error.HTTPError:
        return None
    return dest


def run_tool(exe: str, model: Path, work: Path, tag: str, pattern: re.Pattern) -> str | None:
    """Run a PHENIX validation tool and return its log text (cached)."""
    log = work / f"{tag}_{model.stem}.log"
    if not log.exists() or not pattern.search(log.read_text(errors="ignore")):
        run_logged([phenix(exe), model], log, cwd=work, timeout=3600)
    return log.read_text(errors="ignore") if log.exists() else None


def collect(pdb_ids: list[str], cache: Path, mvd_cache: Path | None) -> tuple[list[dict], list[dict]]:
    """Compare local PHENIX values against the deposited validation report."""
    rows, skipped = [], []
    for pdb_id in pdb_ids:
        pdb_id = pdb_id.upper()
        low = pdb_id.lower()
        print(f"[{pdb_id}]", file=sys.stderr)
        model = fetch_model(pdb_id, cache)
        xml = fetch_text(VALIDATION_XML.format(pdb_id=low), cache / f"{low}_validation.xml")
        stats_raw = fetch_text(KEY_STATS.format(pdb_id=low), cache / f"{low}_keystats.json")
        if model is None or xml is None or stats_raw is None:
            skipped.append({"pdb_id": pdb_id, "reason": "no model or no validation report"})
            continue
        if not xml.lstrip().startswith("<?xml"):
            skipped.append({"pdb_id": pdb_id, "reason": "validation XML not served (got HTML)"})
            continue
        stats = json.loads(stats_raw).get(low, {})

        rama_log = run_tool("phenix.ramalyze", model, cache, "rama", _RAMA_OUT)
        rota_log = run_tool("phenix.rotalyze", model, cache, "rota", _ROTA_OUT)
        if rama_log is None or rota_log is None:
            skipped.append({"pdb_id": pdb_id, "reason": "ramalyze/rotalyze failed"})
            continue
        rama_out = _RAMA_OUT.search(rama_log)
        rota_out = _ROTA_OUT.search(rota_log)
        if not rama_out or not rota_out:
            skipped.append({"pdb_id": pdb_id, "reason": "no SUMMARY line from ramalyze/rotalyze"})
            continue

        def dep_pct(key: str) -> float | None:
            raw = (stats.get(key) or {}).get("percent_outliers")
            try:
                return float(raw)
            except (TypeError, ValueError):
                return None

        row: dict[str, Any] = {
            "pdb_id": pdb_id,
            "phenix_rama_outlier_pct": float(rama_out.group(1)),
            # Reference = the report's own per-residue verdicts, consistent with
            # favored_pct and the rotamer-name agreement (#281). The API percent_outliers
            # is retained below as *_api_pct: for Ramachandran it agrees with the XML, for
            # sidechains it does not (it is a broader metric), which is the bug's evidence.
            "wwpdb_rama_outlier_pct": outlier_pct(xml, _RES_RAMA),
            "phenix_rota_outlier_pct": float(rota_out.group(1)),
            "wwpdb_rota_outlier_pct": outlier_pct(xml, _RES_ROTA),
            "wwpdb_rama_outlier_api_pct": dep_pct("protein_ramachandran"),
            "wwpdb_rota_sidechain_api_pct": dep_pct("protein_sidechains"),
            "wwpdb_completeness": entry_attribute(xml, "DataCompleteness"),
            "deposited_r_free": entry_attribute(xml, "PDB-Rfree"),
            "wwpdb_dcc_r_free": entry_attribute(xml, "DCC_Rfree"),
            "wwpdb_clashscore": entry_attribute(xml, "clashscore"),
        }
        fav = _RAMA_FAV.search(rama_log)
        row["phenix_rama_favored_pct"] = float(fav.group(1)) if fav else None
        row["wwpdb_rama_favored_pct"] = favored_pct(xml, _RES_RAMA)
        row["wwpdb_rota_favored_pct"] = favored_pct(xml, _RES_ROTA)
        rota_fav = _ROTA_FAV.search(rota_log)
        row["phenix_rota_favored_pct"] = float(rota_fav.group(1)) if rota_fav else None
        row.update({f"rotamer_{k}": v for k, v in rotamer_agreement(xml, rota_log).items()})
        row.update({f"ramachandran_{k}": v for k, v in ramachandran_agreement(xml, rama_log).items()})
        row.update({f"boundary_{k}": v for k, v in boundary_exposure(rota_log).items()})
        row.update(chi1_agreement(model, rota_log))
        row.update(cross_library_sidechain(model, rota_log))

        # R-free and completeness come from a model_vs_data run; reuse the R-offset
        # benchmark's cache when one is supplied rather than repeating a slow job.
        mvd_text = None
        if mvd_cache:
            mvd_log = mvd_cache / f"mvd_{low}.log"
            if mvd_log.exists():
                mvd_text = mvd_log.read_text(errors="ignore")
        if mvd_text:
            r_free = _MVD_RFREE.search(mvd_text)
            comp = _MVD_COMPLETENESS.search(mvd_text)
            row["phenix_r_free"] = float(r_free.group(1)) if r_free else None
            row["phenix_completeness_pct"] = round(float(comp.group(1)) * 100, 2) if comp else None
        else:
            row["phenix_r_free"] = row["phenix_completeness_pct"] = None

        for local, dep, name in (
            ("phenix_rama_outlier_pct", "wwpdb_rama_outlier_pct", "rama_outlier_delta_pp"),
            ("phenix_rama_favored_pct", "wwpdb_rama_favored_pct", "rama_favored_delta_pp"),
            ("phenix_rota_favored_pct", "wwpdb_rota_favored_pct", "rota_favored_delta_pp"),
            ("phenix_rota_outlier_pct", "wwpdb_rota_outlier_pct", "rota_outlier_delta_pp"),
            # Two different references, and they are not interchangeable: PDB-Rfree is
            # the depositor's own refinement result, DCC_Rfree is wwPDB re-deriving it
            # from the deposited model and data the way this benchmark does.
            ("phenix_r_free", "deposited_r_free", "r_free_delta"),
            ("phenix_r_free", "wwpdb_dcc_r_free", "r_free_delta_vs_dcc"),
            ("phenix_completeness_pct", "wwpdb_completeness", "completeness_delta_pp"),
        ):
            a, b = row.get(local), row.get(dep)
            row[name] = round(a - b, 4) if a is not None and b is not None else None
        rows.append(row)
        print(f"  rama {row['phenix_rama_outlier_pct']} vs {row['wwpdb_rama_outlier_pct']} | "
              f"rota {row['phenix_rota_outlier_pct']} vs {row['wwpdb_rota_outlier_pct']} | "
              f"Rfree {row['phenix_r_free']} vs {row['deposited_r_free']} | "
              f"compl {row['phenix_completeness_pct']} vs {row['wwpdb_completeness']}",
              file=sys.stderr)
    return rows, skipped


def summarize(rows: list[dict]) -> dict[str, Any]:
    """|Δ| distribution for each of the four tolerances."""
    if not rows:
        return {"n": 0}

    def stats(key: str) -> dict[str, Any]:
        values = sorted(abs(r[key]) for r in rows if r.get(key) is not None)
        if not values:
            return {"n": 0}
        idx = min(len(values) - 1, max(0, round(0.9 * (len(values) - 1))))
        return {"n": len(values), "abs_median": round(statistics.median(values), 4),
                "abs_p90": round(values[idx], 4), "abs_max": round(values[-1], 4)}

    return {
        "n_entries": len(rows),
        "rama_outlier_pp": stats("rama_outlier_delta_pp"),
        "rama_favored_pp": stats("rama_favored_delta_pp"),
        "rota_favored_pp": stats("rota_favored_delta_pp"),
        "cross_library_sidechain": {
            "n_entries": sum(1 for r in rows if r.get("n_sidechains_compared")),
            "n_residues": sum(r.get("n_sidechains_compared", 0) for r in rows),
            **{f"median_z_{v}": (lambda vals: round(statistics.median(vals), 3) if vals else None)(
                [r[f"median_torsion_z_{v}"] for r in rows if r.get(f"median_torsion_z_{v}") is not None])
               for v in ("favored", "allowed", "outlier")},
            **{f"n_{v}": sum(r.get(f"n_{v}", 0) for r in rows)
               for v in ("favored", "allowed", "outlier")},
        },
        "chi1_geometry_agreement": {
            "n_entries": sum(1 for r in rows if r.get("n_chi1_compared")),
            "n_residues": sum(r.get("n_chi1_compared", 0) for r in rows),
            "max_abs_deg": max((r["chi1_max_abs_deg"] for r in rows
                                if r.get("chi1_max_abs_deg") is not None), default=None),
            "n_above_0_1_deg": sum(r.get("n_chi1_above_0_1_deg", 0) for r in rows),
        },
        "favored_allowed_boundary_exposure": {
            "n_residues": sum(r.get("boundary_n_scored", 0) for r in rows),
            **{f"pct_within_x{m}": (
                round(100.0 * sum(r.get(f"boundary_exposed_x{m}", 0) for r in rows)
                      / max(1, sum(r.get("boundary_n_scored", 0) for r in rows)), 2))
               for m in (1.25, 1.5, 2.0)},
        },
        "rotamer_name_agreement": {
            "n_entries": sum(1 for r in rows if r.get("rotamer_n_shared")),
            "n_residues": sum(r.get("rotamer_n_shared", 0) for r in rows),
            "n_same": sum(r.get("rotamer_n_same_rotamer", 0) for r in rows),
            "worst_entry_agreement": min(
                (r["rotamer_rotamer_agreement"] for r in rows
                 if r.get("rotamer_rotamer_agreement") is not None), default=None),
        },
        "rota_outlier_pp": stats("rota_outlier_delta_pp"),
        "r_free_vs_deposited": stats("r_free_delta"),
        "r_free_vs_wwpdb_recomputed": stats("r_free_delta_vs_dcc"),
        "completeness_pp": stats("completeness_delta_pp"),
    }


# INCOMPLETE: 11 of the 17 entries, committed in round 18 as the most recoverable.
#
# This script backs several tolerance rows with DIFFERENT denominators, and they are not
# equally recorded:
#   - completeness and R-free (n = 9): FULLY recorded. The 9-entry table in
#     `ref/research/tolerance_benchmark_vs_deposited.md` gives every value, so those
#     figures are reproducible. Those 9 are the first nine ids below.
#   - Ramachandran/rotamer favored % (n = 17): NO per-entry value was ever written down,
#     not even the worst. The row's median 0.00 / p90 0.02 / max 0.16 pp cannot be
#     recounted.
#   - Ramachandran/rotamer outlier % (n = 17): only the 4 entries with nonzero outliers
#     are named (24MR, 28SW, 28SZ, 9PN7 -- the last two ids below). The 13 that compare
#     0.00 to 0.00 are unnamed, which matters because the row itself says those 13 are
#     the uninformative ones.
#
# So a re-run on this set reproduces the completeness and R-free rows exactly, and
# under-counts the Ramachandran rows by 6 entries.
DEFAULT_SET = [
    "12LO", "30TW", "9LK0", "30IZ", "37AP", "24MR", "11AF", "28SW", "28SX", "28SZ",
    "9PN7",
]
SET_IS_COMPLETE = False
SET_SHORTFALL = "11 of 17 -- the Ramachandran/rotamer figures ran on 17 entries, 6 unnamed"


def main() -> int:
    from benchmark_environment import announce_benchmark_environment

    announce_benchmark_environment()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("pdb_ids", nargs="*")
    ap.add_argument("--ids-file")
    ap.add_argument("--cache")
    ap.add_argument("--mvd-cache", help="reuse mvd_*.log from bench_t06_r_offset.py")
    ap.add_argument("--json", dest="json_out")
    args = ap.parse_args()

    ids = list(args.pdb_ids)
    if args.ids_file:
        payload = json.loads(Path(args.ids_file).read_text())
        ids += payload if isinstance(payload, list) else [i for v in payload.values() for i in v]
    if not ids:
        ids = list(DEFAULT_SET)
        print(f"WARNING: the committed set is INCOMPLETE -- {SET_SHORTFALL}.\n"
              f"Running {len(ids)} entries; published figures used more.",
              file=sys.stderr)

    cache = Path(args.cache) if args.cache else Path(tempfile.gettempdir()) / "bench_cache_dep"
    rows, skipped = collect(ids, cache, Path(args.mvd_cache) if args.mvd_cache else None)
    summary = summarize(rows)
    if args.json_out:
        Path(args.json_out).write_text(
            json.dumps({"rows": rows, "skipped": skipped, "summary": summary}, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    return 0 if rows else 1


if __name__ == "__main__":
    raise SystemExit(main())
