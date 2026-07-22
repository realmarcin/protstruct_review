# Domain-expert review — cross-tool `[template]` agreement tolerances

A crystallographer / structural-biology methods review of the `[template]`-tagged agreement
tolerances in `ref/thresholds_and_standards.md`. These are **inter-program agreement tolerances** —
how close two independent tools must land on the same input for the harness to treat a measurement
as corroborated — not absolute quality bars. The tolerance should approximate the tool/method noise
floor for that quantity.

Produced by a fan-out deep-research pass (21 primary sources → 89 extracted claims → 25 verified by
3-vote adversarial verification → 22 confirmed, 3 refuted). This file is the audit trail; the
actionable edits it motivated are applied to `ref/thresholds_and_standards.md` and noted below.

## Headline verdict

The metric **definitions** the harness compares are sound (clashscore = serious overlaps ≥ 0.4 Å per
1000 atoms; the 98%-favored / 0.5%-outlier Ramachandran calibration; model-map FSC = 0.5 and
half-map FSC = 0.143; CC\* = √(2·CC½/(1+CC½))), so tolerances built on them measure the right
quantities. Two thresholds are wrong as set; the rest of the *assessed* set is defensible; and ten
tolerances were left unassessed for lack of direct evidence (a follow-up pass covers them).

## Applied fixes (see `ref/thresholds_and_standards.md`)

### 1. Bond-angle RMSD ±0.1° — DEFECT, made library-conditional (verified 3-0)

Restraint-library choice **alone** shifts bond-angle RMSD by **0.3–0.4°** — 3–4× the tolerance — and
resolution-independently. PHENIX has defaulted to the conformation-dependent library (CDL) since
~2016; gemmi draws bond/angle targets from the CCP4 monomer library (Engh & Huber lineage, shared
with Refmac). A PHENIX-vs-gemmi pairing therefore breaks ±0.1° for library reasons, not real
disagreement (one benchmark measured a ~0.64° PHENIX-vs-REFMAC angle gap on identical data).
**Fix applied:** require matched restraint libraries before comparing bond-angle RMSD; when libraries
differ, widen the tolerance to ~**±0.4°**.
*Sources: Moriarty, Tronrud, Adams & Karplus 2016 (Acta Cryst. D72:176–186); Tronrud & Karplus 2011;
Touw & Vriend 2010 (Acta Cryst. D66); gemmi documentation; Wojdyr et al. 2023 (Acta Cryst. D).*

### 2. CC½ high-resolution floor — citation corrected + loosened (verified 3-0)

Two problems. (i) **Misattribution**: the CC½ 0.1–0.2 cutoff material is in **Diederichs & Karplus
2013** ("Better models by discarding data?", Acta Cryst. D69:1215–1222), *not* the "Karplus &
Diederichs 2012" the registry cited. (ii) The **0.3 floor is more conservative than the source's own
0.1–0.2 recommendation**, and it ignores that statistical significance is sample-size-dependent
(CC > 0.3 significant only for n > 100; CC > 0.08 significant for n > 1000).
**Fix applied:** correct the citation to the 2013 companion paper and state the floor as **CC½ ≈
0.1–0.2** (with the note that significance is n-dependent), rather than a fixed 0.3.
*Sources: Karplus & Diederichs 2012 (Science 336:1030–1033) for CC½/CC\*; Diederichs & Karplus 2013
(Acta Cryst. D69:1215–1222) for the 0.1–0.2 cutoff and sample-size significance.*

## Confirmed sound (kept, with a noted precondition where relevant)

- **Bond-length RMSD ±0.003 Å** — defensible; bond lengths are nearly library-insensitive (unlike
  angles). Caveat: possibly slightly tight at atomic resolution, where CDL sigmas differ. (Moriarty
  2016; Moriarty et al. 2014, FEBS J.)
- **Clashscore ±1.0** — well grounded (Chen et al. 2010, Acta Cryst. D66:12–21; Williams et al. 2018,
  Protein Science 27:293–315). The absorbed ~0.5 hydrogen-build shift is mechanistically correct
  (Reduce places H at electron-cloud-center for X-ray vs nuclear positions; a ~0.1–0.16 Å per-H shift
  changes clash counts). **Recommended precondition** (added as a note): match the H-build convention
  between the two tools rather than absorbing it as a fudge.
- **Ramachandran / rotamer favored % (±1.0 pp) and outlier % (±0.5 pp)** — the safest fixed numbers;
  the 98%-favored / 0.5%-outlier calibration is correctly stated (Williams et al. 2018). Note: these
  measure inter-tool *agreement*, not convergence to an absolute MolProbity bar.
- **FSC 0.5 / 0.143** — correctly stated and applied (Rosenthal & Henderson 2003, J. Mol. Biol.
  333:721–745; Scheres & Chen 2012, Nat. Methods). Preserve the nuance: half-map FSC = 0.143 ↔
  model/reference-map FSC = 0.5; and `d_FSC_model` is "true resolution" only when the reference model
  is *independent* of the map (a model refined against the same map inherits an overfitting caveat).

## Refuted rationales (do not rely on these, even where the number stands)

Three claims were killed in verification:
- The "absolute MolProbity bar" framing of the pp tolerances (0-3) — they measure agreement, not
  convergence to a fixed MolProbity percentage.
- A >20–30% library-driven **bond-length** shift (1-2) — bond lengths are near-library-insensitive;
  the tight ±0.003 Å tolerance stands *because* of this, not despite it.
- One specific Rosenthal quote grounding the 0.143↔0.5 pairing (0-3) — the pairing still holds via
  Scheres & Chen 2012, but not via that quote.

## Coverage gap — ten tolerances left unassessed here

No direct primary-source evidence was found in this pass for: CA RMSD between superposition tools;
aligned-residue count; Wilson B agreement; L-test ⟨|L|⟩; secondary-structure H/E/C agreement; DockQ;
interface BSA vs PISA; NMR ensemble RMSF; the gemmi-vs-PHENIX R offset; and RSCC/EDSTATS. These are
**unassessed, not endorsed.** One extraction-phase lead worth chasing: Tickle 2012 (Acta Cryst.
D68:454–467) reports RSR/RSCC varying by **>0.1** for an identical residue purely from map
limiting-radius conventions, which would make a fixed ±0.05 RSCC agreement tolerance too tight. A
follow-up research pass covers all ten; its findings will be appended here.

## Time-sensitivity

PHENIX has defaulted to CDL since ~2016 and gemmi now feeds Refmac5 restraints (2023), so the
library-provenance split behind the bond-angle finding is current as of 2026 — but exact default
dictionaries change with tool versions. **The harness should record restraint-library and tool
versions alongside geometry measurements**, so a geometry disagreement can be attributed to a real
difference rather than a library mismatch.
