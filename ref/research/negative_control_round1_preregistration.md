# Negative-control round 1 — pre-registration

Registered **before the headroom screen runs**. This is phase 2 of #295
(`negative_control_benchmark_plan.md`), and it settles the enrollment questions the
plan and phases 0–1 left open — honoring #297: the enrollment tolerance is set here,
by formula against data this round will measure, not borrowed from the cross-path
scaling gap. New measurement series: this is round 1; the benchmark legs
(plan phases 3–4) will be later rounds. Counts quoted below were measured live
2026-08-10 with the phase-0 query shapes.

## The registered decisions

**D1 — window (approved by the project owner on #295, 2026-08-08):** ≤ 1.0 Å,
enrollment as one representative per 30 %-identity cluster, ≤ 0.9 Å carried as a
stratum label.

**D2 — enrollment criteria relax the phase-0 strict tier's rama/rota cuts.** The
phase-1 finding: the strict tier (rama = 0, rota ≤ 0.3 %) starves the protection
mechanism — all 35 sample protections are clashes, because selecting for zero
outliers removes exactly the density-supported genuine-outlier carriers the plan's
confound section names (the Arg126 class). Registered criteria: **≤ 1.0 Å,
structure factors released, ≥ 1 protein entity, clashscore ≤ 2,
Ramachandran outliers ≤ 0.5 %, rotamer outliers ≤ 1.0 %, reported R-free ≤ 0.18.**
Measured pool: **425 entries, 145 clusters at 30 % (+28 unclustered entities)** —
171 entries readmitted relative to strict (254), most via the rotamer axis
(rama-only relaxation readmits 15; rota-only readmits 138). Per-outlier density
support is not asserted by the criteria — it is enforced residue-by-residue by the
phase-1 mask ordering (#298): an outlier that fails the RSRZ/B masks is masked,
not protected.

**D3 — unmasked-residue floor: ≥ 50.** A degradation verdict on a 17-residue
scoring universe (1EJG) is noise-dominated. On the phase-1 sample the floor keeps
9 of 12 entries; the three dropped (1EJG 17, 7A2Y 26, 5OAV 36) are exactly the
small-protein/high-lattice cases. Scouting provenance; the floor's sensitivity is
reported this round (D7-P4).

**D4 — representative rule per cluster:** best d_min, ties broken by lower
clashscore, then lower reported R-free, then lexicographic id (deterministic).
Representatives failing D3 or the D6 screen are replaced by the cluster's next
candidate, with the replacement recorded — a cluster is exhausted, never silently
skipped. Replacements are within-cluster and do not count against the D7 scope,
which is a **cluster** count.

**D5 — mask thresholds finalized for round 1:** |RSRZ| > 2 (wwPDB definition),
B tail factor 2.0×median owab, lattice cutoff 4.0 Å (symmetry images, non-water
partners), clash protection retained alongside rama/rota. ASU-internal interfaces
remain unmasked and are recorded as a known limitation — revisiting them is a
future round's registered change, not a mid-round adjustment.

**D6 — headroom screen and the enrollment tolerance formula.** Each representative
is null-re-refined against its own deposited data (the
`bench_refinement_deltas.py` protocol). ΔR-free = R-free(re-refined) −
R-free(deposited model), computed twice per entry with the same derivation on both
sides of each subtraction: once with `phenix.model_vs_data`, once with
`scripts/gemmi_rfactor.py` — the cross-path scaling gap (0.005–0.015) cancels
within each path and is never part of Δ. Noise scale per path:
**S = MAD of Δ over entries with Δ ≥ 0** (an at-optimum model's re-refinement can
only add noise or reveal headroom; the worsening side is pure noise, so it prices
the noise without contamination from real headroom). **Exclusion rule: an entry is
excluded when Δ < −3S on BOTH paths.** One-path-only exclusions are named and
retained, mirroring the cross-tool trust model. Registered fallback for a thin
estimator (#308): if a path's worsening side holds fewer than 8 entries, S for
both paths is the MAD of the POOLED worsening sides; if the pool is still under 8,
the round stops at a finding — a tolerance invented after seeing the data is
exactly what #297 prohibits.

**D7 — screen scope: 30 clusters.** The ≤ 0.9 Å stratum alone holds **50 clusters
(77 entities)** under the D2 criteria (measured live 2026-08-10), so "all stratum
representatives" does not fit a 30-screen scope (#308). Registered draw,
deterministic: **20 representatives spread evenly across the ≤ 0.9 Å stratum's
d_min-sorted cluster list** (an even spread, not the head — the #243 lesson) **+
10 from (0.9, 1.0] by ascending d_min**. At ~10 min of `phenix.refine` each this
is a ~5 h batch; canary first (one entry end-to-end, artifacts on disk and
non-empty, both R paths parsed) per the standing canary rule.

## Predictions

**P1 — most representatives enroll.** ≥ 80 % of screened representatives survive
D6. *Falsified* if more than 6 of 30 show cross-path-agreed headroom — which would
mean top-percentile validation does not imply at-optimum even at sub-Å, a finding
that would itself justify the screen's existence.

**P2 — the two noise scales are commensurate.** S_phenix and S_gemmi within a
factor of 3 of each other. A larger divergence means one path's Δ is dominated by
its own re-derivation noise rather than the refinement's effect, and the
two-path-agreement rule is doing less than it appears.

**P3 — exclusions skew old.** Entries excluded for headroom skew toward older
deposition years (older refinement software left more on the table — the
PDB_REDO mechanism). Recorded, not banded.

**P4 — the D3 floor is not load-bearing at enrollment scale.** ≤ 3 of 30
representatives fail the ≥ 50-unmasked floor once masks are built. If more fail,
the floor interacts with selection more than the phase-1 sample suggested and D3's
value is re-registered before any benchmark round uses it.

## Decision rule — registered before the screen

- Enrolled set = screened representatives surviving D3 + D6, committed as
  `ref/research/data/negative_control_round1_enrolled.json` (ids, cluster ids,
  stratum labels, per-entry Δ on both paths, mask summary). This is the set the
  benchmark legs run on.
- **If fewer than 15 entries enroll**, the round STOPS at a finding: the criteria
  are re-registered in a round-2 preregistration rather than loosened mid-round.
- Every screened-but-excluded entry is named in the round doc with its Δ pair and
  reason (headroom / floor / data defect), per the no-silent-attrition rule.

## What this round does not do

- **No benchmark verdicts.** Phases 3–4 (the negative-control bench and the
  perturb-then-recover leg) are later rounds; this round only enrolls.
- **No threshold tuning after data.** D2–D6 values are fixed by this document;
  anything learned that argues for different values becomes a re-registration.
- **No cryo-EM analogue.** Out of scope per the plan's open question 3.
- **No catalog/schema changes.** Enrollment artifacts live under `ref/research/`;
  QDS metric definitions come only if a benchmark round needs to emit them.
