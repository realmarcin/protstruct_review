# Negative-control round 3 — pre-registration (the bench)

Registered **before any bench measurement**. Round 2 enrolled the set
(`negative_control_round2_enrolled.json`, 22 entries); this round registers
plan **phase 3** — the negative-control bench proper: refinement subjects start
from enrolled gold standards and their changes are judged for degradation by
multi-metric, cross-tool agreement with the protected-outlier inversion. All
round-2 machinery (masks, array selection, run manifests, input hashes,
hash-verified caches, atomic canonical writes) carries over unchanged. Live
canaries quoted below were run 2026-08-13.

## B1 — subjects

Two registered subjects, both over the enrolled 22:

- **S-null** — the round-2 null protocol (`r2n_` records). NOT re-run: its
  measurements are REUSED from the committed round-2 screen. Role: the bench's
  false-positive probe — a correct detector must not call the null degraded.
- **S-SA** — `phenix.refine` with Cartesian simulated annealing
  (`simulated_annealing=True`, 3 macro cycles, registered array selection,
  output prefix `r3sa_`). Role: an aggressive protocol expected to move a
  gold-standard start detectably — the detector's positive probe. Same
  fetch/mask/selection pipeline; execution begins with the standing one-entry
  canary.

  **Disclosed S-SA canary (4M7G, 2026-08-13):** the registered invocation ran
  end to end in 24 min wall clock (confirming the ~8–16 h batch estimate) and
  moved the in-run R-free from 0.1213 to 0.1410 — **+0.020**, more than twice
  the +3·S_r2 line. In-run figures only (the bench measures re-derived,
  two-path values); as with every disclosed figure, the registered content is
  the subject definition, not this number.

## B2 — metric families and oracles (per entry, post vs deposited start)

1. **Data fit**: ΔR-free by the two registered paths (`phenix.model_vs_data`;
   gemmi sfcalc + `gemmi_rfactor`), plus **REFMAC5 `NCYC 0`** as a third,
   fully non-cctbx opinion. REFMAC input rule, canaried: the DEPOSITED model
   goes in as mmCIF (9YGW's deposited PDB trips REFMAC's residue-numbering
   check; the mmCIF does not), the refined model as the phenix PDB output
   (canaried on `r2n_4m7g_001.pdb`). Disclosed canary figures (4M7G): REFMAC
   free R 0.1738 deposited → 0.1783 null-refined; Δ = +0.0045 vs the two-path
   +0.0083/+0.0090 — same sign, different magnitude (different scaling
   models), which is why REFMAC registers as a **direction-agreement**
   confirmation, never a magnitude match.
2. **Geometry**: Δclashscore, ΔRamachandran-favored %, Δrotamer-outlier % via
   the bench cctbx trio (`phenix.clashscore`/`ramalyze`/`rotalyze`, the
   `bench_refinement_deltas` measure), with REFMAC's rmsBOND/zBOND deltas as
   the non-cctbx geometry confirmation (same `NCYC 0` runs as family 1).
3. **Protected-outlier inversion**: per-residue `ramalyze`/`rotalyze` verdicts
   on the mask's PROTECTED residues, deposited vs post. A protected outlier
   that stops being an outlier is a FIX — counted against the subject
   (the plan's inversion, now operational).
4. **Distance-to-start**: raw Cα shift over matched pairs, NO superposition
   (§4 convention), computed over UNMASKED residues only — masked-region
   movement is not evidence about the subject (#321's spirit applied where it
   is cheap and unambiguous).

## B3 — the registered verdict rule

Per entry and subject, four family flags:

- **F-data**: ΔR-free > +3·S_r2 on BOTH registered paths, where S_r2 are the
  round-2 measured noise scales (phenix 0.00275, gemmi 0.00260 — provenance:
  `negative_control_round2_screen.json`). REFMAC sign disagreement with an
  otherwise-flagged pair is recorded as a named cross-tool conflict and the
  flag stands DOWN (trust model: two families of evidence must agree).
- **F-geom**: the §4 registry geometry clause for the d_min < 2.5 Å branch
  (clashscore ratio ≥ 5×, or favored − 0.5 pp, or rotamer + 4 pp —
  `[benchmark]`-backed rows, cited not restated), via the cctbx trio, with
  REFMAC zBOND not improving as confirmation; cctbx-only worsening with REFMAC
  disagreement is recorded, flag down.
- **F-protected**: ≥ 1 protected-outlier fix (family 3).
- **F-shift**: unmasked Cα shift > 0.12 Å (§4 ΔRMSD band, d_min < 2.5 Å
  branch, `[benchmark]`).

**Verdict: DEGRADED iff ≥ 2 families flag.** Single-family flags are named,
not verdicts. Every flag carries its numbers in the committed record.

## B4 — predictions

**Q1 — the bench does not call the null degraded.** S-null DEGRADED verdicts
≤ 2 of 22. *Falsified* otherwise — a detector that flags its own null is
measuring itself.

**Q2 — SA moves gold standards detectably.** S-SA DEGRADED verdicts ≥ 12 of
22 screened.

**Q3 — the inversion has real targets.** ≥ 1 S-SA entry fixes ≥ 1 protected
outlier.

**Q4 — REFMAC direction agrees.** REFMAC ΔR-free sign matches the two-path
sign on ≥ 90 % of S-SA rows where both are measurable.

## B5 — outputs and scope

- `negative_control_round3_bench.json` (canonical; run manifest, input hashes,
  per-family numbers per row) + `negative_control_round3.md`, reconciled by
  the series guard.
- Runtime: 22 SA refinements (~8–16 h) + REFMAC passes (~1 min each); S-null
  costs nothing (reused).
- **Enrollment is NOT reopened**: the ligand-restraint (18 defects) and
  French-Wilson (11) candidates from round 2 stay parked for a future
  enrollment round; the #321 D6 criterion is enrollment machinery and stays
  blocked-by-design. This round benches the 22 that exist.

## What this round does not do

- No agent artifacts as subjects yet — two registered protocol subjects only;
  agent runs become subjects in a later round once the bench's Q1/Q2 behavior
  is on record.
- No threshold tuning after data; §4 and S_r2 values are fixed by citation.
- No perturb-then-recover leg (plan phase 4) — that is round 4, paired with
  this bench so do-nothing subjects cannot win either round alone.
