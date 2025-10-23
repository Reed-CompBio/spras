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
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, Field

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
class MlLinkage(CaseInsensitiveEnum):
    ward = 'ward'
    complete = 'complete'
    average = 'average'
    single = 'single'

class MlMetric(CaseInsensitiveEnum):
    euclidean = 'euclidean'
    manhattan = 'manhattan'
    cosine = 'cosine'

class MlAnalysis(BaseModel):
    include: bool
    aggregate_per_algorithm: bool = False
    components: int = 2
    labels: bool = True
    kde: bool = False
    remove_empty_pathways: bool = False
    linkage: MlLinkage = MlLinkage.ward
    metric: MlMetric = MlMetric.euclidean

    model_config = ConfigDict(extra='forbid')

class EvaluationAnalysis(BaseModel):
    include: bool
    aggregate_per_algorithm: bool = False

    model_config = ConfigDict(extra='forbid')

class Analysis(BaseModel):
    summary: SummaryAnalysis = SummaryAnalysis(include=False)
    cytoscape: CytoscapeAnalysis = CytoscapeAnalysis(include=False)
    ml: MlAnalysis = MlAnalysis(include=False)
    evaluation: EvaluationAnalysis = EvaluationAnalysis(include=False)

    model_config = ConfigDict(extra='forbid')


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

class ContainerFramework(CaseInsensitiveEnum):
    docker = 'docker'
    singularity = 'singularity'
    apptainer = 'apptainer'
    dsub = 'dsub'

class ContainerRegistry(BaseModel):
    base_url: str
    owner: str = Field(description="The owner or project of the registry")

    model_config = ConfigDict(extra='forbid')

class AlgorithmParams(BaseModel):
    include: bool

    # TODO: use array of runs instead. We currently rely on the
    # extra parameters here to extract the algorithm parameter information,
    # which is why this deviates from the usual ConfigDict(extra='forbid').
    model_config = ConfigDict(extra='allow')

class Algorithm(BaseModel):
    name: str
    params: AlgorithmParams

    model_config = ConfigDict(extra='forbid')

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
    # TODO: move these container values to a nested container key
    container_framework: ContainerFramework = ContainerFramework.docker
    unpack_singularity: bool = False
    container_registry: ContainerRegistry
    enable_profiling: bool = False

    hash_length: int = DEFAULT_HASH_LENGTH
    "The length of the hash used to identify a parameter combination"

    algorithms: list[Algorithm]
    datasets: list[Dataset]
    gold_standards: list[GoldStandard] = []
    analysis: Analysis = Analysis()

    reconstruction_settings: ReconstructionSettings

    # We include use_attribute_docstrings here to preserve the docstrings
    # after attributes at runtime (for future JSON schema generation)
    model_config = ConfigDict(extra='forbid', use_attribute_docstrings=True)
