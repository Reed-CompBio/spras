from typing import Annotated, Optional

from pydantic import AfterValidator, BaseModel, ConfigDict

from spras.config.util import label_validator
from spras.util import LoosePathLike


class DatasetSchema(BaseModel):
    """
    Collection of information related to `Dataset` objects in the configuration.
    """

    # We prefer AfterValidator here to allow pydantic to run its own
    # validation & coercion logic before we check it against our own
    # requirements
    label: Annotated[str, AfterValidator(label_validator("Dataset"))]
    node_files: list[LoosePathLike]
    edge_files: list[LoosePathLike]
    other_files: list[LoosePathLike]
    data_dir: LoosePathLike
    category: Optional[str] = None
    "The dataset category, for working with dataset collections in the configuration."

    model_config = ConfigDict(extra='forbid')
