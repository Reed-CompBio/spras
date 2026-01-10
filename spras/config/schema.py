"""
Contains the raw pydantic schema for the configuration file.

Using Pydantic as our backing config parser allows us to declaratively
type our config, giving us more robust user errors with guarantees
that parts of the config exist after parsing it through Pydantic.

We declare models using two classes here:
- `BaseModel` (docs: https://docs.pydantic.dev/latest/concepts/models/)
- `CaseInsensitiveEnum` (see ./util.py)
"""

import re
import warnings
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, model_validator

from spras.config.algorithms import AlgorithmUnion
from spras.config.container_schema import ContainerSettings
from spras.config.util import CaseInsensitiveEnum

# Most options here have an `include` property,
# which is meant to make disabling parts of the configuration easier.
# When an option does not have a default, it means that it must be set by the user.

class SummaryAnalysis(BaseModel):
    include: bool

    # We prefer to never allow extra keys, to prevent
    # any user mistypes.
    model_config = ConfigDict(extra='forbid')

class CytoscapeAnalysis(BaseModel):
    include: bool

    model_config = ConfigDict(extra='forbid')

# Note that CaseInsensitiveEnum is not pydantic: pydantic
# has special support for enums, but we avoid the
# pydantic-specific "model_config" key here for this reason.
class HacLinkage(CaseInsensitiveEnum):
    ward = 'ward'
    complete = 'complete'
    average = 'average'
    single = 'single'

class HacMetric(CaseInsensitiveEnum):
    euclidean = 'euclidean'
    manhattan = 'manhattan'
    cosine = 'cosine'

def implies(source: bool, target: bool, source_str: str, target_str: str):
    if target and not source:
        warnings.warn(f"{source_str} is False but {target_str} is True; setting {target_str} to False", stacklevel=2)
        return False
    return target

class AggregateAnalysis(BaseModel):
    include: bool
    aggregate_per_algorithm: bool = False

    model_config = ConfigDict(extra='forbid')

    @model_validator(mode='after')
    def check_aggregate_when_include(self):
        self.aggregate_per_algorithm = implies(self.include, self.aggregate_per_algorithm, "include", "aggregate_per_algorithm")
        return self

class EvaluationAnalysis(AggregateAnalysis): pass

class PcaAnalysis(AggregateAnalysis):
    components: int = 2
    labels: bool = True
    kde: bool = False
    remove_empty_pathways: bool = False
    pca_chosen: EvaluationAnalysis = EvaluationAnalysis(include=False)

    @model_validator(mode='after')
    def check_include_when_evaluation_include(self):
        self.pca_chosen.include = implies(self.include, self.pca_chosen.include, "include", "pca_chosen.include")
        self.pca_chosen.aggregate_per_algorithm = implies(self.aggregate_per_algorithm, self.pca_chosen.aggregate_per_algorithm, "aggregate_per_algorithm", "pca_chosen.aggregate_per_algorithm")
        return self

class HacAnalysis(AggregateAnalysis):
    linkage: HacLinkage = HacLinkage.ward
    metric: HacMetric = HacMetric.euclidean

class EnsembleAnalysis(AggregateAnalysis):
    evaluation: EvaluationAnalysis = EvaluationAnalysis(include=False)

    @model_validator(mode='after')
    def check_include_when_evaluation_include(self):
        self.evaluation.include = implies(self.include, self.evaluation.include, "include", "evaluation.include")
        self.evaluation.aggregate_per_algorithm = implies(self.aggregate_per_algorithm, self.evaluation.aggregate_per_algorithm, "aggregate_per_algorithm", "evaluation.aggregate_per_algorithm")
        return self
class JaccardAnalysis(AggregateAnalysis): pass

class Analysis(BaseModel):
    summary: SummaryAnalysis = SummaryAnalysis(include=False)
    cytoscape: CytoscapeAnalysis = CytoscapeAnalysis(include=False)
    pca: PcaAnalysis = PcaAnalysis(include=False)
    hac: HacAnalysis = HacAnalysis(include=False)
    jaccard: JaccardAnalysis = JaccardAnalysis(include=False)
    ensemble: EnsembleAnalysis = EnsembleAnalysis(include=False)
    evaluation: EvaluationAnalysis = EvaluationAnalysis(include=False)
    """Enables PR curve evaluation."""

    model_config = ConfigDict(extra='forbid', use_attribute_docstrings=True)


# The default length of the truncated hash used to identify parameter combinations
DEFAULT_HASH_LENGTH = 7

def label_validator(name: str):
    """
    A validator takes in a label
    and ensures that it contains only letters, numbers, or underscores.
    """
    label_pattern = r'^\w+$'
    def validate(label: str):
        if not bool(re.match(label_pattern, label)):
            raise ValueError(f"{name} label '{label}' contains invalid values. {name} labels can only contain letters, numbers, or underscores.")
        return label
    return validate

class Dataset(BaseModel):
    # We prefer AfterValidator here to allow pydantic to run its own
    # validation & coercion logic before we check it against our own
    # requirements
    label: Annotated[str, AfterValidator(label_validator("Dataset"))]
    node_files: list[str]
    edge_files: list[str]
    other_files: list[str]
    data_dir: str

    model_config = ConfigDict(extra='forbid')

class GoldStandard(BaseModel):
    label: Annotated[str, AfterValidator(label_validator("Gold Standard"))]
    node_files: list[str] = []
    edge_files: list[str] = []
    data_dir: str
    dataset_labels: list[str]

    model_config = ConfigDict(extra='forbid')

class Locations(BaseModel):
    reconstruction_dir: str

    model_config = ConfigDict(extra='forbid')

# NOTE: This setting doesn't have any uses past setting the output_dir as of now.
class ReconstructionSettings(BaseModel):
    locations: Locations

    model_config = ConfigDict(extra='forbid')

class RawConfig(BaseModel):
    containers: ContainerSettings

    hash_length: int = DEFAULT_HASH_LENGTH
    "The length of the hash used to identify a parameter combination"

    # See algorithms.py for more information about AlgorithmUnion
    algorithms: list[AlgorithmUnion] # type: ignore - pydantic allows this.
    datasets: list[Dataset]
    gold_standards: list[GoldStandard] = []
    analysis: Analysis = Analysis()

    reconstruction_settings: ReconstructionSettings

    # We include use_attribute_docstrings here to preserve the docstrings
    # after attributes at runtime (for future JSON schema generation)
    model_config = ConfigDict(extra='forbid', use_attribute_docstrings=True)
