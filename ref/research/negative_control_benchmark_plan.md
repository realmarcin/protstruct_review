# Plan: gold-standard negative-control benchmark for refinement methods

**Status: plan — nothing below has been measured.** This document records the design and
its evidence base so the phases can be preregistered and executed in later rounds.
Tracking issue: [#295](https://github.com/realmarcin/protstruct_review/issues/295)
(phase checklist and dependencies).

## The idea

Use structures with the highest known resolution and best validation features as
**negative tests** for refinement methods: start a method from a near-perfect,
already-at-optimum structure, and treat the changes it introduces as candidate
degradations. Degradation is easier to observe from a pristine start than improvement is
to judge from a poor one.

The known confound, flagged at conception: even "perfect" crystal structures are families
of static solutions — alternate conformers, lattice-contact conformations, genuine
density-supported geometry outliers — so a change is not automatically an error. The
design below makes that confound mechanical (residue-level masks + a protected-outlier
inversion) rather than interpretive.

## What this extends (not greenfield)

| Existing piece | What it already does | What this plan adds |
|---|---|---|
| `scripts/bench_refinement_deltas.py` | The §4 null case: re-refine a deposited model against its own data; measure the drift floor | Curated near-perfect set instead of resolution-windowed entries; verdict protocol instead of Δ-band calibration |
| `scripts/select_xray_entries.py` | Query-pinned RCSB selection on the scalar `diffrn_resolution_high.value` (the multi-valued `resolution_combined` trap is documented there, #238) | Gold-standard criteria: percentile cuts, structure-factor requirement, redundancy clustering, committed set |
| `scripts/bench_vs_deposited.py` | Fetches + parses wwPDB validation XML: per-residue `rama=`/`rota=` verdicts, DCC R-free, clashscore, RSRZ | Reused for percentile harvesting (phase 0) and mask sources (phase 1) |
| `ref/thresholds_and_standards.md` §4 | Refinement Δ-tolerances from the null case | New section: negative-control verdict rules |

## Evidence base (deep-research run, 2026-08-07)

Claims below survived 3-vote adversarial verification against primary sources; two
load-bearing *refutations* are listed too, because the design depends on them.

**The premise has direct prior art.**

- CASP formalized the untouched start as the baseline ("naïve predictor"). CASP13: 25 of
  32 refinement groups scored below it; 24 of 32 degraded more models than they improved
  (Read et al., Proteins 2019, [PMC6851427](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6851427/)).
  CASP14: only 4 groups beat it; near-perfect AF2-derived starts were "anomalous in their
  near-unrefinability", and start quality correlated negatively with refinability
  (Simpkin et al., Proteins 2021, [doi:10.1002/prot.26185](https://onlinelibrary.wiley.com/doi/full/10.1002/prot.26185)).
  CASP dropped the refinement category after CASP14.
- PDB_REDO rejects a re-refined model wholesale when R-free worsens vs the rigid-body
  baseline — operational degradation detection against a fixed start (Joosten et al. 2009,
  [PMC3246819](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3246819/)).
- Afonine et al. 2018 refined an exact reference model against maps computed from itself:
  drift 0.01 Å rmsd at 1 Å resolution → 0.48 Å at 6 Å; plus a perturb-then-refine
  benchmark (phenix.dynamics to prescribed rmsd, score recovery to reference)
  ([Acta Cryst D74:531](https://journals.iucr.org/d/issues/2018/06/00/ic5103/)). Caveat:
  PHENIX-evaluating-PHENIX — this harness swaps in independent oracles.

**Curation must be residue-level.**

- Top2018 (Williams, Richardson & Richardson, Protein Sci 2022,
  [doi:10.1002/pro.4239](https://onlinelibrary.wiley.com/doi/10.1002/pro.4239)): file/chain
  thresholds alone are insufficient — residue-level filters (B, density fit, altconfs,
  clashes) remove ~35–45% of residues even in passing structures. "Good average model
  quality … is nevertheless compatible with extremely bad model quality in locally
  disordered regions."

**The confound is real, in three documented forms.**

1. Altconfs: Top2018 excludes all alternate-conformation residues (24% of residue-level
   removals) rather than adjudicating them. Deposited models underrepresent
   heterogeneity: 2.9% of deposited residues multiconformer vs 40.7% after qFit
   rebuilding (Wankowicz et al., eLife 2024,
   [doi:10.7554/eLife.90606](https://elifesciences.org/articles/90606)).
2. Lattice contacts: CASP14 residual AF2 "errors" concentrated at crystal-lattice
   contacts; assessors: the reference "may simply reflect … non-natural conformations at
   these points."
3. Genuine outliers at functional sites: in a 0.72 Å structure, the fatty-acid-coordinating
   Arg126 guanidinium is a real, conserved geometric outlier at >8σ in MolProbity
   (Laulumaa & Kursula, Molecules 2019,
   [PMC6749445](https://pmc.ncbi.nlm.nih.gov/articles/PMC6749445/)). A method that
   "fixes" it improves its score while degrading the structure.

**Verdicts must be multi-metric and cross-tool.**

- On PDB_REDO's ~12,000-entry set, "improved" ranged 31–75% (re-refinement) / 45–86%
  (with rebuilding) depending on metric (Joosten et al. 2012,
  [PMC3322608](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3322608/)).
- Restraint-library circularity: MolProbity's Ramachandran/rotamer criteria derive from
  high-resolution subsets (Top500/Top8000), so gold standards score well partly by
  construction, and subatomic data show true structures deviate from library targets.
  Geometry-library scores alone cannot call degradation.

**Two refutations that shape the design.**

- "Re-refinement gains cleanly shrink at atomic resolution" — **refuted (1-2)**. Ultra-high-res
  does not imply zero legitimate headroom, so enrollment requires an empirical headroom
  screen (phase 2); it cannot be assumed from resolution + percentiles.
- "Validation algorithms cannot assess ultra-high-res structures" — **refuted (0-3)**. The
  true statement is weaker: they flag real features as outliers without being useless.
  Hence the protected-outlier inversion rather than discarding geometry metrics.

**Anti-gaming lesson.** CASP13's successful strategies restrained movement from the start
— refined models ended closer to the start than to the truth. A do-nothing method wins a
stay-near-start benchmark, so the negative leg must be paired with a
perturb-then-recover positive leg (phase 4).

## Design

### Phase 0 — feasibility scout (no PHENIX, API + gemmi only)

`scripts/select_gold_standards.py`, following the `select_xray_entries.py` pattern
(scalar resolution attribute, query-pinned, committed set):

- RCSB search: `diffrn_resolution_high.value` under candidate windows (< 0.9 / < 1.0 /
  < 1.2 Å), experimental data deposited.
- Harvest wwPDB validation percentiles per hit (reuse `bench_vs_deposited.py` fetch/parse).
- Redundancy clustering at 30% sequence identity (RCSB group API), best
  resolution+validation chain per cluster; report fold diversity.
- Deliverable: survivor counts per window × percentile cut. **Decision point:** pick the
  window from the counts. If sub-Å survivors are a handful of lysozyme-likes, widen to
  < 1.2 Å + top percentile rather than abandoning the design.

### Phase 1 — residue-level masks

`scripts/gold_mask.py`, emitting a committed per-entry mask file, one reason per residue:

1. **Altconf residues** (deposited PDB, gemmi) — masked, Top2018 precedent.
2. **Lattice-contact residues** (gemmi symmetry-mate contact search) — masked, CASP14
   precedent.
3. **Poor local density** (RSRZ outliers, high-B tail from validation XML) — masked.
4. **Protected genuine outliers** — residues that are MolProbity outliers *in the
   deposited gold standard* (per-residue verdicts from validation XML). NOT masked —
   inverted: a method that removes a protected outlier scores a degradation hit even
   though the geometry score improved. Protection is applied **after** masks 1–3: a
   deposited outlier that is also an RSRZ/high-B residue is masked, not protected, so
   every protected outlier is density-supported by construction.

Scoring happens on unmasked residues only. Mask fraction reported per entry (no silent
caps — a 40%-masked entry says so).

### Phase 2 — headroom screen, canaried

Because the atomic-resolution-headroom claim was refuted, every candidate is screened:

- Extend the `bench_refinement_deltas.py` refine→re-measure loop (which reads R from
  `phenix.refine` itself): `phenix.refine` against own deposited data, with R-free
  re-derived by `phenix.model_vs_data` AND a non-cctbx gemmi path. The latter needs
  promoting first — the only `gemmi_rfactor.py` today is an eval artifact under
  `data/coscientists/openscientist/`, not harness plumbing (#296).
- Enroll only entries where both code paths agree there is no headroom. The enrollment
  tolerance is set at phase-2 preregistration from the null-case spread on the
  candidates themselves — the same move rounds 7–42 used for the §4 bands — NOT
  borrowed from the ~0.01–0.015 cross-code-path scaling gap, which is a
  same-model/two-derivations quantity and is tracked separately as measurement
  uncertainty (#297). Entries with real headroom are PDB_REDO-improvable, not gold
  standards — dropped with recorded reason.
- 🐤 Canary: one entry end-to-end (fetch → mask → refine → both oracles → non-empty JSON
  on disk) before fanning out.

### Phase 3 — the negative-control bench

`scripts/bench_negative_control.py`: method under test (a `phenix.refine` protocol
config first; agent artifact directories later) starts from an enrolled gold standard.
Three metric families, each cross-tool:

| Family | Primary | Independent confirmation |
|---|---|---|
| Data fit | `phenix.model_vs_data` R-free/R-work | gemmi R-factor path (#296); DCC value from validation XML as tiebreaker |
| Geometry | standalone MolProbity (non-cctbx) | `phenix.holton_geometry_validation` (cctbx); shared Top8000 ancestry noted in `notes:` |
| Distance-to-start | raw Cα shift over matched pairs, no re-superposition (§4 convention) | TM-score + lDDT mandatory pair for any reported comparison |

Verdict rule: **degradation requires multi-metric, cross-tool agreement** — never one
tool, never geometry alone (the 31–86% metric-disagreement finding is the reason).
Protected-outlier "fixes" count as geometry degradation regardless of score direction.

### Phase 4 — paired positive control (anti-gaming)

Same entries, perturb-then-recover leg: `phenix.dynamics` to prescribed rmsd (start
0.5 Å, per Afonine et al.), method under test runs, recovery toward reference scored on
unmasked residues. A method must pass both legs: don't damage the pristine start, do
repair the perturbed one.

### Phase 5 — registry + docs

- Preregistration before measurement, in a **new series**
  (`ref/research/negative_control_round1_preregistration.md`) — this measures a
  different question than the Δ-tolerance rounds, so it should not share their
  numbering.
- Results doc + `[benchmark]` rows in a new `ref/thresholds_and_standards.md` section
  ("Negative-control verdicts, gold-standard start"): §4 answers "how much does a benign
  refinement move things"; this answers "when do we call a change degradation".
- Later, optional: a T03 driving-example variant (agent is *given* a gold standard —
  does it know when to stop?) and QDS metric definitions if verdicts should be
  emittable. Not needed for round 1.

## Sequencing and cost

Phases 0–1 are free (REST APIs + gemmi) and settle feasibility before any compute.
Phase 2 is the first PHENIX-consuming step and is canaried. Phases 3–4 reuse phase 2
plumbing. Stop-for-decision after phase 0's counts: the resolution window is a judgment
call to be made on data.

## Open questions carried from the research

1. Survivor count and diversity after full curation (phase 0 answers this).
2. Is masking sufficient, or are ensemble-aware references needed (qFit multiconformer,
   room-temperature datasets) so movement within the ensemble envelope is explicitly
   acceptable? Revisit after round 1.
3. Cryo-EM analogue: no EM entry reaches sub-Å X-ray validation quality. Options —
   resolution-matched top-percentile EM entries, or X-ray gold standards with simulated
   maps — distort differently. Out of scope for round 1; needs its own plan.
4. How independent are the "independent" geometry oracles, given shared Top8000 /
   Engh & Huber ancestry? Surface in `notes:` on every geometry verdict; the data-fit
   and distance families do not share this ancestry.
