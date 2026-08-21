# Third-party notices

This file records provenance and upstream reuse constraints; it is not a repository-wide license
and grants no additional rights. The repository does not currently have a root `LICENSE` file.

## PHENIX documentation

No PHENIX documentation mirror is included in the repository. `ref/download_phenix_docs.sh` can
create an ignored local cache from <https://phenix-online.org/documentation/> for users who are
authorized to do so. The cache is deliberately excluded from version control and release contents.

PHENIX publishes license terms at <https://phenix-online.org/license>. Those terms treat associated
online or electronic documentation as part of the licensed software and restrict distribution.
Consequently, a locally created cache must not be assumed to be covered by any license later chosen
for this repository and must not be published or redistributed without appropriate authorization.
Preserve all upstream copyright and proprietary notices.

## wwPDB archive materials

The wwPDB usage policy at <https://www.wwpdb.org/about/usage-policies> makes data files in the PDB
archive available under the CC0 1.0 Universal Public Domain Dedication and encourages attribution
to the original structure authors. RCSB PDB gives entry-level citation guidance at
<https://www.rcsb.org/pages/policies>.

CC0 applies only when a committed artifact can be traced to the PDB archive. It must not be used as
a blanket conclusion for transformed agent outputs or third-party examples bundled with software.
See `data/README.md` and the machine-checked `data/pdb_mtz/fixture_provenance.yaml` for the current
file-level record. Rights-unknown legacy fixtures were removed rather than being assigned an
inferred license.

## Tool outputs and publications

Evaluation records, logs, figures, and reports may quote or derive measurements from PHENIX, CCP4,
wwPDB, journal articles, and other tools. Their inclusion does not relicense the underlying tools,
documentation, publications, or deposited data. Retain source identifiers and citations when
reusing those records.
