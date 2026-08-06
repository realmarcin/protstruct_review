# Round 39 — pre-registration

Registered **before any refinement of the round-39 arms**, in a commit containing no results. This is
the separately-registered decision that round 38 deferred (**#253**): whether the §4 `d_min ≥ 2.5 Å`
favored band should widen, and if so on what basis.

## Why this round exists

Round 38 produced the first null-refinement breach of a §4 refinement Δ-band. **6LE5** (3.10 Å) dropped
favored 93.86 % → 87.58 % = **−6.28 pp** under an unrestrained null re-refinement that *improved*
R-work (0.2769 → 0.2526), R-free (0.3180 → 0.3167) and rotamer outliers (0.51 → 0.06 %) — a
correctly-behaving refinement the **−6 pp** band would wrongly call degradation. The round-38
pre-registration forbade re-fitting the band in the round that first saw the breach, so the decision is
registered here.

**The trap this round exists to avoid.** The naive response — widen the band to clear 6.28 pp — is the
exact move the registry already warns against: *"each new band is again set just above a single worst
case, so treat a further break as the base case."* 6.28 pp rests on **one entry**; the next-worst drop
in round 38 was 2.97 pp, less than half. Bumping a flat band to 6.28 + ε re-fits to n = 1 and will
break again on the next sample. So the decision is not "what number clears 6LE5" but "**is 6.28 pp a
property of the refinement protocol or of the population**", and the two arms below separate those.

## The two explanations, and the arm that tests each

**Explanation A — the breach is an unrestrained-refinement artefact.** The band is quoted for
*unrestrained* refinement, and §4 already records that resolution-appropriate NCS + secondary-structure
restraints shrink the low-resolution favored null spread from **5.26 pp to 3.35 pp** (median −1.23 pp,
10/11 improved). A crystallographer refining at 3 Å applies those restraints. If 6LE5's drop falls
below 6 pp under restraints, the band as it governs *real practice* is not breached, and widening the
unrestrained band would loosen a check no one runs unrestrained at this resolution.

**Explanation B — the band is genuinely mis-sized for the population.** If a maximum can only rise with
more data, a fresh unrestrained low-resolution sample should reach *past* 6.28 pp, and the band is too
tight regardless of restraints.

### Arm 1 — restraint test (reuses the round-38 cache; cheap)

Re-refine the round-38 set **with `--restraints`** (NCS + secondary structure), the flag
`bench_refinement_deltas.py` already carries, and re-measure favored % pre/post. The 17 model+MTZ pairs
are already fetched in the round-38 cache, so this arm adds no downloads. Per-entry, compare the
restrained favored drop against the unrestrained one from round 38.

### Arm 2 — fresh unrestrained sample (new downloads)

Select a **new** low-resolution X-ray set at `d_min ≥ 2.5 Å`, refine **unrestrained** (identical to
round 38), and measure the favored-drop maximum. **The selection MUST exclude every round-37 and
round-38 selected id** — `known_ids()` excludes only `DEFAULT_SET`, so without an explicit
`--exclude` of the **37** distinct ids across
`round37_xray_selection.json` and `round38_xray_selection.json` (21 + 20, 4 shared — round 37 is 21
since #255 restored 1A0C) the deterministic selector redraws round 38's exact 20. Enough offsets to yield ≥ 15 usable entries after that exclusion; the round is
underpowered and says so if it yields fewer.

## Predictions

**P1 — 6LE5's favored drop under restraints falls below 6 pp.** The breach is unrestrained-specific.
*Falsified* if 6LE5 still drops ≥ 6 pp with restraints. **This is the round's first question**: if P1
holds, the operational band is not breached and the decision is to keep −6 pp with a strengthened
unrestrained-only caveat, not to widen.

**P2 — restraints reduce the favored drop across the round-38 set.** Median restrained drop is smaller
than median unrestrained, replicating §4's recorded 5.26 → 3.35 pp shrink on an independent set.
*Falsified* if the median is unchanged or larger.

**P3 — a fresh unrestrained set (n ≥ 15) reaches a favored-drop maximum ≥ 6.28 pp.** The maximum rises
with more data; the band is too tight on the population, not just on 6LE5. This is the **strong
direction** — a maximum can only rise, so P3 *holding* is meaningful while P3 *failing* is weaker.
*Falsified* if the fresh maximum is < 6.28 pp.

## Decision rule — registered before the data

Stated in advance so the band change (or its absence) is not read off whichever arm flatters a prior:

- **P1 holds** (restraints rescue 6LE5): **do not widen.** Keep −6 pp; strengthen the caveat that the
  band is unrestrained-only and that the unrestrained null max is now 6.28 pp. The operational check
  is intact.
- **P1 fails AND P3 holds**: the band is too tight even under restraints and on fresh data. **Widen —
  but fit the width to the pooled DISTRIBUTION** (a Tukey fence or the p95 over the combined
  low-resolution favored-drop set, restrained where restraints are the intended protocol), never to
  the single worst case. Register the new number against the pooled set, not against 6LE5.
- **P1 fails AND P3 fails**: 6LE5 is a real but isolated breach under both protocols. **Do not re-fit
  on n = 1**; record it as the base case the registry already tells us to expect, and re-open only if
  a later sample reaches it again.

## Cost and stopping

- **Arm 1 is nearly free** — 17 refinements against an existing cache, no downloads. It runs first and
  can settle the decision on its own if P1 holds.
- **Arm 2 costs a fetch + unrestrained refinement per entry**, as round 38 did (~a few minutes each).
  Target ≥ 15 usable after exclusion; **if the excluded, era-spread query cannot yield 15, the round
  reports the shortfall and P3 is recorded as underpowered — that is a result, not a failure.**
- A fresh maximum landing **between 5.26 and 6.28 pp** is the ambiguous outcome: it neither exceeds
  6LE5 nor falls under the old lost max, and P3 is then falsified without settling explanation B. Said
  here so it is not re-read as support afterwards.

## What this round cannot answer

- **Whether a PHENIX upgrade moves these values.** `phenix-2.0-5936` is pinned; this is same-binary
  evidence, as every refinement round here is.
- **The lost entries.** Still gone; this measures the branch on fresh and restrained refinements, not
  the batch that set the original band.
- **`d_min < 2.5 Å`.** Out of scope — that branch's favored band (−0.5 pp, null max 0.25 pp) is not
  breached and is not tested here.
- **Whether to widen by how much, if P1 fails.** The width is fit to the pooled distribution in the
  round that measures it, against a prediction registered *then*; this round registers the decision
  procedure, not the number.
