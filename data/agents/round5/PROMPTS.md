# Round-5 S-agent session prompts — committed for auditability

Every blinded session received the base template below (entry id and file
paths substituted). Four deltas were added during the leg as operational
lessons accrued; each is quoted with the entries whose prompts carried it.
This drift is disclosed in `negative_control_round5.md`; the substantive
rules (blinding, budget, transcript) were identical for all 22.

## Base template (all entries)

> You are an agentic crystallographic refinement subject in a blinded
> benchmark (registered protocol:
> ref/research/negative_control_round5_preregistration.md — but do NOT read
> that file or anything else in this repo's ref/ or data/ trees; the rules
> you need are fully stated here).
>
> TASK: You are given a structurally perturbed protein model and its
> diffraction data. Repair the model: produce the best genuinely refined
> structure you can — fit to data AND sound geometry.
>
> INPUTS (read-only):
> - Perturbed model: /tmp/nc_round1_work/r4p_<id>.pdb
> - Diffraction data: /tmp/nc_round1_cache/<id>.mtz (inspect column labels
>   with gemmi; use the amplitude pair and free-flag column you find)
>
> TOOLS: PHENIX at /Users/marcin/phenix-2.0-5936/phenix_bin/ (phenix.refine,
> phenix.model_vs_data, phenix.clashscore, phenix.ramalyze, phenix.rotalyze,
> phenix.dynamics, phenix.ready_set, etc.), gemmi CLI at
> /opt/homebrew/bin/gemmi. Work in a scratch dir you create:
> /tmp/agent_r5_<id>/. For phenix.refine, pass data selectors as
> "miller_array.labels.name=<F>,<SIGF>" and
> "miller_array.labels.name=<free-flag-label>" for the labels you identify.
>
> HARD RULES (violations disqualify your entry — your full command
> transcript is audited):
> 1. NO retrieval of deposited coordinates for this or any entry: no network
>    access of any kind (no curl/wget/phenix.fetch_pdb), no reading this
>    repository's ref/ or data/ directories, no reading any *_mask.json,
>    *_validation.xml, or any file under /tmp/nc_round1_cache other than the
>    .mtz named above.
> 2. At most 6 invocations of refinement programs (phenix.refine or
>    equivalent). Validation/measurement tools are unlimited.
> 3. Every shell command you run must be recorded, in order, in your
>    transcript.
>
> STRATEGY GUIDANCE (yours to accept or reject — you decide): the
> perturbation may have damaged solvent structure and side chains as well as
> coordinates; consider whether ordered-solvent rebuilding, weight
> optimization, or staged strategies earn their cost. Measure as you go;
> stop when marginal gains vanish or your refinement budget is spent.
>
> DELIVERABLES (create the directory):
> /Users/marcin/Documents/VIMSS/ontology/protstruct_review/data/agents/round5/<ID>/
> - final.pdb — your chosen final model (copy it there)
> - decisions.md — per step: what you did, why, what you measured, what you
>   concluded
> - transcript.md — every shell command in execution order (verbatim)
>
> Your self-measured numbers are advisory only — the benchmark independently
> re-measures everything from final.pdb. Return a one-paragraph summary of
> what you did and your final self-measured R-work/R-free as text.

For 4M7G only, the observation labels were named in the prompt
(FOBS,SIGFOBS; R-free-flags); every later entry identified its own labels.
For 9YGW only, an extra sentence noted the MTZ carries several observation
arrays and two free-flag columns, to be chosen deliberately.

## Delta 1 — setsid note (6ZWY onward)

> Note: macOS has no setsid; if you background long jobs use nohup ... & and
> poll the log.

Added after 7R2H's annotated setsid launch failure.

## Delta 2 — budget clarification (8ERE onward; final wording from 6XVM)

> At most 6 invocations of refinement programs (phenix.refine or equivalent)
> that actually perform refinement. A launch that fails before refinement
> starts (shell failure, parameter rejection, pre-refinement crash) does not
> count; annotate any such case clearly in the transcript.

Codifies the auditor rulings already applied to earlier entries (7R2H's
shell failure, 6Q01's PHIL rejections).

## Delta 3 — /tmp-reaper contingency (6F1O onward)

> If this file disappears mid-task (the /tmp reaper has deleted cache files
> before), a faithful copy of the observations survives in any of your own
> phenix.refine output MTZs — recover from there and annotate; do NOT
> re-fetch from the network.

Added after the 9YGW deletion incident. 9TXE exercised it (deletion before
session start; recovered from a round-4 output MTZ).

## Delta 4 — phase hygiene + pkill warning (9TXE only)

> IMPORTANT DATA-HYGIENE RULE: if the MTZ carries any phase-bearing columns
> beyond observations and free flags (FC, PHIFC, HLA-HLD, FWT/PHWT, DELFWT,
> FOM), do NOT let them influence refinement: pass an explicit refinement
> target (target=ml) and use_experimental_phases=False, or strip the MTZ to
> H K L, the amplitude pair, and the free flags before refining.
> phenix.refine silently switches to an MLHL target when HL coefficients are
> present — refining against derived phases violates the blinding.
>
> Never use broad pkill patterns — track your own PIDs; sibling agents run
> phenix concurrently.

Added after the 8R5K agent's MLHL discovery and the two pkill disclosures.
Inert in practice: only 8R5K's MTZ carries HL columns, and its agent (which
never saw this delta) had already found and handled the issue unwarned.
