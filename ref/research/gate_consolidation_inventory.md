# Gate consolidation — inventory and proposal (#293, steps 1–3)

#293 asks for a design pass *before* any working gate is touched: inventory the
`scripts/check_*.py` guards, identify the facts asserted as prose in more than one
place, and propose the smallest consolidation that removes the most literal-parsing
surface without rewriting the registry's human-readable form. This file is that pass.
It changes no gate, no tolerance, and no registry prose. **As of `main` 4b2af28
(2026-08-26): 11 guards, 2 897 lines, 40 regex sites.** Every count in this file is a
restatement of exactly the kind it inventories; re-run the footnote commands rather
than trusting the numbers once the set has moved.

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
| `check_negative_control_records.py` | **mixed** | records ↔ records (internal consistency: data); records ↔ round-doc prose (one hand-written check per record *family*: an f-string test for bench, a proximity regex over four counts for screen, a keyword-anchored `required` dict for sandboxed recover records, #419); registry §6 ↔ `bench_recover_leg` constants | 16 (3 in the prose checks, 5 in the §6 check incl. `TRIPLE_RE`, 8 filename matches — `RECORD_RE` plus seven in `main()`) | the record and §6 checks re-derive; the prose checks are per-family hand-written |

Reading of the table: the **structural** guards (five) carry no literal surface and
are not #293's concern. The **recompute-vs-prose** guards already have the shape #293
wants — a committed data file is the source and the prose is diffed against it — and
their remaining regexes are the unavoidable "find the labelled figure in the sentence"
step. The literal-parsing weight sits in the last four rows: **28 of the 40 regex sites**
are in `check_negative_control_records`, `check_summary_coverage` and
`check_next_tasks_dates` — though 8 of the 16 in the first are filename matches, not
prose parsing — and `check_driver_thresholds`'s entire content is a table of literals
that must be hand-extended every time the registry gains a governed value (PR #436
added an entry, and its first attempt broke `test_driver_thresholds` by changing the
table's order — a literal table with positional tests, `CHECKS[0]`).

## 2. Facts asserted in more than one place

Each row is one fact, where it is authoritative, where it is restated, and what checks
the restatement today. "—" means nothing does.

| Fact | Authoritative source | Restated in | Checked by |
|---|---|---|---|
| Tolerance-series round count — `NEXT_TASKS.md` ("N rounds of …", spelled out) | the set of `tolerance_benchmark_round*.md` | `NEXT_TASKS.md` | `check_summary_coverage.round_count_claim`: renders the expected phrase with `spell()` (fails closed outside 20–99 since PR #159, issue #160) and locates it with a `_TENS`-derived alternation (went MISSING at round 40 until derived, round-40 PR #265; #244 was the same MISSING-on-correct-prose class in `check_round_figures --refresh`, and the comment at `check_summary_coverage.py:261` still credits it — #468) |
| Tolerance-series round count — `lessons.md` title | same | `ref/research/lessons.md` line 1 | — (`lessons_coverage` checks the index table's round tokens, not the count; the title currently says "thirty" against forty-eight — #467) |
| Per-round defect counts / issue ranges | `round_findings.tsv` | `NEXT_TASKS.md`, `lessons.md`, round docs | `check_summary_coverage` (`_DEFECT_CLAIM`), `check_round_figures` (`_SEVERITY_CLAIM`) |
| §4 dataset figures (n, ρ, degradation counts, nesting sentence) | `em_refinement_deltas.tsv` | registry §4 prose | `check_registry_figures` (labelled figures + one nesting-sentence regex) |
| Governed thresholds and their retired values | registry §3/§4/§6 | drivers, `bench_*.py` docstrings | `check_driver_thresholds` `CHECKS` table (five entries, hand-maintained) |
| NC verdict thresholds (ISOT, ANIS), S_r2, MAD floor, shift band, stand-down set | committed NC records → `bench_recover_leg.py` constants | registry §6 | validate 3b (`check_registry_section`, PR #436) |
| NC per-round headline figures (15/22, 21/21, 22 sandboxes, …) | `negative_control_round<N>_*.json` | `negative_control_round<N>.md` | validate 3b, **one hand-written check per record family** (`check_bench_round_doc`, `check_round_doc`, `check_recover_round_doc`; ~92 lines, 3 regex sites) — the surface that grows with every new family or headline |
| NC milestone dates and PR numbers | `git log` squash-merge trail | `NEXT_TASKS.md` NC table | `check_next_tasks_dates` (regex row parser + ±1 day skew) |
| NC round-doc ↔ record linkage | filenames | round docs cite record filenames | validate 3b orphan-family check (PR #436) |
| Partial-record ledger (⚠ rows), marked/backed row status | **none — the registry's §4 row markers are prose** | `NEXT_TASKS.md`, `lessons.md` | — (the #293 body's motivating example; a sidecar would have to be *created*, not derived) |

Nine facts; eight have a committed machine-readable origin. Two of those eight are
already checked against it by a data comparison (NC thresholds and record linkage,
both landed in #436). The single-source **candidates** — facts whose origin is committed
but whose restatement is still checked by hand-written prose parsing — are the NC
headline figures and the NC dates; the `lessons.md` title is unchecked; the
partial-record ledger has no origin to derive from and is a separate design question.

## 3. Proposal — the smallest consolidation

Ranked by literal surface removed per line of new code. Each step is independently
mergeable and must keep its predecessor's negative tests passing before the swap
(#293 step 4; #228 is the standing reminder that a guard test that is not run is not a
guard).

**(a) NC headline sidecar — replaces the per-round pattern dicts.** Every NC driver
already writes its record; add a `headlines` block to the record's `summary` of `{label: rendered string}` —
`"osol_h success": "15/22"`, `"sandbox count": "22 distinct sandbox directories"` —
rendered *by the driver from the same variables it prints*. Each entry carries the
**anchor keyword with the value** (`{"keyword": "osol_h", "value": "15/22"}`), not the
bare figure: `check_round_doc`'s own docstring records that a bare-presence check
"passes whenever another identical digit exists anywhere in the doc", and
`check_round_doc` narrowed its window from 80 to 20 characters after its own test
caught a neighbouring digit satisfying the wrong keyword (comment at
`check_negative_control_records.py:565–568`); `check_recover_round_doc` still uses 80
with no stated rationale. So the window is **per entry**, carried in the headline block
(`"window": 20` default, overridable where a legitimately long phrase needs more —
the recover "H/D range" and "osol comparison" entries), and the generic check keeps
that proximity rule as its one rule: each `(keyword, value)` pair appears within its
window in the round doc.
The three per-family `check_*_round_doc` functions (~92 lines, 3 regex sites) collapse
into one, and the next round adds headlines by writing them, not by editing the guard.
The headlines live in the record as a **top-level `headlines` key** — not inside `summary`, whose
keys validate 3b iterates as subjects, and not as a sibling
`negative_control_round<N>_headlines.json`, which `check_orphan_family` would sweep up (`RECORD_RE`
matches every family) and demand a manifest and citation for. *(Amended at implementation, PR #511.)*
Regression tests: in `test_check_negative_control.py`, `"round doc missing a headline
figure fails"` (the neighbouring-digit case: "1 floor" 25 characters from "screened"),
`"#419: drifted recover prose headline fails"` and `"#419: prose drift names the
protected headline"` must still fail/pass exactly as now under the generic check before
the old functions are deleted. Committed rounds keep their existing checks until a
later round's record carries the block: this proposal's policy is that committed records
are not rewritten to fit a new guard (the same reason #319 admits only full-run records).

**(b) `CHECKS` table → `ref/thresholds_and_standards.yaml` sidecar.** Move
`check_driver_thresholds.CHECKS` into a small YAML file next to the registry:
`metric, section, current, registry_pattern, consumers[], retired[]`. The guard reads
the file; behaviour is unchanged, and — said plainly — the `registry_pattern` strings
are still per-figure regexes, moved from Python to YAML, not removed. What it buys is
narrower: the table becomes data the registry's author edits alongside the prose, the
positional test (`CHECKS[0]`) becomes a keyed lookup, and a later step can generate
the registry's `[provenance]` column from it. It does not conflict with
`CODING_STANDARDS.md` rule 10 (thresholds stay defined once, in the `.md`; the sidecar
is guard data, not a second definition).
Regression test: `test_driver_thresholds.py` on the YAML-loaded table, plus a check
that every `**bold**` figure in a governed section has an entry (the missing-entry
case #445 found by hand). *(Amended at implementation: the sidecar landed as
`ref/thresholds_and_standards.yaml` with a validating loader, keyed lookups, and a
section-heading check; the bold-figure coverage check was NOT implemented — §3/§4/§6
carry dozens of bold figures that are counts and statistics, not governed thresholds,
so it would fail on every one of them. Coverage of new governed values stays a review
obligation, as in #445.)*

**(c) Extend the rendered round count to `lessons.md`.** `round_count_claim` already
renders the expected phrase with `spell()` and fails closed outside 20–99; the only
remaining grammar is the `_TENS`-derived alternation that locates the phrase to tell
STALE from MISSING, and it is already derived from the same table. There is nothing
left to consolidate there. What *is* missing is coverage: the same rendered comparison
does not run on `lessons.md`, whose title is stale today (#467). The step is to run the
existing check on both files, with the title fixed first. *(Implemented: `round_count_claim(text,
rounds, where)` runs on both files, each reported under its own label.)*

**Not proposed.** `check_registry_figures` and `check_round_figures` are already
recompute-vs-prose; their regexes locate labelled figures and are the irreducible part.
`check_next_tasks_dates` parses a table whose columns are the sidecar — a YAML twin of
the NC table would just move the same rows; leave it. The five structural guards are
out of scope.

**Order.** (a) first — not for regex count (it removes 3 of 40) but because it is the
surface that grows: every new record family or headline has so far meant a new
hand-written check, and the drivers already own the values. (b) second — mechanical,
removes the positional coupling. (c) last — a coverage extension of an existing check.
Each as its own PR with its own adversarial review; no tolerance value or registry
prose changes in any of them.

---

Footnotes: guard count `ls scripts/check_*.py | wc -l`; regex sites
`grep -c 're\.\(search\|compile\|findall\|match\|finditer\)' scripts/check_*.py`;
lines `wc -l scripts/check_*.py`; `CHECKS` entries
`uv run --locked -q -- python -c 'import importlib.util as u,sys; s=u.spec_from_file_location("m","scripts/check_driver_thresholds.py"); m=u.module_from_spec(s); s.loader.exec_module(m); print(len(m.CHECKS))'`;
the three prose checks `grep -n '^def check_.*round_doc' scripts/check_negative_control_records.py`.
