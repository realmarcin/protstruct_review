# Negative-control round 10 — pre-registration (first verdicts under ANIS)

Registered **before any round-10 measurement**. This is the track's first
verdict-bearing round under the adopted ANIS convention (round 9), it
extends the round-5 protocol ladder by one rung, and it ships the second
half of #356 — per-entry sandboxes — as load-bearing infrastructure
verified by its own registered prediction. Committed rounds are history.

## K1 — the subject: `osol_h`, the next rung of the protocol ladder

The measured ladder so far (round-4/5 recover legs, 0.15 Å perturbation,
seed 42): plain re-refinement **3/22**, ordered solvent (`osol`)
**11/22**, blinded agents **21/21**. The registered next rung is the
strongest *non-agent* protocol this data supports:

**`osol_h`** = the round-5 `osol` protocol plus **riding hydrogens**:
perturbed model → hydrogens added (riding) → `phenix.refine`,
3 macro cycles, `ordered_solvent=True`, riding-H refinement, default
weights, registered array selection. At this set's resolutions
(0.82–1.0 Å) the H contribution to F_calc is real (round 7 measured
REFMAC's H term at ~0.008 on 2VXN), so the rung is a genuine protocol
upgrade, not a lateral move. The H-addition mechanism is
`phenix.ready_set` (or the refine-native equivalent if the canary shows
2.0 moved it — the canary decides the invocation, the registration fixes
the protocol: riding H present during refinement, nothing else changes).

Candidate models are measured as-is (with their H), the deposited pre
side as-is (without) — the same each-model-as-its-own-content rule the
`osol` leg used for its added waters.

**Grading, first use of the adopted convention:** E1 unchanged in shape;
the fit table is `REGISTERED_FIT_THRESHOLDS_ANIS`
(0.01200 / 0.01025 / **0.01150**) and every REFMAC invocation on both
sides of every delta carries `anis=True`. No comparison mixes
conventions; 9YGW is two-path by standing rule (round 8) and its rows say
so. W4 unchanged (no success may contradict its own evidence at 2×
threshold).

Perturbation inputs: the registered round-4 perturbation
(`phenix.dynamics`, `stop_at_diff=0.5`, `random_seed=42`) regenerated
where /tmp reaping took the `r4p_` models; achieved shifts are recorded
per entry and DISCLOSED against the committed round-4 values (a
reproduction table, not a prediction — round 9's X1 already priced this
class).

## K2 — per-entry sandboxes (#356, the remaining half)

Round 5's two mutual `pkill -f phenix.refine` incidents were name-based
kills crossing entry boundaries. The registered mechanism:

- every entry's subject work runs in its own sandbox directory
  (`<work>/<pdb_id>/`) — no shared filename namespace, so the round-2
  cache-stem collision class dies by construction;
- every refinement subprocess is launched with `start_new_session=True`
  (its own process group — the portable macOS form of the `setsid` the
  round-5 agents lacked), and the row records the sandbox path and pgid;
- any kill the harness ever needs is **pgid-scoped**; name-based
  (`pkill -f`) process management is banned from the driver.

The sandbox is verified, not assumed — Y3 is its registered prediction.

## K3 — scope

Outputs: `negative_control_round10.md` +
`negative_control_round10_recover.json` (rows in the round-5 recover
shape, which the 3b guard already reconciles; plus per-row `sandbox`
and `pgid`). Code: `bench_round10.py` (SET_RECORD-gated), sandbox launch
helpers with tests. NOT in scope: agent subjects (the next agent leg
inherits the sandboxes this round proves); #321 (its registered change
binds the next *screen*, not this recover leg); store writes; re-judging
committed rounds.

## Predictions

**Y1** — `osol_h` clears the `osol` rung: recovery successes **≥ 14 of
22** (osol's 11 plus the riding-H fit gain; falsified if H addition
fails to move enough entries across the registered thresholds).

**Y2** — the ANIS grading machinery holds end to end: the third opinion
is measurable on **21 of 21** non-9YGW rows (both sides, `anis=True`),
zero convention-mixed comparisons (mechanically: the thresholds consumed
are the ANIS table and every REFMAC log in the round carries
`REFI BREF ANIS`), and W4 contradictions = 0.

**Y3** — the sandboxes hold: 22 distinct sandbox directories, 22 distinct
recorded pgids, zero refinements terminated by a signal (every
`phenix.refine` exit is a normal exit, success or failure alike), and
zero cross-entry file collisions (no row reads or writes outside its
sandbox except the shared read-only store).
