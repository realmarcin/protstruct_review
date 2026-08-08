# Tolerance benchmark — round 46: classification agreement becomes the vs-deposited geometry-% check (#284)

Settles **#284**. Round 45 found the raw favored-% and rotamer-outlier-% agreement bands are
**denominator-sensitive**: on altloc/incomplete entries `phenix` and the wwPDB report evaluate a
different residue *set*, so the raw percentage differs by more than the band even when they classify
every shared residue identically. The chosen direction (approved) is **classification agreement primary**
— the check becomes per-shared-residue verdict agreement, and the raw-% `|Δ|` bands are demoted to
reported diagnostics. Pre-registered in
[`tolerance_benchmark_round46_preregistration.md`](tolerance_benchmark_round46_preregistration.md).

## Result against the registered predictions

| prediction | verdict |
|---|---|
| **P1** rotamer classification agreement essentially perfect | **confirmed** — **1.0000 on all 41** protein entries |
| **P2** Ramachandran classification agreement essentially perfect | **confirmed** — **1.0000 on 40/41**; **15C8 at 0.9976**, a single boundary residue |
| **P3** raw-% exceedances are the altloc/completeness entries, and classification still agrees there | **confirmed** — all four (rotamer 14ZZ/2YOL, favored 1ZY2/4NJD) have classification agreement ≥ 0.99 |

Registered floor (≥ 0.99 of shared residues, disagreements named) **holds with margin** — the minimum
across both measures and all 41 entries is **0.9976**.

## What the check now is

The load-bearing vs-deposited geometry-% check is **per-shared-residue classification agreement**: for
the residues both pipelines evaluate, do they assign the same verdict? Keyed `(chain, resnum, resname)`,
exactly like the existing `rotamer_agreement`. Two measures, both computed from the report's own
per-residue verdicts and the `phenix` logs:

- **Rotamer** (`rotamer_agreement`, already present) — 1.0000 on all 41. It genuinely captures the
  OUTLIER verdict: `phenix.rotalyze` prints the rotamer-name field as the literal `OUTLIER` for an
  outlier, matching the XML's `rota="OUTLIER"`.
- **Ramachandran** (`ramachandran_agreement`, added this round) — parses per-residue `Favored`/`Allowed`/
  `OUTLIER` verdicts from the XML `rama=` attribute and the `ramalyze` log. 1.0000 on 40; **15C8 0.9976**,
  the single disagreement named: **(H, 100, GLY) — report `Favored`, phenix `Allowed`**, a residue on the
  Favored/Allowed boundary. This is a real, tiny classification difference, not a denominator artifact.

The raw `|Δ|` bands (favored ± 0.2 pp, rotamer ± 0.5 pp, Ramachandran outlier ≤ 0.11 pp observed) are
**retained as reported diagnostics** in `round46_vs_deposited.json`, with the altloc/completeness caveat
and the named round-45 exceptions. They are no longer gates.

## Why this is the right basis

The raw-% agreement conflated two questions: *do the pipelines classify the same residues the same way?*
(the one the harness cares about) and *do they evaluate the same residue set?* (an artifact of altloc /
completeness handling). Classification agreement isolates the first. On 14ZZ, `phenix` and the report
agree on every one of the 402 shared rotamers yet the raw outlier % differs 1.52 pp purely because the
report scored 57 more altloc residues — a difference of *denominator*, not of *judgement*. A check that
fires on that is measuring the wrong thing. Classification agreement does not fire (1.0000), and the one
place it *does* drop below 1.0 (15C8's boundary glycine) is a genuine, named, single-residue difference —
exactly what the check should surface.

## The outlier row resolves

Round 45 committed the outlier row's record (named set, per-entry values) but left its `⚠ partial record`
mark because the rotamer ± 0.5 pp band was breached. That band question is now settled — the load-bearing
check is classification agreement, which holds — so the mark **resolves**. Registry **16 → 17 fully
backed, 4 → 3 marked**. The favored row's band caveat (round 45) is likewise cleared: its classification
agreement holds, and the 1ZY2/4NJD raw-% exceedances are diagnostics, not failures. **#284 closed.**

## Scope limits

- **The raw-% band *values* are not retired** — 0.2 pp / 0.5 pp stay on record as diagnostics; they are
  simply no longer the gate.
- **Same-binary** — `phenix-2.0-5936` pinned; a PHENIX upgrade could move 15C8's boundary residue (round
  43 registers the cross-version test).
- **Pipeline, not method-independent** — both pipelines are MolProbity-derived; this checks reproduction
  of the deposited reference's classification, not method independence.
- **No other row changes** — #5 (H-placement) and the two RETAIN rows (#2 L-test, #6 EM map-model) are
  untouched.
