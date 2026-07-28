# Tolerance benchmark — round 14: what a null case actually measures

Round 13 left three items: collapse the CC_mask resolution split, re-test both CC_mask bands, and
widen the `d_FSC_model` tail. One EM widening at 2.4–3.2 Å tests all three, since a single `mtriage`
+ `real_space_refine` run produces both quantities.

```bash
python3 scripts/fetch_em_entries.py --cache <dir> --min-res 2.4 --max-res 3.2 --limit 8 \
    --strata 8 --per-stratum 4 --max-map-mb 300 --max-model-mb 8 --exclude <existing set>
python3 scripts/bench_refinement_deltas_em.py --cache <dir> --json out.json
```

The widening produced a result about the **method** before it produced one about the bands, so that
comes first.

## 0. The EM benchmark was not reproducible, and selecting entries was biased

Rounds 5 and 9–13 built their EM cache by hand in a temporary directory. Clearing it — which is what
had happened by the time this round started — destroyed the only record of *which* entries produced
every EM number in this repo. The audit trails name the entries in prose, but nothing re-derives the
set. `scripts/fetch_em_entries.py` closes that: selection is a query, not a transcription.

Writing it exposed a sampling bias that would have invalidated this round:

**A single sorted RCSB query does not sample a resolution window.** Asking for the 40
best-resolution EM entries in 2.4–3.2 Å returns **40 entries at exactly 2.40 Å**. The PDB holds far
more structures at the fine end of any window than the coarse end, so an ascending sort collapses
the range onto its lower bound; a descending sort fails identically at the other edge, and sorting
by release date samples deposition fashion rather than resolution. Since the tolerance under test is
**resolution-conditional**, a set collapsed onto one resolution cannot test it at all. Equal
sub-band queries, interleaved so an early stop still spans the window, are the fix.

**A size cap is a cost gate.** 8RJC reached the cache with 255 550 atoms — 20× every other entry —
and would have refined for hours to contribute a single resolution point. Model size drives
`real_space_refine` cost much harder than map size, so the model cap sits far below the map cap.

**And a skip has to explain itself.** 11MR failed with `Sorry: Fatal problems interpreting model
file` — 128 atoms of a novel ligand (`A1C9W`) with no monomer-library restraints. The benchmark
recorded that as `real_space_refine failed`, which is indistinguishable from a bug in the benchmark.
It is neither a bug nor a tool limit: an entry carrying an unparameterised ligand **cannot** be
re-refined by this pipeline, which is a property of the entry. `refine_failure_reason()` now names
the cause, because the alternative is a skip list nobody can act on.

That failure is also a **selection effect**, and it runs the same way every time: entries with novel
ligands drop out, so the set drifts toward ligand-free and common-ligand structures. Whether ligand
content correlates with refinement behaviour is untested here — it is recorded so the bias is
visible, not because its direction is known.

## 1. Entry count is not evidence for a one-sided band

Round 13 established this for `d_FSC_model`: the clause is one-sided, so only entries that move in
the **gated** direction are evidence, and 28 entries bought only 8 degradations. **CC_mask has the
identical structure and the lesson was never applied to it.**

From round 12's published per-entry table — the only per-entry CC_mask data in the repo:

| Branch | entries | degradations | share |
|---|---:|---:|---:|
| `< 3.0 Å` | 8 | 4 | 50 % |
| `≥ 3.0 Å` | 14 | 5 | 36 % |
| **total** | **22** | **9** | **41 %** |

So "28 entries" describes roughly **a dozen** pieces of evidence for a band that only degradations
can breach. The other ~60 % are structurally incapable of breaching it — an improvement cannot fail
a `post ≥ pre − 0.04` test no matter how large it is.

This has a direct consequence for how rounds are counted as progress. **Adding entries that improve
does not strengthen a degradation band.** It raises the entry count, which is what the tolerance row
quotes, while leaving the evidence base untouched.

## 2. The null-case premise is false for a substantial minority of entries

`bench_refinement_deltas_em.py` states its own premise:

> the deposited model is already at its optimum, so whatever spread remains is the floor a Δ band
> has to clear.

The data contradict it. 9OID improved by **+0.0595** and 10ES by **+0.0418** — both larger than the
entire `< 3.0 Å` band. A model that improves by more than the band's width was **not** at any
optimum when it was deposited.

So the measured Δ is not one quantity. It mixes:

- **refinement noise** — the reproducibility floor for a model genuinely at its optimum, which is
  what the band claims to be calibrated against; and
- **deposition headroom** — how much the depositor left on the table, which is a property of that
  deposition and has nothing to do with whether a refinement degraded a model.

Only the first is what a Δ tolerance means. The second is a different measurement wearing the same
units.

**The corollary is the part that matters for confidence.** The entries that *can* degrade are those
already at their optimum, with the least headroom — so a degradation band is **set** by low-headroom
entries and **validated** on a set in which high-headroom entries are the majority. Every
high-headroom entry added makes the "0 breaches over N entries" statement stronger-looking and no
stronger.

This does not invalidate the current bands: a band set from the worst observed degradation is still
a band that no observed degradation breached. It does mean the entry counts in
`ref/thresholds_and_standards.md` overstate the evidence, and it explains why this tolerance keeps
breaking as the set grows — most growth is not evidence, so the genuine evidence base grows far
more slowly than the count implies.

## 3. Results: eight entries, eight improvements, no evidence

| Entry | d_min | CC_mask | Δ | d_FSC_model |
|---|---:|---|---:|---:|
| 11NJ | 2.40 Å | 0.8471 → 0.8666 | +0.0195 | −0.14 % |
| 11QC | 2.40 Å | 0.8311 → 0.8315 | +0.0004 | 0.00 % |
| 10XZ | 2.60 Å | 0.8797 → 0.8798 | +0.0001 | 0.00 % |
| 11MR | 2.60 Å | *skipped* | — | unparameterised ligand |
| 10YA | 2.70 Å | 0.9061 → 0.9077 | +0.0016 | 0.00 % |
| 11JF | 2.85 Å | 0.8053 → 0.8152 | +0.0099 | −0.11 % |
| 21AO | 2.85 Å | 0.8338 → 0.8344 | +0.0006 | 0.00 % |
| 10ES | 3.00 Å | 0.7491 → 0.7909 | +0.0418 | −1.23 % |
| 10IJ | 3.10 Å | 0.7893 → 0.8137 | +0.0244 | −0.67 % |

**Every entry improved on both quantities.** Minimum CC_mask Δ is **+0.0001**; maximum `d_FSC_model`
degradation is **0.000 %**. So this round adds 8 entries and, by §1, **zero evidence** to either
band — the outcome §1 predicts, observed prospectively rather than reconstructed.

Against the historical 41 % degradation share, eight consecutive improvements has probability
**0.015**. The high-resolution half is the anomalous part: **0 of 6 below 3.0 Å**, where the
historical rate is **50 %** (p = 0.016 for that subset alone). Treat both figures as descriptive —
they were computed after the pattern was noticed, not from a prediction made before it.

Two readings, one available and one not:

- **Available.** The two `≥ 3.0 Å` entries moved *large* amounts (+0.0418, +0.0244) where historical
  `≥ 3.0 Å` entries moved large amounts the other way (−0.0371 to −0.0475). That is consistent with
  rounds 11–12's "resolution **bounds** but does not **predict** the excursion", with this round
  drawing two large positives. It rests on 2 entries.
- **Not available.** Any claim that this round's entries are systematically better-deposited. Nothing
  measured here distinguishes them; all four checked used PHENIX for model refinement, as the
  historical entries largely did.

### Frequency and magnitude are different things

An earlier draft of this round's recommendation said degradations "concentrate at ≥ 3.08 Å" and
proposed widening there to raise the *chance* of one. That misreads the table (#61): degradation is
**more** frequent below 3.0 Å.

| Branch | degradation rate | worst | median degradation |
|---|---:|---:|---:|
| `< 3.0 Å` | **4/8 = 50 %** | −0.0139 | −0.0060 |
| `≥ 3.0 Å` | 5/14 = 36 % | −0.0475 | −0.0402 |

What concentrates above 3.08 Å is **magnitude** — every degradation there is ≥ 0.0217, every one
below 3.0 Å ≤ 0.0139 (9O9K's −0.0311 excepted, which is why that band moved). A frequent 0.006
degradation cannot re-fit a −0.04 band; a 0.0475 one did. So the low-resolution widening is worth
doing for magnitude, not frequency — and the distinction matters, because the two point at opposite
resolutions.

### The three open items, resolved

| Item | Round 14 outcome |
|---|---|
| Re-test both CC_mask bands | **No breach — and no evidence.** 0 degradations in 8 entries. Both bands stand exactly where round 13 left them, on the same observations. |
| Widen the `d_FSC_model` tail | **Not widened.** The tail is still 8 degradations with one above 1.1 %. This round contributed 0 degradations, so the item is *not* closed. |
| Collapse the CC_mask split | **Decided: keep the split.** Reversing the recommendation made in PR #58 — see below. |

## 4. Keeping the split: "buys no additional margin" was the wrong criterion

PR #58 recommended collapsing the resolution split, on the ground that a single −0.06 band has the
same 1.26× headroom as the looser branch, so the split "buys essentially zero additional margin".
Round 14 gives no new data on the question, but the argument does not survive re-examination.

**Headroom against breaching is not what the tolerance is for.** A Δ tolerance exists to flag a
refinement that degraded the map-model fit. Judging it by how hard it is to breach optimises for the
band never firing — which a band of ±∞ achieves perfectly. The right criterion is detection power:
how small a genuine degradation it still catches.

By that criterion the split earns its keep, and the frequency/magnitude table above supports it
directly rather than in the abstract: **the two regimes differ in the size of a null degradation**
(≤ 0.0139 below 3.0 Å versus ≥ 0.0217 above it), which is exactly what a band's width should track.
Collapsing to a single −0.06 **loosens the high-resolution branch by 50 %**, from −0.04 to −0.06, in
exactly the regime where the null spread is genuinely tighter — the worst `< 3.0 Å` degradation is
−0.0311 against −0.0475 above 3.0 Å. A single
band would sit at **1.93×** headroom over the high-resolution worst case: comfortable, and comfortably
blind to a real 0.05 drop at 2.4 Å.

The cost side is also smaller than PR #58 implied. The "resolution lookup" a consumer must do is one
it already has — `real_space_refine` and `map_correlations` both require the resolution as an
argument, so no caller can reach this tolerance without it.

What remains true from PR #58 is that the split's *evidence* is thin: by §1's counting each branch
rests on roughly 5 degradations, not 14 entries. That argues for re-testing it against
low-resolution entries, not for deleting it.

## Applied

> **Both CC_mask bands and the `d_FSC_model` band are unchanged.** 8 new entries at 2.40–3.10 Å
> produced 0 degradations, so there is nothing to re-fit; the bands rest on exactly the observations
> they rested on after round 13.
>
> **The resolution split is kept**, reversing PR #58's recommendation to collapse it. Collapsing
> loosens the `< 3.0 Å` branch by 50 % where the null spread is measurably tighter, trading detection
> power for a simplification whose cost was overstated.
>
> The CC_mask and `d_FSC_model` tolerance rows now quote a **degradation count** alongside the entry
> count. The entry count alone is not a measure of the evidence for a one-sided band.

## Scope limits

- The degradation shares come from round 12's 22-entry table, the only per-entry CC_mask data
  published in this repo. Rounds 13 and 14 report their own entries but the earlier rounds' per-entry
  values were lost with the hand-built cache — which is the reproducibility gap §0 closes going
  forward, not retroactively.
- "Degradation" here means Δ < 0 at the precision published (4 dp). Entries at exactly 0.0000 and
  entries at −0.0001 are separated by less than the measurement's meaningful precision, so the share
  is approximate near zero; 10SH (+0.0001) and 10SG (−0.0019) illustrate the boundary.
- Entries whose ligands lack monomer-library restraints are skipped, so the set under-represents
  structures with novel ligands (11MR in this round). Supplying generated restraints would refine
  those entries under a different protocol than the rest, which is why they are dropped rather than
  patched.
- Whether headroom is *predictable* — e.g. from starting CC_mask — is **not** established here. The
  direction is right: over round 14's entries, Spearman ρ(pre-CC_mask, Δ) = **−0.714**, i.e. models
  that started worse gained more, which is what the headroom reading predicts. But at n = 6 the 5 %
  critical value is |ρ| ≈ 0.886, so this does not reach significance, and pre-CC_mask is
  **confounded with resolution** in this sample (ρ = −0.514) — the two lowest-CC entries are also the
  two lowest-resolution ones. Round 12 tested starting CC_mask against degradations and found
  nothing. Recorded as consistent-with, not evidence-for.
