#!/usr/bin/env python3
"""Negative-control headroom screen: null re-refinement of candidates (#295).

Executes D3, D4 and D6 of `negative_control_round1_preregistration.md` as
amended by `negative_control_round2_preregistration.md` (R2 registered
data-array selection; R1 size criterion lives in the selector) over the
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
# Round-2 outputs (#314): the round-1 record is committed history and a
# round-2 run must never overwrite it.
REPS_JSON = REPO / "ref/research/data/negative_control_round2_reps.json"
SCREEN_JSON = REPO / "ref/research/data/negative_control_round2_screen.json"
ENROLLED_JSON = REPO / "ref/research/data/negative_control_round2_enrolled.json"

FLOOR_UNMASKED = 50          # D3
SIGMA_FACTOR = 3.0           # D6: exclude at delta < -3*S on both paths
MIN_NOISE_N = 8              # D6 fallback trigger — counted over UNIQUE structures
# D6 measurement floor for the noise scale (#318): a constant or near-constant
# worsening side would otherwise yield S ~ 0 and a zero-width tolerance where
# any jointly negative delta excludes. 5e-4 is half the last digit of the
# conventional 4-decimal R-value reporting precision.
S_FLOOR = 0.0005
MVD_RFREE = re.compile(r"^\s*r_free\s*:\s*([\d.]+)\s*$", re.M)


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_bench = _load("bench_refinement_deltas")     # refine protocol
_gold = _load("gold_mask")                    # phase-1 masks
_gr = _load("gemmi_rfactor")                  # independent R path
# Same literal as every other PHENIX-calling script — the validate.sh tool-path
# guard compares the assignment text across scripts, so an alias through another
# module would hide a divergence from it.
PHENIX_BIN = Path.home() / "phenix-2.0-5936" / "phenix_bin"


# --- Round-6 G2: the three-class column rule (registered in
# negative_control_round6_preregistration.md, census-backed) -----------------
# KEEP: enumerated experimental families. DROP: enumerated model-derived.
# UNKNOWN: a named fetch-time error — never a silent pass-through.
import re as _re

KEEP_COLUMN_PATTERNS = (
    r"^[HKL]$",
    r"^(F|FP|FOBS|F-obs|F-obs-filtered)(-\d+)?$",
    r"^(SIGF|SIGFP|SIGFOBS|SIGF-obs|SIGF-obs-filtered)(-\d+)?$",
    r"^(I|IOBS|I-obs)(-\d+)?$",
    r"^(SIGI|SIGIOBS|SIGI-obs)(-\d+)?$",
    r"^(DANO|SIGDANO)(-\d+)?$",
    r"^(F|SIGF|I|SIGI)\([+-]\)(-\d+)?$",
    r"^(R-free-flags|FreeR_flag|FREE|FreeRflag)(-\d+)?$",
)
DROP_COLUMNS = {"FC", "PHIFC", "HLA", "HLB", "HLC", "HLD",
                "FWT", "PHWT", "DELFWT", "PHDELWT", "FOM",
                "2FOFCWT", "PH2FOFCWT", "FOFCWT", "PHFOFCWT",
                "F-model", "PHIF-model"}


def classify_column(label: str) -> str:
    """'keep' | 'drop', or a loud SystemExit on an unclassified label."""
    if label in DROP_COLUMNS:
        return "drop"
    if any(_re.match(p, label) for p in KEEP_COLUMN_PATTERNS):
        return "keep"
    raise SystemExit(
        f"screen: MTZ column {label!r} matches neither the registered KEEP "
        f"families nor the DROP set — classify it by a registered change "
        f"(round-6 G2), never pass it through")


def strip_mtz(path: Path) -> list[str]:
    """Apply the three-class rule in place; returns the dropped labels.
    Observation and flag columns are preserved byte-identically."""
    import gemmi
    import numpy as np
    m = gemmi.read_mtz_file(str(path))
    labels = [c.label for c in m.columns]
    verdicts = {l: classify_column(l) for l in labels}
    dropped = [l for l in labels if verdicts[l] == "drop"]
    if not dropped:
        return []
    keep_idx = [i for i, l in enumerate(labels) if verdicts[l] == "keep"]
    out = gemmi.Mtz(with_base=False)
    out.spacegroup = m.spacegroup
    out.set_cell_for_all(m.cell)
    # #361: the rebuilt file keeps the source dataset's identity — wavelength
    # feeds f'/f'' downstream; dropping it to 0.0 is a silent data defect.
    src = m.datasets[-1] if m.datasets else None
    ds = out.add_dataset(src.dataset_name if src else "stripped")
    if src is not None:
        ds.project_name = src.project_name
        ds.crystal_name = src.crystal_name
        ds.wavelength = src.wavelength
    for i in keep_idx:
        out.add_column(m.columns[i].label, m.columns[i].type)
    data = np.array(m, copy=False)
    out.set_data(data[:, keep_idx].astype(np.float32))
    tmp = path.with_suffix(".mtz.striptmp")
    out.write_to_file(str(tmp))
    tmp.replace(path)
    return dropped


def sha256_file(path: Path) -> str:
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_or_record_hash(path: Path) -> str | None:
    """Hash-verified caching (#320): the first successful fetch records the
    file's SHA-256 in a sidecar; every reuse re-verifies. A mismatch is
    returned as a reason string — a silently mutated cache file must become a
    named data defect, never a quietly different measurement."""
    sidecar = path.with_suffix(path.suffix + ".sha256")
    digest = sha256_file(path)
    if sidecar.exists():
        recorded = sidecar.read_text().strip()
        if recorded != digest:
            return (f"cache corruption: {path.name} hash "
                    f"{digest[:12]}… != recorded {recorded[:12]}…")
    else:
        sidecar.write_text(digest + "\n")
    return None


def tool_versions() -> dict:
    """Tool identity for the run manifest (#320). The gemmi CLI resolves from
    PATH by design (homebrew), so its resolved path is RECORDED rather than
    pinned — reproducibility needs the identity, not a machine-specific
    hardcode; PHENIX is already path-pinned."""
    import shutil
    gemmi_cli = shutil.which("gemmi")
    ver = subprocess.run(["bash", "-c", "gemmi --version 2>/dev/null | head -1"],
                         capture_output=True, text=True).stdout.strip()
    import gemmi as gemmi_py
    return {"phenix_bin": str(PHENIX_BIN),
            "gemmi_cli": gemmi_cli, "gemmi_cli_version": ver or None,
            "gemmi_python": gemmi_py.__version__,
            "python": sys.version.split()[0]}


def fetch_pair(pdb_id: str, cache: Path) -> tuple[Path | None, Path | None, str]:
    """Deposited model + amplitudes MTZ via phenix.fetch_pdb --mtz (cached)."""
    pdb_id = pdb_id.lower()
    model, mtz = cache / f"{pdb_id}.pdb", cache / f"{pdb_id}.mtz"
    if model.exists() and mtz.exists():
        return model, mtz, ""
    # PHENIX 2.0's fetch_pdb is phil-based: the 1.x `--mtz` flag is gone (the
    # round-1 canary caught this); model+data plus convert_to_mtz=True is the
    # equivalent. Two attempts: the canary also caught a transient
    # IncompleteRead killing the download mid-file, so one retry (with
    # --overwrite, since partial files are then present) is cheap insurance
    # against pure network noise; a second failure is a real data defect.
    for attempt, extra in enumerate(("", "--overwrite")):
        subprocess.run(
            ["bash", "-c", f"cd {cache} && {PHENIX_BIN / 'phenix.fetch_pdb'} "
             f"{pdb_id} action=model+data fetch.convert_to_mtz=True {extra} "
             f"> fetch_{pdb_id}.log 2>&1"],
            capture_output=True, text=True, timeout=1800, env=dict(os.environ))
        if model.exists() and mtz.exists():
            break
    if not model.exists() or not mtz.exists():
        tail = (cache / f"fetch_{pdb_id}.log").read_text(errors="ignore") \
            .strip().splitlines()[-2:] if (cache / f"fetch_{pdb_id}.log").exists() else []
        return (model if model.exists() else None,
                mtz if mtz.exists() else None,
                "fetch failed: " + " / ".join(tail) if tail else "fetch failed")
    # Round-6 G2: strip model-derived columns at fetch time, BEFORE the hash
    # sidecar is written — the cache holds observations and flags only.
    dropped = strip_mtz(mtz)
    if dropped:
        print(f"  stripped {len(dropped)} derived column(s) from "
              f"{mtz.name}: {','.join(dropped)}", file=sys.stderr)
    return model, mtz, ""


# Round-2 registered rule (negative_control_round2_preregistration.md): converted
# deposited MTZs frequently carry several observation arrays, and phenix.refine
# rightly refuses to guess — 40 of round 1's 48 data defects were exactly this.
# The observation array is chosen deterministically: first amplitude pair from the
# list below present in the MTZ, then first intensity pair; no match is a named
# data defect. Amplitudes are preferred because both R paths consume F directly.
OBS_LABEL_CANDIDATES: tuple[tuple[str, str], ...] = (
    ("F-obs-filtered", "SIGF-obs-filtered"), ("F-obs", "SIGF-obs"),
    ("FOBS", "SIGFOBS"), ("FP", "SIGFP"), ("F", "SIGF"),
    ("I-obs", "SIGI-obs"), ("IOBS", "SIGIOBS"), ("I", "SIGI"))

# Converted MTZs can also carry SEVERAL R-free flag arrays (9YGW: R-free-flags
# AND R-free-flags-1) — the second ambiguity behind the first. Same registered
# treatment: first present label wins. PHENIX matches the selector by exact
# label before substring, which is what makes "R-free-flags" safe even though
# it is a prefix of "R-free-flags-1" (verified live on 9YGW).
FLAG_LABEL_CANDIDATES: tuple[str, ...] = (
    "R-free-flags", "FreeR_flag", "FREE", "FreeRflag", "R-free-flags-1")


def pick_obs_labels(labels: list[str]) -> tuple[str, str] | None:
    """First registered (obs, sigma) pair present in `labels`, else None."""
    for pair in OBS_LABEL_CANDIDATES:
        if pair[0] in labels and pair[1] in labels:
            return pair
    return None


def pick_flag_label(labels: list[str]) -> str | None:
    """First registered free-flag label present in `labels`, else None (a
    single-array MTZ needs no selector, and phenix's own detection handles a
    lone unconventional name better than a wrong guess would)."""
    for label in FLAG_LABEL_CANDIDATES:
        if label in labels:
            return label
    return None


def select_arrays(mtz: Path) -> tuple[tuple[str, str] | None, str | None]:
    """THE registered selection, computed once per entry (#317).

    Every consumer of the MTZ — phenix.refine, phenix.model_vs_data, and the
    gemmi path — receives these exact labels as arguments; none re-derives its
    own. The Codex review found the previous shape violated the registered
    "one selection rule, three consumers" claim: the gemmi path used
    gemmi_rfactor's own candidate list (different order, no F-obs-filtered)
    and autodetected its free column from a list missing R-free-flags-1.
    """
    import gemmi
    labels = [c.label for c in gemmi.read_mtz_file(str(mtz)).columns]
    return pick_obs_labels(labels), pick_flag_label(labels)


def refine_null(model: Path, mtz: Path, work: Path,
                pair: tuple[str, str], flag: str | None) -> tuple[Path | None, dict]:
    """The bench_refinement_deltas null protocol plus the registered round-2
    observation-array selection. Own prefix (r2n_) so a rerun with a different
    label rule can never silently adopt a cached round-1 output (the #124
    argument: any parameter that moves the refinement belongs in the prefix).
    `pair`/`flag` come from select_arrays — this function does no picking."""
    # PHENIX 2.0's data manager does array selection BEFORE the legacy
    # refinement.input scope is consulted, so the selector is
    # miller_array.labels.name — the exact phil the refusal message names
    # (refinement.input.xray_data.labels parses but is ignored; canaried on
    # 9YGW). One selector per ambiguous array kind.
    selectors = f"\"miller_array.labels.name={pair[0]},{pair[1]}\""
    if flag is not None:
        selectors += f" \"miller_array.labels.name={flag}\""
    prefix = f"r2n_{model.stem}"
    out = work / f"{prefix}_001.pdb"
    log = work / f"refine_{prefix}.log"
    if not out.exists():
        subprocess.run(
            ["bash", "-c",
             f"cd {work} && {PHENIX_BIN / 'phenix.refine'} {model} {mtz} "
             f"main.number_of_macro_cycles={_bench.MACRO_CYCLES} "
             f"{selectors} "
             f"output.prefix={prefix} --overwrite > {log} 2>&1"],
            capture_output=True, text=True, timeout=7200, env=dict(os.environ))
    if not out.exists():
        return None, {"failure_reason": _bench.refine_failure_reason(log)}
    r_values = _bench._R_WORK.findall(log.read_text(errors="ignore")) \
        if log.exists() else []
    stats: dict = {"obs_labels": list(pair)}
    if r_values:
        stats["r_work_pre"], stats["r_free_pre"] = \
            float(r_values[0][0]), float(r_values[0][1])
        stats["r_work_post"], stats["r_free_post"] = \
            float(r_values[-1][0]), float(r_values[-1][1])
    return out, stats


def model_vs_data_rfree(model: Path, mtz: Path, work: Path, tag: str,
                        pair: tuple[str, str], flag: str | None) -> float | None:
    """phenix.model_vs_data R-free, with the SAME registered array selection as
    the refinement, passed in from select_arrays — mvd's selectors are its own
    f_obs_label / r_free_flags_label params (the round-2 canary caught mvd
    failing on the identical ambiguity after the refine selector was fixed)."""
    selectors = f"f_obs_label=\"{pair[0]}\""
    if flag is not None:
        selectors += f" r_free_flags_label=\"{flag}\""
    log = work / f"mvd_{tag}.log"
    if not log.exists() or not MVD_RFREE.search(log.read_text(errors="ignore")):
        subprocess.run(
            ["bash", "-c", f"cd {work} && {PHENIX_BIN / 'phenix.model_vs_data'} "
             f"{model} {mtz} {selectors} > {log} 2>&1"],
            capture_output=True, text=True, timeout=3600, env=dict(os.environ))
    if not log.exists():
        return None
    match = MVD_RFREE.search(log.read_text(errors="ignore"))
    return float(match.group(1)) if match else None


def gemmi_rfree(model: Path, obs_mtz: Path, work: Path, tag: str,
                pair: tuple[str, str], flag: str | None) -> float | None:
    """gemmi sfcalc (FFT, bulk solvent + scaling vs obs) + gemmi_rfactor,
    consuming the SAME select_arrays labels as the phenix consumers (#317) —
    obs columns AND the free column are passed explicitly; gemmi_rfactor's own
    autodetection (different candidate order, no R-free-flags-1) is bypassed.
    The gemmi path needs amplitudes: an intensity pair is a named no-measure."""
    import gemmi
    f_label, sig_label = pair
    if f_label.upper().startswith("I"):
        return None                                   # intensity-only: no F for sfcalc
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
                             f"{f_label},{sig_label}", None, flag, None, 20)
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
    # Input identity (#320): hashes recorded per row; cached reuse re-verified
    # against the fetch-time sidecar.
    for f in (model, mtz):
        problem = verify_or_record_hash(f)
        if problem:
            row["status"], row["reason"] = "data_defect", problem
            return row
    row["input_hashes"] = {"model": sha256_file(model), "mtz": sha256_file(mtz)}

    try:
        mask = _gold.build_mask(pdb_id, cache)
    except SystemExit as exc:
        row["status"], row["reason"] = "data_defect", f"mask build failed: {exc}"
        return row
    for label, name in (("validation_xml", f"{pdb_id.lower()}_validation.xml"),
                        ("cif", f"{pdb_id.lower()}.cif")):
        mask_input = cache / name
        if mask_input.exists():
            row["input_hashes"][label] = sha256_file(mask_input)
    unmasked = mask["n_residues"] - mask["n_masked"]
    row["n_unmasked"] = unmasked
    row["mask_fraction"] = mask["mask_fraction"]
    row["n_protected"] = mask["n_protected"]
    if unmasked < FLOOR_UNMASKED:
        row["status"], row["reason"] = "floor", \
            f"{unmasked} unmasked residues < {FLOOR_UNMASKED} (D3)"
        return row

    # THE selection, once; every consumer below receives it verbatim (#317)
    # and the row records it.
    pair, flag = select_arrays(mtz)
    if pair is None:
        row["status"], row["reason"] = "data_defect", \
            "no registered observation labels in the MTZ"
        return row
    row["array_selection"] = {"obs": list(pair), "free_flag": flag}

    refined, r_stats = refine_null(model, mtz, work, pair, flag)
    if refined is None:
        row["status"] = "data_defect"
        row["reason"] = r_stats.get("failure_reason", "phenix.refine failed")
        return row
    row["in_run"] = r_stats

    deltas = {}
    for path_name, fn in (("phenix", model_vs_data_rfree), ("gemmi", gemmi_rfree)):
        # Tags carry the measured model's stem (#314): the deposited stem for
        # pre, the per-round refined prefix for post, so a cached measurement
        # of one protocol's output can never be adopted for another's — the
        # #124 argument applied to measurement caching.
        pre = fn(model, mtz, work, f"{path_name}_{model.stem}", pair, flag)
        post = fn(refined, mtz, work, f"{path_name}_{refined.stem}", pair, flag)
        deltas[path_name] = {
            "pre": pre, "post": post,
            # Full precision for the D6 statistics (#318); the rounded value is
            # display-only and never feeds MAD.
            "delta": post - pre if pre is not None and post is not None else None,
            "delta_display": round(post - pre, 4)
            if pre is not None and post is not None else None}
    row["paths"] = deltas
    if any(d["delta"] is None for d in deltas.values()):
        dead = [n for n, d in deltas.items() if d["delta"] is None]
        row["status"] = "data_defect"
        row["reason"] = (f"R path(s) {dead} unmeasurable — two-path agreement "
                         f"is impossible, cannot verify at-optimum (D6)")
        return row
    row["status"] = "screened"
    return row


def write_json_atomic(path: Path, payload: dict) -> None:
    """Temp-file + rename: a killed run leaves the previous record intact
    (#319 — write_text alone is not the crash-safety it claimed to be)."""
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2) + "\n")
    tmp.replace(path)


def mad(values: list[float]) -> float:
    med = statistics.median(values)
    return statistics.median(abs(v - med) for v in values)


def d6_statistics(rows: list[dict],
                  min_unmasked_shift: float | None = None) -> dict:
    """Noise scales, the registered fallback, and per-entry exclusion verdicts.

    #318 discipline: the two paths measure the SAME structure with the same
    model, data, and flags — they are paired, not independent (twice they have
    produced identical 4-decimal deltas). Every n-threshold therefore counts
    UNIQUE structures, deltas enter at full precision, and the noise scale has
    a registered floor (S_FLOOR) so a degenerate sample cannot produce a
    zero-width tolerance.

    #321 — the mask-constrained criterion (Codex-7): the global ΔR-free is
    blind to WHERE an improvement lives, so a change confined to masked
    altconf/lattice/poor-density residues can register as headroom and
    exclude an otherwise suitable control. With `min_unmasked_shift` set, a
    both-path improver is EXCLUDED only when corroborated by unmasked-region
    movement (`row["shift_unmasked"] > min_unmasked_shift`); an
    uncorroborated improver ENROLLS with `headroom_mask_attributed=True`
    (named, never silent), and an improver whose row carries no
    `shift_unmasked` is excluded conservatively with
    `headroom_unmasked_shift_missing=True`. The parameter has NO default
    value on purpose — the threshold is a registered quantity, bound by the
    screen round's preregistration that turns this on (first calibration
    datum on record: 2DDX at 0.229 mask fraction). `None` reproduces the
    rounds-1–2 behavior exactly.
    """
    screened = [r for r in rows if r["status"] == "screened"]
    stats: dict = {"n_screened": len(screened)}
    sides, side_structs = {}, {}
    for path in ("phenix", "gemmi"):
        worsening = [(r["pdb_id"], r["paths"][path]["delta"]) for r in screened
                     if r["paths"][path]["delta"] >= 0]
        sides[path] = [d for _, d in worsening]
        side_structs[path] = {p for p, _ in worsening}
        stats[f"{path}_worsening_n"] = len(worsening)
    if all(len(v) >= MIN_NOISE_N for v in side_structs.values()):
        raw_s = {path: mad(v) for path, v in sides.items()}
        stats["fallback"] = "none"
    else:
        pooled_structs = side_structs["phenix"] | side_structs["gemmi"]
        stats["pooled_worsening_unique_structures"] = len(pooled_structs)
        if len(pooled_structs) < MIN_NOISE_N:
            stats["fallback"] = "stop"
            stats["stop_reason"] = (
                f"pooled worsening side covers {len(pooled_structs)} unique "
                f"structures < {MIN_NOISE_N}: the registered D6 fallback stops "
                f"the round at a finding rather than inventing a tolerance")
            return stats
        pooled = sides["phenix"] + sides["gemmi"]
        raw_s = {path: mad(pooled) for path in sides}
        stats["fallback"] = "pooled"
    # The floor report compares the scales the mode ACTUALLY produced — not
    # per-path MADs that a pooled fallback never used (inner review r1).
    s = {path: max(v, S_FLOOR) for path, v in raw_s.items()}
    stats["noise_scale"] = {k: round(v, 6) for k, v in s.items()}
    stats["s_floor_applied"] = any(v < S_FLOOR for v in raw_s.values())
    for r in screened:
        # Deterministic re-annotation: a row re-screened after an earlier
        # pass must not inherit that pass's #321 verdicts.
        r.pop("headroom_mask_attributed", None)
        r.pop("headroom_unmasked_shift_missing", None)
        improver = all(r["paths"][p]["delta"] < -SIGMA_FACTOR * s[p]
                       for p in ("phenix", "gemmi"))
        one_path = [p for p in ("phenix", "gemmi")
                    if r["paths"][p]["delta"] < -SIGMA_FACTOR * s[p]]
        excluded = improver
        if improver and min_unmasked_shift is not None:
            shift = r.get("shift_unmasked")
            if shift is None:
                # No corroboration data at all: exclude conservatively, by
                # name — a missing instrument must not widen enrollment.
                r["headroom_unmasked_shift_missing"] = True
            elif shift <= min_unmasked_shift:
                # The improvement is not corroborated by unmasked movement:
                # mask-attributed, so the entry stays (#321).
                excluded = False
                r["headroom_mask_attributed"] = True
        r["headroom_both_paths"] = excluded
        # #390: a mask-attributed BOTH-path improver must not masquerade as
        # a one-path improver — the field is only for genuine single-path
        # improvement.
        r["headroom_one_path_only"] = (one_path if not improver and one_path
                                       else [])
        r["enrolled"] = not excluded
    stats["n_excluded_headroom"] = sum(1 for r in screened
                                       if r["headroom_both_paths"])
    stats["n_mask_attributed"] = sum(1 for r in screened
                                     if r.get("headroom_mask_attributed"))
    stats["n_enrolled"] = sum(1 for r in screened if r.get("enrolled"))
    return stats


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--reps", default=str(REPS_JSON))
    ap.add_argument("--cache",
                    default=str(Path.home() / "protstruct_bench_inputs"))
    ap.add_argument("--work", default="/tmp/nc_round1_work")
    ap.add_argument("--canary", action="store_true", help="first rep only")
    ap.add_argument("--only", default="", help="comma-separated pdb ids")
    ap.add_argument("--no-replacements", action="store_true",
                    help="screen initial reps only (P4 needs their verdicts first)")
    ap.add_argument("--out", help="output JSON for subset/diagnostic runs")
    args = ap.parse_args()

    # A diagnostic run must never overwrite the canonical record (#319 — a
    # canary already clobbered the committed round-1 screen once). Full-batch
    # mode is the ONLY mode that writes the canonical files.
    full_run = not (args.canary or args.only or args.no_replacements
                    or Path(args.reps).resolve() != REPS_JSON.resolve())
    # --out overrides in EVERY mode — an explicit flag that silently did
    # nothing on full runs was inner-review-r1's finding.
    if args.out:
        screen_out = Path(args.out)
        enrolled_out = screen_out.with_name(screen_out.stem + "_enrolled.json")
    elif full_run:
        screen_out, enrolled_out = SCREEN_JSON, ENROLLED_JSON
    else:
        screen_out = Path("/tmp/nc_screen_diagnostic.json")
        print(f"  diagnostic run: writing {screen_out} (use --out to "
              f"choose); the canonical record is untouched", file=sys.stderr)
        enrolled_out = screen_out.with_name(screen_out.stem + "_enrolled.json")
    if not full_run and (REPO / "ref") in screen_out.resolve().parents:
        # Not just the two canonical screen files: ANY committed artifact under
        # ref/ (reps records, masks, …) is off-limits to a diagnostic run
        # (#319, inner review r2).
        raise SystemExit("screen_round1: a diagnostic run may not write inside "
                         "ref/ — committed records come from full runs only (#319)")
    manifest = {"run_mode": "full" if full_run else "diagnostic",
                "flags": {"canary": args.canary, "only": args.only,
                          "no_replacements": args.no_replacements},
                "reps": str(args.reps),
                "preregistration": "negative_control_round2_preregistration.md",
                "round": 2,
                "tools": tool_versions(),
                "protocol": {"macro_cycles": _bench.MACRO_CYCLES,
                             "refine_prefix": "r2n_", "nbins": 20}}

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
        # Crash-safe for real (#319): temp + atomic rename, every row.
        write_json_atomic(screen_out, {"run": manifest, "rows": rows})

    stats = d6_statistics(rows)
    report = {"run": manifest,
              "floor_unmasked": FLOOR_UNMASKED, "sigma_factor": SIGMA_FACTOR,
              "min_noise_n": MIN_NOISE_N, "s_floor": S_FLOOR,
              "rows": rows, "d6": stats}
    write_json_atomic(screen_out, report)

    if stats.get("fallback") != "stop" and full_run:
        enrolled = [r for r in rows if r.get("enrolled")]
        write_json_atomic(enrolled_out, {
            "run": manifest, "n_enrolled": len(enrolled), "entries": enrolled})
    print(json.dumps({"attempted": len(rows), **{k: v for k, v in stats.items()
                                                 if not isinstance(v, dict)}},
                     indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
