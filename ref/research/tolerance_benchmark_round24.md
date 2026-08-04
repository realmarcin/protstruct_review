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
"corrects" a figure that was correct. Screened rows have no Δ and no post value, so 58 and 35 are
unaffected — but the 63 turned out to have a separate problem of its own, found later in this same
round (#115, below).

Fixed by stating the exclusion: *entries that entered the refinement benchmark*, excluding both the
`LOST` rows and the `screened only` ones.

## The gate

`scripts/check_registry_figures.py`, wired into `scripts/validate.sh`. It pairs each dataset-dependent
figure in the registry with a function that recomputes it from the TSV, and fails if they diverge.

Eight figures are covered (a ninth check was added later in the round — see #115 below): the entry count, the CC_mask degradation count, the `d_FSC_model`
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
| restored | gate passes |

**Not covered, deliberately:** the §3 rows. Their sets are fixed and committed (round 18), so those
figures cannot age without someone editing a `DEFAULT_SET` — which `validate.sh` already gates
separately. Adding them here would be duplicated coverage with a second thing to keep in sync.

## Self-review: the gate did not catch the next instance

Reviewing this PR's own diff found **#115**, in the very sentence this round edited.

The registry stated the denominators as a nesting — *"**69** … of which **63** reached a refinement
attempt, **58** … and **35** …"*. **63 is not a subset of 69.** It counts the 4 `LOST` rows, which
round 13 did measure and which the 69 explicitly excludes. Attempted *within* the 69 is **59**.

```
named (excl LOST + screened)   69      <- the registry's 69
attempted among those 69       59
all rows - skipped - screened  63      <- the registry's 63
```

Either figure is defensible alone. The phrase **"of which"** is what made them inconsistent — the
third instance of this exact family after #84 (a silent convention switch) and #113 (a definition
that drifted). In all three the numbers were individually right and their *relationship* was not.

**The gate built this round would not have caught it.** It verifies each figure against the data, and
63/58/35 are not among the eight it checks — but more to the point, nothing compared the figures to
*each other*. A per-figure check cannot see a broken relationship between figures.

So the gate now carries a ninth check asserting the counts are monotonically nested
(`named ≥ attempted ≥ with-delta ≥ measured`), and the prose states 59 with the 63 given its own base
explicitly.

That is worth recording plainly: **this round built a guard for a class and then immediately shipped
a fourth instance of a neighbouring class that the guard did not cover.** The guard is still worth
having; the lesson is that "gated" is narrower than it sounds, and the scope of a gate should be
stated as carefully as its result.

## Scope limits

- **The gate checks nine things, not every number in the registry.** It covers what is derived from
  the growing per-entry file. A hand-computed figure, or one derived from a source the gate does not
  read, still ages silently.
- **It cannot tell a stale figure from a deliberate change.** Updating the data and the text together
  is a passing state; that is intended, but it means the gate enforces consistency, not correctness.
- **The literal-matching is brittle by design.** Rewording a covered claim fails the build. That is
  the point, and it will occasionally be annoying.
- No tolerance, band or measurement changed in this round.
