# Tolerance benchmark — CA RMSD and aligned-residue count (phenix.superpose_models vs TM-align)

Settles two `[template]` tolerances in `ref/thresholds_and_standards.md` that share a tool pair and
a precondition:

- CA RMSD |Δ| ≤ 0.10 Å **on the same residue selection**
- Aligned-residue count ± 2 residues **within one aligner class**

Both already warned that different aligners align different subsets. This measures how large that
effect is, and what remains once the selections agree.

Reproduce with:

```bash
python3 scripts/bench_t01_superposition.py --cache <dir> --json <out.json>
```

## Configuration

- **PHENIX**: `phenix.superpose_models fixed moving morph=False trim=False` → `Final <moving> RMSD:
  <rmsd> N: <n> of <m>`. Morphing and trimming are **off**: both deform the moving model to improve
  the fit, and TM-align is rigid-body, so leaving them on compares a deformed model against a rigid
  one. (With defaults on, the reported RMSD for 1UBQ/1UBI drops from 0.09 to 0.08 Å for this reason.)
- **TM-align**: `TMalign fixed moving -ter 0` → `Aligned length= <n>, RMSD= <rmsd>`.

Both are structure-based, so the aligned-count tolerance's "one aligner class" precondition holds —
this pairing is inside the class.

**`-ter 0` is the matched configuration.** By default TM-align stops at the first `TER` and aligns
the **first chain only**, while `phenix.superpose_models` matches all chains. Both settings are run
so the effect is measured rather than assumed.

Test set: 12 pairs of independently deposited structures — same protein re-deposited, same protein
in a different state, and one homolog pair (hen vs human lysozyme, ~60 % identity). Two pairs failed
and are reported below rather than dropped silently.

## Results

TM-align with `-ter 0`; ΔRMSD and ΔN are PHENIX − TM-align.

| Pair | TM-score | TM-align RMSD / N | PHENIX RMSD / N | ΔRMSD (Å) | ΔN | ΔN, TM-align default |
|---|---:|---|---|---:|---:|---:|
| 1A2P/1BNI | 0.993 | 1.08 / 324 | 1.58 / 293 | +0.50 | −31 | +185 |
| 4INS/1ZNI | 0.435 | 1.65 / 97 | 1.50 / 82 | −0.15 | −15 | +61 |
| 1MBN/1MBO | 0.987 | 0.61 / 153 | 0.46 / 152 | −0.15 | −1 | −1 |
| 1UBQ/1UBI | 0.999 | 0.09 / 76 | 0.09 / 76 | +0.00 | 0 | 0 |
| 1LYZ/1LZ1 | 0.962 | 0.76 / 129 | 0.78 / 129 | +0.02 | 0 | 0 |
| 2PTN/1TPO | 1.000 | 0.09 / 223 | 0.09 / 223 | +0.00 | 0 | 0 |
| 7RSA/5RSA | 0.999 | 0.15 / 124 | 0.15 / 124 | +0.00 | 0 | 0 |
| 1CA2/2CBA | 0.992 | 0.17 / 256 | 0.17 / 256 | +0.00 | 0 | 0 |
| 1HEW/1HEL | 0.998 | 0.21 / 129 | 0.21 / 129 | +0.00 | 0 | 0 |
| 3EST/1EST | 0.998 | 0.26 / 240 | 0.26 / 240 | +0.00 | 0 | 0 |

| Subset | n | median \|ΔRMSD\| | max \|ΔRMSD\| |
|---|---:|---:|---:|
| Same selection (ΔN = 0) | 7 | 0.00 | **0.02** |
| Different selection (ΔN ≠ 0) | 3 | 0.15 | **0.50** |

Failures, both PHENIX-side: **4PTI/5PTI** — `phenix.superpose_models` rejects 4PTI's
`HETATM ... UNK UNX` records for lacking an element in columns 77–78; **2TRX/1XOB** —
`AttributeError: 'NoneType' object has no attribute 'cluster_info_list'` inside the SSM matcher.
TM-align handled both pairs.

## Findings

**1. On a matched selection the two aligners agree to 0.02 Å — the ±0.10 Å tolerance is 5× looser
than the tools require.** Seven pairs land on identical residue counts, and six of those give
identical RMSD to two decimals. This is a genuine noise floor, not a coincidence of easy pairs: it
holds across RMSDs from 0.09 to 0.78 Å and across 76–256 aligned residues.

**2. Off a matched selection the tolerance is meaningless.** Three pairs disagree on which residues
to align, and their ΔRMSD runs to 0.50 Å — 5× the tolerance. Note **1MBN/1MBO**: a difference of a
**single residue** (153 vs 152) moved the RMSD by 0.15 Å. Selection is not a second-order correction
to this measurement; it dominates it, and one residue is enough.

**3. Most of the selection disagreement is chain multiplicity, and it is configurable.** With
TM-align's default (first chain only), ΔN reaches **185** residues on 1A2P/1BNI — PHENIX matched all
three barnase chains, TM-align one. With `-ter 0` the same pair drops to ΔN = 31. The residual is a
real alignment difference; the 185 was a settings artefact, and it is the kind that reads as a
catastrophic disagreement when nothing is actually wrong.

**4. ±2 residues holds where it can hold.** Seven of ten pairs agree exactly and one differs by 1.
The two failures (−15, −31) are multi-chain, multi-copy cases where the aligners genuinely choose
different subsets — not noise to be absorbed by widening the tolerance.

## Applied tolerances

> **CA RMSD: |Δ| ≤ 0.03 Å, and only when the two aligners report the same aligned-residue count.**
> If the counts differ — even by one — the RMSDs are over different atom sets and must not be
> compared; report both with their counts instead. Observed: 0.02 Å max on matched selections,
> 0.50 Å max on unmatched.
>
> **Aligned-residue count: ± 2 residues**, within one aligner class, **with matched chain handling**
> (`TMalign -ter 0` against a multi-chain-matching aligner). Confirmed: 7/10 exact, 1 pair off by 1.
> A larger difference is a real disagreement about the alignment, and is the signal to inspect it,
> not to widen the band.

CA RMSD tightens from ±0.10 Å to ±0.03 Å — with the same-count condition promoted from advice to a
gate, since it is what makes the tight number meaningful. The aligned-count tolerance keeps its ±2
and gains the chain-handling precondition.

## Scope limits

- 10 pairs, all X-ray, all single-domain or small multimers, TM-score 0.44–1.00. Remote homologs
  (TM-score < 0.4) and large multi-domain assemblies are unmeasured; the same-count condition is
  expected to fail far more often there, which pushes those comparisons into the "report both"
  branch rather than into a wrong number.
- Only one aligner from each side. `gemmi align`, ChimeraX `matchmaker` and US-align are documented
  alternatives in `ref/oracle_tools.md` and are not benchmarked here.
- The two PHENIX failures are real and unfixed; a test set assembled from a broader sample should
  expect a few percent of pairs to fail on the PHENIX side for input-parsing reasons.
