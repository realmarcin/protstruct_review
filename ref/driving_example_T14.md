# Driving example — T14 Hydrogen placement / protonation

Standalone per-task driver for **T14 (hydrogen placement / protonation)**. Follows the structure of
`ref/driving_example.md`. Graded by **cross-tool agreement**: standalone Richardson-lab `reduce` must
corroborate the agent's `phenix.reduce` H-build, since PHENIX wraps the same lineage and the point is
to catch wrapping bugs.

> **Thresholds are defined once** in `ref/thresholds_and_standards.md`; the `[provenance]` tags below
> point into it.

## Scenario

The agent is handed a model without hydrogens (or partial H) and asked to add hydrogens, propose
Asn/Gln/His flips, and report the clashscore change and H-bond-network consistency.

## Dataset — concrete IDs

- **Primary:** PDB `1HQ1` (high-res, no deposited hydrogens).
- **Neutron comparator (where available):** PDB `5E5V` — neutron data locate H directly.

## What the agent must do

1. Add hydrogens with `phenix.reduce` (recording the build variant: `reduce -build` vs default).
2. Record H-atom count, Asn/Gln/His flips proposed, clashscore delta (pre vs post), H-bond-network
   consistency.
3. Expected artefacts: the H-added model + reduce log.

## Independent cross-checks (harness, not agent)

- **Standalone `reduce`** (Richardson lab) — same algorithm, different build. Running both exposes
  wrapping / default differences the PHENIX wrapper might introduce.
- **`propka3`** — independent pKa / protonation-state prediction for His/Asp/Glu.
- Neutron structure — direct experimental H positions, the tiebreaker when available.

## Scoring rubric

Each bullet is pass/fail; all must pass for green.

1. **H-count agreement.** PHENIX vs standalone `reduce` H-atom count agree within **± 2 %**.
   `[template — H-placement agreement]`
2. **Same flip set.** The Asn/Gln/His flips proposed by both builds match; a differing flip set is a
   wrapping/parameter difference to explain, not a silent pass. `[template]`
3. **Clashscore delta agreement.** The pre→post clashscore change agrees between builds within
   **± 1.0** — different H placements shift clashscore by ~0.5, so a larger gap signals a real build
   difference. `[template]`
4. **Build variant disclosed.** `reduce -build` (with flips) vs plain add-H must be stated — the two
   give different clashscores on the same model. `[handbook — MolProbity H-atom placement]`

## Notes

- PHENIX `phenix.reduce` wraps the Richardson `reduce`; exposing both is the whole point of T14 —
  identical outputs confirm the wrapper is faithful, divergence localises a wrapping bug.
