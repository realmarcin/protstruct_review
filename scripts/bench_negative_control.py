#!/usr/bin/env python3
"""The negative-control bench (plan phase 3, #295): round-3 execution.

Implements `negative_control_round3_preregistration.md` verbatim over the
round-2 enrolled set. Two subjects (B1): S-null (the cached `r2n_` null
models — refinement reused, measurements computed) and S-SA (Cartesian
simulated annealing, prefix `r3sa_`). Four metric families (B2), each with
its cross-tool leg; the registered verdict rule (B3): DEGRADED iff >= 2
family flags, where a flag missing its cross-tool confirmation stands DOWN
as a named conflict.

The B3 constants are read from their registered sources, not restated:
S_r2 from the round-2 screen record's d6 block; the section-4 geometry and
shift values are the registry rows the preregistration cites, with the
clashscore clause in its BOUNDED form (ratio only while 1 <= pre <= 20;
below, absolute post vs the section-2 bar of 4 — the enrolled pool was
selected at clashscore <= 2, squarely where the registry documents the
ratio mis-serving).

Usage:
    python3 scripts/bench_negative_control.py --canary          # first entry, both subjects
    python3 scripts/bench_negative_control.py                   # full batch
    python3 scripts/bench_negative_control.py --subjects null   # one subject
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
# The round-18 gate: the entry set this bench runs on is the committed round-2
# enrollment record — stronger than a hardcoded list because every entry
# carries its screening provenance (deltas, hashes, array selection).
SET_RECORD = "ref/research/data/negative_control_round2_enrolled.json"
ENROLLED_JSON = REPO / SET_RECORD
SCREEN_R2_JSON = REPO / "ref/research/data/negative_control_round2_screen.json"
BENCH_JSON = REPO / "ref/research/data/negative_control_round3_bench.json"

CCP4_SETUP = "/Applications/ccp4-9.0.015-shelx-arpwarp-macosarm/ccp4-9/bin/ccp4.setup-sh"

# B3 citations that are fixed numbers in the registry (section-4 d_min < 2.5
# branch; section-2 absolute bar). Values restated here carry their rows'
# provenance via the preregistration's citations.
FAVORED_DROP_PP = 0.5
ROTAMER_RISE_PP = 4.0
CLASH_RATIO = 5.0
CLASH_RATIO_PRE_LO, CLASH_RATIO_PRE_HI = 1.0, 20.0
CLASH_ABS_BAR = 4.0
SHIFT_BAND_A = 0.12

# phenix.ramalyze / rotalyze per-residue verdicts (regex precedent:
# bench_vs_deposited._RAMALYZE_RESIDUE / _ROTALYZE_RESIDUE).
_RAMA_LINE = re.compile(
    r"^\s*(?P<chain>\S+)\s+(?P<resseq>-?\d+)\s*(?P<icode>[A-Za-z]?)\s*"
    r"(?P<resname>\S?[A-Z]{3}):[^:]*:[^:]*:[^:]*:(?P<verdict>Favored|Allowed|OUTLIER):",
    re.M)
_ROTA_LINE = re.compile(
    r"^\s*(?P<chain>\S+)\s+(?P<resseq>-?\d+)(?P<icode>[A-Za-z]?)\s+"
    r"(?P<resname>[A-Z]{3}):[^:]*:[^:]*:.*?:(?P<verdict>Favored|Allowed|OUTLIER):\S+\s*$",
    re.M)
# REFMAC NCYC 0 log: the single Ncyc table row and the summary R lines.
_REFMAC_ROW = re.compile(
    r"^\s+0\s+([\d.]+)\s+([\d.]+)\s+[\d.]+\s+\S+\s+\S+\s+([\d.]+)\s+([\d.]+)", re.M)
_REFMAC_FREE = re.compile(r"^Free R factor\s+=\s+([\d.]+)", re.M)


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_scr = _load("screen_round1")      # select_arrays, R paths, fetch, hashing, atomic IO
_bench = _load("bench_refinement_deltas")
_gold = _load("gold_mask")
PHENIX_BIN = Path.home() / "phenix-2.0-5936" / "phenix_bin"


def refine_sa(model: Path, mtz: Path, work: Path,
              pair: tuple[str, str], flag: str | None) -> tuple[Path | None, dict]:
    """S-SA: the registered subject — null protocol + simulated_annealing=True,
    own prefix per the #124 argument."""
    selectors = f"\"miller_array.labels.name={pair[0]},{pair[1]}\""
    if flag is not None:
        selectors += f" \"miller_array.labels.name={flag}\""
    prefix = f"r3sa_{model.stem}"
    out = work / f"{prefix}_001.pdb"
    log = work / f"refine_{prefix}.log"
    if not out.exists():
        subprocess.run(
            ["bash", "-c",
             f"cd {work} && {PHENIX_BIN / 'phenix.refine'} {model} {mtz} "
             f"main.number_of_macro_cycles={_bench.MACRO_CYCLES} "
             f"simulated_annealing=True {selectors} "
             f"output.prefix={prefix} --overwrite > {log} 2>&1"],
            capture_output=True, text=True, timeout=10800, env=dict(os.environ))
    if not out.exists():
        return None, {"failure_reason": _bench.refine_failure_reason(log)}
    return out, {}


def refmac_pass(model: Path, mtz: Path, work: Path, tag: str,
                pair: tuple[str, str], flag: str | None) -> dict | None:
    """REFMAC5 NCYC 0: the fully non-cctbx R + geometry opinion (B2 families
    1 and 2). Input rule per the disclosed canary: deposited models go in as
    mmCIF, refined models as the phenix PDB."""
    log = work / f"refmac_{tag}.log"
    if not (log.exists() and _REFMAC_FREE.search(log.read_text(errors="ignore"))):
        labin = f"LABIN FP={pair[0]} SIGFP={pair[1]}"
        if flag is not None:
            labin += f" FREE={flag}"
        # Round-6 G5: NEWLIGAND CONTINUE — 8R5K's unmeasurability was a
        # ligand-library gap (Y6Z), not its columns; safe for NCYC 0
        # measurement. REFMAC's default free convention (flag 0 = free)
        # matches every enrolled entry (round-6 G4 step-1 census).
        subprocess.run(
            ["bash", "-c",
             f"source {CCP4_SETUP} 2>/dev/null && cd {work} && "
             f"refmac5 XYZIN {model} HKLIN {mtz} "
             f"XYZOUT ref_{tag}.pdb HKLOUT ref_{tag}.mtz > {log} 2>&1 <<'EOF'\n"
             f"MAKE NEWLIGAND CONTINUE\n{labin}\nNCYC 0\nEND\nEOF"],
            capture_output=True, text=True, timeout=1800, env=dict(os.environ))
    if not log.exists():
        return None
    text = log.read_text(errors="ignore")
    row = _REFMAC_ROW.search(text)
    free = _REFMAC_FREE.search(text)
    if not row:
        return None
    return {"r_work": float(row.group(1)),
            "r_free": float(free.group(1)) if free else float(row.group(2)),
            "rms_bond": float(row.group(3)), "z_bond": float(row.group(4))}


def per_residue_verdicts(model: Path, work: Path, tag: str) -> dict:
    """(chain, resseq, icode) -> {'rama': verdict, 'rota': verdict}."""
    out: dict[tuple, dict] = {}
    for tool, pattern, key in (("phenix.ramalyze", _RAMA_LINE, "rama"),
                               ("phenix.rotalyze", _ROTA_LINE, "rota")):
        log = work / f"{key}res_{tag}.log"
        if not log.exists() or log.stat().st_size == 0:
            subprocess.run(["bash", "-c",
                            f"cd {work} && {PHENIX_BIN / tool} {model} > {log} 2>&1"],
                           capture_output=True, text=True, timeout=3600,
                           env=dict(os.environ))
        for m in pattern.finditer(log.read_text(errors="ignore")):
            k = (m.group("chain"), int(m.group("resseq")),
                 (m.group("icode") or "").strip())
            out.setdefault(k, {})[key] = m.group("verdict")
    return out


def mask_key_set(mask: dict, which: str) -> set[tuple]:
    """(chain, 'resseq[icode]') keys — the `ca_atoms` key form — for masked or
    protected residues of a gold_mask record."""
    out = set()
    for r in mask["residues"]:
        if (which == "masked" and r["masked"]) or \
                (which == "protected" and r["protected"]):
            out.add((r["chain"], f"{r['resnum']}{r['icode']}".strip()))
    return out


def unmasked_ca_shift(pre: Path, post: Path,
                      masked_keys: set[tuple]) -> tuple[float | None, int, float | None]:
    """Raw Cα shift, no superposition (§4 convention): (unmasked_rmsd,
    n_unmasked_pairs, all_residue_rmsd). Both shifts are reported per the
    registered band-transfer caveat."""
    a, b = _bench.ca_atoms(pre), _bench.ca_atoms(post)
    shared = sorted(set(a) & set(b))
    if not shared:
        return None, 0, None

    def rmsd(keys):
        if not keys:
            return None
        total = sum(sum((a[k][i] - b[k][i]) ** 2 for i in range(3)) for k in keys)
        return round((total / len(keys)) ** 0.5, 4)

    unmasked = [k for k in shared if k not in masked_keys]
    return rmsd(unmasked), len(unmasked), rmsd(shared)


def family_flags(numbers: dict, s_r2: dict) -> tuple[dict, list[str]]:
    """B3, pure over the measured numbers — unit-testable.

    numbers: d_phenix, d_gemmi, d_refmac (signed ΔR-free per path);
    clash_pre, clash_post; d_favored_pp, d_rota_pp; d_zbond;
    n_protected_fixed; shift_unmasked.
    Returns ({flag: bool}, [named conflicts]).
    """
    conflicts: list[str] = []

    f_data = (numbers["d_phenix"] is not None and numbers["d_gemmi"] is not None
              and numbers["d_phenix"] > 3 * s_r2["phenix"]
              and numbers["d_gemmi"] > 3 * s_r2["gemmi"])
    if f_data and numbers.get("d_refmac") is not None \
            and numbers["d_refmac"] < 0:
        conflicts.append(
            f"F-data: two-path ΔR-free positive but REFMAC sign negative "
            f"({numbers['d_refmac']:+.4f}) — flag stands down")
        f_data = False

    pre, post = numbers["clash_pre"], numbers["clash_post"]
    if pre is None or post is None:
        clash_bad = False
    elif CLASH_RATIO_PRE_LO <= pre <= CLASH_RATIO_PRE_HI:
        clash_bad = post / pre >= CLASH_RATIO
    else:
        clash_bad = post > CLASH_ABS_BAR      # bounded form: absolute vs §2 bar
    geom_bad = (clash_bad
                or (numbers["d_favored_pp"] is not None
                    and numbers["d_favored_pp"] < -FAVORED_DROP_PP)
                or (numbers["d_rota_pp"] is not None
                    and numbers["d_rota_pp"] > ROTAMER_RISE_PP))
    f_geom = geom_bad
    if f_geom and numbers.get("d_zbond") is not None and numbers["d_zbond"] < 0:
        conflicts.append(
            f"F-geom: cctbx worsening but REFMAC zBOND improved "
            f"({numbers['d_zbond']:+.3f}) — flag stands down")
        f_geom = False

    f_protected = (numbers["n_protected_fixed"] or 0) >= 1
    f_shift = (numbers["shift_unmasked"] is not None
               and numbers["shift_unmasked"] > SHIFT_BAND_A)

    flags = {"F-data": f_data, "F-geom": f_geom,
             "F-protected": f_protected, "F-shift": f_shift}
    return flags, conflicts


def verdict(flags: dict) -> str:
    return "DEGRADED" if sum(flags.values()) >= 2 else "not-degraded"


def measure_model(model: Path, mtz: Path, work: Path, tag: str,
                  pair, flag, deposited_for_refmac: Path | None = None) -> dict:
    """All per-model measurements for one subject state. `deposited_for_refmac`
    substitutes the mmCIF for REFMAC when measuring a deposited PDB (the
    canaried input rule)."""
    refmac_in = deposited_for_refmac or model
    return {
        "rfree_phenix": _scr.model_vs_data_rfree(model, mtz, work,
                                                 f"phenix_{model.stem}", pair, flag),
        "rfree_gemmi": _scr.gemmi_rfree(model, mtz, work,
                                        f"gemmi_{model.stem}", pair, flag),
        "refmac": refmac_pass(refmac_in, mtz, work, f"{tag}_{model.stem}",
                              pair, flag),
        "geometry": _bench.measure(model, work, f"b3_{tag}"),
        "residues": per_residue_verdicts(model, work, f"{tag}_{model.stem}"),
    }


def bench_entry(entry: dict, subject: str, cache: Path, work: Path,
                s_r2: dict) -> dict:
    pdb_id = entry["pdb_id"].upper()
    row: dict = {"pdb_id": pdb_id, "subject": subject,
                 "stratum": entry.get("stratum"), "d_min": entry.get("d_min")}
    model, mtz, fetch_err = _scr.fetch_pair(pdb_id, cache)
    if fetch_err:
        row["status"], row["reason"] = "data_defect", fetch_err
        return row
    mask = _gold.build_mask(pdb_id, cache)
    pair, flag = _scr.select_arrays(mtz)
    if pair is None:
        row["status"], row["reason"] = "data_defect", "no registered obs labels"
        return row
    row["array_selection"] = {"obs": list(pair), "free_flag": flag}
    # Round-6 G1 (#349): input identity in EVERY row type.
    row["input_hashes"] = {"model": _scr.sha256_file(model),
                           "mtz": _scr.sha256_file(mtz)}

    r_stats: dict = {}
    if subject == "null":
        post = work / f"r2n_{model.stem}_001.pdb"
        if not post.exists():                      # cache cleared: re-run the null
            post, r_stats = _scr.refine_null(model, mtz, work, pair, flag)
    else:
        post, r_stats = refine_sa(model, mtz, work, pair, flag)
    if post is None or not Path(post).exists():
        row["status"] = "data_defect"
        row["reason"] = r_stats.get("failure_reason", "refinement failed")
        return row
    post = Path(post)

    deposited_cif = cache / f"{pdb_id.lower()}.cif"
    pre_m = measure_model(model, mtz, work, "pre", pair, flag,
                          deposited_for_refmac=deposited_cif
                          if deposited_cif.exists() else None)
    post_m = measure_model(post, mtz, work, subject, pair, flag)

    protected = mask_key_set(mask, "protected")
    fixed = []
    for key in protected:
        pre_v = _residue_verdict(pre_m["residues"], key)
        post_v = _residue_verdict(post_m["residues"], key)
        for fam in ("rama", "rota"):
            if pre_v.get(fam) == "OUTLIER" and post_v.get(fam) not in (None, "OUTLIER"):
                fixed.append({"chain": key[0], "res": key[1], "family": fam})
    shift_u, n_u, shift_all = unmasked_ca_shift(model, post,
                                                mask_key_set(mask, "masked"))

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
        "n_protected_fixed": len(fixed),
        "shift_unmasked": shift_u,
    }
    if numbers["d_phenix"] is None or numbers["d_gemmi"] is None:
        row["status"] = "data_defect"
        row["reason"] = "an R path is unmeasurable — two-path verdicts impossible"
        return row

    flags, conflicts = family_flags(numbers, s_r2)
    row.update({"status": "benched", "numbers": numbers,
                "pre": {"rfree_phenix": pre_m["rfree_phenix"],
                        "rfree_gemmi": pre_m["rfree_gemmi"],
                        "refmac": pre_m["refmac"]},
                "post": {"rfree_phenix": post_m["rfree_phenix"],
                         "rfree_gemmi": post_m["rfree_gemmi"],
                         "refmac": post_m["refmac"]},
                "protected_fixed": fixed,
                "shift_all_residue": shift_all, "n_unmasked_pairs": n_u,
                "flags": flags, "conflicts": conflicts,
                "verdict": verdict(flags)})
    return row


def _residue_verdict(residues: dict, key: tuple) -> dict:
    """ca-key (chain, 'resseq[icode]') -> the ramalyze/rotalyze verdict dict."""
    chain, resfield = key
    resseq = int(re.sub(r"[A-Za-z]", "", resfield) or 0)
    icode = re.sub(r"[-0-9]", "", resfield)
    return residues.get((chain, resseq, icode), {})


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cache",
                    default=str(Path.home() / "protstruct_bench_inputs"))
    ap.add_argument("--work", default="/tmp/nc_round1_work")
    ap.add_argument("--subjects", default="null,sa")
    ap.add_argument("--canary", action="store_true", help="first entry only")
    ap.add_argument("--only", default="", help="comma-separated pdb ids")
    ap.add_argument("--out", help="output for diagnostic runs")
    args = ap.parse_args()

    enrolled = json.loads(ENROLLED_JSON.read_text())["entries"]
    s_r2 = json.loads(SCREEN_R2_JSON.read_text())["d6"]["noise_scale"]
    subjects = [s.strip() for s in args.subjects.split(",") if s.strip()]
    queue = list(enrolled)
    if args.only:
        wanted = {i.strip().upper() for i in args.only.split(",")}
        queue = [e for e in queue if e["pdb_id"].upper() in wanted]
    if args.canary:
        queue = queue[:1]

    full_run = not (args.canary or args.only) and set(subjects) == {"null", "sa"}
    if args.out:
        out_path = Path(args.out)
    elif full_run:
        out_path = BENCH_JSON
    else:
        out_path = Path("/tmp/nc_bench_diagnostic.json")
        print(f"  diagnostic run: writing {out_path}", file=sys.stderr)
    if not full_run and (REPO / "ref") in out_path.resolve().parents:
        raise SystemExit("bench: a diagnostic run may not write inside ref/ (#319)")

    cache, work = Path(args.cache), Path(args.work)
    cache.mkdir(parents=True, exist_ok=True)
    work.mkdir(parents=True, exist_ok=True)
    manifest = {"run_mode": "full" if full_run else "diagnostic",
                "subjects": subjects, "s_r2": s_r2,
                "preregistration": "negative_control_round3_preregistration.md",
                "round": 3, "tools": _scr.tool_versions()}

    rows: list[dict] = []
    for subject in subjects:
        for entry in queue:
            print(f"[{entry['pdb_id']} / S-{subject}]", file=sys.stderr)
            row = bench_entry(entry, subject, cache, work, s_r2)
            rows.append(row)
            tail = row.get("verdict", row.get("reason", ""))
            print(f"  -> {row['status']}: {tail}", file=sys.stderr)
            _scr.write_json_atomic(out_path, {"run": manifest, "rows": rows})

    summary = {}
    for subject in subjects:
        sub = [r for r in rows if r["subject"] == subject]
        summary[subject] = {
            "attempted": len(sub),
            "benched": sum(1 for r in sub if r["status"] == "benched"),
            "degraded": sum(1 for r in sub if r.get("verdict") == "DEGRADED"),
            "conflicts": sum(len(r.get("conflicts", [])) for r in sub),
            "protected_fixes": sum(r.get("numbers", {}).get("n_protected_fixed", 0)
                                   for r in sub),
        }
    _scr.write_json_atomic(out_path, {"run": manifest, "rows": rows,
                                      "summary": summary})
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

