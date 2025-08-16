import typing
from abc import ABC, abstractmethod
from typing import Any

from spras.dataset import Dataset, InteractomeProperty


class PRM(ABC):
    """
    The PRM (Pathway Reconstruction Module) class,
    which defines the interface that `runner.py` uses to handle
    algorithms.
    """

    required_inputs: list[str] = []
    
    # DOIs aren't strictly required (e.g. local neighborhood),
    # but it should be explicitly declared that there are no DOIs by defining an empty list.
    dois: list[str] = typing.cast(list[str], None)

    # TODO: do we want to check that interactome_properties specifies some specific properties we
    # always want to know about?
    interactome_properties: list[InteractomeProperty] = []
    "The list of interactome properties that this PRM allows."

    def __init_subclass__(cls):
        # modified from https://stackoverflow.com/a/58206480/7589775
        props = ["required_inputs", "dois", "interactome_properties"]
        for prop in props:
            if getattr(PRM, prop) is getattr(cls, prop):
                raise NotImplementedError(
                    "Attribute '{}' has not been overridden in class '{}'" \
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

    @classmethod
    def validate_required_inputs(cls, filename_map: dict[str, str]):
        for input_type in cls.required_inputs:
            if input_type not in filename_map:
                raise ValueError("{input_type} filename is missing")
