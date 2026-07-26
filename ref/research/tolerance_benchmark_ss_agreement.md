# Tolerance benchmark — secondary-structure agreement (DSSP vs biotite P-SEA)

Settles the second clause of the `Secondary-structure agreement` `[template]` tolerance in
`ref/thresholds_and_standards.md`: "two independent assigners floor ≥ **0.80** on a well-ordered
model". `scripts/t15_ss_agreement.py` computes the metric but had only ever been run on the repo's
own 1SAR.

```bash
python3 scripts/bench_t15_ss_agreement.py --cache <dir> --json <out.json>
```

## Configuration

- **DSSP** (`mkdssp` 4.6.1) — Kabsch & Sander hydrogen-bond energetics.
- **biotite P-SEA** (1.7.1) — Labesse Cα-geometry method.

Three-state (H/E/C) agreement over residues both assign. This is one of the few tolerances where
cross-tool agreement means what it says: neither method can be derived from the other, and both are
non-cctbx.

**A latent bug had to be fixed first.** `mkdssp` 4.x sniffs its input format and gets it wrong on
**every** PDB file downloaded from RCSB, dying with "This file does not seem to be an mmCIF file"
followed by a cif-validator error naming a category from the entry's own header. It affects 1UBQ and
12LO alike, so the T15 script would have failed on any real input; it went unnoticed because the
only file it had ever been run on was PHENIX-written. `t15_ss_agreement.py` now routes the model
through `gemmi convert` first. Side effect worth recording: normalising 1SAR shifts its agreement
from 0.8639 to **0.8646**, because the rewrite changes which residues DSSP scores.

Test set: 16 well-known, well-ordered structures spanning fold class.

## Results

| Entry | agreement | concordant / scored | ≥ 0.80 |
|---|---:|---|---|
| 1MBN | 0.8497 | 130/153 | yes |
| 2CI2 | 0.8462 | 55/65 | yes |
| 1CRN | 0.8261 | 38/46 | yes |
| 9PAP | 0.8019 | 170/212 | yes |
| 1TIM | 0.7935 | 392/494 | **no** |
| 7RSA | 0.7903 | 98/124 | **no** |
| 4PTI | 0.7759 | 45/58 | **no** |
| 1LZ1 | 0.7538 | 98/130 | **no** |
| 1BNI | 0.7523 | 243/323 | **no** |
| 1UBQ | 0.7500 | 57/76 | **no** |
| 1HEW | 0.7364 | 95/129 | **no** |
| 2LYZ | 0.7287 | 94/129 | **no** |
| 1LYZ | 0.7209 | 93/129 | **no** |
| 1CA2 | 0.7070 | 181/256 | **no** |
| 2PTN | 0.6906 | 154/223 | **no** |
| 3EST | 0.6792 | 163/240 | **no** |

Median **0.753**, range 0.679–0.850. **4 of 16 meet the asserted 0.80 floor.**

## Findings

**1. The ≥ 0.80 floor fails on 12 of 16 well-ordered structures.** These are canonical, high-quality
entries — ubiquitin, lysozyme, trypsin, RNase A, carbonic anhydrase, triosephosphate isomerase. The
floor is not a slightly optimistic number; it is above the median by 0.05 and above the observed
maximum for three quarters of the set. A harness applying it as written would flag correct
assignments as disagreements on most inputs.

**2. It was set from the single most favourable example available.** The repo's 1SAR scores 0.8646 —
higher than *every* one of the 16 entries here. Same pattern as the clashscore ±1.0 (one 1SAR
observation) and the H-count ±0.1 % (one convention pair): a number generalised from n = 1.

**3. Agreement is fold-class dependent, which is mechanistically expected.** The four passing entries
are α-rich or small (1MBN myoglobin 0.850, 2CI2 0.846, 1CRN crambin 0.826, 9PAP 0.802); the worst are
β-rich proteases (3EST 0.679, 2PTN 0.691) and the mostly-β carbonic anhydrase (1CA2 0.707). P-SEA
infers strands from Cα geometry alone and DSSP from backbone H-bonds; they diverge most where strand
register and edge strands are ambiguous. A single floor across fold classes is the wrong shape.

## Does the floor discriminate? No — the metric is degenerate at the bad end

A floor that nothing fails is not a check, so the same measurement was run on models that *should*
score badly: the first model of a disordered NMR ensemble (2JZ4, the one that failed T17's
ordered-core test), and 1UBQ with Gaussian coordinate noise at 0.5, 1.0 and 2.0 Å.

| Model | agreement | SS content (DSSP H+E) | DSSP assignment |
|---|---:|---:|---|
| 16 well-ordered structures | 0.679 – 0.850 | **0.458 – 0.784** | real H/E/C mix |
| 2JZ4 model 1 (disordered NMR) | 0.7625 | 0.371 | C 188, E 111 |
| 1UBQ + 0.5 Å noise | 0.7368 | 0.105 | C 68, E 8 |
| 1UBQ + 1.0 Å noise | **0.8816** | 0.026 | C 74, E 2 |
| 1UBQ + 2.0 Å noise | **1.0000** | 0.000 | C 76 |

**The agreement metric is anti-correlated with quality at the bad end.** Destroying 1UBQ's backbone
*raises* its score: 0.75 intact → 0.88 at 1 Å noise → **1.00 at 2 Å**. The mechanism is plain in the
last column — as the model degrades both assigners stop finding secondary structure, and once both
label every residue `C` they agree perfectly. Three-state agreement saturates at 1.0 on a structure
with no structure.

So **no floor on agreement can work**. The degraded models span 0.74–1.00, overlapping the entire
well-ordered range and exceeding 14 of the 16 good structures. The old 0.80 floor would have passed
the 1 Å and 2 Å wreckage while failing ubiquitin, lysozyme and trypsin.

**What does discriminate is the SS content itself**: 0.458–0.784 for well-ordered structures versus
0.000–0.105 for the perturbed ones — a clean separation with no overlap. The disordered NMR model
sits between at 0.371, which is the right answer for a model that genuinely does contain β strands.

## Applied tolerance

> **Two independent assigners (DSSP vs biotite P-SEA): report agreement together with the DSSP
> secondary-structure content, and gate on the content, not on the agreement.**
>
> - **SS content (fraction of residues DSSP assigns H or E) must be ≥ 0.20** for the agreement number
>   to mean anything. Well-ordered structures run 0.46–0.78; coordinate-perturbed wreckage runs
>   0.00–0.11.
> - **Given adequate content, expect agreement ≥ 0.65** (16 well-ordered structures: median 0.753,
>   min 0.679), fold-class dependent — **α-rich ~0.80–0.85, β-rich ~0.68–0.72**.
> - **High agreement with low SS content is a failure signal, not a pass.** A model with no
>   secondary structure scores **1.0** because both assigners label everything coil. Never report the
>   agreement alone.
>
> The agent-vs-DSSP clause (≥ 0.85 three-state over DSSP-assigned residues) is **not** measured here
> and is unchanged: that compares an agent against one assigner, not two assigners against each
> other.

## Scope limits

- The 16 reference models are all X-ray and well-ordered by construction. The bad end is probed with
  4 degraded models (one disordered NMR, three noise levels), which is enough to show the metric
  saturates but not enough to calibrate where the SS-content gate should sit precisely; 0.20 is
  placed in the observed gap between 0.105 and 0.371, not fitted.
- One implementation of each method. STRIDE (a third assigner) is not installed, so "P-SEA is the
  outlier" versus "DSSP is" cannot be distinguished.
- The fold-class split is by inspection of 16 structures, not a controlled comparison over a
  fold-classified set.
- Versions: mkdssp 4.6.1, biotite 1.7.1, gemmi 0.7.5 (for input normalisation).
