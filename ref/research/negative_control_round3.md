# Negative-control round 3 — the bench ran; Q1 and Q4 hold, Q2 and Q3 falsify

**Run 2026-08-13/14** per `negative_control_round3_preregistration.md` over the
enrolled 22, both subjects, full-run manifest. **44 rows attempted, 44 benched,
0 data defects.** Committed record: `negative_control_round3_bench.json`.

## Predictions readout

**Q1 — HOLDS. The bench does not flag its own null.** S-null: **0 of 22
DEGRADED** (bound ≤ 2). Three single F-data flags occurred (nulls whose drift
sat just past 3·S_r2) and none reached a verdict; one of them, 2VXN, was
stood down by a genuine REFMAC direction conflict (two-path +0.0214/+0.0220
vs REFMAC **−0.0122**) — the named-conflict machinery doing precisely its job
on the one null where the third opinion disagreed.

**Q2 — FALSIFIED, and the falsification is the round's finding.** S-SA:
**2 of 22 DEGRADED** (bound ≥ 12). SA damaged fit almost everywhere —
**F-data flagged 18 of 22**, median ΔR-free **+0.0209**, three-way
cross-tool confirmed (Q4) — but the damage was fit-ONLY on 20 of 22 entries:
geometry stayed inside the §4 clauses (F-geom 1, of which the zBOND
stand-down removed most candidates — the refiner's restraints actively
tighten bond geometry while fit degrades) and unmasked shift stayed under
0.12 Å (F-shift 2). The registered ≥ 2-family rule therefore reads
restraint-managed fit damage as not-degraded. **At sub-Å, simulated
annealing's signature is fit destruction with cosmetically preserved
geometry — the restraint-circularity confound the original plan named, now
measured on 22 entries.** The two DEGRADED are the catastrophic tail:
7OYN (ΔR-free +0.3837/+0.3882, REFMAC +0.3569, unmasked shift 1.50 Å) and
9TXE (+0.3217, shift 1.62 Å, three families).

**Q3 — FALSIFIED.** Zero protected-outlier fixes across both subjects. The
enrolled set's protections are clash-dominated (the phase-1 starvation
finding), and neither the null nor SA removed one — the inversion currently
has no live targets under protocol subjects.

**Q4 — HOLDS at 100 %.** REFMAC ΔR-free direction agreed with the two-path
sign on **19 of 19** measurable S-SA rows (bound ≥ 90 %). Three rows had no
REFMAC measurement (9YGW, 8R5K, 8QXQ — named, not silent).

## What the falsifications teach (round-4 registration inputs)

1. **The verdict rule under-counts.** F-data alone is already three-tool
   evidence (phenix path + gemmi path + REFMAC direction); requiring a second
   FAMILY suppresses 16 real fit degradations. Round-4 candidate: F-data
   with REFMAC agreement is a verdict by itself; the other families remain
   corroboration and characterization.
2. **The zBOND stand-down is double-edged**: it correctly blocks
   library-tightening from reading as geometry damage, but that is exactly
   why geometry cannot carry fit-damage detection at sub-Å.
3. **The protected-outlier inversion needs subjects that actually regularize**
   (e.g. geometry-weighted protocols) or rama/rota-protected entries
   (the phase-1 selection-starvation finding) before it can discriminate.
4. Guard gap, filed: the reconciliation guard pairs round docs with SCREEN
   records only; bench records need their own reconciliation.

## Bottom line

The harness's core promise is now measured from both sides: it does not
accuse the innocent (Q1: 0/22 false verdicts), it sees real damage when the
damage is structural (both catastrophic entries caught), and its registered
multi-family rule is deliberately conservative to a fault against fit-only
damage — with the fix a registered change away, not a rewrite.
