#!/usr/bin/env python3
"""Round-1 headroom screen: null re-refinement of gold-standard candidates (#295).

Executes D3, D4 and D6 of `negative_control_round1_preregistration.md` over the
representatives selected by `select_round1_reps.py`. Per entry:

  1. fetch model + structure factors (`phenix.fetch_pdb --mtz`, cached)
  2. build the phase-1 mask (`gold_mask`) -> D3 floor (>= 50 unmasked residues)
  3. null re-refinement via the `bench_refinement_deltas.refine` protocol
     (3 macro cycles, default weights, no generated R-free flags — #242)
  4. ΔR-free on two independent code paths, same derivation on both sides of
     each subtraction (D6): `phenix.model_vs_data`, and `gemmi sfcalc
     --scale-to` + `gemmi_rfactor.compute`

Batch end: noise scale S = MAD of each path's worsening side (Δ >= 0); the
registered thin-side fallback pools the two paths, and a still-thin pool STOPS
the round at a finding. Exclusion only when Δ < −3S on BOTH paths. D4
replacement: a representative failing the floor or the data is replaced by its
cluster's next ranked member, recorded; a cluster is exhausted, never silently
skipped. Every exclusion is named with its Δ pair and reason.

The screen writes one JSON row per attempted entry as it goes (crash-safe), and
the committed outputs are `negative_control_round1_screen.json` (all rows +
D6 statistics + P1–P4 readout) and `negative_control_round1_enrolled.json`
(the enrolled set the benchmark legs run on).

Usage:
    python3 scripts/screen_round1.py --canary            # first rep only
    python3 scripts/screen_round1.py                     # full batch
    python3 scripts/screen_round1.py --only 5OQZ,1ABC    # named subset
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import statistics
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
REPS_JSON = REPO / "ref/research/data/negative_control_round1_reps.json"
SCREEN_JSON = REPO / "ref/research/data/negative_control_round1_screen.json"
ENROLLED_JSON = REPO / "ref/research/data/negative_control_round1_enrolled.json"

FLOOR_UNMASKED = 50          # D3
SIGMA_FACTOR = 3.0           # D6: exclude at delta < -3*S on both paths
MIN_NOISE_N = 8              # D6 fallback trigger
MVD_RFREE = re.compile(r"^\s*r_free\s*:\s*([\d.]+)\s*$", re.M)


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_bench = _load("bench_refinement_deltas")     # refine protocol + PHENIX_BIN
_gold = _load("gold_mask")                    # phase-1 masks
_gr = _load("gemmi_rfactor")                  # independent R path
PHENIX_BIN = _bench.PHENIX_BIN


def fetch_pair(pdb_id: str, cache: Path) -> tuple[Path | None, Path | None, str]:
    """Deposited model + amplitudes MTZ via phenix.fetch_pdb --mtz (cached)."""
    pdb_id = pdb_id.lower()
    model, mtz = cache / f"{pdb_id}.pdb", cache / f"{pdb_id}.mtz"
    if model.exists() and mtz.exists():
        return model, mtz, ""
    # PHENIX 2.0's fetch_pdb is phil-based: the 1.x `--mtz` flag is gone (the
    # round-1 canary caught this); model+data plus convert_to_mtz=True is the
    # equivalent.
    result = subprocess.run(
        ["bash", "-c", f"cd {cache} && {PHENIX_BIN / 'phenix.fetch_pdb'} "
         f"{pdb_id} action=model+data fetch.convert_to_mtz=True "
         f"> fetch_{pdb_id}.log 2>&1"],
        capture_output=True, text=True, timeout=1800, env=dict(os.environ))
    if not model.exists() or not mtz.exists():
        tail = (cache / f"fetch_{pdb_id}.log").read_text(errors="ignore") \
            .strip().splitlines()[-2:] if (cache / f"fetch_{pdb_id}.log").exists() else []
        return (model if model.exists() else None,
                mtz if mtz.exists() else None,
                "fetch failed: " + " / ".join(tail) if tail else "fetch failed")
    return model, mtz, ""


def model_vs_data_rfree(model: Path, mtz: Path, work: Path, tag: str) -> float | None:
    log = work / f"mvd_{tag}.log"
    if not log.exists() or not MVD_RFREE.search(log.read_text(errors="ignore")):
        subprocess.run(
            ["bash", "-c", f"cd {work} && {PHENIX_BIN / 'phenix.model_vs_data'} "
             f"{model} {mtz} > {log} 2>&1"],
            capture_output=True, text=True, timeout=3600, env=dict(os.environ))
    if not log.exists():
        return None
    match = MVD_RFREE.search(log.read_text(errors="ignore"))
    return float(match.group(1)) if match else None


def gemmi_rfree(model: Path, obs_mtz: Path, work: Path, tag: str) -> float | None:
    """gemmi sfcalc (FFT, bulk solvent + scaling vs obs) + gemmi_rfactor."""
    import gemmi
    labels = [c.label for c in gemmi.read_mtz_file(str(obs_mtz)).columns]
    try:
        f_label, sig_label = _gr.pick_columns(labels, _gr.OBS_CANDIDATES, "Fobs")
    except SystemExit:
        return None                                   # intensity-only or exotic labels
    d_min = gemmi.read_mtz_file(str(obs_mtz)).resolution_high()
    calc = work / f"calc_{tag}.mtz"
    log = work / f"sfcalc_{tag}.log"
    if not calc.exists():
        subprocess.run(
            ["bash", "-c",
             f"cd {work} && gemmi sfcalc --dmin={d_min:.3f} "
             f"--scale-to={obs_mtz}:{f_label}:{sig_label} "
             f"--to-mtz={calc} {model} > {log} 2>&1"],
            capture_output=True, text=True, timeout=1800, env=dict(os.environ))
    if not calc.exists():
        return None
    try:
        result = _gr.compute(str(obs_mtz), str(calc),
                             f"{f_label},{sig_label}", None, None, None, 20)
    except SystemExit:
        return None
    return result["r_free"]


def screen_entry(rep: dict, cache: Path, work: Path) -> dict:
    """One representative through the whole registered pipeline."""
    pdb_id = rep["pdb_id"].upper()
    row: dict = {"pdb_id": pdb_id, "cluster": rep.get("cluster"),
                 "stratum": rep.get("stratum"), "d_min": rep.get("d_min"),
                 "deposit_year": rep.get("deposit_year")}

    model, mtz, fetch_err = fetch_pair(pdb_id, cache)
    if fetch_err:
        row["status"], row["reason"] = "data_defect", fetch_err
        return row

    try:
        mask = _gold.build_mask(pdb_id, cache)
    except SystemExit as exc:
        row["status"], row["reason"] = "data_defect", f"mask build failed: {exc}"
        return row
    unmasked = mask["n_residues"] - mask["n_masked"]
    row["n_unmasked"] = unmasked
    row["mask_fraction"] = mask["mask_fraction"]
    row["n_protected"] = mask["n_protected"]
    if unmasked < FLOOR_UNMASKED:
        row["status"], row["reason"] = "floor", \
            f"{unmasked} unmasked residues < {FLOOR_UNMASKED} (D3)"
        return row

    refined, r_stats = _bench.refine(model, mtz, work, restraints=False)
    if refined is None:
        row["status"] = "data_defect"
        row["reason"] = r_stats.get("failure_reason", "phenix.refine failed")
        return row
    row["in_run"] = r_stats

    deltas = {}
    for path_name, fn in (("phenix", model_vs_data_rfree), ("gemmi", gemmi_rfree)):
        pre = fn(model, mtz, work, f"{path_name}_pre_{pdb_id}")
        post = fn(refined, mtz, work, f"{path_name}_post_{pdb_id}")
        deltas[path_name] = {
            "pre": pre, "post": post,
            "delta": round(post - pre, 4) if pre is not None and post is not None
            else None}
    row["paths"] = deltas
    if any(d["delta"] is None for d in deltas.values()):
        dead = [n for n, d in deltas.items() if d["delta"] is None]
        row["status"] = "data_defect"
        row["reason"] = (f"R path(s) {dead} unmeasurable — two-path agreement "
                         f"is impossible, cannot verify at-optimum (D6)")
        return row
    row["status"] = "screened"
    return row


def mad(values: list[float]) -> float:
    med = statistics.median(values)
    return statistics.median(abs(v - med) for v in values)


def d6_statistics(rows: list[dict]) -> dict:
    """Noise scales, the registered fallback, and per-entry exclusion verdicts."""
    screened = [r for r in rows if r["status"] == "screened"]
    stats: dict = {"n_screened": len(screened)}
    sides = {}
    for path in ("phenix", "gemmi"):
        worsening = [r["paths"][path]["delta"] for r in screened
                     if r["paths"][path]["delta"] >= 0]
        sides[path] = worsening
        stats[f"{path}_worsening_n"] = len(worsening)
    if all(len(v) >= MIN_NOISE_N for v in sides.values()):
        s = {path: mad(v) for path, v in sides.items()}
        stats["fallback"] = "none"
    else:
        pooled = sides["phenix"] + sides["gemmi"]
        if len(pooled) < MIN_NOISE_N:
            stats["fallback"] = "stop"
            stats["stop_reason"] = (
                f"pooled worsening side has {len(pooled)} entries "
                f"< {MIN_NOISE_N}: the registered D6 fallback stops the round "
                f"at a finding rather than inventing a tolerance")
            return stats
        s = {path: mad(pooled) for path in sides}
        stats["fallback"] = "pooled"
    stats["noise_scale"] = {k: round(v, 4) for k, v in s.items()}
    for r in screened:
        excluded = all(r["paths"][p]["delta"] < -SIGMA_FACTOR * s[p]
                       for p in ("phenix", "gemmi"))
        one_path = [p for p in ("phenix", "gemmi")
                    if r["paths"][p]["delta"] < -SIGMA_FACTOR * s[p]]
        r["headroom_both_paths"] = excluded
        r["headroom_one_path_only"] = one_path if not excluded and one_path else []
        r["enrolled"] = not excluded
    stats["n_excluded_headroom"] = sum(1 for r in screened
                                       if r["headroom_both_paths"])
    stats["n_enrolled"] = sum(1 for r in screened if r.get("enrolled"))
    return stats


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--reps", default=str(REPS_JSON))
    ap.add_argument("--cache", default="/tmp/nc_round1_cache")
    ap.add_argument("--work", default="/tmp/nc_round1_work")
    ap.add_argument("--canary", action="store_true", help="first rep only")
    ap.add_argument("--only", default="", help="comma-separated pdb ids")
    ap.add_argument("--no-replacements", action="store_true",
                    help="screen initial reps only (P4 needs their verdicts first)")
    args = ap.parse_args()

    reps_doc = json.loads(Path(args.reps).read_text())
    queue = list(reps_doc["initial_representatives"])
    if args.only:
        wanted = {i.strip().upper() for i in args.only.split(",")}
        queue = [r for r in queue if r["pdb_id"].upper() in wanted]
    if args.canary:
        queue = queue[:1]

    cache, work = Path(args.cache), Path(args.work)
    cache.mkdir(parents=True, exist_ok=True)
    work.mkdir(parents=True, exist_ok=True)
    by_cluster = {c["cluster"]: c["members"] for c in reps_doc["clusters"]}

    rows: list[dict] = []
    attempted: set[str] = set()
    while queue:
        rep = queue.pop(0)
        if rep["pdb_id"].upper() in attempted:
            continue
        attempted.add(rep["pdb_id"].upper())
        print(f"[{rep['pdb_id']}] cluster {rep.get('cluster')} "
              f"d_min {rep.get('d_min')}", file=sys.stderr)
        row = screen_entry(rep, cache, work)
        row["initial_representative"] = rep["pdb_id"].upper() in {
            r["pdb_id"].upper() for r in reps_doc["initial_representatives"]}
        rows.append(row)
        print(f"  -> {row['status']}" +
              (f" ({row.get('reason','')})" if row["status"] != "screened" else ""),
              file=sys.stderr)
        # D4: replacement from the same cluster's ranking, recorded.
        if row["status"] in ("floor", "data_defect") and not args.canary \
                and not args.no_replacements:
            members = by_cluster.get(row["cluster"], [])
            nxt = next((m for m in members
                        if m["pdb_id"].upper() not in attempted), None)
            if nxt is not None:
                print(f"  D4 replacement: {nxt['pdb_id']}", file=sys.stderr)
                queue.insert(0, {**nxt, "cluster": row["cluster"],
                                 "stratum": row.get("stratum")})
            else:
                print(f"  cluster {row['cluster']} exhausted (recorded)",
                      file=sys.stderr)
        # Crash-safe: the record on disk is always current.
        SCREEN_JSON.write_text(json.dumps({"rows": rows}, indent=2) + "\n")

    stats = d6_statistics(rows)
    report = {"preregistration": "negative_control_round1_preregistration.md",
              "floor_unmasked": FLOOR_UNMASKED, "sigma_factor": SIGMA_FACTOR,
              "min_noise_n": MIN_NOISE_N, "rows": rows, "d6": stats}
    SCREEN_JSON.write_text(json.dumps(report, indent=2) + "\n")

    if stats.get("fallback") != "stop" and not args.canary:
        enrolled = [r for r in rows if r.get("enrolled")]
        ENROLLED_JSON.write_text(json.dumps(
            {"preregistration": "negative_control_round1_preregistration.md",
             "n_enrolled": len(enrolled), "entries": enrolled},
            indent=2) + "\n")
    print(json.dumps({"attempted": len(rows), **{k: v for k, v in stats.items()
                                                 if not isinstance(v, dict)}},
                     indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
