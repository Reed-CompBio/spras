"""
General config utilities. This is the only config file
that should be imported by algorithms, and algorithms should
only import this config file.
"""

from enum import Enum
import time
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


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

class NondeterministicModel(BaseModel):
    """
    A nondeterministic model. Any seedless nondeterministic algorithm should extend this.
    Internally, this inserts a _time parameter that can be serialized but not
    deserialized, and will affect the hash.
    """

    # We don't make this a PrivateAttr for reasons explained in the doc comment.
    time: float = Field(default_factory=time.time, alias="_time")
    """
    The internal _time parameter. This is a parameter only given to nondeterminsitic
    algorithms that provide no randomness seed. While this should be unset,
    we allow specifying `_time` for users that want to re-use outputs of runs,
    though this explicitly breaks the 'immutability' promise of runs.
    """

    model_config = ConfigDict(use_attribute_docstrings=True)
