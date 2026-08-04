# Tolerance benchmark — round 25: auditing the code that produces the numbers

Twenty-four rounds have reviewed prose and data adversarially. The **scripts** producing both had
not been reviewed that way even once. A per-file count of how often each is mentioned in a round's
audit trail makes the asymmetry plain: `analyze_dfsc_outlier.py` and `analyze_em_deltas.py` appear in
one trail each, `bench_t05_bond_rmsd.py` in one, several bench scripts in two — against registry rows
re-read every round for two years of rounds.

So this round graded the code instead of a tolerance. Four independent reviewers over
`scripts/` (37 files, 10 218 lines), every finding re-verified by hand against the real fixtures
before it was filed, then fixed and pinned with a test.

**No tolerance, band, or measurement changed.** Every published figure in
`ref/thresholds_and_standards.md` was re-derived and is unchanged.

## What was found

Twelve defects, filed as #116–#127. Four high (#116, #117, #118, #127).

| | defect | why it mattered |
|---|---|---|
| **#116** | `nesting_check()` never read the registry | the guard built for #115 could not fail |
| **#117** | truncated DSSP accepted as a complete run | `and` where `or` was meant |
| **#118** | the `structure_ref` check the docstring promised was never written | dangling refs passed the ref-integrity gate |
| **#127** | PISA/RCSB failures dropped entries with no record | the one benchmark on a live endpoint |
| **#120** | a re-measurement of an id already on file was discarded silently | 10 `skipped:` rows can never be corrected |
| **#122** | missing violation attributes fabricated as `0.0` | the real value is 17.4 |
| **#121** | twin-operator flag keyed on an unconditional section header | right answer, wrong reason |
| **#119** | EM cache keys omitted `resolution` | stale logs paired with a new resolution |
| **#123** | the record loop covered one hardcoded provider | `nullglob` made zero files a pass |
| **#124** | `MACRO_CYCLES` absent from the refinement prefix | the sibling argument not carried across |
| **#125** | missing `oracle_family` claimed cctbx coverage | with `cctbx_oracles` empty |
| **#126** | the unit regex had no `Å²` | BSA and Wilson B silently became text |

## The headline: a guard whose assertion could not fail

Round 24 closed #115 — the registry stating *"**69** … of which **63** reached a refinement
attempt"*, where 63 counted the 4 `LOST` rows the 69 excludes — and added `nesting_check()` to stop it
recurring. That check took `rows` and never took `registry`:

```python
def nesting_check(rows):
    named = _named(rows); attempted = [...]; with_delta = [...]; measured = [...]
    ok = len(named) >= len(attempted) >= len(with_delta) >= len(measured)
```

Both sides of the comparison come from the same file, and the inclusions hold **by construction**:
`append_results` writes an empty `cc_mask_delta` for every `skipped:` row and a value for every
`measured` one, so no run of the pipeline can produce a file that fails them. The check could fire
only on a hand-edit.

Meanwhile the figures it recomputed — the registry's `**59**`, `**35**` and `**63**` — were pinned to
no literal at all, unlike all eight other checks in the file. Edit a `status` so `attempted` becomes
61 and `69 ≥ 61 ≥ 58 ≥ 35` still nests: every check passes, `validate.sh` exits 0, and the registry's
`59` is silently wrong.

Fixed by pinning all five denominators to derivations, and by moving the relationship check to where
the defect actually lives — the sentence. The numbers are now parsed out of the registry's own prose
and required to nest, so a reworded sentence goes `MISSING` rather than quietly ceasing to be checked.

`scripts/test_guards.py` proves both halves, including the one that matters most:

| test | result |
|---|---|
| drift 59 → 61, ordering still nests | **caught** by the per-figure check |
| … and the ordering check alone | **`OK`** — it would not have caught it |
| state 70 where 59 belongs | **`BROKEN`** |
| reword the sentence | **`MISSING`** |

That second row is the point of the round in one line.

## What the direction of the silent defaults does and does not show

Six of the twelve are silent-failure paths. It is tempting to report that they all fail in the
direction that flatters — this repo has a standing warning about conclusions that land conveniently,
and applying it here:

- **flattering (3):** `#122` fabricates *zero* violations, the best possible answer; `#125` claims
  cross-tool coverage that does not exist; `#127` drops entries from a set whose band is anchored to
  the observed **max**, so a lost extreme makes the band look better supported than it is.
- **alarming (1):** `#121` reports twinning operators *found* on a log that says none were.
- **neutral (2):** `#117` shortens a denominator in no particular direction; `#120` preserves whatever
  is already on file.

So "silent defaults flatter" is **not** a rule this round earned. Three of six is a tendency worth
watching, not a finding. What all six *do* share is more mundane and more useful: every one produces a
**well-formed, plausible value** rather than an error, which is why none was noticed.

## Self-review: the audit's own fixes needed auditing

Reviewing this round's diff found three more defects, two of them in the fixes themselves. Recorded
because the pattern across them is the more useful output.

**#136 (high) — the #119 fix reintroduced the failure it sits next to.** Putting the resolution into
the cache key made `measure()` write `mc_<id>_pre_<res>A.log`. `collect()` went on rebuilding
`mc_<id>_pre.log` by hand:

```python
pre = measure(model, map_file, resolution, cache, f"{pdb_id}_pre")
if pre["cc_mask"] is None:
    reason = failure_reason(cache / f"mc_{pdb_id}_pre.log", "map_correlations")
```

`failure_reason()` took its missing-file branch and returned `"map_correlations produced no log"` —
discarding the unparameterised-ligand and scattering-table causes it exists to surface. That string is
written into `em_refinement_deltas.tsv` as the row's `status`, so the attrition record would have
filled with entries saying nothing about themselves.

It is the **10EN failure that `failure_reason`'s own docstring memorialises**, reintroduced by a fix
three functions above it. The cause is worth naming: **two copies of a naming rule**, one in the
writer and one in the reader. Fixed by returning the log path from `measure()`, so there is only one.
Re-synchronising the copies would have left the mechanism intact.

No existing test caught it — the `cache_key` tests exercise the function in isolation, and the
mid-batch crash test monkeypatches `measure` wholesale, so the real function never ran.

**#130 (medium) — this document said "three high" when four are.** The table above it already led
with all four. A headline disagreeing with the body beneath it is the #91 shape.

**#135 (low) — a "20-file" that is 19**, written into the process document that exists to stop
unverified counts.

The last two are the same mistake twice in consecutive passes: **recounting from memory instead of
from the command.** Both were also wrong in the direction that flatters — fewer high-severity findings
reads as a cleaner audit. That is the bias this repo tells you to check hardest, and it appeared in a
round whose own write-up says so.

## Scope limits

- **Three fixes are not pinned by a test**, and deliberately:
  - **#117** (DSSP) would need `mkdssp` mocked. This suite's own docstring says a fake oracle only
    tests the mock, and the guard is a one-line condition; a test here would assert the mock's
    behaviour. Verified by reading, not by execution.
  - **#123** (`validate.sh` globs) is shell. Proven by hand — a tree with an empty `data/` now exits 1,
    and a record under a new provider is picked up — but that proof is in this document, not in CI.
  - The four-path `skipped` record in **#127** is tested only on the PISA-empty path, since the other
    three need a network failure to occur.
- **Two eligibility filters in `bench_t16_bsa_vs_pisa.collect()` remain unrecorded** — non-protein
  pairs and symmetry mates. They are deterministic given the input rather than failures, so they do
  not threaten the denominator the way a flaky endpoint does. Stated because "adds `skipped` tracking"
  would otherwise read as covering all six `continue`s.
- **#120 warns; it does not rewrite.** A superseded row is announced with both values and the operator
  edits the file by hand. Automatic rewriting of a cumulative, hand-auditable record is the worse
  failure mode, but it means the 10 `skipped:` rows still need a human to act.
- **The audit read the code; it did not re-run the pipelines.** Nothing here re-refined an entry or
  re-fetched a map. #119 and #124 are latent cache defects with no evidence either has ever fired —
  the caches live in temp directories, so no committed figure is implicated, but neither is any
  committed figure *proven* unaffected by re-running it.
- **Coverage is not completeness.** Four reviewers over 37 files found twelve defects on the first
  pass; a second pass over those fixes found three more, one of them high. That is a lower bound on
  what is there, and the rate at which reviewing the fixes finds new defects is itself evidence that
  one pass is not enough.
- **#136 is the second time this round a fix was checked only in isolation.** The `cache_key` unit
  tests passed while the caller was broken. A unit test on the helper does not test the contract
  between the helper and the code that used to do the work itself.
