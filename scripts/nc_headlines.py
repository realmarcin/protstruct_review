#!/usr/bin/env python3
"""Negative-control round headlines as data (#293 step a).

A round doc restates figures that live in its committed record. Until now the
guard (`check_negative_control_records.py`, validate 3b) carried one
hand-written prose check per record family — an f-string test for bench, a
proximity regex over four counts for screen, a ten-entry `required` dict for
sandboxed recover records — and every new family or headline meant editing
the guard. This module makes the headline the *record's* business:

* a driver renders its headlines from the same variables it prints and writes
  them under the record's top-level ``headlines`` key (never inside
  ``summary``, whose keys the guard treats as subjects);
* the guard checks every rendered headline against the round doc with ONE
  rule — the value must sit within a bounded window of its keyword — instead
  of one function per family;
* records that predate the block are rendered on the fly by the per-family
  renderers below, which reproduce the legacy checks exactly, so committed
  rounds are neither rewritten nor re-judged.

Three matching modes cover everything the legacy checks did:

``near``     value within ``window`` characters of ``keyword`` (``order`` =
             ``any`` | ``keyword_first`` | ``value_first``; ``between`` =
             ``nodigit`` | ``sentence`` | ``line`` restricts what may sit in
             the gap). The window is per entry because the guard's own test
             showed an 80-character window lets a neighbouring figure satisfy
             the wrong keyword; the default is 20.
``present``  bare substring — deliberately weak, kept only for the bench Q1
             figure and for id lists, where the legacy check was bare too.
``phrase``   a fixed sentence, whitespace-tolerant.
"""
from __future__ import annotations

import re
from collections import Counter

DEFAULT_WINDOW = 20
BETWEEN = {"nodigit": r"[^0-9\n]", "sentence": r"[^.\n]", "line": r"[^\n]"}
ORDERS = ("any", "keyword_first", "value_first")
MODES = ("near", "present", "phrase")


def headline(label: str, value, keyword: str | None = None, *,
             mode: str = "near", order: str = "any",
             window: int = DEFAULT_WINDOW, between: str = "nodigit") -> dict:
    return {"label": label, "value": str(value), "keyword": keyword,
            "mode": mode, "order": order, "window": int(window),
            "between": between}


def validate(entry) -> str | None:
    """Why an entry is malformed, or None. A malformed headline must be a
    NAMED failure — never a silent pass."""
    if not isinstance(entry, dict):
        return "not an object"
    for key in ("label", "value", "mode"):
        if not isinstance(entry.get(key), str) or not entry[key]:
            return f"missing or empty {key!r}"
    if entry["mode"] not in MODES:
        return f"unknown mode {entry['mode']!r}"
    if entry["mode"] == "near":
        if not isinstance(entry.get("keyword"), str) or not entry["keyword"]:
            return "near-mode headline without a keyword"
        if entry.get("order", "any") not in ORDERS:
            return f"unknown order {entry.get('order')!r}"
        if entry.get("between", "nodigit") not in BETWEEN:
            return f"unknown between {entry.get('between')!r}"
        window = entry.get("window", DEFAULT_WINDOW)
        if not isinstance(window, int) or window < 0 or window > 200:
            return f"window {window!r} out of range 0..200"
    return None


def pattern(entry: dict) -> str:
    """The regex one headline compiles to (exposed for the tests)."""
    value = re.escape(entry["value"])
    if entry["mode"] == "present":
        return value
    if entry["mode"] == "phrase":
        return r"\s+".join(re.escape(w) for w in entry["value"].split())
    gap = BETWEEN[entry.get("between", "nodigit")]
    window = entry.get("window", DEFAULT_WINDOW)
    keyword = re.escape(entry["keyword"])
    # A value must not be a substring of a larger number ("2/2" in "12/2").
    val = rf"\*{{0,2}}(?<![\d.])(?:{value})(?![\d])"
    kf = rf"{keyword}{gap}{{0,{window}}}{val}"
    vf = rf"{val}{gap}{{0,{window}}}{keyword}"
    order = entry.get("order", "any")
    return kf if order == "keyword_first" else vf if order == "value_first" \
        else f"(?:{kf})|(?:{vf})"


def missing(text: str, headlines: list) -> list[str]:
    """Human-readable reasons for every headline the text fails to state."""
    out = []
    for entry in headlines:
        why = validate(entry)
        if why:
            out.append(f"malformed headline {entry!r}: {why}")
            continue
        if not re.search(pattern(entry), text, re.IGNORECASE):
            near = (f" near {entry['keyword']!r}"
                    if entry["mode"] == "near" else "")
            out.append(f"{entry['label']} headline ({entry['value']!r}{near}) "
                       f"is absent")
    return out


# --- per-family renderers: the legacy checks, as data -----------------------

def bench_headlines(rows: list) -> list:
    """Q1: false verdicts on nulls, as degraded/attempted (bare presence, as
    the legacy check was)."""
    null_rows = [r for r in rows if r.get("subject") == "null"]
    if not null_rows:
        return []
    degraded = sum(1 for r in null_rows if r.get("verdict") == "DEGRADED")
    return [headline("Q1 null verdicts (degraded/attempted)",
                     f"{degraded}/{len(null_rows)}", mode="present")]


def screen_headlines(rows: list) -> list:
    counts = Counter(r.get("status") for r in rows)
    figures = {"attempt": len(rows), "floor": counts.get("floor", 0),
               "defect": counts.get("data_defect", 0),
               "screened": counts.get("screened", 0)}
    return [headline(f"{kw} count", value, kw, order="any", window=20,
                     between="sentence") for kw, value in figures.items()]


def recover_headlines(summary: dict) -> list:
    """The NC-10 evidence-bearing headlines (#419), one entry each."""
    subject = summary.get("osol_h") or {}
    anis = summary.get("anis_verification") or {}
    hydrogen = summary.get("hydrogen_verification") or {}
    comparison = summary.get("comparison_with_osol") or {}
    sandbox = summary.get("sandbox_verification") or {}
    perturb = summary.get("perturbation_reproduction") or {}
    kf = dict(order="keyword_first", window=80, between="nodigit")
    vf = dict(order="value_first", window=1, between="line")
    out = [
        headline("osol_h success",
                 f"{subject.get('successes')}/{subject.get('attempted')}",
                 "osol_h", **kf),
        headline("osol comparison",
                 f"{comparison.get('osol_successes')}/"
                 f"{comparison.get('osol_attempted')}", "osol", **kf),
        headline("ANIS measurability",
                 f"{anis.get('measurable')}/{anis.get('measurable')}", "ANIS",
                 **kf),
        headline("H/D range",
                 f"{hydrogen.get('minimum_ready')}–{hydrogen.get('maximum_ready')}",
                 "model", order="value_first", window=30, between="line"),
        headline("H/D retention",
                 f"{hydrogen.get('retained_equal')}/{hydrogen.get('models')}",
                 "retained", **kf),
        headline("ANIS log count", anis.get("logs_with_anis"), "all",
                 order="keyword_first", window=20, between="nodigit"),
        headline("ANIS log count", anis.get("logs_with_anis"), "log",
                 order="value_first", window=30, between="line"),
        headline("sandbox count", sandbox.get("distinct_sandboxes"),
                 "distinct sandbox", **vf),
        headline("PGID count", sandbox.get("distinct_pgids"),
                 "distinct refinement PGID", **vf),
        headline("unmasked reproduction", perturb.get("max_absdiff_unmasked"),
                 "Å unmasked", **vf),
        headline("all-residue reproduction", perturb.get("max_absdiff_all"),
                 "Å all-residue", **vf),
    ]
    for pdb_id in comparison.get("gained") or []:
        out.append(headline("gained-success list", pdb_id, mode="present"))
    if comparison.get("lost") == []:
        out.append(headline("zero-loss comparison", "No old success was lost",
                            mode="phrase"))
    return out
