#!/usr/bin/env python3
"""Phase 1 of the negative-control benchmark: residue-level masks (#295).

`ref/research/negative_control_benchmark_plan.md` requires that scoring from a
gold-standard start happen on unmasked residues only, with the deposited model's
own MolProbity outliers PROTECTED (a method that "fixes" one scores a degradation
hit). This script emits one committed mask file per entry, one reason per residue.

Mask sources (1-3 mask, 4 protects):
  1. altconf          any alternate conformation (validation-XML `altcode`);
                      Top2018 precedent — excluded, not adjudicated
  2. rsrz_outlier     |RSRZ| > 2, the wwPDB outlier definition
  3. high_b           residue owab > 2x the entry's median owab (relative tail —
                      an absolute cut like Top2018's B <= 40 is vacuous at sub-A)
  4. lattice_contact  any atom within 4.0 A of a symmetry-mate non-water atom
                      (gemmi ContactSearch, image_idx != 0); CASP14 precedent —
                      the reference may be in a non-natural conformation there

Protection applies AFTER masking (#298): a deposited rama/rota/clash outlier on an
unmasked residue is protected; the same outlier on a masked residue is just masked.
That ordering is what makes protected outliers density-supported by construction —
the RSRZ and B cuts have already removed the poorly-supported ones.

THRESHOLD STATUS: |RSRZ| > 2 is the wwPDB definition. The 2x-median B tail, the
4.0 A contact cutoff, and clash-protection are scouting values to be finalized in
the phase-2 preregistration (#297 discipline: enrollment-affecting values are
preregistered, not baked in here). All four are flags, so a sensitivity sweep is a
re-run, not a rewrite.

KNOWN LIMITATION: only symmetry-image contacts count as lattice contacts.
Chain-chain interfaces WITHIN the asymmetric unit are ambiguous (biological or
packing); they are not masked here, and the preregistration must decide their
treatment before enrollment.

The per-residue rows come from the wwPDB validation XML (ElementTree, not the
regex idiom of bench_vs_deposited.py, because clash records are child elements and
altconf residues appear as one row PER altloc — nesting and merging both want a
real parser). Waters are excluded from the mask universe.

Usage:
    python3 scripts/gold_mask.py 1EJG 2VXN --out-dir ref/research/data/masks
    python3 scripts/gold_mask.py --ids-json ref/research/data/negative_control_phase0_counts.json --sample 12
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CIF_URL = "https://files.rcsb.org/download/{pdb_id}.cif"
VALIDATION_XML = "https://www.ebi.ac.uk/pdbe/entry-files/download/{pdb_id}_validation.xml"

RSRZ_CUT = 2.0          # wwPDB outlier definition
B_TAIL_FACTOR = 2.0     # scouting value; preregistration finalizes (#297)
LATTICE_CUTOFF_A = 4.0  # scouting value; preregistration finalizes (#297)


def fetch(url: str, dest: Path) -> Path:
    if dest.exists() and dest.stat().st_size > 0:
        return dest
    try:
        with urllib.request.urlopen(url, timeout=300) as r:
            dest.write_bytes(r.read())
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
        raise SystemExit(f"gold_mask: fetch failed for {url}: {exc}")
    if dest.stat().st_size == 0:
        raise SystemExit(f"gold_mask: empty download from {url}")
    return dest


def parse_residue_rows(xml_path: Path) -> list[dict]:
    """One dict per ModelledSubgroup row (a residue may span several — one per
    altloc). Waters excluded here so every downstream count shares one universe."""
    root = ET.parse(xml_path).getroot()
    rows = []
    for sub in root.iter("ModelledSubgroup"):
        if sub.get("resname", "").upper() == "HOH":
            continue
        rows.append({
            "chain": sub.get("chain"),
            "resnum": int(sub.get("resnum")),
            "icode": (sub.get("icode") or " ").strip(),
            "resname": sub.get("resname", "").upper(),
            "altcode": (sub.get("altcode") or " ").strip(),
            "rsrz": _float(sub.get("rsrz")),
            "owab": _float(sub.get("owab")),
            "rama": sub.get("rama"),
            "rota": sub.get("rota"),
            "n_clashes": len(sub.findall("clash")),
        })
    return rows


def _float(text: str | None) -> float | None:
    try:
        return float(text) if text not in (None, "") else None
    except ValueError:
        return None


def merge_rows(rows: list[dict]) -> dict[tuple, dict]:
    """Collapse altloc rows to one record per residue.

    Worst-case aggregation on purpose: max |rsrz|, max owab, any clash, any
    OUTLIER verdict — a residue is as suspect as its worst conformer, and a
    genuine outlier in any conformer is still a feature of the deposited model.
    """
    merged: dict[tuple, dict] = {}
    for row in rows:
        key = (row["chain"], row["resnum"], row["icode"])
        rec = merged.setdefault(key, {
            "resname": row["resname"], "altconf": False, "rsrz": None,
            "owab": None, "rama_outlier": False, "rota_outlier": False,
            "n_clashes": 0})
        if row["altcode"]:
            rec["altconf"] = True
        if row["rsrz"] is not None and (rec["rsrz"] is None
                                        or abs(row["rsrz"]) > abs(rec["rsrz"])):
            rec["rsrz"] = row["rsrz"]
        if row["owab"] is not None and (rec["owab"] is None
                                        or row["owab"] > rec["owab"]):
            rec["owab"] = row["owab"]
        if (row["rama"] or "").upper() == "OUTLIER":
            rec["rama_outlier"] = True
        if (row["rota"] or "").upper() == "OUTLIER":
            rec["rota_outlier"] = True
        rec["n_clashes"] += row["n_clashes"]
    return merged


def classify(residues: dict[tuple, dict], lattice: set[tuple],
             rsrz_cut: float = RSRZ_CUT,
             b_tail_factor: float = B_TAIL_FACTOR) -> dict:
    """Mask reasons and (post-mask) protection per residue.

    `lattice` holds (chain, resnum, icode) keys of lattice-contact residues,
    injected so the classification is testable without gemmi or coordinates.
    """
    owabs = [r["owab"] for r in residues.values() if r["owab"] is not None]
    b_cut = b_tail_factor * statistics.median(owabs) if owabs else None

    out = {}
    for key, rec in sorted(residues.items()):
        masked = []
        if rec["altconf"]:
            masked.append("altconf")
        if rec["rsrz"] is not None and abs(rec["rsrz"]) > rsrz_cut:
            masked.append("rsrz_outlier")
        if b_cut is not None and rec["owab"] is not None and rec["owab"] > b_cut:
            masked.append("high_b")
        if key in lattice:
            masked.append("lattice_contact")
        protected = []
        if not masked:                      # protection applies AFTER masking (#298)
            if rec["rama_outlier"]:
                protected.append("rama_outlier")
            if rec["rota_outlier"]:
                protected.append("rota_outlier")
            if rec["n_clashes"]:
                protected.append("clash")
        out[key] = {"resname": rec["resname"], "masked": masked,
                    "protected": protected}
    return out


def lattice_residues(cif_path: Path, cutoff: float = LATTICE_CUTOFF_A) -> set[tuple]:
    """(chain, resnum, icode) of residues with any atom within `cutoff` of a
    symmetry-mate (image_idx != 0) non-water atom. ASU-internal interfaces are
    deliberately not included — see the module docstring."""
    import gemmi  # deferred: classification tests must not need gemmi

    st = gemmi.read_structure(str(cif_path))
    st.setup_entities()
    ns = gemmi.NeighborSearch(st[0], st.cell, max(5.0, cutoff + 1.0)).populate()
    cs = gemmi.ContactSearch(cutoff)
    cs.ignore = gemmi.ContactSearch.Ignore.SameAsu
    found = set()
    for contact in cs.find_contacts(ns):
        if contact.image_idx == 0:
            continue
        pair = (contact.partner1, contact.partner2)
        if any(cra.residue.is_water() for cra in pair):
            continue
        for cra in pair:
            found.add((cra.chain.name, cra.residue.seqid.num,
                       (cra.residue.seqid.icode or " ").strip()))
    return found


def build_mask(pdb_id: str, cache: Path) -> dict:
    pdb_id = pdb_id.lower()
    xml_path = fetch(VALIDATION_XML.format(pdb_id=pdb_id),
                     cache / f"{pdb_id}_validation.xml")
    cif_path = fetch(CIF_URL.format(pdb_id=pdb_id), cache / f"{pdb_id}.cif")

    residues = merge_rows(parse_residue_rows(xml_path))
    if not residues:
        raise SystemExit(f"gold_mask: {pdb_id}: no modelled residues in the "
                         f"validation XML — nothing to mask")
    lattice = lattice_residues(cif_path)
    classified = classify(residues, lattice)

    n = len(classified)
    n_masked = sum(1 for c in classified.values() if c["masked"])
    reason_counts: dict[str, int] = {}
    for c in classified.values():
        for reason in c["masked"]:
            reason_counts[reason] = reason_counts.get(reason, 0) + 1
    protected = {key: c for key, c in classified.items() if c["protected"]}

    return {
        "pdb_id": pdb_id.upper(),
        "thresholds": {"rsrz": RSRZ_CUT, "b_tail_factor": B_TAIL_FACTOR,
                       "lattice_cutoff_a": LATTICE_CUTOFF_A},
        "n_residues": n,
        "n_masked": n_masked,
        "mask_fraction": round(n_masked / n, 3),
        "mask_reason_counts": reason_counts,       # a residue can carry several
        "n_protected": len(protected),
        "protected": [
            {"chain": k[0], "resnum": k[1], "icode": k[2],
             "resname": c["resname"], "reasons": c["protected"]}
            for k, c in sorted(protected.items())],
        "residues": [
            {"chain": k[0], "resnum": k[1], "icode": k[2],
             "resname": c["resname"], "masked": c["masked"],
             "protected": c["protected"]}
            for k, c in sorted(classified.items())],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ids", nargs="*", help="PDB ids")
    ap.add_argument("--ids-json",
                    help="phase-0 counts JSON; ids come from its percentile sample")
    ap.add_argument("--sample", type=int, default=0,
                    help="with --ids-json: cap ids taken from the sample (0 = all)")
    ap.add_argument("--cache", default="/tmp/goldmask_cache")
    ap.add_argument("--out-dir", default="ref/research/data/masks")
    args = ap.parse_args()

    ids = [i.upper() for i in args.ids]
    if args.ids_json:
        sampled = json.loads(Path(args.ids_json).read_text())[
            "percentile_sample"]["sampled"]
        json_ids = [row["pdb_id"] for row in sampled]
        if args.sample:
            json_ids = json_ids[:args.sample]
        ids += [i for i in json_ids if i not in ids]
    if not ids:
        raise SystemExit("gold_mask: no ids given (positional or --ids-json)")

    cache = Path(args.cache)
    cache.mkdir(parents=True, exist_ok=True)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    summary = []
    for pdb_id in ids:
        mask = build_mask(pdb_id, cache)
        out_path = out_dir / f"{pdb_id.upper()}_mask.json"
        out_path.write_text(json.dumps(mask, indent=2) + "\n")
        summary.append({k: mask[k] for k in
                        ("pdb_id", "n_residues", "n_masked", "mask_fraction",
                         "n_protected")} | {"reasons": mask["mask_reason_counts"]})
        print(f"  {mask['pdb_id']}: {mask['n_masked']}/{mask['n_residues']} masked "
              f"({mask['mask_fraction']:.0%}), {mask['n_protected']} protected "
              f"-> {out_path}", file=sys.stderr)

    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
