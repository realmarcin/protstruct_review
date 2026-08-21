# Data provenance

This directory mixes repository-authored evaluation records, deposited experimental artifacts,
benchmark outputs, and refined structures. Do not assume one license or provenance statement
applies to every file. `THIRD_PARTY_NOTICES.md` records the applicable upstream policies.

## `pdb_mtz/` fixtures

`pdb_mtz/fixture_provenance.yaml` is the machine-readable source of truth. The hermetic gate checks
that every fixture is listed, every listed file exists, and both file and decompressed-content
checksums match. The retained files were verified on 2026-08-21:

| File | Archive identity | Verification and reuse status |
|---|---|---|
| `1d3z.pdb` | PDB 1D3Z NMR ensemble, `https://files.rcsb.org/download/1D3Z.pdb` | Byte-for-byte equal to the current RCSB download; cite PDB 1D3Z and its depositors. |
| `1sar_deposited.pdb` | PDB 1SAR deposited coordinate model, `https://files.rcsb.org/download/1SAR.pdb` | Byte-for-byte equal to the current RCSB download; used for current T15/T16 runnable calibrations, not as a substitute for the removed historical agent input. Cite PDB 1SAR and its depositors. |
| `2n54_validation.xml.gz` | PDB 2N54 wwPDB validation XML, `https://files.rcsb.org/pub/pdb/validation_reports/n5/2n54/2n54_validation.xml.gz` | Replaced with the current archive gzip. Its decompressed XML is byte-for-byte equal to the prior fixture, so T17 parser evidence is unchanged. Cite PDB 2N54 and its depositors. |

The wwPDB usage policy linked from `THIRD_PARTY_NOTICES.md` places archive data files under CC0 and
encourages attribution. The manifest records the exact URL, retrieval date, SHA-256, identifier,
and transformation status for each retained file.

### Removed legacy fixtures

- `1sar.pdb` and `1sar.mtz` were the transformed starting inputs in the historical
  `cdba2c07-daff-4f60-ae96-12452b3a5fbb` agent artifact. Their filenames, unit cell, and former
  mirrored documentation identify the PHENIX ribonuclease-Sa refinement tutorial lineage, but the
  exact upstream package/version and transformations were not recorded. They were removed rather
  than incorrectly relabeled as exact archive downloads. Historical evaluation records and logs
  retain their original paths as evidence of what was run.
- `porin.pdb` and `porin.mtz` matched the PHENIX twinning tutorial identity and unit cell, had no
  repository consumers, and had no recorded redistribution permission. They were removed with the
  tracked PHENIX documentation mirror.

For future fixtures, add the file and its complete manifest entry in the same commit. Do not reuse a
historical path for different bytes: that would silently invalidate the evaluation lineage.

## Agent and benchmark outputs

`agents/` contains refined/generated structures and benchmark artifacts. `coscientists/` contains
evaluation records, logs, reports, and presentation artifacts. These are derived research outputs;
their source structures and experimental data remain subject to their recorded upstream terms.
Round-specific Markdown and machine-readable records provide the scientific lineage, but many older
binary artifacts do not yet carry a complete source URL/checksum trail.

New benchmark records must begin with the environment/tool version record emitted by
`scripts/benchmark_environment.py`, and new externally sourced artifacts must carry the provenance
fields listed above.
