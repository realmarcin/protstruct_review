# Tolerance benchmark — round 24: gating the class instead of fixing the instance

No open issues, no open PRs, one backlog item established as a project rather than a round. So this
round takes the standing risk with the clearest unaddressed shape.

## The class

Three times the registry has been found quoting a figure that had **aged** — computed from
`ref/research/data/em_refinement_deltas.tsv`, which grows every round, and never recomputed:

| | what had aged | how it was found |
|---|---|---|
| **#72** | ρ = +0.397 "over 44 entries", round-16 vintage and unlabelled, with a second `44` serving as a live denominator | reviewing round 19, unrelated |
| **#107** | the CC_mask rate statistics were round-17 vintage (n = 25) after round 19 took the set to 35 | reviewing round 23, unrelated |
| **#113** | the "named entries" convention yielded **93** rather than the **69** it stated, once round 23 appended 24 screening-only rows | this round's audit |

All three were caught while looking at something else. **Catching a class three times by luck is not
a process** — and by this repo's own triage ranking, a defect class with no guard sits above the
individual defects, because it hides them.

## #113, the instance this round found

`ref/thresholds_and_standards.md` defines its headline count deliberately — the definition was added
in round 21 precisely to stop the `53 → 69` convention switch (#84) recurring:

> **69** named entries (excluding the 4 unidentified `LOST` rows), of which **63** reached a
> refinement attempt, **58** carry a recorded Δ and **35** have full pre/post values.

Applying that definition to the file today gives **93**. Round 23 appended 24 `screened only` rows —
entries measured pre-refinement to test the crossing-quality ratio, never refined. They are named and
they are not `LOST`, so the stated exclusion does not remove them.

**The number was right and the definition was wrong**, which is the inverse of #84 and arguably worse:
a reader checking the count against the file gets 93, concludes the registry is 24 behind, and
"corrects" a figure that was correct. The other three counts (63 / 58 / 35) are unaffected — screened
rows have no Δ and no post value.

Fixed by stating the exclusion: *entries that entered the refinement benchmark*, excluding both the
`LOST` rows and the `screened only` ones.

## The gate

`scripts/check_registry_figures.py`, wired into `scripts/validate.sh`. It pairs each dataset-dependent
figure in the registry with a function that recomputes it from the TSV, and fails if they diverge.

Eight figures are covered: the entry count, the CC_mask degradation count, the `d_FSC_model`
degradation count and median, the worst degradation, the resolution correlation, and round 23's
crossing-ratio median and band count.

**It also fails when the literal is absent** — i.e. when someone has reworded the claim rather than
changed the number. That half matters as much as the first: a gate that only compares numbers is
defeated by a rewrite, which is exactly how a figure escapes notice. A reworded claim is not silently
passed; it is flagged for a human to re-check.

Verified in both directions:

| test | result |
|---|---|
| append a row to the TSV (figures age) | **3 checks go STALE**, with the old and new values printed |
| reword one claim, leaving the number right | **1 check goes MISSING**, naming the literal it lost |
| restored | gate passes, 8/8 |

**Not covered, deliberately:** the §3 rows. Their sets are fixed and committed (round 18), so those
figures cannot age without someone editing a `DEFAULT_SET` — which `validate.sh` already gates
separately. Adding them here would be duplicated coverage with a second thing to keep in sync.

## Scope limits

- **The gate checks eight figures, not every number in the registry.** It covers what is derived from
  the growing per-entry file. A hand-computed figure, or one derived from a source the gate does not
  read, still ages silently.
- **It cannot tell a stale figure from a deliberate change.** Updating the data and the text together
  is a passing state; that is intended, but it means the gate enforces consistency, not correctness.
- **The literal-matching is brittle by design.** Rewording a covered claim fails the build. That is
  the point, and it will occasionally be annoying.
- No tolerance, band or measurement changed in this round.
