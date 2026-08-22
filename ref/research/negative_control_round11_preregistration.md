# Negative-control round 11 — pre-registration (the 2VXN echo)

Registered **before any round-11 measurement**. Round 10's Y2 falsification
put 2VXN's W4 contradiction back on the board — the same entry, the same
shape as round 5, now *under* the ANIS convention that fixed its
deposited-model conflict. This round names the mechanism from committed
data, decomposes what remains of it, and registers the amendment that
would dissolve it — or stands 2VXN's third opinion down for candidate
legs. Committed rounds are history.

## L0 — the disclosed mechanism: the conflict is an echo of the pre

From the committed rounds-9/10 records alone (no new measurement):

| | phenix | gemmi | REFMAC (ANIS) |
|---|---|---|---|
| deposited pre | 0.1043 | 0.1059 | 0.1371 |
| `osol_h` post (pre + Δ) | 0.1264 | 0.1270 | 0.1276 |

**The posts agree within 0.0012; the pres differ by 0.0328.** All three
tools measure the round-10 candidate — a phenix-refined model carrying
explicit H, added waters, and aniso ADPs — essentially identically. The
sign conflict (+0.0221/+0.0211 vs −0.0095) is pure arithmetic: REFMAC's
delta subtracts a high pre, the paths subtract a low one. And the round-5
comparison dates the fix: under ISOT the *posts* still spread 0.0258, so
the round-9 adoption made the candidate side consensual; what remains is
the deposited-baseline gap round 7 left as a named residual.

The candidate-quality question W4 exists to protect is therefore not in
dispute on this entry — the dispute is inherited entirely from the
baseline object.

## L1 — decompose the remaining pre-gap (0.0328, ANIS)

The named candidate terms, one change at a time, all NCYC-0 / zero-cycle
on the deposited model:

1. **REFMAC's automatic riding H on the H-less pre** (the paths add none):
   `REFI BREF ANIS` + `MAKE HYDR N`. Round 7 measured this term at +0.0083
   under ISOT.
2. **The solvent model**: `REFI BREF ANIS` + `SOLVENT NO`. Round 6
   measured −0.0201 under ISOT.
3. **The converse H term on the paths' side**: both R paths measured on an
   H-augmented deposited model (`phenix.ready_set`, zero refinement,
   recorded as a derived input with its own hash; the deposited file is
   untouched).

## L2 — the registered amendment, two-sided

**If** the decomposition attributes the pre-gap to named baseline
conventions (Z2), the following is adopted from this round's execution
merge:

> **Post-agreement rule for named-conflict entries.** For an entry whose
> deposited baseline carries a registered cross-family conflict (today:
> 2VXN), the third opinion contributes to candidate verdicts through
> **post-level agreement** — |REFMAC post − mean two-path post| ≤
> `d_refmac_anis` (0.01150) counts as corroboration; beyond it is a named
> conflict — instead of through its within-family delta sign. Deltas
> anchored to a known-conflicted pre are incommensurable across families;
> the candidate itself is measured consensually, and the rule grades what
> the tools actually agree on. W4 keeps its role unchanged against the
> two-path evidence.

**Else** (the gap does not decompose into named terms), 2VXN's third
opinion **stands down for candidate legs** as it already has for the
entry's aniso-reader pathologies' neighbors — the round-8 stand-down
logic extended, no third outcome.

Either way, committed rounds 5 and 10 are not re-judged; L3 discloses
what the amendment would have said.

## L3 — disclosure sweep

Recompute the committed round-5 (`osol`) and round-10 (`osol_h`) 2VXN
rows under the post-agreement rule and disclose the outcomes (prediction
Z3), alongside the same sweep for every other entry's candidate rows —
the rule must be shown to change nothing anywhere the families already
agreed.

## Predictions

**Z1** — the two H terms have the registered signs and magnitudes:
`MAKE HYDR N` raises REFMAC's ANIS pre by +0.004…+0.012 (the ISOT term
was +0.0083), and ready_set H lowers each R path's deposited pre by
0.008…0.035 at 0.82 Å.

**Z2** — the riding-H and solvent terms together account for **≥ 75 %**
of the 0.0328 ANIS pre-gap (|H term| + |solvent term| ≥ 0.0246), leaving
a residual attributable to scaling conventions below 0.008.

**Z3** — under the post-agreement rule, both committed 2VXN candidate
contradictions dissolve (posts within 0.01150 of the two-path mean), and
**zero** non-2VXN rows change their third-opinion contribution in the L3
sweep.

## Outputs and scope

`negative_control_round11.md` + `negative_control_round11_echo.json`
(L1 terms, the decomposition arithmetic, the L3 sweep), swept against the
record. Code: `bench_round11.py` (SET_RECORD-gated, sandboxed per the
NC-10 protocol), the post-agreement rule behind an explicit
named-conflict-entry list (today exactly `{2VXN}`), tests. NOT in scope:
re-judging committed rounds; new subjects; store writes; #292/#293.
