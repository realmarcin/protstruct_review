#!/usr/bin/env python3
"""Round-4 execution: perturb-then-recover + the null-centered fit verdict.

Implements `negative_control_round4_preregistration.md` over the enrolled 22:
perturb (`phenix.dynamics stop_at_diff=0.5 random_seed=42`, prefix `r4p_`),
recover (the registered null protocol refining the perturbed model, prefix
`r4r_`), judge BOTH states against the deposited start with the round-3 bench
machinery plus C1.

C1 discipline: the null-centered thresholds are COMPUTED from the committed
round-3 S-null record and ASSERTED equal to the registered table — if the
record and the registration ever disagree, this script refuses to run rather
than silently preferring either.

Usage:
    python3 scripts/bench_recover_leg.py --canary
    python3 scripts/bench_recover_leg.py
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
from toolchain import phenix, run_logged

REPO = Path(__file__).resolve().parent.parent
# Round-18 gate: the committed enrollment record is the entry set.
SET_RECORD = "ref/research/data/negative_control_round2_enrolled.json"
ENROLLED_JSON = REPO / SET_RECORD
R3_BENCH_JSON = REPO / "ref/research/data/negative_control_round3_bench.json"
OUT_JSON = REPO / "ref/research/data/negative_control_round4_recover.json"

# The registered C1 table — round-7 H1 (negative_control_round7_preregistration.md)
# supersedes the round-4 table after the round-6 U3 falsification. Clean-null
# recompute: 8R5K's round-6 null SUBSTITUTED on the phenix/gemmi paths (n=22)
# and ADDED on the REFMAC path (8R5K had no round-3 REFMAC null; 19 -> 20).
# The round-4 values 0.01220/0.01090/0.00540 are retired history.
REGISTERED_FIT_THRESHOLDS = {"d_phenix": 0.01200, "d_gemmi": 0.01025,
                             "d_refmac": 0.00560}
R6_HYGIENE_JSON_NAME = "ref/research/data/negative_control_round6_hygiene.json"
# Round-9 J3: the ANIS-convention table. The two-path values are the H1
# values (unchanged by REFMAC's ADP convention); d_refmac is re-derived
# from the round-9 ANIS null distribution (REFI BREF ANIS on both sides of
# every delta). Verdict-bearing drivers from round 9 on use THIS table with
# refmac_pass(anis=True); the ISOT table above is retained so rounds 3-8
# reproduce. The two conventions are never mixed inside one comparison.
REGISTERED_FIT_THRESHOLDS_ANIS = {"d_phenix": 0.01200, "d_gemmi": 0.01025,
                                  "d_refmac": 0.01150}
R9_ANIS_JSON_NAME = "ref/research/data/negative_control_round9_anis.json"
MAD_FLOOR = 0.0005
SHIFT_BAND_A = 0.12          # §4 stay-band, cited via the prereg
STOP_AT_DIFF = 0.5
RANDOM_SEED = 42

def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / f"{name}.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


_scr = _load("screen_round1")
_bnc = _load("bench_negative_control")
_bench = _load("bench_refinement_deltas")
_gold = _load("gold_mask")


def fit_thresholds_from_record() -> dict:
    """C1 as re-registered (round-7 H1): median + 3·MAD per tool over the
    round-3 null deltas with 8R5K's clean round-6 null substituted (phenix,
    gemmi) and added (REFMAC), floors applied — recomputed, then verified
    against the registered table."""
    d = json.loads(R3_BENCH_JSON.read_text())
    clean = json.loads((REPO / R6_HYGIENE_JSON_NAME).read_text())[
        "g3_8r5k_rescreen"]["clean_null_deltas"]
    nulls = [r for r in d["rows"] if r["subject"] == "null"
             and r["status"] == "benched"]
    out = {}
    for tool in ("d_phenix", "d_gemmi", "d_refmac"):
        vals = []
        for r in nulls:
            v = clean[tool] if r["pdb_id"] == "8R5K" else r["numbers"][tool]
            if v is not None:
                vals.append(v)
        med = statistics.median(vals)
        mad = max(statistics.median(abs(v - med) for v in vals), MAD_FLOOR)
        out[tool] = round(med + 3 * mad, 5)
    if out != REGISTERED_FIT_THRESHOLDS:
        raise SystemExit(
            f"bench_recover: recomputed C1 thresholds {out} != registered "
            f"{REGISTERED_FIT_THRESHOLDS} — record and registration disagree")
    return out


def anis_thresholds_from_record() -> dict:
    """Round-9 J3: the ANIS table, re-derived — two paths from the same
    record route as fit_thresholds_from_record (conventions do not touch
    them), d_refmac from the round-9 ANIS null distribution — then verified
    against the registered table."""
    isot = fit_thresholds_from_record()
    d = json.loads((REPO / R9_ANIS_JSON_NAME).read_text())
    deltas = [r["refmac"]["anis"]["delta"] for r in d["rows"]
              if isinstance(r.get("refmac"), dict)
              and isinstance(r["refmac"].get("anis"), dict)
              and r["refmac"]["anis"]["delta"] is not None]
    med = statistics.median(deltas)
    mad = max(statistics.median(abs(v - med) for v in deltas), MAD_FLOOR)
    out = {"d_phenix": isot["d_phenix"], "d_gemmi": isot["d_gemmi"],
           "d_refmac": round(med + 3 * mad, 5)}
    if out != REGISTERED_FIT_THRESHOLDS_ANIS:
        raise SystemExit(
            f"bench_recover: recomputed ANIS thresholds {out} != registered "
            f"{REGISTERED_FIT_THRESHOLDS_ANIS} — record and registration "
            f"disagree")
    return out


def fit_degraded(numbers: dict, thresholds: dict) -> bool | None:
    """C1: all three tools past their null-centered thresholds. None when
    REFMAC is unmeasurable — no FIT verdict is possible, fall back."""
    if numbers.get("d_refmac") is None:
        return None
    return all(numbers.get(t) is not None and numbers[t] > thresholds[t]
               for t in thresholds)


def combined_verdict(flags: dict, numbers: dict, thresholds: dict) -> str:
    """Registered precedence: DEGRADED (>= 2 families) > FIT-DEGRADED >
    not-degraded."""
    if _bnc.verdict(flags) == "DEGRADED":
        return "DEGRADED"
    fit = fit_degraded(numbers, thresholds)
    if fit:
        return "FIT-DEGRADED"
    return "not-degraded"


def perturb(model: Path, work: Path) -> tuple[Path | None, str]:
    out = work / f"r4p_{model.stem}.pdb"
    log = work / f"dynamics_{model.stem}.log"
    if not out.exists():
        run_logged(
            [phenix("phenix.dynamics"), model, f"stop_at_diff={STOP_AT_DIFF}",
             f"random_seed={RANDOM_SEED}",
             f"output_file_name_prefix=r4p_{model.stem}"],
            log, cwd=work, timeout=3600,
        )
    if not out.exists():
        tail = log.read_text(errors="ignore").strip().splitlines()[-2:] \
            if log.exists() else []
        return None, "dynamics failed: " + " / ".join(tail)
    return out, ""


def refine_recover(perturbed: Path, mtz: Path, work: Path,
                   pair, flag) -> tuple[Path | None, dict]:
    """The registered null protocol, input = the perturbed model, own
    prefix (#124)."""
    selectors = [f"miller_array.labels.name={pair[0]},{pair[1]}"]
    if flag is not None:
        selectors.append(f"miller_array.labels.name={flag}")
    prefix = f"r4r_{perturbed.stem}"
    out = work / f"{prefix}_001.pdb"
    log = work / f"refine_{prefix}.log"
    if not out.exists():
        run_logged(
            [phenix("phenix.refine"), perturbed, mtz,
             f"main.number_of_macro_cycles={_bench.MACRO_CYCLES}", *selectors,
             f"output.prefix={prefix}", "--overwrite"],
            log, cwd=work, timeout=10800,
        )
    if not out.exists():
        return None, {"failure_reason": _bench.refine_failure_reason(log)}
    return out, {}


def s_r2_from_record() -> dict:
    """Round-2 noise scales, read from their committed record — never
    restated (inner review r2 caught an inline copy)."""
    return json.loads((REPO / "ref/research/data/"
                       "negative_control_round2_screen.json").read_text()
                      )["d6"]["noise_scale"]


def judge_state(state: str, post: Path, model: Path, mtz: Path, work: Path,
                pair, flag, mask, pre_m, thresholds: dict,
                s_r2: dict, fit_fn=None, anis: bool = False) -> dict:
    """Bench judgment of one state (perturbed or recovered) vs the deposited
    start, with C1 layered on the round-3 families."""
    post_m = _bnc.measure_model(post, mtz, work, state, pair, flag, anis=anis)
    protected = _bnc.mask_key_set(mask, "protected")
    fixed = 0
    for key in protected:
        pre_v = _bnc._residue_verdict(pre_m["residues"], key)
        post_v = _bnc._residue_verdict(post_m["residues"], key)
        for fam in ("rama", "rota"):
            if pre_v.get(fam) == "OUTLIER" and post_v.get(fam) not in (None, "OUTLIER"):
                fixed += 1
    shift_u, n_u, shift_all = _bnc.unmasked_ca_shift(
        model, post, _bnc.mask_key_set(mask, "masked"))

    def delta(a, b):
        return round(b - a, 6) if a is not None and b is not None else None

    numbers = {
        "d_phenix": delta(pre_m["rfree_phenix"], post_m["rfree_phenix"]),
        "d_gemmi": delta(pre_m["rfree_gemmi"], post_m["rfree_gemmi"]),
        "d_refmac": delta(pre_m["refmac"]["r_free"], post_m["refmac"]["r_free"])
        if pre_m["refmac"] and post_m["refmac"] else None,
        "clash_pre": pre_m["geometry"]["clashscore"],
        "clash_post": post_m["geometry"]["clashscore"],
        "d_favored_pp": delta(pre_m["geometry"]["rama_favored_pct"],
                              post_m["geometry"]["rama_favored_pct"]),
        "d_rota_pp": delta(pre_m["geometry"]["rotamer_outlier_pct"],
                           post_m["geometry"]["rotamer_outlier_pct"]),
        "d_zbond": delta(pre_m["refmac"]["z_bond"], post_m["refmac"]["z_bond"])
        if pre_m["refmac"] and post_m["refmac"] else None,
        "n_protected_fixed": fixed,
        "shift_unmasked": shift_u,
    }
    if numbers["d_phenix"] is None or numbers["d_gemmi"] is None:
        return {"state": state, "status": "unmeasurable",
                "reason": "an R path is unmeasurable"}
    flags, conflicts = _bnc.family_flags(numbers, s_r2)
    # fit_fn parameterizes the fit rule (round 5's E1 supersedes C1 there);
    # default None keeps the round-4 C1 behavior byte-for-byte.
    fit = (fit_fn or fit_degraded)(numbers, thresholds)
    if _bnc.verdict(flags) == "DEGRADED":
        verdict_str = "DEGRADED"
    elif fit:
        verdict_str = "FIT-DEGRADED"
    else:
        verdict_str = "not-degraded"
    return {"state": state, "status": "judged", "numbers": numbers,
            "shift_all_residue": shift_all, "n_unmasked_pairs": n_u,
            "flags": flags, "conflicts": conflicts,
            "fit_degraded": fit,
            "verdict": verdict_str}


def run_entry(entry: dict, cache: Path, work: Path, thresholds: dict,
              s_r2: dict) -> dict:
    pdb_id = entry["pdb_id"].upper()
    row: dict = {"pdb_id": pdb_id, "stratum": entry.get("stratum"),
                 "d_min": entry.get("d_min")}
    model, mtz, fetch_err = _scr.fetch_pair(pdb_id, cache)
    if fetch_err:
        row["status"], row["reason"] = "data_defect", fetch_err
        return row
    mask = _gold.build_mask(pdb_id, cache)
    pair, flag = _scr.select_arrays(mtz)
    if pair is None:
        row["status"], row["reason"] = "data_defect", "no registered obs labels"
        return row
    # Round-6 G1 (#349): input identity in EVERY row type.
    row["input_hashes"] = {"model": _scr.sha256_file(model),
                           "mtz": _scr.sha256_file(mtz)}

    perturbed, err = perturb(model, work)
    if perturbed is None:
        row["status"], row["reason"] = "data_defect", err
        return row
    ach_u, _, ach_all = _bnc.unmasked_ca_shift(
        model, perturbed, _bnc.mask_key_set(mask, "masked"))
    row["achieved_shift_unmasked"] = ach_u
    row["achieved_shift_all"] = ach_all

    recovered, r_stats = refine_recover(perturbed, mtz, work, pair, flag)
    if recovered is None:
        row["status"] = "data_defect"
        row["reason"] = r_stats.get("failure_reason", "recovery refinement failed")
        return row

    pre_m = _bnc.measure_model(model, mtz, work, "pre", pair, flag,
                               deposited_for_refmac=(cache / f"{pdb_id.lower()}.cif")
                               if (cache / f"{pdb_id.lower()}.cif").exists() else None)
    row["perturbed"] = judge_state("perturbed", perturbed, model, mtz, work,
                                   pair, flag, mask, pre_m, thresholds, s_r2)
    row["recovered"] = judge_state("recovered", recovered, model, mtz, work,
                                   pair, flag, mask, pre_m, thresholds, s_r2)

    rec = row["recovered"]
    row["recovery_success"] = (
        rec.get("status") == "judged"
        and rec["numbers"]["shift_unmasked"] is not None
        and rec["numbers"]["shift_unmasked"] < SHIFT_BAND_A
        and rec["verdict"] == "not-degraded")
    row["status"] = "completed"
    return row


def main() -> int:
    from benchmark_environment import announce_benchmark_environment

    announce_benchmark_environment()
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cache",
                    default=str(Path.home() / "protstruct_bench_inputs"))
    ap.add_argument("--work", default="/tmp/nc_round1_work")
    ap.add_argument("--canary", action="store_true")
    ap.add_argument("--only", default="")
    ap.add_argument("--out", help="output for diagnostic runs")
    args = ap.parse_args()

    thresholds = fit_thresholds_from_record()
    s_r2 = s_r2_from_record()
    enrolled = json.loads(ENROLLED_JSON.read_text())["entries"]
    queue = list(enrolled)
    if args.only:
        wanted = {i.strip().upper() for i in args.only.split(",")}
        queue = [e for e in queue if e["pdb_id"].upper() in wanted]
    if args.canary:
        queue = queue[:1]

    full_run = not (args.canary or args.only)
    if args.out:
        out_path = Path(args.out)
    elif full_run:
        out_path = OUT_JSON
    else:
        out_path = Path("/tmp/nc_recover_diagnostic.json")
        print(f"  diagnostic run: writing {out_path}", file=sys.stderr)
    if not full_run and (REPO / "ref") in out_path.resolve().parents:
        raise SystemExit("bench_recover: a diagnostic run may not write "
                         "inside ref/ (#319)")

    cache, work = Path(args.cache), Path(args.work)
    cache.mkdir(parents=True, exist_ok=True)
    work.mkdir(parents=True, exist_ok=True)
    manifest = {"run_mode": "full" if full_run else "diagnostic",
                "preregistration": "negative_control_round4_preregistration.md",
                "round": 4, "fit_thresholds": thresholds,
                "stop_at_diff": STOP_AT_DIFF, "random_seed": RANDOM_SEED,
                "tools": _scr.tool_versions()}

    rows: list[dict] = []
    for entry in queue:
        print(f"[{entry['pdb_id']}]", file=sys.stderr)
        row = run_entry(entry, cache, work, thresholds, s_r2)
        rows.append(row)
        tag = (f"perturbed={row.get('perturbed', {}).get('verdict', '?')} "
               f"recovered={row.get('recovered', {}).get('verdict', '?')} "
               f"success={row.get('recovery_success')}"
               if row["status"] == "completed" else row.get("reason", ""))
        print(f"  -> {row['status']}: {tag}", file=sys.stderr)
        _scr.write_json_atomic(out_path, {"run": manifest, "rows": rows})

    completed = [r for r in rows if r["status"] == "completed"]
    summary = {
        "attempted": len(rows), "completed": len(completed),
        # V1 judged on the ALL-residue shift — the referent of the prereg's
        # disclosed canary figure (0.2515 was all-residue); the unmasked count
        # is reported alongside because the prereg's wording is ambiguous, and
        # the round doc names that imprecision rather than exploiting it.
        "v1_perturbed_ge_0p15": sum(
            1 for r in completed
            if (r.get("achieved_shift_all") or 0) >= 0.15),
        "v1_unmasked_ge_0p15": sum(
            1 for r in completed
            if (r.get("achieved_shift_unmasked") or 0) >= 0.15),
        "v2_recovery_success": sum(1 for r in completed
                                   if r.get("recovery_success")),
        "v3_perturbed_flagged": sum(
            1 for r in completed
            if r.get("perturbed", {}).get("verdict") in ("DEGRADED",
                                                         "FIT-DEGRADED")),
    }
    _scr.write_json_atomic(out_path, {"run": manifest, "rows": rows,
                                      "summary": summary})
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
