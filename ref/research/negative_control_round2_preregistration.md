# Negative-control round 2 — pre-registration

Registered **before the round-2 screen runs**. Round 1 STOPPED at its registered
D6 finding (`negative_control_round1.md`): 30 of 30 initial representatives
failed before the screen (16 floor / 14 data defect), 40 of 48 defects were one
underspecification, and the single screened entry (a D4 replacement) demonstrated
the mechanism. This document re-registers exactly the three items round 1's
findings demand and NOTHING else — every decision not named below carries over
from `negative_control_round1_preregistration.md` unchanged (D1 window, D3
floor ≥ 50, D4 replacement rule, D5 mask thresholds, D6 tolerance formula with
its thin-side fallback, the stop-below-15 decision rule). Counts and canaries
quoted below were measured live 2026-08-12.

## R1 — size criterion at selection (fixes the floor × stratum tension)

D2 gains one node: **`rcsb_entry_info.deposited_polymer_monomer_count` ≥ 100**.
Rationale from measurement, not taste: round 1's floor failures were the tiny
designed-peptide population (8 entries with ZERO unmasked residues), and the
phase-1 median mask fraction of 0.43 puts a 100-residue entry at ~57 expected
unmasked — above the unchanged D3 floor of 50 with margin, without excluding
real small proteins the benchmark wants.

Measured pool under D2 + R1: **≤ 1.0 Å: 339 entries / 90 clusters (+2
unclustered entities); ≤ 0.9 Å stratum: 35 entries / 26 clusters (+1)**. The
designed-peptide stratum population is gone (77 → 35 entries at ≤ 0.9 Å).

## R2 — registered data-array selection (fixes 40/48 round-1 defects)

Two selector rules, applied when fetching produces a multi-array MTZ, both
implemented in `screen_round1.py` and pinned by unit tests:

- **Observation array**: first present pair from
  `OBS_LABEL_CANDIDATES` — F-obs-filtered/SIGF-obs-filtered, F-obs/SIGF-obs,
  FOBS/SIGFOBS, FP/SIGFP, F/SIGF, then intensity pairs (I-obs/SIGI-obs,
  IOBS/SIGIOBS, I/SIGI). No registered pair present → named data defect.
- **R-free flag array**: first present label from `FLAG_LABEL_CANDIDATES` —
  R-free-flags, FreeR_flag, FREE, FreeRflag, R-free-flags-1. None present → no
  selector (phenix's own single-array detection).

Selector syntax, canaried on 9YGW (a round-1 array-defect casualty): PHENIX
2.0's data manager performs array selection BEFORE the legacy
`refinement.input.xray_data.labels` scope is consulted — that phil parses and
is silently ignored. The working selector is `miller_array.labels.name=`, one
per ambiguous array kind, with exact-label match taking precedence over
substring (which is what makes `R-free-flags` safe alongside its
`R-free-flags-1` twin — verified live). The refinement runs under a fresh
`r2n_` output prefix so no round-1 cached output can be silently adopted
(the #124 argument).

The same registered labels feed **every consumer** of the converted MTZ,
computed ONCE per entry by `screen_round1.select_arrays` and passed as
arguments — no consumer re-derives its own: `phenix.refine` via
`miller_array.labels.name`, `phenix.model_vs_data` via its own `f_obs_label=`
/ `r_free_flags_label=` params, and the gemmi path via explicit obs columns
AND an explicit free column into `gemmi_rfactor.compute` (the 2026-08-12 Codex
review, #317, found the gemmi path previously used its own divergent candidate
list and could not see `R-free-flags-1`). The selected labels are recorded in
every screen row (`array_selection`).

Two-path constraint carried explicitly: the gemmi R path consumes amplitudes,
so an entry whose MTZ offers only intensities can be refined but not
cross-checked — it fails the D6 two-path requirement and is recorded as a named
data defect, not silently single-pathed.

**Disclosed canary (9YGW, 0.87 Å, 252 unmasked — a round-1 array-defect
casualty), run 2026-08-12 under the full R2 rule:** status `screened`;
ΔR-free **+0.0065 on the phenix path (0.1274 → 0.1339) and +0.0065 on the
gemmi path (0.1286 → 0.1351)** — the second entry to show a positive,
cross-path-identical-to-four-decimals null-re-refinement Δ, after round 1's
5SY4 (+0.0056/+0.0056). As with round 1's disclosed figures, the registered
change is the selection rule, not this number; 9YGW re-enters the round-2
screen with everything else and its cached artifacts are under the round-2
prefix by construction.

## R3 — ligand-restraint entries stay named defects

Round 1 hit 2 of 48. Registered treatment: unchanged — a `phenix.refine`
refusal for missing restraint CIFs is a named data defect with D4 replacement.
Generating restraints (`phenix.ready_set`/eLBOW) would add an unregistered,
PHENIX-only preparation step to the protocol; if the defect rate makes this
matter, generation becomes a round-3 registered change.

## A1 — D6 statistical amendments (Codex review 2026-08-12, #318)

Registered before any round-2 measurement; these change round 1's D6 mechanics
in three ways and nothing else:

1. **Unique-structure counting.** The two R paths measure the same structure
   with the same model, data, and flags — paired, not independent (twice they
   have produced identical 4-decimal deltas). Every D6 n-threshold, including
   the pooled-fallback minimum of 8, counts UNIQUE structures. Round 1's stop
   reason counted one structure as "2 entries"; it stops either way, but the
   count is now honest.
2. **Full-precision deltas.** ΔR-free enters MAD unrounded; the 4-decimal
   value is display-only (`delta_display`).
3. **Noise-scale floor.** S_eff = max(S, 0.0005) per path — half the last
   digit of conventional 4-decimal R reporting — so a constant or degenerate
   worsening side cannot yield a zero-width tolerance where any jointly
   negative delta excludes. `s_floor_applied` is recorded whenever the floor
   binds.

## D7′ — the draw over the new pool

The size-filtered stratum holds **26 clusters**, so round 1's original intent
now fits the 30-cluster scope: **every ≤ 0.9 Å stratum cluster representative
(26 measured) + top-up to 30 from (0.9, 1.0] by ascending representative
d_min (4)**. If the live pool has moved and the stratum exceeds 30 at run time,
the draw falls back to the round-1 spread across the stratum (never the head,
#243) — registered here so the executor has no discretion either way. D4
ranking and within-cluster replacement unchanged.

**Estimand, stated plainly (Codex review, #322):** this draw takes all 26
stratum clusters but only 4 of the 64 band clusters, so ~87 % of the sample
comes from a stratum that is ~29 % of the pool. Round-2 results estimate
enrollment behavior for an **extreme-resolution stress set**, NOT the full
≤ 1.0 Å candidate population; P1′/P2′ verdicts are therefore reported both
pooled AND per stratum, and any generalization to the band awaits a
band-weighted draw in a later round. This is deliberate: the stratum is where
gold standards are best and where the benchmark premise is strongest.

**Cluster collisions (Codex review, #323):** entity-level clustering collapsed
to entry ids means one multi-protein entry can sit in several clusters. A
duplicate representative is a recorded cluster collision that falls through to
the cluster's next-ranked member at draw time (`cluster_collisions` in the
committed selection record); a cluster exhausted by collisions is recorded,
never silently absent.

## Predictions

**P1′ — enrollment.** ≥ 80 % of screened representatives survive D6 (round 1's
P1, now testable). *Falsified* if more than 6 of 30 show cross-path-agreed
headroom.

**P2′ — noise scales commensurate.** S_phenix and S_gemmi within a factor of 3
(round 1's P2). The 5SY4 pair (Δ identical to 4 decimals on both paths) says
this should hold comfortably.

**P3′ — exclusions skew old** (round 1's P3, recorded not banded).

**P4′ — the floor is defanged by R1.** ≤ 3 of the 30 initial representatives
(before replacement — fixed denominator, #309) fail the ≥ 50-unmasked floor.
Round 1 observed 16/30 without the size criterion; this is the direct test of
R1.

**P5′ — the defect census collapses under R2.** ≤ 6 of the 30 initial
representatives are data defects (round 1: 14/30, of which the array rule
addresses the dominant cause).

## Decision rule — unchanged

Enrolled set = screened representatives surviving D3 + D6, committed as
`negative_control_round1_enrolled.json`'s round-2 successor
(`negative_control_round2_enrolled.json`). Fewer than 15 enrolled → STOP at a
finding and re-register. Every exclusion named. The registered stop is what
round 1 exercised; nothing about it needs changing.

## What this round does not do

- No benchmark verdicts (plan phases 3–4 remain later rounds).
- No change to masks, floor value, or the tolerance discipline beyond the A1
  amendments above.
- No PHENIX-version change: `phenix-2.0-5936` pinned, its occupancy-selection
  crash (round-1 6UWW) stays a named defect.
- **Known limitation, carried openly (Codex review, #321):** the headroom
  screen's ΔR-free is GLOBAL — a legitimate change confined to masked
  altconf/lattice/poor-density residues can register as headroom and exclude
  an otherwise suitable candidate. Round 2 quantifies this (mask fraction is
  reported for every headroom exclusion); a mask-constrained local-fit
  criterion inside D6 is a candidate round-3 registered change, not a
  mid-round adjustment.
- Run-mode provenance (#319): every screen output embeds a run manifest
  (mode, flags, reps path, round); diagnostic/subset runs cannot write the
  canonical record, and all record writes are atomic.
