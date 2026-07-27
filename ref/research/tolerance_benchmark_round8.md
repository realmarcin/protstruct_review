# Round 8 — the four narrow items

One result **corrects a diagnosis published in round 7**; one validates a band that was previously
an assumption; two are bounded negatives.

```bash
python3 scripts/bench_refinement_deltas.py --cache <dir> --json <out.json>            # null
python3 scripts/bench_refinement_deltas.py --cache <dir> --restraints --json <out>    # restrained
```

## 1. The 2.5 Å split — filled in, and it holds

Round 7 split the §4 bands at `d_min = 2.5 Å` on 5 entries below and 14 above, with **nothing between
2.92 and 3.00 Å** and only one point between 2.5 and 2.9. Adding 7 entries at **2.30–2.89 Å** brings
the set to **26 entries spanning 1.37–3.60 Å**, with the boundary region now populated
(2.30, 2.32, 2.45, 2.47, 2.52, 2.52, 2.55, 2.59, 2.60, 2.89 Å).

| d_min bin | n | Cα shift median | max |
|---|---:|---:|---:|
| < 2.0 Å | 3 | 0.031 | 0.045 |
| 2.0–2.5 Å | 5 | 0.068 | **0.075** |
| 2.5–3.0 Å | 7 | 0.106 | **0.172** |
| 3.0–4.0 Å | 11 | 0.116 | 0.285 |

The dependence is **smooth, not a step** — correlation of `d_min` with Cα shift is **0.589** — but the
transition does happen near 2.5 Å: the largest shift below is 0.075 Å and the first entry above
(31LC, 2.52 Å) is already 0.172 Å.

**A resolution-scaled band was tested and is not better.** Envelope violations over the 26 entries:

| Candidate | Cα shift | favored drop |
|---|---:|---:|
| Two-band step (0.10 / 0.35 Å; 0.5 / 6 pp) | **0 / 26** | **0 / 26** |
| Scaled `0.15 × (d_min − 1.0)` | 0 / 26 | — |
| Scaled `0.12 × (d_min − 1.0)` | 1 / 26 | — |
| Scaled favored `3.0 × (d_min − 1.5)` | — | 2 / 26 |

For Cα shift the scaled and stepped forms tie; for favored drop every scaled form tested fails while
the step covers all 26. **The two-band step is kept**, now validated on a set that fills its own
boundary rather than straddling a gap.

## 2. Low-resolution restraints — the bands are conservative by 20–36 %

Round 7's low-resolution null spreads came from `phenix.refine` with default weights and **no NCS or
secondary-structure restraints** — not how a 3.5 Å structure would be refined. Re-running the 11
low-resolution entries with `ncs_search.enabled=True secondary_structure.enabled=True`:

| | unrestrained max | restrained max | median change | improved / worsened |
|---|---:|---:|---:|---:|
| Cα shift | 0.285 Å | **0.227 Å** (−20 %) | **−0.0067 Å** | 8 / 3 |
| Favored drop | 5.26 pp | **3.35 pp** (−36 %) | **−1.23 pp** | **10 / 1** |

The maxima alone would be one entry out of eleven each, so the distribution matters: the effect is
broad, not an outlier. For Ramachandran favored it is in fact *larger* than the headline suggests — a
median 1.23 pp recovery against drops running 0–5.26 pp — while for Cα shift 3 of 11 entries got
slightly *worse* with restraints, which a "−20 %" figure hides.

The restraints demonstrably engaged: the refinement logs report `Found NCS groups: … Number of NCS
groups: 1` and secondary structure read from the input model.

(Reference-model restraints are deliberately excluded: they restrain to a higher-resolution homolog,
which this benchmark does not have, and pointing them at the input model would restrain it to itself.)

**The published bands are kept at the unrestrained values.** The harness cannot assume which protocol
produced a model it is asked to check, and a band fitted to restrained refinement would flag
correctly-run unrestrained refinements. The 20–36 % headroom is the price of that generality, and a
harness that *knows* the refinement used resolution-appropriate restraints may tighten accordingly.

## 3. `d_FSC_model` coverage — round 7's diagnosis is NOT supported

Round 7 concluded from two EM entries that the degenerate model-map FSC is "a model-to-map coverage
problem", 9VJD having 27 atoms per 10⁶ Å³ of map box against 27WR's 813. Four more entries were
added:

| Entry | atoms | box (10⁶ Å³) | atoms / 10⁶ Å³ | d_FSC_model(0.143) | plausible? |
|---|---:|---:|---:|---:|---|
| 10QT | 78939 | 28.27 | 2792 | 2.99 Å | yes |
| 24UM | 4580 | 2.73 | 1676 | 2.56 Å | yes |
| 27WR | 2220 | 2.73 | 813 | 2.62 Å | yes |
| 10GX | 30100 | 55.22 | 545 | 2.69 Å | yes |
| **21BQ** | 2580 | 36.39 | **71** | **2.62 Å** | **yes** |
| **9VJD** | 1186 | 44.09 | **27** | 29.65 Å | **no** |

**21BQ sits at 71 atoms per 10⁶ Å³ — within a factor of 2.6 of the failing entry — and produces a
perfectly sensible `d_FSC_model`.** So coverage does not predict the failure. Round 7's diagnosis was
a correlation drawn from n = 2, exactly the failure mode this benchmark series keeps finding in
other people's numbers.

**Corrected statement:** `d_FSC_model` is degenerate on **1 of 6** EM entries tested; the cause is
**not identified**. Low coverage is not sufficient to cause it (21BQ) and may not be necessary. The
clause stays ungateable, and any future coverage-conditioned version would need the mechanism
established first — the threshold cannot be placed between 27 and 71 on one failure.

## 4. Rotamer favored/allowed boundary — verified blocked

Applying the "a blocked item is a hypothesis" discipline from round 6, the claim that no independent
rotamer library is available was checked rather than assumed:

- every `molprobity.*` and `phenix.*` rotamer tool is cctbx, so not independent;
- **biotite** exposes only geometric helpers (`find_rotatable_bonds`, `rotate`, `rotate_about_axis`,
  `rotate_centered`) — no rotamer library or classification;
- **Bio.PDB** has no rotamer library;
- the local Richardson tools are `probe`, `reduce` and `tmalign` only.

The blocker is real. ± 1.0 pp remains contingent on the shared-library assumption bounded in round 7
(3.9 % of residues within ×1.25 of the cutoff).

## Applied

> **§4 resolution split at 2.5 Å: kept and validated** — 0/26 violations over 1.37–3.60 Å with the
> boundary region populated. A resolution-scaled band is no better for Cα shift and worse for
> favored drop.
>
> **Bands stay at the unrestrained values.** Resolution-appropriate restraints shrink the
> low-resolution null spread by 20 % (Cα) and 36 % (favored), so the published bands are conservative
> by roughly that much for correctly-restrained refinements.
>
> **`d_FSC_model` remains ungateable, cause unknown** — the round-7 coverage diagnosis is withdrawn.
>
> **Rotamer favored % ± 1.0 pp remains contingent**; no independent rotamer library exists locally,
> now verified rather than assumed.

## Scope limits

- 26 entries for the §4 bands, but only 3 below 2.0 Å — the high-resolution end of the split rests
  on few points, and its band (0.10 Å) is 2× the largest shift observed there.
- The restrained comparison uses one restraint recipe (NCS + secondary structure). Real
  low-resolution practice varies more.
- 6 EM entries for the coverage question, 1 failure. Enough to refute a threshold at ~27–71
  atoms/10⁶ Å³, not enough to find the real mechanism.
- All refinements are `phenix.refine`, 3 macro-cycles.
