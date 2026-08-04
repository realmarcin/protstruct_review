# protstruct_review

Quality-assessment harness for agentically refined or generated protein structures.

Every task is graded by **cross-tool agreement** — never by PHENIX grading PHENIX. Critical metrics are re-run with at least one independent oracle (MolProbity, ChimeraX, REFMAC/Servalcat, TM-align, gemmi, …); the deposited PDB/EMDB entry or publication Table 1 is the tiebreaker.

See `/protstruct-eval` for the catalog conventions, driving-example format, oracle pairings, and per-tool assumptions.

`prompts/backlog-loop-goal.md` is this repo's change cycle — survey, triage, branch, work, PR, adversarial review, file issues, address, merge on approval, clean up. It is a prompt **fed to the native `/goal`**, not a custom command wrapping it. Run it as `/goal prompts/backlog-loop-goal.md`.

`bash scripts/validate.sh` is the gate. There is no CI, so it must pass before any merge.
