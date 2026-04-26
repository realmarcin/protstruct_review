from __future__ import annotations

import re
import sys
from datetime import (
    date,
    datetime,
    time
)
from decimal import Decimal
from enum import Enum
from typing import (
    Any,
    ClassVar,
    Literal,
    Optional,
    Union
)

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    RootModel,
    SerializationInfo,
    SerializerFunctionWrapHandler,
    field_validator,
    model_serializer
)


metamodel_version = "None"
version = "None"


class ConfiguredBaseModel(BaseModel):
    model_config = ConfigDict(
        serialize_by_alias = True,
        validate_by_name = True,
        validate_assignment = True,
        validate_default = True,
        extra = "forbid",
        arbitrary_types_allowed = True,
        use_enum_values = True,
        strict = False,
    )

    @model_serializer(mode='wrap', when_used='unless-none')
    def treat_empty_lists_as_none(
            self, handler: SerializerFunctionWrapHandler,
            info: SerializationInfo) -> dict[str, Any]:
        if info.exclude_none:
            _instance = self.model_copy()
            for field, field_info in type(_instance).model_fields.items():
                if getattr(_instance, field) == [] and not(
                        field_info.is_required()):
                    setattr(_instance, field, None)
        else:
            _instance = self
        return handler(_instance, info)



class LinkMLMeta(RootModel):
    root: dict[str, Any] = {}
    model_config = ConfigDict(frozen=True)

    def __getattr__(self, key:str):
        return getattr(self.root, key)

    def __getitem__(self, key:str):
        return self.root[key]

    def __setitem__(self, key:str, value):
        self.root[key] = value

    def __contains__(self, key:str) -> bool:
        return key in self.root


linkml_meta = LinkMLMeta({'default_prefix': 'protstruct',
     'default_range': 'string',
     'description': 'LinkML schema for the protstruct_review harness. Models the '
                    'cross-tool oracle trust framework used to evaluate '
                    'agentically refined or generated protein structures: a static '
                    'catalog of routine structural-biology tasks (T01..T14), the '
                    'tools that perform them, the metrics those tools report, the '
                    "per-artifact evaluation runs that record each tool's reading, "
                    'and the per-structure Quality Data Sheet that snapshots the '
                    'cross-tool findings as a citable record.',
     'id': 'https://w3id.org/protstruct-review/schema',
     'imports': ['linkml:types'],
     'license': 'CC-BY-4.0',
     'name': 'protstruct_review',
     'prefixes': {'linkml': {'prefix_prefix': 'linkml',
                             'prefix_reference': 'https://w3id.org/linkml/'},
                  'protstruct': {'prefix_prefix': 'protstruct',
                                 'prefix_reference': 'https://w3id.org/protstruct-review/schema/'},
                  'schema': {'prefix_prefix': 'schema',
                             'prefix_reference': 'http://schema.org/'}},
     'source_file': '/Users/marcin/Documents/VIMSS/ontology/protstruct_review/schemas/protstruct_review.yaml',
     'title': 'Protein Structure Review — oracles, measurements, evaluations, '
              'quality data sheets'} )

class CatalogTaskId(str, Enum):
    """
    Stable identifier for a row in the task catalog.
    """
    T01 = "T01"
    """
    Structure superposition + RMSD
    """
    T02 = "T02"
    """
    Per-residue structural comparison
    """
    T03 = "T03"
    """
    Reciprocal-space refinement (X-ray)
    """
    T04 = "T04"
    """
    Real-space refinement (map-based)
    """
    T05 = "T05"
    """
    Geometry validation
    """
    T06 = "T06"
    """
    Model-vs-data statistics
    """
    T07 = "T07"
    """
    Predicted-model processing
    """
    T08 = "T08"
    """
    Docking predicted/homology model into a map
    """
    T09 = "T09"
    """
    Molecular replacement
    """
    T10 = "T10"
    """
    Ligand fitting
    """
    T11 = "T11"
    """
    Loop / missing-region fitting
    """
    T12 = "T12"
    """
    Map quality assessment (cryo-EM)
    """
    T13 = "T13"
    """
    X-ray data quality assessment
    """
    T14 = "T14"
    """
    Hydrogen placement / protonation
    """


class ToolFamily(str, Enum):
    """
    Source code lineage of a tool. The trust model treats `non_cctbx` as genuinely independent from PHENIX; `cctbx` includes any tool that shares the cctbx/iotbx/mmtbx libraries (PHENIX, mmtbx.* CLI tools).
    """
    cctbx = "cctbx"
    non_cctbx = "non_cctbx"


class Stage(str, Enum):
    """
    Which stage of an artifact a measurement applies to.
    """
    start = "start"
    """
    Pre-refinement / starting model
    """
    intermediate = "intermediate"
    """
    Mid-refinement (round_N)
    """
    final = "final"
    """
    Post-refinement / converged model
    """
    all = "all"
    """
    Applies to the whole dataset (e.g. completeness across all reflections).
    """


class PassStatus(str, Enum):
    """
    Outcome of a measurement against its declared pass criterion.
    """
    pass_ = "pass"
    """
    Meets the criterion
    """
    fail_by_oracle = "fail_by_oracle"
    """
    Independent oracle disagrees with agent claim and criterion fails
    """
    pass_with_caveat = "pass_with_caveat"
    """
    Criterion passes but a related claim is wrong
    """
    pass_criterion_fail_headline = "pass_criterion_fail_headline"
    """
    Criterion passes but headline number is inaccurate
    """
    fail_by_oracle_within_cctbx = "fail_by_oracle_within_cctbx"
    """
    Two cctbx tools disagree with agent claim — needs a non-cctbx confirmation to harden
    """
    informational = "informational"
    """
    Reported without a declared criterion
    """


class RefinementMethod(str, Enum):
    """
    Experimental / computational method category for a structure.
    """
    xray = "xray"
    cryo_em = "cryo_em"
    predicted_model = "predicted_model"
    nmr = "nmr"


class StructureIdKind(str, Enum):
    """
    Which database scheme the structure id follows.
    """
    pdb = "pdb"
    emdb = "emdb"
    alphafold = "alphafold"


class RecommendationRole(str, Enum):
    """
    Role a tool fills for a given metric. `top_considered` reflects community / literature consensus on the best canonical tool; `top_performing` reflects empirical results within this harness (often the same tool, sometimes not). `alternative` is an acceptable second-line oracle; `deprecated` is kept only for historical reference.
    """
    top_considered = "top_considered"
    top_performing = "top_performing"
    alternative = "alternative"
    deprecated = "deprecated"


class PlddtDistributionShape(str, Enum):
    """
    Coarse classification of the per-residue pLDDT distribution shape. Mean pLDDT alone is insufficient — distribution tells you whether a model is uniformly confident or hides disordered regions.
    """
    bimodal_sharp = "bimodal_sharp"
    """
    Confident core + disordered tails.
    """
    broad = "broad"
    """
    Uncertain throughout (broad spread centred on mid-range).
    """
    narrow_high = "narrow_high"
    """
    Uniformly confident.
    """
    narrow_low = "narrow_low"
    """
    Uniformly uncertain (suspicious).
    """


class ReferenceKind(str, Enum):
    """
    What kind of reference the candidate is being compared against.
    """
    deposited = "deposited"
    """
    A PDB/EMDB deposited entry treated as the gold standard.
    """
    alphafold = "alphafold"
    """
    An AlphaFold/RoseTTAFold prediction used as reference.
    """
    starting_model = "starting_model"
    """
    The model the agent was given to refine.
    """
    ground_truth = "ground_truth"
    """
    A benchmark "truth" (e.g., ultra-high-res reference).
    """
    consensus = "consensus"
    """
    A multi-tool consensus or PDB-REDO style re-refinement.
    """


class DeltaBaseline(str, Enum):
    """
    Which baseline a Δ-metric is measured against.
    """
    starting_model = "starting_model"
    """
    Δ measured against the input / starting model.
    """
    reference_truth = "reference_truth"
    """
    Δ measured against an independent gold standard.
    """
    same_data_reference = "same_data_reference"
    """
    Δ measured against another model refined against the same data.
    """



class Container(ConfiguredBaseModel):
    """
    Tree root. A single YAML document can carry any subset of the catalog and per-run records. Nothing is required at this level — pass the sub-collections you have.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://w3id.org/protstruct-review/schema', 'tree_root': True})

    catalog_tasks: Optional[list[CatalogTask]] = Field(default=[], json_schema_extra = { "linkml_meta": {'domain_of': ['Container']} })
    tools: Optional[list[Tool]] = Field(default=[], json_schema_extra = { "linkml_meta": {'domain_of': ['Container']} })
    metric_definitions: Optional[list[MetricDefinition]] = Field(default=[], json_schema_extra = { "linkml_meta": {'domain_of': ['Container']} })
    structures: Optional[list[Structure]] = Field(default=[], json_schema_extra = { "linkml_meta": {'domain_of': ['Container']} })
    experimental_data: Optional[list[ExperimentalData]] = Field(default=[], json_schema_extra = { "linkml_meta": {'domain_of': ['Container']} })
    agent_artifacts: Optional[list[AgentArtifact]] = Field(default=[], json_schema_extra = { "linkml_meta": {'domain_of': ['Container']} })
    evaluation_runs: Optional[list[EvaluationRun]] = Field(default=[], json_schema_extra = { "linkml_meta": {'domain_of': ['Container']} })
    quality_data_sheets: Optional[list[QualityDataSheet]] = Field(default=[], json_schema_extra = { "linkml_meta": {'domain_of': ['Container']} })
    tool_recommendations: Optional[list[ToolRecommendation]] = Field(default=[], json_schema_extra = { "linkml_meta": {'domain_of': ['Container']} })
    pairwise_comparisons: Optional[list[PairwiseComparison]] = Field(default=[], json_schema_extra = { "linkml_meta": {'domain_of': ['Container', 'QualityDataSheet']} })


class Finding(ConfiguredBaseModel):
    """
    Shared shape between per-row measurements and headline collapses — both ultimately tie a (catalog_task, metric, oracle_tool) tuple to a number plus optional notes.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://w3id.org/protstruct-review/schema', 'mixin': True})

    metric_definition_ref: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Finding',
                       'MeasurementValue',
                       'HeadlineFinding',
                       'ToolRecommendation']} })
    oracle_tool_ref: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Finding', 'MeasurementValue', 'HeadlineFinding']} })
    oracle_family: ToolFamily = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Finding', 'MeasurementValue', 'HeadlineFinding']} })
    notes: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['Finding',
                       'MeasurementValue',
                       'HeadlineFinding',
                       'ToolRecommendation']} })


class CatalogTask(ConfiguredBaseModel):
    """
    One row in the T01..T14 task catalog.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://w3id.org/protstruct-review/schema'})

    id: CatalogTaskId = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['CatalogTask',
                       'Tool',
                       'MetricDefinition',
                       'Structure',
                       'ExperimentalData',
                       'AgentArtifact',
                       'Refinement',
                       'MeasurementProvenance',
                       'MeasurementValue',
                       'HeadlineFinding',
                       'EvaluationRun',
                       'QualityDataSheet',
                       'IdentityBlock',
                       'GeometrySummary',
                       'RefinementSummary',
                       'MapSummary',
                       'CrossToolCoverage',
                       'TaskCoverage',
                       'DataQualitySummary',
                       'PredictedConfidenceSummary',
                       'PairwiseComparison',
                       'ToolRecommendation']} })
    task_name: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['CatalogTask']} })
    phenix_tool_refs: Optional[list[str]] = Field(default=[], description="""PHENIX tools that primarily implement this task.""", json_schema_extra = { "linkml_meta": {'domain_of': ['CatalogTask']} })
    phenix_doc_paths: Optional[list[str]] = Field(default=[], description="""Doc paths under ref/phenix_docs/phenix-online.org/documentation/.""", json_schema_extra = { "linkml_meta": {'domain_of': ['CatalogTask']} })
    oracle_tool_refs: Optional[list[str]] = Field(default=[], description="""Independent (typically non-cctbx) oracles the harness uses to grade this task.""", json_schema_extra = { "linkml_meta": {'domain_of': ['CatalogTask']} })
    metric_definition_refs: Optional[list[str]] = Field(default=[], description="""Metrics this task is expected to produce.""", json_schema_extra = { "linkml_meta": {'domain_of': ['CatalogTask']} })
    inputs_description: Optional[str] = Field(default=None, description="""Human prose describing typical inputs (file types, optional flags).""", json_schema_extra = { "linkml_meta": {'domain_of': ['CatalogTask']} })
    gold_standard: Optional[str] = Field(default=None, description="""Source of truth (deposition, paper, cross-tool consensus).""", json_schema_extra = { "linkml_meta": {'domain_of': ['CatalogTask']} })
    example_dataset: Optional[str] = Field(default=None, description="""A concrete dataset id (PDB/EMDB/MTZ) so a run is reproducible.""", json_schema_extra = { "linkml_meta": {'domain_of': ['CatalogTask']} })


class Tool(ConfiguredBaseModel):
    """
    A program executable — PHENIX entry point or external oracle.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://w3id.org/protstruct-review/schema'})

    id: str = Field(default=..., description="""Canonical tool name (e.g. phenix.superpose_models, TMalign, gemmi, probe, reduce, servalcat).""", json_schema_extra = { "linkml_meta": {'domain_of': ['CatalogTask',
                       'Tool',
                       'MetricDefinition',
                       'Structure',
                       'ExperimentalData',
                       'AgentArtifact',
                       'Refinement',
                       'MeasurementProvenance',
                       'MeasurementValue',
                       'HeadlineFinding',
                       'EvaluationRun',
                       'QualityDataSheet',
                       'IdentityBlock',
                       'GeometrySummary',
                       'RefinementSummary',
                       'MapSummary',
                       'CrossToolCoverage',
                       'TaskCoverage',
                       'DataQualitySummary',
                       'PredictedConfidenceSummary',
                       'PairwiseComparison',
                       'ToolRecommendation']} })
    version: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['Tool']} })
    install_path: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['Tool']} })
    family: ToolFamily = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Tool']} })
    catalog_tasks_served: Optional[list[CatalogTaskId]] = Field(default=[], json_schema_extra = { "linkml_meta": {'domain_of': ['Tool']} })


class MetricDefinition(ConfiguredBaseModel):
    """
    A named numeric deliverable that one or more tools can produce.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://w3id.org/protstruct-review/schema'})

    id: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['CatalogTask',
                       'Tool',
                       'MetricDefinition',
                       'Structure',
                       'ExperimentalData',
                       'AgentArtifact',
                       'Refinement',
                       'MeasurementProvenance',
                       'MeasurementValue',
                       'HeadlineFinding',
                       'EvaluationRun',
                       'QualityDataSheet',
                       'IdentityBlock',
                       'GeometrySummary',
                       'RefinementSummary',
                       'MapSummary',
                       'CrossToolCoverage',
                       'TaskCoverage',
                       'DataQualitySummary',
                       'PredictedConfidenceSummary',
                       'PairwiseComparison',
                       'ToolRecommendation']} })
    name: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['MetricDefinition']} })
    unit: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['MetricDefinition', 'TypedMeasurementValue']} })
    description: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['MetricDefinition', 'Structure', 'IdentityBlock']} })
    applicable_task_refs: Optional[list[CatalogTaskId]] = Field(default=[], json_schema_extra = { "linkml_meta": {'domain_of': ['MetricDefinition']} })


class Structure(ConfiguredBaseModel):
    """
    A protein structure target (model only — see ExperimentalData for the data side).
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://w3id.org/protstruct-review/schema'})

    id: str = Field(default=..., description="""PDB id (e.g. 1sar), EMDB id (EMDB-11668), or AlphaFold accession (af-p00698-f1).""", json_schema_extra = { "linkml_meta": {'domain_of': ['CatalogTask',
                       'Tool',
                       'MetricDefinition',
                       'Structure',
                       'ExperimentalData',
                       'AgentArtifact',
                       'Refinement',
                       'MeasurementProvenance',
                       'MeasurementValue',
                       'HeadlineFinding',
                       'EvaluationRun',
                       'QualityDataSheet',
                       'IdentityBlock',
                       'GeometrySummary',
                       'RefinementSummary',
                       'MapSummary',
                       'CrossToolCoverage',
                       'TaskCoverage',
                       'DataQualitySummary',
                       'PredictedConfidenceSummary',
                       'PairwiseComparison',
                       'ToolRecommendation']} })
    id_kind: Optional[StructureIdKind] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['Structure']} })
    method: Optional[RefinementMethod] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['Structure', 'IdentityBlock']} })
    resolution_a: Optional[float] = Field(default=None, description="""Best resolution in Ångström, where applicable.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Structure', 'IdentityBlock']} })
    space_group: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['Structure', 'IdentityBlock']} })
    description: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['MetricDefinition', 'Structure', 'IdentityBlock']} })


class ExperimentalData(ConfiguredBaseModel):
    """
    Reflection data, half-maps, or similar — the data side of an experiment.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://w3id.org/protstruct-review/schema'})

    id: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['CatalogTask',
                       'Tool',
                       'MetricDefinition',
                       'Structure',
                       'ExperimentalData',
                       'AgentArtifact',
                       'Refinement',
                       'MeasurementProvenance',
                       'MeasurementValue',
                       'HeadlineFinding',
                       'EvaluationRun',
                       'QualityDataSheet',
                       'IdentityBlock',
                       'GeometrySummary',
                       'RefinementSummary',
                       'MapSummary',
                       'CrossToolCoverage',
                       'TaskCoverage',
                       'DataQualitySummary',
                       'PredictedConfidenceSummary',
                       'PairwiseComparison',
                       'ToolRecommendation']} })
    kind: Optional[str] = Field(default=None, description="""One of mtz, half_maps, map.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ExperimentalData']} })
    attached_to_structure_ref: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['ExperimentalData']} })
    file_paths: Optional[list[str]] = Field(default=[], json_schema_extra = { "linkml_meta": {'domain_of': ['ExperimentalData']} })


class AgentArtifact(ConfiguredBaseModel):
    """
    A bundle of files an agent produced for one structure.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://w3id.org/protstruct-review/schema'})

    id: str = Field(default=..., description="""Full UUID of the agent run, or any other stable id.""", json_schema_extra = { "linkml_meta": {'domain_of': ['CatalogTask',
                       'Tool',
                       'MetricDefinition',
                       'Structure',
                       'ExperimentalData',
                       'AgentArtifact',
                       'Refinement',
                       'MeasurementProvenance',
                       'MeasurementValue',
                       'HeadlineFinding',
                       'EvaluationRun',
                       'QualityDataSheet',
                       'IdentityBlock',
                       'GeometrySummary',
                       'RefinementSummary',
                       'MapSummary',
                       'CrossToolCoverage',
                       'TaskCoverage',
                       'DataQualitySummary',
                       'PredictedConfidenceSummary',
                       'PairwiseComparison',
                       'ToolRecommendation']} })
    short_id: Optional[str] = Field(default=None, description="""First 8 hex chars of the UUID (matches eval-naming convention).""", json_schema_extra = { "linkml_meta": {'domain_of': ['AgentArtifact']} })
    structure_ref: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['AgentArtifact', 'EvaluationRun', 'QualityDataSheet']} })
    agent_provider: Optional[str] = Field(default=None, description="""e.g. coscientists.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AgentArtifact']} })
    agent_system: Optional[str] = Field(default=None, description="""e.g. openscientist.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AgentArtifact']} })
    output_files: Optional[list[str]] = Field(default=[], json_schema_extra = { "linkml_meta": {'domain_of': ['AgentArtifact']} })


class Refinement(ConfiguredBaseModel):
    """
    One round of model improvement. Optional at v0 — fill in for multi-round T03 work.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://w3id.org/protstruct-review/schema'})

    id: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['CatalogTask',
                       'Tool',
                       'MetricDefinition',
                       'Structure',
                       'ExperimentalData',
                       'AgentArtifact',
                       'Refinement',
                       'MeasurementProvenance',
                       'MeasurementValue',
                       'HeadlineFinding',
                       'EvaluationRun',
                       'QualityDataSheet',
                       'IdentityBlock',
                       'GeometrySummary',
                       'RefinementSummary',
                       'MapSummary',
                       'CrossToolCoverage',
                       'TaskCoverage',
                       'DataQualitySummary',
                       'PredictedConfidenceSummary',
                       'PairwiseComparison',
                       'ToolRecommendation']} })
    round_number: int = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Refinement']} })
    model_file: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['Refinement']} })
    mtz_file: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['Refinement']} })
    evaluation_run_ref: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['Refinement']} })


class MeasurementProvenance(ConfiguredBaseModel):
    """
    Audit trail for a measurement (optional at v0).
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://w3id.org/protstruct-review/schema'})

    id: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['CatalogTask',
                       'Tool',
                       'MetricDefinition',
                       'Structure',
                       'ExperimentalData',
                       'AgentArtifact',
                       'Refinement',
                       'MeasurementProvenance',
                       'MeasurementValue',
                       'HeadlineFinding',
                       'EvaluationRun',
                       'QualityDataSheet',
                       'IdentityBlock',
                       'GeometrySummary',
                       'RefinementSummary',
                       'MapSummary',
                       'CrossToolCoverage',
                       'TaskCoverage',
                       'DataQualitySummary',
                       'PredictedConfidenceSummary',
                       'PairwiseComparison',
                       'ToolRecommendation']} })
    command: Optional[str] = Field(default=None, description="""Exact CLI invocation (excluding interactive arguments).""", json_schema_extra = { "linkml_meta": {'domain_of': ['MeasurementProvenance']} })
    tool_version: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['MeasurementProvenance']} })
    input_sha256: Optional[list[str]] = Field(default=[], description="""SHA-256 of each input file, in invocation order.""", json_schema_extra = { "linkml_meta": {'domain_of': ['MeasurementProvenance']} })
    run_at: Optional[datetime ] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['MeasurementProvenance']} })


class MeasurementValue(Finding):
    """
    One oracle's reading of one metric at one stage on one artifact.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://w3id.org/protstruct-review/schema',
         'mixins': ['Finding']})

    id: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['CatalogTask',
                       'Tool',
                       'MetricDefinition',
                       'Structure',
                       'ExperimentalData',
                       'AgentArtifact',
                       'Refinement',
                       'MeasurementProvenance',
                       'MeasurementValue',
                       'HeadlineFinding',
                       'EvaluationRun',
                       'QualityDataSheet',
                       'IdentityBlock',
                       'GeometrySummary',
                       'RefinementSummary',
                       'MapSummary',
                       'CrossToolCoverage',
                       'TaskCoverage',
                       'DataQualitySummary',
                       'PredictedConfidenceSummary',
                       'PairwiseComparison',
                       'ToolRecommendation']} })
    catalog_task_ref: CatalogTaskId = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['MeasurementValue', 'TaskCoverage']} })
    stage: Stage = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['MeasurementValue']} })
    metric_definition_ref: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['Finding',
                       'MeasurementValue',
                       'HeadlineFinding',
                       'ToolRecommendation']} })
    oracle_tool_ref: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['Finding', 'MeasurementValue', 'HeadlineFinding']} })
    oracle_family: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['Finding', 'MeasurementValue', 'HeadlineFinding']} })
    agent_claim: Optional[TypedMeasurementValue] = Field(default=None, description="""Value reported by the agent.""", json_schema_extra = { "linkml_meta": {'domain_of': ['MeasurementValue', 'HeadlineFinding']} })
    oracle_measure: Optional[TypedMeasurementValue] = Field(default=None, description="""Value the independent oracle returned.""", json_schema_extra = { "linkml_meta": {'domain_of': ['MeasurementValue', 'HeadlineFinding']} })
    delta: Optional[TypedMeasurementValue] = Field(default=None, description="""Optional pre-computed difference (oracle − agent or post − pre).""", json_schema_extra = { "linkml_meta": {'domain_of': ['MeasurementValue']} })
    pass_criterion: Optional[str] = Field(default=None, description="""Free-text pass criterion (e.g. \"< 0.05\", \"match within 0.005\").""", json_schema_extra = { "linkml_meta": {'domain_of': ['MeasurementValue']} })
    pass_status: Optional[PassStatus] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['MeasurementValue']} })
    notes: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['Finding',
                       'MeasurementValue',
                       'HeadlineFinding',
                       'ToolRecommendation']} })
    provenance_ref: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['MeasurementValue']} })


class TypedMeasurementValue(ConfiguredBaseModel):
    """
    A typed carrier for one measurement value. Exactly one of {value_numeric, value_text, is_not_applicable=true} should be set — enforced semantically by the loader, not by a LinkML rule (LinkML `rules:` for cross-slot constraints are not honoured by all validators in 1.9; see scripts/tsv_to_records.py for the canonical cell parser that always produces a valid combination).
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://w3id.org/protstruct-review/schema'})

    value_numeric: Optional[float] = Field(default=None, description="""Numeric value when the cell is a clean number.""", json_schema_extra = { "linkml_meta": {'domain_of': ['TypedMeasurementValue']} })
    value_text: Optional[str] = Field(default=None, description="""Non-numeric textual value (ranges like \"49.97 → 2.50\", counts with annotation like \"1 (Asn A 39)\", percentages, or any cell that is not a clean number).""", json_schema_extra = { "linkml_meta": {'domain_of': ['TypedMeasurementValue']} })
    unit: Optional[str] = Field(default=None, description="""Unit string (Å, °, %, σ, count). Optional.""", json_schema_extra = { "linkml_meta": {'domain_of': ['MetricDefinition', 'TypedMeasurementValue']} })
    is_not_applicable: Optional[bool] = Field(default=None, description="""True when the source cell is \"n/a\" or otherwise has no measurement.""", json_schema_extra = { "linkml_meta": {'domain_of': ['TypedMeasurementValue']} })
    percentile: Optional[float] = Field(default=None, description="""Optional rank against a reference distribution (e.g., wwPDB archive percentile for clashscore at this resolution; CASP ranking for TM-score). Range 0-100. Cite the source dataset in `notes` on the parent measurement.""", json_schema_extra = { "linkml_meta": {'domain_of': ['TypedMeasurementValue']} })


class HeadlineFinding(Finding):
    """
    A collapsed top-level finding for one EvaluationRun — typically one row per major metric, picking the strongest oracle (most independent) and pointing back at the supporting per-row MeasurementValues.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://w3id.org/protstruct-review/schema',
         'mixins': ['Finding']})

    id: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['CatalogTask',
                       'Tool',
                       'MetricDefinition',
                       'Structure',
                       'ExperimentalData',
                       'AgentArtifact',
                       'Refinement',
                       'MeasurementProvenance',
                       'MeasurementValue',
                       'HeadlineFinding',
                       'EvaluationRun',
                       'QualityDataSheet',
                       'IdentityBlock',
                       'GeometrySummary',
                       'RefinementSummary',
                       'MapSummary',
                       'CrossToolCoverage',
                       'TaskCoverage',
                       'DataQualitySummary',
                       'PredictedConfidenceSummary',
                       'PairwiseComparison',
                       'ToolRecommendation']} })
    catalog_task_refs: list[CatalogTaskId] = Field(default=..., description="""One or more catalog tasks this finding spans (e.g. T03 + T06 for R-factor).""", json_schema_extra = { "linkml_meta": {'domain_of': ['HeadlineFinding']} })
    metric_definition_ref: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['Finding',
                       'MeasurementValue',
                       'HeadlineFinding',
                       'ToolRecommendation']} })
    oracle_tool_ref: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['Finding', 'MeasurementValue', 'HeadlineFinding']} })
    oracle_family: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['Finding', 'MeasurementValue', 'HeadlineFinding']} })
    agent_claim: Optional[TypedMeasurementValue] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['MeasurementValue', 'HeadlineFinding']} })
    oracle_measure: Optional[TypedMeasurementValue] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['MeasurementValue', 'HeadlineFinding']} })
    verdict_label: Optional[str] = Field(default=None, description="""Free-text label such as \"confirms\", \"off_by_0.015\", \"fails_<_0.05_criterion\". Not an enum at v0 — the label space is still settling.""", json_schema_extra = { "linkml_meta": {'domain_of': ['HeadlineFinding']} })
    notes: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['Finding',
                       'MeasurementValue',
                       'HeadlineFinding',
                       'ToolRecommendation']} })
    supporting_measurement_refs: Optional[list[str]] = Field(default=[], json_schema_extra = { "linkml_meta": {'domain_of': ['HeadlineFinding']} })


class EvaluationRun(ConfiguredBaseModel):
    """
    One full evaluation pass over one AgentArtifact.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://w3id.org/protstruct-review/schema'})

    id: str = Field(default=..., description="""Unconstrained string. The eval_naming.md filename convention (EVAL_<structure>_<artifact-short-id>_<YYYY-MM-DD>) lives on eval_filename_stem, not here.""", json_schema_extra = { "linkml_meta": {'domain_of': ['CatalogTask',
                       'Tool',
                       'MetricDefinition',
                       'Structure',
                       'ExperimentalData',
                       'AgentArtifact',
                       'Refinement',
                       'MeasurementProvenance',
                       'MeasurementValue',
                       'HeadlineFinding',
                       'EvaluationRun',
                       'QualityDataSheet',
                       'IdentityBlock',
                       'GeometrySummary',
                       'RefinementSummary',
                       'MapSummary',
                       'CrossToolCoverage',
                       'TaskCoverage',
                       'DataQualitySummary',
                       'PredictedConfidenceSummary',
                       'PairwiseComparison',
                       'ToolRecommendation']} })
    eval_filename_stem: Optional[str] = Field(default=None, description="""Filename stem matching ref/eval_naming.md.""", json_schema_extra = { "linkml_meta": {'domain_of': ['EvaluationRun']} })
    structure_ref: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['AgentArtifact', 'EvaluationRun', 'QualityDataSheet']} })
    artifact_ref: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['EvaluationRun']} })
    run_date: date = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['EvaluationRun']} })
    catalog_tasks_applied: list[CatalogTaskId] = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['EvaluationRun']} })
    measurements: Optional[list[MeasurementValue]] = Field(default=[], json_schema_extra = { "linkml_meta": {'domain_of': ['EvaluationRun']} })
    headline_findings: Optional[list[HeadlineFinding]] = Field(default=[], json_schema_extra = { "linkml_meta": {'domain_of': ['EvaluationRun']} })
    criteria_met_count: Optional[int] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['EvaluationRun']} })
    criteria_total: Optional[int] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['EvaluationRun']} })
    headline_verdict: Optional[str] = Field(default=None, description="""One-paragraph human summary of the eval outcome.""", json_schema_extra = { "linkml_meta": {'domain_of': ['EvaluationRun', 'QualityDataSheet']} })


class QualityDataSheet(ConfiguredBaseModel):
    """
    Per-structure citable snapshot of cross-tool findings. Generated from one or more EvaluationRun records by scripts/qds_emit.py and treated as immutable: when oracles change or new measurements arrive, emit a new QDS (different id / issued_at), don't mutate the old one.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://w3id.org/protstruct-review/schema'})

    id: str = Field(default=..., description="""e.g. QDS_1sar_cdba2c07_2026-04-24""", json_schema_extra = { "linkml_meta": {'domain_of': ['CatalogTask',
                       'Tool',
                       'MetricDefinition',
                       'Structure',
                       'ExperimentalData',
                       'AgentArtifact',
                       'Refinement',
                       'MeasurementProvenance',
                       'MeasurementValue',
                       'HeadlineFinding',
                       'EvaluationRun',
                       'QualityDataSheet',
                       'IdentityBlock',
                       'GeometrySummary',
                       'RefinementSummary',
                       'MapSummary',
                       'CrossToolCoverage',
                       'TaskCoverage',
                       'DataQualitySummary',
                       'PredictedConfidenceSummary',
                       'PairwiseComparison',
                       'ToolRecommendation']} })
    structure_ref: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['AgentArtifact', 'EvaluationRun', 'QualityDataSheet']} })
    derived_from_evaluation_run_refs: list[str] = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['QualityDataSheet']} })
    issued_at: datetime  = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['QualityDataSheet']} })
    identity_block: Optional[IdentityBlock] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['QualityDataSheet']} })
    geometry_summary: Optional[GeometrySummary] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['QualityDataSheet']} })
    refinement_summary: Optional[RefinementSummary] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['QualityDataSheet']} })
    map_summary: Optional[MapSummary] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['QualityDataSheet']} })
    data_quality_summary: Optional[DataQualitySummary] = Field(default=None, description="""X-ray data quality (completeness, ⟨I/σ⟩, CC½). Optional; omit for cryo-EM and predicted models.""", json_schema_extra = { "linkml_meta": {'domain_of': ['QualityDataSheet']} })
    predicted_confidence_summary: Optional[PredictedConfidenceSummary] = Field(default=None, description="""AlphaFold/RoseTTAFold confidence (pLDDT distribution, PAE). Optional; only for predicted models.""", json_schema_extra = { "linkml_meta": {'domain_of': ['QualityDataSheet']} })
    pairwise_comparisons: Optional[list[PairwiseComparison]] = Field(default=[], description="""One per relevant reference (deposited / starting / AlphaFold / truth). Empty when no reference comparison applies.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Container', 'QualityDataSheet']} })
    cross_tool_coverage: Optional[CrossToolCoverage] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['QualityDataSheet']} })
    tool_recommendations_applied: Optional[list[ToolRecommendation]] = Field(default=[], description="""Snapshot of which recommendations were active at issue time. The QDS is immutable; recommendations evolve, so this captures the recommendations as-of issued_at.""", json_schema_extra = { "linkml_meta": {'domain_of': ['QualityDataSheet']} })
    headline_verdict: Optional[str] = Field(default=None, description="""One-paragraph pinned summary as of issued_at.""", json_schema_extra = { "linkml_meta": {'domain_of': ['EvaluationRun', 'QualityDataSheet']} })


class IdentityBlock(ConfiguredBaseModel):
    """
    Identity facts about the structure being evaluated.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://w3id.org/protstruct-review/schema'})

    id: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['CatalogTask',
                       'Tool',
                       'MetricDefinition',
                       'Structure',
                       'ExperimentalData',
                       'AgentArtifact',
                       'Refinement',
                       'MeasurementProvenance',
                       'MeasurementValue',
                       'HeadlineFinding',
                       'EvaluationRun',
                       'QualityDataSheet',
                       'IdentityBlock',
                       'GeometrySummary',
                       'RefinementSummary',
                       'MapSummary',
                       'CrossToolCoverage',
                       'TaskCoverage',
                       'DataQualitySummary',
                       'PredictedConfidenceSummary',
                       'PairwiseComparison',
                       'ToolRecommendation']} })
    pdb_id: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['IdentityBlock']} })
    emdb_id: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['IdentityBlock']} })
    alphafold_id: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['IdentityBlock']} })
    method: Optional[RefinementMethod] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['Structure', 'IdentityBlock']} })
    resolution_a: Optional[float] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['Structure', 'IdentityBlock']} })
    space_group: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['Structure', 'IdentityBlock']} })
    description: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['MetricDefinition', 'Structure', 'IdentityBlock']} })


class GeometrySummary(ConfiguredBaseModel):
    """
    Headline geometry numbers as of QDS issue date.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://w3id.org/protstruct-review/schema'})

    id: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['CatalogTask',
                       'Tool',
                       'MetricDefinition',
                       'Structure',
                       'ExperimentalData',
                       'AgentArtifact',
                       'Refinement',
                       'MeasurementProvenance',
                       'MeasurementValue',
                       'HeadlineFinding',
                       'EvaluationRun',
                       'QualityDataSheet',
                       'IdentityBlock',
                       'GeometrySummary',
                       'RefinementSummary',
                       'MapSummary',
                       'CrossToolCoverage',
                       'TaskCoverage',
                       'DataQualitySummary',
                       'PredictedConfidenceSummary',
                       'PairwiseComparison',
                       'ToolRecommendation']} })
    clashscore: Optional[TypedMeasurementValue] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['GeometrySummary']} })
    ramachandran_outliers_pct: Optional[TypedMeasurementValue] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['GeometrySummary']} })
    ramachandran_favored_pct: Optional[TypedMeasurementValue] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['GeometrySummary']} })
    rotamer_outliers_pct: Optional[TypedMeasurementValue] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['GeometrySummary']} })
    molprobity_score: Optional[TypedMeasurementValue] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['GeometrySummary']} })
    bond_rmsd_a: Optional[TypedMeasurementValue] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['GeometrySummary']} })
    angle_rmsd_deg: Optional[TypedMeasurementValue] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['GeometrySummary']} })


class RefinementSummary(ConfiguredBaseModel):
    """
    Headline R-factors as of QDS issue date (X-ray refinement only).
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://w3id.org/protstruct-review/schema'})

    id: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['CatalogTask',
                       'Tool',
                       'MetricDefinition',
                       'Structure',
                       'ExperimentalData',
                       'AgentArtifact',
                       'Refinement',
                       'MeasurementProvenance',
                       'MeasurementValue',
                       'HeadlineFinding',
                       'EvaluationRun',
                       'QualityDataSheet',
                       'IdentityBlock',
                       'GeometrySummary',
                       'RefinementSummary',
                       'MapSummary',
                       'CrossToolCoverage',
                       'TaskCoverage',
                       'DataQualitySummary',
                       'PredictedConfidenceSummary',
                       'PairwiseComparison',
                       'ToolRecommendation']} })
    r_work: Optional[TypedMeasurementValue] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['RefinementSummary']} })
    r_free: Optional[TypedMeasurementValue] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['RefinementSummary']} })
    r_free_gap: Optional[TypedMeasurementValue] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['RefinementSummary']} })


class MapSummary(ConfiguredBaseModel):
    """
    Headline map quality numbers as of QDS issue date (cryo-EM only).
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://w3id.org/protstruct-review/schema'})

    id: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['CatalogTask',
                       'Tool',
                       'MetricDefinition',
                       'Structure',
                       'ExperimentalData',
                       'AgentArtifact',
                       'Refinement',
                       'MeasurementProvenance',
                       'MeasurementValue',
                       'HeadlineFinding',
                       'EvaluationRun',
                       'QualityDataSheet',
                       'IdentityBlock',
                       'GeometrySummary',
                       'RefinementSummary',
                       'MapSummary',
                       'CrossToolCoverage',
                       'TaskCoverage',
                       'DataQualitySummary',
                       'PredictedConfidenceSummary',
                       'PairwiseComparison',
                       'ToolRecommendation']} })
    cc_mask: Optional[TypedMeasurementValue] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['MapSummary']} })
    d_fsc_model_a: Optional[TypedMeasurementValue] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['MapSummary']} })


class CrossToolCoverage(ConfiguredBaseModel):
    """
    Per-task summary of which tool families confirmed each measurement. The point of the QDS is to make it obvious where the trust model is strong (cctbx + non-cctbx agree) vs weak (cctbx only).
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://w3id.org/protstruct-review/schema'})

    id: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['CatalogTask',
                       'Tool',
                       'MetricDefinition',
                       'Structure',
                       'ExperimentalData',
                       'AgentArtifact',
                       'Refinement',
                       'MeasurementProvenance',
                       'MeasurementValue',
                       'HeadlineFinding',
                       'EvaluationRun',
                       'QualityDataSheet',
                       'IdentityBlock',
                       'GeometrySummary',
                       'RefinementSummary',
                       'MapSummary',
                       'CrossToolCoverage',
                       'TaskCoverage',
                       'DataQualitySummary',
                       'PredictedConfidenceSummary',
                       'PairwiseComparison',
                       'ToolRecommendation']} })
    task_coverage: Optional[list[TaskCoverage]] = Field(default=[], json_schema_extra = { "linkml_meta": {'domain_of': ['CrossToolCoverage']} })


class TaskCoverage(ConfiguredBaseModel):
    """
    One row in CrossToolCoverage — which oracles ran for this catalog task.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://w3id.org/protstruct-review/schema'})

    id: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['CatalogTask',
                       'Tool',
                       'MetricDefinition',
                       'Structure',
                       'ExperimentalData',
                       'AgentArtifact',
                       'Refinement',
                       'MeasurementProvenance',
                       'MeasurementValue',
                       'HeadlineFinding',
                       'EvaluationRun',
                       'QualityDataSheet',
                       'IdentityBlock',
                       'GeometrySummary',
                       'RefinementSummary',
                       'MapSummary',
                       'CrossToolCoverage',
                       'TaskCoverage',
                       'DataQualitySummary',
                       'PredictedConfidenceSummary',
                       'PairwiseComparison',
                       'ToolRecommendation']} })
    catalog_task_ref: CatalogTaskId = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['MeasurementValue', 'TaskCoverage']} })
    cctbx_oracles: Optional[list[str]] = Field(default=[], json_schema_extra = { "linkml_meta": {'domain_of': ['TaskCoverage']} })
    non_cctbx_oracles: Optional[list[str]] = Field(default=[], json_schema_extra = { "linkml_meta": {'domain_of': ['TaskCoverage']} })
    gap_status: Optional[str] = Field(default=None, description="""Free-text (e.g. \"closed\", \"closed at clashscore\", \"open — needs standalone Rama-Z\"). Settling into an enum once we see more data.""", json_schema_extra = { "linkml_meta": {'domain_of': ['TaskCoverage']} })


class DataQualitySummary(ConfiguredBaseModel):
    """
    X-ray data-quality numbers — bound the model quality from below. Live in the QDS for X-ray structures; absent for cryo-EM and predicted. Sources: data-processing log, phenix.xtriage, CCP4 aimless, gemmi.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://w3id.org/protstruct-review/schema'})

    id: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['CatalogTask',
                       'Tool',
                       'MetricDefinition',
                       'Structure',
                       'ExperimentalData',
                       'AgentArtifact',
                       'Refinement',
                       'MeasurementProvenance',
                       'MeasurementValue',
                       'HeadlineFinding',
                       'EvaluationRun',
                       'QualityDataSheet',
                       'IdentityBlock',
                       'GeometrySummary',
                       'RefinementSummary',
                       'MapSummary',
                       'CrossToolCoverage',
                       'TaskCoverage',
                       'DataQualitySummary',
                       'PredictedConfidenceSummary',
                       'PairwiseComparison',
                       'ToolRecommendation']} })
    completeness_overall_pct: Optional[TypedMeasurementValue] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['DataQualitySummary']} })
    completeness_outer_shell_pct: Optional[TypedMeasurementValue] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['DataQualitySummary']} })
    mean_i_over_sigma_outer: Optional[TypedMeasurementValue] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['DataQualitySummary']} })
    cc_half_outer: Optional[TypedMeasurementValue] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['DataQualitySummary']} })
    r_merge: Optional[TypedMeasurementValue] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['DataQualitySummary']} })
    r_meas: Optional[TypedMeasurementValue] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['DataQualitySummary']} })
    wilson_b: Optional[TypedMeasurementValue] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['DataQualitySummary']} })


class PredictedConfidenceSummary(ConfiguredBaseModel):
    """
    AlphaFold/RoseTTAFold confidence summary. Mean pLDDT alone is insufficient — distribution shape is what tells you whether a model is uniformly confident or hides disordered regions.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://w3id.org/protstruct-review/schema'})

    id: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['CatalogTask',
                       'Tool',
                       'MetricDefinition',
                       'Structure',
                       'ExperimentalData',
                       'AgentArtifact',
                       'Refinement',
                       'MeasurementProvenance',
                       'MeasurementValue',
                       'HeadlineFinding',
                       'EvaluationRun',
                       'QualityDataSheet',
                       'IdentityBlock',
                       'GeometrySummary',
                       'RefinementSummary',
                       'MapSummary',
                       'CrossToolCoverage',
                       'TaskCoverage',
                       'DataQualitySummary',
                       'PredictedConfidenceSummary',
                       'PairwiseComparison',
                       'ToolRecommendation']} })
    predictor: Optional[str] = Field(default=None, description="""e.g. AlphaFold2, AlphaFold3, RoseTTAFold, ESMFold.""", json_schema_extra = { "linkml_meta": {'domain_of': ['PredictedConfidenceSummary']} })
    predictor_version: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['PredictedConfidenceSummary']} })
    mean_plddt: Optional[TypedMeasurementValue] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['PredictedConfidenceSummary']} })
    plddt_distribution_shape: Optional[PlddtDistributionShape] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['PredictedConfidenceSummary']} })
    pae_max_a: Optional[TypedMeasurementValue] = Field(default=None, description="""Maximum PAE in Å across the matrix.""", json_schema_extra = { "linkml_meta": {'domain_of': ['PredictedConfidenceSummary']} })
    pae_multimer_block_min_a: Optional[TypedMeasurementValue] = Field(default=None, description="""For multimers — the minimum PAE in the off-diagonal block between subunits. Low values indicate confident inter-subunit placement; > 15 Å typically unreliable.""", json_schema_extra = { "linkml_meta": {'domain_of': ['PredictedConfidenceSummary']} })


class PairwiseComparison(ConfiguredBaseModel):
    """
    Candidate vs reference structure comparison. Modern default per ref/quality_reporting.md is to report TM-score AND lDDT as a mandatory pair (CASP15+ consensus, Mariani et al. 2013); CA RMSD is reported additionally for legibility but is not the basis of the verdict on its own.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://w3id.org/protstruct-review/schema'})

    id: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['CatalogTask',
                       'Tool',
                       'MetricDefinition',
                       'Structure',
                       'ExperimentalData',
                       'AgentArtifact',
                       'Refinement',
                       'MeasurementProvenance',
                       'MeasurementValue',
                       'HeadlineFinding',
                       'EvaluationRun',
                       'QualityDataSheet',
                       'IdentityBlock',
                       'GeometrySummary',
                       'RefinementSummary',
                       'MapSummary',
                       'CrossToolCoverage',
                       'TaskCoverage',
                       'DataQualitySummary',
                       'PredictedConfidenceSummary',
                       'PairwiseComparison',
                       'ToolRecommendation']} })
    candidate_ref: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['PairwiseComparison']} })
    reference_ref: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['PairwiseComparison']} })
    reference_kind: ReferenceKind = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['PairwiseComparison']} })
    alignment_method: str = Field(default=..., description="""Tool used for the alignment that backs every metric in this row (e.g. \"TMalign\", \"phenix.superpose_models\", \"gemmi align\", \"ChimeraX matchmaker\"). State exactly one — different tools give subtly different alignments.""", json_schema_extra = { "linkml_meta": {'domain_of': ['PairwiseComparison']} })
    atoms_aligned: Optional[str] = Field(default=None, description="""e.g. \"Cα\", \"all-atom\", \"main-chain\".""", json_schema_extra = { "linkml_meta": {'domain_of': ['PairwiseComparison']} })
    residues_aligned: Optional[int] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['PairwiseComparison']} })
    tm_score: Optional[TypedMeasurementValue] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['PairwiseComparison']} })
    lddt: Optional[TypedMeasurementValue] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['PairwiseComparison']} })
    gdt_ts: Optional[TypedMeasurementValue] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['PairwiseComparison']} })
    gdt_ha: Optional[TypedMeasurementValue] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['PairwiseComparison']} })
    ca_rmsd_a: Optional[TypedMeasurementValue] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['PairwiseComparison']} })
    per_residue_max_displacement_a: Optional[TypedMeasurementValue] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['PairwiseComparison']} })
    delta_r_free: Optional[TypedMeasurementValue] = Field(default=None, description="""ΔR-free (candidate − baseline). Always quote `delta_baseline`.""", json_schema_extra = { "linkml_meta": {'domain_of': ['PairwiseComparison']} })
    delta_cc_mask: Optional[TypedMeasurementValue] = Field(default=None, description="""ΔCC_mask for cryo-EM, same baseline rules as delta_r_free.""", json_schema_extra = { "linkml_meta": {'domain_of': ['PairwiseComparison']} })
    delta_baseline: Optional[DeltaBaseline] = Field(default=None, description="""Required when any delta_* slot is populated.""", json_schema_extra = { "linkml_meta": {'domain_of': ['PairwiseComparison']} })
    verdict: Optional[str] = Field(default=None, description="""improved / equivalent / worse / incomparable, with rationale.""", json_schema_extra = { "linkml_meta": {'domain_of': ['PairwiseComparison']} })


class ToolRecommendation(ConfiguredBaseModel):
    """
    A ranked recommendation tying a Tool to a (MetricDefinition, role) pair. `top_considered` reflects literature/community consensus (\"the canonical tool for this metric\"); `top_performing` reflects empirical results within this harness (\"the tool that has done best on this metric in our evaluations\"). Often the same tool fills both roles; when they differ, both rows exist and a downstream consumer can compare. Stable across evaluations until the recommendation is consciously updated; bump `as_of_date` when that happens, don't mutate in place.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://w3id.org/protstruct-review/schema'})

    id: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['CatalogTask',
                       'Tool',
                       'MetricDefinition',
                       'Structure',
                       'ExperimentalData',
                       'AgentArtifact',
                       'Refinement',
                       'MeasurementProvenance',
                       'MeasurementValue',
                       'HeadlineFinding',
                       'EvaluationRun',
                       'QualityDataSheet',
                       'IdentityBlock',
                       'GeometrySummary',
                       'RefinementSummary',
                       'MapSummary',
                       'CrossToolCoverage',
                       'TaskCoverage',
                       'DataQualitySummary',
                       'PredictedConfidenceSummary',
                       'PairwiseComparison',
                       'ToolRecommendation']} })
    metric_definition_ref: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Finding',
                       'MeasurementValue',
                       'HeadlineFinding',
                       'ToolRecommendation']} })
    tool_ref: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ToolRecommendation']} })
    role: RecommendationRole = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ToolRecommendation']} })
    rank: Optional[int] = Field(default=None, description="""1 = primary recommendation, 2+ = alternatives in order.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ToolRecommendation']} })
    justification: Optional[str] = Field(default=None, description="""One-line rationale (\"CASP gold standard for fold similarity\"; \"matches PHENIX within 0.03 Å on 1SAR eval\"). Cite the source paper or the EvaluationRun id that supplies the evidence.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ToolRecommendation']} })
    evidence_refs: Optional[list[str]] = Field(default=[], description="""Citation keys (e.g. \"Zhang2004\", \"Williams2018\") and/or EvaluationRun ids that support this recommendation.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ToolRecommendation']} })
    as_of_date: Optional[date] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['ToolRecommendation']} })
    notes: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['Finding',
                       'MeasurementValue',
                       'HeadlineFinding',
                       'ToolRecommendation']} })


# Model rebuild
# see https://pydantic-docs.helpmanual.io/usage/models/#rebuilding-a-model
Container.model_rebuild()
Finding.model_rebuild()
CatalogTask.model_rebuild()
Tool.model_rebuild()
MetricDefinition.model_rebuild()
Structure.model_rebuild()
ExperimentalData.model_rebuild()
AgentArtifact.model_rebuild()
Refinement.model_rebuild()
MeasurementProvenance.model_rebuild()
MeasurementValue.model_rebuild()
TypedMeasurementValue.model_rebuild()
HeadlineFinding.model_rebuild()
EvaluationRun.model_rebuild()
QualityDataSheet.model_rebuild()
IdentityBlock.model_rebuild()
GeometrySummary.model_rebuild()
RefinementSummary.model_rebuild()
MapSummary.model_rebuild()
CrossToolCoverage.model_rebuild()
TaskCoverage.model_rebuild()
DataQualitySummary.model_rebuild()
PredictedConfidenceSummary.model_rebuild()
PairwiseComparison.model_rebuild()
ToolRecommendation.model_rebuild()
