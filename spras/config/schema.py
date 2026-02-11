"""
Contains the raw pydantic schema for the configuration file.

Using Pydantic as our backing config parser allows us to declaratively
type our config, giving us more robust user errors with guarantees
that parts of the config exist after parsing it through Pydantic.

We declare models using two classes here:
- `BaseModel` (docs: https://docs.pydantic.dev/latest/concepts/models/)
- `CaseInsensitiveEnum` (see ./util.py)
"""

from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict

from spras.config.algorithms import AlgorithmUnion
from spras.config.container_schema import ContainerSettings
from spras.config.dataset import DatasetSchema
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
    osdf_immutable: bool = False
    """
    If enabled, this tags all files with their local file version.
    Most files do not have a specific version, and by default, this will be the hash of
    all the SPRAS files in the PyPA installation. This option will not work if SPRAS was not installed
    in a PyPA-compliant manner (PyPA-compliant installations include but are not limited to pip, poetry, uv, conda, pixi.)

    By default, this is disabled, as it can make output file names confusing.
    """

    hash_length: int = DEFAULT_HASH_LENGTH
    "The length of the hash used to identify a parameter combination"

    # See algorithms.py for more information about AlgorithmUnion
    algorithms: list[AlgorithmUnion] # type: ignore - pydantic allows this.
    datasets: list[DatasetSchema]
    gold_standards: list[GoldStandard] = []
    analysis: Analysis = Analysis()

    reconstruction_settings: ReconstructionSettings

    # We include use_attribute_docstrings here to preserve the docstrings
    # after attributes at runtime (for future JSON schema generation)
    model_config = ConfigDict(extra='forbid', use_attribute_docstrings=True)
