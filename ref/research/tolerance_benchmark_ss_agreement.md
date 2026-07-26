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

## Applied tolerance

> **Two independent assigners (DSSP vs biotite P-SEA): three-state agreement ≥ 0.65**, not 0.80.
> Measured across 16 well-ordered structures: median 0.753, minimum **0.679**. Expect **α-rich folds
> ~0.80–0.85 and β-rich folds ~0.68–0.72** — agreement below ~0.65 indicates a genuinely disordered
> or mis-built model rather than normal method divergence.
>
> The agent-vs-DSSP clause (≥ 0.85 three-state over DSSP-assigned residues) is **not** measured here
> and is unchanged: that compares an agent against one assigner, not two assigners against each
> other.

## Scope limits

- 16 models, all X-ray, all well-ordered by construction — the floor is for the *easy* case. A
  disordered or low-resolution model would score lower, which is the point of a floor, but the
  benchmark does not establish where the "genuinely bad" boundary sits.
- One implementation of each method. STRIDE (a third assigner) is not installed, so "P-SEA is the
  outlier" versus "DSSP is" cannot be distinguished.
- The fold-class split is by inspection of 16 structures, not a controlled comparison over a
  fold-classified set.
- Versions: mkdssp 4.6.1, biotite 1.7.1, gemmi 0.7.5 (for input normalisation).
