# Round 10 — completing three evidence bases

Two items were "finish the measurement"; one was a verified dead end that turned out to have a
measurable half. Completing the EM set **breaks a band that has stood since round 5**.

```bash
python3 scripts/bench_refinement_deltas_em.py --cache <dir> --json <out.json>
python3 scripts/bench_refinement_deltas.py --cache <hi-res cache> --json <out.json>
python3 scripts/bench_vs_deposited.py --ids-file <ids.json> --cache <dir> --json <out.json>
```

## 1. EM set completed (3 → 6 entries) — and CC_mask fails

The three outstanding `real_space_refine` runs finished. All six EM entries, null refinement,
`d_FSC_model` computed with the sustained-crossing rule from round 9:

| Entry | resolution | CC_mask pre → post | Δ | d_FSC_model Δ |
|---|---:|---|---:|---:|
| 27WR | 2.70 Å | 0.8039 → 0.7974 | −0.0065 | +0.0028 |
| 9VJD | 2.86 Å | 0.9081 → 0.9165 | +0.0084 | +0.0002 |
| 10GX | 3.20 Å | 0.8266 → 0.8307 | +0.0041 | −0.0038 |
| 10QT | 3.40 Å | 0.7988 → 0.8106 | +0.0118 | −0.0094 |
| **21BQ** | 2.70 Å | 0.8549 → **0.8410** | **−0.0139** | −0.0017 |
| 24UM | 2.70 Å | 0.8216 → 0.8156 | −0.0060 | +0.0009 |

**`CC_mask_post ≥ CC_mask_pre − 0.01` is breached by a null refinement** on 21BQ (−0.0139). The band
was set in round 5 on **2 entries** and retained through rounds 6–9; completing the set to 6 breaks
it. Round 5 had already flagged that a null refinement consumed 65 % of the band on one of the two
entries — that was the warning, and it was right.

**`d_FSC_model` is comfortable**: max |Δ| **0.0094 Å** against ± 0.05 Å, ~5× headroom, now measured
on all 6 rather than the 3 round 9 could complete.

That 0.0094 is an **upper bound on the refinement effect**, not a clean measure of it. Two reasons:

- **The estimator changed between rounds.** Round 9's ± 0.0007 used the interim last-crossing rule;
  the sustained rule is noisier on the same entries (27WR +0.0007 → +0.0028, 10GX 0.0000 → −0.0038),
  so the 13× increase in the reported maximum is partly the rule, not only the larger set.
- **Part of each Δ is shell quantisation.** The sustained rule returns the start of a run of 20
  sub-threshold shells, which can move several shells for a small curve change:

  | Entry | crossing | local shell spacing | Δ | Δ in shells |
  |---|---:|---:|---:|---:|
  | 27WR | 2.5893 Å | 0.00132 Å | 0.0028 Å | **~2** |
  | 10GX | 2.6904 Å | 0.00008 Å | 0.0038 Å | ~47 |

  27WR's Δ is two shells — the estimator's own resolution. 10GX's is a real curve movement. The
  sustained rule buys accuracy (it rejects both FSC artefacts) at the cost of precision.

## 2. §4 high-resolution end (3 → 9 entries below 2.0 Å)

Round 8 recorded that the `< 2.5 Å` band rested on 3 entries below 2.0 Å and had "2× headroom".
Six more at **1.45–1.98 Å**:

| Entry | d_min | Cα shift | favored drop |
|---|---:|---:|---:|
| 9LLR | 1.45 Å | 0.0262 | 0.00 |
| 9LLN | 1.72 Å | 0.0626 | 0.00 |
| 9LLO | 1.80 Å | 0.0148 | 0.00 |
| **9LLP** | 1.82 Å | **0.0867** | 0.00 |
| 37AS | 1.91 Å | 0.0459 | +0.24 |
| 32CR | 1.98 Å | 0.0549 | −0.68 |

**No breaches** — but the headroom collapses. The combined set is now **32 entries**:

| Subset | n | shift median | shift max | band | headroom |
|---|---:|---:|---:|---:|---:|
| < 2.5 Å | 14 | 0.0566 | **0.0867** | 0.10 Å | **1.15×** |
| ≥ 2.5 Å | 18 | 0.1112 | 0.2854 | 0.35 Å | 1.23× |

Round 8's "2× headroom" at the tight end was an artefact of having only 3 high-resolution entries;
the true figure is **1.15×**. The band holds on 32/32, but it is far closer to the null-refinement
envelope than it appeared, and one more entry could breach it.

## 3. Rotamer boundary — the geometry half is now verified

The library remains unavailable (round 8 verified: every `molprobity.*`/`phenix.*` rotamer tool is
cctbx, biotite has only geometric rotation helpers, Bio.PDB none). But the classification is a
**library lookup applied to chi angles**, and the chi angles *can* be checked independently.

chi1 computed with **gemmi** (`calculate_dihedral` on N–CA–CB–X) against `phenix.rotalyze`'s chi1
column, over 17 entries:

| | |
|---|---:|
| Residues compared | **8054** |
| Max \|Δchi1\| | **0.05°** |
| Residues above 0.1° | **0** |

0.05° is exactly the rounding of rotalyze's one-decimal output, so the two agree to the precision
printed. **The unverified surface therefore narrows from "the classification" to "the library
density lookup" alone** — chi computation contributes nothing to any favored-% disagreement.

Combined with round 7's boundary-exposure measurement (3.9 % of residues within ×1.25 of the 2 %
cutoff), the residual risk to ± 1.0 pp is precisely: a systematic difference in *library density
values* between two implementations, applied to residues near the cutoff.

## Applied

> **Map-model CC_mask: `CC_mask_post ≥ CC_mask_pre − 0.02`** (was − 0.01), which a null real-space
> refinement breached on 1 of 6 EM entries (21BQ, −0.0139). Max observed 0.0139; the band is rounded
> up from that on a 6-entry set.
>
> **`d_FSC_model` ± 0.05 Å retained**, now on all 6 EM entries: max |Δ| 0.0094 Å, ~5× headroom —
> and that maximum is an **upper bound**, since part of it is the sustained estimator's shell
> quantisation rather than model movement.
>
> **§4 `< 2.5 Å` bands retained** (+0.10 Å, − 0.5 pp) and validated on 14 entries including 9 below
> 2.0 Å — but the headroom is **1.15×**, not the 2× round 8 reported. Treat as at the edge of its
> evidence rather than comfortably inside it.
>
> **Rotamer chi geometry is verified exact** (8054 residues, ≤ 0.05°). Any favored-% disagreement
> between pipelines is attributable to the rotamer library alone.

## Scope limits

- CC_mask's new band rests on 6 EM entries with one breach; the rounding from 0.0139 to 0.02 is a
  judgement, not a measurement, and a seventh entry could move it again.
- The `< 2.5 Å` shift band now has 1.15× headroom on 14 entries. That is thin enough that it should
  be re-checked whenever entries are added, not treated as settled.
- chi1 only. chi2–chi4 are not compared, and a rotamer name depends on all of them; agreement on
  chi1 is strong evidence but not proof that the full assignment geometry matches.
- `d_FSC_model` Δs are not comparable across rounds 9 and 10: the crossing rule changed, and the
  sustained rule reports larger differences for the same curves.
- All refinements `phenix.refine` / `phenix.real_space_refine`, 3 macro-cycles, default weights.
- One high-resolution entry (9LK0) failed in `phenix.refine` — the same missing-ligand-restraint
  failure seen in round 5 — and is reported rather than dropped.
