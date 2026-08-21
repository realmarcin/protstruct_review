#!/usr/bin/env python3
"""Round-8 execution: the round-7 closeout (#295).

Implements `negative_control_round8_preregistration.md`:

- **I3/W4 first** — the 9YGW PDB-form experiment (ANISOU records carry no
  residue-name join), so the census knows whether 9YGW is in it.
- **I1/W1/W2** — the `REFI BREF ANIS` census: REFMAC NCYC 0 on every
  measurable deposited model under BOTH conventions. Census only — the
  registered no-mixing rule keeps ANIS out of every verdict-bearing
  invocation until a registered round re-derives d_refmac under it.
- **I2/W3** — the 11-entry wavelength patch, PROOF-ONLY by default: the
  patched candidate is built beside the store and fingerprint-proved; the
  store write itself (write=True) additionally requires the user's
  explicit in-conversation go-ahead, per the registered gating.

Usage:
    python3 scripts/bench_round8.py                 # census + I3 + proofs
    python3 scripts/bench_round8.py --census-only 2VXN   # one-entry canary
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SET_RECORD = "ref/research/data/negative_control_round2_enrolled.json"
ENROLLED_JSON = REPO / SET_RECORD
R7_JSON = REPO / "ref/research/data/negative_control_round7_attribution.json"
OUT_JSON = REPO / "ref/research/data/negative_control_round8_closeout.json"

CCP4_SETUP = "/Applications/ccp4-9.0.015-shelx-arpwarp-macosarm/ccp4-9/bin/ccp4.setup-sh"

# I2, registered: |staged - deposition| < 1e-3 is agreement (#375).
WL_AGREE_TOL = 1e-3


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / f"{name}.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


_scr = _load("screen_round1")
_bnc = _load("bench_negative_control")
_b6 = _load("bench_round6")


def refmac_conv(model: Path, mtz: Path, work: Path, tag: str,
                pair, flag, anis: bool) -> float | None:
    """REFMAC NCYC 0 under one ADP convention; returns R-free or None."""
    log = work / f"refmac_{tag}.log"
    if not (log.exists()
            and _bnc._REFMAC_FREE.search(log.read_text(errors="ignore"))):
        kw = "REFI BREF ANIS\n" if anis else ""
        subprocess.run(
            ["bash", "-c",
             f"source {CCP4_SETUP} 2>/dev/null && cd {work} && "
             f"refmac5 XYZIN {model} HKLIN {mtz} XYZOUT rc_{tag}.pdb "
             f"HKLOUT rc_{tag}.mtz > {log} 2>&1 <<EOF\n"
             f"MAKE NEWLIGAND CONTINUE\n{kw}"
             f"LABIN FP={pair[0]} SIGFP={pair[1]} FREE={flag}\n"
             f"NCYC 0\nEND\nEOF"],
            capture_output=True, text=True, timeout=1800, env=dict(os.environ))
    text = log.read_text(errors="ignore") if log.exists() else ""
    m = _bnc._REFMAC_FREE.search(text)
    return float(m.group(1)) if m else None


# --- I3: the 9YGW PDB-form experiment ----------------------------------------------

def i3_9ygw(durable: Path, work: Path) -> dict:
    pdb = durable / "9ygw.pdb"
    mtz = durable / "9ygw.mtz"
    rec: dict = {"input_form": "deposited PDB (ANISOU carries no comp join)",
                 "input_hashes": {"model": _scr.sha256_file(pdb),
                                  "mtz": _scr.sha256_file(mtz)}}
    pair, flag = _scr.select_arrays(mtz)
    r = refmac_conv(pdb, mtz, work, "r8i3_9ygw_isot", pair, flag, anis=False)
    rec["refmac_isot_r_free"] = r
    rec["measurable"] = r is not None
    if r is None:
        log = work / "refmac_r8i3_9ygw_isot.log"
        text = log.read_text(errors="ignore") if log.exists() else ""
        rec["diagnostic_lines"] = [
            l.strip() for l in text.splitlines()
            if "aniso" in l.lower() or "error" in l.lower()
            or "Problem" in l or "mismatch" in l.lower()][-6:]
        rec["outcome"] = ("STOOD DOWN to permanent two-path status by the "
                         "round-8 registration — no further repair attempts "
                         "without a new registered mechanism")
    else:
        rec["outcome"] = ("named per-entry input-form exception: mmCIF "
                          "default, PDB form for 9YGW, recorded in every "
                          "future row that uses it")
    return rec


# --- I1: the both-convention census ------------------------------------------------

def census(durable: Path, work: Path, include_9ygw: bool) -> dict:
    out = {}
    for e in json.loads(ENROLLED_JSON.read_text())["entries"]:
        pid = e["pdb_id"].upper()
        lid = pid.lower()
        mtz = durable / f"{lid}.mtz"
        model = durable / (f"{lid}.pdb" if pid == "9YGW" else f"{lid}.cif")
        if pid == "9YGW" and not include_9ygw:
            out[pid] = {"census": "excluded (I3 did not unlock)"}
            continue
        pair, flag = _scr.select_arrays(mtz)
        isot = refmac_conv(model, mtz, work, f"r8c_{lid}_isot", pair, flag,
                           anis=False)
        anis = refmac_conv(model, mtz, work, f"r8c_{lid}_anis", pair, flag,
                           anis=True)
        out[pid] = {"r_free_isot": isot, "r_free_anis": anis,
                    "delta_anis_minus_isot":
                        round(anis - isot, 5) if isot is not None
                        and anis is not None else None}
    return out


# --- I2: the wavelength patch behind its proof gate --------------------------------

def deposition_wavelength(cif: Path) -> float | None:
    m = re.search(r"_diffrn_radiation_wavelength\.wavelength\s+([\d.]+)",
                  cif.read_text(errors="ignore"))
    return float(m.group(1)) if m else None


def patch_entry(pdb_id: str, durable: Path, work: Path,
                staged_wl: float, write: bool = False) -> dict:
    """Build the patched candidate beside the store and prove it; the store
    write (write=True) additionally requires the user's explicit
    in-conversation go-ahead, per the registered I2 gating."""
    import gemmi
    lid = pdb_id.lower()
    store = durable / f"{lid}.mtz"
    rec: dict = {"pdb_id": pdb_id}
    dep_wl = deposition_wavelength(durable / f"{lid}.cif")
    if dep_wl is None:
        rec["status"] = "no_deposition_wavelength_store_untouched"
        return rec
    rec["deposition_wavelength"] = dep_wl
    rec["staged_crosscheck"] = {
        "staged": staged_wl,
        "agrees": abs(dep_wl - staged_wl) < WL_AGREE_TOL,
    }
    pre_fp = _b6.obs_fingerprint(store)
    cand = work / f"patched_{lid}.mtz"
    m = gemmi.read_mtz_file(str(store))
    # The stripped files carry a single dataset whose id is 0 — an
    # "id != 0 skips HKL_base" guard would skip the only dataset (the
    # canary caught exactly that). Set every dataset; the files have one.
    for ds in m.datasets:
        ds.wavelength = dep_wl
    m.write_to_file(str(cand))
    post_fp = _b6.obs_fingerprint(cand)
    rec["fingerprints_identical"] = (pre_fp == post_fp)
    back = gemmi.read_mtz_file(str(cand))
    got_wl = back.datasets[-1].wavelength if back.datasets else 0.0
    rec["patched_wavelength"] = round(got_wl, 6)
    ok = (rec["fingerprints_identical"]
          and abs(got_wl - dep_wl) < 1e-6)
    if not ok:
        rec["status"] = "proof_failed_store_untouched"
        return rec
    if not write:
        rec["status"] = "proof_ok_awaiting_user_go_ahead"
        return rec
    store.write_bytes(cand.read_bytes())
    sidecar = store.with_suffix(".mtz.sha256")
    sidecar.write_text(_scr.sha256_file(store) + "\n")
    rec["rebaseline_ruling"] = ("negative_control_round8_preregistration.md "
                                "I2 + the user's explicit in-conversation "
                                "go-ahead; proof: KEEP fingerprints identical, "
                                "deposition wavelength")
    rec["input_hashes"] = {"mtz": _scr.sha256_file(store)}
    rec["status"] = "patched"
    return rec


def main() -> int:
    from benchmark_environment import announce_benchmark_environment

    announce_benchmark_environment()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--durable",
                    default=str(Path.home() / "protstruct_bench_inputs"))
    ap.add_argument("--work", default="/tmp/nc_round8_work")
    ap.add_argument("--census-only", default="",
                    help="run the census for this one entry only, then stop")
    args = ap.parse_args()
    durable, work = Path(args.durable), Path(args.work)
    work.mkdir(parents=True, exist_ok=True)

    if args.census_only:
        lid = args.census_only.lower()
        mtz = durable / f"{lid}.mtz"
        pair, flag = _scr.select_arrays(mtz)
        model = durable / f"{lid}.cif"
        isot = refmac_conv(model, mtz, work, f"r8c_{lid}_isot", pair, flag, False)
        anis = refmac_conv(model, mtz, work, f"r8c_{lid}_anis", pair, flag, True)
        print(json.dumps({"isot": isot, "anis": anis}, indent=2))
        return 0

    print("== I3: 9YGW PDB form ==", file=sys.stderr)
    i3 = i3_9ygw(durable, work)
    print(f"  measurable={i3['measurable']} r_free={i3.get('refmac_isot_r_free')}",
          file=sys.stderr)

    print("== I1: both-convention census ==", file=sys.stderr)
    cen = census(durable, work, include_9ygw=i3["measurable"])
    for pid, row in sorted(cen.items()):
        print(f"  {pid}: {row}", file=sys.stderr)

    print("== I2: patch proofs (write gated) ==", file=sys.stderr)
    r7 = json.loads(R7_JSON.read_text())
    staged = {r["pdb_id"]: r["staged_wavelength"] for r in r7["h4_remediation"]
              if r["status"] == "proof_failed_store_untouched"}
    patches = [patch_entry(pid, durable, work, wl)
               for pid, wl in sorted(staged.items())]
    for r in patches:
        print(f"  {r['pdb_id']}: {r['status']} dep_wl="
              f"{r.get('deposition_wavelength')}", file=sys.stderr)

    deltas = [row["delta_anis_minus_isot"] for row in cen.values()
              if isinstance(row, dict) and row.get("delta_anis_minus_isot")
              is not None]
    import statistics
    report = {
        "run": {"preregistration": "negative_control_round8_preregistration.md",
                "round": 8, "durable_store": str(durable),
                "tools": _scr.tool_versions()},
        "i3_9ygw_pdb_form": i3,
        "i1_census": cen,
        "i1_summary": {
            "n_census": len(deltas),
            "n_anis_lower": sum(1 for d in deltas if d < 0),
            "median_delta": round(statistics.median(deltas), 5) if deltas else None,
            "n_abs_delta_over_d_refmac":
                sum(1 for d in deltas if abs(d) > 0.00560),
        },
        "i2_patch_proofs": patches,
    }
    _scr.write_json_atomic(OUT_JSON, report)
    print(json.dumps({
        "i3_measurable": i3["measurable"],
        "census": report["i1_summary"],
        "patch_proofs_ok": sum(1 for r in patches
                               if r["status"] == "proof_ok_awaiting_user_go_ahead"),
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
