"""
Contains the raw pydantic schema for the configuration file.
"""

from enum import Enum
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional

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

class AlgorithmParams(BaseModel):
    include: bool = Field(default=False)
    directed: Optional[bool]
    # TODO

class Algorithm(BaseModel):
    name: str
    params: AlgorithmParams

class Dataset(BaseModel):
    label: str
    node_files: list[str]
    edge_files: list[str]
    other_files: list[str]
    data_dir: str

class GoldStandard(BaseModel):
    label: str
    node_files: list[str]
    data_dir: str
    dataset_labels: list[str]

class Locations(BaseModel):
    reconstruction_dir: str

class ReconstructionSettings(BaseModel):
    locations: Locations

class RawConfig(BaseModel):
    # TODO: move this to nested container key
    container_framework: Optional[ContainerFramework]
    unpack_singularity: bool = Field(default=False)
    container_registry: ContainerRegistry

    hash_length: Optional[int] = Field(
        description="The length of the hash used to identify a parameter combination",
        default=DEFAULT_HASH_LENGTH)

    algorithms: list[Algorithm]
    datasets: list[Dataset]
    gold_standards: list[GoldStandard] = Field(default=[])

    reconstruction_settings: ReconstructionSettings
