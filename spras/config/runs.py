from typing import Annotated, Optional

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field
from pytimeparse import parse


def validate_duration(value):
    if isinstance(value, int): return value
    parsed_duration = parse(value, granularity='seconds')
    if not parsed_duration: raise RuntimeError(f"Encountered unparsable duration string '{value}'.")
    return parsed_duration

PyDateTimeDuration = Annotated[
    int,
    BeforeValidator(validate_duration)
]

class RunSettings(BaseModel):
    """All of the non-parameter settings associated with a run."""

    timeout: Optional[PyDateTimeDuration] = None
    """The associated timeout with a run, parsed with `pytimeparse`."""

    conditionals: list[str] = Field(alias="if", default_factory=lambda: [])
    """
    If any of the specified runs in this list succeed, then this run itself is permitted to run.
    We refer to these as 'conditional runs,' and since Python reserves the `if` keyword, we call
    them "conditionals" for short in-code, but users interface with this using `if`.
    """

    model_config = ConfigDict(extra='forbid', use_attribute_docstrings=True)
