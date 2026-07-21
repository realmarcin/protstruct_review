# Driving example — T01 Structure superposition + RMSD

Standalone per-task driver for **T01 (structure superposition + RMSD)**. Follows the structure of
`ref/driving_example.md`. Graded by **cross-tool agreement**: the same superposition computed by
PHENIX and by an independent aligner must agree, because RMSD depends on the alignment and there is
no single "true" number — only tools that concur.

Provenance tags: `[catalog]` = the gold-standard tolerance stated in `ref/catalog.yaml` for T01;
`[template]` = a check reused from `ref/driving_example.md`; `[literature]` = an established
community threshold (cited inline); `[calibration]` = a sanity check against a known case.

## Scenario

The agent is handed two models — a **fixed** reference and a **moving** candidate — and asked to
superpose them and report CA RMSD, all-atom RMSD, number of aligned residues, and (for
fold-level comparison) TM-score. The harness independently re-superposes with a non-PHENIX aligner
and checks agreement.

## Dataset — concrete IDs

- **Primary:** PDB `1UBQ` (fixed) vs `1UBI` (moving) — two ubiquitin structures, same fold, small
  and fast. Expected CA RMSD is sub-Ångström, so the tools should agree tightly.
- **Fold-level stress:** a deposited structure vs its AlphaFold model (e.g. PDB `2LYZ` vs
  `AF-P00698-F1`), where TM-score rather than RMSD is the meaningful agreement metric.

## What the agent must do

1. Run `phenix.superpose_models fixed=1ubq.pdb moving=1ubi.pdb output=moving_sup.pdb`.
2. Record CA RMSD, all-atom RMSD, number of aligned residues.
3. For the fold-level case, also compute TM-score (via the oracle below — PHENIX does not report it).
4. Expected artefacts: `moving_sup.pdb`, `superpose_models.log`.

## Independent cross-checks (harness, not agent)

- **TM-align** (installed; see `ref/oracle_tools.md`) — sequence-independent superposition, reports
  RMSD, number of aligned residues, and TM-score normalised by both lengths.
- **`gemmi align`** / **ChimeraX `matchmaker`** — independent CA RMSD on the same selection.

## Scoring rubric

Each bullet is pass/fail; all must pass for green.

1. **Cross-tool CA RMSD agreement.** PHENIX `superpose_models` CA RMSD vs TM-align (or ChimeraX
   `matchmaker`) CA RMSD on the same aligned atoms: **|Δ| ≤ 0.10 Å**. `[catalog gold_standard]`
   `[template check 3]`
2. **Aligned-residue-count agreement.** The number of aligned residues from the two tools agrees
   within **±2 residues** (larger divergence means the tools aligned different cores, so the RMSDs
   are not comparable and the ≤0.10 Å check above is meaningless). `[template — comparability guard]`
3. **TM-score fold call.** For the fold-level case, TM-score **> 0.5** confirms the two models share
   the same fold; **< 0.17** would indicate unrelated structures. (Xu & Zhang, *Bioinformatics*
   2010 — TM-score > 0.5 ≈ same fold, < 0.17 ≈ random.) `[literature]`
4. **Selection disclosed.** The atom/chain/residue selection used for the superposition must be
   recorded. RMSD without its selection is uninterpretable; absence is a fail. `[template — the
   selection is part of the measurement]`
5. **Calibration on identity.** Superposing `1UBQ` onto itself gives CA RMSD = 0.00 Å and aligned
   residues = full length. A non-zero self-RMSD exposes a pipeline bug. `[calibration — identity]`

## Notes

- RMSD is meaningless without its alignment; every reported RMSD must travel with the selection and
  the aligner that produced it. This is why T01 grades agreement between two aligners rather than a
  single absolute number.
- TM-score, unlike RMSD, is length-normalised and comparison-robust, which is why it — not RMSD — is
  the pass criterion for the predicted-vs-experimental fold-level case.
