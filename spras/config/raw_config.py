"""
Contains the raw pydantic schema for the configuration file.
"""

import re
from typing import Annotated, Optional

from pydantic import AfterValidator, BaseModel, ConfigDict, Field

from spras.config.raw_config_analysis import Analysis
from spras.config.util_enum import CaseInsensitiveEnum

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

class AlgorithmParams(BaseModel):
    include: bool = False
    directed: Optional[bool] = None

    # TODO: use array of runs instead
    model_config = ConfigDict(extra='allow')

class Algorithm(BaseModel):
    name: str
    params: AlgorithmParams

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
    # TODO: move these container values to a nested container key
    container_framework: ContainerFramework = ContainerFramework.docker
    unpack_singularity: bool = False
    container_registry: ContainerRegistry

    hash_length: int = Field(
        description="The length of the hash used to identify a parameter combination",
        default=DEFAULT_HASH_LENGTH)

    algorithms: list[Algorithm]
    datasets: list[Dataset]
    gold_standards: list[GoldStandard] = []
    analysis: Analysis = Analysis()

    reconstruction_settings: ReconstructionSettings

    model_config = ConfigDict(extra='forbid')
