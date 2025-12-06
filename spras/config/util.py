import re
from enum import Enum
from typing import Any


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
