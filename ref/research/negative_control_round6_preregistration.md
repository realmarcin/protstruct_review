# Negative-control round 6 — pre-registration (data hygiene)

Registered **before any round-6 measurement**. This round closes every data-
integrity wound the round-5 incidents exposed — #350 (MLHL phase leak), #349
(missing row hashes / the 6XVM arbiter gap), #355 (the 2VXN cross-tool
anomaly), #356 (durable storage) — in one registered pass. No benchmark
verdicts; committed rounds are history and are not re-judged. Live canaries
quoted below were run 2026-08-17.

## G1 — durable inputs and universal row hashes (#349, #356)

- The benchmark input store moves from `/tmp` (the reaper deleted three
  inputs mid-round-5) to a durable path: `~/protstruct_bench_inputs/`,
  fetched-and-hash-sidecar'd exactly as before.
- **Every per-entry row in every driver** (`screen_round1`,
  `bench_negative_control`, `bench_recover_leg`, `bench_round5`, and the new
  round-6 driver) records `input_hashes` — the round-4/5 recover and bench
  rows lacked them, which is why the 6XVM deletion had no committed arbiter.
- **Sidecar policy, registered after the round-5 operator finding**: a hash
  sidecar is written at fetch and verified on every reuse; it is NEVER
  re-baselined except with (a) a data-identity proof recorded in the same
  row/record (matched reflection count, amplitude and flag identity
  fractions, and the arbiter source), or (b) a user-approved ruling cited by
  name. Unilateral re-baselining is the defect class the permission layer
  halted in round 5; this clause makes the rule explicit rather than
  emergent.

## G2 — fetch-time stripping of phase-bearing derived columns (#350)

After `phenix.fetch_pdb` conversion, MTZs are stripped of
`FC, PHIFC, HLA–HLD, FWT/PHWT, DELFWT/PHDELWT, FOM` and map-coefficient
variants (`2FOFCWT/…`). Observations (amplitude and intensity pairs,
anomalous pairs) and all free-flag columns are KEPT byte-identically.

**Disclosed canary (8R5K, the one entry with HL columns):** stripping
removed exactly the 11 derived columns, `FOBS` verified byte-identical, and
`phenix.refine` on the stripped file selects **`target ml`** — the silent
MLHL switch is dead.

## G3 — 8R5K clean re-screen

8R5K's protocol legs (rounds 2–5 osol) are MLHL-contaminated history; this
round re-screens it clean: the registered null protocol (`r6n_` prefix) on
the stripped MTZ, two R paths + REFMAC, D6/E1 machinery unchanged.

**Threshold integrity check (registered):** the C1 null-centered table was
computed from 22 round-3 nulls INCLUDING 8R5K's contaminated null. Round 6
recomputes the table with the clean 8R5K null substituted and DISCLOSES
whether any threshold moves at the registered 5-decimal precision (U3); a
moved threshold triggers re-registration, not silent adoption.

## G4 — the 2VXN investigation (#355)

Three-for-three across rounds: both R paths agree while REFMAC's ΔR-free
sign conflicts. **Ruled out by disclosed canary (2026-08-17): twinning (no
twin laws possible for the C 1 2 1 lattice; L-test ⟨L²⟩ = 0.328 vs 0.333
untwinned) and exotic columns (the MTZ carries only FOBS/SIGFOBS + one flag
column).** Registered protocol, in order:

1. Flag-convention verification: which value marks 2VXN's test set, and does
   the REFMAC `FREE=` assignment agree with the phenix-selected
   `test_flag_value`?
2. Controlled REFMAC invocations: explicit resolution limits, explicit
   scaling options, solvent-model variations — one change at a time.
3. **Servalcat as the discriminator** (the third non-cctbx refiner in
   `ref/oracle_tools.md`): if Servalcat's ΔR-free direction agrees with the
   two R paths, REFMAC's handling of this entry is the outlier.

Registered outcomes (two-sided, U5): the conflict is ATTRIBUTED to a named
cause, or it is recorded unattributed and the registered substitution is
enacted — 2VXN's third-opinion leg switches from REFMAC to Servalcat, by
name, in all future rounds.

## G5 — REFMAC protocol amendments

- `MAKE NEWLIGAND CONTINUE` joins the standard `NCYC 0` invocation.
  **Disclosed canary:** 8R5K's REFMAC unmeasurability was a LIGAND-LIBRARY
  gap (Y6Z unknown → "New ligand… Stopping"), NOT the phase columns; with
  the keyword it measures cleanly (Free R 0.1837 on the deposited model).
  The prior belief that stripping would unlock REFMAC was wrong and is
  corrected here before registration.
- The `FREE=` flag convention is verified per entry against the
  phenix-selected `test_flag_value`; mismatches are recorded in the row
  (a swapped convention silently relabels work as free).

## Predictions

**U1** — stripping preserves every observation and flag column byte-exactly
on all 22 entries (canaried on 8R5K; verified programmatically per entry).

**U2** — with G5, REFMAC becomes measurable on at least 2 of the 3
previously unmeasurable entries (8R5K canaried; 9YGW and 8QXQ predicted to
share the ligand-gap cause).

**U3** — the C1 thresholds are unchanged at 5-decimal precision under the
clean-8R5K substitution.

**U4** — 8R5K's clean null re-screen ENROLLS (all measurable paths inside
the D6/E1 tolerances).

**U5** — two-sided as registered in G4.

## Outputs and scope

- `negative_control_round6_hygiene.json` (strip verification per entry,
  8R5K re-screen, C1 recomputation, 2VXN investigation record) +
  `negative_control_round6.md`, swept against the record.
- Code: the strip step in `screen_round1.fetch_pair` (all drivers inherit),
  row hashes in the three drivers lacking them, the REFMAC amendments,
  durable-store path change. Tests for each.
- NOT in scope: re-judging committed rounds; enrollment changes beyond
  8R5K's provenance annotation; #321 and #338 (separate work); agent
  process sandboxes (#356's second half — deferred until the next agent
  leg, where it is load-bearing).
