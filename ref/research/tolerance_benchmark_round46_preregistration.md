# Round 46 — pre-registration

Registered **before the vs-deposited geometry-% tolerances are re-defined**. This settles **#284**, the
band-semantics question round 45 opened: the raw favored-% and rotamer-outlier-% agreement bands are
**denominator-sensitive** — on altloc/incomplete entries `phenix` and the wwPDB report evaluate a
different residue *set*, so the raw percentage differs by more than the band even when they classify
every shared residue identically. The chosen direction (approved) is **classification agreement primary**.

## The tolerance change (this is the registered change)

For the three vs-deposited geometry-% rows (Ramachandran favored %, Ramachandran outlier %, rotamer
outlier %), the **load-bearing check becomes per-shared-residue classification agreement** — do the two
pipelines assign the same verdict to the residues they both evaluate? — keyed by `(chain, resnum,
resname)`, exactly as the existing `rotamer_agreement` already is. The **raw-% `|Δ|` bands are retained
as reported diagnostics**, not gates, with the altloc/completeness caveat and the named exceptions from
round 45. This makes the check measure what the harness actually cares about (do the pipelines agree on
classification) and robust to the denominator artifact.

## Method

Extend `bench_vs_deposited.py` with a `ramachandran_agreement()` measure parallel to the existing
`rotamer_agreement()`: parse per-residue Ramachandran verdicts (`Favored`/`Allowed`/`OUTLIER`) from the
validation XML's `rama=` attribute and from the `phenix.ramalyze` log, and report the shared-residue
agreement. Rotamer classification agreement already exists (`rotamer_agreement`, and it genuinely
captures the OUTLIER verdict — `phenix.rotalyze` prints the rotamer-name field as the literal `OUTLIER`
for an outlier, matching the XML's `rota="OUTLIER"`). Re-run over the **42 committed named entries**
(`round45_ids.json`; 41 protein, 12CI nucleic), pinned `phenix-2.0-5936`. Add unit tests for the new
parser. Canary one entry, then the batch.

## Predictions — figures disclosed (computed from the cached round-45 logs)

The agreement figures already exist in the round-45 cache, so — as rounds 38/42/44 did — they are
disclosed here rather than concealed; the **registered change is the tolerance re-definition and the
decision rule**, not the numbers.

**P1 — rotamer classification agreement is essentially perfect.** Observed **1.0000 on all 41 protein
entries** (every shared residue's rotamer verdict, OUTLIER included, agrees). *Falsified* if any entry
falls below the registered floor.

**P2 — Ramachandran classification agreement is essentially perfect.** Observed **1.0000 on 40/41**, with
**15C8 at 0.9976** — a single boundary residue the report calls one side of the Favored/Allowed line and
`ramalyze` the other. *Falsified* if the disagreement is larger or systematic (many entries, or an
OUTLIER-vs-Favored flip rather than a Favored/Allowed boundary).

**P3 — the raw-% exceedances are exactly the altloc/completeness entries, and only those.** rotamer
14ZZ (1.52 pp) / 2YOL (0.57 pp) both altloc; favored 1ZY2 (0.36, completeness) / 4NJD (0.28, altloc). On
all four, classification agreement is ≥ 0.99, confirming the exceedances are denominator, not
classification, differences.

## Registered floor and decision rule — before the data is re-run

- **Floor:** classification agreement **≥ 0.99** of shared residues (equivalently ≤ 1 % disagree), with
  any disagreeing residues **named**. Observed: rotamer 1.0000/41; Ramachandran 1.0000 on 40, 0.9976 on
  15C8 — so the floor holds with margin.
- **P1 + P2 hold** → adopt classification agreement as the load-bearing vs-deposited geometry-% check;
  demote the raw-% `|Δ|` bands to reported diagnostics with the altloc/completeness caveat. **Resolve
  the outlier row's `⚠ partial record` mark** (its record was committed in round 45; the only thing
  keeping it marked was the band question, now settled) — registry **16 → 17 fully backed, 4 → 3
  marked** — and clear the favored row's band caveat. Close #284.
- **A prediction fails** (agreement below the floor on some entry, or a systematic Ramachandran
  disagreement) → do **not** adopt; the classification check would itself be unreliable, and that is a
  finding about the check, written up with the entries named, mark stays.

## What this round does not do

- **It does not widen or retire the raw-% bands' values** — 0.2 pp favored and 0.5 pp rotamer stay on
  record as diagnostics; they are simply no longer the gate.
- **It does not change any other row** — H-placement (#5) and the two RETAIN rows (#2, #6) are untouched.
- **Same-binary** — `phenix-2.0-5936` pinned; a PHENIX upgrade could move the boundary residue (round 43
  registers the cross-version test).
- **Pipeline, not method-independent** — both pipelines are MolProbity-derived; this checks reproduction
  of the deposited reference's classification, not method independence.
