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
| **P1** rotamer classification agreement essentially perfect | **confirmed** — rotamer **OUTLIER-verdict agreement 1.0000 on all 41**; the stricter exact-*name* agreement is 1.0000 on 40 and **0.9919 on 15C8** (3 insertion-code residues, both Favored, different rotamer names) |
| **P2** Ramachandran classification agreement essentially perfect | **confirmed** — **1.0000 on all 41** protein entries |
| **P3** raw-% exceedances are the altloc/completeness entries, and classification still agrees there | **confirmed** — all four (rotamer 14ZZ/2YOL, favored 1ZY2/4NJD) have classification agreement ≥ 0.99 |

Registered floor (≥ 0.99 of shared residues, disagreements named) **holds with margin** — the minimum
across both measures and all 41 entries is **0.9919**.

> **Correction from adversarial review.** The pre-registration disclosed Ramachandran agreement as
> "1.0000 on 40, 0.9976 on 15C8 — a boundary residue." Review found that 0.9976 was an **insertion-code
> keying artifact**: chain H position 100 of 15C8 holds three residues by icode (100 GLY, 100A HIS, 100B
> GLY), and a key of `(chain, resnum, resname)` collided the two GLYs (last-wins) while the `ramalyze`
> regex silently dropped the icode lines entirely. With the insertion code in the key and the parser
> (fixed here), Ramachandran agreement is **1.0000 on all 41**, and the coverage improvement instead
> surfaced a genuine, smaller **rotamer** signal on 15C8 (below). The floor still holds.

## What the check now is

The load-bearing vs-deposited geometry-% check is **per-shared-residue classification agreement**: for
the residues both pipelines evaluate, do they assign the same verdict? Keyed `(chain, resnum, resname)`,
exactly like the existing `rotamer_agreement`. Two measures, both computed from the report's own
per-residue verdicts and the `phenix` logs:

- **Rotamer** (`rotamer_agreement`, already present) — the **OUTLIER verdict agrees on all 41** (the
  measure captures it: `phenix.rotalyze` prints the rotamer-name field as the literal `OUTLIER` for an
  outlier, matching the XML's `rota="OUTLIER"`). The stricter exact-*name* agreement is 1.0000 on 40 and
  **0.9919 on 15C8**: three insertion-code residues — H/52A PRO (`t0` vs `Cg_exo`), H/82A SER (`mt` vs
  `p`), H/82B SER (`mt` vs `m`) — where the two pipelines assign a **different rotamer name but both call
  the residue Favored**. So the *outlier* classification agrees; only the finer rotamer-name assignment
  differs, on three alternate/inserted residues, and it is named (`rotamer_name_disagreements`).
- **Ramachandran** (`ramachandran_agreement`, added this round) — parses per-residue `Favored`/`Allowed`/
  `OUTLIER` verdicts from the XML `rama=` attribute and the `ramalyze` log, keyed with the insertion
  code. **1.0000 on all 41.**

The raw `|Δ|` bands (favored ± 0.2 pp, rotamer ± 0.5 pp, Ramachandran outlier ≤ 0.11 pp observed) are
**retained as reported diagnostics** in `round46_vs_deposited.json`, with the altloc/completeness caveat
and the named round-45 exceptions. They are no longer gates.

## Why this is the right basis

The raw-% agreement conflated two questions: *do the pipelines classify the same residues the same way?*
(the one the harness cares about) and *do they evaluate the same residue set?* (an artifact of altloc /
completeness handling). Classification agreement isolates the first. On 14ZZ, `phenix` and the report
agree on every one of the 402 shared rotamers yet the raw outlier % differs 1.52 pp purely because the
report scored 57 more altloc residues — a difference of *denominator*, not of *judgement*. A check that
fires on that is measuring the wrong thing. Classification agreement does not fire on the outlier
verdict (1.0000 on all 41), and the one place the stricter rotamer-*name* agreement dips below 1.0
(15C8's three insertion-code residues, all Favored) is a genuine, named, finer-grained difference in
*which* rotamer was assigned — exactly the kind of specific, per-residue signal the check should surface,
and nothing like the whole-percentage denominator noise it replaces.

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
