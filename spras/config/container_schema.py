"""
The separate container schema specification file.
For information about pydantic, see schema.py.

We move this to a separate file to allow `containers.py` to explicitly take in
this subsection of the configuration.
"""

import warnings
from dataclasses import dataclass
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from spras.config.util import CaseInsensitiveEnum

DEFAULT_CONTAINER_PREFIX = "docker.io/reedcompbio"

class ContainerFramework(CaseInsensitiveEnum):
    docker = 'docker'
    # TODO: add apptainer variant once #260 gets merged
    singularity = 'singularity'
    dsub = 'dsub'

class ContainerRegistry(BaseModel):
    base_url: str = "docker.io"
    "The domain of the registry"

    owner: str = "reedcompbio"
    "The owner or project of the registry"

    model_config = ConfigDict(extra='forbid', use_attribute_docstrings=True)

class ContainerSettings(BaseModel):
    framework: ContainerFramework = ContainerFramework.docker
    unpack_singularity: bool = False
    registry: ContainerRegistry
    hash_length: int = 7

    model_config = ConfigDict(extra='forbid')

@dataclass
class ProcessedContainerSettings:
    framework: ContainerFramework = ContainerFramework.docker
    unpack_singularity: bool = False
    prefix: str = DEFAULT_CONTAINER_PREFIX
    hash_length: int = 7

    @staticmethod
    def from_container_settings(settings: ContainerSettings, default_hash_length: int) -> "ProcessedContainerSettings":
        if settings.framework == ContainerFramework.dsub:
            warnings.warn("'dsub' framework integration is experimental and may not be fully supported.", stacklevel=2)
        container_framework = settings.framework

        # Unpack settings for running in singularity mode. Needed when running PRM containers if already in a container.
        if settings.unpack_singularity and container_framework != "singularity":
            warnings.warn("unpack_singularity is set to True, but the container framework is not singularity. This setting will have no effect.", stacklevel=2)
        unpack_singularity = settings.unpack_singularity

        # Grab registry from the config, and if none is provided default to docker
        container_prefix = DEFAULT_CONTAINER_PREFIX
        if settings.registry and settings.registry.base_url != "" and settings.registry.owner != "":
            container_prefix = settings.registry.base_url + "/" + settings.registry.owner

        return ProcessedContainerSettings(
            framework=container_framework,
            unpack_singularity=unpack_singularity,
            prefix=container_prefix,
            hash_length=settings.hash_length or default_hash_length
        )
