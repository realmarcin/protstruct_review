# Round 44 — pre-registration

Registered **before the geometry row's clashscore figures are re-based**, in a commit containing no
results. Round 42 re-based the §4 geometry row's *favored* figure onto the 44 fresh named entries and
left the row marked `⚠ partial record` **only for its clashscore figures** — the 4.26× null ratio and
the "17.2 starting clashscore", both from the lost ~11 low-resolution entries. Round 44 finishes the
job (**P3b triage item #1**, `partial_record_triage.md`): re-base those two figures on the same 44/45
fresh named entries, resolving the row's last partial mark.

## No band value changes

The clashscore degradation gate is **unchanged**: `clashscore_post / clashscore_pre ≥ 5×` is degradation,
gated only while `1 ≲ clashscore_pre ≲ 20`, with the absolute §2 bar used outside that range. Round 44
touches only the **evidence figures** that support the gate — the observed null-ratio maximum and the
starting-clashscore ceiling — moving them from a lost set onto named data. This is a record-integrity
re-basing, not a tolerance change.

## Method

Over the fresh named X-ray entries (rounds 37/38/41, the same set round 42 used), compute:
- the maximum null clashscore ratio `post/pre` **within the gate's valid range `1 ≤ pre ≤ 20`**, and
- the maximum starting clashscore across all entries (the ceiling the gate's upper bound guards).

Computed by the committed `scripts/analyze_xray_band_coverage.py` (extended with a clashscore section),
so both figures are re-derivable. The set is already committed in `round{37,38,41}_xray_deltas.json`.

Selection ran before this file (the set is the round-42 set, unchanged) and the figures are disclosed in
the predictions below, as rounds 38/42 disclosed theirs — concealing an already-computed figure would
misrepresent the design.

## Predictions

**P1 — the fresh named max null ratio stays below 5×**, so the gate holds on a named basis. The lost set
gave 4.26× over 19 entries; the fresh named max is **4.25×** over 38 gate-valid entries. *Falsified* if
any fresh gate-valid entry reaches 5× (which would mean a correctly-behaving null re-refinement trips the
degradation gate, and the gate — not just its provenance — would need revisiting).

**P2 — the fresh named starting clashscore exceeds the lost 17.2**, making the named basis *more*
comprehensive than the lost one (the gate's upper bound at ~20 is now exercised by named entries).
Fresh max is **38.70**, with **7** fresh entries above pre = 20. *Not falsifiable in a meaningful
direction* — it is the reassurance that the lost "17.2 not reproducible" ceiling is not a limit of the
named data.

## Decision rule — registered before the data

- **P1 holds** (max < 5×): re-base the geometry row's clashscore figures onto the named set, **resolve
  the row's `⚠ partial record` mark** (its favored half was resolved in round 42; this is the other
  half), and move the registry count from **14 → 15 fully backed, 6 → 5 marked**. No gate value changes.
- **P1 fails** (some fresh entry ≥ 5×): do **not** re-base as a reassurance — a fresh named entry
  tripping the gate is a finding about the *gate*, registered separately, not a records fix.

## What this round cannot answer

- **Whether a PHENIX upgrade moves the ratio** — same-binary, `phenix-2.0-5936` pinned (round 43
  registers that experiment).
- **The other five partial-record rows** — triaged in `partial_record_triage.md`; this round does #1
  only.
- **Anything about the clashscore *difference*** — the row already records that it moves both ways and
  cannot be banded; only the ratio and the starting ceiling are re-based.
