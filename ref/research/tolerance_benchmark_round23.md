# Tolerance benchmark — round 23: testing the crossing-quality hypothesis

Round 22 left one open item. `d_FSC_model`'s band rests on 10BU, and the candidate explanation is
that **its FSC crossing was poorly determined to begin with**: when the crossing sits far beyond the
map's own stated resolution, the curve is flat where it is read, so a small model change moves it a
long way. The two entries on record with `pre / d_min` > 1.3 are the two largest excursions in the
benchmark — but that is n = 2, and round 8's rule applies.

The successor test was specified because the predictor is measurable **before** refinement, so a set
can be selected on it without circularity. This round runs it.

## Design, and the feasibility problem it has to confront first

**There is no targeting shortcut.** Analysing the 36 existing measurements before designing this
round:

| d_min band | n | median `pre` | median ratio | n with ratio > 1.3 |
|---|---:|---:|---:|---:|
| 2.3–2.9 Å | 6 | 2.56 | 0.986 | 0 |
| 2.9–3.2 Å | 10 | 3.04 | 0.986 | 1 |
| 3.2–3.6 Å | 13 | 3.31 | 0.989 | 1 |
| 3.6–4.2 Å | 7 | 3.81 | 0.976 | 0 |

The median ratio is **~0.98 in every band** — the crossing tracks the map's stated resolution almost
exactly for typical entries — and the two high-ratio cases are scattered rather than concentrated.
`pre` is not floored at some fixed value either; it rises with `d_min`. **So high-ratio entries
cannot be enriched by choosing a resolution window.** They must be found by screening.

Base rate: **2 of 36 = 5.6 %**.

### What that costs, and whether the test is even possible

Screening is cheap relative to refining — a map download plus `mtriage`, no `real_space_refine` — but
it is not free, and the yield is low. Registering the arithmetic before spending anything:

- To expect **3** high-ratio entries requires screening ≈ **54**.
- To expect **2** requires ≈ 36. Screening **24** gives P(at least one) ≈ **75 %**, P(at least two) ≈ **39 %**.

And the comparison's own power, with perfect separation (every high-ratio entry above every control),
one-sided Mann–Whitney:

| high-ratio n | controls n | best achievable p |
|---:|---:|---:|
| 1 | 19 | 0.050 |
| **2** | **6** | **0.036** |
| 2 | 5 | 0.048 |
| 3 | 5 | 0.018 |

**So the test is feasible at 2 high-ratio entries against 6 controls, but only if separation is
perfect** — which is what the hypothesis predicts (a ~180× median gap), so it is a fair test rather
than a rigged one. At **1** high-ratio entry the test cannot reach significance against any control
group I can afford, and the round would have to report that instead.

This is round 17's lesson applied before the fact rather than after: **the power is computed first,
and the outcome where the round cannot answer the question is written down in advance as a real
possible result.**

### Method

```bash
# screen: fetch + mtriage only, no refinement
python3 scripts/fetch_em_entries.py --cache <dir> --min-res 2.4 --max-res 4.2 --limit 24 \
    --round 23 --exclude <every prior entry>
python3 scripts/screen_dfsc_ratio.py --cache <dir>     # d_FSC_model_pre / d_min per entry
# refine only the high-ratio entries plus matched controls
python3 scripts/bench_refinement_deltas_em.py --cache <dir> --entries <selected> --round 23
```

Selection is on a **pre-refinement** quantity, so it is not circular. Controls are drawn from the
**same screened batch**, so they share the fetch criteria and differ only in the ratio.

**Every screened entry is reported**, whether or not it is refined — the base rate is a result in its
own right and the denominator must not go missing (rounds 16–18).

## Predictions, registered before any fetching

| # | Prediction | Falsified if | P |
|---|---|---|---|
| **P0** | The base rate of `ratio > 1.3` in a fresh batch is **3–15 %**, consistent with the 5.6 % on record. | It falls outside that interval. | 70 % |
| **P1** | At least **one** high-ratio entry appears in 24 screened. | None does. | 75 % |
| **P2** | **The hypothesis:** every high-ratio entry refined has \|Δ\| **at least 10×** the control median. | Any high-ratio entry falls below that. | 55 % |
| **P3** | The controls' median \|Δ\| lands in **[0.02, 0.5] %**, replicating the 0.112 % of the ≤ 1.3 population. | It falls outside. | 70 % |
| **P4** | Screening finds at least one entry with `ratio > 1.3` whose Δ is an **improvement**, not a degradation — i.e. the effect is on \|movement\|, not on direction. | Every high-ratio entry degrades. | 50 % |

**P2 is the hypothesis and P4 is what distinguishes it from a band problem.** Round 22's two
high-ratio entries moved in *opposite* directions — 9H7U improved by 36 %, 10BU degraded by 4.8 %. If
crossing quality drives *magnitude* regardless of sign, then a poorly determined crossing is a
**measurement-reliability** caveat, not evidence the band is mis-sized. P4 tests that reading
directly.

**If P1 fails the round reports a base rate and nothing else**, and says so rather than reaching for
whatever the screened set happens to show.


## Results — the test could not be run, which was a registered possible outcome

**24 entries screened, 0 with `ratio > 1.3`.** No refinements were run, because there was nothing to
refine.

| # | Prediction | Outcome |
|---|---|---|
| **P0** | base rate 3–15 % | ❌ **falsified — 0.0 %** (but see below) |
| **P1** | ≥ 1 high-ratio entry in 24 | ❌ **falsified — zero** |
| P2 | high-ratio \|Δ\| ≥ 10× the control median | **unevaluable** — no high-ratio entries |
| P3 | control median \|Δ\| in [0.02, 0.5] % | **unevaluable** — no refinements run |
| P4 | at least one high-ratio entry improves | **unevaluable** |

Registered in advance: *"If P1 fails the round reports a base rate and nothing else."* That is what
this is.

### P0 was falsified as written, and the inference is the opposite of what that sounds like

I registered P0 as an interval on the **observed** rate. 0 % falls outside [3 %, 15 %], so it is
falsified — but **0/24 is entirely consistent with the 5.6 % prior rate**:

- Fisher's exact on 0/24 against the prior 2/36: **p = 0.512**.
- 95 % CI for the rate given 0/24: **[0 %, 14.2 %]**, which contains 5.6 %.
- P(seeing zero in 24 | true rate 5.6 %) = 0.944²⁴ = **25 %** — a one-in-four outcome.

So the honest reading is *"consistent with the prior rate; this batch happened to contain none"*, not
*"the rate is lower than thought"*. **P0 was the wrong shape of prediction** — an interval on a point
estimate rather than a test of consistency — which is round 17's lesson (*registering a prediction
does not protect you from registering a bad test*) recurring in a new form. P1, registered as a
straightforward count at 75 %, was well calibrated and failed honestly.

### The useful finding is the shape of the distribution

Combining this round's 24 with the 36 on record gives **60 measured crossings**, and the ratio is far
tighter than the 1.3 cut assumed:

| | n | median ratio | max |
|---|---:|---:|---:|
| prior | 36 | 0.9862 | 1.3718 |
| round 23 | 24 | 0.9736 | 1.0937 |
| **combined** | **60** | **0.9843** | — |

**The sustained-crossing estimator tracks the map's own stated resolution closely for most entries** —
**50 of 60** sit between 0.73 and 1.01, i.e. **83 %**, with a median of 0.9843. That is a new
characterisation of the estimator round 9 introduced. The ten outside the band are 36QD (0.674),
6O1M (0.676), 10EH (1.016), 10EP (1.033), 10EQ (1.044), 10ET (1.060), 10EU (1.076), 6PMJ (1.094),
10BU (1.360) and 9H7U (1.372) — a right-skewed tail rather than a symmetric spread.

It also reframes the threshold. A Tukey fence on the **combined** ratio distribution sits at
**1.074**, not 1.3 — and **four** entries clear it, not the three this round first reported:

| entry | ratio | Δ |
|---|---:|---|
| **10EU** | **1.0762** | **−1.084 %** — *already refined, round 16* |
| 6PMJ | 1.0937 | never refined |
| 10BU | 1.3598 | +4.786 % |
| 9H7U | 1.3718 | −36.150 % |

So the post-hoc 1.3 cut inherited from n = 2 was **too conservative**.

### The corrected fence puts existing evidence in play, and it leans against the hypothesis

**10EU was refined in round 16 and its Δ is on record.** Applying this round's own P2 criterion at the
corrected fence — |Δ| ≥ 10× the control median, i.e. ≥ **1.102 %** — 10EU's **1.084 %** *just fails
it*.

That is weak evidence, and it is evidence: at the data-driven threshold there is one already-measured
candidate, and it does not behave the way the hypothesis predicts. **The round's first draft said
"screening found no candidates; it did not examine any" — that was wrong**, and wrong in the direction
that flattered the hypothesis. It found no candidates *above 1.3*; at the threshold the data itself
suggests, one candidate was already in hand.

So the honest verdict is not "untested". It is: **untested at 1.3, and one near-miss at 1.074.**

### Why 6PMJ was not refined

It would not have been a test. One high-ratio entry against three controls gives a best achievable
one-sided p of **1/4 = 0.25** — the power table registered before this round shows a single candidate
cannot reach significance against any control group affordable here. Refining it would have added an
*observation*, not a *test*, and this series has spent four rounds learning to tell those apart.

That reasoning is unchanged by the correction above, but the corrected picture makes 6PMJ **more**
worth doing in a future round: with 10EU and 6PMJ both at ~1.08–1.09, a targeted set at the 1.074
fence has a base rate of **4 of 60 = 6.7 %** rather than 3.3 %, and two of its members are already
identified.

## What it would actually take

The cost is now known rather than guessed:

| | |
|---|---|
| combined base rate at ratio > 1.3 | **2 of 60 = 3.3 %** |
| at the data-driven fence 1.074 | **4 of 60 = 6.7 %** |
| entries to screen for **3** candidates | **~60–90** |
| cost per screened entry | one map download (100–250 MB) + `mtriage` (~2–5 min) |

**That is a project, not a round** — roughly 60–90 map downloads and several hours of screening before
a single refinement. The successor item is re-scoped accordingly rather than left as though it were
cheap.

## Applied

> **No band changed and no tolerance moved.** The crossing-quality hypothesis is **untested at the
> 1.3 cut**. At the data-driven fence of **1.074** it has one already-measured near-miss — 10EU,
> Δ −1.084 % against a 10× bar of 1.102 % — which leans mildly against it.
>
> **New, and worth keeping:** the crossing/resolution ratio over **60** entries has median **0.9843**
> with **50 of 60 (83 %)** in 0.73–1.01 and a right-skewed tail. The outlier fence is **1.074**, not
> the 1.3 inherited from n = 2, and **4 of 60** clear it.

## Self-review finding: a stale statistic, re-derived and confirmed

Reviewing this PR turned up something unrelated to the round's own work
([#107](https://github.com/realmarcin/protstruct_review/issues/107)). The registry characterised the
CC_mask rate question with figures computed in **round 17 on 25 entries**; round 19 added 10, so the
current data gives **35** and materially different numbers — Mann–Whitney p 0.32 → **0.18**, and
ρ(pre, Δ) −0.445 → **−0.506, p = 0.0019**. None carried its n, so all read as current.

**Re-running round 17's own robustness checks on the grown set confirms its verdict rather than
overturning it:**

| check | round 17 (n = 25) | now (n = 35) |
|---|---:|---:|
| ρ(pre, Δ) | −0.445, p = 0.026 | **−0.506, p = 0.0019** |
| ρ(mean, Δ) — Oldham | −0.279, p = 0.18 | **−0.281, p = 0.10** |
| ρ(post, Δ) | −0.05 | **−0.006** |

**The raw correlation strengthened and the corrected one did not.** That is exactly the signature
round 17 used to diagnose arithmetic coupling rather than an effect, now holding on 40 % more data —
a stronger result than round 17 could claim. The figures are updated and labelled with their n.

This is round 18's rule applied to statistics rather than clauses, and the second instance after #72.
A quoted statistic ages the moment the set grows, and nothing in the pipeline notices.

## Second self-review pass

An adversarial read of this PR found two more
([#108](https://github.com/realmarcin/protstruct_review/issues/108),
[#109](https://github.com/realmarcin/protstruct_review/issues/109)), both fixed above.

- **#108 (high)** — two miscounts. "57 of 60 within 0.73–1.01" is **50**; "3 of 60 above the 1.074
  fence" is **4**. The missing fourth is **10EU at 1.076, already refined in round 16**, whose Δ of
  −1.084 % *just fails* this round's own 10× bar. The error was visible in the round's own diagram,
  which printed `fence 1.074` and jumped to `1.094`. It mattered: the round had concluded "screening
  found no candidates; it did not examine any", which was wrong **in the direction that flattered the
  hypothesis**. Corrected to "untested at 1.3, one near-miss at 1.074".
- **#109 (medium)** — the fetch-interruption test did not test the fix. It exercised
  `append_fetch_record`'s dedup — unchanged code — and would have passed even if `flush()` had never
  been wired into the loop. Rewritten to drive `main()` and interrupt it, and **negative-tested**:
  removing the per-candidate `flush()` now fails the suite.

**Both are the same failure as rounds 20–22**: the arithmetic was fine and the claim built on it was
not. Here it went one step further — a miscount produced a conclusion more favourable to the
hypothesis under test than the data supported, which is the direction that matters most.

## Scope limits

- **The hypothesis is untested at the 1.3 cut, and has one near-miss at the corrected 1.074 fence.**
  10EU (ratio 1.076, Δ −1.084 %) just fails the round's own 10× bar. One entry is not a refutation,
  but it is not nothing, and the round's first draft wrongly claimed no candidate had been examined.
- **P0's falsification is an artefact of how it was written.** 0/24 is consistent with the prior rate
  (p = 0.512); the interval was on the wrong quantity.
- **The 1.074 fence is computed on the combined 60** and includes the two entries that motivated the
  hypothesis, so it is not independent of them.
- All 24 screened entries are recorded in `em_refinement_deltas.tsv` with a `screened only` status,
  carrying their pre-refinement crossing but no Δ — they are denominator, not evidence.
