# Round 43 — pre-registration

Registered **before any cross-version refinement**, in a commit containing no results. This is **P3(a)
of the Codex review action plan** ([`codex_review_action_plan.md`](codex_review_action_plan.md)): the
single most-cited untested caveat in the registry is that every §4 refinement result is **same-binary**
— produced under the pinned `phenix-2.0-5936`, with "whether a PHENIX upgrade would move these values"
declared **untested**. This round registers the experiment that would turn that disclaimer into a
measured quantity: **is version shift material, or is it within the noise the bands already tolerate?**

## ⚠ Execution blocker (disclosed up front)

**Only `phenix-2.0-5936` is installed on this machine.** A cross-version experiment needs a *second*
PHENIX build, which is not present. So this round is **registered but not runnable here**: it is a
pre-committed design, to be executed when a newer build is available, so the comparison is not chosen
post-hoc. Registering it now is the point — a reproducibility claim about version stability must fix its
panel and predictions *before* seeing which entries move, or it is just a story told after the fact.

## Why register it now (rather than wait for the build)

The round-38 X-ray cache — 17 model+MTZ pairs, already re-refined under `phenix-2.0-5936` with every
per-entry value committed in `round38_xray_deltas.json` — is a **ready-made paired panel**: identical
inputs, one binary already run. The cross-version experiment is then *only* the second binary on the
same inputs, so the design is fully specified now and nothing about it can drift when the build arrives.

## Method

**Paired, same-input, two-binary.** For each panel entry, re-run the *identical* pipeline under the
newer build and difference each quantity against its committed `phenix-2.0-5936` value. Version shift is
treated as **its own distribution** — the per-entry `Δ_version = value_new − value_pinned` — not assumed
to be noise.

- **X-ray arm (primary).** The 17 round-38 pairs (cached), re-refined unrestrained, 3 macro-cycles,
  identical to round 38 except the binary. Quantities: Cα-shift RMSD, Ramachandran favored %,
  clashscore, rotamer outlier % — the §4 refinement Δ-clause inputs. Committed baseline:
  `round38_xray_deltas.json`.
- **EM arm (secondary).** A spanning subset of **8** `measured` EM entries from
  `em_refinement_deltas.tsv`, chosen across the 2.4–4.1 Å window, re-measured (mtriage + real-space
  refine) under the newer build. Quantities: CC_mask, `d_FSC_model`. Baseline: the committed TSV values.

The panel ids are committed with the result, as every benchmark set is.

## Predictions

**P1 — version shift is within the null-refinement spread.** For Cα-shift RMSD, the per-entry
`|Δ_version|` distribution stays **below the band's own headroom** — the +0.25 Å band sits ~0.05 Å above
the fresh-set maximum (0.2004 Å), so a version shift that keeps every entry under 0.25 Å leaves the band
valid. *Falsified* if any panel entry's `|Δ_version|` in Cα-shift exceeds **0.05 Å**, or if the
version-shift median exceeds the same-binary reproduction floor (round 20: 8/8 reproduced *exactly*).

**P2 — the favored/CC_mask/d_FSC_model bands survive the version shift.** No panel entry crosses its §4
band under the new binary that did not under the pinned one (favored −6 pp, CC_mask −0.04/−0.06,
`d_FSC_model` ×1.05). *Falsified* by any new band crossing attributable to the version change.

**P3 — determinism is a same-binary property, not a cross-version one.** Round 20 showed
`phenix.refine` reproduces 8/8 byte-identically under the *same* binary. The prediction is that the
*cross-version* comparison will **not** be byte-identical for most entries — some non-zero `Δ_version` is
expected — so the interesting question is its *magnitude*, not its existence. *Falsified* only if the
new build reproduces the pinned one byte-identically throughout (which would make the caveat vacuous).

## Decision rule — registered before the data

- **P1 and P2 hold**: the "same-binary" caveat is **downgraded to "same-binary, version shift measured
  and within band headroom on N entries"** — a measured reassurance, not a disclaimer. No band changes.
- **P1 or P2 fails**: version shift is **material**. The affected band's caveat becomes an explicit
  *versioned* one, the band is re-checked under the new build before the next release is adopted, and a
  gate is considered that pins the binary in the registry the way `bench_*.py` already pin
  `phenix-2.0-5936`.
- **Underpowered outcome**: if fewer than 12 X-ray entries and 6 EM entries complete under the new
  build, the round reports the shortfall and the version-shift distribution is recorded as
  *characterised but not powered* — a result, not a failure.

## What this round cannot answer

- **Which** newer build — the result is specific to the pair (`2.0-5936`, new build X); a third build is
  a third experiment. State the exact new build's version string with the result.
- **The lost entries or any non-refinement tolerance** — this is the §4 refinement quantities only.
- **Whether a shift is a bug or an intended change** in the newer build — it measures magnitude, not
  cause; a large shift is a flag to investigate, not a verdict on either binary.
