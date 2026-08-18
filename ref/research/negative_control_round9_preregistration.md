# Negative-control round 9 — pre-registration (the ANIS adoption)

Registered **before any round-9 measurement**. This round discharges the
adoption gate rounds 7–8 armed: the third-opinion leg switches from
grading gold standards with their anisotropy discarded (`BREF ISOT`,
REFMAC's default) to applying it (`REFI BREF ANIS`) — but only through the
registered no-mixing route: a full re-derivation of the REFMAC null
distribution under the new convention. No benchmark verdicts this round;
committed rounds are history.

**Disclosed basis (2026-08-18):** the round-8 census (every measurable
entry drops under ANIS, median −0.0329, all beyond `d_refmac` ×~6); the
durable store is wavelength-complete (rounds 7–8 remediation); and the
round-2/3 refined null models are **gone** — the /tmp reaper took them,
only 8R5K's round-6 clean null (`r6n_`) survives. The null legs must
therefore be regenerated, which is a new measurement batch under the
registered protocol, not a recovery.

## J1 — regenerate the null legs

The registered null protocol, unchanged from rounds 2–3 (phenix.refine,
3 macro cycles, default weights, registered array selection, no generated
flags), on all 22 entries from the durable store, `r9n_` prefix. Canary
one entry end to end before the batch.

Basis for reproducibility expectations, disclosed: the store's
observation and flag bytes are identical to what rounds 2–3 refined
against (round-6 strip preserved them by fingerprint; the wavelength patch
touched dataset metadata only), and `phenix.refine` measured deterministic
8/8 on this machine and version (tolerance round 20). Regeneration should
therefore land close to the committed round-3 deltas — X1 makes that a
prediction, not an assumption.

The regenerated models' ADP form is recorded per entry (does the refined
output carry `ANISOU`?). phenix.refine keeps the anisotropic
parameterization for atoms that had it; an entry whose null comes back
iso-only is named, and its ANIS leg is expected to behave as ISOT there.

## J2 — the ANIS null distribution and the new threshold

Per entry: REFMAC NCYC 0 under `REFI BREF ANIS` on the deposited model
(the round-8 census already holds these) and on the regenerated `r9n_`
null; `delta_anis = post − pre`. Over the measurable population (21 —
9YGW is permanently two-path by the round-8 stand-down):

    d_refmac_anis = median(delta_anis) + 3 · MAD(delta_anis),
    MAD floored at 0.0005 (the registered S_FLOOR), rounded to 5 decimals

— the same estimator as C1/H1, on the new convention's own null
distribution. The ISOT `d_refmac` (0.00560) is retired to history for
reproduction of rounds 3–8; it is never compared against an ANIS
measurement (the no-mixing rule survives the adoption).

## J3 — the adoption, as code with a cross-check

On this round's execution merge:

- `bench_negative_control.refmac_pass` gains an explicit ADP-convention
  parameter; the ISOT default is retained so committed history reproduces,
  and future verdict-bearing drivers pass ANIS by name.
- `bench_recover_leg.py` gains `REGISTERED_FIT_THRESHOLDS_ANIS` beside the
  retained ISOT table, with a startup cross-check that re-derives it from
  the round-9 record (the same record-vs-registration discipline as C1/H1).
- The E1 rule is unchanged in shape: all-three when REFMAC is measurable
  (now under ANIS), two-path standing alone when not; 9YGW is
  two-path by standing rule and its rows say so.

The threshold value itself is registered by the round-9 doc from the
measured distribution — this preregistration registers the estimator, the
population, and the adoption mechanics, not the number.

## Predictions

**X1** — regeneration reproduces the committed round-3 two-path null
deltas: on ≥ 20 of 22 entries, |Δd_phenix| and |Δd_gemmi| between the
regenerated and committed values are each ≤ 0.002 (determinism + identical
observation bytes; the allowance is for the wavelength-metadata change and
any library-state drift).

**X2** — the ANIS null distribution is as tight as or tighter than ISOT's:
median |delta_anis| < 0.01 and `d_refmac_anis` lands in [0.002, 0.012]
(applying the deposited aniso model to both sides of the delta should not
widen the null noise).

**X3** — REFMAC direction-agreement with the two paths does not degrade
under ANIS. Population (#380): the null entries whose two path deltas
share a sign (an entry where d_phenix and d_gemmi disagree in sign has no
"two-path sign" and is excluded, with the excluded count reported). On
that population, the count of entries whose REFMAC delta sign matches the
shared two-path sign under ANIS is ≥ the count under ISOT, both measured
on the same regenerated models.

## Outputs and scope

`negative_control_round9.md` + `negative_control_round9_anis.json`
(regenerated null deltas both paths + both REFMAC conventions per entry,
the derived threshold, the X1 reproduction table), swept against the
record. Code: `bench_round9.py` (SET_RECORD-gated), the J3 adoption edits
with tests (threshold cross-check; refmac_pass convention parameter
defaulting to history-faithful ISOT). NOT in scope: benchmark verdicts;
agent legs and sandboxes (#356); #338, #321; re-judging committed rounds;
any store write (the store is complete as of the round-8 writes).
