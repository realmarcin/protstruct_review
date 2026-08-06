# Tolerance benchmark — round 40: the crossing-quality mechanism is real, but the ratio was the wrong measure of it (#224)

**#224 is answered, and it closes.** The §4 `d_FSC_model` caveat — *the Δ may be least trustworthy
when the crossing sits far past the map's own resolution* — has been an untested n = 2 hypothesis since
round 22, and the ratio screen built to test it failed three ways (2-point leverage, fit confound
#234, empty candidate pool; `analyze_crossing_fence_viability.py`, #258). Round 40 stopped **selecting
on the ratio** and instead **measured crossing determinacy directly**, on 19 entries that already carry
a measured excursion — a ~5 GB re-analysis, no `real_space_refine`, no 50 GB screen. The mechanism is
**real**, the ratio was simply the wrong way to measure it, and a determinacy measure predicts the
excursion **robustly and independent of fit**.

The pre-registration is
[`tolerance_benchmark_round40_preregistration.md`](tolerance_benchmark_round40_preregistration.md); the
set, both determinacy measures and the committed excursion labels are in
[`ref/research/data/round40_dfsc_determinacy.json`](data/round40_dfsc_determinacy.json), produced by
`scripts/bench_dfsc_determinacy.py`.

## Result

| prediction | verdict |
|---|---|
| **P1** — D_perturb predicts \|excursion\| and survives dropping the two extremes (ρ ≥ 0.4) | **confirmed** — ρ = **0.792** without 9H7U + 10BU (0.505 with) |
| **P2** — the excursion is mostly jitter (\|excursion\| within ~2× of D_perturb) | **FALSIFIED** — excursion is **8–2900×** the perturbation shift |
| **P3** — the relationship survives controlling for fit (partial ρ ≥ 0.3) | **confirmed** — partial ρ = **0.818** |

## The decisive contrast

Two crossing-quality measures were computed per entry from the **deposited** model, with no refinement:
**D_perturb**, how far a fixed Gaussian coordinate perturbation (σ = 0.1/0.2/0.3 Å, two seeds) moves the
sustained crossing; and **D_width**, how flat the FSC curve is at the crossing. Spearman ρ against
\|excursion\|, on the identical 19-entry set:

| predictor | all 19 | 9H7U + 10BU removed |
|---|---:|---:|
| `d_FSC_model_pre / d_min` (the ratio) | +0.319 | **+0.049** |
| **D_perturb** (perturbation-recross) | +0.505 | **+0.792** |
| D_width (curve flatness) | +0.600 | +0.681 |

The ratio **collapses to +0.049** once the two entries it always rested on are removed — the same
2-point leverage `analyze_crossing_fence_viability.py` found over 36 entries, reproduced here. The
determinacy measures do the opposite: they **strengthen** without the extremes, and D_perturb's
extremes-removed ρ survives leave-one-out at **0.75–0.85** (no single entry carries it). So the crossing
quality genuinely predicts the excursion — the ratio was just a poor, extreme-dependent proxy for it.

## P3: it is not the #234 fit confound

#234 warned the ratio selects on model-map fit. Round 40 measures the mechanism instead of selecting on
it, and controls for fit directly. Fit alone predicts the excursion only weakly (ρ(cc_mask_pre,
\|excursion\|) = −0.41), and partialling it out barely dents D_perturb's correlation (0.792 → partial
**0.818**). The determinacy signal is not the fit confound wearing a different hat.

## P2 falsified: the excursion is real movement, not estimator jitter

The reframe's second half — that a poorly-determined crossing's excursion is mostly shell-quantisation
jitter — is **false**. A controlled 0.1–0.3 Å perturbation moves the crossing far *less* than refinement
did: for the high-ratio entries \|excursion\| runs **8× to 2900×** the perturbation shift (9H7U: 36.15 %
excursion vs a 0.012 % perturbation shift at σ = 0.2 Å; 10EU: 7.8×; 10EQ: 24×). So the large excursions are **genuine
model movement**, consistent with round 17's byte-identical reproduction of 10BU. D_perturb *ranks* the
entries by excursion well (P1) without *reproducing* the excursion magnitude (P2) — crossing quality
predicts which entries move most, it does not explain the movement away as noise.

## What changes: the §4 caveat, not the band

The `d_FSC_model` band value is unchanged (`× 1.05`). The **caveat** is rewritten: the n = 2 ratio
hypothesis is retired, replaced by a measured statement — the excursion magnitude is predicted by how
well-determined the crossing is (perturbation-recross ρ ≈ 0.79, independent of fit), and a large
predicted excursion is a **real degradation to check, not an artefact to discount**. See
`ref/thresholds_and_standards.md` §4.

## Why #224 closes here

The registered decision rule for **P1 holds, P2 fails** was: *the §4 caveat stands, now measured by
determinacy rather than by the ratio — still no rare-event screen; #224 closes as answered.* That is the
outcome. The project that needed ~330 screened entries and ~50 GB to fill a contaminated candidate pool
is resolved on **19 entries with existing labels**, because the redesign measured the mechanism instead
of hunting rare instances of it. #234's confound is dissolved (the determinacy signal survives
controlling for fit), and #258's closure recommendation is superseded by this answer — the ratio screen
is retired not because it is uneconomical but because a better measure exists.

## Scope limits

- **D_perturb is shell-quantised and coarse** — absolute values run 0.0007–0.049 Å, a fraction of a
  shell, and σ = 0.2 alone gives 0 for some entries. Only its **rank** is used (Spearman), which is what
  P1 and P3 test; no claim rests on the absolute magnitude. That the rank correlation is this strong
  *despite* the coarseness is evidence for the signal, not against it.
- **n = 19**, spanning ratio 1.372–0.676, all with committed excursions. Not a fresh refinement set —
  a new predictor tested against existing outcomes.
- **Same-binary.** `phenix-2.0-5936` pinned; whether a PHENIX upgrade moves the crossings is untested.
- **This predicts excursion *magnitude*, not direction.** Whether a large excursion is an improvement or
  a degradation is a separate question the band already handles (one-sided, `× 1.05`).
