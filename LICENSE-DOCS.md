# License for documentation, schema, and authored records

The non-code content this repository owns is licensed under the
**Creative Commons Attribution 4.0 International License (CC-BY-4.0)**,
SPDX identifier `CC-BY-4.0`. The full legal code, which governs, is at
<https://creativecommons.org/licenses/by/4.0/legalcode>.

Copyright (c) 2026, Marcin P. Joachimiak.

## Scope

| Content class | License | Where |
|---|---|---|
| Code: scripts, generated Python models, workflows, tests, shell helpers, project/lock files | BSD-3-Clause ([`LICENSE`](LICENSE)) | `scripts/`, `protstruct_review/`, `.github/`, `pyproject.toml`, `uv.lock`, `.python-version`, `ref/download_phenix_docs.sh`, and any `.py` under `data/` (e.g. `data/coscientists/openscientist/gemmi_rfactor.py`) |
| Documentation and prose | CC-BY-4.0 (this file) | `README.md`, `CLAUDE.md`, `CODING_STANDARDS.md`, `NEXT_TASKS.md`, `docs/`, `prompts/`, `ref/*.md`, `schemas/README.md`, `data/README.md`, `.claude/skills/` |
| LinkML schema, the catalog, and the reference tables | CC-BY-4.0 (this file; the schema declares it in its header) | `schemas/`, `ref/catalog.yaml`, `ref/tasks_and_evaluations.tsv`, `ref/structural_criteria.yaml`, `ref/thresholds_and_standards.yaml`, `ref/tool_assumptions.yaml`, `ref/tool_recommendations.yaml` |
| Authored scientific records: round documents, preregistrations, benchmark records (JSON/TSV, masks), evaluation and QDS records, lessons | CC-BY-4.0 (this file) | `ref/research/` and `ref/research/data/**`; `data/examples/`; `EVAL_*`/`QDS_*` YAML, `.md`, `.tsv`, `.yaml` under `data/`. Figures these records derive from third-party data carry that data's attribution obligation |
| Derived structures and bundled agent artefacts: refined coordinate/reflection files produced from deposited entries, third-party agent outputs | **Upstream terms of the source entry or producer control — not relicensed here** | `data/agents/*/**/*.pdb`, `*.mtz`; the third-party agent bundle `data/coscientists/**/*_report.pdf`, `*_artifacts.zip` (slide decks built here by `build_slides.py` are authored, CC-BY-4.0); see [`data/README.md`](data/README.md) |
| Third-party material: deposited wwPDB coordinates, structure factors and validation reports; PHENIX/CCP4 documentation; any fixture with an upstream source | **Upstream terms control — not licensed here** | `data/pdb_mtz/` (manifest `data/pdb_mtz/fixture_provenance.yaml`); see [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md), [`data/README.md`](data/README.md) |

Anything not listed above and not third-party follows its file type: `.py`, `.sh`, `.toml`,
`.lock`, workflow `.yml` are BSD-3-Clause; everything else is CC-BY-4.0.

`CITATION.cff`'s `version` and `date-released` track `pyproject.toml` and are updated together at
each tagged release; until the first tag they name the current development version.

Attribution for CC-BY-4.0 content: cite the repository as given in
[`CITATION.cff`](CITATION.cff). Where a record derives figures from third-party
data, the attribution obligation to that upstream source is unchanged by this
license.
