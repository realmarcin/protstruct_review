# Tolerance benchmark — four tolerances against the wwPDB validation report

Settles, in one pass, `Ramachandran outlier %`, `Rotamer outlier %`, `R-free vs deposited` and
`Completeness (overall)` from `ref/thresholds_and_standards.md`.

```bash
python3 scripts/bench_vs_deposited.py --ids-file <ids.json> --cache <dir> \
    --mvd-cache <bench_t06 cache> --json <out.json>
```

## Configuration

The reference is the **wwPDB validation report**, which the trust model already names as the
tiebreaker:

| Quantity | Local | Reference |
|---|---|---|
| Ramachandran outlier % | `phenix.ramalyze` | validation XML → per-residue `rama="OUTLIER"` verdicts |
| Rotamer outlier % | `phenix.rotalyze` | validation XML → per-residue `rota="OUTLIER"` verdicts |
| R-free | `phenix.model_vs_data` | validation XML → `PDB-Rfree` (deposited) **and** `DCC_Rfree` (wwPDB-recomputed) |
| Completeness | `phenix.model_vs_data` | validation XML → `DataCompleteness` |

This is a **pipeline** comparison, not a method-independent one — wwPDB's geometry percentages are
MolProbity-derived, as are PHENIX's. What it tests is whether a local run reproduces the deposited
reference, which is exactly what these tolerances claim.

**Completeness was reported as data-blocked and is not.** The PDBe *experiment* API exposes a
`completeness` field that was null for all 10 entries checked; the validation report XML carries
`DataCompleteness` for every entry tested.

**One parsing trap.** The report's `<Entry>` attributes are hyphenated and prefixed —
`DCC_Rfree`, `absolute-percentile-DCC_Rfree`, `high-resol-relative-percentile-DCC_Rfree`. A
`(\w+)="..."` scan matches the *tail* of the prefixed ones and silently returns a percentile (1.36)
where an R-free (0.2358) was wanted. `entry_attribute()` anchors on a non-name character.

Test set: 18 entries with validation reports (of 24 attempted; 6 are mmCIF-only). R-free and
completeness are available for the 9 that also have a `model_vs_data` run.

## Results

> **Round 45 update (corrected instrument, #282).** The two *outlier %* rows below were measured in the
> round-17 era against `key_validation_stats`' `protein_ramachandran` / `protein_sidechains` — and the
> sidechain field is a broader metric inconsistent with the report's per-residue `rota=OUTLIER` verdicts
> (#281). On the corrected instrument (outlier % counted from the per-residue XML verdicts) over the
> **42 committed named entries** (`round45_ids.json`, 41 protein), Ramachandran outlier reproduces to
> **≤ 0.11 pp** (median 0.000) and rotamer outlier reproduces **exactly on 39/41**, with **14ZZ (1.52 pp)
> and 2YOL (0.57 pp)** breaching ±0.5 pp for an altloc denominator reason (rotamer *names* agree
> exactly). The **rotamer "max 0.34 pp" below is superseded** by that named measurement; the ±0.5 band's
> semantics are open in **#284**. See `tolerance_benchmark_round45.md`. The favored, R-free, and
> completeness rows are unaffected (favored was always counted from the XML; see Finding 1b).
>
> **Round 46 update (#284 closed).** The band question is settled: the load-bearing vs-deposited
> geometry-% check is now **per-shared-residue classification agreement** — do the pipelines assign the
> same verdict to residues they both evaluate? — robust to the altloc/completeness denominator
> difference. Rotamer OUTLIER-verdict agreement is **1.0000 on all 41** and Ramachandran verdict
> agreement (added in round 46, keyed with the insertion code) is **1.0000 on all 41**; the stricter
> exact rotamer-*name* agreement is 1.0000 on 40 and 0.9919 on 15C8 (three insertion-code residues,
> different names, all Favored — named). The raw-% `|Δ|` rows below are **retained as reported
> diagnostics**, not gates. See `tolerance_benchmark_round46.md`.

| Tolerance | n | median \|Δ\| | p90 | max | current band |
|---|---:|---:|---:|---:|---|
| Ramachandran outlier % | 17 | **0.00 pp** | 0.00 | **0.00 pp** *(round-17 measurement; superseded — the round-46 check is per-shared-residue verdict agreement, 1.0000/41, #284 closed)* | ± 0.5 pp |
| Rotamer outlier % | 17 | 0.00 pp | 0.00 | **0.34 pp** *(round-17 measurement; superseded — round-46 check is verdict agreement 1.0000/41; raw-% is a diagnostic, #284 closed)* | ± 0.5 pp |
| R-free vs **deposited** | 9 | 0.0020 | 0.0097 | **0.0128** | ≤ 0.02 |
| R-free vs **wwPDB-recomputed** | 9 | **0.0000** | 0.0033 | 0.0067 | — |
| Completeness | 9 | 0.05 pp | 0.10 | **0.11 pp** | ± 1 pp |

Per-entry R-free and completeness:

| Entry | PHENIX R-free | deposited | wwPDB DCC | Δ vs deposited | completeness (PHENIX / wwPDB) |
|---|---:|---:|---:|---:|---|
| 12LO | 0.2360 | 0.2340 | 0.2358 | +0.0020 | 98.46 / 98.50 |
| 30TW | 0.1916 | 0.2044 | 0.1949 | **−0.0128** | 99.69 / 99.61 |
| 9LK0 | 0.2474 | 0.2456 | 0.2474 | +0.0018 | 99.98 / 99.97 |
| 30IZ | 0.2381 | 0.2423 | 0.2381 | −0.0042 | 62.00 / 62.05 |
| 37AP | 0.2001 | 0.1940 | 0.2001 | +0.0061 | 100.00 / 99.98 |
| 24MR | 0.2710 | 0.2705 | 0.2707 | +0.0005 | 99.96 / 99.94 |
| 11AF | 0.2679 | 0.2776 | 0.2746 | −0.0097 | 99.23 / 99.13 |
| 28SW | 0.2951 | 0.2950 | 0.2951 | +0.0001 | 99.78 / 99.71 |
| 28SX | 0.2851 | 0.2850 | 0.2851 | +0.0001 | 99.44 / 99.33 |

## Findings

**1. Ramachandran outlier % is reproduced exactly — on n = 4 informative comparisons.** Zero
difference on 17 of 17 entries, but **13 of those are `0.00` vs `0.00`**: both pipelines agreeing a
good structure has no outliers, which cannot distinguish "they compute the same thing" from "there
was nothing to compute". The four entries with a nonzero value are the evidence:

| Entry | PHENIX | wwPDB |
|---|---:|---:|
| 24MR | 1.03 | 1.03 |
| 28SW | 1.06 | 1.06 |
| 28SZ | 0.70 | 0.70 |
| 9PN7 | 0.09 | 0.09 |

Agreeing to two decimal places on both the outlier count and the denominator is not luck, so the
tightening is justified — but it rests on four structures, and "exact" means *at the reported
precision*: both sources round to 2 dp, so sub-0.01 pp differences are invisible either way.
Rotamer is better evidenced: 12 of 17 nonzero, 10 exact, 2 differing.

**1b. Ramachandran *favored* % agrees to 0.16 pp.** Measured separately (and later — it was missed
in the first pass) by counting per-residue `rama="Favored" | "Allowed" | "OUTLIER"` verdicts in the
report XML, since `key_validation_stats` exposes outlier counts only. Median **0.00 pp**, p90 0.02,
max **0.16 pp** over all 17 entries. This evidence is stronger than the outlier row's: favored % sits
between 89 % and 100 % on real structures, so there is no 0.00-vs-0.00 degeneracy and all 17
comparisons are informative. The ± 1.0 pp band is ~6× too loose.

The **rotamer** favored % could not be measured the same way: the report's `rota=` attribute holds
the rotamer *name* (`m-10`, `mp`, `mt-10`, …) with no favored/allowed classification, and no
`rota="OUTLIER"` values appear at all. That half of the tolerance still has no wwPDB reference —
but round 6 established what the report *can* corroborate: the rotamer **assignment** itself is
identical for **8054 of 8054** residues across these 17 entries, in the same MolProbity vocabulary
`phenix.rotalyze` prints. Since the favored/allowed verdict is derived from the assignment, that
bounds one source of disagreement to zero and leaves only the classification boundary unverified.

**2. Rotamer outlier % is nearly exact**, with two exceptions: 30IZ (0.70 vs 0.50) and 9HW2 (0.87 vs
1.21), max 0.34 pp. The ± 0.5 pp band is about right here, and it is the looser of the two geometry
percentages for a reason — rotamer classification depends on the sidechain completeness and altloc
handling that differ slightly between pipelines.

**3. A local PHENIX run reproduces wwPDB's *recomputed* R-free almost exactly (median 0.0000, max
0.0067) but differs from the *deposited* value by up to 0.0128.** Those are two different references
and should not be conflated: `DCC_Rfree` is wwPDB re-deriving R-free from the deposited model and
data — the same thing `model_vs_data` does — while `PDB-Rfree` is whatever the depositor's own
refinement produced, with their software, their test set and their bulk-solvent treatment. Five of
nine entries match DCC to four decimal places. The ± 0.02 band is correct for the deposited
reference and roughly 3× too loose for the recomputed one.

**4. Completeness agrees to 0.11 pp.** The ± 1 pp band is ~10× too loose. Note 30IZ at 62 % —
agreement holds at low completeness too, so the tightening is not an artefact of easy cases.

**5. Third-source corroboration for clashscore.** The validation XML also carries wwPDB's clashscore.
Against the cctbx values measured in PR #28, over the 10 shared models: median |Δ| **0.00**, max
0.16 (12LO 1.18/1.18, 37AP 2.49/2.49, 11AF 6.65/6.65, 28SZ 9.64/9.64 exact). Three independent
pipelines — cctbx, standalone probe, wwPDB — now agree on clashscore far inside the ±1.0 band.

## Applied tolerances

> **Ramachandran outlier %: exact match expected (Δ = 0)** against a wwPDB validation report;
> investigate any difference. Observed 0.00 pp on 17/17 — but **13 of those compare 0.00 to 0.00**,
> so the informative evidence is the 4 entries with nonzero outliers, all exact. At 2 dp reported
> precision.
>
> **Rotamer outlier %: ± 0.5 pp** — confirmed, max observed 0.34 pp.
>
> **Ramachandran favored %: ± 0.2 pp** (max observed 0.16 pp over 17 entries), replacing ± 1.0 pp.
> **Rotamer favored % remains unmeasured** — no wwPDB reference exists for it.
>
> **R-free: |Δ| ≤ 0.02 vs the deposited value** (max observed 0.0128), but **|Δ| ≤ 0.01 vs
> `DCC_Rfree`**, the wwPDB-recomputed figure (max observed 0.0067, median 0.0000). State which
> reference is being used — they differ by more than the tolerance.
>
> **Completeness: ± 0.2 pp** vs the validation report's `DataCompleteness` (max observed 0.11 pp),
> replacing ± 1 pp.

## Scope limits

- MolProbity-derived on both sides for the geometry percentages, so this measures pipeline
  reproducibility, not method independence.
- R-free and completeness rest on 9 entries — the ones with both a validation report and a local
  `model_vs_data` run. The geometry percentages rest on 17 entries but only 4 (Ramachandran) and 12
  (rotamer) of those carry a nonzero value; the rest are 0.00-vs-0.00.
- Both sources report percentages to 2 dp, so every "exact" claim here means exact at that
  precision.
- 6 of 24 candidate entries are mmCIF-only and were skipped; the benchmark does not yet read mmCIF
  coordinates.
- Recent depositions only, so all reports come from a current wwPDB pipeline version. Older entries
  were validated by older pipelines and may agree less well.
