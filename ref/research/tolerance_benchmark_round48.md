# Tolerance benchmark — round 48: the flip-set check becomes the confident-conflict rate; #5 resolves

Settles **#287**. Round 47 re-measured the Asn/Gln/His flip-set agreement (`reduce` vs `mmtbx.reduce2`)
on the named 42-set and found the **raw** disagreement rate 10.95 %, over the ≤ 10 % band — but 82 % of it
was residues `reduce` itself flagged uncertain (`X`). The approved direction: make the load-bearing check
the **genuine confident-conflict rate** — a disagreement counts only when `reduce` is confident (category
`F`/`K`) and `reduce2` still disagrees — and keep the raw rate as a diagnostic. Pre-registered in
[`tolerance_benchmark_round48_preregistration.md`](tolerance_benchmark_round48_preregistration.md).

## Result against the registered predictions

| prediction | verdict |
|---|---|
| **P1** confident-conflict aggregate ≤ 10 % | **confirmed** — **56 / 3105 = 1.80 %** over 41 protein entries |
| **P2** confident conflicts are dominated by confident *flips* (`F`) | **confirmed** — 55 `F`, 1 `K` |
| **P3** no single model alarming on the confident measure; name any over 10 % | **confirmed for the aggregate; four small-n models named** — 1TIJ 4/20 (20 %), 1OWJ 2/16 (12.5 %), 1BDJ 2/17 (11.8 %), 2QTU 2/17 (11.8 %); all high-variance small counts, versus the raw measure's worst of 40 % and 25 models over 10 % |

## What the check now is

The load-bearing flip-set check is the **confident-conflict rate**: `reduce`-vs-`reduce2` flip-decision
disagreements restricted to residues where `reduce` is confident (`F` = flipped or `K` = keep). It is
**1.80 %** on the named 42-set, comfortably under the ≤ 10 % band. The band value is unchanged; only what
it is measured against changed. Computed by `confident_conflicts()` in `bench_t14_flip_sets.py` (tested),
committed per-model in `round48_flip_sets.json`.

The **raw disagreement rate is retained as a reported diagnostic**: 10.95 % (340/3105), of which 279 are
`reduce` category `X` (uncertain), 5 `C` (clashes either way), and only 56 confident. Keeping it visible
preserves the honest fact that ~9 % of flippable residues are ambiguous enough that `reduce` declines to
commit — the raw number is not wrong, it just answers a different question ("how often is a flip
ambiguous?") than the tolerance asks ("how often do the builders genuinely conflict?").

## Why confident-conflict, not raw

A raw disagreement where `reduce` wrote `X` is one builder hedging and the other guessing, not two
builders conflicting about the model — the registry row already drew this line before round 47. Counting
those against the tolerance measures the *difficulty of the residues*, not the *disagreement of the
builders*. The same shape as round 46 (#284): re-measurement (round 47) resolved the record; this round
fixes the measure to the robust signal. The four per-model exceedances (all 2–4 conflicts on 16–20
flippable residues) are the small-n tail, named rather than smoothed; the aggregate is what the band
guards, exactly as the retired figure quoted an aggregate (7.5 %) with a higher worst model (16.4 %).

## #5 resolves — the resolvable partial records are exhausted

Round 47 committed the record (named 42-set); round 48 settles the measure. The H-placement row's
`⚠ partial record` mark **resolves**. Registry **17 → 18 fully backed, 3 → 2 marked**. The two remaining
marks — **#2 L-test** and **#6 EM map-model** — are both **RETAIN** (honest, disclosed limits not
resolvable by re-measurement), so **every *resolvable* partial record in the registry is now resolved.**
**#287 closed.**

## Scope limits

- **`reduce` vs `reduce2` only** — the two named builders; not a claim about other H builders.
- **The band value is unchanged** (≤ 10 %); the raw rate is retired *as a gate*, not as a record.
- **Same-binary** — `phenix-2.0-5936` pinned; a PHENIX upgrade could move `reduce2`'s flip calls (round
  43 registers the cross-version test).
- **Flip decision, not H position** — unchanged from the row's standing caveat.
