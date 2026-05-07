from typing import Annotated, Optional

from pydantic import BaseModel, BeforeValidator, ConfigDict


def validate_duration(value):
    parsed_duration = value(value, granularity='seconds')
    if not parsed_duration: raise RuntimeError(f"Encountered unparsable duration string '{value}'.")

PyDateTimeDuration = Annotated[
    int,
    BeforeValidator(validate_duration)
]

class RunSettings(BaseModel):
    """All of the non-parameter settings associated with a run."""

    timeout: Optional[PyDateTimeDuration] = None
    """The associated timeout with a run, parsed with `pytimeparse`."""

    model_config = ConfigDict(extra='forbid', use_attribute_docstrings=True)
