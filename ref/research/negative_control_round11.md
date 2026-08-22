# Negative-control round 11 — the echo attributed; the amendment refuses itself

**Run 2026-08-22** per `negative_control_round11_preregistration.md`. Record:
`negative_control_round11_echo.json`. Score: **Z1 HOLDS, Z2 HOLDS by its
registered letter (with the signed accounting disclosed), Z3 is
FALSIFIED** — and the falsification is the round's finding: the
post-agreement rule fails its own registered safety sweep, so the
amendment is **refused** and the else-branch **stand-down is enacted**.

## L1/Z1/Z2 — the pre-gap decomposes, almost exactly. HOLD.

One change at a time on the deposited model (sandboxed, NCYC-0/zero-cycle):

| term | value | registered bar |
|---|---|---|
| REFMAC riding-H (`MAKE HYDR N`, ANIS) | **+0.0111** | +0.004…+0.012 ✓ |
| REFMAC solvent (`SOLVENT NO`, ANIS) | **−0.0410** | (measured) |
| paths on the ready_set-H model (2 123 H) | **−0.0110 / −0.0119** | −0.008…−0.035 ✓ |

Z2's registered accounting (|H| + |solvent| = 0.0521 ≥ 0.0246) holds, but
the honest arithmetic is the **signed** decomposition, and it closes to
three thousandths:

    pre_gap  =  solvent penalty − riding-H benefit + residual
    0.0328   =  0.0410          − 0.0111           + 0.0029

REFMAC's elevated 2VXN baseline is its bulk-solvent model (a −0.041 term
under ANIS — larger than the ISOT-era −0.020, and larger than the whole
gap) partly masked by its automatic riding hydrogens. The registered
|·|-sum formulation overshoots the gap (residual −0.0193 as registered);
both accountings are recorded, neither retro-fitted.

## L3/Z3 — FALSIFIED: the rule flips 54 of 78 rows, not 2.

The registered safety requirement — the rule must change nothing where
the families already agreed — fails in two distinct ways:

- **All 47 ISOT-era flips are category errors**: posts from rounds 4–5
  carry the set-wide aniso tax on REFMAC's side (median post-gap 0.0282,
  max 0.0566 — the round-8 census, re-expressed), so post-level
  comparison across that era is invalid by construction. The registration
  swept those rows and demanded zero change without era-scoping; the
  demand was right and the rule failed it.
- **The ANIS era is subtler**: 2VXN dissolves exactly as predicted
  (post-gap 0.0009 vs the delta-sign conflict), and five other entries
  (6ZWY, 5XS6, 7TVL, 7OYN, 9TXE; post-gaps 0.0004–0.0027) show the same
  shape — their delta-sign "disagreements" are noise-scale sign flips the
  posts reveal as agreement. But **6XVM flips the other way** (post-gap
  0.0166 > the tolerance): a real level difference the rule would turn
  from agreement into conflict.

Per the registration there is no third outcome: the decomposition
attributed the gap, but the amendment's own safety clause failed, so the
adoption branch is closed and the else branch applies —

**2VXN's third opinion stands down for candidate legs** (the 9YGW
round-8 move, new entry, new named cause: pre-anchored deltas are
incommensurable across families on this entry, and the level-agreement
substitute is not a usable instrument at the registered tolerance).
`CANDIDATE_LEG_THIRD_OPINION_STANDDOWN = {"2VXN"}` ships in
`bench_recover_leg.py`, pinned by test; future candidate rows for 2VXN
are two-path and say so. Committed rounds are untouched.

## What the falsification bought

The sweep was the first cross-era, cross-entry measurement of post-level
family agreement, and it shows: (a) the phenomenon that motivated the
rule — consensual candidate measurement — is real but **per-entry**, not
set-wide (the solvent term varies by entry; 6XVM's posts genuinely
differ); and (b) five ANIS-era delta-sign conflicts in committed records
are noise-scale artifacts the posts resolve. A future round could
register an era-scoped, per-entry-calibrated form of the rule; this
round's registered form is dead, honestly.

## Round-12 inheritance

1. The five noise-scale delta-sign conflicts (6ZWY, 5XS6, 7TVL, 7OYN,
   9TXE) — candidates for a registered near-zero-delta sign-agreement
   guard (a sign is not evidence when |Δ| is inside the null noise).
2. 6XVM's ANIS-era post-level gap (0.0166) — unexplained, now named.
3. #292/#293 (tolerance P4), the publication track (#397/#399/#402/#410).
