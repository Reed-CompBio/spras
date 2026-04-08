"""
General config utilities. This is the only config file
that should be imported by algorithms, and algorithms should
only import this config file.
"""

import re
from enum import Enum
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict


def label_validator(name: str):
    """
    A validator takes in a label
    and ensures that it contains only letters, numbers, or underscores.
    """
    label_pattern = r'^\w+$'
    def validate(label: str):
        if not bool(re.match(label_pattern, label)):
            raise ValueError(f"{name} label '{label}' contains invalid values. {name} labels can only contain letters, numbers, or underscores.")
        return label
    return validate

# https://stackoverflow.com/a/76883868/7589775
class CaseInsensitiveEnum(str, Enum):
    """
    We prefer this over Enum to make sure the config parsing
    is more relaxed when it comes to string enum values.
    """
    @classmethod
    def _missing_(cls, value: Any):
        if isinstance(value, str):
            value = value.lower()

            for member in cls:
                if member.lower() == value:
                    return member
        return None

# We also need to allow `CaseInsensitiveEnum` to be represented in yaml.safe_dump,
# allowing us to safely log parameters in Snakemake:
# https://github.com/yaml/pyyaml/issues/722#issue-1781352490
yaml.SafeDumper.add_multi_representer(
    CaseInsensitiveEnum,
    yaml.representer.SafeRepresenter.represent_str,
)

# The single source of truth for all supported algorithms.
# Keys are algorithm names; values are (module_path, class_name) tuples for importlib loading.
# To register a new algorithm, add an entry here.
ALGORITHM_REGISTRY: dict[str, tuple[str, str]] = {
    "allpairs":        ("spras.allpairs", "AllPairs"),
    "bowtiebuilder":   ("spras.btb", "BowTieBuilder"),
    "diamond":         ("spras.diamond", "DIAMOnD"),
    "domino":          ("spras.domino", "DOMINO"),
    "meo":             ("spras.meo", "MEO"),
    "mincostflow":     ("spras.mincostflow", "MinCostFlow"),
    "omicsintegrator1": ("spras.omicsintegrator1", "OmicsIntegrator1"),
    "omicsintegrator2": ("spras.omicsintegrator2", "OmicsIntegrator2"),
    "pathlinker":      ("spras.pathlinker", "PathLinker"),
    "responsenet":     ("spras.responsenet", "ResponseNet"),
    "rwr":             ("spras.rwr", "RWR"),
    "strwr":           ("spras.strwr", "ST_RWR"),
}

# Auto-generated enum from the registry keys. Inherits CaseInsensitiveEnum so
# AlgorithmName("PathLinker") resolves to AlgorithmName.pathlinker.
AlgorithmName = CaseInsensitiveEnum("AlgorithmName", {k: k for k in ALGORITHM_REGISTRY})

def get_valid_algorithm_names() -> set[str]:
    """Return the set of valid algorithm name strings (lowercase)."""
    return {member.value for member in AlgorithmName}


class Empty(BaseModel):
    """
    The empty base model. Used for specifying that an algorithm takes no parameters,
    yet is deterministic.
    """
    model_config = ConfigDict(extra="forbid")
