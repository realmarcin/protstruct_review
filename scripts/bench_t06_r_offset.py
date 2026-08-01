#!/usr/bin/env python3
"""Benchmark the independent-code-path R offset: gemmi sfcalc vs phenix.model_vs_data.

Measures the tolerance in `ref/thresholds_and_standards.md` whose row states its own
magnitude is **unbenchmarked**: "an independent R re-derivation may differ by a small
amount from scaling / resolution-binning differences".

Method — both paths start from the same deposited model and the same MTZ:
  - PHENIX: `phenix.model_vs_data model.pdb data.mtz` → `r_work` (its own bulk-solvent
    correction, anisotropic scaling, outlier rejection and resolution handling).
  - gemmi:  `gemmi sfcalc --dmin=<d_min> --scale-to=<mtz>:<F>:<SIG> --to-mtz=...`
    computes Fcalc with a flat-mask bulk-solvent correction and anisotropic scaling —
    the same physics PHENIX uses, which is the point: gemmi is an independent
    implementation, NOT a simpler model. R is then summed over the work set:
    R = Σ||Fobs| − |Fcalc|| / Σ|Fobs|.

The R summation is deliberately done here rather than inside either program: it is
three lines of arithmetic, and keeping it outside means the comparison is between the
two Fcalc computations, not between two reporting conventions. The work/test split and
the reflection set are taken from the same MTZ for both sides.

Entries must have deposited **amplitudes** (`_refln.F_meas_au`) and a free-flag status
column; intensity-only entries are skipped rather than converted, since the conversion
would itself be a code path under test.

Usage:
    python3 scripts/bench_t06_r_offset.py 1ABC 2DEF --cache DIR --json out.json
    python3 scripts/bench_t06_r_offset.py --ids-file ids.json --cache DIR
    python3 scripts/bench_t06_r_offset.py --screen 1ABC 2DEF
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

RCSB_SF = "https://files.rcsb.org/download/{pdb_id}-sf.cif"
RCSB_PDB = "https://files.rcsb.org/download/{pdb_id}.pdb"
RCSB_CIF = "https://files.rcsb.org/download/{pdb_id}.cif"
MODEL_VS_DATA = str(Path.home() / "phenix-2.0-5936" / "phenix_bin" / "phenix.model_vs_data")

_R_WORK = re.compile(r"^\s*r_work:\s*([\d.]+)\s*$", re.M)
_R_FREE = re.compile(r"^\s*r_free:\s*([\d.]+)\s*$", re.M)
_RESO = re.compile(r"Resolution range:\s*([\d.]+)\s+([\d.]+)")

# Amplitude column names cif2mtz may produce, in preference order.
_F_PAIRS = (("FP", "SIGFP"), ("F", "SIGF"), ("FOBS", "SIGFOBS"))


def fetch(url: str, dest: Path) -> Path | None:
    """Download `url` to `dest` unless cached; None when the server has no such file."""
    if dest.exists() and dest.stat().st_size:
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        with urllib.request.urlopen(url, timeout=180) as resp:
            dest.write_bytes(resp.read())
    except urllib.error.HTTPError:
        return None
    return dest


def screen(pdb_ids: list[str]) -> list[str]:
    """Which entries deposited amplitudes *and* a free-flag status column?

    Reads only the head of each sf-cif — the `_refln` loop header is in the first few
    KB — so unusable entries cost a few KB instead of a full download.
    """
    eligible = []
    for pdb_id in pdb_ids:
        try:
            with urllib.request.urlopen(RCSB_SF.format(pdb_id=pdb_id.upper()), timeout=60) as r:
                head = r.read(16384).decode("utf-8", errors="ignore")
        except urllib.error.HTTPError:
            continue
        if "_refln.F_meas_au" in head and "_refln.status" in head:
            eligible.append(pdb_id.upper())
    return eligible


def to_mtz(sf: Path, work: Path) -> tuple[Path, tuple[str, str], str] | None:
    """Convert the sf-cif; return (mtz, (F_label, SIG_label), free_label).

    Uses `gemmi cif2mtz` rather than CCP4's: CCP4's converter re-settings the space
    group for some entries (11AF: deposited CRYST1 says P 2 21 21, CCP4 cif2mtz
    writes P 21 21 2), and `phenix.model_vs_data` then aborts on a symmetry mismatch
    against the model. gemmi preserves the deposited setting. Both programs read the
    identical converted file either way, so the choice of converter does not affect
    what is being compared.
    """
    mtz = work / (sf.stem.replace("-sf", "") + "_g.mtz")
    if not mtz.exists():
        proc = subprocess.run(["bash", "-c", f"cd {work} && gemmi cif2mtz {sf} {mtz} 2>&1"],
                              capture_output=True, text=True, timeout=1800)
        if not mtz.exists():
            print(f"  ! gemmi cif2mtz failed: {proc.stdout[-200:]}", file=sys.stderr)
            return None
    import gemmi
    import numpy as np

    full = gemmi.read_mtz_file(str(mtz))
    labels = {c.label for c in full.columns}
    free = next((lab for lab in ("FreeR_flag", "FREE") if lab in labels), None)
    if free is None:
        return None
    fpair = next((p for p in _F_PAIRS if labels.issuperset(p)), None)
    if fpair is None:
        return None

    # Strip to H K L + amplitudes + free flags. Depositions often also carry FC/PHIC,
    # and phenix.model_vs_data then aborts with "Multiple equally suitable arrays of
    # observed xray data found" rather than choosing. Stripping removes the ambiguity
    # at the source and guarantees both programs see exactly the same columns.
    stripped = mtz.with_name(mtz.stem + "_obs.mtz")
    if not stripped.exists():
        src = {c.label: i for i, c in enumerate(full.columns)}
        out = gemmi.Mtz(with_base=True)
        out.spacegroup = full.spacegroup
        out.set_cell_for_all(full.cell)
        out.add_dataset("obs")
        for label, ctype in ((fpair[0], "F"), (fpair[1], "Q"), (free, "I")):
            out.add_column(label, ctype)
        cols = [0, 1, 2, src[fpair[0]], src[fpair[1]], src[free]]
        out.set_data(np.asarray(full.array)[:, cols])
        out.write_to_file(str(stripped))
    return stripped, fpair, free


def run_model_vs_data(model: Path, mtz: Path, work: Path) -> dict[str, Any] | None:
    """PHENIX r_work / r_free and the resolution range it used.

    `model_vs_data` emits **two** result blocks: the first over the data as given, the
    second re-run inside the resolution limits recorded in the model header. On 28JJ
    those give r_work 0.2424 (64.79-2.10 Å) and 0.2231 (64.79-2.30 Å), and the second
    block reports the 26047 excluded reflections as "F-obs outliers".

    The **first** block is the one to read: the gemmi side is run at the `d_min` parsed
    from that same block, so both cover the same range. `.search()` returning the first
    match is therefore load-bearing, not incidental — switching to the last match would
    silently change the comparison by up to 0.02 in R, the whole width of the tolerance.
    """
    log = work / f"mvd_{model.stem}.log"
    if not log.exists() or not _R_WORK.search(log.read_text(errors="ignore")):
        subprocess.run(["bash", "-c", f"cd {work} && {MODEL_VS_DATA} {model} {mtz} > {log} 2>&1"],
                       capture_output=True, text=True, timeout=3600, env=dict(os.environ))
    if not log.exists():
        return None
    text = log.read_text(errors="ignore")
    r_work, reso = _R_WORK.search(text), _RESO.search(text)
    if not r_work:
        return None
    r_free = _R_FREE.search(text)
    return {
        "r_work": float(r_work.group(1)),
        "r_free": float(r_free.group(1)) if r_free else None,
        "d_max": float(reso.group(1)) if reso else None,
        "d_min": float(reso.group(2)) if reso else None,
    }


def free_test_value(flags) -> int | None:
    """Which value of the FREE column marks the *test* set.

    The convention is file-dependent and getting it backwards silently computes
    R-free and calls it R-work — a mistake worth about +0.06 in R, which is an order
    of magnitude larger than the offset being measured. Two conventions occur:

    - **Two-valued flags** (PHENIX-written MTZs, and many depositions): one value
      marks the test set and it is the minority, at ~5-10 % of reflections.
    - **Multi-bin flags** (CCP4/REFMAC style, e.g. 10 or 20 roughly equal bins): the
      bin index is not a work/test split at all, and by CCP4 convention bin **0** is
      the test set. Verified against PHENIX's own free-reflection count on 11MQ
      (518 reflections with flag 0; PHENIX reported Nfree = 517).

    Returns None when neither pattern applies, so the entry is skipped, not guessed.
    """
    import collections
    import numpy as np

    counts = collections.Counter(int(v) for v in flags if np.isfinite(v))
    if len(counts) < 2:
        return None
    if len(counts) == 2:
        (minor, minor_n) = counts.most_common()[-1]
        total = sum(counts.values())
        return minor if minor_n / total <= 0.2 else None
    return 0 if 0 in counts else None


def run_gemmi_r(model: Path, mtz: Path, labels: tuple[str, str], free_label: str,
                d_min: float, work: Path, radii_set: str) -> dict[str, Any] | None:
    """R-work from gemmi's scaled Fcalc, summed over the same work reflections.

    `radii_set` selects the bulk-solvent mask convention. `cctbx` matches what PHENIX
    uses, so it is the matched-configuration comparison; gemmi's own default (`vdw`)
    is run too, to show how much of any offset is mask convention rather than code.
    """
    import gemmi
    import numpy as np

    calc = work / f"gemmi_{model.stem}_{radii_set}.mtz"
    if not calc.exists():
        proc = subprocess.run(
            ["bash", "-c",
             f"cd {work} && gemmi sfcalc --dmin={d_min:.4f} --radii-set={radii_set} "
             f"--scale-to={mtz}:{labels[0]}:{labels[1]} --to-mtz={calc} {model} 2>&1"],
            capture_output=True, text=True, timeout=3600)
        if not calc.exists():
            print(f"  ! gemmi sfcalc failed: {proc.stdout[-200:]}", file=sys.stderr)
            return None

    obs, fcalc = gemmi.read_mtz_file(str(mtz)), gemmi.read_mtz_file(str(calc))
    oi = {c.label: i for i, c in enumerate(obs.columns)}
    ci = {c.label: i for i, c in enumerate(fcalc.columns)}
    calc_by_hkl = {(int(r[0]), int(r[1]), int(r[2])): r[ci["FC"]] for r in fcalc.array}

    test_flag = free_test_value(obs.array[:, oi[free_label]])
    if test_flag is None:
        return None

    fo, fc = [], []
    for row in obs.array:
        key = (int(row[0]), int(row[1]), int(row[2]))
        f, flag = row[oi[labels[0]]], row[oi[free_label]]
        if key not in calc_by_hkl or not np.isfinite(f) or not np.isfinite(flag):
            continue
        if int(flag) == test_flag:
            continue
        fo.append(f)
        fc.append(calc_by_hkl[key])
    if len(fo) < 100:
        return None
    fo, fc = np.array(fo), np.array(fc)
    return {"r_work": float(np.sum(np.abs(fo - fc)) / np.sum(fo)), "n_work": len(fo)}


def collect(pdb_ids: list[str], cache: Path) -> tuple[list[dict], list[dict]]:
    """Run both R derivations on every usable entry."""
    rows, skipped = [], []
    for pdb_id in pdb_ids:
        pdb_id = pdb_id.upper()
        print(f"[{pdb_id}]", file=sys.stderr)
        sf = fetch(RCSB_SF.format(pdb_id=pdb_id), cache / f"{pdb_id.lower()}-sf.cif")
        # Large entries are mmCIF-only — no PDB-format file exists. Both programs read
        # mmCIF, so fall back rather than silently dropping every big structure and
        # biasing the set towards small ones.
        model = fetch(RCSB_PDB.format(pdb_id=pdb_id), cache / f"{pdb_id.lower()}.pdb")
        if model is None:
            model = fetch(RCSB_CIF.format(pdb_id=pdb_id), cache / f"{pdb_id.lower()}.cif")
        if sf is None or model is None:
            skipped.append({"pdb_id": pdb_id, "reason": "no sf-cif or no coordinate file"})
            continue
        converted = to_mtz(sf, cache)
        if converted is None:
            print("  ! no amplitudes / no FREE column — skipped", file=sys.stderr)
            skipped.append({"pdb_id": pdb_id, "reason": "no amplitude or free-flag columns"})
            continue
        mtz, labels, free_label = converted
        phenix = run_model_vs_data(model, mtz, cache)
        if phenix is None or phenix["d_min"] is None:
            print("  ! model_vs_data failed", file=sys.stderr)
            skipped.append({"pdb_id": pdb_id, "reason": "model_vs_data failed"})
            continue
        matched = run_gemmi_r(model, mtz, labels, free_label, phenix["d_min"], cache, "cctbx")
        default = run_gemmi_r(model, mtz, labels, free_label, phenix["d_min"], cache, "vdw")
        if matched is None or default is None:
            skipped.append({"pdb_id": pdb_id, "reason": "gemmi sfcalc failed or too few matches"})
            continue
        delta = matched["r_work"] - phenix["r_work"]
        rows.append({
            "pdb_id": pdb_id,
            "d_min": phenix["d_min"],
            "n_work": matched["n_work"],
            "phenix_r_work": round(phenix["r_work"], 4),
            "phenix_r_free": phenix["r_free"],
            "gemmi_r_work_cctbx_mask": round(matched["r_work"], 4),
            "gemmi_r_work_vdw_mask": round(default["r_work"], 4),
            "delta": round(delta, 4),
            "abs_delta": round(abs(delta), 4),
            "mask_convention_effect": round(default["r_work"] - matched["r_work"], 4),
        })
        print(f"  d_min {phenix['d_min']:.2f}  PHENIX {phenix['r_work']:.4f}  "
              f"gemmi {matched['r_work']:.4f}  Δ {delta:+.4f}  (n_work {matched['n_work']}, "
              f"mask effect {default['r_work'] - matched['r_work']:+.4f})", file=sys.stderr)
    return rows, skipped


def summarize(rows: list[dict]) -> dict[str, Any]:
    """|Δ| distribution overall and by resolution."""
    if not rows:
        return {"n": 0}

    def stats(subset: list[dict]) -> dict[str, Any]:
        if not subset:
            return {"n": 0}
        absolute = sorted(r["abs_delta"] for r in subset)
        idx = min(len(absolute) - 1, max(0, round(0.9 * (len(absolute) - 1))))
        return {
            "n": len(subset),
            "signed_median": round(statistics.median(r["delta"] for r in subset), 4),
            "abs_median": round(statistics.median(absolute), 4),
            "abs_p90": round(absolute[idx], 4),
            "abs_max": round(absolute[-1], 4),
        }

    return {
        "overall": stats(rows),
        "gemmi_higher": sum(1 for r in rows if r["delta"] > 0),
        "phenix_higher": sum(1 for r in rows if r["delta"] < 0),
        "by_resolution": {
            "d_min < 1.8 A": stats([r for r in rows if r["d_min"] < 1.8]),
            "1.8-2.5 A": stats([r for r in rows if 1.8 <= r["d_min"] < 2.5]),
            "d_min >= 2.5 A": stats([r for r in rows if r["d_min"] >= 2.5]),
        },
    }


# The 15 entries (1.20-2.92 A) the R offset was measured on, committed in round 18.
# Recovered from the per-entry table in `ref/research/tolerance_benchmark_r_offset.md`,
# which names all 15 with their gemmi and PHENIX R values.
DEFAULT_SET = [
    "29QD", "12LO", "29OL", "29OH", "30TW", "9LK0", "37AP", "36TD", "30IZ", "28JJ",
    "11MQ", "24MR", "28SX", "11AF", "28SW",
]
SET_IS_COMPLETE = True


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("pdb_ids", nargs="*")
    ap.add_argument("--ids-file", help="JSON file: list of IDs, or {bin: [ids]}")
    ap.add_argument("--cache", help="work/download directory")
    ap.add_argument("--json", dest="json_out")
    ap.add_argument("--screen", action="store_true",
                    help="only report which candidates have amplitudes + free flags")
    args = ap.parse_args()

    ids = list(args.pdb_ids)
    if args.ids_file:
        payload = json.loads(Path(args.ids_file).read_text())
        ids += payload if isinstance(payload, list) else [i for v in payload.values() for i in v]
    if not ids:
        ids = list(DEFAULT_SET)
        print(f"using the committed benchmark set ({len(ids)} entries)",
              file=sys.stderr)

    if args.screen:
        eligible = screen(ids)
        out = json.dumps(eligible, indent=1)
        if args.json_out:
            Path(args.json_out).write_text(out + "\n")
        print(out)
        return 0 if eligible else 1

    cache = Path(args.cache) if args.cache else Path(tempfile.gettempdir()) / "bench_cache_t06"
    rows, skipped = collect(ids, cache)
    summary = summarize(rows)
    if args.json_out:
        Path(args.json_out).write_text(
            json.dumps({"rows": rows, "skipped": skipped, "summary": summary}, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    return 0 if rows else 1


if __name__ == "__main__":
    raise SystemExit(main())
