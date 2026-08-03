# Tolerance benchmark — round 22: is 10BU explicable, and can a partial row be made regenerable?

Three standing risks were left after round 21, none of them an open task:

1. **Seven rows carry `⚠ partial record`** — each quotes a figure from a set that cannot be rebuilt.
2. **The §4 X-ray band widths rest on ~11 entries named nowhere.** Round 20 established these are
   unrecoverable; only a fresh low-resolution measurement could give those bands a checkable basis.
3. **`d_FSC_model` rests on one verified extreme** — 10BU at +4.786 %, **3.24×** above anything else
   on record and 30.6× the median.

This round takes (3) and (1). Risk (2) needs a new low-resolution X-ray refinement set and is left
alone rather than half-done.

## Item 1 — is 10BU explicable, or just extreme?

The band is `post ≤ pre × 1.05` and exists entirely for 10BU. Round 17 proved it reproduces
byte-identically, so it cannot be dismissed. Rounds 16 and 19 both hunted for a second large
degradation in the low-resolution regime and found none — worst +1.476 % and +0.277 %.

So the open question is not "is it real" but **"is it explicable"**. If some property of 10BU predicts
its excursion, the band could eventually be conditioned on that property rather than on one entry.

**Hypothesis: the crossing was poorly determined to begin with.** `d_FSC_model` is the resolution at
which the model–map FSC falls below 0.143 and stays there. When that crossing sits far beyond the
map's own stated resolution, the curve is flat and noisy where it is being read, so **a small change
in the model moves the reported crossing a long way.** 10BU's pre-refinement crossing is 4.35 Å for a
**3.20 Å** map.

### Disclosure of what I had already seen

I know 10BU's own numbers — pre 4.3513 Å at 3.20 Å, ratio **1.36** — because they appear throughout
rounds 17–21. What I have **not** computed is that ratio for any other entry, nor any correlation.
The predictions below are about the *other* 35 measurements, and P1 is stated as a rank rather than a
value precisely because 10BU's value was already in front of me.

### Registered scope limit: the arithmetic runs against the hypothesis

Round 17's P2 held as registered and was still wrong, because the predictor shared a term with the
outcome. The same check applies here, and this time it cuts the *helpful* way:

`d_fsc_model_delta_pct = (post − pre) / pre × 100`, and the proposed predictor is `pre / resolution`.
Both contain `pre`. A larger `pre` **inflates the denominator of the outcome**, which biases the
correlation **negative**. So a *positive* correlation would be found against the arithmetic bias, not
because of it — which is the opposite of round 17's situation and makes a positive result stronger
rather than weaker. Recorded before running it.

### Predictions

| # | Prediction | Falsified if | P |
|---|---|---|---|
| **P0** | **Gate:** 10BU is a statistical outlier among the degradation magnitudes — above Q3 + 1.5 × IQR. | It sits inside that fence, i.e. there is no anomaly to explain. | 85 % |
| **P1** | 10BU has the **highest** `d_fsc_model_pre / resolution` ratio of all entries with both values. | Any entry ranks above it. | 55 % |
| **P2** | \|`d_fsc_model_delta_pct`\| correlates **positively** with `d_fsc_model_pre / resolution` (Spearman, p < 0.05). | ρ ≤ 0, or p ≥ 0.05. | 45 % |
| **P3** | P2 survives **removing 10BU** — the relationship is not one point. | ρ ≤ 0 or p ≥ 0.05 without 10BU. | 30 % |

**P2 and P3 are the informative ones and I do not expect P3 to hold.** Three mechanism hunts in this
series have failed (rounds 7, 15, 17), and the honest prior is that this is a fourth. P3 is registered
separately from P2 precisely so that "the correlation exists but is carried by 10BU alone" is recorded
as a *failure* rather than written up as support.

**If P0 fails there is nothing to explain** and P1–P3 become decoration, exactly as round 17's P0
made P1–P3 decoration.

## Item 2 — make a partial row regenerable

Round 21 showed the route: a row whose set cannot be rebuilt can still be given figures **anyone can
regenerate**, by re-running on the committed subset. It also showed the ceiling — when the new set
overlaps the lost one, that is reproducibility, not corroboration, and the `⚠` mark stays.

Both candidates carry a committed partial set already:

| row | committed set | missing |
|---|---:|---|
| H-placement / flip sets | 12 of 17 | the 5 models with **zero** disagreements |
| Ramachandran favored % + outlier % | 11 of 17 | 6 entries, unnamed |

The flip-set row is the better target: its shortfall is **structured** rather than arbitrary. The five
missing models are exactly the ones that showed *no* disagreement, so the published aggregate
(48 disagreements over 639 residues, 7.5 %) has a known numerator and an unknown denominator — the
same shape as the L-test, and the same reason it might be recoverable in substance even if not in
membership.

No prediction is registered for item 2 until item 1's result is in; if the flip-set re-run happens
this round it gets its own registration first.
