<task>
Review two GitHub pull requests in the structural-biology evaluation harness at
/Users/marcin/Documents/VIMSS/ontology/protstruct_review (GitHub repo
realmarcin/protstruct_review). Fetch each branch and read its full diff against main:
  gh pr diff 7   # "Close tool_recommendations coverage gap: 142/142 metrics"
  gh pr diff 8   # "Make T15 runnable: DSSP-vs-biotite secondary-structure agreement"
Also read, for grounding: CODING_STANDARDS.md, ref/oracle_tools.md, ref/catalog.yaml,
ref/thresholds_and_standards.md, and scripts/t15_ss_agreement.py.

This is a DOMAIN-CORRECTNESS review, not a code-style review. The repo's own
scripts/validate.sh already gates schema validity, referential integrity, view drift,
and tests — assume mechanical correctness is covered and do NOT report style, naming, or
lint issues. Judge the science.

The load-bearing invariant of this harness (CODING_STANDARDS.md rules 1-3): every metric
is graded by CROSS-TOOL AGREEMENT with at least one genuinely independent, non-cctbx
oracle — never PHENIX-grading-PHENIX. A recommendation or oracle pairing that violates
this, or that names a tool which does not actually compute the quantity in question, is a
real defect.

PR #7 — 112 new `top_considered` ToolRecommendation rows (one per previously-uncovered
metric). For each assignment, judge: does the named tool actually compute that specific
metric? Is it genuinely independent of PHENIX/cctbx? Where a metric was given a per-metric
override (e.g. ctruncate vs aimless for merged-vs-unmerged T13 metrics; ResMap for local
resolution; FSC-Q for per-residue RSCC; gemmi for T05 atom/water/B counts; biotite AF
parsers for pLDDT; PDB-REDO for DPI), is the override correct and better than the task
default? Flag every assignment where the tool cannot produce that metric, or where a more
canonical oracle exists.

PR #8 — makes T15's gradeable metric (three-state DSSP-vs-biotite secondary-structure
agreement) runnable, substituting biotite's P-SEA for STRIDE (which is no longer
Homebrew-installable). Judge specifically: (a) is biotite P-SEA a legitimately INDEPENDENT
second assigner vs DSSP, or do they share enough algorithm to make the agreement
tautological? (b) is the 8-state->3-state DSSP collapse and the biotite a/b/c->H/E/C
collapse in scripts/t15_ss_agreement.py correct per the standard conventions? (c) is the
residue-alignment and agreement-fraction math sound (per-chain, shared-residue only)? (d)
is the reported 0.86 on 1sar a defensible number, and is calling this the "gradeable T15
metric" scientifically sound? (e) does substituting biotite for STRIDE weaken the trust
model in any way that should block merge?
</task>

<grounding_rules>
Ground every finding in the actual capability of the named tool and in the diff you read.
Do not present an inference about what a tool computes as fact — if you are not certain a
given oracle produces a given metric, label it a hypothesis and say what would confirm it.
Prefer primary knowledge of the tool's documented output over pattern-matching on names.
</grounding_rules>

<dig_deeper_nudge>
After the first questionable assignment, keep going: check for systematic errors (a whole
task's metrics routed to a tool that only covers some of them), independence violations
(an "oracle" that is actually cctbx-derived), and metrics whose only oracle is another
PHENIX tool. For PR #8 also consider empty/edge cases: chains with no assigned SS,
hetero/multi-chain models, and residues one tool scores but the other drops.
</dig_deeper_nudge>

<structured_output_contract>
Return two sections, "PR #7" and "PR #8". Under each, a list of findings ordered
most-severe first. For each finding give: the metric/decision, severity
(blocker / should-fix / nit), the specific problem, and a concrete corrected assignment or
fix. If an assignment or decision is correct, do not list it. End each section with a
one-line merge recommendation (merge as-is / merge after fixes / do not merge). Keep it
compact — no scene-setting, no restating the diff.
</structured_output_contract>

<action_safety>
Read-only review. Do not modify files, push, or comment on the PRs. If you check out a
branch, leave the working tree as you found it.
</action_safety>
