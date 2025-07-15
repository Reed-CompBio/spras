import os
from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar, cast

from pydantic import BaseModel

from spras.config.container_schema import ProcessedContainerSettings
from spras.dataset import Dataset

T = TypeVar('T', bound=BaseModel)

class PRM(ABC, Generic[T]):
    """
    The PRM (Pathway Reconstruction Module) class,
    which defines the interface that `runner.py` uses to handle
    algorithms.
    """

    required_inputs: list[str] = []
    # DOIs aren't strictly required (e.g. local neighborhood),
    # but it should be explicitly declared that there are no DOIs.
    dois: list[str] = cast(list[str], None)

    def __init_subclass__(cls):
        # modified from https://stackoverflow.com/a/58206480/7589775
        props = ["required_inputs", "dois"]
        for prop in props:
            if getattr(PRM, prop) is getattr(cls, prop):
                raise NotImplementedError(
                    "Attribute '{}' has not been overriden in class '{}'" \
                    .format(prop, cls.__name__)
                )

    @staticmethod
    @abstractmethod
    def generate_inputs(data: Dataset, filename_map: dict[str, str]):
        """
        Access fields from the dataset and write the required input files
        @param data: dataset
        @param filename_map: a dict mapping file types in the required_inputs to the filename for that type
        """
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def run(inputs: dict[str, str | os.PathLike], output_file: str | os.PathLike, args: T, container_settings: ProcessedContainerSettings):
        """
        Runs an algorithm with the specified inputs, algorithm params (T),
        the designated output_file, and the desired container_settings.
        """
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def parse_output(raw_pathway_file: str, standardized_pathway_file: str, params: dict[str, Any]):
        raise NotImplementedError
