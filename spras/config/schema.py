"""
Contains the raw pydantic schema for the configuration file.

Using Pydantic as our backing config parser allows us to declaratively
type our config, giving us more robust user errors with guarantees
that parts of the config exist after parsing it through Pydantic.

We declare models using two classes here:
- `BaseModel` (docs: https://docs.pydantic.dev/latest/concepts/models/)
- `CaseInsensitiveEnum` (see ./util.py)
"""

from typing import Annotated, Optional

from pydantic import AfterValidator, BaseModel, ConfigDict

from spras.config.dataset import DatasetSchema
from spras.config.container_schema import ContainerSettings
from spras.config.util import CaseInsensitiveEnum, label_validator

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

class ContainerFramework(CaseInsensitiveEnum):
    docker = 'docker'
    # TODO: add apptainer variant once #260 gets merged
    singularity = 'singularity'
    dsub = 'dsub'

class ContainerRegistry(BaseModel):
    base_url: str
    owner: str = Field(description="The owner or project of the registry")

    model_config = ConfigDict(extra='forbid')

class AlgorithmParams(BaseModel):
    include: bool
    directed: Optional[bool] = None

    # TODO: use array of runs instead. We currently rely on the
    # extra parameters here to extract the algorithm parameter information,
    # which is why this deviates from the usual ConfigDict(extra='forbid').
    model_config = ConfigDict(extra='allow')

class Algorithm(BaseModel):
    name: str
    params: AlgorithmParams

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

    algorithms: list[Algorithm]
    datasets: list[DatasetSchema]
    gold_standards: list[GoldStandard] = []
    analysis: Analysis = Analysis()

    reconstruction_settings: ReconstructionSettings

    # We include use_attribute_docstrings here to preserve the docstrings
    # after attributes at runtime (for future JSON schema generation)
    model_config = ConfigDict(extra='forbid', use_attribute_docstrings=True)
