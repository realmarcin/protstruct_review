# Tolerance benchmark — Asn/Gln/His flip sets (phenix.reduce vs standalone reduce)

Closes the other gap PR #28 opened. The H-placement tolerance in
`ref/thresholds_and_standards.md` requires the two H builders to produce the "same Asn/Gln/His flip
set", but PR #28 measured only H count and clashscore, because `phenix.clashscore` does not emit flip
records. `reduce` does.

Reproduce with:

```bash
python3 scripts/bench_t14_flip_sets.py --ids-file <ids.json> --cache <dir> --json <out.json>
```

## Configuration

Both builders write `USER  MOD` records into the output PDB, one per flippable residue:

```
USER  MOD Single : A  32 GLN     :FLIP  amide:sc=   0.435  F(o=-0.2,f=0.44)
USER  MOD Single : A   2 GLN     :      amide:sc=   1.61   X(o=1.6,f=1.2)
```

The letter before `(o=` is the flip category — `F` flipped, `K` keep, `C` clashes either way,
`X` uncertain. Both the **decision** and the **category** are compared: an `X`-vs-`K` disagreement is
two builders hedging differently on an ambiguous residue, while `F`-vs-`K` is a real conflict about
the model.

Test set: 17 deposited X-ray models (the PR #28 set), **634** flippable Asn/Gln/His residues.

## Results

| | |
|---|---:|
| Models compared | 17 |
| Flippable residues compared | 634 |
| Models with identical flip calls | 13 / 17 |
| **Flip-decision disagreements** | **0** |
| Category-only disagreements | 1 |
| Residues recorded by only one builder | 6 |
| Residues flipped (PHENIX / standalone) | 56 / 54 |

The 2-flip difference in the totals comes entirely from the 6 residues that appear in only one
builder's records — among the 634 **shared** residues there is not a single decision disagreement.

## Findings

**1. The two builders are the same program.** Version strings are identical:

```
$ phenix.reduce -version   → reduce.4.16.250520
$ reduce -version          → reduce.4.16.250520
```

`phenix.reduce` is the Richardson `reduce` binary, redistributed. The flip sets agree perfectly
because there is only one implementation being run twice.

**2. So the "same flip set" clause checks nothing for this tool pair.** A tolerance clause that is
satisfied by construction gives false assurance: it reads as cross-tool corroboration and provides
none. It should be stated as a same-implementation identity check, and a genuine flip-set comparison
needs a *different* H builder — `phenix.reduce2` (the cctbx reimplementation) or Molprobity's
`reduce2` are the candidates on this machine.

**3. This also sharpens PR #28's clashscore result.** That benchmark measured a median 0.115
clashscore difference between the "cctbx path" and the "standalone path" under a matched H
convention, and left the cause open. Since both paths build hydrogens with the *same binary*, the
0.115 cannot come from H placement — it must come from the clash-counting step
(`phenix.clashscore`'s internal contact analysis vs the `probe` summation in
`scripts/bench_t05_clashscore_h.py`). The H-build convention still dominates when it is
*mismatched* (median 9.95); it is the matched-case residual that is now attributed correctly.

**4. Flips are rare in deposited models, which limits the test.** Only 7 of 17 models had any flips
at all, and one model (24MR) contributes 49 of the 56. Most deposited structures have already been
flip-optimised before deposition, so a set of deposited coordinates under-samples exactly the
residues this tolerance is about.

## Applied

> **Asn/Gln/His flip-set agreement**: exact-match expected — 0 disagreements over 634 residues —
> but **only because `phenix.reduce` and standalone `reduce` are the same binary
> (reduce.4.16.250520)**. Treat this clause as a same-implementation identity check, not as cross-tool
> corroboration. A meaningful flip-set comparison requires a genuinely independent H builder
> (e.g. `reduce2`), which is not yet benchmarked here.

## Scope limits

- One implementation, run twice, so this measures redistribution integrity rather than method
  agreement. That *is* the finding, but it means no cross-tool flip tolerance has been established.
- Deposited models are flip-optimised before deposition, so the 634 residues include few genuinely
  ambiguous cases. A perturbed or freshly-built model set would exercise the decision boundary much
  harder.
- 6 residues appeared in only one builder's records; the cause was not investigated (most likely
  altloc or occupancy handling at the record-writing stage).
- One version: reduce 4.16.250520 on both sides.
