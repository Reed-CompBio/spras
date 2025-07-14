from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import Any, cast, TypeVar, Generic

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
    def run(inputs: dict[str, str], args: T, output_file: str, container_framework="docker"):
        """
        Runs an algorithm with the specified inputs, algorithm params (T),
        the designated output_file, and the desired container_framework.
        """
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def parse_output(raw_pathway_file: str, standardized_pathway_file: str, params: dict[str, Any]):
        raise NotImplementedError
