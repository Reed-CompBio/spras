import typing
from abc import ABC, abstractmethod
from typing import Any

from spras.dataset import Dataset


class PRM(ABC):
    """
    The PRM (Pathway Reconstruction Module) class,
    which defines the interface that `runner.py` uses to handle
    algorithms.
    """

    required_inputs: list[str] = []
    # DOIs aren't strictly required (e.g. local neighborhood),
    # but it should be explicitly declared that there are no DOIs.
    dois: list[str] = typing.cast(list[str], None)

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
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def run(**kwargs):
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def parse_output(raw_pathway_file: str, standardized_pathway_file: str, params: dict[str, Any]):
        raise NotImplementedError
