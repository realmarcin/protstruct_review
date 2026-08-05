# Round 36 — pre-registration

Registered **before any refinement is run**, in a commit containing no results.

## Why this round needs a registration rather than a decision

Round 35 found the crossing-quality fence is **confounded with model-map fit** (#234): 7DZX cleared it
at ratio 1.210 with a `cc_mask_pre` of 0.2083, worse than any of the 59 entries on record. Two of the
five entries ever above the fence are that second kind.

The fix is obvious — exclude entries that barely fit their maps — and that is exactly why it must be
registered. **Choosing the exclusion after seeing which entry it removes is fitting the criterion to
the data**, which this repo filed as #146 in round 26 and called P4 indeterminate for.

## The exclusion rule, fixed here

> **An entry is eligible only if `cc_mask_pre ≥ 0.6038`.**

Derived, not chosen: the **Tukey lower fence** on `cc_mask_pre` over the **59-entry record**, which is
the same rule and the same construction round 23 used to replace the post-hoc 1.3 ratio cut with the
data-driven 1.074 one.

    Q1 = 0.7577   median = 0.8053   Q3 = 0.8603
    fence = Q1 - 1.5 * (Q3 - Q1) = 0.6038

**Full disclosure of the order of events**, because it is the thing that could invalidate this: the
*need* for a fit criterion was recognised after seeing 7DZX. The *threshold* is computed from a
distribution that predates round 35 entirely, by a rule already precedented in this work, and it was
not tuned — no alternative was tried. It excludes 7DZX (0.2083) and 6PMJ (0.4297), and it would also
have excluded 7U0F (0.5928), whose ratio is 0.684 and which was never a candidate.

## What the exclusion leaves, and the problem it reveals

| entry | ratio | `cc_mask_pre` | eligible | Δ `d_FSC_model` | used to define the hypothesis? |
|---|---|---|---|---|---|
| 9H7U | 1.372 | **unrecorded** | undecidable | −36.150 % | **yes** |
| 10BU | 1.360 | 0.7577 | yes | +4.786 % | **yes** |
| 10EU | 1.076 | 0.7542 | yes | −1.084 % | no |
| 6PMJ | 1.094 | 0.4297 | **no** | not refined | no |
| 7DZX | 1.210 | 0.2083 | **no** | not refined | no |

**The eligible, non-circular candidate pool has exactly one member: 10EU** — and it already fails the
hypothesis's own 10× bar at −1.084 % against a 1.102 % threshold. One of 110 screened is **0.9 %**.

9H7U and 10BU are the two observations the hypothesis was built on. Testing it on them is circular,
which round 8's rule already forbids. 9H7U additionally cannot be checked against the exclusion at
all, because its `cc_mask_pre` was never recorded.

**Round 35 added 50 screened entries and zero eligible candidates.**

## Predictions

**P1 — screening to three eligible, non-circular candidates requires more than 200 further entries.**

The rates, all against the 110 screened to date, and the distinction between them is the point:

| population | count | rate |
|---|---:|---:|
| above the 1.074 ratio fence | 5 | 4.5 % |
| … and eligible (`cc ≥ 0.6038`) | 3 | 2.7 % |
| … **and non-circular** | **1** | **0.9 %** |

Only 10EU qualifies: 9H7U and 10BU *are* the observations the hypothesis was built on, so they cannot
also test it. At 0.9 % three such candidates needs **~330 screened in total — about 220 more** than
exist today, at ~155 MB and ~4 min each.

*Falsified* if a further screen of 50 yields two or more eligible, non-circular candidates.

The first draft of this prediction said "more than 150" and reasoned from the **2.7 %** eligible rate,
which silently counted 9H7U and 10BU — the two entries that define the hypothesis — as evidence for
it. Corrected before registering, and recorded because the conflation is precisely the circularity
this prediction exists to price.

**P2 — the eligible rate is lower than the unfiltered rate by at least a factor of two.**
Unfiltered: 5 of 110 = 4.5 %. Eligible: 3 of 110 = 2.7 % counting generously. *Falsified* if a further
screen puts the eligible rate above half the unfiltered one.

**P3 — `cc_mask_pre` and the ratio are NOT meaningfully correlated once poor fits are excluded.**
Round 35 measured r = −0.088 over 50, and +0.466 with one point removed — uninterpretable. Restricted
to eligible entries the correlation should be near zero, i.e. the confound is a **tail effect**, not a
gradient. *Falsified* if |r| > 0.3 among eligible entries at n ≥ 40. This matters: a gradient would
mean the fence cannot be rescued by an exclusion at all.

**P4 — 6PMJ, if refined, moves less than the 10× bar.**
It is ineligible under the rule registered above, so it is **not** part of the test. Registered anyway
because it is the one remaining unrefined entry above the ratio fence, and predicting its behaviour
in advance is free. *Falsified* if |Δ| ≥ 1.102 %.

## What this round will do

**Nothing expensive, and no refinement.** The exclusion rule is registered; whether to spend the
**~220 further screened entries** P1 prices is a decision for after P1 and P2 are testable, not
before. (This sentence said "~110" until the P1 correction above was applied and its body was not —
a fix moving a headline and leaving the body, caught in the same file that prices the error.)

Concretely: apply the eligibility rule to the committed record and the round-35 screen, publish the
eligible counts, and state the cost of continuing. **If P1 holds, the honest recommendation will be to
stop screening and record the hypothesis as unfalsifiable at this repo's scale** — the same conclusion
round 33 reached about the correction-rate question, arrived at by measurement rather than fatigue.

## What this round cannot answer

- **Whether the hypothesis is true.** One eligible non-circular candidate exists and it leans against.
- **Whether 9H7U is eligible.** Its `cc_mask_pre` is unrecoverable from the record; round 13 published
  `d_FSC` only. The strongest case for the hypothesis therefore cannot be checked against the
  criterion that protects it.
- **Whether 0.6038 is the right fence.** It is *a* principled fence, computed by precedent from data
  predating the round. A different rule would give a different number, and nothing here tests which
  separates the two populations best.
- **Whether the two populations are really two.** #234 argues from four points that poor-fit and
  genuine high-ratio entries are distinct kinds. That is a hypothesis about a confound, not a
  measurement of one.
