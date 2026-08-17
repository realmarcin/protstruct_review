#!/usr/bin/env python3
"""Round-7 execution: re-registration fallout + attribution (#295).

Implements `negative_control_round7_preregistration.md`:

- **H1/V1** — flip-disclosure sweep: every committed round-4/5 verdict
  recomputed under the re-registered C1 table; any flip disclosed by entry
  and round. Round-3 verdicts are flag-based (the C1 table postdates them)
  and cannot flip by construction — recorded as such.
- **H2/V2** — the 2VXN experiment ladder, one change at a time: the
  iso-only derived model against all four tools, the resolution-range log
  audit, the demoted hydrogen bound (`MAKE HYDR N`).
- **H3/V3** — the 9YGW metadata-only aniso repair (CYS -> CSO on the
  anisotrop rows of the CSO atoms only), then REFMAC on the derived file.
- **H4/V4** — store remediation behind the proof gate: staging re-fetch,
  per-column KEEP fingerprints must match the current store file exactly
  before any replacement; sidecar re-baselines cite prereg H4 by name.
- Census: REFMAC measurability over all 22 entries after H3.

Usage:
    python3 scripts/bench_round7.py --h4-canary 7R2H   # one-entry H4 proof
    python3 scripts/bench_round7.py                    # the full round
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
R4_JSON = REPO / "ref/research/data/negative_control_round4_recover.json"
R5_JSON = REPO / "ref/research/data/negative_control_round5_recover.json"
R6_JSON = REPO / "ref/research/data/negative_control_round6_hygiene.json"
OUT_JSON = REPO / "ref/research/data/negative_control_round7_attribution.json"

CCP4_SETUP = "/Applications/ccp4-9.0.015-shelx-arpwarp-macosarm/ccp4-9/bin/ccp4.setup-sh"

# The superseded round-4 table, kept here ONLY as the sweep's "old" side —
# 0.01220/0.01090/0.00540 were the registered values before round-7 H1.
OLD_FIT_THRESHOLDS = {"d_phenix": 0.01220, "d_gemmi": 0.01090,
                      "d_refmac": 0.00540}


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / f"{name}.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


_scr = _load("screen_round1")
_bnc = _load("bench_negative_control")
_brl = _load("bench_recover_leg")
_br5 = _load("bench_round5")
_b6 = _load("bench_round6")


# --- H1: the flip-disclosure sweep --------------------------------------------------

def sweep_h1(new: dict) -> dict:
    """Recompute every round-4/5 verdict under old and new tables; disclose
    flips. Uses each round's own fit function (round 4: None-fallback
    `fit_degraded`; round 5: `e1_fit_degraded`) — the sweep must apply the
    rule each verdict was committed under."""
    flips = []
    checked = 0
    for path, round_no, fit_fn in ((R4_JSON, 4, _brl.fit_degraded),
                                   (R5_JSON, 5, _br5.e1_fit_degraded)):
        rows = json.loads(path.read_text())["rows"]
        for r in rows:
            rec = r.get("recovered") or {}
            numbers = rec.get("numbers")
            if not numbers or rec.get("status") != "judged":
                continue
            checked += 1
            entry = {"round": round_no, "pdb_id": r["pdb_id"],
                     "subject": r.get("subject")}
            old_fit = fit_fn(numbers, OLD_FIT_THRESHOLDS)
            new_fit = fit_fn(numbers, new)
            if old_fit != new_fit:
                flips.append({**entry, "field": "fit_degraded",
                              "old": old_fit, "new": new_fit,
                              "numbers": {t: numbers.get(t) for t in new}})
            old_v = _brl.combined_verdict(rec.get("flags", {}), numbers,
                                          OLD_FIT_THRESHOLDS)
            new_v = _brl.combined_verdict(rec.get("flags", {}), numbers, new)
            if old_v != new_v:
                flips.append({**entry, "field": "verdict",
                              "old": old_v, "new": new_v})
            if round_no == 5:
                success = bool(r.get("recovery_success"))
                old_w4 = _br5.w4_contradiction({"numbers": numbers},
                                               OLD_FIT_THRESHOLDS, success)
                new_w4 = _br5.w4_contradiction({"numbers": numbers}, new, success)
                if old_w4 != new_w4:
                    flips.append({**entry, "field": "w4_contradiction",
                                  "old": old_w4, "new": new_w4})
    return {"old_table": OLD_FIT_THRESHOLDS, "new_table": new,
            "rows_checked": checked, "flips": flips,
            "round3_note": ("round-3 verdicts are flag-based; the C1 table "
                            "postdates them — no flip is possible by "
                            "construction")}


# --- H2: the 2VXN experiment ladder -------------------------------------------------

def derive_iso_only(cif: Path, out_cif: Path) -> dict:
    """Experiment-1 input: every aniso tensor zeroed, B_iso/coordinates/
    occupancies untouched. Returns the derivation summary."""
    import gemmi
    st = gemmi.read_structure(str(cif))
    st.setup_entities()
    n = 0
    for model in st:
        for chain in model:
            for res in chain:
                for atom in res:
                    if atom.aniso.nonzero():
                        atom.aniso = gemmi.SMat33f(0, 0, 0, 0, 0, 0)
                        n += 1
    st.make_mmcif_document().write_file(str(out_cif))
    return {"n_aniso_zeroed": n, "derived": out_cif.name,
            "sha256": _scr.sha256_file(out_cif)}


def measure_four_tools(model: Path, mtz: Path, work: Path, tag: str,
                       pair, flag) -> dict:
    """One model against all four tools (NCYC-0 / zero-cycle everywhere)."""
    out = {}
    out["phenix_mvd"] = _scr.model_vs_data_rfree(model, mtz, work,
                                                 f"mvd_{tag}", pair, flag)
    out["gemmi_path"] = _scr.gemmi_rfree(model, mtz, work,
                                         f"gemmi_{tag}", pair, flag)
    ref = _bnc.refmac_pass(model, mtz, work, f"refmac_{tag}", pair, flag)
    out["refmac"] = ref["r_free"] if ref else None
    slog = work / f"servalcat_{tag}.log"
    subprocess.run(
        ["bash", "-c",
         f"source {CCP4_SETUP} 2>/dev/null && cd {work} && "
         f"servalcat refine_xtal_norefmac -s xray --model {model} "
         f"--hklin {mtz} --labin '{pair[0]},{pair[1]},{flag}' --ncycle 0 "
         f"-o serval_{tag} > {slog} 2>&1"],
        capture_output=True, text=True, timeout=3600, env=dict(os.environ))
    stext = slog.read_text(errors="ignore") if slog.exists() else ""
    # The summary line is `Rwork = 0.1435 Rfree = 0.1473`; a loose
    # last-match regex lands on the stats table's Ncyc row and reads 0.
    sm = re.findall(r"Rfree\s*=\s*([\d.]+)", stext)
    out["servalcat"] = float(sm[-1]) if sm else None
    return out


def resolution_audit(work: Path) -> dict:
    """Experiment 2, step 1: the resolution ranges each tool used, read
    from this round's own baseline logs."""
    out = {}
    ref_log = work / "refmac_refmac_r7_2vxn_baseline.log"
    if ref_log.exists():
        m = re.search(r"Refinement resln\s*:\s*([\d.]+)\s+([\d.]+)",
                      ref_log.read_text(errors="ignore"))
        out["refmac"] = [float(m.group(1)), float(m.group(2))] if m else None
    mvd_log = work / "mvd_mvd_r7_2vxn_baseline.log"
    if mvd_log.exists():
        m = re.search(r"high_resolution\s*:\s*([\d.]+)",
                      mvd_log.read_text(errors="ignore"))
        out["phenix_high"] = float(m.group(1)) if m else None
    return out


def ladder_2vxn(durable: Path, work: Path) -> dict:
    lid = "2vxn"
    mtz = durable / f"{lid}.mtz"
    cif = durable / f"{lid}.cif"
    pair, flag = _scr.select_arrays(mtz)
    rec: dict = {"input_hashes": {"model": _scr.sha256_file(cif),
                                  "mtz": _scr.sha256_file(mtz)}}
    # Baseline: the deposited CIF through all four tools, so experiment 1 is
    # cif-vs-cif (the round-6 phenix/gemmi figures were measured on the PDB
    # form; a format-level difference must not masquerade as an aniso effect).
    rec["baseline_deposited_cif"] = measure_four_tools(
        cif, mtz, work, "r7_2vxn_baseline", pair, flag)
    # Experiment 1: iso-only derived model.
    iso_cif = work / "2vxn_isoonly.cif"
    rec["exp1_derivation"] = derive_iso_only(cif, iso_cif)
    rec["exp1_iso_only"] = measure_four_tools(
        iso_cif, mtz, work, "r7_2vxn_isoonly", pair, flag)
    # Experiment 2: resolution audit (RESO-forced re-run only if ranges differ
    # — decided and recorded, not silently skipped).
    rec["exp2_resolution_audit"] = resolution_audit(work)
    # Experiment 3: the demoted hydrogen bound.
    hlog = work / "refmac_2vxn_hydr_n.log"
    subprocess.run(
        ["bash", "-c",
         f"source {CCP4_SETUP} 2>/dev/null && cd {work} && "
         f"refmac5 XYZIN {cif} HKLIN {mtz} XYZOUT rh_2vxn.pdb "
         f"HKLOUT rh_2vxn.mtz > {hlog} 2>&1 <<EOF\n"
         f"MAKE NEWLIGAND CONTINUE\nMAKE HYDR N\n"
         f"LABIN FP={pair[0]} SIGFP={pair[1]} FREE={flag}\n"
         f"NCYC 0\nEND\nEOF"],
        capture_output=True, text=True, timeout=1800, env=dict(os.environ))
    htext = hlog.read_text(errors="ignore") if hlog.exists() else ""
    m = _bnc._REFMAC_FREE.search(htext)
    rec["exp3_refmac_hydr_n_r_free"] = float(m.group(1)) if m else None
    # The closing-invocation test the registered outcome calls for: REFMAC's
    # default BREF ISOT collapses input aniso ADPs to isotropic equivalents
    # even at NCYC 0; REFI BREF ANIS keeps them. If this closes the gap
    # toward the two paths, it is the registered protocol amendment.
    alog = work / "refmac_2vxn_bref_anis.log"
    subprocess.run(
        ["bash", "-c",
         f"source {CCP4_SETUP} 2>/dev/null && cd {work} && "
         f"refmac5 XYZIN {cif} HKLIN {mtz} XYZOUT ra_2vxn.pdb "
         f"HKLOUT ra_2vxn.mtz > {alog} 2>&1 <<EOF\n"
         f"MAKE NEWLIGAND CONTINUE\nREFI BREF ANIS\n"
         f"LABIN FP={pair[0]} SIGFP={pair[1]} FREE={flag}\n"
         f"NCYC 0\nEND\nEOF"],
        capture_output=True, text=True, timeout=1800, env=dict(os.environ))
    atext = alog.read_text(errors="ignore") if alog.exists() else ""
    m = _bnc._REFMAC_FREE.search(atext)
    rec["closing_invocation_refmac_bref_anis_r_free"] = \
        float(m.group(1)) if m else None
    # Disclosed post-registration extension (same one-change protocol): the
    # candidate Servalcat counterpart. `--adp aniso` is a refinement
    # parameterization, not an input-interpretation fix — at ncycle 0 it
    # reinitializes the ADP model and degrades R badly, so NO closing
    # invocation exists for Servalcat; its attribution rests on the exp-1
    # invariance alone.
    xlog = work / "servalcat_2vxn_adpaniso.log"
    if not xlog.exists():
        subprocess.run(
            ["bash", "-c",
             f"source {CCP4_SETUP} 2>/dev/null && cd {work} && "
             f"servalcat refine_xtal_norefmac -s xray --model {cif} "
             f"--hklin {mtz} --labin '{pair[0]},{pair[1]},{flag}' "
             f"--ncycle 0 --adp aniso -o serval_2vxn_adpaniso "
             f"> {xlog} 2>&1"],
            capture_output=True, text=True, timeout=3600, env=dict(os.environ))
    xtext = xlog.read_text(errors="ignore") if xlog.exists() else ""
    xm = re.findall(r"Rfree\s*=\s*([\d.]+)", xtext)
    rec["disclosed_extension_servalcat_adp_aniso_r_free"] = \
        float(xm[-1]) if xm else None
    return rec


# --- H3: the 9YGW metadata-only repair ----------------------------------------------

def repair_9ygw(cif: Path, out_cif: Path) -> dict:
    """Rename label_comp_id/auth_comp_id CYS -> CSO on exactly the anisotrop
    rows whose atom id belongs to a CSO atom_site. Text-level cif edit —
    a gemmi Structure round-trip would rewrite the whole file and the V3
    rename-only invariant could not be shown."""
    import gemmi.cif as gcif
    doc = gcif.read(str(cif))
    block = doc.sole_block()
    atom_ids_cso = set()
    tbl = block.find("_atom_site.", ["id", "label_comp_id"])
    for row in tbl:
        if row[1] == "CSO":
            atom_ids_cso.add(row[0])
    renamed = 0
    # 9YGW's anisotrop category uses the pdbx_-prefixed comp tags.
    aniso = block.find("_atom_site_anisotrop.",
                       ["id", "pdbx_label_comp_id", "?pdbx_auth_comp_id"])
    for row in aniso:
        if row[0] in atom_ids_cso and row[1] == "CYS":
            row[1] = "CSO"
            if row.has(2) and row[2] == "CYS":
                row[2] = "CSO"
            renamed += 1
    doc.write_file(str(out_cif))
    return {"n_cso_atom_sites": len(atom_ids_cso),
            "n_anisotrop_rows_renamed": renamed,
            "derived": out_cif.name, "sha256": _scr.sha256_file(out_cif)}


def h3_9ygw(durable: Path, work: Path) -> dict:
    cif = durable / "9ygw.cif"
    mtz = durable / "9ygw.mtz"
    derived = work / "9ygw_r7fix.cif"
    rec: dict = {"repair": repair_9ygw(cif, derived)}
    pair, flag = _scr.select_arrays(mtz)
    res = _bnc.refmac_pass(derived, mtz, work, "r7_9ygw_fix", pair, flag)
    rec["refmac"] = ({"measurable": True, "r_free": res["r_free"],
                      "r_work": res.get("r_work")}
                     if res else {"measurable": False})
    if not res:
        log = work / "refmac_r7_9ygw_fix.log"
        text = log.read_text(errors="ignore") if log.exists() else ""
        rec["refmac"]["diagnostic_lines"] = [
            l.strip() for l in text.splitlines()
            if "aniso" in l.lower() or "mismatch" in l.lower()
            or "Problem" in l]
    return rec


# --- H4: store remediation behind the proof gate ------------------------------------

def _diagnose_flag_diff(store_mtz: Path, staged_mtz: Path,
                        cols: list[str]) -> dict:
    """Per mismatched flag column: how many positions differ, how many of
    those sit on reflections with NO measured amplitude/intensity, and the
    free-assignment count among the differing positions in each file."""
    import gemmi
    import numpy as np
    out = {}
    ms = gemmi.read_mtz_file(str(store_mtz))
    mt = gemmi.read_mtz_file(str(staged_mtz))
    ds, dt = np.array(ms, copy=True), np.array(mt, copy=True)
    labels_s = [c.label for c in ms.columns]
    labels_t = [c.label for c in mt.columns]
    obs_idx = [i for i, c in enumerate(ms.columns)
               if c.type in ("F", "J")]
    obs_nan = np.all(np.isnan(ds[:, obs_idx]), axis=1) if obs_idx else \
        np.zeros(ds.shape[0], dtype=bool)
    for col in cols:
        i_s, i_t = labels_s.index(col), labels_t.index(col)
        diff = ds[:, i_s] != dt[:, i_t]
        out[col] = {
            "n_differing": int(diff.sum()),
            "n_differing_on_unmeasured": int((diff & obs_nan).sum()),
            "free_among_differing_store": int((ds[diff, i_s] == 0).sum()),
            "free_among_differing_staged": int((dt[diff, i_t] == 0).sum()),
        }
    return out


def remediate_entry(pdb_id: str, durable: Path, staging: Path,
                    write: bool = False) -> dict:
    """One entry through the H4 gate. With write=False (the default) this
    collects the PROOF ONLY — staging fetch, fingerprint comparison,
    wavelength — and never touches the store. The replacement itself
    (write=True) additionally requires the user's explicit, in-conversation
    go-ahead for the sidecar re-baseline: the session's permission layer
    ruled that the merged registration alone does not name the specific
    rewrite, and this driver honors that ruling."""
    lid = pdb_id.lower()
    rec: dict = {"pdb_id": pdb_id}
    store_mtz = durable / f"{lid}.mtz"
    staging.mkdir(parents=True, exist_ok=True)
    model, mtz, err = _scr.fetch_pair(lid, staging)
    if err or mtz is None:
        rec["status"] = "staging_fetch_failed"
        rec["reason"] = err or "no mtz"
        return rec
    import gemmi
    store_fp = _b6.obs_fingerprint(store_mtz)
    staged_fp = _b6.obs_fingerprint(mtz)
    rec["fingerprints_match"] = (store_fp == staged_fp)
    staged = gemmi.read_mtz_file(str(mtz))
    wl = staged.datasets[-1].wavelength if staged.datasets else 0.0
    rec["staged_wavelength"] = round(wl, 6)
    if not rec["fingerprints_match"]:
        rec["status"] = "proof_failed_store_untouched"
        rec["mismatched_columns"] = sorted(
            k for k in set(store_fp) | set(staged_fp)
            if store_fp.get(k) != staged_fp.get(k))
        # #368: when only flag columns mismatch, diagnose — are the
        # differing assignments confined to unmeasured reflections (the
        # converter's random fill), leaving measured-data identity intact?
        if all(("free" in c.lower() or "flag" in c.lower())
               for c in rec["mismatched_columns"]):
            rec["flag_diff_diagnosis"] = _diagnose_flag_diff(
                store_mtz, mtz, rec["mismatched_columns"])
        return rec
    if wl <= 0.0:
        rec["status"] = "wavelength_still_zero_store_untouched"
        return rec
    rec["staged_sha256"] = _scr.sha256_file(mtz)
    if not write:
        rec["status"] = "proof_ok_awaiting_user_go_ahead"
        return rec
    store_mtz.write_bytes(mtz.read_bytes())
    sidecar = store_mtz.with_suffix(".mtz.sha256")
    sidecar.write_text(_scr.sha256_file(store_mtz) + "\n")
    rec["rebaseline_ruling"] = ("negative_control_round7_preregistration.md "
                                "H4 + the user's explicit in-conversation "
                                "go-ahead; proof: KEEP fingerprints identical")
    rec["input_hashes"] = {"mtz": _scr.sha256_file(store_mtz)}
    rec["status"] = "remediated"
    return rec


# --- census -------------------------------------------------------------------------

def refmac_census(durable: Path, work: Path, derived_9ygw: Path | None) -> dict:
    out = {}
    for e in json.loads(ENROLLED_JSON.read_text())["entries"]:
        pid = e["pdb_id"].upper()
        lid = pid.lower()
        mtz = durable / f"{lid}.mtz"
        cif = durable / f"{lid}.cif"
        if pid == "9YGW" and derived_9ygw is not None and derived_9ygw.exists():
            cif = derived_9ygw
        pair, flag = _scr.select_arrays(mtz)
        res = _bnc.refmac_pass(cif, mtz, work, f"r7c_{lid}", pair, flag)
        out[pid] = ({"measurable": True, "r_free": res["r_free"]}
                    if res else {"measurable": False})
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--durable",
                    default=str(Path.home() / "protstruct_bench_inputs"))
    ap.add_argument("--work", default="/tmp/nc_round7_work")
    ap.add_argument("--staging", default="/tmp/nc_round7_staging")
    ap.add_argument("--h4-canary", default="",
                    help="run H4 for this one entry only, then stop")
    args = ap.parse_args()
    durable, work = Path(args.durable), Path(args.work)
    staging = Path(args.staging)
    work.mkdir(parents=True, exist_ok=True)

    thresholds = _brl.fit_thresholds_from_record()

    if args.h4_canary:
        rec = remediate_entry(args.h4_canary.upper(), durable, staging)
        print(json.dumps(rec, indent=2))
        return 0

    print("== H1: flip-disclosure sweep ==", file=sys.stderr)
    h1 = sweep_h1(thresholds)
    print(f"  rows checked: {h1['rows_checked']}, flips: {len(h1['flips'])}",
          file=sys.stderr)

    print("== H3: 9YGW repair ==", file=sys.stderr)
    h3 = h3_9ygw(durable, work)
    print(f"  renamed {h3['repair']['n_anisotrop_rows_renamed']} rows; "
          f"refmac measurable={h3['refmac'].get('measurable')}", file=sys.stderr)

    print("== H2: 2VXN ladder ==", file=sys.stderr)
    h2 = ladder_2vxn(durable, work)
    print(f"  baseline={h2['baseline_deposited_cif']} "
          f"iso_only={h2['exp1_iso_only']}", file=sys.stderr)

    print("== H4: store remediation ==", file=sys.stderr)
    stripped = [r["pdb_id"] for r in json.loads(R6_JSON.read_text())["migration"]
                if r.get("dropped_columns")]
    h4 = [remediate_entry(p, durable, staging) for p in stripped]
    for r in h4:
        print(f"  {r['pdb_id']}: {r['status']} wl={r.get('staged_wavelength')}",
              file=sys.stderr)

    print("== census ==", file=sys.stderr)
    census = refmac_census(durable, work, work / "9ygw_r7fix.cif"
                           if h3["refmac"].get("measurable") else None)

    report = {
        "run": {"preregistration": "negative_control_round7_preregistration.md",
                "round": 7, "durable_store": str(durable),
                "tools": _scr.tool_versions()},
        "h1_flip_sweep": h1,
        "h2_2vxn_ladder": h2,
        "h3_9ygw_repair": h3,
        "h4_remediation": h4,
        "refmac_census": census,
    }
    _scr.write_json_atomic(OUT_JSON, report)
    print(json.dumps({
        "h1_flips": len(h1["flips"]),
        "h2_baseline": h2["baseline_deposited_cif"],
        "h2_iso_only": h2["exp1_iso_only"],
        "h3_measurable": h3["refmac"].get("measurable"),
        "h4_remediated": sum(1 for r in h4 if r["status"] == "remediated"),
        "census_measurable": sum(1 for v in census.values() if v["measurable"]),
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
