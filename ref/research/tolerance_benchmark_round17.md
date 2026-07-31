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
