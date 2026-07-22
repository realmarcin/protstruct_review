# Next tasks

Backlog of substantive work not yet done. Mirrors the open GitHub issues; this file
carries the execution detail. Keep in sync — close a GitHub issue and check the box here.

## Tolerance benchmarks (from the domain-expert `[template]` review)

Two agreement tolerances in `ref/thresholds_and_standards.md` are marked **provisional**: no
published inter-program reproducibility figure exists, so they can only be settled by *running the
tools on a structured test set*. Both are structural-biology harness work, not a literature pass.

### [ ] Benchmark interface BSA: biotite SASA vs PISA — GitHub #18

De-provisionalize `Interface buried surface area | |Δ| ≤ 10 %` (and the
`T16_interface_buried_surface_area` entry in `ref/structural_criteria.yaml`).

**Why provisional:** PISA uses a Lee & Richards surface with a 1.4 Å probe; biotite Shrake–Rupley
differs in point density and water/hetero handling; PISA also defines *interface* area differently
from ΣSASA(chains) − SASA(complex). The ±10 % is unmeasured.

**Execute:**
1. Pick a test set of ~10–15 deposited complexes spanning interface sizes: e.g. `1BRS`
   (barnase–barstar), `2SIC` (subtilisin–SSI), plus a few obligate dimers and a large multimer.
   Fetch coordinates with `curl -sL https://files.rcsb.org/download/<ID>.pdb`.
2. For each, compute BSA two ways with the **same probe radius (1.4 Å) and matched atom selection**
   (protein-only, no waters/hetero):
   - biotite: `python3 scripts/t16_interface_quality.py <model>.pdb` (reads the BSA row).
   - PISA: PDBePISA interface area from <https://www.ebi.ac.uk/pdbe/pisa/> (web; the deposition-grade
     reference). Record PISA's *interface area* definition explicitly.
3. Tabulate `|Δ| / mean` per complex; report the distribution (median, 90th percentile).
4. Replace the provisional ±10 % in `ref/thresholds_and_standards.md` and the
   `T16_interface_buried_surface_area` entry in `ref/structural_criteria.yaml` with the empirical
   noise floor (or confirm ±10 %), flip `provisional: false`, and add an `example_measurement` per
   complex. Note any systematic offset from the differing interface-area definitions.

**Blocked on:** PISA web access (or a local `pisa`/CCP4 install).

### [ ] Benchmark Wilson B: phenix.xtriage vs CCP4 ctruncate — GitHub #19

De-provisionalize `Wilson B | ± 5 Å²` (and the `T13_wilson_b` entry in
`ref/structural_criteria.yaml`).

**Why provisional:** `xtriage` uses an ML anisotropy-aware Wilson-B estimate; `ctruncate`/`truncate`
a classic straight-line Wilson plot (bin-choice sensitive). The two can differ by several Å², more
at low resolution / under anisotropy. The ±5 Å² is inference-only — no literature benchmark survived
the review.

**Execute:**
1. Assemble a **resolution- and anisotropy-stratified** set of ~15–20 deposited datasets with public
   reflection files (PDB-REDO supplies MTZs): low (~3.0 Å), mid (~2.0 Å), high (~1.2 Å), plus a
   couple with known anisotropy.
2. For each, on the **same reflection file**, run:
   - `phenix.xtriage data.mtz` → Wilson B (ML).
   - `ctruncate -hklin data.mtz -colin '/*/*/[I,SIGI]'` → Wilson B (classic).
3. Tabulate `|Δ|` per dataset, stratified by resolution and anisotropy; report the spread.
4. Set the tolerance to the empirical floor (possibly **resolution-conditional** — the review
   predicts a larger gap at low resolution), or confirm ±5 Å². Update
   `ref/thresholds_and_standards.md` and the `T13_wilson_b` entry, flip `provisional: false`, and add
   `example_measurement`s.

**Blocked on:** PHENIX + CCP4 both on the same reflection files (both installed locally per
`ref/oracle_tools.md`).

## Other tracked work

- **GitHub #2** *(closed — informational)*: driving examples complete (17/17).
- **GitHub #3** *(closed — informational)*: T15/T16/T17 runnable; only web/report-blocked pieces remain.
