#!/usr/bin/env python3
"""Round-9 execution: the ANIS adoption via null re-derivation (#295).

Implements `negative_control_round9_preregistration.md`:

- **J1/X1** — regenerate the 22 null legs (`r9n_`) under the registered
  protocol (phenix.refine, 3 macro cycles, default weights, registered
  array selection, no generated flags) from the durable store; measure the
  two-path deltas and compare against the committed round-3 values.
- **J2/X2/X3** — REFMAC NCYC 0 under BOTH conventions on the deposited
  model and the regenerated null; `d_refmac_anis` by the C1 estimator
  (median + 3·MAD, S_FLOOR, 5 decimals) over the 21 measurable entries
  (9YGW is permanently two-path per the round-8 stand-down).

Resumable: every stage caches by output/log existence, so a relaunch
skips completed entries.

Usage:
    python3 scripts/bench_round9.py --only 4M7G     # canary
    python3 scripts/bench_round9.py                 # full batch
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import statistics
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SET_RECORD = "ref/research/data/negative_control_round2_enrolled.json"
ENROLLED_JSON = REPO / SET_RECORD
R3_BENCH_JSON = REPO / "ref/research/data/negative_control_round3_bench.json"
OUT_JSON = REPO / "ref/research/data/negative_control_round9_anis.json"

PHENIX_BIN = Path.home() / "phenix-2.0-5936" / "phenix_bin"
MAD_FLOOR = 0.0005


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / f"{name}.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


_scr = _load("screen_round1")
_b8 = _load("bench_round8")     # refmac_conv: the both-convention invocation


def regen_null(pdb_id: str, durable: Path, work: Path) -> dict:
    """J1: one entry's null leg — refine, two paths, both REFMAC
    conventions on pre and post."""
    lid = pdb_id.lower()
    model = durable / f"{lid}.pdb"
    cif = durable / f"{lid}.cif"
    mtz = durable / f"{lid}.mtz"
    row: dict = {"pdb_id": pdb_id}
    if not (model.exists() and mtz.exists() and cif.exists()):
        row["status"] = "inputs_missing"
        return row
    row["input_hashes"] = {"model": _scr.sha256_file(model),
                           "mtz": _scr.sha256_file(mtz)}
    pair, flag = _scr.select_arrays(mtz)
    if pair is None:
        row["status"] = "data_defect"
        return row
    row["array_selection"] = {"obs": list(pair), "free_flag": flag}
    prefix = f"r9n_{lid}"
    out = work / f"{prefix}_001.pdb"
    log = work / f"refine_{prefix}.log"
    selectors = f"\"miller_array.labels.name={pair[0]},{pair[1]}\""
    if flag is not None:
        selectors += f" \"miller_array.labels.name={flag}\""
    if not out.exists():
        subprocess.run(
            ["bash", "-c",
             f"cd {work} && {PHENIX_BIN / 'phenix.refine'} {model} {mtz} "
             f"main.number_of_macro_cycles=3 {selectors} "
             f"output.prefix={prefix} --overwrite > {log} 2>&1"],
            capture_output=True, text=True, timeout=10800, env=dict(os.environ))
    if not out.exists():
        tail = log.read_text(errors="ignore").strip().splitlines()[-3:] \
            if log.exists() else []
        row["status"] = "refine_failed"
        row["log_tail"] = tail
        return row
    # ADP form of the regenerated model (J1 records it per entry).
    row["refined_has_aniso"] = "ANISOU" in out.read_text(errors="ignore")[:2_000_000]
    # Two paths, pre and post.
    paths = {}
    for name, fn in (("phenix", _scr.model_vs_data_rfree),
                     ("gemmi", _scr.gemmi_rfree)):
        pre = fn(model, mtz, work, f"{name}_r9_{lid}_pre", pair, flag)
        post = fn(out, mtz, work, f"{name}_{prefix}", pair, flag)
        paths[name] = {"pre": pre, "post": post,
                       "delta": round(post - pre, 5)
                       if pre is not None and post is not None else None}
    row["paths"] = paths
    # REFMAC, both conventions: deposited as mmCIF, refined as phenix PDB
    # (the canaried input rule).
    if pdb_id != "9YGW":
        refmac = {}
        for conv, anis in (("isot", False), ("anis", True)):
            pre = _b8.refmac_conv(cif, mtz, work, f"r9_{lid}_pre_{conv}",
                                  pair, flag, anis=anis)
            post = _b8.refmac_conv(out, mtz, work, f"r9_{lid}_post_{conv}",
                                   pair, flag, anis=anis)
            refmac[conv] = {"pre": pre, "post": post,
                            "delta": round(post - pre, 5)
                            if pre is not None and post is not None else None}
        row["refmac"] = refmac
    else:
        row["refmac"] = {"standing": "two-path permanent (round-8 stand-down)"}
    row["status"] = "regenerated"
    return row


def derive_threshold(deltas: list[float]) -> float:
    med = statistics.median(deltas)
    mad = max(statistics.median(abs(v - med) for v in deltas), MAD_FLOOR)
    return round(med + 3 * mad, 5)


def main() -> int:
    from benchmark_environment import announce_benchmark_environment

    announce_benchmark_environment()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--durable",
                    default=str(Path.home() / "protstruct_bench_inputs"))
    ap.add_argument("--work", default="/tmp/nc_round9_work")
    ap.add_argument("--only", default="", help="comma-separated pdb ids")
    args = ap.parse_args()
    durable, work = Path(args.durable), Path(args.work)
    work.mkdir(parents=True, exist_ok=True)

    entries = [e["pdb_id"].upper()
               for e in json.loads(ENROLLED_JSON.read_text())["entries"]]
    if args.only:
        keep = {x.strip().upper() for x in args.only.split(",")}
        entries = [e for e in entries if e in keep]

    rows = []
    for pid in entries:
        row = regen_null(pid, durable, work)
        rows.append(row)
        print(f"  {pid}: {row['status']} "
              f"paths={ {k: v.get('delta') for k, v in row.get('paths', {}).items()} } "
              f"refmac={ {k: v.get('delta') for k, v in row.get('refmac', {}).items() if isinstance(v, dict)} }",
              file=sys.stderr)

    # X1: reproduction of the committed round-3 two-path deltas.
    committed = {r["pdb_id"]: r["numbers"]
                 for r in json.loads(R3_BENCH_JSON.read_text())["rows"]
                 if r["subject"] == "null" and r["status"] == "benched"}
    x1 = []
    for row in rows:
        if row["status"] != "regenerated" or row["pdb_id"] not in committed:
            continue
        old = committed[row["pdb_id"]]
        ent = {"pdb_id": row["pdb_id"]}
        for p, key in (("phenix", "d_phenix"), ("gemmi", "d_gemmi")):
            new = row["paths"][p]["delta"]
            ent[f"{key}_regen"] = new
            ent[f"{key}_committed"] = old[key]
            ent[f"{key}_absdiff"] = (round(abs(new - old[key]), 5)
                                     if new is not None and old[key] is not None
                                     else None)
        x1.append(ent)
    x1_pass = sum(1 for e in x1
                  if e["d_phenix_absdiff"] is not None
                  and e["d_phenix_absdiff"] <= 0.002
                  and e["d_gemmi_absdiff"] is not None
                  and e["d_gemmi_absdiff"] <= 0.002)

    # J2: the ANIS null distribution and threshold (+ ISOT re-derived on the
    # same regenerated models, reported for comparison only).
    anis_deltas = [r["refmac"]["anis"]["delta"] for r in rows
                   if isinstance(r.get("refmac"), dict)
                   and isinstance(r["refmac"].get("anis"), dict)
                   and r["refmac"]["anis"]["delta"] is not None]
    isot_deltas = [r["refmac"]["isot"]["delta"] for r in rows
                   if isinstance(r.get("refmac"), dict)
                   and isinstance(r["refmac"].get("isot"), dict)
                   and r["refmac"]["isot"]["delta"] is not None]

    # X3: direction agreement on the shared-sign population (#380).
    def sign_counts(conv: str) -> tuple[int, int, int]:
        agree = pop = excluded = 0
        for r in rows:
            if r["status"] != "regenerated" or not isinstance(r.get("refmac"), dict):
                continue
            rc = r["refmac"].get(conv)
            if not isinstance(rc, dict) or rc.get("delta") is None:
                continue
            dp = r["paths"]["phenix"]["delta"]
            dg = r["paths"]["gemmi"]["delta"]
            if dp is None or dg is None or (dp >= 0) != (dg >= 0):
                excluded += 1
                continue
            pop += 1
            if (rc["delta"] >= 0) == (dp >= 0):
                agree += 1
        return agree, pop, excluded

    x3_anis = sign_counts("anis")
    x3_isot = sign_counts("isot")

    report = {
        "run": {"preregistration": "negative_control_round9_preregistration.md",
                "round": 9, "durable_store": str(durable),
                "tools": _scr.tool_versions()},
        "rows": rows,
        "x1_reproduction": {"entries": x1, "n_within_0p002_both_paths": x1_pass},
        "j2_anis": {
            "n": len(anis_deltas),
            "median_abs_delta": round(statistics.median(
                abs(d) for d in anis_deltas), 5) if anis_deltas else None,
            "d_refmac_anis": derive_threshold(anis_deltas) if anis_deltas else None,
            "isot_rederived_for_comparison_only":
                derive_threshold(isot_deltas) if isot_deltas else None,
        },
        "x3_direction_agreement": {
            "anis": {"agree": x3_anis[0], "population": x3_anis[1],
                     "excluded_sign_split": x3_anis[2]},
            "isot": {"agree": x3_isot[0], "population": x3_isot[1],
                     "excluded_sign_split": x3_isot[2]},
        },
    }
    if not args.only:
        _scr.write_json_atomic(OUT_JSON, report)
    print(json.dumps({
        "regenerated": sum(1 for r in rows if r["status"] == "regenerated"),
        "x1_within": x1_pass,
        "j2": report["j2_anis"],
        "x3": report["x3_direction_agreement"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
