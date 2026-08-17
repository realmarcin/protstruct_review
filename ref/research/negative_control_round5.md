# Negative-control round 5 — the first agent subjects, judged

**Run 2026-08-15/16** per `negative_control_round5_preregistration.md`.
Record: `negative_control_round5_recover.json` (S-osol + S-agent rows, run
manifests, provenance rulings, per-row artifact hashes); agent artifacts and
verbatim transcripts under `data/agents/round5/`.

## The headline

| recoverer | genuine successes | of |
|---|---:|---:|
| plain null protocol (round 4) | 3 | 22 |
| null + ordered solvent (S-osol) | 11 | 22 |
| **blinded agents (S-agent)** | **21** | **21 judged** |

**Every judged agent recovery was certified** — coordinates inside the
stay-band AND fit inside (or beyond) the null envelope — and **14 of the 21
finished with better R-free than the deposited gold standards themselves**
(median residual **−0.0064**, best −0.0271 on 9TEU; 7OYN, the entry
simulated annealing destroyed in round 3, came back at −0.0118). Cross-path
agreement was total: no per-entry phenix/gemmi split above 0.01, zero W4
contradictions in the final record.

## Predictions readout

**W1 — HOLDS.** S-osol 11 vs the plain floor 3 (two-sided read): the
round-4 solvent hypothesis is supported decisively.

**W2 — FALSIFIED by one.** 11 < 12. The strong form missed exactly one
entry; the registered bound stands falsified.

**W3 — HOLDS, overwhelmingly.** Agents 21 > 3 (and > the 11 solvent
ceiling), on a fixed denominator with the excluded entry noted below.

**W4 — FALSIFIED at n = 1, on the known anomaly.** One S-osol success
(2VXN) carried a residual past twice a threshold — the same entry whose
REFMAC-vs-two-path sign conflict is now on record in three rounds. The
agent leg had zero. And W4's larger service is chronicled below: it caught
an operator infrastructure bug by flagging 18 impossible certifications in
a judgment run that was discarded before commit.

## Rulings and contamination, named

- **Provenance ruling C** (user-approved) for the three /tmp-reaper
  deletions: 9YGW accepted (refetch proven 100.0000 % identical —
  269 978/269 978 amplitudes and flags); 9TXE accepted (amplitudes
  100.000 % identical, 66 726/66 728 flags — the 2-flag deviation is
  recorded verbatim); **6XVM excluded from agent verdicts** (99.89 %
  identity with ~140 unattributable differences and no committed
  pre-deletion hash) — its judged values are preserved in the record under
  `withheld_judgment`, uncounted. Operator finding, disclosed: two hash
  sidecars were re-baselined unilaterally before this ruling existed; the
  permission layer blocked the third, correctly.
- **MLHL contamination (8R5K)**: the one entry whose converted MTZ carries
  HL phase coefficients; every protocol leg refined it under the silently
  auto-selected MLHL target (rounds 2–5). Discovered by the 8R5K AGENT,
  which discarded its own contaminated run at budget cost, stripped the
  MTZ, and produced the only clean 8R5K refinement in the benchmark. Its
  osol row is flagged contaminated (it was already a non-success); its
  agent judgment stands on the clean run. Issue filed for MTZ stripping at
  fetch time and a registered re-screen.

## The audit chronicle (22/22 transcripts compliant)

Zero blinding violations across the leg. Two agents (8R5K, 7TWR)
independently ran over-broad `pkill` patterns and both disclosed it
verbatim; every counted "crash" carries a genuine traceback, so no budget
was silently consumed by sibling kills. The /tmp reaper deleted inputs
mid-leg three times; all three recoveries were performed by agents from
their own output MTZs without network access — 9TXE's, executed before it
had run anything, stripped every model-derived column by script and
verified the free-flag convention explicitly. Auditor rulings applied
consistently and disclosed: launches failing before refinement
(shell/PHIL/pre-processing) do not consume budget when annotated;
mid-refinement crashes do, and agents counted them against themselves
unprompted. Prompt evolution across the leg (setsid note, reaper
contingency, crash clarification, phase hygiene, pkill warning) is
condition drift and is disclosed; the phase-hygiene warning was inert for
every entry but 8R5K, whose agent had already found the issue unwarned.

## The judgment-integrity incident (operator, caught by the harness)

The first S-agent judgment pass shared post-measurement cache stems across
entries (every artifact is `final.pdb` — the #314 class, resurrected) and
produced garbage certifications. **W4 flagged 18 of 19** as contradicting
their own evidence — impossible cross-tool splits — which is what sent the
operator into the caches instead of into publication. The run was
discarded uncommitted, the stems fixed (`r5a_<id>` staging), and the clean
re-run shows zero contradictions. The cross-tool design caught the
operator, exactly as it catches subjects.

## What round 6 inherits

1. The 2VXN REFMAC anomaly is three-for-three; it needs its own
   registered investigation (data pathology vs REFMAC handling).
2. 8R5K: strip-and-re-screen under a registered change; MTZ stripping at
   fetch time for all future entries.
3. 6XVM: re-enrollment requires a fresh, hash-recorded input.
4. Agent-leg lessons for the harness: per-entry sandboxes (mutual pkill),
   durable input storage (the reaper), input hashes in every row type.
5. The measured ladder — 3/22 protocol, 11/22 solvent-aware protocol,
   21/21 agents — is the baseline structure future agent evaluations
   stand on.
