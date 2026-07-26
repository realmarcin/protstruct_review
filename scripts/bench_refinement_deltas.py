#!/usr/bin/env python3
"""Benchmark the §4 refinement Δ-tolerances by actually refining.

`ref/thresholds_and_standards.md` §4 governs the compare→refine flow and asserts how
far a refinement may move a quantity before it counts as degradation:

  - ΔRMSD sanity            RMSD_post ≤ RMSD_pre + 0.05 Å
  - Geometry did not degrade  clashscore_post ≤ max(clashscore_pre, 4);
                              favored_post ≥ min(favored_pre, 97 %);
                              rotamer outliers_post ≤ max(outliers_pre, 2 %)

These are **not** cross-tool agreement tolerances, so none of the rounds 1-4 machinery
applies: the question is not "do two tools agree" but "how much does a refinement that
did *not* degrade the model actually move these numbers". That needs a refine →
re-measure loop, which is what this does.

Method — the null case. Each deposited model is re-refined against its own deposited
data with `phenix.refine`. The model is already at its refinement optimum, so a
correctly-behaving refinement should move these quantities very little; whatever
spread remains is the floor a Δ band has to clear.

Every tolerance above mixes a **Δ band** with an **absolute floor** (4, 97 %, 2 %).
They are different claims and only the Δ is measurable this way, so the floors are
reported separately: how often deposited structures violate them tells you whether
they are refinement checks at all or simply quality bars in disguise.

RMSD is computed **without re-superposition**, over matched (chain, resseq) Cα pairs.
Refinement preserves the coordinate frame, so the raw shift is the quantity of
interest, and superposing first would absorb part of what is being measured.

Usage:
    python3 scripts/bench_refinement_deltas.py --cache DIR --json out.json
    python3 scripts/bench_refinement_deltas.py 12LO 30IZ --cache DIR
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
from pathlib import Path
from typing import Any

PHENIX_BIN = Path.home() / "phenix-2.0-5936" / "phenix_bin"

_CLASHSCORE = re.compile(r"clashscore\s*=\s*([\d.]+)")
_RAMA_FAV = re.compile(r"SUMMARY:\s*([\d.]+)%\s*favored")
_ROTA_OUT = re.compile(r"SUMMARY:\s*([\d.]+)%\s*outliers")
_R_WORK = re.compile(r"r_work=([\d.]+)\s+r_free=([\d.]+)")

# The absolute floors embedded in the §4 tolerances, split out so they can be
# assessed as quality bars rather than as refinement deltas.
FLOOR_CLASHSCORE, FLOOR_FAVORED_PCT, FLOOR_ROTAMER_OUTLIER_PCT = 4.0, 97.0, 2.0

MACRO_CYCLES = 3


def ca_atoms(model: Path) -> dict[tuple[str, str], tuple[float, float, float]]:
    """Cα coordinates keyed by (chain, resseq+icode), altloc A or blank only."""
    out = {}
    for line in model.read_text(errors="ignore").splitlines():
        if not line.startswith("ATOM") or line[12:16].strip() != "CA":
            continue
        if line[16] not in (" ", "A"):
            continue
        key = (line[21], line[22:27].strip())
        if key not in out:
            out[key] = (float(line[30:38]), float(line[38:46]), float(line[46:54]))
    return out


def ca_shift_rmsd(before: Path, after: Path) -> tuple[float | None, int]:
    """RMSD over matched Cα pairs with NO superposition — the raw refinement shift."""
    a, b = ca_atoms(before), ca_atoms(after)
    shared = sorted(set(a) & set(b))
    if not shared:
        return None, 0
    total = sum((a[k][0] - b[k][0]) ** 2 + (a[k][1] - b[k][1]) ** 2 + (a[k][2] - b[k][2]) ** 2
                for k in shared)
    return round((total / len(shared)) ** 0.5, 4), len(shared)


def run_tool(exe: str, model: Path, work: Path, tag: str, pattern: re.Pattern) -> float | None:
    """Run a PHENIX validation tool on `model` and pull one number out of its log."""
    log = work / f"{tag}_{model.stem}.log"
    if not log.exists() or not pattern.search(log.read_text(errors="ignore")):
        subprocess.run(["bash", "-c", f"cd {work} && {PHENIX_BIN / exe} {model} > {log} 2>&1"],
                       capture_output=True, text=True, timeout=3600, env=dict(os.environ))
    if not log.exists():
        return None
    match = pattern.search(log.read_text(errors="ignore"))
    return float(match.group(1)) if match else None


def measure(model: Path, work: Path, tag: str) -> dict[str, Any]:
    """Clashscore, Ramachandran favored % and rotamer outlier % for one model."""
    return {
        "clashscore": run_tool("phenix.clashscore", model, work, f"cs_{tag}", _CLASHSCORE),
        "rama_favored_pct": run_tool("phenix.ramalyze", model, work, f"rama_{tag}", _RAMA_FAV),
        "rotamer_outlier_pct": run_tool("phenix.rotalyze", model, work, f"rota_{tag}", _ROTA_OUT),
    }


def refine(model: Path, mtz: Path, work: Path) -> tuple[Path | None, dict[str, Any]]:
    """Re-refine a deposited model against its own data; returns (refined model, R stats)."""
    prefix = f"r_{model.stem}"
    out = work / f"{prefix}_001.pdb"
    log = work / f"refine_{model.stem}.log"
    if not out.exists():
        subprocess.run(
            ["bash", "-c",
             f"cd {work} && {PHENIX_BIN / 'phenix.refine'} {model} {mtz} "
             f"main.number_of_macro_cycles={MACRO_CYCLES} output.prefix={prefix} "
             f"--overwrite > {log} 2>&1"],
            capture_output=True, text=True, timeout=7200, env=dict(os.environ))
    if not out.exists():
        return None, {}
    r_values = _R_WORK.findall(log.read_text(errors="ignore")) if log.exists() else []
    stats: dict[str, Any] = {}
    if r_values:
        stats["r_work_pre"], stats["r_free_pre"] = float(r_values[0][0]), float(r_values[0][1])
        stats["r_work_post"], stats["r_free_post"] = float(r_values[-1][0]), float(r_values[-1][1])
    return out, stats


def collect(pairs: list[tuple[Path, Path]], work: Path) -> tuple[list[dict], list[dict]]:
    """Refine each model and measure the geometry quantities before and after."""
    rows, skipped = [], []
    work.mkdir(parents=True, exist_ok=True)
    for model, mtz in pairs:
        name = model.stem.upper()
        print(f"[{name}]", file=sys.stderr)
        pre = measure(model, work, "pre")
        if pre["clashscore"] is None or pre["rama_favored_pct"] is None:
            skipped.append({"pdb_id": name, "reason": "pre-refinement validation failed"})
            continue
        refined, r_stats = refine(model, mtz, work)
        if refined is None:
            print("  ! phenix.refine failed", file=sys.stderr)
            skipped.append({"pdb_id": name, "reason": "phenix.refine failed"})
            continue
        post = measure(refined, work, "post")
        if post["clashscore"] is None or post["rama_favored_pct"] is None:
            skipped.append({"pdb_id": name, "reason": "post-refinement validation failed"})
            continue
        shift, n_ca = ca_shift_rmsd(model, refined)

        row: dict[str, Any] = {"pdb_id": name, "n_ca_matched": n_ca, "ca_shift_rmsd": shift,
                               **r_stats}
        for key in ("clashscore", "rama_favored_pct", "rotamer_outlier_pct"):
            row[f"{key}_pre"], row[f"{key}_post"] = pre[key], post[key]
            if pre[key] is not None and post[key] is not None:
                row[f"{key}_delta"] = round(post[key] - pre[key], 4)
        # Do the deposited models even satisfy the absolute floors?
        row["floor_clashscore_pre_ok"] = (pre["clashscore"] or 0) <= FLOOR_CLASHSCORE
        row["floor_favored_pre_ok"] = (pre["rama_favored_pct"] or 0) >= FLOOR_FAVORED_PCT
        row["floor_rotamer_pre_ok"] = (pre["rotamer_outlier_pct"] or 0) <= FLOOR_ROTAMER_OUTLIER_PCT
        rows.append(row)
        print(f"  Cα shift {shift} Å over {n_ca} | clash {pre['clashscore']}→{post['clashscore']}"
              f" | favored {pre['rama_favored_pct']}→{post['rama_favored_pct']}"
              f" | rota_out {pre['rotamer_outlier_pct']}→{post['rotamer_outlier_pct']}",
              file=sys.stderr)
    return rows, skipped


def summarize(rows: list[dict]) -> dict[str, Any]:
    """Δ distributions, plus how often deposited models meet the absolute floors."""
    if not rows:
        return {"n": 0}

    def stats(key: str, signed: bool = False) -> dict[str, Any]:
        values = [r[key] for r in rows if r.get(key) is not None]
        if not values:
            return {"n": 0}
        ordered = sorted(values if signed else (abs(v) for v in values))
        idx = min(len(ordered) - 1, max(0, round(0.9 * (len(ordered) - 1))))
        return {"n": len(values), "median": round(statistics.median(ordered), 4),
                "p90": round(ordered[idx], 4), "max": round(ordered[-1], 4)}

    return {
        "n_entries": len(rows),
        "ca_shift_rmsd": stats("ca_shift_rmsd"),
        "clashscore_delta": stats("clashscore_delta"),
        "rama_favored_delta_pp": stats("rama_favored_pct_delta"),
        "rotamer_outlier_delta_pp": stats("rotamer_outlier_pct_delta"),
        "absolute_floors_met_by_deposited_models": {
            "clashscore <= 4": sum(1 for r in rows if r["floor_clashscore_pre_ok"]),
            "favored >= 97 %": sum(1 for r in rows if r["floor_favored_pre_ok"]),
            "rotamer outliers <= 2 %": sum(1 for r in rows if r["floor_rotamer_pre_ok"]),
            "of": len(rows),
        },
    }


def find_pairs(cache: Path, ids: list[str] | None) -> list[tuple[Path, Path]]:
    """Match cached `<id>.pdb` with `<id>_g_obs.mtz` from the R-offset benchmark."""
    pairs = []
    for mtz in sorted(cache.glob("*_g_obs.mtz")):
        stem = mtz.name[: -len("_g_obs.mtz")]
        model = cache / f"{stem}.pdb"
        if not model.exists():
            continue
        if ids and stem.upper() not in {i.upper() for i in ids}:
            continue
        pairs.append((model, mtz))
    return pairs


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("pdb_ids", nargs="*")
    ap.add_argument("--cache", required=True,
                    help="directory holding <id>.pdb and <id>_g_obs.mtz (bench_t06_r_offset.py)")
    ap.add_argument("--work", help="where to run refinements (default: <cache>/refine)")
    ap.add_argument("--json", dest="json_out")
    args = ap.parse_args()

    cache = Path(args.cache)
    pairs = find_pairs(cache, args.pdb_ids or None)
    if not pairs:
        raise SystemExit(f"no <id>.pdb + <id>_g_obs.mtz pairs found in {cache}")
    work = Path(args.work) if args.work else cache / "refine"

    rows, skipped = collect(pairs, work)
    summary = summarize(rows)
    if args.json_out:
        Path(args.json_out).write_text(
            json.dumps({"rows": rows, "skipped": skipped, "summary": summary}, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    return 0 if rows else 1


if __name__ == "__main__":
    raise SystemExit(main())
