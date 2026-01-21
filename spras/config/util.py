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

class Empty(BaseModel):
    """
    The empty base model. Used for specifying that an algorithm takes no parameters,
    yet is deterministic.
    """
    model_config = ConfigDict(extra="forbid")
