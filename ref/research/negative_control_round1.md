# Negative-control round 1 — STOPPED at the registered finding

**Run 2026-08-10** per `negative_control_round1_preregistration.md`. The screen
attempted **71 entries** (30 initial representatives + 41 D4 replacements until
cluster exhaustion): **22 floor failures, 48 data defects, 1 fully screened**.
The pooled worsening side held 2 entries < 8, so the registered D6 fallback
**stopped the round without enrollment verdicts** — a tolerance invented after
seeing the data is exactly what #297 prohibits. Committed record:
`ref/research/data/negative_control_round1_screen.json` (every exclusion named
with its reason, per the no-silent-attrition rule).

Stopping IS the preregistration working: every finding below was purchased at
one batch's cost and lands in round 2's registration, not in mid-round
improvisation.

## Predictions readout

**P4 — FALSIFIED, decisively.** Predicted ≤ 3 of the 30 initial representatives
failing the ≥ 50-unmasked floor; observed **16 of 30**, and **13 of the 20
stratum representatives**. Eight entries have **zero** unmasked residues
(6UF8, 9MDB, 6EVH, 8GK1, 9C06, 6DIY, 5LHW, 9EG0). The cause is structural: the
≤ 0.9 Å stratum is dominated by tiny designed peptides and framework assemblies
(small crystals diffract best), where every residue is an altconf or a lattice
contact — and the D7 draw's best-resolution ordering amplifies exactly that
population. The floor and the stratum are in direct tension; phase 1's 12-entry
sample (drawn from the strict pool's full d_min range) did not show this because
it under-sampled the sub-0.9 extreme.

**P1–P3 — UNEVALUABLE.** One screened entry cannot exercise predictions about
enrollment rates, noise-scale agreement, or deposit-year skew. Recorded as
unevaluable, not as passes.

## The defect census (48 data defects)

| cause | n | nature |
|---|---:|---|
| "Multiple equally suitable arrays of observed xray data" | 40 | **pipeline, fixable**: converted sub-Å MTZs carry several observation arrays (F and I, multiple wavelengths); the registered protocol specified no selection rule, so `phenix.refine` refuses — correctly |
| fetch failed (HTTP errors, truncations) | 4 | transient/infra; one retry already registered |
| ligand needs restraint CIF | 2 | protocol gap: exotic-ligand entries need `phenix.ready_set`-style restraint generation, unregistered |
| no usable R-free flags | 1 | 1IQZ — the #242 mechanism, correctly named, correctly not worked around with generated flags |
| `phenix.refine` internal crash (occupancy_selections on partial-occupancy waters) | 1 | 6UWW — a PHENIX 2.0-5936 bug tripped by altconf-rich sub-Å entries |

40 of 48 defects are ONE underspecification — data-array selection — not 40 bad
entries. The registered protocol inherited `bench_refinement_deltas.py`'s
invocation, whose historical cache carried pre-normalized single-array MTZs; the
underspecification only became visible against fresh `phenix.fetch_pdb`
conversions.

## The one screened entry is the mechanism working

5SY4 (0.98 Å, 267 unmasked residues — a **D4 replacement**, not an initial
representative; not one of the 30 initial representatives survived to the
screen (#311), which sharpens the P4 finding):

| path | R-free pre | R-free post | Δ |
|---|---:|---:|---:|
| `phenix.model_vs_data` | 0.1457 | 0.1513 | **+0.0056** |
| gemmi (`sfcalc --scale-to` + `gemmi_rfactor`) | 0.1464 | 0.1520 | **+0.0056** |

Null re-refinement made a gold-standard structure measurably worse, and two
independent code paths measured the identical degradation to four decimals,
0.0007 apart in absolute value. n = 1 proves nothing statistically; as a
proof of mechanism it is exactly the benchmark premise — degradation from a
near-perfect start is visible and cross-tool confirmable.

## What round 2 must re-register

1. **Data-array selection rule** (fixes ~40/48 defects): deterministic
   observation-label choice for converted MTZs (amplitude array preferred,
   explicit `xray_data.labels`), registered as part of the protocol.
2. **The floor×stratum tension** (fixes 16/30 + 13/20): a protein-size criterion
   at SELECTION time (searchable polymer length), or a redefined stratum that
   excludes the designed-peptide population the floor will reject anyway.
3. **Ligand-restraint handling**: generate restraints or exclude
   restraint-needing entries at selection — registered either way.
4. Replacement-queue behavior confirmed sound: exhausted clusters were recorded,
   and the crash-safe row-by-row record survived a 71-entry batch.

The D6 formula itself was never reached at scale; nothing observed argues
against it. The 5SY4 pair suggests the two paths' Δ agreement will be tight,
which bodes well for P2 when round 2 gets a real sample.
