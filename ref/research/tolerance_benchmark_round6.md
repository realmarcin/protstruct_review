# Round 6 — closing the three named blockers

Three items were carried as blocked or untestable. **Two of the three blockers were wrong**, and the
third turned out to be answerable a different way.

```bash
python3 scripts/bench_t14_flip_sets.py --ids-file <ids.json> --cache <dir> --json <out.json>
python3 scripts/bench_vs_deposited.py  --ids-file <ids.json> --cache <dir> --json <out.json>
python3 scripts/bench_refinement_deltas.py --cache <dir> --detection-test --json <out.json>
```

## 1. Flip sets vs an independent H builder — the blocker was the invocation

Round 3 recorded: "`mmtbx.reduce2` reports **no flip information**: zero occurrences of 'flip' in its
`.txt` log and no `USER MOD` records." That was true of the run, and wrong about the tool.

`reduce2` takes `add_flip_movers`, and it **defaults to `False`** — so the run never built flip
movers and had nothing to report. With `approach=add add_flip_movers=True` it reports every
flippable group's final pose:

```
AmideFlip at chain A GLN 2 NE2 Initial score: 13.30 final score: 13.30 pose Unflipped
HisFlip   at chain A HIS 55 ...                                        pose Flipped
```

So the comparison round 3 called impossible is not only possible, it is the one comparison in this
family that measures anything — `phenix.reduce` and standalone `reduce` are the same binary, while
`reduce2` is the cctbx reimplementation.

### Result

| Comparison | residues | flip-decision disagreements |
|---|---:|---:|
| `phenix.reduce` vs standalone `reduce` (same binary) | 634 | **0** |
| `reduce` vs **`mmtbx.reduce2`** (independent) | 639 | **48 (7.5 %)** |

Per model, the disagreement rate runs from 0 to **16.4 %** (30IZ, 12 of 73):

| Model | disagree / shared | | Model | disagree / shared |
|---|---|---|---|---|
| 30IZ | 12 / 73 | | 9HX9 | 5 / 82 |
| 9PN7 | 10 / 102 | | 9HW2 | 3 / 24 |
| 24MR | 8 / 134 | | 11AF | 3 / 13 |
| 9LK0 | 2 / 51 | | 30TW, 37AP, 37AS, 37BG, 28SV | 1 each |

**Finding.** The tolerance clause "same Asn/Gln/His flip set" is meaningful after all — but as an
*exact-match* requirement it is wrong. Two independent implementations disagree on roughly **1 in 13**
flippable residues, and on one model 1 in 6. Round 3's conclusion that the clause "checks nothing"
was an artefact of comparing a binary with itself; the correction is not that the clause is vacuous
but that it needs a rate, not an identity.

## 2. Rotamer favored % — no reference for the metric, but a reference for what it is built on

The blocker is real: the wwPDB validation report carries no favored/allowed verdict. Its
`ModelledSubgroup` elements expose `rota="mmm"` — the rotamer **name** — and nothing else, so a
favored percentage cannot be differenced against it.

What the report *does* give is the rotamer assignment itself, in the same MolProbity vocabulary
`phenix.rotalyze` prints (`A 1 MET:…:Favored:mmm` against `rota="mmm" chain="A" resnum="1"`). The
favored/allowed classification is derived from that assignment, so agreement on the assignment is
the strongest available evidence for the tolerance.

### Result

| | |
|---|---:|
| Entries | 17 |
| Residues compared | **8054** |
| Identical rotamer assignment | **8054** |
| Worst per-entry agreement | **1.000** |

**Finding.** The two pipelines assign the *same rotamer to every one of 8054 residues*. The
favored-% tolerance cannot be measured directly, but the quantity it is computed from is reproduced
exactly, so ± 1.0 pp is not at risk from assignment disagreement — the residual risk is confined to
how each pipeline draws the favored/allowed boundary for a given assignment, which neither exposes.

## 3. §4 refinement bands — the false-negative side

Round 5 calibrated only the false-positive side: how often a refinement that changed nothing gets
flagged. This does the converse. Each deposited model is damaged by known Gaussian coordinate noise
(σ = 0.05 … 1.0 Å) and the round-5 bands are asked whether they notice.

| σ (Å) | median Cα shift | caught by any band | clashscore ratio (post/pre) |
|---:|---:|---:|---|
| 0.05 | ~0.09 | **2 / 9** | 1.2 – 4.2× |
| 0.10 | ~0.17 | 9 / 9 | 8.5 – 77.2× |
| 0.20 | ~0.35 | 9 / 9 | 38.8 – 401.7× |
| ≥ 0.30 | ≥ 0.52 | 9 / 9 | up to 1073× |

For reference, the **null** re-refinements from round 5 gave clashscore ratios of **0.00 – 4.26×**.
Comparing those aggregate extremes would be misleading — the 4.26× null maximum and the 8.5× damage
minimum come from opposite ends of the clashscore range — so the separation is given **per model**:

| Model | pre | null ratio | σ = 0.1 damage ratio | margin |
|---|---:|---:|---:|---:|
| 30TW | 1.17 | 4.26× | 76.2× | 17.9× |
| 12LO | 1.18 | 0.00× | 77.2× | — |
| 30IZ | 1.83 | 2.09× | 59.9× | 28.7× |
| 37AP | 2.49 | 0.89× | 39.2× | 44.0× |
| 28SX | 4.24 | 3.45× | 23.3× | **6.7×** |
| 11AF | 6.65 | 0.97× | 16.7× | 17.2× |
| 28SW | 11.53 | 1.15× | 10.1× | 8.8× |
| 24MR | 13.61 | 0.80× | 8.5× | 10.5× |

Every model separates, with a worst-case margin of 6.7×.

**Finding A — there is a detection floor at ~0.1 Å.** At σ = 0.05, which moves Cα by about 0.09 Å,
**7 of 9 damaged models pass every band**. (The 2 that were caught were caught by the *Ramachandran
favored* clause, not by ΔRMSD — favored % occasionally notices sub-floor damage, but not reliably.) That is not a tuning problem: 0.09 Å is inside the
null-refinement spread (up to 0.107 Å), so no Δ band on these quantities can separate that damage
from ordinary refinement jitter. Degradation below ~0.1 Å Cα RMSD is invisible to §4 by construction,
and should be stated rather than left as an assumption of sensitivity.

**Finding B — the ΔRMSD band works but with little margin.** At σ = 0.1 the shift is ~0.17 Å against
a +0.15 Å band: it fires on 9/9, but a slightly smaller perturbation would slip under.

**Finding C — clashscore is the most sensitive signal, and round 5 gave up on it too readily.** At
σ = 0.05, where every other quantity is silent, clashscore already moves (1.2–4.2×). At σ = 0.1 it is
8.5–77×, while Ramachandran favored and rotamer outliers still register nothing. Round 5 removed the
clashscore gate because its null-case *difference* ranged over −2.70 to +10.39 — but as a **ratio**
the separation is clean:

- null re-refinement: **≤ 4.26×**
- σ = 0.1 damage: **≥ 8.5×**

so a ratio threshold in the gap between them is a real check where a difference band was not.

**Finding D — but the ratio gate has a validity limit, and it is not far away.** At σ = 0.1 Å the
damaged clashscore lands at **89–117 regardless of where it started** (1.17 → 89.20; 13.61 → 115.04).
The damage ratio is therefore approximately **100 / pre**, which means a 5× gate only fires while the
starting clashscore is **≲ 20**. A model deposited above that — the benchmark's own set already
reaches 13.6 — could be damaged at σ = 0.1 Å and not trip the gate. Above pre ≈ 20 the ratio is the
wrong statistic and the **absolute** post-clashscore against §2's quality bar is what still works: a
value near 100 is unambiguous however it is normalised.

## Applied

> **Asn/Gln/His flip sets: expect ≤ 10 % of flippable residues to differ** between independent H
> builders (measured 7.5 % over 639 residues, worst model 16.4 %). **Exact match is the wrong
> requirement** — it holds only when both sides are the same binary, which `phenix.reduce` and
> standalone `reduce` are. Use `mmtbx.reduce2 approach=add add_flip_movers=True` for a genuine second
> opinion; without `add_flip_movers` it silently reports nothing.
>
> **Rotamer favored %: keep ± 1.0 pp, unmeasurable directly.** The wwPDB report has no favored/allowed
> verdict. The underlying rotamer *assignment* is reproduced exactly — 8054/8054 residues over 17
> entries — so assignment disagreement is not a risk to the band.
>
> **§4 clashscore: gate on the ratio, not the difference — while `clashscore_pre ≲ 20`.**
> `clashscore_post / clashscore_pre ≥ 5×` is evidence of degradation; every model separates its null
> ratio from its σ = 0.1 Å damage ratio by at least 6.7×. **Above pre ≈ 20 the gate stops working**:
> damage drives clashscore to ~100 regardless of the starting value, so the ratio collapses towards
> 5× and below. There, compare the **absolute** post-clashscore against §2's quality bar instead. The
> *difference* stays ungated in all cases, as round 5 concluded.
>
> **§4 detection floor: degradation below ~0.1 Å Cα RMSD is not detectable** by any §4 clause —
> 7 of 9 models damaged at σ = 0.05 Å passed everything. State this alongside the bands; it is a
> property of the quantities, not a gap to be tuned away.

## Scope limits

- The flip comparison is `reduce` vs `reduce2` on deposited models, which are flip-optimised before
  deposition; a freshly built or perturbed model would exercise the decision boundary harder.
- Rotamer *assignment* agreement is not the same as *favored-%* agreement. Perfect assignment
  agreement bounds one source of disagreement and says nothing about the classification boundary.
- The detection test uses isotropic Gaussian noise on every atom, which is not what a bad refinement
  does — real degradation is correlated and localised. It establishes a detection floor in RMSD
  terms, not a model of realistic failure.
- 9 models for detection, 17 for flips and rotamers; one refinement protocol throughout.
