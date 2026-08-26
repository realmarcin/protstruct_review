#!/usr/bin/env python3
"""Guard: the negative-control series' committed records reconcile (#312).

The tolerance series has round-figure guards; the negative-control series
shipped without them, and its very first round doc carried a provenance error
(#311) of exactly the class a guard catches mechanically. This checker runs
from `validate.sh` and fails loudly when:

  - a screen record's rows are internally inconsistent (duplicate ids, unknown
    statuses, screened rows missing a path delta, d6 counts that disagree with
    the rows they summarize)
  - a screen record carries a diagnostic-run manifest — committed records come
    from full runs only (#319); records predating manifests (round 1) are
    exempt from the manifest requirement but not from row checks
  - an enrolled record lists an entry its screen record does not show as
    enrolled
  - a reps record's initial representatives are not unique, or name a cluster
    the record does not rank
  - a round doc `negative_control_round<N>.md` exists whose screen record's
    headline counts (attempted / floor / data defects / screened) do not all
    appear as literal figures in the doc — the #311 drift, mechanized

Network-free; reads only committed files. `--root` exists for the tests.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

KNOWN_STATUSES = {"screened", "floor", "data_defect", "cluster_collision"}


def fail(msg: str, failures: list[str]) -> None:
    print(f"FAIL  {msg}")
    failures.append(msg)


def check_screen(path: Path, failures: list[str]) -> dict | None:
    doc = json.loads(path.read_text())
    rows = doc.get("rows", [])
    ids = [r["pdb_id"] for r in rows]
    if len(ids) != len(set(ids)):
        fail(f"{path.name}: duplicate pdb_ids in rows", failures)
    for r in rows:
        if r["status"] not in KNOWN_STATUSES:
            fail(f"{path.name}: {r['pdb_id']} has unknown status "
                 f"{r['status']!r}", failures)
        if r["status"] == "screened":
            for p in ("phenix", "gemmi"):
                if r.get("paths", {}).get(p, {}).get("delta") is None:
                    fail(f"{path.name}: screened {r['pdb_id']} missing "
                         f"{p} delta", failures)
    run = doc.get("run")
    if run is not None and run.get("run_mode") != "full":
        fail(f"{path.name}: committed record carries a "
             f"{run.get('run_mode')!r} run manifest — full runs only (#319)",
             failures)
    d6 = doc.get("d6", {})
    n_screened = sum(1 for r in rows if r["status"] == "screened")
    if "n_screened" in d6 and d6["n_screened"] != n_screened:
        fail(f"{path.name}: d6.n_screened={d6['n_screened']} but rows hold "
             f"{n_screened}", failures)
    if "n_enrolled" in d6:
        enrolled_rows = sum(1 for r in rows if r.get("enrolled"))
        if d6["n_enrolled"] != enrolled_rows:
            fail(f"{path.name}: d6.n_enrolled={d6['n_enrolled']} but rows "
                 f"hold {enrolled_rows}", failures)
    return doc


def check_enrolled(path: Path, screen: dict | None, failures: list[str]) -> None:
    doc = json.loads(path.read_text())
    entries = {e["pdb_id"] for e in doc.get("entries", [])}
    if doc.get("n_enrolled") != len(entries):
        fail(f"{path.name}: n_enrolled={doc.get('n_enrolled')} but "
             f"{len(entries)} entries listed", failures)
    if screen is not None:
        screen_enrolled = {r["pdb_id"] for r in screen.get("rows", [])
                           if r.get("enrolled")}
        extra = entries - screen_enrolled
        if extra:
            fail(f"{path.name}: entries not enrolled in the screen record: "
                 f"{sorted(extra)}", failures)


def check_reps(path: Path, failures: list[str]) -> None:
    doc = json.loads(path.read_text())
    initial = [r["pdb_id"] for r in doc.get("initial_representatives", [])]
    if len(initial) != len(set(initial)):
        fail(f"{path.name}: duplicate initial representatives", failures)
    known_clusters = {c["cluster"] for c in doc.get("clusters", [])}
    for r in doc.get("initial_representatives", []):
        if r.get("cluster") not in known_clusters:
            fail(f"{path.name}: representative {r['pdb_id']} names unknown "
                 f"cluster {r.get('cluster')!r}", failures)


# --- #338: bench and recover records join the gate ---------------------------------

FLAG_KEYS = {"F-data", "F-geom", "F-protected", "F-shift"}
RECOVER_VERDICTS = {"DEGRADED", "FIT-DEGRADED", "not-degraded"}


def _flags_degraded(flags: dict) -> bool:
    """The registered flag rule (bench_negative_control.verdict): DEGRADED
    iff >= 2 families flag."""
    return sum(bool(v) for v in flags.values()) >= 2


def _check_full_run(doc: dict, name: str, failures: list[str]) -> None:
    run = doc.get("run")
    if run is not None and run.get("run_mode") != "full":
        fail(f"{name}: committed record carries a "
             f"{run.get('run_mode')!r} run manifest — full runs only (#319)",
             failures)


def check_bench(path: Path, failures: list[str]) -> dict | None:
    doc = json.loads(path.read_text())
    rows = doc.get("rows", [])
    keys = [(r["pdb_id"], r.get("subject")) for r in rows]
    if len(keys) != len(set(keys)):
        fail(f"{path.name}: duplicate (pdb_id, subject) rows", failures)
    for r in rows:
        who = f"{r['pdb_id']}/{r.get('subject')}"
        if r["status"] != "benched":
            fail(f"{path.name}: {who} has unknown status {r['status']!r}",
                 failures)
            continue
        flags = r.get("flags") or {}
        if set(flags) != FLAG_KEYS:
            fail(f"{path.name}: {who} flags are {sorted(flags)}, not the "
                 f"registered four families", failures)
        for p in ("d_phenix", "d_gemmi"):
            if (r.get("numbers") or {}).get(p) is None:
                fail(f"{path.name}: benched {who} missing {p}", failures)
        v = r.get("verdict")
        expect = "DEGRADED" if _flags_degraded(flags) else "not-degraded"
        if v != expect:
            fail(f"{path.name}: {who} verdict {v!r} contradicts its flags "
                 f"(registered rule says {expect!r})", failures)
    for subj, s in (doc.get("summary") or {}).items():
        srows = [r for r in rows if r.get("subject") == subj]
        derived = {
            "attempted": len(srows),
            "benched": sum(1 for r in srows if r["status"] == "benched"),
            "degraded": sum(1 for r in srows if r.get("verdict") == "DEGRADED"),
            "conflicts": sum(1 for r in srows if r.get("conflicts")),
            "protected_fixes": sum((r.get("numbers") or {})
                                   .get("n_protected_fixed", 0) for r in srows),
        }
        for k, want in derived.items():
            if k in s and s[k] != want:
                fail(f"{path.name}: summary.{subj}.{k}={s[k]} but rows hold "
                     f"{want}", failures)
    _check_full_run(doc, path.name, failures)
    return doc


def check_recover(path: Path, failures: list[str]) -> dict:
    doc = json.loads(path.read_text())
    rows = doc.get("rows", [])
    sandboxed = (doc.get("run") or {}).get("sandbox_protocol") == \
        "per-entry-process-group-v1"
    if sandboxed:
        run = doc.get("run") or {}
        set_record = run.get("set_record")
        if (not isinstance(set_record, str) or Path(set_record).is_absolute()
                or ".." in Path(set_record).parts):
            fail(f"{path.name}: sandboxed run has unsafe or missing "
                 f"set_record {set_record!r}", failures)
        else:
            root = path.parents[3]
            enrolled_path = root / set_record
            if not enrolled_path.is_file():
                fail(f"{path.name}: set_record does not exist: {set_record}",
                     failures)
            elif run.get("run_mode") == "full":
                enrolled = json.loads(enrolled_path.read_text())
                expected_ids = [e["pdb_id"].upper()
                                for e in enrolled.get("entries", [])]
                actual_ids = [r["pdb_id"].upper() for r in rows]
                if actual_ids != expected_ids:
                    missing = sorted(set(expected_ids) - set(actual_ids))
                    extra = sorted(set(actual_ids) - set(expected_ids))
                    fail(f"{path.name}: full sandboxed run does not exactly "
                         f"match {set_record} (missing={missing}, extra={extra})",
                         failures)
        perturb_record = run.get("perturbation_record")
        if (not isinstance(perturb_record, str)
                or Path(perturb_record).is_absolute()
                or ".." in Path(perturb_record).parts):
            fail(f"{path.name}: sandboxed run has unsafe or missing "
                 f"perturbation_record {perturb_record!r}", failures)
        else:
            perturb_path = path.parents[3] / perturb_record
            if not perturb_path.is_file():
                fail(f"{path.name}: perturbation_record does not exist: "
                     f"{perturb_record}", failures)
            else:
                old_rows = json.loads(perturb_path.read_text()).get("rows", [])
                old_by_id = {r["pdb_id"].upper(): r for r in old_rows}
                for row in rows:
                    if row.get("status") != "completed":
                        continue
                    who = f"{row['pdb_id']}/{row.get('subject')}"
                    old = old_by_id.get(row["pdb_id"].upper())
                    reproduction = row.get("perturbation_reproduction") or {}
                    if old is None:
                        fail(f"{path.name}: {who} absent from "
                             f"{perturb_record}", failures)
                        continue
                    expected = {
                        "committed_unmasked": old.get("achieved_shift_unmasked"),
                        "regenerated_unmasked": row.get(
                            "achieved_shift_unmasked"),
                        "absdiff_unmasked": round(abs(
                            row["achieved_shift_unmasked"]
                            - old["achieved_shift_unmasked"]), 4),
                        "committed_all": old.get("achieved_shift_all"),
                        "regenerated_all": row.get("achieved_shift_all"),
                        "absdiff_all": round(abs(
                            row["achieved_shift_all"]
                            - old["achieved_shift_all"]), 4),
                    }
                    if reproduction != expected:
                        fail(f"{path.name}: {who} perturbation reproduction "
                             f"does not match {perturb_record}", failures)
    keys = [(r["pdb_id"], r.get("subject")) for r in rows]
    if len(keys) != len(set(keys)):
        fail(f"{path.name}: duplicate (pdb_id, subject) rows", failures)
    for r in rows:
        who = f"{r['pdb_id']}/{r.get('subject')}"
        if r["status"] not in {"completed", "data_defect"}:
            fail(f"{path.name}: {who} has unknown status {r['status']!r}",
                 failures)
            continue
        if r["status"] != "completed":
            continue
        rec = r.get("recovered") or {}
        if rec.get("status") != "judged":
            fail(f"{path.name}: completed {who} not judged "
                 f"({rec.get('status')!r})", failures)
            continue
        flags = rec.get("flags") or {}
        if set(flags) != FLAG_KEYS:
            fail(f"{path.name}: {who} flags are {sorted(flags)}, not the "
                 f"registered four families", failures)
        v = rec.get("verdict")
        if v not in RECOVER_VERDICTS:
            fail(f"{path.name}: {who} verdict {v!r} outside the vocabulary",
                 failures)
        # Registered precedence: DEGRADED (flags) > FIT-DEGRADED > not-
        # degraded; fit_degraded None (REFMAC-unmeasurable fallback) is falsy.
        expect = ("DEGRADED" if _flags_degraded(flags)
                  else "FIT-DEGRADED" if rec.get("fit_degraded")
                  else "not-degraded")
        if v != expect:
            fail(f"{path.name}: {who} verdict {v!r} contradicts its evidence "
                 f"(precedence says {expect!r})", failures)
        if "two_path_only" in rec:
            want_tp = (rec.get("numbers") or {}).get("d_refmac") is None
            if bool(rec["two_path_only"]) != want_tp:
                fail(f"{path.name}: {who} two_path_only={rec['two_path_only']}"
                     f" but d_refmac is "
                     f"{'absent' if want_tp else 'present'}", failures)
        if sandboxed:
            sandbox = r.get("sandbox")
            expected_sandbox = r["pdb_id"].upper()
            if sandbox != expected_sandbox:
                fail(f"{path.name}: {who} sandbox {sandbox!r} is not its "
                     f"entry directory {expected_sandbox!r}", failures)
            pgid = r.get("pgid")
            processes = r.get("processes") or {}
            refine = processes.get("refine") or {}
            if not isinstance(pgid, int) or pgid <= 0:
                fail(f"{path.name}: {who} has no positive recorded pgid",
                     failures)
            if refine.get("pgid") != pgid:
                fail(f"{path.name}: {who} row pgid {pgid!r} disagrees with "
                     f"its refine process {refine.get('pgid')!r}", failures)
            for stage in ("dynamics", "ready_set", "refine"):
                process = processes.get(stage) or {}
                if process.get("start_new_session") is not True:
                    fail(f"{path.name}: {who} {stage} did not record "
                         f"start_new_session=True", failures)
                if process.get("returncode") != 0:
                    fail(f"{path.name}: {who} {stage} returncode is "
                         f"{process.get('returncode')!r}, not a normal exit",
                         failures)
                cache_inputs = process.get("cache_input_hashes")
                if (not isinstance(cache_inputs, dict) or not cache_inputs
                        or any(
                            not isinstance(key, str)
                            or not isinstance(value, str)
                            or not re.fullmatch(r"[0-9a-f]{64}", value)
                            for key, value in cache_inputs.items()
                        )):
                    fail(f"{path.name}: {who} {stage} has no content-addressed "
                         f"input identity", failures)
                output_hash = process.get("output_sha256")
                if (not isinstance(output_hash, str)
                        or not re.fullmatch(r"[0-9a-f]{64}", output_hash)):
                    fail(f"{path.name}: {who} {stage} has no valid output "
                         f"content hash", failures)
            if r.get("refinement_terminated_by_signal") is not False:
                fail(f"{path.name}: {who} refinement was signal-terminated",
                     failures)
            if r.get("store_unchanged") is not True:
                fail(f"{path.name}: {who} did not prove the shared store "
                     f"byte-unchanged", failures)
            if r.get("refmac_convention") != "ANIS":
                fail(f"{path.name}: {who} mixes or omits the ANIS REFMAC "
                     f"convention", failures)
            anis_logs = r.get("anis_log_verification") or {}
            if anis_logs != {"checked": 2, "with_anis": 2}:
                fail(f"{path.name}: {who} does not prove ANIS in both "
                     f"pre/post REFMAC logs", failures)
    summary = doc.get("summary") or {}
    groups = ({None: summary} if "attempted" in summary
              else {subj: s for subj, s in summary.items()})
    for subj, s in groups.items():
        srows = [r for r in rows if subj is None or r.get("subject") == subj]
        derived = {
            "attempted": len(srows),
            "completed": sum(1 for r in srows if r["status"] == "completed"),
            "successes": sum(1 for r in srows if r.get("recovery_success")),
            "v2_recovery_success": sum(1 for r in srows
                                       if r.get("recovery_success")),
            "two_path_only": sum(1 for r in srows
                                 if (r.get("recovered") or {})
                                 .get("two_path_only")),
            "w4_contradictions": sum(1 for r in srows
                                     if r.get("w4_contradiction")),
            "excluded_by_ruling": sum(1 for r in srows
                                      if r["status"] == "data_defect"),
        }
        label = "summary" if subj is None else f"summary.{subj}"
        for k, want in derived.items():
            if k in s and s[k] != want:
                fail(f"{path.name}: {label}.{k}={s[k]} but rows hold {want}",
                     failures)
    if sandboxed:
        completed = [r for r in rows if r.get("status") == "completed"]
        sandboxes = [r.get("sandbox") for r in completed]
        pgids = [r.get("pgid") for r in completed]
        if len(sandboxes) != len(set(sandboxes)):
            fail(f"{path.name}: sandbox directories are not unique", failures)
        if len(pgids) != len(set(pgids)):
            fail(f"{path.name}: recorded process groups are not unique",
                 failures)
        verification = (doc.get("summary") or {}).get("sandbox_verification") or {}
        derived = {
            "distinct_sandboxes": len(set(sandboxes)),
            "distinct_pgids": len(set(pgids)),
            "signal_terminated": sum(
                1 for r in completed if r.get("refinement_terminated_by_signal")
            ),
            "store_mutations": sum(
                1 for r in completed if not r.get("store_unchanged")
            ),
        }
        for key, want in derived.items():
            if verification.get(key) != want:
                fail(f"{path.name}: sandbox_verification.{key}="
                     f"{verification.get(key)!r} but rows hold {want}", failures)
        anis_summary = (doc.get("summary") or {}).get("anis_verification") or {}
        anis_derived = {
            "measurable": sum(
                (r.get("recovered") or {}).get("numbers", {}).get("d_refmac")
                is not None for r in completed
            ),
            "mixed_convention_rows": sum(
                r.get("refmac_convention") != "ANIS" for r in completed
            ),
            "logs_checked": sum(
                (r.get("anis_log_verification") or {}).get("checked", 0)
                for r in completed
            ),
            "logs_with_anis": sum(
                (r.get("anis_log_verification") or {}).get("with_anis", 0)
                for r in completed
            ),
        }
        if anis_summary != anis_derived:
            fail(f"{path.name}: anis_verification summary {anis_summary!r} "
                 f"but rows derive {anis_derived!r}", failures)
        ready_h = [
            (r.get("processes") or {}).get("hydrogen_count_ready")
            for r in completed
        ]
        refined_h = [
            (r.get("processes") or {}).get("hydrogen_count_refined")
            for r in completed
        ]
        if any(not isinstance(value, int) or value <= 0
               for value in ready_h + refined_h):
            fail(f"{path.name}: hydrogen counts are missing or non-positive",
                 failures)
        else:
            hydrogen_derived = {
                "models": len(ready_h),
                "minimum_ready": min(ready_h, default=None),
                "maximum_ready": max(ready_h, default=None),
                "retained_equal": sum(
                    ready == refined
                    for ready, refined in zip(ready_h, refined_h, strict=True)
                ),
            }
            hydrogen_summary = (doc.get("summary") or {}).get(
                "hydrogen_verification") or {}
            if hydrogen_summary != hydrogen_derived:
                fail(f"{path.name}: hydrogen_verification summary "
                     f"{hydrogen_summary!r} but rows derive "
                     f"{hydrogen_derived!r}", failures)
        comparison_record = run.get("comparison_record")
        if (not isinstance(comparison_record, str)
                or Path(comparison_record).is_absolute()
                or ".." in Path(comparison_record).parts):
            fail(f"{path.name}: sandboxed run has unsafe or missing "
                 f"comparison_record {comparison_record!r}", failures)
        else:
            comparison_path = path.parents[3] / comparison_record
            if not comparison_path.is_file():
                fail(f"{path.name}: comparison_record does not exist: "
                     f"{comparison_record}", failures)
            else:
                old_rows = json.loads(comparison_path.read_text()).get("rows", [])
                old_subject = "osol"
                old_subject_rows = [
                    r for r in old_rows if r.get("subject") == old_subject
                ]
                old_successes = {
                    r["pdb_id"].upper() for r in old_subject_rows
                    if r.get("recovery_success")
                }
                current_successes = {
                    r["pdb_id"].upper() for r in completed
                    if r.get("recovery_success")
                }
                comparison_derived = {
                    "record": comparison_record,
                    "osol_attempted": len(old_subject_rows),
                    "osol_successes": len(old_successes),
                    "osol_h_attempted": len(completed),
                    "osol_h_successes": len(current_successes),
                    "gained": sorted(current_successes - old_successes),
                    "lost": sorted(old_successes - current_successes),
                }
                comparison_summary = (doc.get("summary") or {}).get(
                    "comparison_with_osol") or {}
                if comparison_summary != comparison_derived:
                    fail(f"{path.name}: comparison_with_osol summary "
                         f"{comparison_summary!r} but records derive "
                         f"{comparison_derived!r}", failures)
        reproductions = [r.get("perturbation_reproduction") or {}
                         for r in completed]
        perturb_summary = (doc.get("summary") or {}).get(
            "perturbation_reproduction") or {}
        perturb_derived = {
            "n": len(reproductions),
            "max_absdiff_unmasked": max(
                (r.get("absdiff_unmasked") for r in reproductions),
                default=None),
            "max_absdiff_all": max(
                (r.get("absdiff_all") for r in reproductions), default=None),
        }
        if perturb_summary != perturb_derived:
            fail(f"{path.name}: perturbation_reproduction summary "
                 f"{perturb_summary!r} but rows derive {perturb_derived!r}",
                 failures)
        run = doc.get("run") or {}
        if run.get("refmac_convention") != "ANIS":
            fail(f"{path.name}: sandboxed run does not declare ANIS REFMAC",
                 failures)
    _check_full_run(doc, path.name, failures)
    return doc


def check_bench_round_doc(md: Path, bench: dict, failures: list[str]) -> None:
    """The bench round's registered headline (Q1: false verdicts on nulls)
    must appear as its degraded/attempted figure in the round doc."""
    text = md.read_text()
    rows = bench.get("rows", [])
    null_rows = [r for r in rows if r.get("subject") == "null"]
    if not null_rows:
        return
    degraded = sum(1 for r in null_rows if r.get("verdict") == "DEGRADED")
    headline = f"{degraded}/{len(null_rows)}"
    if headline not in text:
        fail(f"{md.name}: Q1 headline {headline!r} (null degraded/attempted) "
             f"not in the doc — record and prose have drifted (#311 class)",
             failures)


def check_recover_round_doc(md: Path, recover: dict,
                            failures: list[str]) -> None:
    """Guard the evidence-bearing NC-10 prose headlines (#419)."""
    if (recover.get("run") or {}).get("sandbox_protocol") != \
            "per-entry-process-group-v1":
        return
    text = md.read_text()
    summary = recover.get("summary") or {}
    subject = summary.get("osol_h") or {}
    anis = summary.get("anis_verification") or {}
    hydrogen = summary.get("hydrogen_verification") or {}
    comparison = summary.get("comparison_with_osol") or {}
    sandbox = summary.get("sandbox_verification") or {}
    perturb = summary.get("perturbation_reproduction") or {}
    success = f"{subject.get('successes')}/{subject.get('attempted')}"
    old_success = (
        f"{comparison.get('osol_successes')}/{comparison.get('osol_attempted')}"
    )
    anis_fraction = f"{anis.get('measurable')}/{anis.get('measurable')}"
    h_range = (
        f"{hydrogen.get('minimum_ready')}–{hydrogen.get('maximum_ready')}"
    )
    h_retained = f"{hydrogen.get('retained_equal')}/{hydrogen.get('models')}"
    required = {
        "osol_h success": rf"osol_h[^0-9\n]{{0,80}}{re.escape(success)}",
        "osol comparison": rf"osol[^0-9\n]{{0,80}}{re.escape(old_success)}",
        "ANIS measurability": rf"ANIS[^0-9\n]{{0,80}}{re.escape(anis_fraction)}",
        "H/D range": rf"{re.escape(h_range)}[^\n]{{0,30}}model",
        "H/D retention": rf"retained[^0-9\n]{{0,80}}{re.escape(h_retained)}",
        "ANIS log count": rf"all[^0-9\n]{{0,20}}{anis.get('logs_with_anis')}[^\n]{{0,30}}log",
        "sandbox count": (
            rf"{sandbox.get('distinct_sandboxes')} distinct sandbox"
        ),
        "PGID count": rf"{sandbox.get('distinct_pgids')} distinct refinement PGID",
        "unmasked reproduction": (
            rf"{perturb.get('max_absdiff_unmasked')} Å unmasked"
        ),
        "all-residue reproduction": (
            rf"{perturb.get('max_absdiff_all')} Å all-residue"
        ),
    }
    for label, pattern in required.items():
        if not re.search(pattern, text, re.IGNORECASE):
            fail(f"{md.name}: {label} headline is absent — "
                 f"record and prose have drifted (#419)", failures)
    gained = comparison.get("gained") or []
    if gained and any(pdb_id not in text for pdb_id in gained):
        fail(f"{md.name}: gained-success list is absent or incomplete (#419)",
             failures)
    if (comparison.get("lost") == []
            and not re.search(r"No old success was\s+lost", text)):
        fail(f"{md.name}: zero-loss comparison is absent (#419)", failures)


def check_round_doc(md: Path, screen: dict, failures: list[str]) -> None:
    """Each headline count must appear NEAR its keyword — a bare
    number-presence check passes whenever another identical digit exists
    anywhere in the doc (the guard's own test caught that weakness)."""
    text = md.read_text()
    rows = screen.get("rows", [])
    from collections import Counter
    counts = Counter(r["status"] for r in rows)
    figures = {"attempt": len(rows), "floor": counts.get("floor", 0),
               "defect": counts.get("data_defect", 0),
               "screened": counts.get("screened", 0)}
    for keyword, value in figures.items():
        # A 20-char window: wide enough for "attempted **71 entries**" and
        # "1 fully screened", narrow enough that a neighboring figure's digit
        # cannot satisfy the wrong keyword (the guard's test caught an 80-char
        # window doing exactly that).
        near = (rf"\*{{0,2}}\b{value}\b[^.\n]{{0,20}}{keyword}|"
                rf"{keyword}[^.\n]{{0,20}}\*{{0,2}}\b{value}\b")
        if not re.search(near, text, re.IGNORECASE):
            fail(f"{md.name}: figure {value} not found near {keyword!r} — "
                 f"record and prose have drifted (#311 class)", failures)


KNOWN_FAMILIES = {"screen", "enrolled", "reps", "bench", "recover"}
RECORD_RE = re.compile(r"negative_control_round(\d+)_([a-z0-9]+)\.json")


def check_orphan_family(path: Path, research: Path, failures: list[str]) -> None:
    """#434: record families the per-family checks above do not open
    (hygiene, attribution, closeout, anis, echo, and any future one) must
    still parse, carry a run manifest, and be cited by filename from their
    round doc. Passing 3b must mean every committed record was looked at."""
    match = RECORD_RE.match(path.name)
    if not match or match.group(2) in KNOWN_FAMILIES:
        return
    rec = json.loads(path.read_text())
    run = rec.get("run") if isinstance(rec, dict) else None
    if not isinstance(run, dict):
        fail(f"{path.name}: no run manifest block", failures)
    else:
        if run.get("round") != int(match.group(1)):
            fail(f"{path.name}: run.round {run.get('round')!r} does not "
                 f"match the filename", failures)
        prereg = run.get("preregistration")
        target = (research / prereg).resolve() if isinstance(prereg, str) else None
        if (target is None or not target.is_file()
                or research.resolve() not in target.parents):
            fail(f"{path.name}: run.preregistration {prereg!r} is not a "
                 f"committed document", failures)
        if not isinstance(run.get("tools"), dict) or not run["tools"]:
            fail(f"{path.name}: run.tools missing or empty", failures)
        if "run_mode" in run and run["run_mode"] != "full":
            fail(f"{path.name}: committed record carries a "
                 f"{run['run_mode']!r} run manifest — full runs only (#319)",
                 failures)
    doc = research / f"negative_control_round{match.group(1)}.md"
    if not doc.exists():
        fail(f"{path.name}: no round doc {doc.name}", failures)
    elif path.name not in doc.read_text():
        fail(f"{path.name}: not cited by filename in {doc.name}", failures)


REGISTRY_ROWS = {
    # row label fragment -> (constant name in bench_recover_leg)
    "ISOT convention": "REGISTERED_FIT_THRESHOLDS",
    "ANIS convention": "REGISTERED_FIT_THRESHOLDS_ANIS",
}
TRIPLE_RE = re.compile(r"d_phenix \*\*([\d.]+)\*\*, d_gemmi \*\*([\d.]+)\*\*"
                       r"(?: \([^)]*\))?, d_refmac \*\*([\d.]+)\*\*")


def registry_section(text: str) -> str | None:
    match = re.search(r"^## 6\. Negative-control verdict rules.*?(?=^## |\Z)",
                      text, re.S | re.M)
    return match.group(0) if match else None


def check_registry_section(text: str, constants: dict, failures: list[str],
                           label: str = "thresholds_and_standards.md") -> None:
    """#433: the registry's section 6 restates bench_recover_leg's registered
    constants — the doc is checked against the machine-readable source, not
    the other way round (#293: one source, no new per-figure parser)."""
    sec = registry_section(text)
    if sec is None:
        fail(f"{label}: no '## 6. Negative-control verdict rules' section",
             failures)
        return
    for fragment, const in REGISTRY_ROWS.items():
        rows = [line for line in sec.splitlines()
                if line.startswith("| FIT thresholds") and fragment in line]
        if len(rows) != 1:
            fail(f"{label}: expected one FIT-thresholds row for {fragment}, "
                 f"found {len(rows)}", failures)
            continue
        m = TRIPLE_RE.search(rows[0])
        if not m:
            fail(f"{label}: {fragment} row has no bold d_phenix/d_gemmi/"
                 f"d_refmac triple", failures)
            continue
        got = {"d_phenix": float(m.group(1)), "d_gemmi": float(m.group(2)),
               "d_refmac": float(m.group(3))}
        if got != constants[const]:
            fail(f"{label}: {fragment} row states {got}, {const} is "
                 f"{constants[const]}", failures)
    m = re.search(r"Set: \*\*\{([^}]*)\}\*\*", sec)
    if not m:
        fail(f"{label}: stand-down row has no bold set", failures)
    else:
        got = {s.strip() for s in m.group(1).split(",") if s.strip()}
        want = set(constants["CANDIDATE_LEG_THIRD_OPINION_STANDDOWN"])
        if got != want:
            fail(f"{label}: stand-down set {sorted(got)} != registered "
                 f"{sorted(want)}", failures)
    m = re.search(r"S_r2 = [^|]*?\*\*([\d.]+) / ([\d.]+)\*\*", sec)
    if not m:
        fail(f"{label}: F-data row has no bold S_r2 pair", failures)
    elif ((float(m.group(1)), float(m.group(2)))
          != (constants["S_R2"]["phenix"], constants["S_R2"]["gemmi"])):
        fail(f"{label}: S_r2 {m.group(1)}/{m.group(2)} != record "
             f"{constants['S_R2']}", failures)
    if "above **2×** its threshold" not in sec:
        fail(f"{label}: W4 row must state the 2× bound in bold", failures)
    for phrase, key in ((r"MAD floored at \*\*([\d.]+)\*\*", "MAD_FLOOR"),
                        (r"unmasked Cα shift > \*\*([\d.]+) Å\*\*", "SHIFT_BAND_A")):
        m = re.search(phrase, sec)
        if not m:
            fail(f"{label}: no bold {key} figure", failures)
        elif float(m.group(1)) != constants[key]:
            fail(f"{label}: {key} stated {m.group(1)}, registered "
                 f"{constants[key]}", failures)


def registered_constants(scripts: Path) -> dict:
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "brl", scripts / "bench_recover_leg.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["brl"] = mod
    spec.loader.exec_module(mod)
    return {
        "REGISTERED_FIT_THRESHOLDS": mod.fit_thresholds_from_record(),
        "REGISTERED_FIT_THRESHOLDS_ANIS": mod.anis_thresholds_from_record(),
        "CANDIDATE_LEG_THIRD_OPINION_STANDDOWN":
            mod.CANDIDATE_LEG_THIRD_OPINION_STANDDOWN,
        "S_R2": mod.s_r2_from_record(),
        "MAD_FLOOR": mod.MAD_FLOOR,
        "SHIFT_BAND_A": mod.SHIFT_BAND_A,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=str(Path(__file__).resolve().parent.parent))
    args = ap.parse_args()
    root = Path(args.root)
    research = root / "ref" / "research"
    data = research / "data"
    failures: list[str] = []

    def guarded(fn, path, *fn_args):
        """A malformed committed record is a NAMED failure, not a traceback —
        the gate must say which file and why (inner review r1)."""
        try:
            return fn(path, *fn_args)
        except (json.JSONDecodeError, KeyError, TypeError, OSError) as exc:
            fail(f"{path.name}: unreadable or malformed record "
                 f"({type(exc).__name__}: {exc})", failures)
            return None

    screens: dict[str, dict] = {}
    for path in sorted(data.glob("negative_control_round*_screen.json")):
        match = re.match(r"negative_control_round(\d+)_screen\.json", path.name)
        screen = guarded(check_screen, path, failures)
        if screen is not None and match:
            screens[match.group(1)] = screen
    for path in sorted(data.glob("negative_control_round*_enrolled.json")):
        match = re.match(r"negative_control_round(\d+)_enrolled\.json", path.name)
        guarded(check_enrolled, path,
                screens.get(match.group(1)) if match else None, failures)
    for path in sorted(data.glob("negative_control_round*_reps.json")):
        guarded(check_reps, path, failures)
    benches: dict[str, dict] = {}
    for path in sorted(data.glob("negative_control_round*_bench.json")):
        match = re.match(r"negative_control_round(\d+)_bench\.json", path.name)
        bench = guarded(check_bench, path, failures)
        if bench is not None and match:
            benches[match.group(1)] = bench
    recovers: dict[str, dict] = {}
    for path in sorted(data.glob("negative_control_round*_recover.json")):
        match = re.match(r"negative_control_round(\d+)_recover\.json", path.name)
        recover = guarded(check_recover, path, failures)
        if recover is not None and match:
            recovers[match.group(1)] = recover
    for md in sorted(research.glob("negative_control_round*.md")):
        match = re.match(r"negative_control_round(\d+)\.md", md.name)
        if match and match.group(1) in benches:
            guarded(check_bench_round_doc, md, benches[match.group(1)],
                    failures)
    for md in sorted(research.glob("negative_control_round*.md")):
        match = re.match(r"negative_control_round(\d+)\.md", md.name)
        if match and match.group(1) in screens:
            guarded(check_round_doc, md, screens[match.group(1)], failures)
    for md in sorted(research.glob("negative_control_round*.md")):
        match = re.match(r"negative_control_round(\d+)\.md", md.name)
        if match and match.group(1) in recovers:
            guarded(check_recover_round_doc, md, recovers[match.group(1)],
                    failures)

    for path in sorted(data.glob("negative_control_round*.json")):
        guarded(check_orphan_family, path, research, failures)
    # #433: the registry section restates the record-derived constants.
    # Enforced whenever --root is this script's own checkout (the gate's
    # path) or the tree carries bench_recover_leg.py; only synthetic
    # guard-test trees are skipped — a moved script cannot fail open (#442).
    own_repo = Path(__file__).resolve().parent.parent
    brl = root / "scripts" / "bench_recover_leg.py"
    registry = root / "ref" / "thresholds_and_standards.md"
    if root.resolve() == own_repo or brl.exists():
        if not brl.exists():
            fail("scripts/bench_recover_leg.py missing — §6 cannot be checked",
                 failures)
        elif not registry.exists():
            fail("ref/thresholds_and_standards.md missing", failures)
        else:
            try:
                consts = registered_constants(root / "scripts")
            except (SystemExit, Exception) as exc:  # noqa: BLE001
                fail(f"bench_recover_leg constants do not re-derive "
                     f"({type(exc).__name__}: {exc})", failures)
            else:
                check_registry_section(registry.read_text(), consts, failures)

    if failures:
        print(f"{len(failures)} negative-control record failure(s)")
        return 1
    print("negative-control records reconcile")
    return 0


if __name__ == "__main__":
    sys.exit(main())
