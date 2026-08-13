# Negative-control round 2 — ENROLLED

**Run 2026-08-13** per `negative_control_round2_preregistration.md` (with its A1
amendments), under full-run manifests with per-row input hashes. The screen
attempted **58** entries (30 initial representatives + 28 D4 replacements):
**3** floor failures, **32** data defects, **23** screened. D6 completed with
**no fallback** (18 unique worsening structures per path), one cross-path-agreed
headroom exclusion, and **22 entries enrolled** — above the stop-at-15 line, so
the round-1 negative-control set now exists. Committed records:
`negative_control_round2_screen.json`, `negative_control_round2_enrolled.json`,
`negative_control_round2_reps.json` (all reconciled by validate step 3b).

## Predictions readout

**P1′ — HOLDS.** 22 of 23 screened representatives enrolled (95.7 % ≥ 80 %).

**P2′ — HOLDS, emphatically.** S_phenix = 0.00275, S_gemmi = 0.00260 — a ratio
of 1.06 against the registered factor-of-3 bound. Per-entry cross-path
|Δ_phenix − Δ_gemmi| ran median 0.0007, max 0.0019: the two code paths measure
the same drift.

**P3′ — consistent, n = 1, recorded not banded.** The single headroom exclusion
is **2DDX** — the OLDEST screened deposition (2006; next oldest 2008, newest
2026). One data point of the PDB_REDO mechanism (older refinement software left
more on the table), exactly where the prediction pointed.

**P4′ — HOLDS at the bound.** 3 of the 30 initial representatives failed the
≥ 50-unmasked floor (registered bound ≤ 3; round 1: 16/30). All three sit just
under it (5HB7 40, 6Q00 41, 9RZL 38) — the R1 size criterion moved the floor
from a stratum-wide wall to a marginal cut.

**P5′ — FALSIFIED.** 11 of the 30 initial representatives were data defects
(bound ≤ 6; round 1: 14/30). The registered array-selection rule did its job —
the round-1 dominant cause ("multiple equally suitable arrays", 40/48) fell to
2 obs-label defects in the whole 58 — but two attrition sources were
underestimated: **intensity-only depositions** (4 initial; the gemmi path
consumes amplitudes, so the D6 two-path requirement is unmeetable — the
registered named-defect outcome) and **ligand-restraint entries** (5 initial;
R3 kept restraint generation out of the protocol).

## The headroom machinery discriminated

2DDX: Δ = **−0.0085 / −0.0083** (phenix/gemmi), past both −3S lines
(−0.00825 / −0.00780) — excluded, with the registered mask-fraction report:
0.229 masked, 253 unmasked, 4 protected residues (a low mask fraction, so the
apparent headroom is not obviously a masked-region artifact — the #321
confound is quantified, not silent). 7R2H (−0.0051/−0.0054) sat INSIDE the
tolerance on both paths and enrolled: the noise scale separates real headroom
from null-refinement wobble rather than excluding every improver.

Screened drift ran min −0.0085 / median **+0.0032** / max +0.0214 — the
positive shift the negative-control premise predicts from gold-standard starts.

## Defect census (32 across all 58 attempts)

| cause | n | disposition |
|---|---:|---|
| ligand needs restraint CIF | 18 | R3 registered named-defect; the count now argues for generation as a round-3 change |
| intensity-only deposition (gemmi path dead) | 11 | registered two-path constraint; a French-Wilson F conversion is a round-3 candidate |
| no registered observation labels | 2 | the R2 rule's residue — exotic label schemes |
| fetch failed | 1 | transient, after retry |

## Stratum-specific reporting (registered estimand)

Stratum (≤ 0.9 Å): 21 screened, 20 enrolled. Band (0.9, 1.0]: 2 screened, 2
enrolled. Per the registered estimand statement these results characterize the
extreme-resolution stress set; band coverage remains thin by design.

## The enrolled set (22)

2VXN 3ZOJ 4M7G 5KXV 5R32 5XS6 6F1O 6Q01 6XVM 6ZWY 7ATV 7OYN 7R2H 7TVL 7TWR
8ERE 8QXQ 8R5K 9P25 9TEU 9TXE 9YGW

This is the set the benchmark legs (plan phases 3–4) run on.

## Carried to round 3

1. Ligand-restraint generation (18 defects say the R3 named-defect stance is
   expensive) — registered change candidate.
2. French-Wilson conversion for intensity-only entries (11 defects) — would
   need the gemmi path to consume converted F with the conversion recorded.
3. The #321 mask-constrained D6 criterion, with its first real calibration
   datum (2DDX's 0.229 mask fraction).
4. P5′'s falsification means the defect-rate prediction needs re-basing on
   this round's census before round 3 registers its own.
