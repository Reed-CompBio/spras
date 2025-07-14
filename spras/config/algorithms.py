"""
Dynamic construction of algoithm parameters with runtime type information for
parameter combinations. This has been isolated from schema.py as it is not declarative,
and rather mainly contains validators and lower-level pydantic code.
"""
from typing import Any, cast, Union

from spras.runner import algorithms
from pydantic import BaseModel, create_model

__all__ = ['AlgorithmUnion']

def construct_algorithm_model(name: str, model: type[BaseModel]) -> type[BaseModel]:
    """
    Dynamically constructs a parameter-combination model based on the original args model.
    This is the most 'hacky' part of this code, but, thanks to pydantic, we almost*
    avoid reflection and preserve rich type information.
    """
    # First, we need to take our 'model' and coerce it to permit parameter combinations.
    # This assumes that all of the keys are flattened, so we only get a structure like so:
    # class AlgorithmParams(BaseModel):
    #   key1: int
    #   key2: list[str]
    #   ...
    # and we want to transform this to:
    # class AlgorithmParamsCombination(BaseModel):
    #   key1: list[int]
    #   key2: list[list[str]]
    # This function does not worry about getting the cartesian product of this.

    # Map our fields to a list (assuming we have no nested keys)
    mapped_list_field: dict[str, type[list[Any]]] = {name: list[field.annotation] for name, field in model.model_fields.items()}

    # Runtime assertion check: mapped_list_field does not contain any `__-prefixed` fields
    for key in mapped_list_field.keys():
        assert not key.startswith("__"), f"A private key has been passed from {name}'s argument schema." + \
            "This should have been caught by the Snakemake CI step."

    # Pass this as kwargs to create_model, which usually takes in parameters field_name=type.
    # This is the asterisk (*) from the docstring: we do need to cast create_model, since otherwise
    # the type-checker complains that we may have had a key that starts with __ in mapped_list_fields.
    # The above assertion prevents this.
    run_model = (cast(Any, create_model))(
        f'{name}RunModel',
        **mapped_list_field
    )
    
    # Here is an example of how this would look like inside config.yaml
    # name: pathlinker
    # include: true
    # runs:
    #   run1:
    #     (from run_model)
    #   ...
    return create_model(
        f'{name}Model',
        name=name,
        include=bool,
        runs=dict[str, run_model]
    )

algorithm_models: list[type[BaseModel]] = [construct_algorithm_model(name, model) for name, (_, model) in algorithms.items()]
AlgorithmUnion = Union[tuple(algorithm_models)]
