#!/usr/bin/env python3
"""Measure `d_FSC_model_pre / d_min` for cached EM entries, before any refinement.

Round 22 found that the two entries whose model-map FSC crossing sits furthest past
their map's own stated resolution are the two largest `d_FSC_model` excursions in the
benchmark -- 9H7U (ratio 1.372, -36.15 %) and 10BU (1.360, +4.786 %). That is n = 2,
so it is a hypothesis (round 8's rule).

The reason it is testable at all is that the ratio is a **pre-refinement** quantity:
it needs only `mtriage` on the deposited model against its own map. A set can
therefore be SELECTED on it and then refined, without the selection being downstream
of the outcome. This script is that selection step.

It reuses `bench_refinement_deltas_em.measure()` rather than reimplementing the
crossing, so the screen and the benchmark compute the identical quantity -- including
the sustained-crossing rule (20 consecutive shells below 0.143) that round 9 had to
introduce because mtriage's own reported value is defeated by one anomalous shell.

The base rate matters as much as the hits, and it is DERIVED from the committed record
at the cut in force rather than written here -- this docstring used to say "2 of 36 on
record, ~5.6 %", which was true when written, and the set is now 60 (#227). Every
screened entry is written out, hit or miss, so the denominator cannot go missing the
way rounds 16-18 found it had elsewhere.

Usage:
    python3 scripts/screen_dfsc_ratio.py --cache DIR --json screened.json
    python3 scripts/screen_dfsc_ratio.py --cache DIR --cut 1.3     # round 22's cut
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import statistics
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parent.parent

# Round 22's cut, from n = 2, chosen because the ratio distribution has a clean gap
# there (1.372, 1.360, then 1.076). Round 23 SCREENED AT IT, found 0 of 24, could not
# complete the test, and then showed the cut is too conservative: the Tukey fence on
# the combined set sits at 1.074, where the base rate is double.
#
# It stayed hardcoded anyway (round 26 saw the line and declined), so the default is
# now the data-driven fence and the post-hoc one is opt-in (#226). At 1.3 a screen
# needs roughly twice the entries to reach three candidates -- ~90 against ~45, at
# 100-250 MB and ~2.5 min each -- which is the difference between a project and an
# impossible one.
TUKEY_FENCE = 1.074
POST_HOC_CUT = 1.3
DEFAULT_CUT = TUKEY_FENCE

# Where the prior base rate comes from. It used to be the literal 5.6, meaning "2 of 36
# on record" -- true when written, and the set is now 60, so every run emitted a stale
# figure into machine-readable output that round documents then quote (#227). A script
# is the one place this repo insists figures must NOT be remembered.
DELTAS_TSV = REPO / "ref/research/data/em_refinement_deltas.tsv"


def prior_base_rate(cut: float) -> dict[str, Any]:
    """The base rate above `cut` among entries already on record, derived not recalled.

    Returns the numerator and denominator alongside the percentage, because a bare
    rate with no denominator is what round 28 spent itself correcting.
    """
    import csv
    if not DELTAS_TSV.exists():
        return {"prior_base_rate_pct": None,
                "prior_note": f"no record at {DELTAS_TSV.name}"}
    ratios = []
    with DELTAS_TSV.open() as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            try:
                pre = float((row.get("d_fsc_model_pre") or "").strip())
                res = float((row.get("resolution") or "").strip())
            except ValueError:
                continue
            if res:
                ratios.append(pre / res)
    if not ratios:
        return {"prior_base_rate_pct": None, "prior_note": "no computable ratios on record"}
    hits = sum(1 for r in ratios if r > cut)
    return {"prior_base_rate_pct": round(100.0 * hits / len(ratios), 1),
            "prior_hits": hits, "prior_n": len(ratios)}


# The ratio is d_FSC_model_pre / d_min, and the 60 on record run 0.73-1.372. A cut
# outside this band selects everything or nothing, and `--cut 0` did it SILENTLY --
# reporting a 100 % base rate in well-formed JSON that a round document could quote
# (#230). Same class as #190 on round_figures: nonsense in, confident output.
CUT_MIN, CUT_MAX = 0.5, 3.0


def _cut_value(text: str) -> float:
    import argparse as _ap
    try:
        value = float(text)
    except ValueError:
        raise _ap.ArgumentTypeError(f"{text!r} is not a number")
    if not CUT_MIN <= value <= CUT_MAX:
        raise _ap.ArgumentTypeError(
            f"{value} is outside the plausible range {CUT_MIN}-{CUT_MAX}; the ratios on "
            f"record run 0.73-1.372, so this selects everything or nothing. The Tukey "
            f"fence is {TUKEY_FENCE} and round 22's post-hoc cut was {POST_HOC_CUT}")
    return value


def load_bench():
    """Import the EM benchmark so the screen measures the identical quantity."""
    spec = importlib.util.spec_from_file_location(
        "bench_em", REPO / "scripts" / "bench_refinement_deltas_em.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def screen(entries: list[dict], cache: Path,
           cut: float = DEFAULT_CUT) -> tuple[list[dict], list[dict]]:
    """Measure the pre-refinement crossing for each entry. No refinement is run."""
    bench = load_bench()
    rows, skipped = [], []
    for entry in entries:
        pdb_id = entry["pdb_id"].lower()
        resolution = float(entry["resolution"])
        model, map_file = cache / f"{pdb_id}.cif", cache / f"{pdb_id}.map"
        print(f"[{pdb_id.upper()}]", file=sys.stderr)
        if not model.exists() or not map_file.exists():
            skipped.append({"pdb_id": pdb_id.upper(), "reason": "model or map missing"})
            continue
        pre = bench.measure(model, map_file, resolution, cache, f"{pdb_id}_pre")
        crossing = pre["d_fsc_model_masked"]
        if crossing is None or not pre["d_fsc_model_plausible"]:
            reason = ("no sustained crossing" if crossing is None
                      else f"crossing {crossing:.2f} A implausible for a {resolution} A map")
            print(f"  ! {reason}", file=sys.stderr)
            skipped.append({"pdb_id": pdb_id.upper(), "reason": reason})
            continue
        ratio = crossing / resolution
        rows.append({
            "pdb_id": pdb_id.upper(), "resolution": resolution,
            "d_fsc_model_pre": crossing, "ratio": round(ratio, 4),
            "cc_mask_pre": pre["cc_mask"],
            "high_ratio": bool(ratio > cut),
        })
        print(f"  crossing {crossing:.3f} A / {resolution} A = ratio {ratio:.3f}"
              f"{'   <-- HIGH' if ratio > cut else ''}", file=sys.stderr)
    return rows, skipped


def summarize(rows: list[dict], cut: float = DEFAULT_CUT) -> dict[str, Any]:
    if not rows:
        return {"n": 0}
    ratios = [r["ratio"] for r in rows]
    hits = [r for r in rows if r["high_ratio"]]
    return {
        "n_screened": len(rows),
        "n_high_ratio": len(hits),
        "base_rate_pct": round(100.0 * len(hits) / len(rows), 1),
        "high_ratio_ids": [r["pdb_id"] for r in hits],
        "ratio_median": round(statistics.median(ratios), 4),
        "ratio_min": round(min(ratios), 4), "ratio_max": round(max(ratios), 4),
        "cut": cut,
        **prior_base_rate(cut),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cache", required=True)
    ap.add_argument("--entries", help="JSON: [{pdb_id, resolution}, ...]; default <cache>/entries.json")
    ap.add_argument("--json", dest="json_out")
    ap.add_argument("--cut", type=_cut_value, default=DEFAULT_CUT,
                    help=f"ratio above which an entry is a candidate "
                         f"(default {DEFAULT_CUT}, the Tukey fence; "
                         f"round 22's post-hoc cut was {POST_HOC_CUT})")
    args = ap.parse_args()

    cache = Path(args.cache)
    entries_path = Path(args.entries) if args.entries else cache / "entries.json"
    entries = json.loads(entries_path.read_text())

    rows, skipped = screen(entries, cache, args.cut)
    summary = summarize(rows, args.cut)
    if args.json_out:
        Path(args.json_out).write_text(
            json.dumps({"rows": rows, "skipped": skipped, "summary": summary}, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    return 0 if rows else 1


if __name__ == "__main__":
    raise SystemExit(main())
