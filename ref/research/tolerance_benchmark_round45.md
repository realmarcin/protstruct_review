# Tolerance benchmark — round 45: the vs-deposited geometry-% rows re-based on named data; favored resolves, rotamer surfaces a band question

**No favored/Ramachandran band changes.** Round 45 re-runs `bench_vs_deposited.py` over the **42
committed named entries** (`round45_ids.json`, the union of the rounds 37/38/41 X-ray sets) to re-base
the two `⚠ partial record` `vs_deposited` rows onto a named, re-derivable set — **P3b triage items #3
(Ramachandran favored %) and #4 (Ramachandran/rotamer outlier %)**.

Pre-registered in [`tolerance_benchmark_round45_preregistration.md`](tolerance_benchmark_round45_preregistration.md)
before any figure was computed. The run was done **on the corrected instrument**: round 45 first
uncovered that `bench_vs_deposited` compared the rotamer outlier % against the wrong wwPDB endpoint
(#281, fixed in #282), so the outlier % is now counted from the report's per-residue `rota=`/`rama=`
verdicts. 12CI is nucleic acid (no protein Ramachandran/rotamer), so the geometry-% comparisons are over
**41 protein entries**; it is named here, not silently dropped.

## Result against the registered predictions

| prediction | verdict |
|---|---|
| **P1** favored median \|Δ\| ≤ 0.2 pp | **confirmed** — median **0.000**, p90 0.06, max 0.36 pp over 41 |
| **P2** favored max is the weak direction, may exceed 0.2 on a single entry | **confirmed** — only 1ZY2 (0.36) and 4NJD (0.28) exceed 0.2; both old/low-completeness, non-falsifying |
| **P3** Ramachandran outlier reproduces exactly (Δ=0.00) on nonzero entries | **partially** — 33/41 exact; 8 differ by **≤ 0.11 pp**. "Exact Δ=0" is too strong for 41 entries; the operational ±0.5 pp band holds with wide margin |
| **P4** rotamer \|Δ\| ≤ 0.5 pp, max < 0.5 | **falsified** — exact on **39/41**, but **14ZZ (1.52 pp)** and **2YOL (0.57 pp)** breach ±0.5, for a denominator reason (below) |
| **P5** every entry named, per-entry values committed | **met** — `round45_vs_deposited.json` |

## #3 favored — resolved

The Ramachandran favored comparison on the named 41-entry set: median \|Δ\| **0.000**, p90 0.06. The
favored row's `⚠ partial record` mark is **resolved** — the set is named and committed and the per-entry
values are written down (registry **15 → 16 fully backed, 5 → 4 marked**), because the round-45
pre-registration judged this row on the **median** (P1, held) and pre-declared single-entry
max-exceedance **non-falsifying** (P2).

**Honesty note — the favored band shows the same denominator-sensitivity as rotamer.** Two entries
exceed the ± 0.2 pp band: 1ZY2 (0.36, an old low-completeness entry) and 4NJD (0.28). This is the *same*
effect as the rotamer breach below — `phenix` and the report evaluating slightly different residue sets —
just smaller. It is "not a band failure" here **only because the pre-registration scored favored on the
median while scoring rotamer on the max**; the two exceedances are not qualitatively different from
14ZZ/2YOL. So the favored band's per-entry denominator-sensitivity is **folded into #284** alongside
rotamer's; what round 45 settles for this row is the *record* (named, committed), not that the raw-%
band holds on every entry.

## #4 outlier — Ramachandran reproduces; rotamer surfaces a real band question, so the mark stays

**Ramachandran outlier** reproduces to **≤ 0.11 pp** (median 0.000; the 8 nonzero deltas are 1VYJ 0.11,
1ZY2 0.11, 2I4M 0.06, then five at ≤0.02). The registry's "**exact match (Δ = 0), reproduced exactly on
17/17**" was true of the smaller round-17 set but does not generalise — it is restated as **≤ 0.11 pp on
the named 41**. The operational ±0.5 pp band holds comfortably.

**Rotamer outlier** reproduces **exactly on 39 of 41** entries. The two exceedances are **denominator,
not classification, differences**:

| entry | phenix.rotalyze | wwPDB (XML `rota=OUTLIER`) | Δ | rotamer *name* agreement | altlocs |
|---|---:|---:|---:|---:|:--:|
| 14ZZ | 3.49 % (evaluated 402) | 5.01 % (evaluated 459) | −1.52 | **402 / 402 identical** | A, B |
| 2YOL | 10.17 % (evaluated 40) | 9.60 % (evaluated 177) | +0.57 | **40 / 40 identical** | A, B |

Both entries carry **alternate conformations (altloc A/B)**; the clean Δ=0 controls do not. wwPDB
evaluates altloc sidechains that `phenix.rotalyze` does not, so the two pipelines score a **different
number of residues** (14ZZ: 459 vs 402) — and altloc sidechains are more often rotamer outliers (14ZZ:
23 vs 9). The disagreement is therefore **not a classification disagreement**: on 14ZZ every one of the
402 shared residues gets the identical rotamer name, and the outlier % still differs 1.52 pp purely
because wwPDB counted 57 more (altloc) residues. This is exactly the "sidechain completeness and altloc
handling that differ slightly between pipelines" the row already names as the reason rotamer is the
looser tolerance — but larger than round 17's max (0.34 pp) because that set contained no altloc-heavy
entry.

Per the round-45 decision rule, **a band that fails on a fresh named set is a finding, not a quiet
widen** — so the outlier row's mark **stays**. The finding is filed (rotamer outlier % is
denominator-sensitive under altloc handling; the classification agrees exactly, the raw % does not), for
a follow-up that decides whether the check should be **classification agreement** (which holds 41/41)
rather than raw-% agreement. The record-integrity half is done — the set is named and committed — but the
band question is not, so #4 is not claimed resolved.

## The historical "rotamer max 0.34 pp" is superseded

Registry row 90 read "Rotamer: ± 0.5 pp — confirmed, max observed **0.34 pp**." That figure was measured
in the round-17 era **against the buggy API field (#281) and on a set with no altloc-heavy entry**. On
the corrected instrument and the named 42-set the rotamer outlier % reproduces **exactly on 39/41**, with
a max \|Δ\| of **1.52 pp** (14ZZ) driven by altloc denominator differences. The 0.34 pp figure is
replaced by this named measurement; the ±0.5 pp band is retained as written but flagged as
denominator-sensitive pending the follow-up.

## Scope limits

- **Same-binary** — `phenix-2.0-5936` pinned; round 43 registers the cross-version test.
- **Pipeline, not method-independent** — wwPDB's percentages are MolProbity-derived, as are PHENIX's;
  this checks reproduction of the deposited reference, not method independence.
- **Reproduces, does not corroborate** — a fresh named set (the round-21 caveat): it makes the
  tolerances rest on committed data, it does not re-derive the lost round-17 set.
- **R-free / completeness** are emitted `n=0` here (no `model_vs_data` cache supplied); those rows are
  not partial and are out of scope for this round.
