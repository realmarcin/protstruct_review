# Independent oracle tools — install status and per-metric recommendations

The protstruct_review trust model requires that PHENIX outputs be cross-checked by **at least one non-cctbx tool** per task (see `tasks_and_evaluations.md` philosophy section). This page records which oracles are installed locally on this machine and how to invoke them. The **canonical per-metric recommendations** live in `ref/tool_recommendations.yaml` (LinkML-validated, schema-class `ToolRecommendation`).

## Recommendations vocabulary

For each metric in the catalog we track up to four kinds of tool record:

| Role | Meaning | Source |
|---|---|---|
| **`top_considered`** | The canonical tool the literature / community consensus says to use for this metric. | Citations in `ref/quality_reporting.md` and `ref/tool_recommendations.yaml`. |
| **`top_performing`** | The tool that has empirically done best on this metric **in this harness**. Often the same tool as `top_considered`; when they differ both rows exist. | Evidence is an `EvaluationRun.id` from `data/.../EVAL_*.yaml`. |
| **`alternative`** | Acceptable second-line oracle. Used when the primary tool is unavailable or as a corroborating check. | Same. |
| **`deprecated`** | Was recommended; no longer is. Kept for historical comparison. | Same; `notes` field carries the deprecation reason. |

When a `MeasurementValue.oracle_tool_ref` doesn't match any `top_considered` or `top_performing` recommendation for that metric, downstream tooling should flag it. The `QualityDataSheet.tool_recommendations_applied[]` slot snapshots the recommendations active at the time the QDS was issued, since recommendations evolve and the QDS is immutable.

To browse / query recommendations:

```bash
linkml-validate --schema schemas/protstruct_review.yaml ref/tool_recommendations.yaml
python -c "
import yaml; d = yaml.safe_load(open('ref/tool_recommendations.yaml'))
for r in d['tool_recommendations']:
    if r['role'] == 'top_considered':
        print(f\"{r['metric_definition_ref']:40} -> {r['tool_ref']}\")
"
```

## Installed

| Oracle | Version | Path | Catalog tasks served |
|---|---|---|---|
| **gemmi** | 0.7.5 | `/opt/homebrew/bin/gemmi` (brew tap `brewsci/bio`) | T01 (`gemmi align`), T06 (`gemmi sfcalc`), T14 (`gemmi h`), T05 (`gemmi validate`) |
| **TM-align** | 20220412 | `$HOME/tools/tmalign/TMalign` | T01 (TM-score, sequence-independent superposition) |
| **probe** (Richardson lab) | 2.26.021123 | `$HOME/tools/probe-src/probe` | T05 (clash detection — feeds clashscore) |
| **reduce** (Richardson lab) | 4.16.250520 | `$HOME/tools/reduce-src/build/reduce_src/reduce` | T14 (H-atom placement); T05 (input prep for clashscore) |
| **Servalcat** | 0.4.131 | conda env `cryst-oracles` (`mamba activate cryst-oracles`) | T03 (`servalcat refine_xtal_norefmac`), T06 (`servalcat fsc`, `fofc`, `sigmaa`), T12 |
| **OpenStructure (OST)** | 2.11.1 | conda env `cryst-oracles` (CLI `lddt`, Python `import ost`) | T01 (`lddt` — CASP15+ reference implementation, global + per-residue), T02 (per-residue Cα distance + structural comparison), T05 (Ramachandran φ/ψ extraction; outlier classification needs external Top8000 contour data), T07 (per-residue lDDT for predicted-vs-experimental) |

Together, `probe` + `reduce` constitute the standalone Richardson-lab MolProbity pipeline that the catalog calls "MolProbity standalone" — these are the same binaries the MolProbity web service runs.

Servalcat ships a no-REFMAC refinement mode (`refine_xtal_norefmac`, `refine_spa_norefmac`) so it can serve as a T03 second-opinion oracle even without CCP4.

## Not installed (recorded gaps)

| Tool | Why not installed | Catalog tasks affected | Recommendation |
|---|---|---|---|
| **CCP4 / REFMAC5 / ProSMART** | Gated behind free academic registration at <https://www.ccp4.ac.uk/download/registration/>; multi-GB suite. | T03 (REFMAC5 = canonical second-opinion refiner; PDB-REDO methodology), T05 (ProSMART = non-cctbx Ramachandran-Z + per-residue rotamer comparison; closes the cctbx-only gap on the geometry %s), T06 (REFMAC5 R-factors), T13 (aimless / pointless / ctruncate for data-quality metrics) | Register at the URL above; download macOS-arm64 installer; install to `$HOME/ccp4`; source `$HOME/ccp4/setup-scripts/sh/ccp4.setup-sh`. Catalog tool entries (REFMAC5, ProSMART, aimless, pointless, ctruncate) are pre-staged at commit a54964a's successor. |
| **ChimeraX** | Heavy GUI install; useful for `matchmaker` (T01) and `fitmap` (T08) | T01, T08 | <https://www.cgl.ucsf.edu/chimerax/download.html> |
| **MoRDa** | Specialised MR pipeline | T09 only | Install only if T09 becomes a regression target |

## Quick activation snippets

**Crystallography oracle env (Servalcat):**
```bash
source /opt/homebrew/Caskroom/miniforge/base/etc/profile.d/conda.sh
conda activate cryst-oracles
```

**Richardson-lab tools on PATH:**
```bash
export PATH="$HOME/tools/probe-src:$HOME/tools/reduce-src/build/reduce_src:$HOME/tools/tmalign:$PATH"
```

(Add to `~/.bashrc` or wrap in a project-local `env.sh` — not committed.)

## Verifying after install

```bash
gemmi --version            # 0.7.5
TMalign | head -2          # TM-align Version 20220412
probe -version             # probe.2.26.021123
reduce -version            # reduce.4.16.250520
conda activate cryst-oracles && servalcat --version  # 0.4.131
```

## Cross-tool oracle assignment per catalog task

| Task | Primary PHENIX tool | Oracle (now installed) | Oracle (still missing) |
|---|---|---|---|
| T01 | `phenix.superpose_models` | TM-align, `gemmi align` | ChimeraX matchmaker, US-align |
| T03 | `phenix.refine` | `servalcat refine_xtal_norefmac` | REFMAC5, BUSTER |
| T05 | `phenix.holton_geometry_validation` | `probe` + `reduce` (std MolProbity), `gemmi validate` | wwPDB validation pipeline |
| T06 | `phenix.model_vs_data` | `gemmi sfcalc`, `servalcat fsc`/`fofc`/`sigmaa` | CCP4 sfcheck |
| T12 | `phenix.mtriage` | `servalcat fsc`, `servalcat localcc` | RELION postprocess, ResMap |
| T14 | `phenix.reduce` | standalone `reduce` (Richardson lab — same binary, different build) | propka3, OpenBabel |

All tasks now have at least one **non-cctbx** oracle. The trust model is satisfied at minimum strength; CCP4/REFMAC will harden T03/T06.

## Build notes (for reproducibility)

**TM-align** — single C++ source. `malloc.h` include must be commented out on macOS:
```bash
mkdir -p $HOME/tools/tmalign && cd $HOME/tools/tmalign
curl -sL -o TMalign.cpp https://zhanggroup.org/TM-align/TMalign.cpp
sed -i.bak 's|^#include <malloc.h>|// #include <malloc.h>|' TMalign.cpp
c++ -O3 -ffast-math -o TMalign TMalign.cpp
```

**probe** — use the default `Makefile`, NOT `Makefile.macOSX` (the latter hardcodes a stale 10.8 SDK):
```bash
cd $HOME/tools && git clone --depth=1 https://github.com/rlabduke/probe.git probe-src
cd probe-src && make
```

**reduce** — CMake build:
```bash
cd $HOME/tools && git clone --depth=1 https://github.com/rlabduke/reduce.git reduce-src
cd reduce-src && mkdir build && cd build && cmake .. && make
```

**Servalcat** — conda-forge:
```bash
mamba create -n cryst-oracles -c conda-forge python=3.11 servalcat
```

**gemmi** — Homebrew (the `brewsci/bio` tap):
```bash
brew install brewsci/bio/gemmi
```
