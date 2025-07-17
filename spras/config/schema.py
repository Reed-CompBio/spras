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

from spras.config.algorithms import AlgorithmUnion
from spras.config.container_schema import ContainerSettings
from spras.config.util import CaseInsensitiveEnum


class SummaryAnalysis(BaseModel):
    include: bool

    model_config = ConfigDict(extra='forbid')

class CytoscapeAnalysis(BaseModel):
    include: bool

    model_config = ConfigDict(extra='forbid')

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
    label_pattern = r'^\w+$'
    def validate(label: str):
        if not bool(re.match(label_pattern, label)):
            raise ValueError(f"{name} label '{label}' contains invalid values. {name} labels can only contain letters, numbers, or underscores.")
        return label
    return validate

class ContainerFramework(CaseInsensitiveEnum):
    docker = 'docker'
    # TODO: add apptainer variant once #260 gets merged
    singularity = 'singularity'
    dsub = 'dsub'

class ContainerRegistry(BaseModel):
    base_url: str
    owner: str = Field(description="The owner or project of the registry")

    model_config = ConfigDict(extra='forbid')

class Dataset(BaseModel):
    label: Annotated[str, AfterValidator(label_validator("Dataset"))]
    node_files: list[str]
    edge_files: list[str]
    other_files: list[str]
    data_dir: str

    model_config = ConfigDict(extra='forbid')

class GoldStandard(BaseModel):
    label: Annotated[str, AfterValidator(label_validator("Gold Standard"))]
    node_files: list[str]
    data_dir: str
    dataset_labels: list[str]

    model_config = ConfigDict(extra='forbid')

class Locations(BaseModel):
    reconstruction_dir: str

    model_config = ConfigDict(extra='forbid')

class ReconstructionSettings(BaseModel):
    locations: Locations

    model_config = ConfigDict(extra='forbid')

class RawConfig(BaseModel):
    resume: bool = Field(alias="_resume", default=False)
    """
    Declares whether a config has resumability. This is meant to be used internally, as it
    enforces some extra preconditions on the config (such that all defaults must be explicitly
    declared within the config, and that it meets the specified hash).

    Unlike their nonresumable counterparts, these resumable configurations will store all configuration
    defaults (including, most importantly, _time from NondeterministicModel and any seeded values).

    Resumable configurations are generated whenever a non-resumable configuration is run, inside
    `{output}/resumables/{hash}.yaml`. The timestamp is present only for file ordering, and {hash} is a hash
    of the configuration _excluding_ default values.

    By default, SPRAS runs through Snakemake will generate a resumable configuration if none is present,
    or reuse the configuration associated with its hash otherwise.
    """

    containers: ContainerSettings

    hash_length: int = DEFAULT_HASH_LENGTH
    "The length of the hash used to identify a parameter combination"

    # See algorithms.py for more information about AlgorithmUnion
    algorithms: list[AlgorithmUnion] # type: ignore - pydantic allows this.
    datasets: list[Dataset]
    gold_standards: list[GoldStandard] = []
    analysis: Analysis = Analysis()

    reconstruction_settings: ReconstructionSettings

    model_config = ConfigDict(extra='forbid', use_attribute_docstrings=True)
