"""
General config utilities. This is the only config file
that should be imported by algorithms, and algorithms should
only import this config file.
"""

from enum import Enum
from typing import Any

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


class Empty(BaseModel):
    """
    The empty base model. Used for specifying that an algorithm takes no parameters,
    yet are deterministic.
    """
    model_config = ConfigDict(extra="forbid")
