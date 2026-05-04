"""
These are errors for the SPRAS workflow: we describe these as 'artifact' information,
as Snakemake produces artifacts, and the error/success status of these artifacts is associated with
a separate file, named `artifact-info.json`. Note that an `artifact-info.json` file is attached to a
part of the workflow run, which may produce multiple artifacts, and not a single artifact.

This file makes some heavy use of pydantic discriminated unions and type adapters,
both of which happen to be described in the unions page:
https://pydantic.dev/docs/validation/latest/concepts/unions/#discriminated-unions
"""

import json
from pathlib import Path
from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field, TypeAdapter

from spras.util import LoosePathLike


class TimeoutArtifactError(BaseModel):
    # We can't use the key `type` without some extra pydantic aliasing.
    error_type: Literal['timeout'] = 'timeout'
    duration: int

# NOTE: when we have several errors, replace this with Union[TimeoutError, <OtherError>, ...]
"""All possible distinguished errors."""
ArtifactErrorOptions = TimeoutArtifactError

class ArtifactError(BaseModel):
    """
    One of the two variants of artifact information describing errors. See `ArtifactSuccess` for the other option.

    This variant is returned when we have a failing point in the workflow,
    with `details` delegating to `ArtifactErrorOptions` for more information about the error.
    """
    details: ArtifactErrorOptions = Field(discriminator="error_type")
    status: Literal['error'] = 'error'

class ArtifactSuccess(BaseModel):
    """
    One of the two variants of artifact information describing successes. See `ArtifactError` for the other option.

    This variant only says that this part of the workflow succeeded.
    """
    status: Literal['success'] = 'success'

"""Describes what happened to a [potentially collection of] artifacts at a point in the workflow."""
ArtifactInfo = Annotated[Union[ArtifactError, ArtifactSuccess], Field(discriminator="status")]
ArtifactInfoAdapter = TypeAdapter[ArtifactInfo](ArtifactInfo)

# Collection of Snakemake utilities.

def artifact_info_to_str(artifact_info: ArtifactInfo) -> str:
    """Converts some `ArtifactInfo` into a string."""
    return json.dumps(ArtifactInfoAdapter.validate_python(artifact_info).model_dump(mode='json'))

def artifact_info_from_file(file: LoosePathLike) -> ArtifactInfo:
    """Converts a file into ArtifactInfo."""
    with open(file, 'r') as f:
        return ArtifactInfoAdapter.validate_json(json.load(f))

def mark_error(file: LoosePathLike, artifact_error: ArtifactErrorOptions):
    """Marks an artifact information file as an error with associated details."""
    Path(file).write_text(artifact_info_to_str(ArtifactError(details=artifact_error)))

def mark_success(file: LoosePathLike):
    """Marks an artifact information file as successful"""
    Path(file).write_text(artifact_info_to_str(ArtifactSuccess()))

def is_error(file: LoosePathLike):
    """Checks if a file was produced by mark_error."""
    try:
        return artifact_info_from_file(file).status == "error"
    except ValueError:
        return False
