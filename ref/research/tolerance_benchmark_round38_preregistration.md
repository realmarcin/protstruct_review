# Round 38 — pre-registration

Registered **before any refinement of the round-38 set**, in a commit containing no results.

## Why repeat round 37

Round 37 measured 10 usable entries and lost 11 of 21 to three defects with one root cause: the
selector took the head of each stratum, which is the oldest depositions, which are also the entries
missing R-free flags and most likely to be nucleic acid. All three are fixed (#241, #243, #247).

**So round 38 is round 37 with the selection defect removed, and its first job is to say whether that
was the whole problem.**

The scientific question is unchanged from round 37 and its predictions carry over verbatim: does a
fresh named set reach the unrecoverable `d_min ≥ 2.5 Å` maxima of **0.285 Å** (Cα-shift) and
**5.26 pp** (favored)?

## Method

Identical to round 37 except for the selector, which now samples evenly spaced offsets across each
stratum and requires `polymer_entity_count_protein ≥ 1`. Same window (2.5–3.2 Å), same 4 strata, same
`--limit 20`, same null re-refinement, same quantities.

**The set is committed with the result**, as in round 37.

Selection ran before this file and returned 20 ids spanning 12UN to 7PLN, of which **17** yielded a
model + structure-factor pair; 3 were rejected at fetch for carrying no amplitudes or no FREE column.
That is disclosed here because it is already known and concealing it would misrepresent the design —
it is attrition of the same kind round 37 saw, and at the same rate.

## Predictions

**P6 — the refinement failure rate falls below round 37's 7 of 18 (39 %).**
The failures were `no usable R-free flags`, systematic among early depositions, and the selector no
longer favours those. *Falsified* if 6 or more of the 17 fail. **This is the round's first question**,
because if P6 holds then #242's methodological half — whether to generate R-free flags — is moot, and
if it fails that decision becomes unavoidable.

**P7 — usable n is at least 14 of 17.** Round 37 managed 10 of 21. *Falsified* below 14.

**P1–P3 carry over from round 37**: both bands hold; the fresh Cα-shift maximum stays below 0.285 Å;
the fresh favored drop stays below 5.26 pp. The same asymmetry applies and is restated rather than
assumed — **a maximum can only rise with more data, so these holding is the weak direction.**

**P5 carries over and was falsified in round 37** (a fresh sample reached clashscore 38.70 against the
"not reproducible" 17.2). Registered again only to see whether it replicates on an era-spread sample;
round 37's set was entirely pre-2000 and this one is not.

## What this round cannot answer

- **Whether the lost entries were like these.** Still gone. This measures the branch.
- **Whether the era spread is now representative.** It is *more* spread — 8 of 20 pre-2000 against
  20 of 20 — not demonstrably representative.
- **Anything about `d_min < 2.5 Å`**, out of scope by #237.
- **Whether a band should change.** Nothing is re-fitted regardless of outcome, as in round 37.
