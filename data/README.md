# Data provenance

This directory mixes repository-authored evaluation records, deposited experimental artifacts,
benchmark outputs, and refined structures. Do not assume one license or provenance statement
applies to every file. `THIRD_PARTY_NOTICES.md` records the applicable upstream policies.

## `pdb_mtz/` fixtures

| Files | Recorded provenance | Status for reuse |
|---|---|---|
| `1d3z.pdb` | Added as the deposited 1D3Z NMR ensemble for T17; commit history does not record the retrieval URL/date or checksum. | Re-fetch from the wwPDB archive and cite PDB ID 1D3Z before redistribution. |
| `2n54_validation.xml.gz` | Added as the deposited wwPDB validation report for PDB ID 2N54; retrieval URL/date and checksum were not recorded. | Verify against the current wwPDB report and cite PDB ID 2N54. |
| `1sar.pdb`, `1sar.mtz` | Added as X-ray example inputs. PDB ID 1SAR is named, but the exact source, retrieval date, and transformations were not recorded. | Provenance must be reconstructed before asserting wwPDB CC0. |
| `porin.pdb`, `porin.mtz` | Added as X-ray example inputs without an accession, source URL, retrieval date, or license record. | Provenance and redistribution rights are unresolved. |

For future deposited fixtures, record the archive URL, PDB/EMDB identifier, retrieval date,
SHA-256 checksum, source license, and any transformations in this file in the same commit.

## Agent and benchmark outputs

`agents/` contains refined/generated structures and benchmark artifacts. `coscientists/` contains
evaluation records, logs, reports, and presentation artifacts. These are derived research outputs;
their source structures and experimental data remain subject to their recorded upstream terms.
Round-specific Markdown and machine-readable records provide the scientific lineage, but many older
binary artifacts do not yet carry a complete source URL/checksum trail.

New benchmark records must begin with the environment/tool version record emitted by
`scripts/benchmark_environment.py`, and new externally sourced artifacts must carry the provenance
fields listed above.

The legacy backfill is tracked in
[#400](https://github.com/realmarcin/protstruct_review/issues/400).
