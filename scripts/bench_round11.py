#!/usr/bin/env python3
"""Round-11 execution: the 2VXN echo (#295).

Implements `negative_control_round11_preregistration.md`:

- **L1/Z1/Z2** — decompose the remaining ANIS deposited-2VXN pre-gap
  (0.0328) one change at a time: REFMAC `MAKE HYDR N` (the automatic
  riding-H term), REFMAC `SOLVENT NO` (the solvent-model term), and the
  converse ready_set-H term on the two R paths.
- **L3/Z3** — pure-record sweep: every candidate row in the committed
  round-4/5/10 recover records re-evaluated under the post-agreement
  rule (posts reconstructed from the committed round-3/9 pre values);
  disclose every row where the rule's answer differs from the committed
  delta-sign contribution.

All tool legs run inside one `EntrySandbox` per the NC-10 protocol.

Usage:
    python3 scripts/bench_round11.py --l1-canary   # ready_set leg only
    python3 scripts/bench_round11.py               # the full round
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
from entry_sandbox import EntrySandbox
from toolchain import ccp4_environment, phenix

REPO = Path(__file__).resolve().parent.parent
SET_RECORD = "ref/research/data/negative_control_round2_enrolled.json"
ENROLLED_JSON = REPO / SET_RECORD
R3_JSON = REPO / "ref/research/data/negative_control_round3_bench.json"
R4_JSON = REPO / "ref/research/data/negative_control_round4_recover.json"
R5_JSON = REPO / "ref/research/data/negative_control_round5_recover.json"
R9_JSON = REPO / "ref/research/data/negative_control_round9_anis.json"
R10_JSON = REPO / "ref/research/data/negative_control_round10_recover.json"
OUT_JSON = REPO / "ref/research/data/negative_control_round11_echo.json"

# The committed ANIS baselines the decomposition is anchored to (round 9).
def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / f"{name}.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


_scr = _load("screen_round1")
_bnc = _load("bench_negative_control")
_brl = _load("bench_recover_leg")

# The registered anchors, derived from their records at import and asserted
# against the values the preregistration states (#425) — a restated literal
# with no cross-check is the class the C1/H1 discipline exists to prevent.
_r9_2vxn = next(r for r in json.loads(R9_JSON.read_text())["rows"]
                if r["pdb_id"] == "2VXN")
PRE_PATHS = {p: _r9_2vxn["paths"][p]["pre"] for p in ("phenix", "gemmi")}
PRE_REFMAC_ANIS = _r9_2vxn["refmac"]["anis"]["pre"]
if (PRE_PATHS != {"phenix": 0.1043, "gemmi": 0.1059}
        or PRE_REFMAC_ANIS != 0.1371):
    raise SystemExit(
        f"bench_round11: round-9 record anchors {PRE_PATHS}/{PRE_REFMAC_ANIS} "
        f"!= the preregistration's stated values — record and registration "
        f"disagree")
PRE_GAP = round(PRE_REFMAC_ANIS - PRE_PATHS["phenix"], 4)   # 0.0328
POST_AGREEMENT_TOL = _brl.REGISTERED_FIT_THRESHOLDS_ANIS["d_refmac"]


def refmac_variant(sandbox: EntrySandbox, model: Path, mtz: Path,
                   tag: str, pair, flag, extra_keyword: str) -> float | None:
    """REFMAC NCYC 0 under ANIS plus exactly one extra keyword."""
    log_name = f"refmac_{tag}.log"
    log = sandbox.child(log_name)
    if not (log.exists()
            and _bnc._REFMAC_FREE.search(log.read_text(errors="ignore"))):
        keywords = (f"MAKE NEWLIGAND CONTINUE\nREFI BREF ANIS\n{extra_keyword}\n"
                    f"LABIN FP={pair[0]} SIGFP={pair[1]} FREE={flag}\n"
                    f"NCYC 0\nEND\n")
        sandbox.run_logged(
            ["refmac5", "XYZIN", model, "HKLIN", mtz,
             "XYZOUT", f"rv_{tag}.pdb", "HKLOUT", f"rv_{tag}.mtz"],
            log_name, timeout=1800, env=ccp4_environment(),
            input_text=keywords)
    text = log.read_text(errors="ignore") if log.exists() else ""
    m = _bnc._REFMAC_FREE.search(text)
    return float(m.group(1)) if m else None


def ready_set_h(sandbox: EntrySandbox, model: Path) -> tuple[Path | None, dict]:
    """L1 leg 3: the H-augmented deposited model, a recorded derivation."""
    out = sandbox.child(f"{model.stem}.updated.pdb")
    rec: dict = {}
    if not out.exists():
        sandbox.run_logged([phenix("phenix.ready_set"), model],
                           "ready_set.log", timeout=1800)
    if not out.exists():
        log = sandbox.child("ready_set.log")
        rec["log_tail"] = (log.read_text(errors="ignore").strip()
                           .splitlines()[-4:] if log.exists() else [])
        return None, rec
    text = out.read_text(errors="ignore")
    rec["n_hydrogens"] = sum(1 for line in text.splitlines()
                             if line.startswith(("ATOM", "HETATM"))
                             and line[76:78].strip() in ("H", "D"))
    rec["derived"] = out.name
    rec["sha256"] = _scr.sha256_file(out)
    return out, rec


def l1_decomposition(durable: Path, work: Path) -> dict:
    sandbox = EntrySandbox(work, "2VXN")
    cif = durable / "2vxn.cif"
    pdb = durable / "2vxn.pdb"
    mtz = durable / "2vxn.mtz"
    pair, flag = _scr.select_arrays(mtz)
    rec: dict = {"input_hashes": {"cif": _scr.sha256_file(cif),
                                  "pdb": _scr.sha256_file(pdb),
                                  "mtz": _scr.sha256_file(mtz)},
                 "committed_baselines": {"paths_pre": PRE_PATHS,
                                         "refmac_anis_pre": PRE_REFMAC_ANIS,
                                         "pre_gap": PRE_GAP}}
    hydr_n = refmac_variant(sandbox, cif, mtz, "anis_hydr_n", pair, flag,
                            "MAKE HYDR N")
    solv_no = refmac_variant(sandbox, cif, mtz, "anis_solvent_no", pair, flag,
                             "SOLVENT NO")
    rec["refmac_anis_hydr_n"] = hydr_n
    rec["refmac_anis_solvent_no"] = solv_no
    rec["h_term_refmac"] = (round(hydr_n - PRE_REFMAC_ANIS, 4)
                            if hydr_n is not None else None)
    rec["solvent_term_refmac"] = (round(solv_no - PRE_REFMAC_ANIS, 4)
                                  if solv_no is not None else None)
    h_model, derivation = ready_set_h(sandbox, pdb)
    rec["ready_set"] = derivation
    if h_model is not None:
        paths_h = {}
        for name, fn in (("phenix", _scr.model_vs_data_rfree),
                         ("gemmi", _scr.gemmi_rfree)):
            paths_h[name] = fn(h_model, mtz, sandbox.path,
                               f"{name}_r11_hpre", pair, flag)
        rec["paths_on_h_model"] = paths_h
        rec["h_term_paths"] = {
            p: round(paths_h[p] - PRE_PATHS[p], 4)
            for p in paths_h if paths_h[p] is not None}
    # Z2 accounting, exactly as registered.
    terms = [rec.get("h_term_refmac"), rec.get("solvent_term_refmac")]
    if all(t is not None for t in terms):
        rec["z2_terms_sum_abs"] = round(sum(abs(t) for t in terms), 4)
        rec["z2_bar"] = round(0.75 * PRE_GAP, 4)
        rec["z2_holds"] = rec["z2_terms_sum_abs"] >= rec["z2_bar"]
        rec["z2_residual"] = round(PRE_GAP - rec["z2_terms_sum_abs"], 4)
    rec["sandbox"] = sandbox.path.name
    rec["sandbox_files"] = sandbox.inventory()
    return rec


# --- L3: the pure-record sweep -----------------------------------------------------

def l3_sweep() -> dict:
    r3_pre = {r["pdb_id"]: r["pre"]
              for r in json.loads(R3_JSON.read_text())["rows"]
              if r["subject"] == "null"}
    r9 = {r["pdb_id"]: r for r in json.loads(R9_JSON.read_text())["rows"]}
    rows_out = []
    diffs = []

    def eval_row(round_no, subject, pdb_id, numbers, era):
        d_ref = numbers.get("d_refmac")
        if d_ref is None:
            return None
        if era == "isot":
            pre = r3_pre.get(pdb_id)
            if pre is None:
                return None
            pre_paths = {"phenix": pre["rfree_phenix"], "gemmi": pre["rfree_gemmi"]}
            pre_ref = pre["refmac"]["r_free"]
        else:
            r9row = r9.get(pdb_id)
            if r9row is None or not isinstance(r9row.get("refmac"), dict) \
                    or "anis" not in r9row["refmac"]:
                return None
            pre_paths = {p: r9row["paths"][p]["pre"] for p in ("phenix", "gemmi")}
            pre_ref = r9row["refmac"]["anis"]["pre"]
        posts = {p: pre_paths[p] + numbers[f"d_{p}"] for p in pre_paths}
        post_ref = pre_ref + d_ref
        post_mean = sum(posts.values()) / 2
        post_agree = abs(post_ref - post_mean) <= POST_AGREEMENT_TOL
        # The committed contribution: does the REFMAC delta share the
        # two-path delta sign (both paths sharing one)?
        dp, dg = numbers["d_phenix"], numbers["d_gemmi"]
        if (dp >= 0) == (dg >= 0):
            delta_agree = (d_ref >= 0) == (dp >= 0)
        else:
            delta_agree = None       # no shared two-path sign to agree with
        row = {"round": round_no, "subject": subject, "pdb_id": pdb_id,
               "era": era, "post_refmac": round(post_ref, 4),
               "post_paths_mean": round(post_mean, 4),
               "post_gap": round(abs(post_ref - post_mean), 4),
               "post_agreement": post_agree, "delta_sign_agreement": delta_agree}
        if delta_agree is not None and post_agree != delta_agree:
            diffs.append(row)
        return row

    for r in json.loads(R4_JSON.read_text())["rows"]:
        rec = r.get("recovered") or {}
        if rec.get("status") == "judged":
            row = eval_row(4, None, r["pdb_id"], rec["numbers"], "isot")
            if row:
                rows_out.append(row)
    for r in json.loads(R5_JSON.read_text())["rows"]:
        rec = r.get("recovered") or {}
        if rec.get("status") == "judged":
            row = eval_row(5, r.get("subject"), r["pdb_id"], rec["numbers"],
                           "isot")
            if row:
                rows_out.append(row)
    for r in json.loads(R10_JSON.read_text())["rows"]:
        rec = r.get("recovered") or {}
        if rec.get("status") == "judged":
            row = eval_row(10, r.get("subject"), r["pdb_id"], rec["numbers"],
                           "anis")
            if row:
                rows_out.append(row)
    return {"rows": rows_out, "rule_flips": diffs,
            "n_rows": len(rows_out), "n_flips": len(diffs),
            "tolerance": POST_AGREEMENT_TOL}


def main() -> int:
    from benchmark_environment import announce_benchmark_environment

    announce_benchmark_environment()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--durable",
                    default=str(Path.home() / "protstruct_bench_inputs"))
    ap.add_argument("--work", default="/tmp/nc_round11_work")
    ap.add_argument("--l1-canary", action="store_true",
                    help="ready_set leg only, then stop")
    args = ap.parse_args()
    durable, work = Path(args.durable), Path(args.work)
    work.mkdir(parents=True, exist_ok=True)

    if args.l1_canary:
        sandbox = EntrySandbox(work, "2VXN")
        h_model, rec = ready_set_h(sandbox, durable / "2vxn.pdb")
        print(json.dumps({"ok": h_model is not None, **rec}, indent=2))
        return 0

    print("== L1: pre-gap decomposition ==", file=sys.stderr)
    l1 = l1_decomposition(durable, work)
    print(json.dumps({k: l1[k] for k in l1
                      if k not in ("sandbox_files", "input_hashes")},
                     indent=2, default=str), file=sys.stderr)

    print("== L3: pure-record sweep ==", file=sys.stderr)
    l3 = l3_sweep()
    for d in l3["rule_flips"]:
        print(f"  FLIP {d['round']}/{d['subject']}/{d['pdb_id']}: "
              f"post_gap={d['post_gap']}", file=sys.stderr)

    report = {
        "run": {"preregistration": "negative_control_round11_preregistration.md",
                "round": 11, "durable_store": str(durable),
                "sandbox_protocol": "per-entry-process-group-v1",
                "set_record": SET_RECORD,
                "tools": _scr.tool_versions()},
        "l1_decomposition": l1,
        "l3_sweep": l3,
    }
    _scr.write_json_atomic(OUT_JSON, report)
    print(json.dumps({
        "h_term_refmac": l1.get("h_term_refmac"),
        "solvent_term_refmac": l1.get("solvent_term_refmac"),
        "h_term_paths": l1.get("h_term_paths"),
        "z2": {k: l1.get(k) for k in ("z2_terms_sum_abs", "z2_bar",
                                      "z2_holds", "z2_residual")},
        "l3": {"n_rows": l3["n_rows"], "n_flips": l3["n_flips"],
               "flips": [(d["round"], d["subject"], d["pdb_id"])
                         for d in l3["rule_flips"]]},
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
