# Negative-control round 4 — pre-registration (recover leg + fit verdict)

Registered **before any round-4 measurement**. Two registered changes, both
demanded by round 3's falsifications, plus the perturb-then-recover leg (plan
phase 4). Everything else — enrolled set, masks, array selection, provenance
machinery, the ≥ 2-family structural verdict — carries over unchanged. Live
canaries and retro-computations quoted below were run 2026-08-14.

## C1 — the fit verdict, re-registered and NULL-CENTERED

Round 3 measured why the ≥ 2-family rule undercounts: at sub-Å, fit damage
travels alone. The candidate fix (F-data + REFMAC as a standalone verdict)
was retro-checked before registration and the naive form FAILED it: with
thresholds at 3·S from ZERO, **3 of 22 round-3 nulls** would read as fit
verdicts — because the null drift is not zero-centered (median +0.0035), so a
zero-based threshold sits only ~1.7 MAD above the null's center. The zero
anchoring was a design flaw caught by retro-check, and the registered rule is
centered on the measured null instead:

**FIT-DEGRADED** iff ALL three tools exceed their null-centered thresholds
`median_null + 3·MAD_null`, computed per tool from the round-3 S-null record
(n = 22; 19 for REFMAC) and FIXED here:

| tool | null median | null MAD | threshold |
|---|---:|---:|---:|
| phenix path | +0.00350 | 0.00290 | **+0.01220** |
| gemmi path | +0.00385 | 0.00235 | **+0.01090** |
| REFMAC | +0.00180 | 0.00120 | **+0.00540** |

REFMAC unmeasurable → no FIT-DEGRADED verdict is possible for that row; the
conservative ≥ 2-family rule alone applies (named, as in round 3). Verdict
precedence: DEGRADED (≥ 2 families, unchanged) ⊃ FIT-DEGRADED ⊃ not-degraded.

**Retro-disclosure on the round-3 record** (the rule's acceptance basis, not
a prediction): nulls — **1 of 22** past the centered rule (6XVM,
+0.0161/+0.0156/+0.0071, a genuine null-tail outlier; within the ≤ 2
false-verdict bound). S-SA — **13 of 22** FIT-DEGRADED including both
structural DEGRADED entries; the two fit-damaged rows it cannot reach (9YGW,
8R5K) are exactly the REFMAC-unmeasurable ones, falling back as registered.

## C2 — the perturb-then-recover leg (plan phase 4)

Per enrolled entry:

1. **Perturb**: `phenix.dynamics stop_at_diff=0.5 random_seed=42` (fixed seed
   — the draw must reproduce), output prefix `r4p_`. The internals of the
   stop criterion are NOT registered (and not verified); what is registered
   is that the ACHIEVED unmasked and all-residue Cα shifts are measured and
   recorded per entry, and V1 is judged on those recorded values. Disclosed
   canary (4M7G): achieved Cα 0.2515 Å over 222 pairs at stop_at_diff=0.5 —
   past the 0.12 Å stay-band, far from catastrophic.
2. **Recover**: the registered null protocol (default `phenix.refine`,
   3 macro cycles, registered array selection) refining the PERTURBED model
   against the deposited data, prefix `r4r_`.
3. **Judge** both the perturbed model and the recovered model against the
   deposited start with the full round-3 bench machinery + C1.

**Recovery SUCCESS** (registered): recovered-vs-deposited unmasked Cα
< 0.12 Å (§4 band) AND the recovered model is neither DEGRADED nor
FIT-DEGRADED vs the deposited start.

## Predictions

**V1 — the perturbation bites.** Achieved Cα shift ≥ 0.15 Å on ≥ 20 of 22
(fixed denominator; a dynamics failure counts against).

**V2 — sub-Å data pulls back hard.** Recovery SUCCESS on ≥ 16 of 22
(Afonine's recovery result at lower resolution, cited in the plan, should
only strengthen at sub-Å).

**V3 — a do-nothing subject cannot pass this harness.** The UNRECOVERED
perturbed models read DEGRADED or FIT-DEGRADED on ≥ 20 of 22. This is the
pairing the plan demanded: round 3 established the bench does not flag
correct models; V3 establishes it flags un-repaired damage — so a subject
that returns its input unchanged fails round 4 while a damaging subject
fails round 3.

## Outputs and scope

- `negative_control_round4_recover.json` (canonical; manifests, hashes,
  per-stage numbers) + `negative_control_round4.md`, swept against the record.
- Runtime: 22 dynamics runs (seconds each) + 22 recovery refinements
  (~25 min each ≈ 9 h) + bench measurement passes.
- Subjects remain protocols; the FIRST AGENT SUBJECT is round 5, now that
  both harness edges are measured. Enrollment unchanged; #321 and the parked
  expansion candidates unaffected.

## What this round does not do

- No re-judging of round-3 verdicts in the round-3 record — C1 applies from
  round 4 forward; the retro-computation above is disclosure, not a rewrite
  of a committed record.
- No threshold tuning after data: the C1 table and the 0.12 Å / stop_at_diff
  / seed values are fixed by this document.
