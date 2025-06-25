from enum import Enum
from typing import Any

# https://stackoverflow.com/a/76883868/7589775
class CaseInsensitiveEnum(str, Enum):
    @classmethod
    def _missing_(cls, value: Any):
        if isinstance(value, str):
            value = value.lower()

            for member in cls:
                if member.lower() == value:
                    return member
        return None
