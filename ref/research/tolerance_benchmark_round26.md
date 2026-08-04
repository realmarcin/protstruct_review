# Tolerance benchmark — round 26: one rule, one copy — and counting from the command

Round 25 closed with three statements that were claims rather than conclusions. This round tests
them. Predictions were registered in `tolerance_benchmark_round26_preregistration.md`, in a commit
containing no results.

**No tolerance, band or measurement changed.** Every registry figure was re-derived and is unchanged.

## P2 — the status vocabulary: *falsified in letter, confirmed in consequence*

`ref/research/data/em_refinement_deltas.tsv`'s `status` column is written by `append_results` and
read by four predicates in `check_registry_figures.py`. No declaration of the vocabulary existed
anywhere. I predicted **0 rows** would fall outside it.

**28 of 97 do** — 23 `delta-only`, 1 `d_FSC only`, 4 `LOST`. The three prefixes the predicates
actually test (`skipped`, `screened only`, `measured`) cover 69 rows.

And yet **every published denominator is correct**: 69 / 59 / 58 / 35 / 63, all matching the registry.
The reason is the mechanism that makes this dangerous — `attempted` is defined by **subtraction**:

```python
def _attempted(rows):
    return [r for r in _named(rows) if not r["status"].startswith("skipped")]
```

An unrecognised status does not raise. It joins `attempted` by default, and for these 24 rows that is
genuinely right — they *were* attempted. The count is correct **by luck of the default**.

**My falsification criterion was wrong**, and that is the more useful finding. I wrote:

> *If violated*, some row's status is already unrecognised by one of the predicates, and at least one
> published denominator is wrong today.

Those two are not the same claim, and I registered them as if they were. A default bucket makes
"unrecognised" and "miscounted" independent: the first can be true for years while the second stays
false, right up until a status arrives that does not belong in the default.

### The guard

`STATUS_PREFIXES` is now declared once, in `bench_refinement_deltas_em.py`, next to the writer that
produces the values. `check_registry_figures.py` **imports** it rather than carrying a copy — the
whole point of the round. A status matching no declared prefix is now `UNDECLARED` rather than
silently counted.

Demonstrated on the case it exists for — a typo in an existing status:

| mutation | `attempted` | vocabulary check |
|---|---|---|
| none | 59 | `OK` |
| a new undeclared status | 60 | `UNDECLARED` |
| `skipped:` → `skip:` | **69** | `UNDECLARED` |

**Scope, stated rather than implied:** on that last row the registry's literal checks *also* go
`STALE`. They are not redundant with each other, and the difference matters — the registry check
reports *"registry says 59, data gives 69"*, which points at the registry and invites correcting a
figure that is right. That is #113's failure mode exactly. The vocabulary check names the cause.
It also covers counts the registry does not pin, where nothing else fires at all.

## P3 — round 25's document survives its own gate: **confirmed**

`scripts/check_round_figures.py` checks a round document's claims about its own findings against a
committed record of those findings. Applied to `tolerance_benchmark_round25.md` as merged: **5 checks,
0 discrepancies.** The #130 and #135 corrections were complete.

The gate was then proved to fail four ways, including the exact #130 miscount:

| mutation | result |
|---|---|
| `Four high (...)` → `Three high (...)` | `MISSING` |
| `#136 (high)` → `#136 (medium)` | `STALE` |
| cite an issue that does not exist | `MISSING` |
| reword a covered claim | `MISSING` |

### Why the findings are committed data and not a live `gh` call

`validate.sh` is offline and stays offline. A check that silently skips when `gh` is unavailable or
unauthenticated is a guard that does not guard — the class round 25 spent itself on. So
`ref/research/data/round_findings.tsv` is committed and refreshed deliberately
(`--refresh`), exactly as `em_refinement_deltas.tsv` is.

### Building it reproduced two defects this repo has already shipped

The refresh was canaried on one issue first, per the standing rule, and the canary earned its keep
three times over:

1. **The canary "failed" while succeeding.** Exit code 1 — but the TSV was on disk, non-empty and
   correct. The crash was in the *success message* (`relative_to` on a path outside the repo). This is
   verbatim why the rule says **verify the side effects, not the exit code**.
2. **`gh issue view <n>` resolves a PULL REQUEST.** Walking a numeric range pulled #128 and #129 —
   this cycle's own PRs — into the findings record with severity `unstated`. Fixed by intersecting
   with `gh issue list`, which returns issues only.
3. **The severity regex took the first match anywhere in the body.** #130's body *opens by quoting the
   label it is reporting on* — "Four of the twelve are labelled `**Severity: high**`" — so the record
   read `high` for an issue that declares `medium` twelve lines below. **That is #121**: keying on the
   first match when the meaningful one is elsewhere, reproduced by me inside the round whose subject
   is fragile rules. Fixed by anchoring to the start of a line; a declaration is always its own line,
   a mention never is.

**`fixed_pr` was designed, built, and then removed.** It cannot be derived reliably:
`closedByPullRequestsReferences` is empty for an issue auto-closed by a `Fix #NNN` commit keyword, and
the workflow's "Fixed in #NNN" close comment is absent for exactly those same issues. A column that is
right for some rows and silently empty for others is worse than no column in a record meant to be
authoritative. `state` replaced it.

## P1 — "twelve is a lower bound": **confirmed**

Pass 4 read `scripts/` with a lens fixed in advance and different from passes 1–3 — *one rule, two
copies*, rather than silent failure and guard gaps. It found **two** major defects, so twelve was
indeed a lower bound, and the fourth pass over the same code was not wasted.

**#139 (high) — the T17 ordered-core cutoff.** `t17_nmr_ensemble.py` defines the ordered core at
`_ORDERED_CORE_RMSF_CUTOFF = 2.0`. `bench_t17_ordered_core.py` said, in its docstring:

> This re-uses its own functions, so the sweep measures the harness's metric rather than a
> re-implementation of it.

It did not. It imported the module for `run_precision()` only, reimplemented the ordered-core filter
inline, and indexed the result with the hardcoded string key `"2.0"`. **Three** independent
divergences had accumulated:

| | harness | benchmark |
|---|---|---|
| cutoff | `_ORDERED_CORE_RMSF_CUTOFF` | hardcoded `"2.0"` |
| mean | `sum/len`, 3 dp | `fmean`, 4 dp |
| empty core | `_fail(...)` | silent `None` |

Move the harness's cutoff and `"2.0"` stays a valid key, so nothing raises and
`whole_chain_minus_2A_core` keeps reporting the old bucket **under a name asserting otherwise**. On a
synthetic ensemble, 2.0 → 2.5 moves the true gap 0.957 → 0.665 while the old code reported 0.957 at
both — a 44 % error.

Fixed by reading the cutoff from the harness, calling `ordered_core_precision()` so the column is the
harness's metric, naming the key for the cutoff it used, and correcting the docstring.

**The fix's own verification found a further instance of the same class.** Calling
`ordered_core_precision(rmsf)` bare would have used the default bound at **def time**, silently
ignoring the cutoff just read — two copies again, by a subtler route. It is passed explicitly, and
the test asserts that.

**#140 (medium) — nine copies of two tool paths.** `PHENIX_BIN` in five files, `CCP4_SETUP` in four.
The honest reading is that the likely consequence is a loud crash: if an upgrade removes the old
install, the stale scripts fail. The quiet case needs the old install left on disk — which installers
do — and then benchmark numbers get computed against mismatched tool versions with nothing to say so.
That matters because §4 claims **same-binary** reproducibility against `phenix-2.0-5936` pinned since
round 5, and that pin is only as good as its nine copies agreeing.

**Gated rather than refactored.** These are standalone scripts run from the repo root, so `scripts/`
is not on `sys.path` and sharing a constant would need `importlib` in nine files — more machinery
than the risk warrants. `validate.sh` now fails if the literals disagree, naming both values and
which files carry each.

## P4 — the class is small: **confirmed**

Predicted at least one instance beyond filenames and fewer than five. **Three** asserted — the status
vocabulary (P2), the T17 cutoff (#139), the tool paths (#140) — plus the def-time default found while
fixing #139, and one **declined**: `HIGH_RATIO = 1.3` appears in both `screen_dfsc_ratio.py` and
`analyze_dfsc_outlier.py`, but both are round-scoped research constants rather than a maintained
contract, and the registry already records that round 23 superseded 1.3 with a data-derived 1.074
fence *without* updating either. Reported here rather than filed, so the judgement is visible.

Duplication in this repo is therefore enumerable, not systemic — which is what makes gating each
instance a proportionate response rather than a refactor.

## Scope limits

- **The round-figure gate covers one document.** It is written against round 25's phrasings; rounds
  1–24 have their own and are not checked. A gate covering one document is worth less than it looks,
  and the honest statement is that it will cover round *N* only if round *N* is written to it.
- **It cannot check a claim nobody wrote down as a number.** "Four high" is checkable; "the audit was
  thorough" is not.
- **The vocabulary guard protects one column of one file.** Pass 4 checked the others it could find —
  `oracle_family` is schema-enforced, and `fetch_em_entries.py`'s attrition `outcome` column has no
  programmatic reader at all, so there is no second copy to drift from. That is a survey, not a proof.
- **P1 confirms depth is not exhausted; it cannot say where the bottom is.** A fifth pass with a fifth
  lens would be the same argument again. The honest statement stays "lower bound" at every depth.
- **#140 is gated, not eliminated.** Nine copies still exist; the gate only stops them disagreeing
  silently. It also cannot catch the case where all nine are updated together to a path that is
  wrong.
- **The gate is red between pre-registration and the round document.** `validate.sh` requires every
  `tolerance_benchmark_round*.md` to have a lessons entry, and a pre-registration file matches that
  glob. This is inherent to registering predictions in a commit with no results, and is stated here
  rather than worked around.
