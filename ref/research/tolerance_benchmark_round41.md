# Tolerance benchmark — round 41: the largest fresh X-ray set holds the bands, and locates 6LE5 as an isolated outlier (#225)

**No band is re-fitted.** Round 41 is the fresh low-resolution X-ray set **#225** asks for, run as round
39's **arm 2** (which arm 1 deferred here). It is the largest fresh named set this work has produced —
**20 usable of 25 selected**, all excluding the round-37/38 ids — and it answers the question round 38's
6LE5 breach raised: **a fresh era-spread sample does not reach 6.28 pp**, so that breach is an isolated
outlier, not a property of the branch. The §4 `d_min ≥ 2.5 Å` bands hold with room to spare, exactly as
arm 1's keep-the-band decision expected.

The [pre-registration](tolerance_benchmark_round41_preregistration.md) is a no-results commit; the set
and measurements are committed in
[`round41_xray_selection.json`](data/round41_xray_selection.json) and
[`round41_xray_deltas.json`](data/round41_xray_deltas.json).

## Result

| prediction | verdict |
|---|---|
| **P3** — fresh unrestrained favored-drop max ≥ 6.28 pp | **FALSIFIED** — worst drop **−1.85 pp** (4Q9R); no −6 pp breach |
| **P_Cα** — fresh Cα-shift max vs the lost 0.285 Å | **0.1849 Å** (4Q9R) — below round 38's 0.2004 and the lost 0.285 |
| **P_n** — at least 15 of 25 usable | **confirmed** — **20** usable |

P3 was falsified in the **weak** direction, which the pre-registration stated in advance: a maximum can
only rise with more data, so *reaching* 6.28 pp would have been meaningful while *failing* to is weaker
evidence. But 20 fresh entries falling this far short — worst 1.85 pp against 6.28 — is itself
informative: it says 6LE5 sits well outside the fresh distribution, not at its edge.

## Attrition: 25 → 20 usable, the best yield yet

| stage | lost | reason |
|---|---:|---|
| fetch | 4 | no amplitudes or no FREE column (3EUJ, 3GRT, 4EL1, 6CSM) |
| refine | 1 | no usable R-free flags (3D45) |
| **usable** | **20** | 0 lost to nucleic acid (the #241 protein filter held) |

The era-spread selection (2QIZ, 2IEF … 7LMC, 7D6N) and the wider offsets did what round 37's biased
sample could not: 20 usable of 25, against round 37's 10 of 21 and round 38's 14 of 17.

## The pooled picture: 6LE5 is 1 of 44

Across the three fresh named sets — rounds 37 (10), 38 (14) and 41 (20), **44 usable protein entries** —
the §4 `d_min ≥ 2.5 Å` bands are breached exactly once:

- **Favored (−6 pp):** one breach in 44, **6LE5 at −6.28 pp** (round 38). Round 41's worst is −1.85 pp;
  round 37's was −2.61 pp. So the breach that arm 1 showed restraints tame (6.28 → 2.21 pp) is also the
  lone breach across every fresh unrestrained entry measured — **1 of 44 (2.3 %)**.
- **Cα-shift (+0.35 Å):** zero breaches; the pooled maximum is **0.2004 Å** (7P4U, round 38), still
  short of the lost 0.285 Å. Round 41's 0.1849 Å does not reach it either.

This is the checkable basis #225 set out to build. The band widths still rest on two lost maxima (0.285
Å, 5.26 pp) that no fresh set has reproduced, but the bands themselves now have **44 fresh named entries**
underneath them, breached once, by an entry restraints tame. Nothing here re-fits a band — it confirms
the ones arm 1 kept.

## What round 41 delivers, and does not

- **Delivers:** the largest fresh named low-resolution X-ray set; confirmation that 6LE5's 6.28 pp is an
  outlier a fresh era-spread sample does not approach; a third independent set on which both §4 X-ray
  bands hold; the Cα band's first fresh check on data excluding rounds 37–38.
- **Does not:** reproduce either lost maximum (0.285 Å, 5.26 pp) — the weak direction, as registered;
  change any band (arm 1 settled the favored band, the Cα band is not breached); speak to restrained
  refinement (this set, like round 38, is unrestrained).

## Scope limits

- **Same-binary.** `phenix-2.0-5936` pinned; a PHENIX upgrade is untested.
- **Unrestrained only.** The pooled 1-of-44 breach rate is for unrestrained null re-refinement; arm 1
  showed restraints shrink the favored spread further (6LE5 6.28 → 2.21 pp).
- **The lost maxima remain unreproduced**, so the band *widths* still rest on numbers that cannot be
  recounted; what has a fresh basis is that the bands *hold*, not the figures that set their width.
- **`d_min < 2.5 Å`** out of scope by #237.
