# Gate consolidation — inventory and proposal (#293, steps 1–3)

#293 asks for a design pass *before* any working gate is touched: inventory the
`scripts/check_*.py` guards, identify the facts asserted as prose in more than one
place, and propose the smallest consolidation that removes the most literal-parsing
surface without rewriting the registry's human-readable form. This file is that pass.
It changes no gate, no tolerance, and no registry prose. Counts below are from
`main` at the merge of PR #436 (11 guards, 2 897 lines); re-run the commands in
the footnotes rather than trusting the numbers if the set has grown.

## 1. Inventory

Three kinds of guard, by what the assertion is keyed on. "Regex sites" counts
`re.(search|compile|findall|match|finditer)` calls — a proxy for how much of the guard
is a bespoke prose parser rather than a data comparison.

| Guard | Kind | Keyed on | Regex sites | Restates / re-derives |
|---|---|---|---|---|
| `check_referential_integrity.py` | **structural** | YAML refs → `ref/catalog.yaml` ids | 0 | re-derives |
| `check_qds_trust_invariant.py` | **structural** | QDS coverage rows + waiver blocks | 0 | re-derives |
| `check_selection_deltas.py` | **structural** | `round*_xray_deltas.json` ⊆ `round*_xray_selection.json` | 0 | re-derives |
| `check_fixture_provenance.py` | **structural** | fixture sidecars (sha256, date) | 2 (format only) | re-derives |
| `check_documentation_state.py` | **structural** | catalog task ids ↔ driver/wrapper files | 3 (id shapes) | re-derives |
| `check_registry_figures.py` | **recompute-vs-prose** | `em_refinement_deltas.tsv` → registry §4 figures | 1 (the nesting sentence) | recomputes, then diffs *labelled* figures in prose |
| `check_round_figures.py` | **recompute-vs-prose** | `round_findings.tsv` → round docs' claims about themselves | 5 | recomputes, then parses severity claims out of prose |
| `check_driver_thresholds.py` | **literal table** | a hand-written `CHECKS` table: current value regex + retired literals per metric | 1 (generic) | the table *is* the restatement |
| `check_summary_coverage.py` | **prose parser** | `NEXT_TASKS.md` and `lessons.md` round coverage, defect-count claims, spelled-out round counts (`_TENS`/`_UNITS`) | 7 | parses prose, compares with the round-doc set |
| `check_next_tasks_dates.py` | **prose parser** | NC-table rows: PR numbers + date spans vs `git log` | 5 | parses prose, compares with git |
| `check_negative_control_records.py` | **mixed** | records ↔ records (internal consistency: data); records ↔ round-doc prose (per-round `required` pattern dicts: #419 style); registry §6 ↔ `bench_recover_leg` constants | 16 | the record checks re-derive; the prose checks are per-round hand-written pattern lists |

Reading of the table: the **structural** guards (five) carry no literal surface and
are not #293's concern. The **recompute-vs-prose** guards already have the shape #293
wants — a committed data file is the source and the prose is diffed against it — and
their remaining regexes are the unavoidable "find the labelled figure in the sentence"
step. The literal-parsing weight sits in the last four rows: **29 of the 40 regex sites**
are in `check_negative_control_records`, `check_summary_coverage` and
`check_next_tasks_dates`, and `check_driver_thresholds`'s entire content is a table of
literals that must be hand-extended every time the registry gains a governed value
(PR #436 added the fifth entry, and its first attempt broke `test_driver_thresholds`
by changing the table's order — a literal table with positional tests).

## 2. Facts asserted in more than one place

Each row is one fact, where it is authoritative, where it is restated, and what checks
the restatement today. "—" means nothing does.

| Fact | Authoritative source | Restated in | Checked by |
|---|---|---|---|
| Tolerance-series round count | the set of `tolerance_benchmark_round*.md` | `NEXT_TASKS.md` ("N rounds of …", spelled out), `lessons.md` | `check_summary_coverage` via `_TENS`/`_UNITS` (the #160/#244 class: a spelled-number regex that stopped at "thirty") |
| Per-round defect counts / issue ranges | `round_findings.tsv` | `NEXT_TASKS.md`, `lessons.md`, round docs | `check_summary_coverage` (`_DEFECT_CLAIM`), `check_round_figures` (`_SEVERITY_CLAIM`) |
| §4 dataset figures (n, ρ, degradation counts, nesting sentence) | `em_refinement_deltas.tsv` | registry §4 prose | `check_registry_figures` (labelled figures + one nesting-sentence regex) |
| Governed thresholds and their retired values | registry §3/§4/§6 | drivers, `bench_*.py` docstrings | `check_driver_thresholds` `CHECKS` table (five entries, hand-maintained) |
| NC verdict thresholds (ISOT, ANIS), S_r2, MAD floor, shift band, stand-down set | committed NC records → `bench_recover_leg.py` constants | registry §6 | validate 3b (`check_registry_section`, PR #436) |
| NC per-round headline figures (15/22, 21/21, 22 sandboxes, …) | `negative_control_round<N>_*.json` | `negative_control_round<N>.md` | validate 3b, **one hand-written `required` pattern dict per round family** (`check_bench_round_doc`, `check_round_doc`, `check_recover_round_doc`) — the surface that grows fastest |
| NC milestone dates and PR numbers | `git log` squash-merge trail | `NEXT_TASKS.md` NC table | `check_next_tasks_dates` (regex row parser + ±1 day skew) |
| NC round-doc ↔ record linkage | filenames | round docs cite record filenames | validate 3b orphan-family check (PR #436) |
| Partial-record ledger (⚠ rows), marked/backed row status | registry §4 row markers | `NEXT_TASKS.md`, `lessons.md` | — (prose only; the #293 body's motivating example) |

The single-source candidates are the last five rows: each has an unambiguous
machine-readable origin already committed (a record, a TSV, or git), and the prose is
the *only* thing being parsed.

## 3. Proposal — the smallest consolidation

Ranked by literal surface removed per line of new code. Each step is independently
mergeable and must keep its predecessor's negative tests passing before the swap
(#293 step 4; #228 is the standing reminder that a guard test that is not run is not a
guard).

**(a) NC headline sidecar — replaces the per-round pattern dicts.** Every NC driver
already writes its record; add a `headlines` block to the record's `summary` (or a
sibling `negative_control_round<N>_headlines.json`) of `{label: rendered string}` —
`"osol_h success": "15/22"`, `"sandbox count": "22 distinct sandbox directories"` —
rendered *by the driver from the same variables it prints*. 3b then has one generic
check: every rendered headline string appears verbatim in the round doc. The three
per-family `check_*_round_doc` functions and their `required` dicts (about 120 lines,
10 of the 16 regex sites) collapse into ~15 lines, and the next round adds headlines
by writing them, not by editing the guard. Regression test: the #419 drift cases
(`test_check_negative_control.py`) must still fail by name under the generic check
before the old functions are deleted. Committed rounds keep their existing checks
until their records carry the block — do not re-render history.

**(b) `CHECKS` table → `ref/thresholds_and_standards.yaml` sidecar.** Move
`check_driver_thresholds.CHECKS` into a small YAML file next to the registry:
`metric, section, current, registry_pattern, consumers[], retired[]`. No behaviour
change; the guard reads the file. What it buys: the table becomes data the registry's
author edits alongside the prose, the positional test (`CHECKS[0]`) becomes a keyed
lookup, and a later step can generate the registry's `[provenance]` column from it.
Regression test: `test_driver_thresholds.py` on the YAML-loaded table, plus a check
that every `**bold**` figure in a governed section has an entry (the missing-entry
case #445 found by hand).

**(c) Spelled-out counts → render, don't parse.** `check_summary_coverage` already
knows the true round count; instead of parsing "forty-eight rounds" with `_TENS`, have
it *render* the expected phrase (`num2words`-style, twenty…ninety-nine plus an
explicit fail above the table's range) and search for that string. Removes the
open-ended number grammar; the guard fails closed when the count leaves the rendered
range instead of going MISSING as in #160.

**Not proposed.** `check_registry_figures` and `check_round_figures` are already
recompute-vs-prose; their regexes locate labelled figures and are the irreducible part.
`check_next_tasks_dates` parses a table whose columns are the sidecar — a YAML twin of
the NC table would just move the same rows; leave it. The five structural guards are
out of scope.

**Order.** (a) first — largest surface, most growth, and its regression tests already
exist. (b) second — mechanical. (c) last — smallest. Each as its own PR with its own
adversarial review; no tolerance value or registry prose changes in any of them.

---

Footnotes: guard count `ls scripts/check_*.py | wc -l`; regex sites
`grep -c 're\.\(search\|compile\|findall\|match\|finditer\)' scripts/check_*.py`;
lines `wc -l scripts/check_*.py`.
