# Round 40 — pre-registration

Registered **before any measurement**, in a commit containing no results. This is the **redesign of
#224** — a replacement for the crossing-ratio screen, chosen over closing the project (#258) or funding
the ~50 GB screen. It is independent of round 39 (which concerns the X-ray *favored* band); this round
concerns the EM `d_FSC_model` band.

## Why the ratio screen is being replaced, not extended

`scripts/analyze_crossing_fence_viability.py` (#257) established three failures of selecting on
`d_FSC_model_pre / d_min` above a fence:

1. **The signal is 2-point leverage.** `r(ratio, |excursion|)` is +0.587 over 36 entries but **+0.041**
   with 9H7U and 10BU removed — round 22's n = 2 on the full set.
2. **The confound (#234) is secondary to that.** Restricting to good-fit entries barely moves it
   (0.587 → 0.519); fit alone predicts the excursion only weakly (r = −0.30).
3. **The fresh candidate pool is empty**, and refilling it needs ~220 screened entries (~50 GB) for
   candidates that would still rest on the same two points.

The common cause is that the ratio is a **selection** criterion for a rare event. The redesign stops
selecting and starts **measuring the mechanism directly**, on every entry, from data already parsed.

## The reframe

The §4 caveat is really a claim about the **estimator**, not about a physical effect:

> *the Δ may be least trustworthy when the crossing starts far beyond the map's own resolution*

A model-map FSC crossing that sits on a **flat** stretch of the curve is poorly *determined*: the curve
hovers near 0.143 over many shells, so a small model change moves the reported crossing a long way, and
the pre→post "excursion" is then mostly **shell-quantisation jitter, not model movement**. The registry
already hints at this (*"part of each Δ is the sustained estimator's shell quantisation … 27WR's Δ is
~2 shells"*). So the testable quantity is **crossing determinacy**, measurable per entry with no
refinement and no rare-event screen.

## Two determinacy measures, both from existing tooling

Computed from `bench_refinement_deltas_em.read_fsc_curve()` (the per-shell curve the benchmark already
reads) and `bench_refinement_deltas.perturb()` (the Gaussian-noise perturber the X-ray detection test
already uses). Neither needs `real_space_refine` — the expensive, HPC-shaped step is removed.

- **D_width** — the resolution range (in 1/d) over which the masked model-map FSC stays within
  [0.143 − δ, 0.143 + δ] around the sustained crossing. Wider = flatter = less determined. Pure
  re-read of the deposited model's mtriage curve; **zero** extra tool runs per entry.
- **D_perturb** — perturb the deposited model by a fixed σ (0.1, 0.2, 0.3 Å; two seeds each), re-run
  mtriage, and record how far the sustained crossing moves. This is the crossing's sensitivity to a
  **known, controlled** model change — a within-entry measurement that isolates determinacy from the
  absolute fit level. Cost: a handful of mtriage runs per entry, no refinement.

## Test set

Entries with a **measured** `d_FSC_model` excursion already on record (`em_refinement_deltas.tsv`, 36
of them), whose map is recoverable, **chosen to span the ratio range** — including the two extremes
(9H7U, 10BU) and the near-miss (10EU), plus ordinary-ratio entries across the record. Target **≥ 15**.
Selection criterion registered here rather than a pre-picked list; the ids are committed with the
result, as in rounds 37–38. **No new refinements** — the excursions are the committed labels; only the
determinacy measures are new, so this is a re-analysis of existing outcomes, not a fresh benchmark.

## Predictions

**P1 — D_perturb predicts |excursion| and survives dropping the two extremes.** Spearman
ρ(D_perturb, |excursion|) ≥ 0.4 with **9H7U and 10BU removed**, where the ratio collapses to 0.04.
*Falsified* if ρ < 0.4 without the extremes. **This is the round's first question**: if determinacy
predicts the excursion where the ratio only did through two points, the mechanism is real and
measurable on any entry.

**P2 — the excursion is mostly jitter, not movement.** For the high-ratio entries, |excursion| is
within ~2× of D_perturb at σ = 0.2 Å — i.e. a controlled 0.2 Å perturbation moves the crossing about
as far as refinement did. *Falsified* if |excursion| exceeds D_perturb by more than 2× (the excursion
is real model movement past the estimator noise).

**P3 — determinacy predicts the excursion controlling for fit.** Partial ρ(D_perturb, |excursion| |
cc_mask_pre) stays ≥ 0.3, where the ratio's relationship was carried by the two points and not the
fit. *Falsified* below 0.3.

## Decision rule — registered before the data

- **P1 and P2 hold**: replace the §4 ratio caveat with a **determinacy report** — quote `d_FSC_model`
  alongside its curve-width / perturbation sensitivity, and do **not** gate a small excursion at a
  poorly-determined crossing. No ratio fence, no screen. #224 closes as *redesigned and answered*.
- **P1 holds, P2 fails**: determinacy predicts the excursion but the excursion is real movement beyond
  jitter. The §4 caveat stands, now *measured by determinacy* rather than by the ratio — still no
  rare-event screen. #224 closes as *answered*.
- **P1 fails**: the determinacy reframe does not predict the excursion either. #224 is then genuinely
  unanswerable at feasible cost and **closes** on the #258 recommendation. Recorded, not hidden.

## Cost, canary and stopping

- **Canary first (#canary):** one entry — **10BU**, the band's sole degradation — fetched, mtriaged
  deposited + perturbed, to confirm D_width and D_perturb are computable and non-trivial (a
  perturbation that moves the crossing by 0 shells would mean the measure has no dynamic range). Verify
  the artefact on disk before the set. Only then the spanning set.
- **~15 deposited maps × [1 mtriage + 6 perturbed mtriage] ≈ ~5 GB, ~1–2 hr**, no `real_space_refine`.
  Embarrassingly parallel; small enough for the workstation, and a job array on HPC if preferred (per
  #258's addendum).
- **Underpowered outcome stated in advance:** if fewer than 15 maps are recoverable, or D_perturb has
  no dynamic range on the canary, the round reports that and P1 is recorded as untestable here — a
  result, not a failure.

## What this round cannot answer

- **Whether a PHENIX upgrade moves the crossing.** `phenix-2.0-5936` pinned; same-binary evidence.
- **A new physical mechanism.** It distinguishes estimator jitter from model movement; it does not
  explain movement where movement is real.
- **The favored or Cα bands.** Out of scope — this is the `d_FSC_model` band only.
