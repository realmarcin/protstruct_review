# Negative-control round 6 — data hygiene executed; U3 falsified, 2VXN deepens

**Run 2026-08-17** per `negative_control_round6_preregistration.md`. Record:
`negative_control_round6_hygiene.json`. The durable input store is live at
`~/protstruct_bench_inputs/` (all 22 entries migrated, stripped, sidecar'd);
every driver now records input hashes per row and defaults to the durable
store.

## Predictions readout

**U1 — HOLDS, with a correction to the prereg's own census.** All 22 entries
migrated and stripped with per-column observation fingerprints identical
before and after. But the strip removed derived columns from **12 entries,
not 1**: eleven carried map-coefficient sets (FWT/PHWT/DELFWT/PHDELWT, plus
FC/PHIFC/FOM on 6ZWY), alongside 8R5K's full HL set. The prereg's disclosed
census claimed "model-derived columns on 8R5K only" — wrong, because the
census script excluded DROP-listed labels from its unclassified report and
so never surfaced them. Map coefficients are inert to `phenix.refine`'s
target selection (round 5 established this), so no verdict changes; the
registration's factual claim was still wrong and is corrected here.

**U2 — HOLDS at exactly its bound, 2 of 3.** With `MAKE NEWLIGAND CONTINUE`:
8R5K measurable (0.1837, canaried) and **8QXQ newly measurable (0.1955)**.
9YGW remains unmeasurable, and its cause is now **named precisely**: the
log tail reads `rdaniso_cif: label_comp_id mismatch — atom record CSO /
aniso record CYS … Problem in read aniso`. The modified residue CSO
(S-hydroxycysteine) carries its parent name CYS in the deposited
anisotropic-ADP records, and REFMAC's aniso reader rejects the mismatch.
Plausibly workaroundable (strip or rename the aniso records); carried to
round 7. An earlier draft called this a silent termination — the cause was
in the log tail all along.

**U3 — FALSIFIED: the C1 table moves.** With the clean 8R5K null substituted
(+0.0034/+0.0043/+0.0060 — see U4), the recomputed table is
phenix **0.01200** (was 0.01220), gemmi **0.01025** (was 0.01090), REFMAC
**0.00560** (was 0.00540). Per the registration this triggers
**re-registration, not silent adoption**: the registered C1 table remains in
force until a round-7 registration adopts the clean-null table.

**U4 — HOLDS. 8R5K enrolls clean.** The stripped, phase-free null re-screen
(`r6n_`) gives ΔR-free +0.0034 / +0.0043 / +0.0060 — comfortably inside
every tolerance, no headroom, no fit degradation. 8R5K's gold-standard
status is restored on clean provenance; its contaminated protocol rows
(rounds 2–5) remain flagged history.

**U5 — the honest outcome is PARTIAL attribution, and the registered
substitution is NOT enacted.** The investigation's course:

1. Flag-convention hypothesis **refuted** (all 22 entries mark the test set
   with flag 0, matching REFMAC's default).
2. Controlled variants isolate a **solvent component** of REFMAC's
   divergence (~0.02: SOLVENT NO moves 0.1712 → 0.1511).
3. The Servalcat discriminator **also diverges**: the four-tool spread on
   deposited 2VXN is phenix mvd **0.1043** / gemmi path **0.1059** /
   Servalcat **0.1473** / REFMAC **0.1712** — against a
   deposition-reported R-free of **0.103**. The trust model's tiebreaker
   (the deposited entry) sides with the two same-data code paths; both
   Murshudov-family tools diverge high, and disagree with each other.

Substituting Servalcat would be false progress — it diverges from the
tiebroken pair too. 2VXN stays a named cross-tool anomaly, now quantified
across four tools plus the deposition, with sharper round-7 hypotheses:
resolution-cutoff handling, anisotropic scaling, and hydrogen-contribution
treatment at 0.82 Å. Disclosed: an earlier draft of the record's
attribution claimed Servalcat agreed with the two paths, citing "phenix
0.1467" — that figure belongs to 9BB0/5R2Z, not 2VXN; caught against the
round-2/3 records and corrected before commit.

## Also closed or codified this round

- The sidecar policy is code-adjacent doctrine (G1): written at fetch,
  verified on reuse, never re-baselined without recorded proof or a cited
  ruling. The round-6 migration wrote first-sight sidecars for the new
  store — a new store's first hash is not a re-baseline.
- `#349` is closed by construction: every driver row now carries input
  hashes.
- The `round_figures` findings snapshot went stale mid-round (the track
  filed ~35 issues since its last refresh) and tripped its own gate;
  refreshed. A staleness this large is the round-26 known mechanic at
  unusual scale.

## Round-7 inheritance

1. **Adopt the clean-null C1 table by registration** (the U3 falsification's
   required follow-up).
2. **The 2VXN four-tool spread** — the sharpened anomaly, with named
   mechanism candidates.
3. 9YGW's CSO/CYS aniso-record mismatch (try stripping/renaming aniso
   records); per-entry agent sandboxes (#356's second half) when the next
   agent leg runs.
