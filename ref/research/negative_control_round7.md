# Negative-control round 7 — the 2VXN anomaly is attributed; two premises fall

**Run 2026-08-17** per `negative_control_round7_preregistration.md`. Record:
`negative_control_round7_attribution.json`. Score: V1 and V2 HOLD, V3 and
V4 are FALSIFIED — both by premises the execution overturned, recorded
below without repair-by-iteration.

## H1/V1 — the re-registered table changes no committed verdict. HOLDS.

All 66 judged round-4/5 rows recomputed under both tables (each round's own
fit rule): **zero flips** in `fit_degraded`, the combined verdict, and the
round-5 W4 contradiction check. Round-3 verdicts are flag-based and predate
the C1 table — no flip possible by construction. The clean-null table
(0.01200 / 0.01025 / 0.00560) is now the live registered table in
`bench_recover_leg.py`, whose startup cross-check re-derives it from the
round-3 record plus the round-6 clean 8R5K null.

## H2/V2 — ATTRIBUTED, family-wide. HOLDS, precisely as predicted.

The discriminating experiment (iso-only derived model, all 2 511 aniso
tensors zeroed, coordinates/occupancies/B_iso untouched):

| model | phenix mvd | gemmi path | Servalcat | REFMAC |
|---|---|---|---|---|
| deposited (aniso) | 0.1043 | 0.1059 | 0.1473 | 0.1712 |
| iso-only derived | 0.1553 | 0.1569 | **0.1473** | **0.1710** |

The two R paths rise **+0.051** — the physical signature of losing the
anisotropic ADP model at 0.82 Å. **Neither Murshudov-family tool moves at
all**: both compute F_calc from isotropic-equivalent ADPs and never applied
the deposited aniso tensors. V2's registered pattern (two paths ≥ +0.03,
REFMAC < 0.01) is hit exactly.

- **The closing invocation exists for REFMAC**: default `BREF ISOT`
  collapses input aniso ADPs to isotropic equivalents even at NCYC 0;
  `REFI BREF ANIS` keeps them and moves REFMAC **0.1712 → 0.1371**. Per
  the registered outcome this is the protocol amendment for the
  third-opinion leg: aniso-model entries add `REFI BREF ANIS`. Only 2VXN
  was measured under it this round (one-change discipline); the rollout
  census across the other 21 entries is round-8 work.
- Candidate 2 (resolution) refuted: both tools cut at 0.82 Å.
- Candidate 3 (hydrogen) behaved exactly as its registered expected-null:
  `MAKE HYDR N` moves REFMAC +0.008 (riding H was *helping*), bounding the
  H term far below the +0.07 anomaly.
- **Disclosed post-registration extension**: the candidate Servalcat
  counterpart `--adp aniso` is a refinement parameterization, not an
  input-interpretation fix — at ncycle 0 it reinitializes the ADP model
  (R-free 0.4068). No closing invocation exists for Servalcat; its
  attribution rests on the exp-1 invariance (0.1473 on both models).
- The residual after the amendment (0.1371 vs 0.1043) is consistent with
  the round-6 solvent component (~0.02) plus remaining family conventions;
  it is a named residual, not a resolved one.

Three rounds of "REFMAC disagrees in sign on 2VXN" (#355) reduce to: the
gold standard's aniso ADP model — the very thing that makes a 0.82 Å
structure gold — was invisible to the third-opinion tools.

## H3/V3 — FALSIFIED: the registered repair's premise was wrong.

The registered rename (aniso `label_comp_id` CYS → CSO on the CSO atoms'
rows) matches **zero rows**: 9YGW's deposited anisotrop block is
**internally consistent**. Verified per atom id: residue 109 in both chains
is compositional microheterogeneity modeled as alternate conformers — CYS
at altloc A (aniso rows say CYS), CSO at altloc B (aniso rows say CSO).
REFMAC's `rdaniso_cif` mismatch therefore does not come from mislabeled
records; the plausible mechanism is a positional join in its reader that
collides the two comps sharing seq position 109. Per the registration the
repair is not iterated: the no-op derivation and the unchanged failure are
recorded, and 9YGW stays **named-unmeasurable**. The measurability census
lands on the registered fallback branch: **21/22**.

## H4/V4 — FALSIFIED: byte-reproducible refetch is impossible for 11 of 12.

The proof gate produced a finding rather than a remediation. On 11 of 12
entries the staged re-fetch differs from the store on exactly one column —
`R-free-flags` — and on 7R2H every one of the 1 016 differing positions is
a reflection with **no measured amplitude** (FOBS = NaN; free/work totals
identical at 508/508). The converter **generates random free flags for
unmeasured reflections on every fetch**, so the per-column fingerprint can
never match across fetches for entries with incomplete observations.
Measured-data identity holds everywhere it was tested; the registered
instrument is stricter than measurement-relevant identity, and per the
registered gate all 11 stores were left untouched (wavelength still 0.0,
staged wavelengths recorded per entry: 0.65–1.0).

**8R5K alone passed the full proof** (fingerprints identical, staged
wavelength 0.85). Its store write did NOT happen: the session's permission
layer ruled that the merged registration is not, by itself, the user
naming this specific sidecar rewrite — so the driver was restructured to a
proof-only default, and the single write awaits the user's explicit
go-ahead. Round-8 alternative for the other 11: an in-place wavelength
patch of the existing store files (observation bytes untouched, no flag
exposure), which needs its own registered ruling.

## Also found and fixed this round

- The Servalcat R-free parse in both round drivers took the last loose
  `R…free` match, which lands on a stats-table row and reads 0 — fixed to
  the explicit `Rfree =` form (the committed round-6 figure was obtained
  manually and is unaffected).
- The exp-2 log audit initially read round-6 log paths; fixed to this
  round's own logs before the verdict was taken.

## Round-8 inheritance

1. **`REFI BREF ANIS` rollout census** across the 21 other entries (the
   amendment is registered; its blast radius is not yet measured).
2. The 11-entry **wavelength patch ruling** (in-place metadata edit).
3. 9YGW: whether a REFMAC-side aniso positional-join workaround exists
   that is not a model edit (or 9YGW stays two-path permanently).
4. The 8R5K store write, if and when the user gives the explicit go-ahead.
