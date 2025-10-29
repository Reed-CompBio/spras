"""
General config utilities. This is the only config file
that should be imported by algorithms, and algorithms should
only import this config file.
"""

from enum import Enum
from typing import Any
import yaml

from pydantic import BaseModel, ConfigDict


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

# We also need to allow `CaseInsensitiveEnum` to be represented in yaml.safe_dump:
# https://github.com/yaml/pyyaml/issues/722#issue-1781352490
yaml.SafeDumper.add_multi_representer(
    CaseInsensitiveEnum,
    yaml.representer.SafeRepresenter.represent_str,
)

class Empty(BaseModel):
    """
    The empty base model. Used for specifying that an algorithm takes no parameters,
    yet are deterministic.
    """
    model_config = ConfigDict(extra="forbid")
