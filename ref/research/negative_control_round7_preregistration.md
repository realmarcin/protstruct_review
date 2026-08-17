# Negative-control round 7 — pre-registration (re-registration + attribution)

Registered **before any round-7 measurement**. This round discharges the
obligations round 6 created: the U3 falsification's required re-registration
of the C1 table, the 2VXN four-tool anomaly (#355) with the mechanism
candidates round 6 named, the 9YGW aniso-record repair, and the #361 store
remediation under the G1 sidecar policy's ruling clause. No new benchmark
subjects; committed rounds are history and are not re-judged. The disclosed
basis below is the round-6 record (`negative_control_round6_hygiene.json`),
measured 2026-08-17.

## H1 — C1 re-registration (the U3 falsification's follow-up)

The clean-null table, computed in round 6 with 8R5K's uncontaminated null
substituted on the phenix and gemmi paths and ADDED on the REFMAC path
(see the population disclosure below), is **adopted by this registration**
and supersedes the round-3 C1 table for all future verdicts:

| path | superseded (round 3) | registered here |
|---|---|---|
| d_phenix | 0.01220 | **0.01200** |
| d_gemmi | 0.01090 | **0.01025** |
| d_refmac | 0.00540 | **0.00560** |

Same definition as C1 (median_null + 3·MAD_null per tool; S_FLOOR and the
E1 fit rule unchanged). **Population disclosure (#364):** the phenix and
gemmi recomputes are true substitutions at n = 22, but 8R5K had no round-3
REFMAC null (it was unmeasurable), so its clean null (+0.0060) is a NEW
observation and the REFMAC population grows 19 → 20 — that growth, not a
substitution, is what moves d_refmac. **Registered disclosure obligation:** every
committed verdict from rounds 3–5 is recomputed under the new table and any
verdict that would flip is DISCLOSED by entry and round in the round-7 doc.
Committed rounds are not re-judged — the disclosure names what the old
table's looseness or tightness concealed, nothing more.

## H2 — the 2VXN mechanism hunt (#355, continues round-6 G4)

Round 6 established the four-tool spread on the deposited model — phenix
mvd 0.1043 / gemmi path 0.1059 / Servalcat 0.1473 / REFMAC 0.1712 — against
a deposition-reported R-free of 0.103. The tiebreaker sides with the two
paths; both Murshudov-family tools diverge high. The registered
substitution was NOT enacted (Servalcat diverges too). Mechanism candidates
named in round 6, here ranked and given one discriminating experiment each,
run in this order and one change at a time:

1. **Anisotropic-ADP handling (ranked first).** 2VXN is a 0.82 Å structure
   with deposited anisotropic ADPs — **disclosed check (2026-08-17): all
   2511 atoms carry nonzero aniso tensors** — and the 9YGW failure is in
   REFMAC's aniso *reader*, which makes the family's aniso path the prime
   suspect.
   Discriminating experiment: a derived 2VXN model with all anisotropic
   records removed (isotropic B only, coordinates and occupancies
   untouched, recorded with its own hash). All four tools measure it.
   - If the two paths jump toward ~0.17 while REFMAC barely moves, the
     divergence IS aniso: REFMAC is not applying the deposited aniso ADPs
     at NCYC 0, and the attribution is complete.
   - If all four agree on the iso-only model, the residual spread on the
     deposited model is still aniso-located but the defect is in how each
     tool consumes the records — attributed to the same term, finer-grained.
   - If the spread survives unchanged, aniso is refuted; proceed.
2. **Resolution-cutoff handling.** Cheap log audit first: the exact
   resolution ranges each tool used in round 6, from their existing logs;
   then REFMAC re-run with `RESO` forced to the phenix range if they
   differ.
3. **Hydrogen treatment (demoted to last, #365, #366).** Disclosed check
   (2026-08-17): the deposited model contains 0 explicit H among its 2511
   atoms, and REFMAC restores riding hydrogens by default. Direction
   argument: adding riding H at 0.82 Å should LOWER REFMAC's R relative to
   an H-free calculation, so differential H treatment cannot CAUSE the
   +0.07 excess — it can only partially mask a larger divergence. The
   experiment stays registered because it is one keyword and bounds the H
   term: REFMAC with `MAKE HYDR N` vs default; a null result is expected,
   not surprising.

**Registered outcomes (two-sided):** the divergence is ATTRIBUTED to a
named mechanism with the invocation change (if any) that closes it — which
then becomes a registered protocol amendment for the third-opinion leg —
or all three candidates are refuted and 2VXN's third-opinion leg is
formally STOOD DOWN as a named cross-tool conflict: no REFMAC or Servalcat
opinion is counted for this entry, and its verdicts rest on the two-path +
deposition agreement alone. No third outcome; "unattributed but still
counted" is not available.

## H3 — the 9YGW aniso-record repair (completes U2)

Round 6 named the cause precisely: `rdaniso_cif: label_comp_id mismatch —
atom record CSO / aniso record CYS`. The deposited mmCIF's aniso block
carries the parent residue name for the modified residue. Registered
repair, **metadata-only**: a derived 9YGW mmCIF in which the aniso block's
`label_comp_id` for the affected residue(s) is renamed CYS → CSO to match
the atom records — **disclosed check (2026-08-17): 9YGW carries exactly 2
CSO residues**. Zero coordinates, occupancies, B values, or aniso tensor
values change; the derived file gets its own hash and lives beside the
original, which is untouched. REFMAC (and only REFMAC) consumes the
derived file. If the repair does not unlock REFMAC, the failure is
re-diagnosed from the new log and 9YGW stays named-unmeasurable — the
repair is not iterated past the registered rename.

## H4 — store remediation under the G1 ruling clause (#361 part 2)

Round 6's `strip_mtz` discarded dataset metadata; the 12 stripped files in
`~/protstruct_bench_inputs` carry wavelength = 0.0. The metadata-preserving
strip is already merged (#359). Registered remediation:

1. Re-fetch the 12 entries to a staging area and re-strip with the merged
   (metadata-preserving) code.
2. **Proof obligation before any store write:** per-column SHA-256
   fingerprints of every KEEP column (the round-6 U1 arbiter) must match
   the current store file exactly, and the restored wavelength must be
   nonzero and equal to the value in the staging fetch's own conversion
   log. Both are recorded per entry in the round-7 record.
3. Only then is the store file replaced and its sidecar re-baselined, each
   row citing this section by name. A fingerprint mismatch on any entry
   halts remediation for that entry and is recorded as a named defect —
   the store file is NOT replaced on a mismatch.

Per G1(b), the user-gated merge of this preregistration **is** the ruling
this remediation cites; no store file is touched before that merge.

## Housekeeping registered with this round

- The REFMAC measurability census after H3: predicted 22/22 measurable
  (21/22 if H3 fails), recorded either way. 8QXQ's newly measurable
  third opinion (round 6) joins the E1 all-three rule for future rounds.
- NOT in scope: new benchmark subjects; agent legs and sandboxes (#356
  second half); #321 and #338 (separate work); re-judging rounds 3–5
  (disclosure only, per H1).

## Predictions

**V1** — zero committed verdicts flip under the re-registered C1 table
(the moves are small and no round-3–5 delta sits between the old and new
thresholds on the deciding path).

**V2** — the 2VXN divergence is attributed by experiment 1: the iso-only
derived model moves the two paths up by ≥ 0.03 toward REFMAC while REFMAC
moves by < 0.01, identifying unapplied anisotropic ADPs as the dominant
term. (Falsifiable in two directions: the spread surviving the iso-only
model refutes the aniso candidate; all-four convergence on it relocates
the defect to record consumption.)

**V3** — the H3 rename unlocks REFMAC on 9YGW and U2 completes 3/3, with
the derived file differing from the deposited mmCIF only in the renamed
`label_comp_id` strings.

**V4** — all 12 remediated entries pass the H4 proof obligation on the
first staging fetch: observation fingerprints identical, wavelengths
restored nonzero.

## Outputs

`negative_control_round7.md` + `negative_control_round7_attribution.json`
(H1 flip-disclosure sweep, the H2 experiment ladder with all four tools per
step, the H3 repair diff summary and REFMAC result, the H4 per-entry proof
rows), swept against the record. Code: the round-7 driver
(`bench_round7.py`, SET_RECORD-gated), the H3 mmCIF repair as a recorded
derivation, the H4 remediation with its proof gate. Tests for the repair
(rename-only invariant) and the remediation proof gate.
