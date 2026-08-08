# Negative-control benchmark, phase 0: feasibility counts

**Measured 2026-08-08** by `scripts/select_gold_standards.py` (#295, phase 0 of
`negative_control_benchmark_plan.md`). Full record, including the strict-tier entry
ids per window, spot-checks, and the percentile sample:
`ref/research/data/negative_control_phase0_counts.json`. Reproduce with:

```
python3 scripts/select_gold_standards.py --json ref/research/data/negative_control_phase0_counts.json
```

## The question phase 0 answers

Does anything survive gold-standard curation, and is the survivor pool diverse or a
handful of lysozyme-likes? These are COUNTS for the resolution-window decision. The
scouting tiers are searchable proxies, not enrollment criteria — enrollment is
preregistered at phase 2 (#297), and two requirements are not searchable at all
(residue-level masks, the headroom screen), so every count is an upper bound.

Tiers, cumulative: **base** = X-ray + released structure factors + ≥ 1 protein
entity; **geom** = + clashscore ≤ 2 + zero Ramachandran outliers; **strict** =
+ rotamer outliers ≤ 0.3 % + reported R-free ≤ 0.18.

## Counts

| window | tier | entries | protein entities | clusters @30 % | unclustered entities |
|---|---|---:|---:|---:|---:|
| ≤ 0.9 Å | base | 411 | 430 | 183 | 45 |
| ≤ 0.9 Å | geom | 86 | 89 | 57 | 15 |
| ≤ 0.9 Å | **strict** | **56** | 57 | **39** | 10 |
| ≤ 1.0 Å | base | 1 664 | 1 765 | 586 | 86 |
| ≤ 1.0 Å | geom | 482 | 504 | 172 | 35 |
| ≤ 1.0 Å | **strict** | **254** | 266 | **116** | 26 |
| ≤ 1.2 Å | base | 7 530 | 8 119 | 2 131 | 278 |
| ≤ 1.2 Å | geom | 2 166 | 2 283 | 643 | 108 |
| ≤ 1.2 Å | **strict** | **975** | 1 039 | **338** | 73 |

"Unclustered entities" are those RCSB's precomputed 30 %-identity clustering has no
group for (typically short sequences); they are additional diversity of unknown
degree, reported rather than folded into either column.

## Verification

- **Spot-checks (#238 discipline):** 10 strict survivors per window re-verified
  against the entry record — zero problems; every sampled d_min in window.
- **Percentile sample** (12 of 254 strict survivors at ≤ 1.0 Å, even spread across
  the d_min-sorted pool; wwPDB validation-XML `absolute-percentile-*` ranks):

  | metric | n | min | median |
  |---|---:|---:|---:|
  | clashscore | 12 | 88.7 | 95.7 |
  | Ramachandran outliers | 12 | 100.0 | 100.0 |
  | rotamer outliers | 12 | 85.9 | 100.0 |
  | DCC R-free | 11 | 96.1 | 99.4 |
  | RSRZ outliers | 12 | **1.7** | 39.9 |

  The scouting cuts select genuinely top-percentile entries on geometry and R-free.
  The RSRZ row is the exception and the lesson: **searchable cuts do not control
  local density fit** — one sampled entry sits at the 1.7th RSRZ percentile. This is
  exactly what the plan's phase-1 residue-level masks (and Top2018's residue-level
  filtering finding) exist for, now visible in this pool's own numbers.

## Observations for the window decision

1. **Every window is viable; none is lysozyme-only.** Even ≤ 0.9 Å strict holds 39
   clusters. Sampled titles at ≤ 1.0 Å span crambin, SH3 domains, designed
   peptide frameworks, and PanDDA fragment-screening depositions.
2. **≤ 1.0 Å strict (254 entries / 116 clusters) comfortably feeds a 20–50-entry
   benchmark** with one representative per cluster, with attrition margin for
   phases 1–2 (mask fraction, missing R-free flags (#242), headroom failures).
3. **≤ 0.9 Å strict (56 / 39) is usable but thin** once phase-2 attrition bites;
   it would make a fine *subatomic stratum inside* a ≤ 1.0 Å set rather than the
   whole set.
4. **≤ 1.2 Å strict (975 / 338) is the fallback margin** if phase-1/2 attrition is
   heavier than expected; nothing in the counts forces it now.
5. **PanDDA group depositions are a redundancy hazard** (hundreds of near-identical
   fragment-screening entries); the 30 %-identity clustering already absorbs them,
   which is one more reason enrollment must pick per-cluster representatives, not
   raw entries.

**Recommendation:** window ≤ 1.0 Å, enrollment as one representative per 30 %
cluster, with ≤ 0.9 Å tracked as a stratum label. The decision itself is the
project owner's call (plan §"Sequencing and cost"), to be recorded in the phase-2
preregistration.
