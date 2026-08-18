# Negative-control round 8 — the closeout: the aniso defect is set-wide

**Run 2026-08-18** per `negative_control_round8_preregistration.md`. Record:
`negative_control_round8_closeout.json`. Score: **W1, W2, W3 HOLD; W4
FALSIFIED** — and the falsification closes its question permanently.

## I1/W1/W2 — the census: every entry pays the aniso tax. HOLDS.

REFMAC NCYC 0 on all 21 measurable deposited models under both ADP
conventions:

- **21 of 21 lower under `REFI BREF ANIS`** (W1 bar: ≥ 20). Median drop
  **−0.0329** (bar: ≥ 0.01); range −0.0100 (7R2H, the set's only < 50 %
  aniso model) to −0.0565 (3ZOJ). The round-7 2VXN figures reproduce
  exactly (0.1712 → 0.1371).
- **21 of 21 exceed the registered `d_refmac` threshold (0.00560)** in
  magnitude (W2 bar: half) — at roughly **6× threshold scale**. The
  registered no-mixing rule is therefore structural: one convention-mixed
  comparison would dwarf the tolerance it feeds. Every committed REFMAC
  figure in rounds 3–7 is ISOT-convention and internally consistent;
  adopting ANIS for verdict-bearing use requires the round-9 re-derivation
  of the REFMAC null distribution, as registered.

The set-wide reading: the third-opinion tool has been grading every gold
standard with its anisotropy discarded — a ~0.01–0.06 systematic level
error that never corrupted a verdict only because both sides of every
committed delta shared the convention.

## I3/W4 — FALSIFIED: the PDB form fails too. 9YGW is stood down.

The registered experiment ran and the named risk materialized precisely:
REFMAC's PDB reader rejects the file at **chain A residue 106** — the
CYS-altA/CSO-altB position — with `Problem with coordinate file`. The
mmCIF path fails in the aniso join; the PDB path fails in the coordinate
reader; both on the same compositional microheterogeneity. Per the
registration, **9YGW is stood down to permanent two-path status**: no
REFMAC opinion is counted for this entry, its rows say so, and no further
repair is attempted without a new registered mechanism. The census stands
at 21 of 22 with the exclusion named.

## I2/W3 — all 11 patch proofs pass. HOLDS. Writes await the go-ahead.

Every patched candidate proves: KEEP-column fingerprints byte-identical
through the edit, the deposition-mmCIF wavelength applied (the registered
primary source), and the staged cross-check recorded — the two converter
placeholders (6Q01 staged 1.0 vs deposition 0.8211; 6F1O staged 1.0 vs
deposition 0.97926) are the only divergences, exactly as the registration
named (9TXE's 2e-5 rounding difference sits inside the registered 1e-3
tolerance). Per the registered gating, **no store file was touched**: the
proofs are on candidates beside the store, and the 11 writes run only on
the user's explicit in-conversation instruction naming the patch.

The canary earned its keep here too: the first patch attempt set the
wavelength on no dataset at all (an `id != 0` guard meant to skip
`HKL_base` skipped the stripped files' single id-0 dataset) and the proof
gate caught it — `patched_wavelength: 0.0` — before anything mattered.

## Round-9 inheritance

1. **The ANIS re-derivation** (registered as the adoption gate): re-run
   the REFMAC null legs under `REFI BREF ANIS`, re-derive `d_refmac`, and
   register the convention switch — after which the third opinion grades
   gold standards with their anisotropy applied.
2. **The 11 wavelength writes**, whenever the user names them.
3. Agent sandboxes (#356) with the next agent leg; #338, #321.
