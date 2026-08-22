# Negative-control round 10 — `osol_h` clears the rung; sandboxes hold; W4 does not

**Run 2026-08-21** per `negative_control_round10_preregistration.md`. Record:
`negative_control_round10_recover.json`. Score: **Y1 HOLDS, Y2 is FALSIFIED as
registered, Y3 HOLDS**. The round completed all 22 subjects; its driver exits
nonzero after writing the full record because Y2's W4 clause found one
contradiction. That scientific failure is preserved, not normalized away.

## K1/Y1 — `osol_h` clears the `osol` rung. HOLDS, 15/22.

The riding-H plus ordered-solvent protocol recovered **15 of 22**, above the
registered floor of 14 and four more than `osol`'s **11/22**. No old success was
lost. The four entries that cross from failure under `osol` to success under
`osol_h` are **7ATV, 8R5K, 5R32, and 7OYN**.

Every `phenix.ready_set` output contained H/D atoms (**725–5196 per model**) and
every refined output retained exactly the same per-entry H/D count (22/22).
The seven failures are 6Q01, 8ERE, 3ZOJ, 9YGW, 7TWR, 6XVM, and 5KXV: six
`FIT-DEGRADED`, plus 3ZOJ `DEGRADED` by the multi-family rule. 9YGW remains the
registered permanent two-path case; every other row has the third opinion.

## K1 disclosure — the round-4 perturbations were regenerated

All 22 perturbations were regenerated with the registered
`stop_at_diff=0.5`, seed 42 invocation because the old `/tmp` artefacts were not
durable. The record joins every regenerated achieved shift to its committed
round-4 value. The maximum absolute reproduction gap is **0.0214 Å unmasked**
(9TEU) and **0.0181 Å all-residue** (7ATV). These are disclosed reproduction
differences, not a claim that coordinate generation is byte-deterministic; the
recovered candidates are graded from the shifts they actually received.

## K1/Y2 — ANIS holds end to end; W4 does not. FALSIFIED as a conjunction.

The convention machinery itself holds exactly:

- ANIS REFMAC is measurable on **21/21** non-9YGW rows;
- **0** rows mix conventions;
- all **44** pre/post REFMAC logs, including 9YGW's unmeasurable attempts,
  contain `REFI BREF ANIS`; and
- the driver consumes the registered 0.01200 / 0.01025 / 0.01150 table.

But Y2 also predicted **zero W4 contradictions**, and 2VXN repeats its named
contradiction. Its two primary paths worsen by +0.0221 and +0.0211 R-free; the
gemmi residual exceeds 2 × 0.01025, while ANIS REFMAC improves by −0.0095. The
standing conflict rule therefore refuses a fit-degradation verdict, yet W4
correctly refuses to let the resulting nominal success certify itself. The
record reports `w4_contradictions: 1`, and the driver exits nonzero after the
full record is written. This is the same entry that contradicted `osol` under
W4 in round 5; riding hydrogens did not resolve the cross-family disagreement.

## K2/Y3 — per-entry sandboxes hold. HOLDS, 22/22.

Every entry ran under its own `<work>/<PDB_ID>/` directory. Every subject
process started a new POSIX session; timeout and interrupt cleanup target only
the recorded PGID. The full-run evidence is:

- **22 distinct sandbox directories**;
- **22 distinct refinement PGIDs**;
- **0 signal-terminated refinements** (and no signal termination in any
  recorded dynamics/ready-set/refine stage);
- **0 shared-store mutations**, verified by hashing each PDB, mmCIF, MTZ, and
  validation XML before and after its row; and
- no work artefact outside its entry directory.

The execution also exercised interruption rather than merely testing it in
isolation: an early sequential 2VXN stage was interrupted while changing to the
bounded four-worker run. Only its active PGID was terminated; the two completed
rows remained intact, the active registry emptied, and the partial output was
refused as a cache hit on resume. That interrupted diagnostic process is not a
row in the full-run record.

## Infrastructure landed

- `entry_sandbox.py` owns path containment, fresh-session launch, active-PGID
  registration, and whole-group TERM→KILL cleanup, including descendants that
  outlive the group leader. Name-based `pkill` is absent.
- `bench_round10.py` supports bounded concurrent entries while retaining
  precise all-active cancellation, content-addressed stage resume, durable-
  store checks on every exit path, and atomic completed-row persistence.
- The negative-control guard rejects duplicate sandboxes/PGIDs, non-session or
  abnormal exits in any subject stage, store mutation, stale ANIS/H/comparison
  headlines, drifted perturbation comparisons, and interrupted “full” records
  that do not exactly match `SET_RECORD`.
- Focused tests launch real parent/child process groups and prove that a timeout
  reaches and, when needed, force-kills a descendant without touching a sibling
  sandbox. The adversarial review and remediation are recorded in
  `negative_control_round10_review.md`.

## Inheritance

The remaining half of #356 is complete. Future agent legs inherit
`EntrySandbox`; they must not reintroduce name-based process management. The
`osol_h` rung is measured at 15/22, but the 2VXN W4 conflict remains a named
scientific exception, not a certified success.
