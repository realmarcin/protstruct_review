# Negative-control round 8 — pre-registration (the round-7 closeout)

Registered **before any round-8 measurement**. This round closes the three
threads round 7 opened: the `REFI BREF ANIS` amendment's blast radius (I1),
the 11-entry wavelength patch under the G1 ruling clause (I2), and the 9YGW
endgame (I3). No new benchmark subjects; committed rounds are history.
Disclosed checks below run 2026-08-17 against the durable store and the
committed round-7 record.

## I1 — the `REFI BREF ANIS` rollout census

Round 7 registered the amendment (aniso-model entries add `REFI BREF ANIS`
to the third-opinion NCYC-0 invocation) and measured it on one entry.
**Disclosed census: every one of the 22 entries carries an aniso model**
(21 at ≥ 50 % of atoms; 7R2H at 44 %) — the amendment's scope is the whole
set, so its blast radius must be measured before any verdict-bearing use.

Census protocol: REFMAC NCYC 0 on each deposited model under BOTH
conventions (default `BREF ISOT` and `REFI BREF ANIS`), same inputs
otherwise; per-entry `r_free_isot`, `r_free_anis`, and the delta recorded.
9YGW is census-excluded unless I3 unlocks it (then both conventions run on
the unlocked form, recorded as such).

**The no-mixing rule, registered:** every committed REFMAC figure in
rounds 3–7 — including the C1/H1 `d_refmac` threshold and every
direction-agreement verdict — was measured under the ISOT convention.
`REFI BREF ANIS` therefore does NOT enter any verdict-bearing invocation
in this round or after it until a registered round re-derives the REFMAC
null distribution (and `d_refmac`) under ANIS. This round's census is
measurement of the amendment's effect, not its adoption; mixing
conventions inside one comparison would corrupt the verdict it feeds.

## I2 — the 11-entry wavelength patch (#361, the G1(b) ruling)

Round 7 proved refetch cannot reproduce these 11 files (the converter
rolls random free flags on unmeasured reflections), so the remediation is
an **in-place dataset-metadata edit** of each store MTZ: set the dataset
wavelength to the value recorded in the round-7 record's staged proof
(committed, per entry: 7R2H 0.8265, 7ATV 0.9184, 6Q01 1.0, 6ZWY 0.7653,
3ZOJ 0.65, 9P25 0.7872, 6F1O 1.0, 7TWR 0.7749, 6XVM 0.9793, 5R32 0.827,
9TXE 0.77488). Observation and flag bytes are untouched.

Proof obligation per entry, recorded before any sidecar re-baseline:

1. KEEP-column fingerprints (the round-6 U1 arbiter) byte-identical before
   and after the edit;
2. the only change is dataset metadata (wavelength, and nothing else the
   fingerprint does not already cover);
3. the new wavelength equals the committed round-7 staged value.

A failed proof on any entry leaves that file untouched and is recorded as
a named defect. **Write gating, registered from the round-7 precedent:**
the merged registration authorizes the *protocol*; the writes themselves
run only on the user's explicit in-conversation instruction naming the
patch (the session's permission layer requires the named go-ahead for
sidecar re-baselines, and this registration adopts that as its own rule
rather than relitigating it). Until then the driver runs proof-only
against staged copies.

## I3 — the 9YGW endgame

Round 7 established the deposited mmCIF is internally consistent and the
failure is REFMAC's positional aniso join over the CYS-altA/CSO-altB
residue. One registered experiment remains before the entry is stood down:

**The PDB-format form.** PDB-format `ANISOU` records carry no residue-name
join — the collision cannot occur by construction. The store holds the
deposited `9ygw.pdb` (disclosed check). One REFMAC NCYC-0 run on it, same
MTZ, same keywords. Risks named in advance: the round-3 canary moved
deposited models to mmCIF because PDB-form numbering microheterogeneity
broke other entries, and 9YGW's residue 109 carries exactly that
microheterogeneity (CYS-altA/CSO-altB at one position) — the experiment
tests whether REFMAC's PDB path handles what its mmCIF path does not.

Registered outcomes, two-sided: measurable → 9YGW gets a **named
per-entry input-form exception** (mmCIF default, PDB form for 9YGW,
recorded in every future row that uses it), and the I1 census includes it
under both conventions; not measurable → 9YGW is **stood down to
permanent two-path status** by this registration — no further repair
attempts without a new registered mechanism, and its rows say so.

## Predictions

**W1** — the census direction is uniform: `REFI BREF ANIS` lowers REFMAC's
R-free on ≥ 20 of the 21 census entries, median drop ≥ 0.01 (the set is
sub-Å; collapsed aniso should cost fit everywhere).

**W2** — the census shows |Δ(ANIS − ISOT)| > the registered `d_refmac`
threshold (0.00560) on at least half the entries — proving convention
mixing would corrupt verdicts and the no-mixing rule is load-bearing, not
ceremonial.

**W3** — all 11 wavelength patches pass the full proof obligation
(fingerprints identical, wavelength equal to the committed staged value).

**W4** — the PDB form unlocks REFMAC on 9YGW (the positional join cannot
collide without a comp label), completing the census at 22/22.

## Outputs and scope

`negative_control_round8.md` + `negative_control_round8_closeout.json`
(census rows both conventions, patch proofs, the 9YGW experiment), swept
against the record. Code: `bench_round8.py` (SET_RECORD-gated), the patch
tool with its proof gate (write-gated as in I2), tests for the patch
invariant and the census parser. NOT in scope: adopting ANIS in
verdict-bearing invocations (needs the round-9 null re-derivation); agent
legs and sandboxes (#356); #338, #321; re-judging committed rounds.
