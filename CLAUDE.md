# protstruct_review

Quality-assessment harness for agentically refined or generated protein structures.

Every task is graded by **cross-tool agreement** — never by PHENIX grading PHENIX. Critical metrics are re-run with at least one independent oracle (MolProbity, ChimeraX, REFMAC/Servalcat, TM-align, gemmi, …); the deposited PDB/EMDB entry or publication Table 1 is the tiebreaker.

See `/protstruct-eval` for the catalog conventions, driving-example format, oracle pairings, and per-tool assumptions.
