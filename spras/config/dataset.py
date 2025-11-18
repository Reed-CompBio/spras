import os
from typing import Annotated
from pydantic import AfterValidator, BaseModel, ConfigDict

from spras.config.util import label_validator

class DatasetSchema(BaseModel):
    """
    Collection of information related to `Dataset` objects in the configuration.
    """

    # We prefer AfterValidator here to allow pydantic to run its own
    # validation & coercion logic before we check it against our own
    # requirements
    label: Annotated[str, AfterValidator(label_validator("Dataset"))]
    node_files: list[str | os.PathLike]
    edge_files: list[str | os.PathLike]
    other_files: list[str | os.PathLike]
    data_dir: str | os.PathLike

    model_config = ConfigDict(extra='forbid')
