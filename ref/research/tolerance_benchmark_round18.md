# Tolerance benchmark — round 18: committing the sets, and what re-running settles

Round 17 audited the registry and found the defect was not a list of careless rows but one missing
mechanism: **almost no bench script committed the entry set it ran on.** Where a tolerance was
recoverable, it was recoverable because an author had happened to paste a table into an audit trail.

This round fixes that, and then uses the fix — re-running two benchmarks whose sets are now pinned,
to find out whether "recoverable in principle" survives contact with the tools.

## 1. Every benchmark now ships its set

Ten scripts took their entries from an uncommitted `--ids-file` or globbed a cache. All ten now carry
the set, recovered from the per-entry tables in the audit trails:

| script | set | complete? |
|---|---:|---|
| `bench_t05_bond_rmsd` | 17 | ✅ |
| `bench_t05_restraint_library` | 17 | ✅ (verified identical to bond-length's) |
| `bench_t05_clashscore_h` | 10 | ✅ |
| `bench_t06_r_offset` | 15 | ✅ |
| `bench_t13_wilson_b` | 24 | ✅ |
| `bench_t17_ordered_core` | 5 (+1 failed) | ✅ |
| `bench_t14_flip_sets` | **12 of 17** | ❌ the 5 models with zero disagreements were never named |
| `bench_vs_deposited` | **11 of 17** | ❌ 9 complete for completeness/R-free; 6 unnamed for Ramachandran |
| `bench_refinement_deltas` | **16 of 37** | ❌ the ~11 entries setting both §4 band widths are named nowhere |
| `bench_t13_l_test` | **5 of 27** | ❌ no id argument exists; it reads a prior run's logs |

**A partial set is declared partial in the script**, via `SET_IS_COMPLETE = False` and a
`SET_SHORTFALL` string naming the denominator, and the script prints that warning when it falls back
to the default. A set silently short of its published denominator would be worse than none: a re-run
would look like a reproduction.

`bench_t13_l_test.py` is the extreme case and gets a different shape. It has **no id argument at
all** — it parses whatever `xt_*.log` / `ct_*.log` pairs a prior Wilson B run left in a cache, so its
set was never expressible, let alone recorded. It records `PUBLISHED_N = 27` and the 5 `KNOWN_IDS`,
and warns when a run's count differs from 27, so a future run is read as a new measurement rather
than a reproduction.

### The gate

`scripts/validate.sh` now fails if any `bench_*.py` does not declare a set. It checks that a set is
**declared**, not that it is complete — several are knowingly partial and say so. Declared-and-partial
is the honest state and passes; undeclared does not. Verified in both directions: removing a
`DEFAULT_SET` fails the gate, restoring it passes.

**The gate checks *use*, not just declaration — because the first version did not.** Self-review of
this PR found that `bench_refinement_deltas.py` declared its `DEFAULT_SET`, mentioned it only inside a
warning string, and went on globbing the cache. It passed the gate. That is the one script behind the
**most expensive partial record in the registry**, so the guarantee this whole round claims was false
exactly where it mattered most (#78). The gate now parses each script and requires a reference to the
set outside its assignment and outside a `print()`; two benchmarks whose sets genuinely cannot drive
a run — the L-test, which has no id argument, and the ordered-core script, which takes file paths —
opt out via an explicit `SET_NOT_RUNNABLE` carrying the reason, rather than being special-cased
inside the gate.

Both directions are tested: breaking a set's *use* fails the gate, and restoring it passes.

`bench_refinement_deltas_em.py` is the one script that legitimately has no list, because its set is
the cumulative `em_refinement_deltas.tsv` — a stronger form, since that file also records the skips
and the round. The gate accepts a `SET_RECORD` pointing at a committed file **and checks the file
exists**, so the declaration is a record rather than a promise.

Unit tests pin every set's size, its completeness flag, and two facts the audit established by hand:
that bond-length and restraint-library share one set, and that the flip-set benchmark's set includes
9LK0 while its siblings' do not — so a future round cannot "tidy" them into one list.

## 2. Re-running settles what reading could not

Round 17 marked two rows **partial but recoverable**. Both are now re-run.

### DockQ: not partial at all — the audit was wrong

Round 17 reasoned that `plausible_mappings(..., limit=8)` scores up to 8 mappings per complex while
the trail shows only 6, so some were computed and never printed. **Re-running shows `limit` is a cap
that was never reached.**

| complex | mappings scored | published |
|---|---:|---:|
| 4HHB | 4 | 4 |
| 1BRS | 2 | 2 |
| 1VFB, 3HFM, 2SIC | 0 (no equivalent chains) | reported as skipped |

Every value reproduces exactly — 4HHB `ABCD` 1.0000, `ADCB` 0.2145, `CBAD` 0.2116, `CDAB` 0.9819;
1BRS `ABCDEF` 1.0000, `CBADEF` 0.2175 — and `n_mappings_scored` equals the number published in every
case. **The DockQ row is a FULL RECORD**, and its round-17 mark is withdrawn.

Worth naming the failure mode, because it cuts the other way from everything else in this series: the
audit inferred a gap from reading the *code's upper bound* rather than its *output*. That is the same
error as inferring a distribution from its published extreme, made about a script instead of a
dataset. A `limit=` is not a count.

### Bond-angle RMSD: recovered, and three of its four figures reproduce

This one was a genuine gap. `bench_t05_restraint_library.py` computes per-entry angle figures into
its `--json`, and the trail tabulated only the **bond** columns — so the bond-angle tolerance's
median and max had no per-entry backing anywhere. Re-run on the now-committed 17-model set, all 17
processed with no skips:

| entry | CDL (A) | E&H (B) | gemmi (C) | A−B library | B−C implementation | A−C cross-library |
|---|---:|---:|---:|---:|---:|---:|
| 9PN7 | 0.440 | 0.911 | 1.201 | **0.471** | 0.290 | 0.761 |
| 9LLR | 0.713 | 1.153 | 1.551 | 0.440 | 0.398 | 0.838 |
| 30IZ | 0.573 | 1.010 | 1.319 | 0.437 | 0.309 | 0.746 |
| 28SX | 0.523 | 0.938 | 1.645 | 0.415 | **0.707** | **1.122** |
| 28SZ | 0.585 | 0.949 | 1.336 | 0.364 | 0.387 | 0.751 |
| 37BG | 0.924 | 1.263 | 1.561 | 0.339 | 0.298 | 0.637 |
| 12LO | 0.797 | 1.131 | 1.425 | 0.334 | 0.294 | 0.628 |
| 37AS | 1.266 | 1.533 | 1.520 | 0.267 | −0.013 | 0.254 |
| 37AP | 1.196 | 1.461 | 1.493 | 0.265 | 0.032 | 0.297 |
| 9HW2 | 1.410 | 1.633 | 1.973 | 0.223 | 0.340 | 0.563 |
| 28SV | 1.318 | 1.537 | 1.837 | 0.219 | 0.300 | 0.519 |
| 28SW | 1.456 | 1.656 | 1.958 | 0.200 | 0.302 | 0.502 |
| 9HX9 | 1.995 | 2.082 | 2.069 | 0.087 | −0.013 | 0.074 |
| 30TW | 1.055 | 1.135 | 1.565 | 0.080 | 0.430 | 0.510 |
| 24MR | 1.653 | 1.713 | 1.470 | 0.060 | −0.243 | **−0.183** |
| 11AF | 1.904 | 1.964 | 2.104 | 0.060 | 0.140 | 0.200 |
| 9PLB | 1.191 | 1.191 | 1.210 | **0.000** | 0.019 | 0.019 |

**Three published numbers reproduce exactly**: library-effect median **0.2648°** (published
0.265), max **0.4711°** (published 0.471), and the library's share of the cross-library gap
**51.1 %** (published 51 %). The row was right on those; it simply had nothing behind them that
anyone could check.

**The fourth was not reproduced, and this section originally claimed it was** (#81). The row also
quotes *56 % on matched-count models*, and that subset cannot be reconstructed from this run —
`collect()` emits no bond-count-match flag per entry, so the matched-count models cannot be
separated after the fact. It stands unverified until a re-run records the flag. Writing "every
published figure reproduces" over a cell containing four figures, having checked three, is the
same over-reach this round caught in the DockQ mark — in the opposite direction.

Two things the aggregate hid, now visible:

- **The library effect is one-signed in 16 of 17** — CDL always reports a *lower* angle RMSD than
  Engh & Huber on the same model, in the same implementation. A directional effect is a different
  claim from a symmetric ±0.265° spread, and it is the kind of thing a median cannot show.
- **9PLB has a library effect of exactly 0.000°** — CDL and E&H return the identical 1.19146. The
  range is therefore 0.000–0.471°, not a tight cluster around the median, and one model contributes
  nothing at all to the effect the tolerance is sized on.

Neither changes the band. Both are the sort of detail that was unavailable while the only record was
a median and a max, which is the whole argument for keeping per-entry values.

**The bond-angle row is now a FULL RECORD.**

### Why a committed set is enough here, and not for the EM benchmark

Round 16 argued per-entry *values* must be committed, because prose in a trail is not a record. Round
18 argues committed *sets* are the fix. Those are not in tension, and the difference is cost:

- **Cheap, deterministic benchmarks** — this one took minutes over 17 models, and reproduced every
  published figure to 4 significant figures. The committed set *is* the record: anything derivable
  from it is one command away, so caching the values adds a copy to keep in sync.
- **Expensive ones** — a single EM entry is a 30-minute-plus `real_space_refine`, and the full set is
  53 entries. Re-deriving a figure is a day's compute, so `em_refinement_deltas.tsv` caches the
  values and the set is the file.

The rule that covers both: **a benchmark's evidence must be re-derivable without asking anyone what
they ran.** A committed set achieves that when re-running is cheap; a committed table of values is
needed when it is not.

## 3. The §4 "19 vs 37" discrepancy is real, and worse than a stale number

Round 17 noticed the §4 geometry row says **19 entries** where the ΔRMSD row directly above says
**37**, and flagged it as possible staleness. Traced round by round, it is staleness — of a specific
and more awkward kind than a number left un-updated.

| round | X-ray set | < 2.5 Å | ≥ 2.5 Å | what was re-tested |
|---|---:|---:|---:|---|
| 5/6 | 8 | — | — | the original single bands (rotamer max 3.60 pp, clashscore ratio 4.26× both originate here) |
| 7 | **19** | 5 | 14 | all four clauses: RMSD 4/19, favored 6/19, rotamer 0/19, clashscore 0/19 |
| 8 | 26 | — | — | **Cα shift and favored only** |
| 10 | 32 | 14 | 18 | **Cα shift and favored only** |
| 11 | **37** | **19** | 18 | **RMSD only** (43SK breached 0.10 Å → widened to 0.12 Å) |

The ΔRMSD row is **correct**: 37 = 19 below 2.5 Å + 18 above, traceable through rounds 10 and 11.

The tempting reading — that the geometry row's `19` is really the `< 2.5 Å` branch, which is also 19 —
is **ruled out structurally**. The rotamer-outlier clause and the clashscore-ratio gate were never
resolution-split; they are single global bands, so there is no `< 2.5 Å` branch for a 19 to denote.
That 19 = 19 is a coincidence between round 7's *total* and round 11's *low-resolution subset*.

So the finding is not a typo:

> **`rotamer outliers_post ≤ outliers_pre + 4 pp` and the `5×` clashscore-ratio gate have not been
> re-tested since round 7, while the set they are quoted against grew from 19 to 37.** Eighteen
> entries — including every entry added at the high-resolution end — have never been checked against
> either clause.

Both quoted worst cases (3.60 pp, 4.26×) are older still: they come from the original 8-entry set.

**Why this round does not simply re-run them.** The X-ray §4 set is one of the four that is
irrecoverable — only **16 of 37** entries are identifiable (§1), and the ~21 unnamed include the
low-resolution batch that produces the other clauses' quoted maxima. A re-run on the 16 would be a
**new measurement on a smaller set**, not a re-validation of the published figures, and reporting it
as the latter is precisely the error this arc has been unwinding. The row is marked with the
diagnosis instead, and the re-measurement is left as a scoped backlog item.

Worth noting what this says about the audit method: round 17 found the discrepancy by comparing two
adjacent rows, and could not tell which was wrong. Tracing the *rounds* rather than the *rows*
answered it in one pass — and turned "a count is stale" into "two clauses are untested", which is a
materially different claim.
