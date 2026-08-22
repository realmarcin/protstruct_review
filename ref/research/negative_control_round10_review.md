# Negative-control round 10 — adversarial review closeout

**Review 2026-08-21** of PR #415. The review was performed read-only before
any remediation. Every verified finding was filed before code changed.

## Findings and disposition

- #416 (high): a child that ignored `SIGTERM` survived after its process-group
  leader exited. Cleanup now tests liveness of the whole owned PGID and sends
  `SIGKILL` after the grace period even when the leader has already exited.
  Real-process regressions cover timeout and concurrent cancellation.
- #417 (high): a normal-exit cache record could return stale output after its
  protocol arguments changed. Cache hits now require exact arguments, hashes
  of every stage input, and the output hash. Tests alter each identity
  component independently. The 66 preserved process records from this run
  were upgraded from their extant inputs and outputs; no scientific
  measurement or verdict was recomputed during that evidence migration.
- #418 (medium): early data-defect exits skipped the shared-store after-hash.
  Store verification now executes in `finally` after every path that acquired
  a before snapshot. A synthetic failed stage that mutates an input is refused.
- #419 (medium): the guard did not derive the ANIS, hydrogen, prior-`osol`, and
  all-stage session headlines. The record now carries row-level ANIS-log and
  content-identity evidence plus derived hydrogen/comparison summaries. The
  guard reconciles those summaries, all three subprocess stages, and the
  round-10 prose; mutation tests exercise each class.

## Reconciled evidence

The remediation preserves the registered result: `osol_h` succeeds on 15/22
entries versus 11/22 for `osol`, with four gains and no losses; ANIS is
measurable on 21/21 eligible rows and appears in 44/44 recorded pre/post logs;
H/D counts span 725–5196 and are retained on 22/22 entries; the 22 sandboxes
and refinement PGIDs remain distinct; and 2VXN remains the single W4
contradiction. The scientific driver therefore still exits nonzero after a
full run for the preregistered W4 reason.
