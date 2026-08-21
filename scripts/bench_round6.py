#!/usr/bin/env python3
"""Round-6 execution: the data-hygiene round (#295).

Implements `negative_control_round6_preregistration.md`:

- **G1/U1** — migrate the input store to the durable path, strip each entry
  under the three-class rule, verify observation identity per entry, write
  fresh first-sight sidecars (the STRIPPED file is the canonical input from
  here on; a new store's first-sight hash is not a re-baseline).
- **G3/U4** — 8R5K clean null re-screen (`r6n_` prefix, stripped data).
- **U2** — REFMAC measurability on the three previously unmeasurable
  entries under the G5 amendments.
- **U3** — recompute the C1 null-centered table with the clean 8R5K null
  substituted; disclose any movement at 5-decimal precision.
- **G4** — the 2VXN record: step 1 (flag census — refuted), steps 2–3
  (controlled REFMAC variants; Servalcat discriminator).

Usage:
    python3 scripts/bench_round6.py
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import statistics
import sys
from pathlib import Path

if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
from toolchain import phenix, run_logged, run_refmac

REPO = Path(__file__).resolve().parent.parent
SET_RECORD = "ref/research/data/negative_control_round2_enrolled.json"
ENROLLED_JSON = REPO / SET_RECORD
R3_BENCH_JSON = REPO / "ref/research/data/negative_control_round3_bench.json"
OUT_JSON = REPO / "ref/research/data/negative_control_round6_hygiene.json"

OLD_CACHE = Path("/tmp/nc_round1_cache")
def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / f"{name}.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


_scr = _load("screen_round1")
_bnc = _load("bench_negative_control")
_brl = _load("bench_recover_leg")
_gr = _load("gemmi_rfactor")


def obs_fingerprint(mtz: Path) -> dict:
    """Per-column SHA of the KEEP data — the U1 identity instrument."""
    import gemmi
    import numpy as np
    import hashlib
    m = gemmi.read_mtz_file(str(mtz))
    data = np.array(m, copy=False)
    out = {}
    for i, c in enumerate(m.columns):
        if _scr.classify_column(c.label) == "keep":
            col = data[:, i].astype(np.float32).tobytes()
            out[c.label] = hashlib.sha256(col).hexdigest()[:16]
    return out


def migrate_entry(pdb_id: str, durable: Path) -> dict:
    """Copy from the old /tmp cache (or refetch), strip, verify, sidecar."""
    rec: dict = {"pdb_id": pdb_id}
    durable.mkdir(parents=True, exist_ok=True)
    lid = pdb_id.lower()
    src_mtz = OLD_CACHE / f"{lid}.mtz"
    dst_mtz = durable / f"{lid}.mtz"
    for ext in (".pdb", ".cif", "_validation.xml"):
        s, d = OLD_CACHE / f"{lid}{ext}", durable / f"{lid}{ext}"
        if s.exists() and not d.exists():
            d.write_bytes(s.read_bytes())
    if not dst_mtz.exists():
        if src_mtz.exists():
            dst_mtz.write_bytes(src_mtz.read_bytes())
        else:
            model, mtz, err = _scr.fetch_pair(pdb_id, durable)
            if err:
                rec["status"] = "fetch_failed"
                rec["reason"] = err
                return rec
    pre_fp = obs_fingerprint(dst_mtz)
    dropped = _scr.strip_mtz(dst_mtz)
    post_fp = obs_fingerprint(dst_mtz)
    rec["dropped_columns"] = dropped
    rec["obs_identity_preserved"] = (pre_fp == post_fp)
    rec["n_obs_columns"] = len(post_fp)
    sidecar = dst_mtz.with_suffix(".mtz.sha256")
    sidecar.write_text(_scr.sha256_file(dst_mtz) + "\n")   # first sight of the new store
    rec["input_hashes"] = {"mtz": _scr.sha256_file(dst_mtz)}
    rec["status"] = "migrated"
    return rec


def rescreen_8r5k(durable: Path, work: Path, thresholds: dict) -> dict:
    """G3: the clean null re-screen on stripped data, r6n_ prefix."""
    model = durable / "8r5k.pdb"
    mtz = durable / "8r5k.mtz"
    pair, flag = _scr.select_arrays(mtz)
    prefix = "r6n_8r5k"
    out = work / f"{prefix}_001.pdb"
    log = work / f"refine_{prefix}.log"
    selectors = [f"miller_array.labels.name={pair[0]},{pair[1]}"]
    if flag is not None:
        selectors.append(f"miller_array.labels.name={flag}")
    if not out.exists():
        run_logged(
            [phenix("phenix.refine"), model, mtz, "main.number_of_macro_cycles=3",
             *selectors, f"output.prefix={prefix}", "--overwrite"],
            log, cwd=work, timeout=10800,
        )
    if not out.exists():
        return {"status": "refine_failed"}
    rec: dict = {"status": "screened", "array_selection": {"obs": list(pair),
                                                           "free_flag": flag}}
    rec["input_hashes"] = {"model": _scr.sha256_file(model),
                          "mtz": _scr.sha256_file(mtz)}
    deltas = {}
    for name, fn in (("phenix", _scr.model_vs_data_rfree), ("gemmi", _scr.gemmi_rfree)):
        pre = fn(model, mtz, work, f"{name}_r6_8r5k_pre", pair, flag)
        post = fn(out, mtz, work, f"{name}_{out.stem}", pair, flag)
        deltas[name] = {"pre": pre, "post": post,
                        "delta": post - pre if pre is not None and post is not None
                        else None}
    ref_pre = _bnc.refmac_pass(durable / "8r5k.cif", mtz, work, "r6_8r5k_pre",
                               pair, flag)
    ref_post = _bnc.refmac_pass(out, mtz, work, "r6_8r5k_post", pair, flag)
    deltas["refmac"] = {"pre": ref_pre["r_free"] if ref_pre else None,
                        "post": ref_post["r_free"] if ref_post else None,
                        "delta": ref_post["r_free"] - ref_pre["r_free"]
                        if ref_pre and ref_post else None}
    rec["paths"] = deltas
    n = {"d_phenix": deltas["phenix"]["delta"], "d_gemmi": deltas["gemmi"]["delta"],
         "d_refmac": deltas["refmac"]["delta"]}
    rec["clean_null_deltas"] = n
    # E1: enrolls iff no fit degradation under the registered thresholds
    fit = all(n[t] is not None and n[t] > thresholds[t] for t in thresholds) \
        if n["d_refmac"] is not None else \
        all(n[t] is not None and n[t] > thresholds[t]
            for t in ("d_phenix", "d_gemmi"))
    improvement = (n["d_phenix"] is not None and n["d_gemmi"] is not None
                   and n["d_phenix"] < -3 * 0.00275 and n["d_gemmi"] < -3 * 0.0026)
    rec["fit_degraded_e1"] = fit
    rec["headroom_improvement"] = improvement
    rec["enrolls_clean"] = not fit and not improvement
    return rec


def recompute_c1(clean_8r5k: dict | None) -> dict:
    """U3: the C1 table with the clean 8R5K null substituted."""
    d = json.loads(R3_BENCH_JSON.read_text())
    nulls = [r for r in d["rows"] if r["subject"] == "null"
             and r["status"] == "benched"]
    out = {}
    for tool in ("d_phenix", "d_gemmi", "d_refmac"):
        vals = []
        for r in nulls:
            v = r["numbers"][tool]
            if r["pdb_id"] == "8R5K":
                v = clean_8r5k.get(tool) if clean_8r5k else v
            if v is not None:
                vals.append(v)
        med = statistics.median(vals)
        mad = max(statistics.median(abs(v - med) for v in vals), 0.0005)
        out[tool] = round(med + 3 * mad, 5)
    return out


def refmac_u2(durable: Path, work: Path) -> dict:
    """U2: measurability of the previously unmeasurable trio under G5."""
    out = {}
    for pid in ("8R5K", "9YGW", "8QXQ"):
        lid = pid.lower()
        mtz = durable / f"{lid}.mtz"
        cif = durable / f"{lid}.cif"
        if not (mtz.exists() and cif.exists()):
            out[pid] = {"measurable": False, "reason": "inputs missing"}
            continue
        pair, flag = _scr.select_arrays(mtz)
        res = _bnc.refmac_pass(cif, mtz, work, f"r6u2_{lid}", pair, flag)
        out[pid] = ({"measurable": True, "r_free": res["r_free"]}
                    if res else {"measurable": False, "reason": "no parsed R"})
    return out


def investigate_2vxn(durable: Path, work: Path) -> dict:
    """G4 steps 2-3 on 2VXN (step 1, the flag census, refuted the convention
    hypothesis — every enrolled entry marks its test set with flag 0)."""
    rec: dict = {"step1_flag_convention": {
        "result": "REFUTED as cause — all 22 entries use flag 0 as the test "
                  "set, matching REFMAC's default (census 2026-08-17)"}}
    lid = "2vxn"
    mtz = durable / f"{lid}.mtz"
    cif = durable / f"{lid}.cif"
    pair, flag = _scr.select_arrays(mtz)
    # step 2: controlled REFMAC variants, one change at a time
    variants = {
        "standard": "",
        "simple_scaling": "SCALE TYPE SIMPLE\n",
        "no_solvent": "SOLVENT NO\n",
    }
    step2 = {}
    for name, extra in variants.items():
        log = work / f"refmac_2vxn_{name}.log"
        keywords = (f"MAKE NEWLIGAND CONTINUE\n{extra}"
                    f"LABIN FP={pair[0]} SIGFP={pair[1]} FREE={flag}\n"
                    "NCYC 0\nEND\n")
        run_refmac(cif, mtz, f"rv_{name}.pdb", f"rv_{name}.mtz", log,
                   keywords, cwd=work)
        text = log.read_text(errors="ignore") if log.exists() else ""
        m = _bnc._REFMAC_FREE.search(text)
        step2[name] = float(m.group(1)) if m else None
    rec["step2_refmac_variants_r_free"] = step2
    # step 3: Servalcat discriminator, NCYC 0 equivalent
    slog = work / "servalcat_2vxn.log"
    run_logged(
        ["servalcat", "refine_xtal_norefmac", "-s", "xray", "--model", cif,
         "--hklin", mtz, "--labin", f"{pair[0]},{pair[1]},{flag}",
         "--ncycle", "0", "-o", "serval_2vxn"],
        slog, cwd=work, timeout=3600, ccp4=True,
    )
    stext = slog.read_text(errors="ignore") if slog.exists() else ""
    import re
    # `Rwork = ... Rfree = ...` is the summary line; a loose last-match
    # regex lands on the stats table's Ncyc row and reads 0 (round-7 find).
    sm = re.findall(r"Rfree\s*=\s*([\d.]+)", stext)
    rec["step3_servalcat_r_free"] = float(sm[-1]) if sm else None
    rec["step3_log_tail"] = stext.strip().splitlines()[-3:] if stext else []
    return rec


def main() -> int:
    from benchmark_environment import announce_benchmark_environment

    announce_benchmark_environment()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--durable",
                    default=str(Path.home() / "protstruct_bench_inputs"))
    ap.add_argument("--work", default="/tmp/nc_round1_work")
    args = ap.parse_args()
    durable, work = Path(args.durable), Path(args.work)
    work.mkdir(parents=True, exist_ok=True)

    thresholds = _brl.fit_thresholds_from_record()
    enrolled = json.loads(ENROLLED_JSON.read_text())["entries"]

    print("== G1/U1: migrate + strip + verify ==", file=sys.stderr)
    migration = []
    for e in enrolled:
        rec = migrate_entry(e["pdb_id"].upper(), durable)
        migration.append(rec)
        print(f"  {rec['pdb_id']}: {rec['status']} "
              f"dropped={len(rec.get('dropped_columns', []))} "
              f"obs_ok={rec.get('obs_identity_preserved')}", file=sys.stderr)

    print("== G3/U4: 8R5K clean re-screen ==", file=sys.stderr)
    r8 = rescreen_8r5k(durable, work, thresholds)
    print(f"  8R5K: {r8.get('status')} deltas={r8.get('clean_null_deltas')} "
          f"enrolls={r8.get('enrolls_clean')}", file=sys.stderr)

    print("== U3: C1 recomputation ==", file=sys.stderr)
    c1_new = recompute_c1(r8.get("clean_null_deltas"))
    c1_moved = c1_new != _brl.REGISTERED_FIT_THRESHOLDS

    print("== U2: REFMAC measurability ==", file=sys.stderr)
    u2 = refmac_u2(durable, work)

    print("== G4: 2VXN ==", file=sys.stderr)
    g4 = investigate_2vxn(durable, work)

    report = {
        "run": {"preregistration": "negative_control_round6_preregistration.md",
                "round": 6, "durable_store": str(durable),
                "tools": _scr.tool_versions()},
        "migration": migration,
        "u1_all_preserved": all(r.get("obs_identity_preserved") for r in migration
                                if r["status"] == "migrated"),
        "g3_8r5k_rescreen": r8,
        "u3_c1_recomputed": {"table": c1_new,
                             "registered": _brl.REGISTERED_FIT_THRESHOLDS,
                             "moved": c1_moved},
        "u2_refmac_measurability": u2,
        "g4_2vxn": g4,
    }
    _scr.write_json_atomic(OUT_JSON, report)
    print(json.dumps({"u1_all_preserved": report["u1_all_preserved"],
                      "8r5k_enrolls": r8.get("enrolls_clean"),
                      "c1_moved": c1_moved,
                      "u2": {k: v.get("measurable") for k, v in u2.items()},
                      "servalcat_r_free": g4.get("step3_servalcat_r_free")},
                     indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
