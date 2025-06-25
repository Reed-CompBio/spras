"""
Contains the raw pydantic schema for the configuration file.
"""

from enum import Enum
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional

from spras.config.raw_config_analysis import Analysis

# The default length of the truncated hash used to identify parameter combinations
DEFAULT_HASH_LENGTH = 7

class ContainerFramework(str, Enum):
    docker = 'docker'
    # TODO: add apptainer variant once #260 gets merged
    singularity = 'singularity'
    dsub = 'dsub'

class ContainerRegistry(BaseModel):
    base_url: str
    owner: str = Field(description="The owner or project of the registry")

    model_config = ConfigDict(extra='forbid')

class AlgorithmParams(BaseModel):
    include: bool = Field(default=False)
    directed: Optional[bool]

    # TODO: use array of runs instead
    model_config = ConfigDict(extra='allow')

class Algorithm(BaseModel):
    name: str
    params: AlgorithmParams

    model_config = ConfigDict(extra='forbid')

class Dataset(BaseModel):
    label: str
    node_files: list[str]
    edge_files: list[str]
    other_files: list[str]
    data_dir: str

    model_config = ConfigDict(extra='forbid')

class GoldStandard(BaseModel):
    label: str
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
    # TODO: move these container values to a nested container key
    container_framework: ContainerFramework = Field(default=ContainerFramework.docker)
    unpack_singularity: bool = Field(default=False)
    container_registry: ContainerRegistry

    hash_length: int = Field(
        description="The length of the hash used to identify a parameter combination",
        default=DEFAULT_HASH_LENGTH)

    algorithms: list[Algorithm]
    datasets: list[Dataset]
    gold_standards: list[GoldStandard] = Field(default=[])
    analysis: Optional[Analysis]

    reconstruction_settings: ReconstructionSettings

    model_config = ConfigDict(extra='forbid')
