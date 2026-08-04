---
name: goal
description: Drive a goal end to end — triage and prioritize open issues, branch, implement, push, PR, adversarially review, file issues from the review, address them, then merge and clean up. Handles stacked/dependent PRs and pauses for decisions only the user can make. Use when the user says "work on the open issues", "take this to a PR", "/goal", or asks for a full change cycle rather than a single edit.
---

# Goal: issue triage → change → review → merge

Run a piece of work through the whole cycle without dropping the parts that are easy to skip:
prioritizing honestly, reviewing your own diff as an adversary, and cleaning up afterwards.

**Two rules override everything below.** Merging is the user's call — never merge without explicit
go-ahead in the current conversation. And branch *before* the first edit, never after.

---

## Phase 0 — Survey before deciding anything

```bash
gh issue list --state open --json number,title,labels
gh pr list --state open --json number,title,baseRefName,mergeable,mergeStateStatus
git branch --show-current && git status --short
git log origin/main..HEAD --oneline
bash scripts/validate.sh   # or the repo's gate; must exit 0 before any merge
```

Note whether `main` has moved, whether any PR is based on another branch rather than `main`, and
whether the working tree is clean. Report the state in one short paragraph before proposing work.

---

## Phase 1 — Triage and prioritize

For each open issue decide: **is it real, how bad, and what does it block?** Rank by

1. **Correctness of a published claim** — a wrong number, a stale figure, an unsupported assertion.
   Highest, because everything downstream inherits it.
2. **A guard that does not guard** — a test or gate that would pass with the defect present. Nearly as
   bad as the defect, because it hides the class.
3. **Silent failure paths** — anything that degrades to "no output" rather than an error.
4. **Staleness** — a figure or count that was right when written and is not now.
5. **Readability of load-bearing text** — a correct claim nobody can parse still misleads.

Then say which you will do **in this change** and which you will leave filed, **and why**. "As needed"
is a judgement, not a rubber stamp: fixing everything at once produces an unreviewable diff.

> ⏸ **Pause and ask** if: the ranking depends on the user's priorities rather than the code; two issues
> imply contradictory designs; or an issue's fix would change a published result. Ask a direct
> question with concrete options — do not guess and proceed.

---

## Phase 2 — Branch, then work

```bash
git checkout -b <short-descriptive-branch>
```

Before any long or costly batch — billed calls, downloads, refinements, mass rewrites — **canary
one unit end to end through the same path the batch will take**, and verify the *side effects*:
the file exists, is non-empty, has the expected row, the counter moved. An exit code of 0 proves
nothing. Say what the canary did and did not exercise.

If the work produces a measurement or tests a hypothesis:

- **Register predictions in a commit that contains no results**, so the registration is verifiable in
  git history rather than asserted.
- **Compute the power and the sampling cost first.** A cheap selector is not a cheap experiment. Write
  down, in advance, the outcome where the round cannot answer the question — it is a real result.
- Prefer a prediction about the *comparison you care about* over an interval around a point estimate.

---

## Phase 3 — Commit and push

Commit messages: what changed, **why**, and what it means. State the failure the change prevents.
Push and open a PR whose body a reviewer could act on without reading the diff first.

---

## Phase 4 — Review, as a separate adversarial pass

**This is the phase most worth not skipping, and it is read-only: do not edit, push, or fix while
reviewing.** Re-read the diff as someone trying to find what is wrong with it, not as the person who
wrote it.

Re-derive every quoted figure **from the committed artefact**, not from prose and not from a rounded
table. If a document cites a script, run that script and diff its output against the text.

Check specifically:

- **Numbers vs the data.** Counts, medians, denominators, n. Recompute; don't read.
- **Does the claim match the arithmetic?** The arithmetic being right is not the claim being right.
  Watch for a stronger version of a true result — "validated" for "measured on a subset",
  "independent" for a re-run, "across versions" for one pinned binary.
- **Denominators.** Did a count change meaning? Is n stated? Would a reader know what it counts?
- **Guards.** Would the new test fail if the fix were reverted? **Prove it** — revert the fix, watch it
  fail, restore.
- **Siblings.** If this fixes one instance of a defect class, grep for the others. A defect fixed in
  one script is usually present in its neighbour.
- **Staleness the change introduces.** A figure updated in one place and missed in its twin.
- **Lead sentences.** In long documents the bolded opener is what gets read; a correction buried in
  the body is not a correction.

Delegating breadth to sub-agents is useful here — they read the diff without the author's memory of
intending something. **Verify their findings yourself before acting**; they are wrong often enough to
matter, and a false finding filed as an issue is its own defect.

**Also review the fix commits.** Fixes written under review pressure are where new defects go.

---

## Phase 5 — File every finding as an issue

One issue per finding, **before** fixing any of them. An issue is the record that the finding existed
even when the answer is "won't fix". Each should state: what is claimed, why it is wrong, the evidence
(quote it), the suggested fix, and a severity.

---

## Phase 6 — Address, then re-check

Fix what belongs in this change. Leave the rest filed and say which is which and why. Re-run the gate
and the tests. Re-verify each corrected figure against its source — a fix that introduces a new wrong
number is common.

Record what the review found in the change's own write-up. A defect caught and quietly fixed teaches
nobody; the pattern across several is usually the more valuable finding.

---

## Phase 7 — Merge and clean up

> ⏸ **Pause here. Do not merge without explicit go-ahead in the current conversation.** Approval of a
> previous PR is not approval of this one. Summarize what merging would land, then wait.

On approval:

```bash
bash scripts/validate.sh                     # must exit 0
gh pr merge <N> --squash --delete-branch     # match the repo's existing merge style
git checkout main && git pull
git branch -D <branch>                       # remote and local
gh issue close <fixed issues> --comment "Fixed in #<N>, merged to main as <sha>."
```

Then confirm: PR merged, both branches gone, issues closed, gate green on `main`.

---

## Dependencies between PRs

**Deleting a base branch does not retarget its dependent PRs — GitHub closes them.** This is the trap
worth remembering; it costs a rebuild every time.

When PR B is based on PR A's branch:

1. **Merge A first.** There is no other order — B's diff is meaningless without A.
2. Deleting A's branch **closes B**. Either retarget B to `main` *before* deleting, or expect to
   reopen/recreate it.
3. After A merges by squash, B's branch still holds A's individual commits, which `main` no longer
   has. Rebuilding B on `main` and re-applying only B's own changes is usually cleaner than merging.
   Diff from **B's first commit**, not from the shared ancestor, or you will replay A's work too.
4. Where both touched the same lines, **resolve by keeping both sides** — a late fix in A and a change
   in B are usually both wanted. Verify afterwards that none of A's fixes were dropped.

If more than two are stacked, say so and propose an order before touching anything.

> ⏸ **Pause and ask** before force-pushing a shared branch, reverting on `main`, or merging anything
> the user has not named.

---

## When to stop and ask

Pause for: priorities only the user knows; a fix that changes a published result; destructive or
hard-to-reverse actions; scope that has grown past what was asked; and any point where you would
otherwise guess. Ask one direct question with options — not "shall I proceed?".

Do **not** pause for: reversible work that follows from the request, or a choice with an obvious
default. Make it, say you made it, and carry on.

## Recurring traps, from practice

- A figure recomputed from a **rounded** table instead of the source.
- A statistic that ages silently when the dataset grows.
- A count that switches convention — same word, different denominator.
- A relative gate with a bound at one end only; check what happens at zero.
- "It reproduces" when the same pinned binary ran on the same inputs.
- A subset re-run described as independent corroboration.
- A conclusion that lands, by coincidence, in the direction that flatters the hypothesis under test.
  Check those hardest.
