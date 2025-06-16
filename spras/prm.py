from abc import ABC, abstractmethod

from spras.dataset import Dataset


class PRM(ABC):
    """
    The PRM (Pathway Reconstruction Module) class,
    which defines the interface that `runner.py` uses to handle
    algorithms.
    """

    @property
    @staticmethod
    @abstractmethod
    def required_inputs(self):
        # Note: This NotImplementedError will never trigger.
        # See CONTRIBUTING.md for more information.
        raise NotImplementedError

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
    def parse_output(raw_pathway_file: str, standardized_pathway_file: str):
        raise NotImplementedError
