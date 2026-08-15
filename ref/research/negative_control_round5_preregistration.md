# Negative-control round 5 — pre-registration (the first agent subject)

Registered **before any round-5 measurement**. Rounds 0–4 built and measured
the harness; this round points it at what the repo exists for: an **agentic
refinement artifact judged by machinery whose false-positive rate,
detection rate, and recovery baseline are all on record.** Three registered
changes/subjects; everything unnamed carries over from rounds 2–4 unchanged.
Canary figures quoted below were run 2026-08-15.

## E1 — the fallback asymmetry fixed (#342)

Round 4 measured the defect: REFMAC-unmeasurability disarmed the C1 fit rule
and nothing replaced it, so recovery success got EASIER exactly where
evidence was weakest (2 of 5 registered successes were this artifact).
Registered fix: **fit status always requires positive evidence.**

- REFMAC measurable → the C1 all-three rule, unchanged.
- REFMAC unmeasurable → the TWO-PATH rule stands alone: FIT-DEGRADED iff
  both `d_phenix` and `d_gemmi` exceed their null-centered thresholds
  (+0.01220 / +0.01090, the registered C1 table); the row is marked
  `two_path_only: true`.

**Retro-disclosure on the committed round-4 record:** under E1, 9YGW
(+0.0333/+0.0335) and 8R5K (+0.0263/+0.0283) become FIT-DEGRADED and their
recovery successes vanish — the registered success count would have been
**3 of 22**, exactly the audit's honest count. E1 changes no committed
record; it applies from round 5 forward.

## E2 — S-osol: the solvent hypothesis, tested

Round 4's finding (coordinates recover, fit does not) came with a named
hypothesis: the perturbation scrambles ordered solvent that the plain
protocol never rebuilds. Registered subject: **the null protocol +
`ordered_solvent=True`**, recovering the SAME cached `r4p_` perturbed
models (prefix `r5o_`), judged identically under E1.

**Disclosed canary (4M7G, the round-4 canary entry whose plain recovery
stuck at +0.0169 two-path residual):** the registered S-osol invocation ran
end to end on the cached perturbed model; in-run R-free went 0.3984
(perturbed start) → **0.1352** — in the neighborhood of the deposited
value's in-run equivalent, where plain recovery stopped ~0.017 short.
In-run figures only (the bench judges re-derived two-path + REFMAC values);
as always, the registered content is the subject definition, not this
number — but it is why W2 is registered in strong form rather than hedged.

## E3 — S-agent: the first agent subject

Per enrolled entry, an agentic session attempts recovery of the `r4p_`
perturbed model. Registered operational definition:

- **Blinding — auditable, not information-theoretic (review r1).** True
  blinding is impossible for deposited structures: the perturbed filename
  carries the id, and even anonymized, the unit cell fingerprints the entry
  (search-by-cell deanonymizes). So the registered rule is enforce-by-audit:
  the agent receives the perturbed model, the deposited MTZ, and tool
  access, and the action space EXCLUDES any retrieval of the entry's
  deposited coordinates or derivatives — network fetches of the entry,
  this repo's data/ tree, mask records, prior round records. The full
  command transcript is part of the artifact; a transcript showing such
  retrieval **disqualifies that row, by name**. A recovery benchmark where
  the subject reads the answer measures copying, not repair — this rule
  makes that detectable rather than pretending it impossible.
- **Action space**: documented PHENIX tools plus the repo's non-cctbx
  oracles, any phil, at most 6 refinement invocations per entry; the agent
  decides strategy per entry and writes a decision log.
- **Artifact discipline**: final model + full decision log + command
  transcript committed per entry, with hashes, per the repo's agent-artifact
  trust model — generation is not reproducible (agents are not), the
  ARTIFACT and its JUDGMENT are. Judged identically under E1 vs the
  deposited start.
- **Operator-identity disclosure (review r2)**: the S-agent may be the same
  model family and session tooling as the harness operator. The mitigation
  is structural, not procedural: every verdict number is recomputed from the
  committed artifacts by the deterministic bench scripts, agent-reported
  numbers appear nowhere in verdicts, and the transcript is committed for
  audit. The conflict is disclosed here because a trust-model registration
  that leaves it discoverable-but-unstated would be practicing the opposite
  of what it enforces.

## Predictions

**W1 — the solvent hypothesis is decidable.** S-osol genuine successes ≠ 3
(the plain-protocol baseline): strictly more supports the hypothesis;
equal-or-fewer refutes it. Registered as a two-sided read, not a hoped
direction.

**W2 — the strong solvent form.** S-osol successes ≥ 12 of 22 (fixed
denominator; unscreenable rows count against).

**W3 — the agent beats the floor.** S-agent genuine successes > 3. The
comparative S-agent vs S-osol count is REPORTED, not banded — an agent's
choices are not a distribution this document can bound honestly.

**W4 — no false certification.** Zero S-osol or S-agent recoveries judged
successful while any measurable path's residual exceeds twice its C1
threshold — the certification must never contradict its own evidence.

## Outputs and scope

- `negative_control_round5_recover.json` (+ per-entry agent artifacts under
  `data/agents/round5/`) + `negative_control_round5.md`, swept against the
  record.
- Runtime: S-osol ≈ 22 refinements (~9 h); S-agent is interactive-agentic
  and runs after S-osol's record is committed, entry by entry.
- Enrollment, masks, thresholds, provenance machinery: unchanged. #321 and
  #338 remain parked housekeeping.

## What this round does not do

- No re-judging of committed rounds (E1 retro-numbers are disclosure).
- No agent self-grading: every number in the round doc is re-measured by
  the harness oracles from the committed artifacts — the agent's own
  reported numbers appear nowhere in verdicts (the repo's founding rule).
- No threshold tuning after data.
