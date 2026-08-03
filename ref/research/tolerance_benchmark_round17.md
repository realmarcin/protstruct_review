# Tolerance benchmark — round 17: the third mechanism hunt, pre-registered

Four items from the round-16 backlog:

1. Audit the `[benchmark]` rows for extremes quoted from partial records.
2. Re-run 10BU before trusting +4.787 % as the number that sets the thinnest band.
3. Screen unparameterised ligands at fetch time, as charges now are.
4. Find what drives the CC_mask degradation *rate* — **predictions registered first**.

Item 4 is the third mechanism hunt in this series. The previous two — round 7's coverage story for
`d_FSC_model`, round 15's publication-clustering story for CC_mask — were **both wrong**, and both
were proposed after looking at the data. This section is therefore committed before any analysis is
run, and the commit that introduces it contains no results.

## Predictions for the CC_mask degradation rate, registered before the analysis

The premise from the backlog: round 15 (3.00–3.90 Å) degraded CC_mask in **4 of 8** entries, worst
−0.0351; round 16 (3.00–4.11 Å, coarser) degraded **1 of 9**, worst −0.0003. Resolution sets the
magnitude envelope (ρ = +0.397, n = 44) but plainly not the rate.

**Disclosure of what I had seen when registering.** I had read
`ref/research/data/em_refinement_deltas.tsv` in full — the per-entry pre/post values are in it — but
had computed nothing from it: no correlation, no group mean, no test. The predictions below are
motivated by mechanism, not by a pattern already spotted. That is a weaker guarantee than a genuinely
blind registration and is stated rather than glossed.

### The gate

| # | Prediction | Falsified if |
|---|---|---|
| **P0** | The round-15 vs round-16 rate difference is **real** — Fisher's exact two-tailed test on 4/8 vs 1/9 gives **p < 0.05**. | p ≥ 0.05. |

**P0 is registered first because the whole item presupposes it, and I do not believe it.** 4/8 versus
1/9 is a four-fold rate difference on seventeen entries, which is exactly the size of effect that
small samples manufacture. I put P0 at **about 25 %** — i.e. I expect it to be falsified, and I expect
the round's finding to be that there is no rate difference to explain.

If P0 fails, the backlog item is answering a question the data does not pose, and P1–P3 below become
tests of a mechanism for a phenomenon that was never established. They are still worth running — a
predictor of the *sign* of Δ is useful whether or not two particular rounds differ — but they stop
being an explanation of anything.

### The mechanism

**Hypothesis: headroom.** A null re-refinement moves a deposited model under two competing pulls — the
map target and the geometry restraints. A model already sitting near its map-optimal position has
nothing to gain from the map term and can only be pulled *off* by the restraint term, so it degrades.
A model that starts poorly fitted has room to climb. If that is right, the starting CC_mask should
predict the *sign* of Δ, and it should do so across all entries rather than within one round.

| # | Prediction | Falsified if |
|---|---|---|
| **P1** | Entries that degrade have a **higher** `cc_mask_pre` than entries that improve (Mann–Whitney, one-sided, p < 0.05) over every entry with recorded pre/post values. | p ≥ 0.05, or the difference runs the other way. |
| **P2** | `cc_mask_delta` is **negatively** correlated with `cc_mask_pre` (Spearman ρ < 0, |ρ| above the 5 % critical value for n). | ρ ≥ 0, or |ρ| below the critical value. |
| **P3** | Headroom accounts for the round-15/round-16 difference: round 15's entries have a **higher mean `cc_mask_pre`** than round 16's. | Round 16's mean is ≥ round 15's. |

P1 at **65 %**, P2 at **60 %**, P3 at **50 %**. P3 is conditional on P0 in substance though not in
form: if the rate difference is noise, then whichever way P3 lands says nothing.

### The control

| # | Prediction | Falsified if |
|---|---|---|
| **P4** | Resolution does **not** separate degraders from improvers (Mann–Whitney p ≥ 0.05), replicating round 16's claim that resolution sets magnitude but not rate. | Resolution separates them at p < 0.05. |

P4 at **80 %**. It is a replication, not a discovery, and it is registered so that a *positive* result
here would be read as evidence against round 16's reading rather than quietly absorbed.

### Registered scope limit

**P1 and P2 cannot distinguish two mechanisms**, and I am recording that before seeing whether they
hold rather than after. CC_mask is bounded above by 1, so a high-starting entry has less room to rise
for a purely arithmetic reason, independent of any restraint story. "Headroom" in the mechanistic
sense and "ceiling" in the arithmetic sense make the same prediction here. A confirmation of P1/P2 is
therefore evidence that `cc_mask_pre` **predicts** the sign, and not evidence for the restraint
explanation of *why*. Separating them needs a quantity this benchmark does not record — the
restraint-term weight, or the model's coordinate shift.

## Results: the gate failed, and it took the item with it

`scripts/analyze_em_deltas.py`, over the 25 entries with a recorded pre/post CC_mask pair
(rounds 14–16; the `delta-only` rows carry a Δ but no pre value, so they cannot serve a hypothesis
about the *starting* value — the round-13 record loss acting on an analysis rather than on a count).

| # | Prediction | Outcome | Statistic |
|---|---|---|---|
| **P0** | rate difference is real | ❌ **falsified** | Fisher exact 4/8 vs 1/9, **p = 0.131** |
| **P1** | degraders start higher | ❌ falsified | Mann–Whitney p = 0.317 |
| **P2** | Δ correlates negatively with pre | ⚠️ **held, then withdrawn** | ρ = −0.445, p = 0.026 — see below |
| **P3** | headroom explains the round difference | ❌ falsified, **in the opposite direction** | round 15 mean pre **0.7625** < round 16 **0.7879** |
| **P4** | resolution does not set the rate | ✅ held | Mann–Whitney p = 0.919 |

### P0: there is no rate difference to explain

**4 of 8 versus 1 of 9 is p = 0.131.** The observation the backlog asked me to find a mechanism for
is not distinguishable from chance. Two rounds of eight-ish entries cannot establish a rate
difference of that size; the four-fold ratio is what small samples do.

A power calculation says how far off the benchmark is. Holding the observed rates (50 % versus 11 %),
Fisher's exact test first clears p < 0.05 at **20 entries per round**:

| entries per round | 8 | 12 | 16 | **20** | 24 | 32 |
|---|---:|---:|---:|---:|---:|---:|
| p | 0.28 | 0.069 | 0.054 | **0.014** | 0.011 | 0.003 |

Rounds carry 8–9 entries. **This benchmark is structurally underpowered to compare per-round
degradation rates at all** — not for want of a cleverer predictor, but because the rounds are a
quarter of the size the comparison needs. That is the round's most reusable finding: a future round
that wants to answer a *rate* question must be built at n ≈ 20 per arm, or not asked.

A post-hoc 3-round test is worth recording because it is the strongest form of the claim available,
and it is still weak: permuting the degrade/improve labels across all 25 entries (200 000
permutations, seed fixed) gives **p = 0.048** for rate homogeneity across rounds 14/15/16. That is a
coin's breadth inside 0.05, it is post-hoc where P0 was registered, and it is driven mostly by round
14's 0/8. It is not a licence to go looking for a mechanism.

### P3 fails in the direction that kills the hypothesis

Headroom does not merely fail to reach significance — the round-level means run **backwards**:

| round | window | mean starting CC_mask | degraded |
|---|---|---:|---:|
| 14 | 2.40–3.10 Å | **0.8302** (highest) | **0 of 8** |
| 15 | 3.00–3.90 Å | 0.7625 (lowest) | 4 of 8 |
| 16 | 3.00–4.11 Å | 0.7879 | 1 of 9 |

The round that started with the **best**-fitted models degraded **none** of them, and the round that
started with the worst-fitted degraded half. If a high starting CC_mask left a model with nowhere to
go but down, round 14 should have been the worst round in the series. It was the best.

### P2 held as registered, and the registered form was the wrong test

P2 is the one that would have been published as this round's finding. It should not be.

Correlating a **change** against its own **baseline** is negatively biased by construction — the
baseline appears on both sides, with opposite signs. The standard correction (Oldham's method) is to
correlate the change against the *mean* of the two measurements instead. Doing that, and two other
checks:

| test | ρ | p |
|---|---:|---:|
| as registered, ρ(pre, Δ) | −0.445 | **0.026** |
| Oldham, ρ(mean(pre,post), Δ) | −0.279 | 0.177 |
| ρ(post, Δ) | −0.055 | 0.795 |
| ρ(pre, Δ) dropping 10EH | −0.373 | 0.073 |
| ρ(pre, Δ) weakest leave-one-out | −0.373 | — (below the 0.396 critical value) |

The asymmetry is the signature: **pre correlates with Δ at −0.445 while post correlates at −0.055.**
A real "well-fitted models degrade" effect would show up against both. This one shows up only against
the variable that is arithmetically inside Δ. It also fails to survive dropping any single entry.

**P2 is recorded as falsified in substance.** It held in the form I registered, and the form I
registered was wrong — which is the same failure mode round 13 hit when it sized a band of the wrong
shape, and round 15 when it read improvements as breaches. Registering a prediction protects against
fitting a story to the data; it does **not** protect against registering a bad test.

One thing does license this test more than the textbook case: round 16 showed the pipeline is
deterministic, so `cc_mask_pre` carries no *measurement* error, and the classic
regression-to-the-mean artefact — which is driven by measurement error in the baseline — does not
strictly apply. The bias here comes from the arithmetic coupling rather than from noise. That is why
P2 is reported as unsupported rather than as a pure artefact. Either way it is not evidence.

### What survives

**P4.** Resolution does not separate degraders from improvers (median 3.20 Å versus 3.25 Å,
p = 0.919), replicating round 16's reading that resolution sets the magnitude envelope and not the
rate. Among these 25 entries the coarse/fine split is also uninformative: 0 of 6 below 3.0 Å and 5 of
19 above it degrade, Fisher p = 0.289.

**The third mechanism hunt is wrong too** — but this one was pre-registered, and the registration is
what caught it. Without P0 the round would have reported a four-fold rate difference as real; without
the registered scope limit on P1/P2, it would have reported ρ = −0.445 as a mechanism. The score for
mechanism hunts in this series is now **0 for 3**.

**The lesson is not "try a fourth predictor."** It is that a *rate* question needs roughly 20 entries
per arm and this benchmark builds 8, so the question was unanswerable before any predictor was
chosen. Check the power before registering the mechanism.

## 10BU reproduces — byte for byte

The thinnest band in the file rests on one entry. Round 16 established the pipeline is deterministic
on 32FE (one entry, one repeat), which made this cheap to check and made a *non*-reproduction the
informative outcome.

Re-run from a clean directory with only the deposited model and map — nothing cached, no
intermediates carried over, two days after the original:

| | round 15 | round 17 | |
|---|---|---|---|
| refined model MD5 | `ba90ea7e…` | `ba90ea7e…` | **byte-identical** |
| CC_mask pre → post | 0.7577 → 0.7278 | 0.7577 → 0.7278 | identical |
| `d_FSC_model` pre | 4.3513179439314325 Å | 4.3513179439314325 Å | identical to full float precision |
| `d_FSC_model` post | 4.559556403675602 Å | 4.559556403675602 Å | identical |

A 33-minute optimisation returning a **byte-identical** coordinate file is about as strong as
determinism evidence gets. Round 16's finding now rests on two entries rather than one, and the
number that sets the thinnest band in the file is confirmed rather than assumed. **The one entry
holding up the `d_FSC_model` band is real.**

### The number is 4.786 %, not 4.787 %

The re-run did find something, just not what it was looking for. The exact degradation is

```
(4.559556403675602 − 4.3513179439314325) / 4.3513179439314325 × 100  =  4.785641 %
```

The recorded **4.787 %** comes from computing that ratio out of values already rounded to 4 decimal
places (`(4.5596 − 4.3513) / 4.3513`) during round 16's backfill. It is a **backfill artefact, not a
measurement**: rounds 14–15 were reconstructed from published figures, which is why their TSV rows
carried 4-dp values while round 16's rows carry full precision.

The correction is small — headroom moves from 1.0445× to **1.0448×** — and it changes no verdict. It
matters because this is *the* number that sets the tightest tolerance in the registry, and it was
not the number the pipeline produces. Every rounds-14–15 `d_FSC_model` value has been refreshed from
the surviving mtriage curves; the 16 recomputed values differ from the published ones by at most
**0.0024 pp**, confirming rounding rather than error.

**One value was recovered outright.** 21AO (round 14) had blank `d_FSC_model` columns; its curves
survive and give 2.812499371582172 Å before and after — a legitimate, plausible, zero-change
observation that had simply never been written down. It is a non-degradation, so it does not move the
degradation count, but it is one more entry the band's denominator can now name.

## Item 1: auditing the `[benchmark]` rows for partial records

Round 16's finding — the worst case is always recorded, the typical often is not — was tested against
every `[benchmark]` row. For each: does the quoted extreme come from a set whose *other* values were
also written down, and is the input set enumerated anywhere committed?

**First, a count correction — itself corrected in round 18.** The registry's `[benchmark]` rows
number **20**, against the **21** long quoted in `NEXT_TASKS.md`.

*Round 17 attributed the gap to CC_mask and `d_FSC_model` sharing the "Map-model fit did not degrade"
row. That is a true fact and the wrong explanation.* §3 and §4 hold **21 rows**, so that count was
right all along; the false part was "every tolerance carries `[benchmark]`", because §4's *absolute
geometry floors* row is `[literature]` (Chen 2010 / Williams 2018) and was never measured here.

Round 18 reconciled all of it: **21 rows, 20 of them `[benchmark]`, carrying 21 benchmarked
tolerances** — the shared map-model row is why the tolerance count exceeds the row count, and it is
also why the long-standing "lost 21 times out of 21" is correct. Three numbers, all right, counting
three different things.

Left visible rather than quietly amended: an audit that miscounts while correcting a miscount is
worth keeping in the record, and it is the same failure this round diagnosed elsewhere — a figure
carried forward because it sounded settled.

| Verdict | rows | Which |
|---|---:|---|
| **FULL RECORD** | 11 | CA RMSD, aligned-residue count, clashscore, bond-length RMSD, completeness, R-free, Wilson B, SS agreement, interface BSA, NMR RMSF, R offset |
| **PARTIAL, RECOVERABLE** | 2 | bond-angle RMSD, DockQ |
| **PARTIAL RECORD** | 7 | H-placement, Ramachandran/rotamer favored %, Ramachandran/rotamer outlier %, L-test, §4 ΔRMSD, §4 geometry Δ, §4 map-model fit |

**Just over half the registry is fully backed. Seven rows — carrying eight distinct figures, since
the map-model row is partial for both CC_mask and `d_FSC_model` — quote a number from a set that
cannot be reconstructed.**

### The systemic cause: recoverability is accidental

The eight partial rows are not partial because anyone decided to record less. They are partial
because **almost none of the bench scripts commit the entry set they ran on.** Only four hardcode a
default set — `bench_t01_superposition.py` (`DEFAULT_PAIRS`), `bench_t15_ss_agreement.py`,
`bench_t16_bsa_vs_pisa.py`, `bench_t16_dockq_mapping.py`. The rest take `--ids-file <ids.json>` or
glob an uncommitted `--cache`, **and no `ids.json` is committed anywhere in this repo.**

So where a row *is* recoverable, it is recoverable because an author happened to paste a table into
the audit trail — not because any mechanism preserved it. Wilson B, completeness and the R offset
survive by that accident; the L-test, at n = 27, does not, and its set is not even the same as
Wilson B's n = 24, so the extra datasets are unnamed.

That is round 16's "prose in an audit trail is not a record" one level up. Round 16 fixed it for the
*values* of the EM benchmark. The **inputs** of every other benchmark are still in the position round
13's entries were in: measured, published in aggregate, and no longer identifiable.

### The most expensive instance

The two §4 X-ray rows are the highest-stakes case, because their quoted maxima *are* the band widths:

- ΔRMSD `d_min ≥ 2.5 Å` is **+0.35 Å**, set just above a **null max of 0.285 Å**.
- Favored `d_min ≥ 2.5 Å` is **−6 pp**, set just above a **null max of 5.26 pp**.

Both maxima come from the ~11 low-resolution entries round 7 added. **Those entries are named
nowhere.** Round 7 and round 8 report only that bin's median and max; `bench_refinement_deltas.py`
globs whatever MTZs sit in an uncommitted cache. Of the 37 entries the ΔRMSD row cites, **16 have an
individually recorded value** — and the ~11 that produce both quoted maxima are not among them.

This is exactly the shape that misled round 16's P2 prior, now sitting under the two widest bands in
§4. It is also worse than the CC_mask case, which at least publishes a *range* (15–20) to advertise
its own uncertainty.

A second defect surfaced alongside it: the §4 geometry row still says **19 entries** where the
neighbouring ΔRMSD row says **37**. The two rows describe the same benchmark. One of them was not
re-validated when the set grew.

### What is being changed

Nothing is silently repaired — the affected rows are **marked**, which is what the backlog asked for
where recovery is impossible. Recovery was attempted and succeeded only for the EM `d_FSC_model`
values above, where the raw curves happened to survive on disk.

## Item 3: the ligand screen

The third of the two attrition causes is now off the expensive path. Components with no
monomer-library restraints are checked from the model alone, before the map download — 3 of the 6
skips across rounds 14–16, each of which previously cost a model download, a 200–300 MB map download
and a `real_space_refine` attempt.

**The obvious implementation is wrong.** Checking whether `geostd/<c>/data_<CODE>.cif` or
`mon_lib/<c>/<CODE>.cif` exists gets 11MR and 10EG exactly right and then flags every DNA chain:
`DT`, `DA`, `DC` and `DG` are in **neither** library under those names, and cctbx resolves them
through a separate nucleic-acid path. On 28JV that reads 1431 atoms where 38 actually failed.
Standard polymer residues are therefore exempted via gemmi's own residue table.

Because this is a reimplementation of what cctbx does at refinement time, it was checked against the
authoritative code path — `phenix.pdb_interpretation`, the same interpretation `real_space_refine`
runs — over **all 37 cached models from rounds 14–16**:

| | screen | `phenix.pdb_interpretation` |
|---|---|---|
| 11MR | 128 atoms (A1C9W) | 128 |
| 10EG | 195 atoms (CL0) | 195 |
| 28JV | 38 atoms (VM6) | 38 |
| 10GJ/GK/GL/GM | 23 atoms (8OG) | 23 |
| 30 models with no unparameterised component | pass | 0 |

**Zero disagreements.** The **three** charge failures in the set (10EN, 10FL, 10FJ) correctly report
nothing here — that is a different cause with its own screen. Note the 30-model bucket is *models
with no ligand hit*, not *models that refined*: 25 of them refined cleanly, and the other five are
the three charge rejections plus 10TP and 10UA, which never reached a refinement attempt. Cost is ~0.1 s per model against the
~9 s the authoritative check takes and the hours the failure used to.

10GJ, 10GK, 10GL and 10GM are an incidental finding: four models sitting in round 14's cache carrying
an unparameterised ligand, which appeared in **no durable record at all**. They were dropped before a
refinement attempt, and this file records attrition only from the refinement stage onward.

> **Closed in round 18.** All four are now in `ref/research/data/em_fetch_attrition.tsv`, recorded as
> `unrecorded` rather than as rejections — the screen verdicts on them were computed in round 18 and
> are not why they were dropped at the time.

## Applied

> **No band changed.** `d_FSC_model` holds at 5 %, with its worst degradation corrected from
> +4.787 % to **+4.786 %** (a backfill rounding artefact, not a measurement) and 10BU **verified by
> byte-identical re-run**. Headroom 1.0448×, still the thinnest in the file. CC_mask bands unchanged.
>
> **The CC_mask degradation-rate question is closed as unanswerable at this sample size** — not
> explained. It needs ~20 entries per arm; rounds build 8–9.
>
> **7 of 20 `[benchmark]` rows are marked `⚠ partial record`**, 2 more as recoverable. The systemic cause
> — bench scripts that do not commit their entry sets — is documented in the registry's provenance
> section and left as the next round's work.
>
> **Attrition:** the ligand cause is now screened at fetch time. Both known causes are now off the
> expensive path.

## Scope limits

- **P0's falsification is not proof the rates are equal.** It is a failure to reject at n = 17.
  A real rate difference could exist and be invisible here; that is the point of the power table.
- The 3-round permutation test (p = 0.048) is **post-hoc**. Only the 15-vs-16 comparison was
  registered.
- **The registration of P1–P3 was not blind.** I had read the per-entry TSV, though I had computed
  nothing from it. That is weaker than a genuinely blind registration and is disclosed above rather
  than glossed.
- **Determinism now rests on two entries** (32FE round 16, 10BU round 17), both cryo-EM
  `real_space_refine`. A protocol with stochastic components on some other input class is not
  excluded.
- **The audit's verdicts are per-row judgements about the record, not re-measurements.** No tolerance
  was re-derived; a row marked `⚠ partial record` is not thereby wrong.
- The ligand screen is validated against `phenix.pdb_interpretation` on **37 models, all cryo-EM,
  all from rounds 14–16**. It is not validated on X-ray entries or on models with unusual
  linking/altloc conventions, and it checks *component presence* only — an entry could still fail
  interpretation for a reason this screen does not model.
- **The `<=12` round labels** on 9VXE, 13GH and 9TZY are a bound, not a fact: rounds 12 and 13 both
  report those failures as cumulative series totals without saying which round attempted them.
