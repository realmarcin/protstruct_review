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
      `clashscore`
  - `https://www.ebi.ac.uk/pdbe/api/validation/key_validation_stats/entry/<id>`
    → `protein_ramachandran` and `protein_sidechains` outlier percentages

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
import os
import re
import statistics
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

RCSB_PDB = "https://files.rcsb.org/download/{pdb_id}.pdb"
VALIDATION_XML = "https://www.ebi.ac.uk/pdbe/entry-files/download/{pdb_id}_validation.xml"
KEY_STATS = "https://www.ebi.ac.uk/pdbe/api/validation/key_validation_stats/entry/{pdb_id}"
PHENIX_BIN = Path.home() / "phenix-2.0-5936" / "phenix_bin"

_RAMA_OUT = re.compile(r"SUMMARY:\s*([\d.]+)%\s*outliers")
_RAMA_FAV = re.compile(r"SUMMARY:\s*([\d.]+)%\s*favored")
_ROTA_OUT = re.compile(r"SUMMARY:\s*([\d.]+)%\s*outliers")
_ROTA_FAV = re.compile(r"SUMMARY:\s*([\d.]+)%\s*favored")
_MVD_RFREE = re.compile(r"^\s*r_free:\s*([\d.]+)\s*$", re.M)
_MVD_COMPLETENESS = re.compile(r"Completeness in resolution range:\s*([\d.]+)")
# Per-residue verdicts in the validation report. There is no entry-level "favored %"
# attribute — only outlier counts — so the Ramachandran favored fraction is counted
# from `rama="Favored|Allowed|OUTLIER"`. NOTE the rotamer attribute is NOT a verdict:
# `rota="m-10"`, `rota="mp"` etc. name the rotamer the residue adopts, with no
# favored/allowed classification and no OUTLIER value present, so the rotamer favored %
# cannot be obtained this way and is left unmeasured.
_RES_RAMA = re.compile(r'\brama="([^"]+)"')
_RES_ROTA = re.compile(r'\brota="([^"]+)"')


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
        subprocess.run(["bash", "-c", f"cd {work} && {PHENIX_BIN / exe} {model} > {log} 2>&1"],
                       capture_output=True, text=True, timeout=3600, env=dict(os.environ))
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
            "wwpdb_rama_outlier_pct": dep_pct("protein_ramachandran"),
            "phenix_rota_outlier_pct": float(rota_out.group(1)),
            "wwpdb_rota_outlier_pct": dep_pct("protein_sidechains"),
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
        "rota_outlier_pp": stats("rota_outlier_delta_pp"),
        "r_free_vs_deposited": stats("r_free_delta"),
        "r_free_vs_wwpdb_recomputed": stats("r_free_delta_vs_dcc"),
        "completeness_pp": stats("completeness_delta_pp"),
    }


def main() -> int:
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
        ap.error("give PDB IDs or --ids-file")

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
