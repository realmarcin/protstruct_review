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

## Applied

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
- Whether headroom is *predictable* — e.g. from starting CC_mask — is not established here. Round 12
  tested starting CC_mask against degradations and found nothing, and any relationship in round 14's
  entries alone rests on too few points to claim. Recorded as a question, not a finding.
