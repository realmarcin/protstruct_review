# Next tasks

Backlog of substantive work not yet done. Mirrors the open GitHub issues; this file
carries the execution detail. Keep in sync — close a GitHub issue and check the box here.

**Last reconciled: 2026-07-26.** No open GitHub issues, no open PRs. There is no CI in this
repo — `bash scripts/validate.sh` is the gate, and it must exit 0 before a merge.

## Where the tolerance work stands

Four rounds of benchmarking have replaced inferred magnitudes with measured ones. **17 of the 21**
tolerances in `ref/thresholds_and_standards.md` now carry `[benchmark]` provenance; **4 do not**,
and they are the open work below.

| Round | PR | Settled |
|---|---|---|
| 1 | [#24](https://github.com/realmarcin/protstruct_review/pull/24) (2026-07-25) | interface BSA, Wilson B — the two marked *provisional* |
| 2 | [#28](https://github.com/realmarcin/protstruct_review/pull/28) (2026-07-26) | R offset, clashscore, H-placement, CA RMSD, aligned-residue count, bond-length RMSD |
| 3 | [#32](https://github.com/realmarcin/protstruct_review/pull/32) (2026-07-26) | restraint-library decomposition, Asn/Gln/His flip sets, L-test |
| 4 | [#36](https://github.com/realmarcin/protstruct_review/pull/36) (2026-07-26) | Ramachandran/rotamer outlier %, R-free, completeness, SS agreement, DockQ mapping, NMR ordered core |

Per-tolerance detail lives in the audit trails under `ref/research/tolerance_benchmark_*.md` and in
the re-runnable `scripts/bench_*.py`. It is deliberately **not** duplicated here — a backlog that
accumulates a changelog stops being readable as a backlog.

Pattern worth carrying into the remaining work: **five tolerances measured so far had been
generalised from a single observation** — clashscore ±1.0 from one 1SAR pair; H-count ±0.1 % from
one builder in two conventions; the SS floor ≥0.80 from 1SAR alone; the bond-length attribution by
analogy with bond angles; the DockQ and NMR preconditions asserted with no magnitude at all. Every
one moved when measured, three by more than an order of magnitude, and one (SS agreement) turned out
to be the wrong *shape* of check entirely. Assume the remaining four are in the same state.

## Open

### [ ] Ramachandran / rotamer **favored** % — ± 1.0 pp, never measured

Round 4 measured the **outlier** percentages and left the **favored** row untouched
(`ref/thresholds_and_standards.md` §3, still `[template]`). They are separate rows and separate
quantities, and the favored row was missed rather than deliberately deferred.

**Why it looked blocked and is not:** the PDBe `key_validation_stats` endpoint reports only outlier
counts, so there is no entry-level favored % to compare against. But the validation report **XML**
carries per-residue `rama="Favored" | "Allowed" | "OUTLIER"` attributes, so the favored fraction can
be counted directly. Verified on 12LO: 53 Favored + 1 Allowed = 54 → **98.15 %**, exactly what
`phenix.ramalyze` reports.

**Execute:** extend `scripts/bench_vs_deposited.py` to count per-residue `rama=` (and the rotamer
equivalent) from the XML, compare against `phenix.ramalyze` / `phenix.rotalyze` favored percentages
over the same 17-entry set, and re-derive the ±1.0 pp band. Expect the same shape as the outlier
rows — near-exact agreement — with one advantage: favored % has no 0.00-vs-0.00 degeneracy, so
unlike the Ramachandran *outlier* result (informative on only 4 of 17 entries, see #37) the evidence
will be informative on all 17.

### [ ] Refinement Δ-tolerances (§4) — a different class, never benchmarked

Three tolerances govern the compare→refine flow and all remain `[template]`:

- **ΔRMSD sanity** — `RMSD_post ≤ RMSD_pre + 0.05 Å`
- **Geometry did not degrade** — `clashscore_post ≤ max(clashscore_pre, 4)`; `favored_post ≥ min(favored_pre, 97 %)`; `rotamer outliers_post ≤ max(outliers_pre, 2 %)`
- **Map-model fit did not degrade** — `CC_mask_post ≥ CC_mask_pre − 0.01`; `d_FSC_model_post ≤ d_FSC_model_pre + 0.05 Å`

These are **not cross-tool agreement tolerances**, so the machinery from rounds 1–4 does not
transfer. They assert how far a *refinement* may move a quantity before it counts as degradation,
which needs a refine→re-measure loop rather than two tools on one file.

**Execute:** run `phenix.refine` (plus `servalcat` or REFMAC5 for a non-cctbx second opinion) over
deposited model+data pairs, measure each quantity before and after, and characterise the Δ
distribution for refinements that did *not* degrade the model; the bands follow from that. Note each
tolerance mixes a **Δ band** with an **absolute floor** (`4`, `97 %`, `2 %`) — two different claims.
Only the Δ is measurable this way; the floors are quality bars and should be split out and cited
separately, the way §2's literature thresholds are.

**Blocked on nothing.** PHENIX, CCP4 and reflection data for ~15 entries are already cached by
`scripts/bench_t06_r_offset.py`. This is the largest remaining piece of work in the file.

### [ ] Flip sets vs an independent H builder — BLOCKED on reduce2's output

Round 3 established that `phenix.reduce` and standalone `reduce` are the **same binary**
(`reduce.4.16.250520`), so the "same Asn/Gln/His flip set" clause currently checks nothing.
`mmtbx.reduce2` (v2.14.0) is the independent implementation — but it reports **no flip information**:
zero occurrences of "flip" in its `.txt` log and no `USER  MOD` records in its output PDB, so flip
calls cannot be extracted.

Re-check on the next PHENIX upgrade. Until then the clause stays labelled as a same-implementation
identity check rather than corroboration.

## Not actionable in this repo (listed so the gaps are explained, not recommended)

- **ctruncate Wilson-plot fit range** (residual confound from #19): the fit ranges were not matched
  because ctruncate does not report the range it used, so the measured 13.7 % is an upper bound on
  estimator divergence. Needs a ctruncate that reports or accepts an explicit range. *Partial local
  probe:* re-run `phenix.xtriage` with a restricted low-resolution cutoff to bound how much of the
  gap is range choice — worth doing only if the Wilson-B tolerance becomes load-bearing.
- **L-test matched resolution range**: the same shape, and confirmed unachievable — ctruncate
  restricts the L-test by a median 0.46 Å and its usage line exposes no resolution flag. Recorded as
  a caveat on the tolerance rather than a gate.
- **Fragment guard is `SSBOND`-only** (from #25): a cleaved molecule held together by something other
  than a disulfide, or an entry omitting `SSBOND` records, would not be caught. Extending it needs
  RCSB entity annotations rather than the coordinate file alone.
- **T16 BSA covers protein–protein only**: nucleic-acid and protein–ligand interfaces are out of
  scope for the tolerance as written (protein-only atom selection).
- **T17 independent NMR oracle**: no local wwPDB NMR validation / PROCHECK-NMR / RPF install;
  deposited validation reports are fetched per entry. A deliberate gap in `ref/oracle_tools.md`.
- **ChimeraX (T01, T08), MoRDa (T09), STRIDE (T15)**: recorded deliberate gaps; install only if those
  tasks become regression targets. **STRIDE is worth more now than before**: it is a third SS
  assigner, and round 4 could not tell whether DSSP or P-SEA is the outlier when they disagree.

## Other tracked work

- **GitHub #2** *(closed — informational)*: driving examples complete (17/17).
- **GitHub #3** *(closed — informational)*: T15/T16/T17 runnable; only web/report-blocked pieces remain.
- **GitHub #18, #19** *(closed 2026-07-25, PR #24)*: the two provisional tolerances.
- **GitHub #25, #26, #27** *(closed 2026-07-26, PR #24)*: intramolecular fragment pairs counted as
  interfaces, cache written into the working tree, multi-block sf-cifs.
- **GitHub #29, #30, #31** *(closed 2026-07-26, PR #28)*: two-block `model_vs_data` logs and outlier
  asymmetry, the near-identical-pairs weakness in the CA RMSD floor, dead code.
- **GitHub #33, #34, #35** *(closed 2026-07-26, PR #32)*: subset-dependent library share,
  unknown-vs-mismatched L-test ranges, and the het-dictionary difference that exposed a wrong
  H-count tolerance.
- **GitHub #37, #38** *(closed 2026-07-26, PR #36)*: the Ramachandran 0.00-vs-0.00 evidence base, and
  the SS-agreement metric being degenerate at the bad end.
