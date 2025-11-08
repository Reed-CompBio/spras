"""
The separate container schema specification file.
For information about pydantic, see schema.py.

We move this to a separate file to allow `containers.py` to explicitly take in
this subsection of the configuration.
"""

import warnings
from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict

from spras.config.util import CaseInsensitiveEnum

DEFAULT_CONTAINER_PREFIX = "ghcr.io/reed-compbio"

class ContainerFramework(CaseInsensitiveEnum):
    docker = 'docker'
    singularity = 'singularity'
    apptainer = 'apptainer'
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
    enable_profiling: bool = False
    "A Boolean indicating whether to enable container runtime profiling (apptainer/singularity only)"
    registry: ContainerRegistry

    model_config = ConfigDict(extra='forbid', use_attribute_docstrings=True)

@dataclass
class ProcessedContainerSettings:
    framework: ContainerFramework = ContainerFramework.docker
    unpack_singularity: bool = False
    prefix: str = DEFAULT_CONTAINER_PREFIX
    enable_profiling: bool = False
    hash_length: int = 7
    """
    The hash length for container-specific usage. This does not appear in
    the output folder, but it may show up in logs, and usually never needs
    to be tinkered with. This will be the top-level `hash_length` specified
    in the config.

    We prefer this `hash_length` in our container-running logic to
    avoid a (future) dependency diamond.
    """

    @staticmethod
    def from_container_settings(settings: ContainerSettings, hash_length: int) -> "ProcessedContainerSettings":
        if settings.framework == ContainerFramework.dsub:
            warnings.warn("'dsub' framework integration is experimental and may not be fully supported.", stacklevel=2)
        container_framework = settings.framework

        # Unpack settings for running in singularity mode. Needed when running PRM containers if already in a container.
        if settings.unpack_singularity and container_framework != "singularity":
            warnings.warn("unpack_singularity is set to True, but the container framework is not singularity. This setting will have no effect.", stacklevel=2)
        unpack_singularity = settings.unpack_singularity

        # Grab registry from the config, and if none is provided default to GHCR
        container_prefix = DEFAULT_CONTAINER_PREFIX
        if settings.registry and settings.registry.base_url != "" and settings.registry.owner != "":
            container_prefix = settings.registry.base_url + "/" + settings.registry.owner

        return ProcessedContainerSettings(
            framework=container_framework,
            unpack_singularity=unpack_singularity,
            prefix=container_prefix,
            hash_length=hash_length
        )
