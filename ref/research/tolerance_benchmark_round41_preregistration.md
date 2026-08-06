# Round 41 — pre-registration

Registered **before any refinement of the round-41 set**, in a commit containing no results. This is
**#225** — a fresh low-resolution X-ray set to give the §4 band widths a checkable basis — and it runs
**round 39 arm 2**, which round 39 registered and left unrun (it could not change the favored-band
decision arm 1 had already settled, so it was deferred to here).

## What arm 1 settled, and what this cannot change

Round 39 arm 1 showed 6LE5's favored-band breach is an **unrestrained-refinement artefact** — 6.28 pp
unrestrained, 2.21 pp under restraints — so the §4 `d_min ≥ 2.5 Å` favored band is **kept at −6 pp**.
That decision stands. **This round cannot re-fit any band**: a higher fresh *unrestrained* maximum would
sharpen the unrestrained caveat's basis, not reopen the band, which is sized for the restrained protocol
low-resolution refinement actually uses.

What it *does* give #225: the §4 Cα-shift and favored band widths rest on two maxima (0.285 Å, 5.26 pp)
from a lost batch named nowhere. Rounds 37–38 produced fresh named sets; this adds a third, **excluding
every round-37 and round-38 id** so it is genuinely new data, not a re-draw.

## Method

Identical to round 38 (unrestrained null re-refinement, `phenix.refine`, 3 macro-cycles, pinned
`phenix-2.0-5936`), except the selector **excludes the 37 round-37/38 ids** and widens the offsets
(`--per-stratum 40 --chunks 8 --limit 25`) to clear ≥ 15 usable after that exclusion. The set is
committed with the result, as in rounds 37–38.

Selection ran before this file and returned **25 ids**, d_min 2.5–3.2 Å, none overlapping the excluded
37, with a genuine era spread (2QIZ, 2IEF … 7LMC, 7D6N — not the all-pre-2000 sample round 37 drew):
3GRT, 3A01, 4EL1, 5DZK, 5T9A, 5URQ, 3G7M, 3EUJ, 6QGY, 4FN9, 6CSM, 5X6C, 2QIZ, 2IY0, 3ZM5, 4Q9R, 2IEF,
2I4M, 7LMC, 7D6N, 5MAC, 4W7P, 3D45, 2YOL, 3MIU. Disclosed here because it is already known and
concealing it would misrepresent the design — attrition of the same kind rounds 37–38 saw is expected.

## Predictions

**P3 (carried from round 39 arm 2) — a fresh unrestrained set reaches a favored-drop maximum ≥ 6.28 pp.**
The maximum can only rise with more data, so **P3 holding is the meaningful direction and P3 failing is
weaker evidence**. *Falsified* if the fresh unrestrained maximum is < 6.28 pp. Whichever way it lands,
**no band is re-fitted** — this sharpens the unrestrained caveat, it does not reopen the −6 pp decision.

**P_Cα — the fresh unrestrained Cα-shift maximum is compared against the lost 0.285 Å**, giving that
band width its first fresh check on data excluding rounds 37–38. Round 38 reached 0.2004 Å; a value
that reaches or exceeds 0.285 Å would be the meaningful direction (a maximum rising), a lower one the
weaker. Reported, not a pass/fail band change.

**P_n — at least 15 of the 25 usable.** Round 38 managed 14 of 17 pairs; the wider selection targets
≥ 15 usable. *Falsified below 15*, in which case the round reports the shortfall and P3 is recorded as
underpowered — a result, not a failure.

## What this round cannot answer

- **Whether any band should change.** Nothing is re-fitted regardless of outcome; arm 1 settled the
  favored band and the Cα band is not breached.
- **The lost entries.** Still gone; this measures the branch on fresh entries.
- **The restrained maximum.** This set is refined unrestrained, as round 38 was, so it speaks only to
  the unrestrained caveat, not to restrained practice.
- **Same-binary only.** `phenix-2.0-5936` pinned; a PHENIX upgrade is untested.
- **`d_min < 2.5 Å`.** Out of scope by #237.
