#!/usr/bin/env python3
"""Re-derive the registry's dataset-dependent figures and diff them against the text.

`ref/thresholds_and_standards.md` quotes numbers computed from
`ref/research/data/em_refinement_deltas.tsv`. That file grows every round, so those
numbers age -- silently, because nothing recomputes them. Three instances were caught,
all three by accident during reviews of unrelated work:

  #72   rho = +0.397 "over 44 entries", round-16 vintage, unlabelled, and a second
        "44" being used as a live denominator.
  #107  the CC_mask rate statistics were round-17 vintage (n = 25) after round 19
        took the set to 35. Re-deriving them confirmed the verdict and moved every
        number.
  #113  the "named entries" convention yielded 93 rather than the 69 it stated, once
        round 23 appended 24 screening-only rows.

Catching a class three times by luck is not a process. This is the gate.

HOW IT WORKS. Each check pairs a literal string that must appear in the registry with
a function that recomputes it from the TSV. A check fails if either

  - the recomputed value differs from what the registry states -- the figure aged; or
  - the literal is absent -- someone reworded the claim, so it needs re-checking by a
    human rather than silently passing.

The second half matters as much as the first. A gate that only compares numbers is
defeated by a rewrite, which is exactly how a figure escapes notice.

Deliberately NOT checked here: the §3 rows. Their sets are fixed and committed
(round 18), so those figures cannot age without someone editing a `DEFAULT_SET` --
which `scripts/validate.sh` already gates separately.

Usage:
    python3 scripts/check_registry_figures.py          # exits 1 on any divergence
    python3 scripts/check_registry_figures.py --json out.json
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import statistics
import sys
from pathlib import Path
from typing import Any, Callable

from scipy import stats

def _load_vocabulary():
    """The declared status vocabulary, from the script that WRITES the file."""
    spec = importlib.util.spec_from_file_location(
        "bench_em_status", Path(__file__).resolve().parent / "bench_refinement_deltas_em.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.STATUS_PREFIXES, module.status_is_known


_VOCAB, _IS_KNOWN = _load_vocabulary()

REGISTRY = "ref/thresholds_and_standards.md"
TSV = "ref/research/data/em_refinement_deltas.tsv"


def load(path: Path) -> list[dict[str, str]]:
    lines = path.read_text().splitlines()
    header = lines[0].split("\t")
    return [dict(zip(header, l.split("\t"))) for l in lines[1:] if l.strip()]


# --- the derivations, each one line of intent -------------------------------------

def _status_is(row, token: str) -> bool:
    """Does this row's status match the DECLARED token, delimiter included?

    #152: `status_is_known` was tightened in #148 to match on each status's delimiter,
    and these predicates were not — they kept the bare `startswith("skipped")` that #148
    removed, so `skipped-early: ...` was excluded from `_attempted` as though it were a
    real skip. Nothing escaped only because `vocabulary_check` rejects such a row
    independently; the denominators were right because a separate check happened to fail
    first, which is a backstop rather than correctness. One rule, one copy.
    """
    matches = [(d, rule) for d, (rule, _) in _VOCAB.items() if d.startswith(token)]
    if not matches:
        raise KeyError(f"{token!r} is not a declared status token")
    if len(matches) > 1:
        # An AMBIGUOUS token resolved silently by dict order, which is the same shape as
        # the defects this function was written to fix (#153). No two declared statuses
        # share a prefix today; the trigger is someone adding one, i.e. exactly what the
        # vocabulary exists to support. Fail rather than pick.
        raise KeyError(
            f"{token!r} matches {len(matches)} declared statuses "
            f"({[d for d, _ in matches]}) — the predicate cannot tell which is meant; "
            f"use the full status token")
    declared, rule = matches[0]
    return row["status"] == declared if rule == "exact" else \
        row["status"].startswith(declared)


def _named(rows):
    """Entries that entered the refinement benchmark.

    Excludes the 4 unidentified `LOST` rows AND the `screened only` rows, which were
    measured pre-refinement to test a hypothesis and never refined (#113). Both are in
    the file; neither is part of the benchmark's denominator.
    """
    return [r for r in rows
            if not r["pdb_id"].startswith("UNKNOWN")
            and not _status_is(r, "screened only")]


def _cc_deltas(rows):
    return [float(r["cc_mask_delta"]) for r in rows if r["cc_mask_delta"]]


def _dfsc_pcts(rows):
    return [float(r["d_fsc_model_delta_pct"]) for r in rows if r.get("d_fsc_model_delta_pct")]


def _dfsc_degradations(rows):
    return sorted(x for x in _dfsc_pcts(rows) if x > 0)


def _ratios(rows):
    return [float(r["d_fsc_model_pre"]) / float(r["resolution"])
            for r in rows if r.get("d_fsc_model_pre") and r.get("resolution")]


def _attempted(rows):
    """Of the entries that entered the benchmark, those not skipped."""
    return [r for r in _named(rows) if not _status_is(r, "skipped")]


def _with_delta(rows):
    return [r for r in _named(rows) if r["cc_mask_delta"]]


def _measured(rows):
    return [r for r in _named(rows) if _status_is(r, "measured")]


def _attempted_incl_lost(rows):
    """Refinement attempts over the whole file, i.e. including the 4 `LOST` rows.

    This is the registry's 63. It does NOT nest under the 69 -- that was #115 -- so it
    is stated against its own base and checked against its own derivation.
    """
    return [r for r in rows
            if not _status_is(r, "screened only") and not _status_is(r, "skipped")]


def _resolution_rho(rows):
    pairs = [(float(r["resolution"]), abs(float(r["cc_mask_delta"])))
             for r in rows if r["cc_mask_delta"] and r["resolution"]]
    return stats.spearmanr([a for a, _ in pairs], [b for _, b in pairs])[0], len(pairs)


# (label, literal that must be in the registry, derivation -> value to compare)
CHECKS: list[tuple[str, str, Callable[[list[dict]], Any]]] = [
    ("EM entry count",
     "**69** entries that entered the refinement benchmark",
     lambda rows: f"**{len(_named(rows))}** entries that entered the refinement benchmark"),
    # The nested denominators. #115 corrected the prose here; the check added with it
    # compared these counts only to each other, so all four could drift together --
    # or any one of them alone, as long as the ordering survived -- without a single
    # check firing (#116). Each is now pinned to the data like every other figure.
    ("refinement-attempt count",
     "of which **59** reached a refinement attempt",
     lambda rows: f"of which **{len(_attempted(rows))}** reached a refinement attempt"),
    ("recorded-Δ count",
     "**58** carry a recorded Δ",
     lambda rows: f"**{len(_with_delta(rows))}** carry a recorded Δ"),
    ("full pre/post count",
     "**35** have full pre/post values",
     lambda rows: f"**{len(_measured(rows))}** have full pre/post values"),
    ("refinement attempts incl. LOST",
     "(**63** entries reached a refinement attempt in total",
     lambda rows: f"(**{len(_attempted_incl_lost(rows))}** entries reached a "
                  f"refinement attempt in total"),
    ("CC_mask degradation count",
     "**17 degraded — a lower bound, not a count**",
     lambda rows: f"**{sum(1 for x in _cc_deltas(rows) if x < 0)} degraded "
                  f"— a lower bound, not a count**"),
    ("d_FSC degradation count",
     "of the **8 degradation magnitudes on record**",
     lambda rows: f"of the **{len(_dfsc_degradations(rows))} degradation magnitudes on record**"),
    ("d_FSC degradation median",
     "the median is 0.157 %",
     lambda rows: f"the median is {statistics.median(_dfsc_degradations(rows)):.3f} %"),
    ("worst d_FSC degradation",
     "the largest *degradation* is **+4.786 %**",
     lambda rows: f"the largest *degradation* is **+{max(_dfsc_degradations(rows)):.3f} %**"),
    ("resolution correlation",
     "**+0.361** over the **58** entries with a recorded Δ",
     lambda rows: (lambda rho, n: f"**{rho:+.3f}** over the **{n}** entries with a recorded Δ")
                  (*_resolution_rho(rows))),
    ("crossing-ratio median",
     "median ratio **0.9843**",
     lambda rows: f"median ratio **{statistics.median(_ratios(rows)):.4f}**"),
    ("crossing-ratio band count",
     "**50 of 60 (83 %) between 0.73 and 1.01**",
     lambda rows: (lambda r: f"**{sum(1 for x in r if 0.73 <= x <= 1.01)} of {len(r)} "
                             f"({100*sum(1 for x in r if 0.73 <= x <= 1.01)/len(r):.0f} %) "
                             f"between 0.73 and 1.01**")(_ratios(rows))),
]


# The registry's nesting sentence, read as the registry states it rather than as the
# data implies it. Anchored on the phrases, so a reworded claim goes MISSING (the same
# contract as CHECKS) instead of quietly ceasing to be checked.
_NESTING_SENTENCE = re.compile(
    r"\*\*(?P<named>\d+)\*\* entries that entered the refinement benchmark.*?"
    r"of which \*\*(?P<attempted>\d+)\*\* reached a refinement attempt, "
    r"\*\*(?P<with_delta>\d+)\*\* carry a recorded Δ and "
    r"\*\*(?P<measured>\d+)\*\* have full pre/post values",
    re.DOTALL)


# Per-entry figures the registry asserts for a named entry. These are quoted throughout
# §4's map-model row and NONE were gated: all 12 CHECKS above are aggregate, and both
# registry errors round 28 found (#167) were per-entry -- 10RI's delta stated as
# +0.45 % against a recorded 0.4441, and a range endpoint taken from an entry that has
# no recorded value at all (#180).
#
# (id, column, literal that must appear, how to render the TSV value)
PER_ENTRY: list[tuple[str, str, str, Any]] = [
    ("10RI", "cc_mask_delta", "10RI: CC_mask +0.0115", lambda v: f"10RI: CC_mask +{float(v):.4f}"),
    ("10RI", "d_fsc_model_delta_pct", "`d_FSC_model` degraded +0.444 %",
     lambda v: f"`d_FSC_model` degraded +{float(v):.3f} %"),
    ("10BU", "d_fsc_model_delta_pct", "the largest *degradation* is **+4.786 %**",
     lambda v: f"the largest *degradation* is **+{float(v):.3f} %**"),
    ("10ME", "d_fsc_model_delta_pct", "worst **+1.476 %** (10ME)",
     lambda v: f"worst **+{float(v):.3f} %** (10ME)"),
    ("9H7U", "d_fsc_model_delta_pct", "a **36 % improvement** (9H7U",
     lambda v: f"a **{abs(float(v)):.0f} % improvement** (9H7U"),
]


def per_entry_checks(registry: str, rows: list[dict]) -> list[dict[str, Any]]:
    """Each per-entry figure the registry quotes, against that entry's TSV row.

    Reports DERIVABLE and UNDERIVABLE separately and counts both. A figure naming an
    entry whose value was never recorded -- a `LOST` row, a `delta-only` row, round 13's
    unpublished values -- cannot be checked at all, and skipping those silently while
    printing OK would overstate the coverage. That is #116's shape, and this check
    states its denominator instead.
    """
    by_id = {r["pdb_id"]: r for r in rows}
    results = []
    for pdb_id, column, literal, render in PER_ENTRY:
        row = by_id.get(pdb_id)
        value = (row or {}).get(column, "")
        if not value:
            results.append({
                "check": f"{pdb_id}.{column}", "status": "UNDERIVABLE", "per_entry": True,
                "detail": (f"the registry asserts {literal!r} but {pdb_id} has no recorded "
                           f"{column} — "
                           + ("no such entry in the file" if row is None
                              else f"status {row['status']!r}") +
                           " — so the figure cannot be checked against anything")})
            continue
        derived = render(value)
        if literal not in registry:
            status, detail = "MISSING", (
                f"the registry no longer contains {literal!r} — reworded or removed, so "
                f"there is nothing to compare; the record gives {derived!r}")
        elif derived != literal:
            status, detail = "STALE", f"registry says {literal!r}; the record gives {derived!r}"
        else:
            status, detail = "OK", derived
        results.append({"check": f"{pdb_id}.{column}", "status": status,
                        "detail": detail, "per_entry": True})
    return results


def nesting_check(registry: str, rows: list[dict]) -> dict[str, Any]:
    """The nested denominators must nest **as the registry states them**.

    #115: the registry read "69 ... of which 63 reached a refinement attempt", and 63
    was not a subset of 69 -- it counted the 4 LOST rows that 69 excludes. Every figure
    was individually right against the data, so the per-figure checks all passed and
    nothing compared them to each other.

    The check written with that fix compared four counts it derived **itself** from the
    TSV, and never read the registry at all. Those inclusions hold by construction --
    `append_results` writes an empty `cc_mask_delta` for every `skipped:` row and a
    value for every `measured` one -- so no run of the pipeline can produce a file that
    fails them. It could fire only on a hand-edit, i.e. essentially never on the class
    it was written for (#116).

    So the relationship is now checked where the defect lives: in the sentence. The
    numbers are parsed out of the registry's own prose and required to nest. The
    data-side derivations are pinned separately, one literal per figure, in CHECKS.
    """
    m = _NESTING_SENTENCE.search(registry)
    if not m:
        return {
            "check": "stated counts nest", "status": "MISSING",
            "detail": ("the registry's nested-denominator sentence no longer matches "
                       "the expected phrasing — reworded or removed, so the "
                       "relationship between 69/59/58/35 cannot be checked"),
        }
    named, attempted, with_delta, measured = (
        int(m.group(k)) for k in ("named", "attempted", "with_delta", "measured"))
    ok = named >= attempted >= with_delta >= measured
    return {
        "check": "stated counts nest", "status": "OK" if ok else "BROKEN",
        "detail": (f"registry states named {named} >= attempted {attempted} >= "
                   f"with-delta {with_delta} >= measured {measured}"
                   + ("" if ok else "  <- not monotonically nested")),
    }


def _status_vocabulary():
    """The declared `status` vocabulary, imported from the script that WRITES it.

    Not re-declared here. Every predicate in this file keys on a status, and before
    round 26 those keys were the only definition of the vocabulary that existed --
    spread across four functions, in the reader, while the writer that produces the
    values lived in another file. That is the shape of #136.
    """
    return _VOCAB, _IS_KNOWN


def vocabulary_check(rows: list[dict]) -> dict[str, Any]:
    """Every `status` in the file must match the declared vocabulary.

    `attempted` is defined by subtraction (`not startswith("skipped")`), so a status
    nobody declared does not raise -- it joins the attempted count silently and moves a
    published denominator. This check is what stops that being invisible.
    """
    prefixes, is_known = _status_vocabulary()
    unknown = sorted({r["status"] for r in rows if not is_known(r["status"])})
    return {
        "check": "status vocabulary",
        "status": "OK" if not unknown else "UNDECLARED",
        "detail": (f"all {len(rows)} rows carry one of {len(prefixes)} declared statuses"
                   if not unknown else
                   f"{len(unknown)} status value(s) match no declared prefix — they are "
                   f"being counted as `attempted` by default: {unknown}"),
    }


def run(registry: str, rows: list[dict]) -> list[dict[str, Any]]:
    results = []
    for label, literal, derive in CHECKS:
        derived = derive(rows)
        if literal not in registry:
            # Say "expected literal", not "no longer contains X ... the data gives X",
            # which is what this read when the registry sentence was edited while the
            # underlying figure was unchanged -- a self-contradicting message on the
            # commonest failure mode.
            status, detail = "MISSING", (
                f"the registry does not contain the expected literal {literal!r} — the "
                f"figure was edited or the claim reworded, so there is nothing to "
                f"compare; the data currently gives {derived!r}. Find the sentence in "
                f"the registry and re-check it by hand.")
        elif derived != literal:
            status, detail = "STALE", f"registry says {literal!r}; data gives {derived!r}"
        else:
            status, detail = "OK", derived
        results.append({"check": label, "status": status, "detail": detail})
    results.append(nesting_check(registry, rows))
    results.append(vocabulary_check(rows))
    results += per_entry_checks(registry, rows)
    return results


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--registry", default=REGISTRY)
    ap.add_argument("--tsv", default=TSV)
    ap.add_argument("--json", dest="json_out")
    args = ap.parse_args()

    results = run(Path(args.registry).read_text(), load(Path(args.tsv)))
    bad = [r for r in results if r["status"] != "OK"]
    for r in results:
        print(f"  {r['status']:<8} {r['check']:<28} {r['detail']}",
              file=sys.stderr if r["status"] != "OK" else sys.stdout)
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(results, indent=2) + "\n")
    if bad:
        print(f"\n{len(bad)} registry figure(s) no longer match the data.", file=sys.stderr)
        return 1
    # State the coverage, not just the verdict. The per-entry figures gated here are a
    # SUBSET: round 29 found at least 15 derivable and gates 5. It also found that the
    # derivable/underivable split has no reliable value (9:20 by regex, ~15:11 by hand,
    # #182), so this line claims coverage is partial without claiming how partial. A
    # gate printing "all figures match" while covering a third overstates what it
    # verified, which is #116's shape.
    # Tagged, not sniffed: "refinement attempts incl. LOST" contains a dot and was
    # counted as per-entry by a `"." in check` test -- a wrong coverage figure inside
    # the statement written to stop overstating coverage.
    n_entry = sum(1 for r in results if r.get("per_entry"))
    print(f"\nall {len(results)} checked registry figures match the data "
          f"({n_entry} per-entry; the registry quotes more per-entry figures than are "
          f"gated here, some of them not derivable at all — see round 29)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
