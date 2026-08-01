#!/usr/bin/env python3
"""Benchmark the T13 Wilson-B agreement tolerance: phenix.xtriage vs CCP4 ctruncate.

De-provisionalizes the `Wilson B | ± 5 Å²` tolerance in `ref/thresholds_and_standards.md`
/ `ref/structural_criteria.yaml` (GitHub #19) by measuring the actual inter-program
spread on deposited reflection data instead of asserting a magnitude.

Method — both programs read the **same** MTZ, converted once from the deposited
structure-factor file, so nothing but the estimator differs:
  - RCSB `<ID>-sf.cif` → `cif2mtz` → MTZ with merged intensities (I, SIGI).
    Entries that deposited amplitudes only (no `_refln.intensity_meas`) are skipped
    and reported, since a Wilson B from F is not the same measurement.
  - `phenix.xtriage`  → "ML estimate of overall B value" (maximum-likelihood,
    anisotropy-aware scaling).
  - `ctruncate`       → "Estimate of Wilson B factor" (classic Wilson-plot slope,
    BEST-reference corrected, bin-choice sensitive).

Each row also carries the resolution limit and xtriage's anisotropy spread
(max − min eigenvalue of B_cart), so the spread can be stratified post hoc rather
than by pre-labelling datasets as "anisotropic".

Usage:
    python3 scripts/bench_t13_wilson_b.py 9PLB 9HOO ...   --cache DIR --json out.json
    python3 scripts/bench_t13_wilson_b.py --ids-file candidates.json
"""
from __future__ import annotations

import argparse
import json
import os
import re
import statistics
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

RCSB_SF = "https://files.rcsb.org/download/{pdb_id}-sf.cif"
CCP4_SETUP = "/Applications/ccp4-9.0.015-shelx-arpwarp-macosarm/ccp4-9/bin/ccp4.setup-sh"
XTRIAGE = str(Path.home() / "phenix-2.0-5936" / "phenix_bin" / "phenix.xtriage")

_XT_WILSON = re.compile(r"ML estimate of overall B value:\s*\n\s*([-\d.]+)\s*A\*\*2")
_XT_RESO = re.compile(r"Resolution range:\s*([\d.]+)\s+([\d.]+)")
_XT_EIGEN = re.compile(r"\|\s*[123]\s*\|\s*([-\d.]+)\s*\|\s*\(")
_CT_WILSON = re.compile(r"Estimate of Wilson B factor:\s*([-\d.]+)\s*A\^\(-2\)")


def sh(cmd: str, timeout: int = 3600) -> subprocess.CompletedProcess:
    """Run `cmd` under bash with the CCP4 environment sourced."""
    return subprocess.run(
        ["bash", "-c", f"source {CCP4_SETUP} >/dev/null 2>&1; {cmd}"],
        capture_output=True, text=True, timeout=timeout,
    )


def fetch_sf(pdb_id: str, cache: Path) -> Path | None:
    """Download the deposited structure-factor cif; None if RCSB has none."""
    dest = cache / f"{pdb_id.lower()}-sf.cif"
    if dest.exists() and dest.stat().st_size:
        return dest
    cache.mkdir(parents=True, exist_ok=True)
    try:
        with urllib.request.urlopen(RCSB_SF.format(pdb_id=pdb_id.upper()), timeout=180) as resp:
            dest.write_bytes(resp.read())
    except urllib.error.HTTPError as exc:
        print(f"  ! no sf file ({exc.code})", file=sys.stderr)
        return None
    return dest


def has_intensities(sf: Path) -> bool:
    """True when the cif declares `_refln.intensity_meas` (not amplitudes only)."""
    with sf.open(errors="ignore") as fh:
        return any(line.startswith("_refln.intensity_meas") for line in fh)


def screen(pdb_ids: list[str]) -> list[str]:
    """Cheap pre-filter: which entries deposited merged intensities?

    Reads only the head of each structure-factor cif (the `_refln` loop header lives
    in the first few KB) instead of downloading files that are useless to this
    benchmark — a large fraction of deposited entries carry amplitudes only.
    """
    eligible = []
    for pdb_id in pdb_ids:
        try:
            with urllib.request.urlopen(RCSB_SF.format(pdb_id=pdb_id.upper()), timeout=60) as resp:
                head = resp.read(16384).decode("utf-8", errors="ignore")
        except urllib.error.HTTPError:
            continue
        if "_refln.intensity_meas" in head:
            eligible.append(pdb_id.upper())
    return eligible


def count_blocks(sf: Path) -> int:
    """Number of `data_` blocks in the sf-cif.

    `cif2mtz` converts the FIRST block only. Both estimators then read that same
    MTZ, so a multi-block entry stays internally consistent — but the row's `d_min`
    would describe whichever block happened to be converted, which may not be the
    dataset the entry's stated resolution refers to. Multi-block entries are skipped
    loudly rather than silently benchmarked on an arbitrary crystal.
    """
    with sf.open(errors="ignore") as fh:
        return sum(1 for line in fh if line.startswith("data_"))


def to_mtz(sf: Path, work: Path) -> tuple[Path, str] | None:
    """cif2mtz the sf file and return (mtz, colin_spec) for the merged intensities."""
    mtz = work / (sf.stem.replace("-sf", "") + ".mtz")
    if not mtz.exists():
        proc = sh(f"cd {work} && cif2mtz hklin {sf} hklout {mtz} <<'EOF'\nEND\nEOF")
        if not mtz.exists():
            print(f"  ! cif2mtz failed: {proc.stdout[-400:]}", file=sys.stderr)
            return None
    dump = sh(f"mtzdump hklin {mtz} <<'EOF'\nEND\nEOF")
    labels = ""
    lines = dump.stdout.splitlines()
    for i, line in enumerate(lines):
        if "Column Labels" in line:
            labels = " ".join(lines[i + 1:i + 4])
            break
    cols = set(labels.split())
    for pair in (("I", "SIGI"), ("IMEAN", "SIGIMEAN"), ("IOBS", "SIGIOBS")):
        if cols.issuperset(pair):
            return mtz, f"{pair[0]},{pair[1]}"
    print(f"  ! no merged intensity columns in MTZ (labels: {labels.strip()})", file=sys.stderr)
    return None


def run_ctruncate(mtz: Path, labels: str, work: Path) -> float | None:
    """Classic Wilson-plot B from ctruncate, on the `labels` intensity columns."""
    log = work / f"ct_{mtz.stem}.log"
    if not log.exists() or not _CT_WILSON.search(log.read_text(errors="ignore")):
        sh(f"cd {work} && ctruncate -hklin {mtz} -hklout {work}/ct_{mtz.stem}.mtz "
           f"-colin '/*/*/[{labels}]' > {log} 2>&1")
    match = _CT_WILSON.search(log.read_text(errors="ignore"))
    return float(match.group(1)) if match else None


def run_xtriage(mtz: Path, labels: str, work: Path) -> dict[str, Any] | None:
    """ML Wilson B, resolution limit and anisotropy spread from phenix.xtriage.

    `obs_labels` is always passed: deposited MTZs routinely carry F, I and their
    anomalous pairs, and xtriage aborts ("Multiple equally suitable arrays") rather
    than choose. Naming the columns also guarantees ctruncate sees the same data.
    """
    log = work / f"xt_{mtz.stem}.log"
    if not log.exists() or not _XT_WILSON.search(log.read_text(errors="ignore")):
        subprocess.run(
            ["bash", "-c", f"cd {work} && {XTRIAGE} {mtz} obs_labels='{labels}' > {log} 2>&1"],
            capture_output=True, text=True, timeout=3600, env=dict(os.environ),
        )
    if not log.exists():
        return None
    text = log.read_text(errors="ignore")
    wilson = _XT_WILSON.search(text)
    if not wilson:
        return None
    reso = _XT_RESO.search(text)
    eigen = [float(v) for v in _XT_EIGEN.findall(text)[:3]]
    return {
        "wilson_b": float(wilson.group(1)),
        "d_max": float(reso.group(1)) if reso else None,
        "d_min": float(reso.group(2)) if reso else None,
        "aniso_delta_b": round(max(eigen) - min(eigen), 2) if len(eigen) == 3 else None,
    }


def collect(pdb_ids: list[str], cache: Path) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    """Run both estimators on every entry that deposited merged intensities."""
    rows: list[dict[str, Any]] = []
    skipped: list[dict[str, str]] = []
    for pdb_id in pdb_ids:
        pdb_id = pdb_id.upper()
        print(f"[{pdb_id}]", file=sys.stderr)
        sf = fetch_sf(pdb_id, cache)
        if sf is None:
            skipped.append({"pdb_id": pdb_id, "reason": "no structure-factor file"})
            continue
        if not has_intensities(sf):
            print("  ! amplitudes only — skipped", file=sys.stderr)
            skipped.append({"pdb_id": pdb_id, "reason": "amplitudes only (no intensity_meas)"})
            continue
        blocks = count_blocks(sf)
        if blocks > 1:
            print(f"  ! {blocks} data blocks — skipped (cif2mtz converts the first only)",
                  file=sys.stderr)
            skipped.append({"pdb_id": pdb_id, "reason": f"multi-block sf-cif ({blocks} blocks)"})
            continue
        converted = to_mtz(sf, cache)
        if converted is None:
            skipped.append({"pdb_id": pdb_id, "reason": "cif2mtz / no merged intensity columns"})
            continue
        mtz, labels = converted
        xt = run_xtriage(mtz, labels, cache)
        ct = run_ctruncate(mtz, labels, cache)
        if xt is None or ct is None:
            print(f"  ! parse failed (xtriage={xt is not None}, ctruncate={ct is not None})",
                  file=sys.stderr)
            skipped.append({"pdb_id": pdb_id, "reason": "estimator failed or unparsable log"})
            continue
        delta = xt["wilson_b"] - ct
        rows.append({
            "pdb_id": pdb_id,
            "d_min": xt["d_min"],
            "aniso_delta_b": xt["aniso_delta_b"],
            "xtriage_ml_wilson_b": round(xt["wilson_b"], 2),
            "ctruncate_wilson_b": round(ct, 2),
            "delta": round(delta, 2),
            "abs_delta": round(abs(delta), 2),
            "rel_delta_pct": round(100.0 * delta / ((xt["wilson_b"] + ct) / 2.0), 2),
        })
        print(f"  d_min {xt['d_min']}  xtriage {xt['wilson_b']:7.2f}  ctruncate {ct:7.2f}"
              f"  Δ {delta:+6.2f}  anisoΔB {xt['aniso_delta_b']}", file=sys.stderr)
    return rows, skipped


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """|Δ| distribution overall and stratified by resolution and anisotropy."""
    if not rows:
        return {"n": 0}

    def stats(subset: list[dict[str, Any]]) -> dict[str, Any]:
        if not subset:
            return {"n": 0}
        absolute = sorted(r["abs_delta"] for r in subset)
        idx = min(len(absolute) - 1, max(0, round(0.9 * (len(absolute) - 1))))
        return {
            "n": len(subset),
            "signed_median": round(statistics.median(r["delta"] for r in subset), 2),
            "abs_median": round(statistics.median(absolute), 2),
            "abs_p90": round(absolute[idx], 2),
            "abs_max": round(absolute[-1], 2),
        }

    def bin_by(pred) -> list[dict[str, Any]]:
        return [r for r in rows if r["d_min"] is not None and pred(r["d_min"])]

    return {
        "overall": stats(rows),
        "by_resolution": {
            "d_min < 1.5 A": stats(bin_by(lambda d: d < 1.5)),
            "1.5-2.5 A": stats(bin_by(lambda d: 1.5 <= d < 2.5)),
            "d_min >= 2.5 A": stats(bin_by(lambda d: d >= 2.5)),
        },
        "by_anisotropy": {
            "delta_B_cart < 5": stats([r for r in rows
                                       if (r["aniso_delta_b"] or 0) < 5]),
            "delta_B_cart >= 5": stats([r for r in rows
                                        if (r["aniso_delta_b"] or 0) >= 5]),
        },
    }


# The 24 datasets the Wilson B tolerance was measured on, committed in round 18.
# Recovered from the per-entry table in `ref/research/tolerance_benchmark_wilson_b.md`,
# which names all 24 with d_min, dB_cart, both estimators and both deltas.
#
# This is NOT the L-test set, despite both rows being measured with the same two tools:
# that benchmark reports n = 27. The extra datasets are unnamed -- see
# `bench_t13_l_test.py`.
DEFAULT_SET = [
    "9PLB", "9ZHM", "9PM1", "9HW2", "9PNX", "12LO", "9LLR", "9PLC", "37AP", "37AS",
    "37BG", "32CR", "30IZ", "28JJ", "28SV", "28JK", "28SZ", "28SX", "31EG", "28SW",
    "9PN7", "9HX9", "9RWI", "9PI0",
]
SET_IS_COMPLETE = True


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("pdb_ids", nargs="*")
    ap.add_argument("--ids-file", help="JSON file: list of IDs, or {bin: [ids]}")
    ap.add_argument("--cache", help="work/download directory (required unless --screen)")
    ap.add_argument("--json", dest="json_out", help="write full results here")
    ap.add_argument("--screen", action="store_true",
                    help="only report which candidates deposited merged intensities")
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
        payload = json.dumps(eligible, indent=1)
        if args.json_out:
            Path(args.json_out).write_text(payload + "\n")
        print(payload)
        return 0 if eligible else 1

    if not args.cache:
        ap.error("--cache is required")
    rows, skipped = collect(ids, Path(args.cache))
    summary = summarize(rows)
    out = {"rows": rows, "skipped": skipped, "summary": summary}
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    return 0 if rows else 1


if __name__ == "__main__":
    raise SystemExit(main())
