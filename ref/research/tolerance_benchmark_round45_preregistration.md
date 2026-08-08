# Round 45 — pre-registration

Registered **before `bench_vs_deposited.py` is run over the named set**, in a commit containing no
results. This executes **P3b triage items #3 + #4** (`partial_record_triage.md`): the two
`vs_deposited` geometry-% rows that carry a `⚠ partial record (round 17 audit)` mark — the Ramachandran
**favored %** row and the Ramachandran/rotamer **outlier %** row. Both marks record the *same* defect:
the original 17-entry comparison drew its set from an **uncommitted `--ids-file`**, so the entries cannot
be re-identified and **no per-entry favored/outlier value was written down anywhere**. One script over
one set backs both rows, so this is one round, not two.

## No tolerance value changes

The bands are **unchanged**: Ramachandran favored **± 0.2 pp**, Ramachandran outlier **exact match**,
rotamer outlier **± 0.5 pp**. Round 45 touches only the **record** — it moves the evidence from a lost,
uncommitted set onto a named, committed one and writes down the per-entry values. This is a
record-integrity re-basing in the round-42/44 mould, not a re-fit. (`bench_vs_deposited.py` also emits
R-free and completeness; those rows are not partial and are out of scope here, though the committed JSON
will carry them.)

## The set — already named and committed

The re-basing set is the **union of the committed named X-ray entries from rounds 37/38/41**, listed in
`ref/research/data/round{37,38,41}_xray_deltas.json`: **42 unique deposited protein X-ray entries**

```
12CI 12OC 14ZZ 15C8 1A0C 1B9B 1BDJ 1OWJ 1RH7 1TIJ 1VYJ 1W1I 1ZY2 2I4M 2IEF 2IY0 2QIZ 2QTU 2YOL 3A01
3G7M 3MIU 3ZM5 4DYT 4FN9 4MH1 4NJD 4Q9R 4W7P 5DZK 5MAC 5T9A 5URQ 5X6C 6ABT 6LE5 6QGY 6TPW 7D6N 7LMC
7P4U 7PLN
```

Choosing this set — rather than a fresh fetch — is deliberate: it is the **same named basis rounds
42/44 already used** for the refinement bands, so the vs-deposited geometry-% rows come to rest on the
same committed entries as the rest of §4. It is 42 vs the lost 17, so the named basis is *more*
comprehensive. The set is fixed by this file; it was not selected after seeing any result.

`bench_vs_deposited` compares a **local `phenix.ramalyze`/`phenix.rotalyze` run on the deposited model**
against that entry's **wwPDB validation report** — a deposited-reference reproduction check, independent
of refinement, so any deposited protein X-ray entry with a validation report is admissible. Entries
whose validation report lacks a usable `rama=` count (or that fail to fetch) will be **excluded and named
explicitly** in the results — no silent drop.

## Method

```
python3 scripts/bench_vs_deposited.py --ids-file round45_ids.json \
    --cache <cache dir> --json ref/research/data/round45_vs_deposited.json
```

pinned `phenix-2.0-5936` (same-binary; the pin has not moved since round 5). Canary **one entry**
end-to-end first — verify the JSON row is on disk with non-null favored/outlier fields — before the
batch. Commit `round45_vs_deposited.json` (per-entry) so both rows become re-derivable, and record the
favored-% agreement (median / p90 / max |Δ|), the Ramachandran outlier exact-match count, and the
rotamer outlier max |Δ|.

## Predictions — registered blind (nothing is computed yet)

**P1 — the favored ± 0.2 pp band holds on the named set: median |Δ| ≤ 0.2 pp.** *(confidence 80 %.)*
The round-17 set gave median 0.00, p90 0.02, max 0.16 pp; favored % is never degenerate, so all 42
entries are informative. *Falsified* if median |Δ| > 0.2 pp — which would put the band itself in
question, not just its provenance.

**P2 — the named max favored |Δ| is the weak direction and may exceed 0.2 pp on a single entry.**
*(confidence 65 % that at least one entry exceeds 0.2 pp.)* This is the explicitly-named weak
direction: the set includes several **old, low-completeness entries** (1A0C, 1B9B, 1BDJ, 1OWJ, 1TIJ,
1W1I, 1ZY2) whose altloc / missing-residue handling can differ between a local ramalyze and the
deposited report. A single entry over 0.2 pp does **not** falsify the band (P1 is median-based); it is
recorded as the entry to watch. A *max* far above 0.2 (say > 1 pp) on multiple entries **would**.

**P3 — Ramachandran outlier % reproduces exactly (Δ = 0.00 at 2 dp) on the entries with nonzero
outliers.** *(confidence 75 %.)* The round-17 evidence was 4 nonzero entries all exact; this is the
robust half. *Falsified* if any nonzero-outlier entry disagrees at 2 dp.

**P4 — rotamer outlier |Δ| ≤ 0.5 pp, max < 0.5 pp.** *(confidence 70 %.)* Round 17 saw max 0.34 pp;
rotamer is the looser of the two (sidechain completeness / altloc). *Falsified* if any entry exceeds
0.5 pp.

**P5 (met by construction) — every entry is named and its per-entry favored/outlier value committed.**
This is the actual objective. It cannot fail unless the batch fails to run; it is stated so the
record-integrity claim is explicit, not smuggled in with the numeric ones.

## Decision rule — registered before the data

- **P1, P3, P4 hold** (bands hold on the named set) → re-base both rows onto the committed named set,
  commit the per-entry JSON, and **resolve both `⚠ partial record` marks**, moving the registry from
  **15 → 17 fully backed, 5 → 3 marked**. No band value changes.
- **A band fails** (e.g. median favored |Δ| > 0.2 pp, or a nonzero-outlier entry disagrees) → do **not**
  quietly widen it. A band failing on a fresh named set is a **finding about the band**, written up as
  its own result with the offending entries named, and the mark stays until it is understood. Re-basing
  is only honest when the band it re-bases actually holds.
- **The round-21 caveat applies.** Re-measuring resolves the mark only because the lost members were
  **unremarkable** (favored % near-degenerate-free; outliers mostly 0.00) — the same precondition round
  21 set for the L-test. This is a fresh named set: it makes the tolerances rest on committed data
  (*reproducible*), it does not *corroborate* the lost 17 (a different, un-recreatable set).

## What this round cannot answer

- **Method-independence** — wwPDB's geometry percentages are MolProbity-derived, as are PHENIX's; this
  checks that a local run reproduces the deposited reference, not that two independent methods agree
  (already disclosed in both rows).
- **Whether a PHENIX upgrade moves these values** — same-binary, `phenix-2.0-5936` pinned (round 43
  registers that experiment).
- **The other partial rows** — #5 (H-placement) and the two RETAIN rows (#2 L-test, #6 EM map-model)
  are untouched; this round does #3 + #4 only.
