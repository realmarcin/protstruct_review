# Negative-control round 9 — the ANIS adoption: all three predictions hold

**Run 2026-08-19** per `negative_control_round9_preregistration.md`. Record:
`negative_control_round9_anis.json`. Score: **X1, X2, X3 all HOLD** — the
first round of this track with no falsification, and the adoption lands.

## J1/X1 — regeneration reproduces the committed nulls. HOLDS, 22/22.

All 22 null legs regenerated (`r9n_`) under the registered protocol from
the durable store. Every entry's two-path deltas reproduce the committed
round-3 values within the registered 0.002 — and the worst absolute
difference across all 44 comparisons is **0.0006** (8R5K), an order
tighter than the allowance. The reproduction confirms in one sweep: the
round-6 strip and round-8 wavelength patch preserved measurement-relevant
data identity, and the refinement protocol is deterministic enough to
regenerate history from clean inputs. Every regenerated model carries
anisotropic ADPs (`ANISOU` present, 22/22), so the ANIS legs measured what
they claim to.

## J2/X2 — the ANIS null distribution. HOLDS.

Over the 21 measurable entries (9YGW permanently two-path, round 8):
median |delta_anis| = **0.0051** (< 0.01 as predicted), and

    d_refmac_anis = 0.01150

— inside the registered [0.002, 0.012] bracket. The ISOT estimator
re-derived on the same regenerated models gives 0.0054 (vs the committed
0.00560 — consistency, reported for comparison only, never for verdicts).
The ANIS threshold is roughly 2× the ISOT one: applying the deposited
aniso model to both sides of the delta exposes real ADP-model movement
that iso-collapse was hiding, so the null noise is honestly larger.

## X3 — direction agreement improves under ANIS. HOLDS, 20/21 vs 17/21.

On the shared-sign population (21 entries; **zero** sign-split
exclusions): REFMAC's delta sign matches the two paths on **20 of 21**
under ANIS against **17 of 21** under ISOT. And the entry that started
this thread closes mechanistically: 2VXN's null delta is **−0.0122 under
ISOT** (the three-round sign conflict, #355) and **+0.0130 under ANIS**.
The conflict was never about 2VXN's data — collapsing the deposited
model's superior aniso ADPs cost REFMAC more than collapsing the refined
model's, so refinement appeared to *improve* its R. The convention the
family defaulted to was manufacturing the disagreement.

## J3 — the adoption, landed

- `bench_negative_control.refmac_pass` (and the extracted, unit-tested
  `refmac_keywords`) gain the `anis` parameter; the ISOT default keeps
  rounds 3–8 reproducible byte-for-byte.
- `bench_recover_leg.REGISTERED_FIT_THRESHOLDS_ANIS` =
  {d_phenix 0.01200, d_gemmi 0.01025, **d_refmac 0.01150**} — two-path
  values are the H1 table (conventions do not touch them); the REFMAC
  value is registered here from the measured distribution, with
  `anis_thresholds_from_record()` re-deriving it at startup (the same
  record-vs-registration discipline as C1/H1).
- From round 10 on, verdict-bearing drivers pass `anis=True` by name and
  grade gold standards with their anisotropy applied; the ISOT table and
  default remain solely as history. The no-mixing rule survives the
  adoption: no comparison crosses conventions.

## Round-10 inheritance

1. The first verdict-bearing round under ANIS (any new subject leg uses
   the adopted convention and table).
2. Agent sandboxes (#356) with the next agent leg; #321 (mask-constrained
   D6) with the next screen registration.
