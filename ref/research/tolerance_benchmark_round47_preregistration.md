# Round 47 — pre-registration

Registered **before the flip-set comparison is run on named data**, in a commit containing no results.
This executes **P3b triage item #5** — the last resolvable `⚠ partial record`: the H-placement row's
Asn/Gln/His flip-set figure, **7.5 % (48 of 639 residues, 17 models, worst model 16.4 %)** for standalone
`reduce` vs `mmtbx.reduce2`, drawn from a set whose 0 %-disagreement members were never named and whose
17 ids cannot be recounted (`bench_t14_flip_sets.py` commits only 12).

## Why a fresh named set, not a subset re-run

Round 22 established that the **round-21 subset-re-run route does not transfer here and would mislead**:
the five lost models are exactly the **zero-disagreement** ones, so re-running the committed 12 would
reproduce all 48 disagreements over a *shrunken* denominator and report a rate **higher than 7.5 %** —
an artefact of which models survived, not a measurement. So round 47 does **not** re-run the old 17. It
takes the round-42/45 route instead: **retire the lost 17-model set and re-base the figure on a fresh,
fully named, committed set** — the 42 entries in `round45_ids.json` (rounds 37/38/41). A new set with its
own named denominator sidesteps the denominator-shrink trap entirely.

## Method

`python3 scripts/bench_t14_flip_sets.py --ids-file ref/research/data/round45_ids.json --cache <dir>
--json ref/research/data/round47_flip_sets.json`, pinned `phenix-2.0-5936`. It compares standalone
Richardson `reduce` against `mmtbx.reduce2` (`approach=add add_flip_movers=True`) on the per-residue
Asn/Gln/His flip decision **and** category (F/K/C/X), and also compares the H-atom count. Canary **one
entry** end-to-end — verify the JSON row carries flip-decision counts and that `reduce2` actually built
flip movers (not the silent add_flip_movers=off failure) — before the batch. Every entry that yields no
comparable flip records (no Asn/Gln/His, or a builder that fails) is **named and excluded**, not silently
dropped.

## No tolerance value change proposed

The band is **≤ 10 % of flippable residues may differ** between independent H builders. Round 47 re-bases
the *evidence* for that band onto named data; it does not move the band. (A record-integrity re-basing in
the round-42/45 mould.)

## Predictions — registered blind (nothing is computed yet)

**P1 — the flip-set disagreement rate on the named set stays under the 10 % band.** *(confidence 70 %.)*
The lost set gave 7.5 % overall. *Falsified* (for the band) only if the **aggregate** named rate exceeds
10 %, which would put the band itself in question.

**P2 — a single named model may exceed 10 % at the per-model level.** *(confidence 60 % that at least one
does.)* The lost set's worst model was 16.4 %; small flippable-residue counts make the per-model rate
high-variance. This is the named weak direction: one model over 10 % does **not** falsify the band (P1 is
the aggregate); it is recorded and named. Many models over 10 %, or an aggregate over 10 %, would.

**P3 — most disagreements are the weaker X-vs-K category (hedging on ambiguous residues), not F-vs-K
(genuine conflicts).** *(confidence 65 %.)* The row already distinguishes these; the benchmark records the
category, so the *kind* of disagreement is nameable, not just the rate.

**P4 (met by construction) — every model is named and its per-residue disagreements committed** in
`round47_flip_sets.json`. This is the record-integrity objective; it resolves what the mark records.

## Decision rule — registered before the data

- **P1 holds** (aggregate named rate ≤ 10 %) → re-base the flip-set figure onto the named set, resolve
  the H-placement row's `⚠ partial record` mark, and move the registry **17 → 18 fully backed, 3 → 2
  marked**. The band value (≤ 10 %) is unchanged. Both remaining marks (#2 L-test, #6 EM map-model) are
  then RETAIN — the resolvable partial records are exhausted.
- **P1 fails** (aggregate named rate > 10 %) → do **not** re-base as a reassurance. A named aggregate over
  the band is a **finding about the band**, written up with the offending models named, and the mark
  stays. (The round-45 rule: a band failing on a named set is a finding, not a quiet widen.)
- **The round-21/22 caveat is already discharged** by choosing a fresh named set rather than a subset:
  this measurement reproduces nothing from the lost 17; it establishes the rate on committed data
  (*reproducible*), and does not claim to corroborate the lost 7.5 %.

## What this round cannot answer

- **Method scope** — `reduce` and `reduce2` are the two builders the tolerance names; this is not a claim
  about other H builders.
- **Same-binary for `reduce2`** — `phenix-2.0-5936` pinned; a PHENIX upgrade could move `reduce2`'s flip
  calls (round 43 registers the cross-version test).
- **H-position vs H-count** — the count is nearly insensitive to the electron-cloud/nuclear convention;
  the row already states the count must not be read as evidence that two H builds match on position.
- **The other rows** — #2 L-test and #6 EM map-model are untouched (both RETAIN).
