import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Generic, Optional, TypeVar, cast, get_args

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
    # but it should be explicitly declared that there are no DOIs by defining an empty list.
    dois: list[str] = cast(list[str], None)

    def __init_subclass__(cls):
        # modified from https://stackoverflow.com/a/58206480/7589775
        props = ["required_inputs", "dois"]
        for prop in props:
            if getattr(PRM, prop) is getattr(cls, prop):
                raise NotImplementedError(
                    "Attribute '{}' has not been overridden in class '{}'" \
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

    @classmethod
    def run_typeless(cls, inputs: dict[str, str | os.PathLike], output_file: str | os.PathLike, args: dict[str, Any], container_settings: ProcessedContainerSettings):
        """
        This is similar to PRA.run, but it does pydantic logic internally to re-validate argument parameters.
        """
        # awful reflection here, unfortunately:
        # https://stackoverflow.com/a/71720366/7589775
        # alternatively, one could have a T_class parameter
        # for PRA here, but this level of implicitness seems alright.
        T_class: type[T] = get_args(cast(Any, cls).__orig_bases__[0])[0]

        # Since we just used reflection, we provide a mountain-dewey error message here
        # to protect against any developer confusion.
        if not issubclass(T_class, BaseModel):
            raise RuntimeError("The generic passed into PRM is not a pydantic.BaseModel.")

        # (and pydantic already provides nice error messages, so we don't need to worry about
        # catching this.)
        T_parsed = T_class.model_validate(args)

        return cls.run(inputs, output_file, T_parsed, container_settings)

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

    @classmethod
    def validate_required_inputs(cls, filename_map: dict[str, str]):
        for input_type in cls.required_inputs:
            if input_type not in filename_map:
                raise ValueError("{input_type} filename is missing")

    @classmethod
    def validate_required_run_args(cls, inputs: dict[str, str | os.PathLike], relax: Optional[list[str]] = None):
        """
        Validates the `inputs` parameter for `PRM#run`.

        @param inputs: See `PRM#run`.
        @param relax: List of inputs that aren't required: if they are specified, they should be valid path
        """
        if not relax: relax = []

        # Check that `relax` is a valid list
        for entry in relax:
            if entry not in cls.required_inputs:
                raise RuntimeError(f"{relax} is not contained in this PRM's required inputs ({cls.required_inputs}). This should have been caught in testing.")

        # Check that all non-relaxed required inputs are present
        for input_type in cls.required_inputs:
            if input_type not in inputs or not inputs[input_type]:
                # Ignore relaxed inputs
                if input_type in relax:
                    continue
                raise ValueError(f'Required input "{input_type}" is not set')

            path = Path(inputs[input_type])
            if not path.exists():
                raise OSError(f'Required input "{input_type}" is pointing to a missing file "{path}".')

        # Then, check that all inputs are required inputs (to prevent typos / catch errors when inputs are updated)
        for input_type in inputs.keys():
            if input_type not in cls.required_inputs:
                raise ValueError(f'Extra input "{input_type}" was provided but is not present in required inputs ({cls.required_inputs})')
