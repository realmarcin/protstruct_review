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

Two-path constraint carried explicitly: the gemmi R path consumes amplitudes,
so an entry whose MTZ offers only intensities can be refined but not
cross-checked — it fails the D6 two-path requirement and is recorded as a named
data defect, not silently single-pathed.

## R3 — ligand-restraint entries stay named defects

Round 1 hit 2 of 48. Registered treatment: unchanged — a `phenix.refine`
refusal for missing restraint CIFs is a named data defect with D4 replacement.
Generating restraints (`phenix.ready_set`/eLBOW) would add an unregistered,
PHENIX-only preparation step to the protocol; if the defect rate makes this
matter, generation becomes a round-3 registered change.

## D7′ — the draw over the new pool

The size-filtered stratum holds **26 clusters**, so round 1's original intent
now fits the 30-cluster scope: **every ≤ 0.9 Å stratum cluster representative
(26 measured) + top-up to 30 from (0.9, 1.0] by ascending representative
d_min (4)**. D4 ranking and within-cluster replacement unchanged.

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
- No change to masks, floor value, D6 formula, or the tolerance discipline.
- No PHENIX-version change: `phenix-2.0-5936` pinned, its occupancy-selection
  crash (round-1 6UWW) stays a named defect.
