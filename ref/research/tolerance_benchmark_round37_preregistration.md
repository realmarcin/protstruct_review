# Round 37 — pre-registration

Registered **before any refinement of the selected set**, in a commit containing no results.

## The claim under test

Two §4 band widths for `d_min ≥ 2.5 Å` are sized by null maxima that **cannot be checked**:

    ΔRMSD    `d_min ≥ 2.5 Å`: + 0.35 Å   (null max 0.285 Å)
    favored  `d_min ≥ 2.5 Å`: − 6 pp     (null max 5.26 pp)

Both come from the ~11 low-resolution entries whose ids were never recorded. Round 20 re-measured the
**16 identifiable** entries and both clauses held — but the two maxima that actually *set the widths*
are from the lost batch, and the registry says so plainly. The same paragraph records that the quoted
starting clashscore of 17.2 is not reproducible either; the highest recoverable is 13.61.

This is not a `⚠ partial record` row that round 21's route can fix. Round 22 established that
re-measuring a committed subset works **only when the lost members were unremarkable**, and here the
lost members are precisely the extremes.

**So the question is not "do the bands hold" — round 20 answered that on what remains. It is: does a
fresh, named, low-resolution set reproduce maxima of the same size, or were 0.285 Å and 5.26 pp
unrepresentative?**

## Method, fixed in advance

**Selection** — `scripts/select_xray_entries.py`, default window `d_min 2.5–3.2 Å`, 4 strata,
`--limit 20`, excluding the 16 ids `bench_refinement_deltas.DEFAULT_SET` can still name. Selection is
by query on `rcsb_entry_info.diffrn_resolution_high.value` and every hit is re-verified against the
entry record (#238). **The ids are committed with the result**, which is the whole point of the round.

**Measurement** — `bench_t06_r_offset.py` to fetch each model and its structure factors, then
`bench_refinement_deltas.py` for the **null re-refinement**: each deposited model re-refined against
its own deposited data with `phenix.refine`. The model is already at its refinement optimum, so
whatever spread remains is the floor a Δ band must clear. Unchanged from rounds 5–20, deliberately, so
the numbers are commensurable with the ones they are checking.

**Quantities** — Cα-shift RMSD without re-superposition, Ramachandran-favored Δ in pp, rotamer-outlier
Δ in pp, clashscore Δ and ratio. The maxima are what matter; medians are reported for context.

**The canary is in the population and its value was known before this file was written.** 1A0C
(2.5 Å, 1748 Cα) gave `ca_shift_rmsd` **0.1036 Å**, favored **−0.52 pp**, rotamer **−3.04 pp**. It is
declared rather than dropped: removing a known-small value would bias nothing about a *maximum*, but
concealing that one member was measured first would misrepresent the design.

## Predictions

**P1 — both bands hold on the fresh set.** No entry's Cα-shift exceeds **0.35 Å** and no entry's
favored drop exceeds **6 pp**. *Falsified* by a single breach, which would be a live finding about a
published band rather than a bookkeeping result.

**P2 — the fresh Cα-shift maximum is BELOW 0.285 Å.** The lost maximum was the worst of ~11; a fresh
20 drawn by query rather than by hand should not reach it. *Falsified* if the fresh maximum is
≥ 0.285 Å — which would **corroborate** the lost figure and make the 0.35 Å width look well-sized.

**P3 — the fresh favored maximum is BELOW 5.26 pp.** Same reasoning. *Falsified* if ≥ 5.26 pp.

P2 and P3 are the round's substance: they are the first check on whether the unrecoverable maxima were
typical of the branch or the tail of a small sample. **Either outcome is informative** — reproducing
them restores confidence in a band nobody can audit, and falling well short means the widths rest on
extremes that a fresh sample does not reach.

**P4 — at least one deposited model fails an absolute floor.** The §4 floors (`clashscore ≤ 4`,
`favored ≥ 97 %`, `rotamer outliers ≤ 2 %`) are quality bars, not refinement checks, and the canary
already failed two of three. *Falsified* if all 20 deposited models meet all three floors. Registered
because it is nearly certain and therefore cheap to be wrong about — and because if it *is* falsified,
the floors are doing something different from what round 5 assumed.

**P5 — the fresh clashscore maximum does not reach the unreproducible 17.2.** *Falsified* if any
deposited model starts above 17.2, which would show the lost value was ordinary rather than extreme.

## What this round cannot answer

- **Whether the lost entries were these entries.** They are gone. This measures the *branch*, not the
  batch, and a fresh maximum agreeing with 0.285 Å would be corroboration, not recovery.
- **Whether 20 is enough.** The lost batch was ~11 and produced the record maxima. A larger fresh
  sample can only push a maximum up, so P2/P3 failing at n = 20 is meaningful while P2/P3 holding is
  weaker evidence — disclosed here rather than argued afterwards.
- **Anything about `d_min < 2.5 Å`.** That branch's sizing case (43SK, 0.1011 Å) is named and was
  re-measured by round 20. Out of scope by construction (#237).
- **Whether a band should change.** Nothing is re-fitted this round regardless of outcome. If P1 is
  falsified the breach is reported and the decision is registered separately, which is the rule round
  14 set when it reversed an earlier recommendation to collapse a split.
