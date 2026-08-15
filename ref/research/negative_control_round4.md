# Negative-control round 4 — V1 and V3 hold; V2 falsifies; the arch closes

**Run 2026-08-14** per `negative_control_round4_preregistration.md` over the
enrolled 22. **22 attempted, 22 completed, 0 data defects.** Record:
`negative_control_round4_recover.json` (manifest carries the C1 thresholds,
recomputed from the round-3 record and asserted against the registration at
startup).

## Predictions readout

**V1 — HOLDS on both readings, 22 of 22.** Achieved perturbation shift ran
0.204–0.280 Å (median 0.246) on the all-residue reading and 22/22 also on the
unmasked reading — the prereg's wording ambiguity (which shift V1 meant) is
moot on this data and is named here rather than exploited.

**V3 — HOLDS, 22 of 22.** Every unrecovered perturbed model read **DEGRADED**
— F-data and F-shift on all 22, F-geom additionally on 13, and **F-protected
on 2: the protected-outlier inversion's first live firings.** The perturber
itself supplied them — `phenix.dynamics` defaults to
`fix_rotamer_outliers=True`, i.e. it regularizes genuine protected outliers
(the Arg126 mechanism the plan's confound section named), which round 3's Q3
could not observe under SA. Together with round 3's Q1 (0/22 false
verdicts on correct models), the plan's anti-gaming arch is now measured
from both ends: **a damaging subject fails round 3; a do-nothing subject
fails round 4.**

**V2 — FALSIFIED, 5 of 22 registered successes (bound ≥ 16), and the honest
count is lower.** The five: 7R2H, 6ZWY, 9TXE, 9YGW, 8R5K. Audit before
publishing, not after:

- **9YGW (+0.0333) and 8R5K (+0.0263) are fallback artifacts, not healed
  fits** — they are the REFMAC-unmeasurable entries, where C1 cannot fire by
  registration and the ≥ 2-family fallback finds nothing. Rule-correct, and
  disclosed as what it is: success by absence of evidence.
- 7R2H, 6ZWY, 9TXE are genuine but **marginal** — residuals +0.0109 to
  +0.0124 sit just under the C1 lines.

So: **3 of 22 genuinely fit-healed.** The systematic finding: recovery
restored COORDINATES almost perfectly everywhere (unmasked shift to
deposited: 0.008–0.045 Å, median 0.021 — the 0.25 Å shake geometrically
undone) while residual ΔR-free stayed at +0.010 to +0.049 (median +0.019,
≈ 5× the null-typical drift). **At sub-Å, the plain null protocol recovers
structure but not fit** — consistent with the perturbation scrambling
ordered solvent that the protocol never rebuilds (registered protocols
contain no ordered_solvent step; hypothesis for round 5, not measured here).
One recovery (8QXQ, also REFMAC-unmeasurable) even read DEGRADED on the
round-3 families.

## What this buys the harness

The C1 rule refused to certify 16 incomplete repairs whose coordinates
looked perfect. That is precisely the discrimination an agent-grading
harness needs: "my coordinates are back" is measurably not "the structure
is repaired," and the bench can tell the difference cross-tool.

## Carried to round 5 (the first agent subject)

1. **Fix the fallback asymmetry**: REFMAC-unmeasurability currently makes
   success EASIER (the C1 rule disarms and nothing replaces it). Round-5
   registration should require positive fit evidence for recovery success —
   e.g. two-path thresholds standing alone when REFMAC is absent — instead
   of benefiting from missing evidence. Filed as an issue.
2. **The recoverer is the floor, not the bar**: 3/22 is what the plain null
   protocol achieves; an agent subject claiming repair now has a measured
   baseline to beat and a bench that cannot be satisfied with coordinates
   alone.
3. The ordered-solvent hypothesis is testable as a registered protocol
   variant (null + solvent rebuilding) before or alongside agent subjects.
