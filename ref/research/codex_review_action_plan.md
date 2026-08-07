# Action plan — Codex conceptual review (2026-08-06)

An external conceptual review by the Codex plugin (`codex resume 019fdabc-efb8-7d42-b518-83f62daca4a4`)
of `main` at `f38eb02` produced the findings this plan addresses. The two load-bearing findings were
**verified against the repo before planning** (a false finding acted on is its own defect):

- **The registry's "single source of truth" is leaking.** `ref/driving_example.md` and per-task drivers
  (`driving_example_T01/T04/T13.md`) and several `bench_*.py` docstrings quote **retired** threshold
  values while the registry has moved on — e.g. `driving_example.md:68` grades cross-tool CA RMSD
  agreement at **0.10 Å** where §3 now says **0.03 Å**; `:69,:71` use ΔRMSD +0.05, CC_mask −0.01,
  `d_FSC_model` +0.05 (round-5 values retired by rounds 7/13/40); `driving_example_T04.md:36` is tagged
  `[template — registry §4 map-model]` yet carries the old numbers. **No gate reconciles registry →
  consumers.** Confirmed.
- **`NEXT_TASKS.md`'s "Open tasks" prose is stale** — line 166 says "state as of round 27"; its open
  items (#224 crossing-quality "untested", #225 X-ray widths "rest on lost maxima") are superseded by
  rounds 40/41/42. The round *table* is current; only the ledger prose drifted. Confirmed.

**One nuance the plan must respect:** some driver numbers are `[catalog gold_standard]` (how good a
*result* should be) — a different quantity from §3's cross-tool *agreement* tolerance — so the fix is a
**per-value audit**, not a blind find-replace.

## Priority 1 — Stop the source-of-truth leak (highest risk)

1. Audit every threshold value in `driving_example.md`, `driving_example_T01/T04/T13.md`, and the
   docstrings of `bench_t01_superposition.py`, `bench_t13_wilson_b.py`, `bench_refinement_deltas_em.py`.
   Classify each as **(a)** a stale *restatement* of a registry value → replace with a citation to the
   registry row (CODING_STANDARDS rule 2: "cite, don't restate"), or **(b)** a legitimately different
   quantity (`[catalog gold_standard]`, `[literature]`) → keep, but verify its tag points at the right
   source.
2. Add a **registry-to-consumer consistency gate** (`check_driver_thresholds.py`, testable, wired into
   `validate.sh`): for each numeric threshold a driver quotes with a `[registry §N]`/`[template]` tag,
   assert it matches the current registry value; flag restated-but-untagged numbers. The durable fix —
   it makes recurrence impossible, the repo's standing "gate the gap" response to silent-drift classes.

## Priority 2 — Reconcile the ledger

3. Rewrite `NEXT_TASKS.md`'s "Open tasks" section to current reality: mark #224 (round 40), #225
   (round 41), #269 (round 42) resolved; drop the "state as of round 27" framing; bump "Last
   reconciled" to round 42.

## Priority 3 — Scientific direction (each a preregistered round, needs approval)

4. **Cross-version reproducibility round** — the single most-cited untested caveat. Pre-register a
   representative X-ray/EM panel refined under pinned `phenix-2.0-5936` *and* one newer build, treating
   version shift as its own distribution rather than assumed noise.
5. **Triage the 6 remaining `⚠ partial record` rows** — for each, decide replace-with-coverage-estimator
   (as round 42 did), remeasure-on-fresh-population, or retain-as-historical. Live ones: the §4
   geometry row's clashscore figures; the EM map-model denominators.
6. **Shore up the small-n load-bearing fits** — round 42's n=44 lognormal, round 40's 19 labels. Grow
   the samples toward the ~300 a nonparametric 99/95 bound needs, or add a goodness-of-fit guard so the
   lognormal assumption is re-checked as entries accrue.

## Priority 4 — Sustainability of the machinery

7. Write explicit stopping/consolidation criteria for the round cadence (the repo's own lessons warn
   audits are unbounded), and consider consolidating the proliferating literal-based gates behind fewer
   machine-readable representations.

## Sequencing

P1 and P2 are pure integration hygiene — no new measurement, mergeable in one or two clean PRs, and
P1's gate prevents the whole class recurring; do them first. P3 items are real scientific rounds needing
pre-registration and target decisions (as #269 did). P4 is a short design note.
