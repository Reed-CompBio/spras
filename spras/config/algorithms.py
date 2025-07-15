"""
Dynamic construction of algoithm parameters with runtime type information for
parameter combinations. This has been isolated from schema.py as it is not declarative,
and rather mainly contains validators and lower-level pydantic code.
"""
from typing import Annotated, Any, Callable, cast, Optional, Union, Literal

from spras.runner import algorithms
from pydantic import BaseModel, BeforeValidator, create_model

__all__ = ['AlgorithmUnion']

def is_numpy_friendly(type: type[Any] | None) -> bool:
    """
    Whether the passed in type can have any numpy helpers.
    This is mainly used to provide hints in the JSON schema.
    """
    return type in (int, float)

def python_evalish_coerce(type: type[Any] | None) -> Callable[[Any], Any]:
    """
    Allows for using numpy and python calls
    """
    
    def numpy_coerce_validator(value: Any) -> Any:
        raise NotImplementedError

    return numpy_coerce_validator


def list_coerce(value: Any) -> Any:
    """
    Coerces to a value to a list if it isn't already.
    Used as a BeforeValidator.
    """
    if not isinstance(value, list):
        return [value]
    return value

def construct_algorithm_model(name: str, model: type[BaseModel], model_default: Optional[BaseModel]) -> type[BaseModel]:
    """
    Dynamically constructs a parameter-combination model based on the original args model.
    This is the most 'hacky' part of this code, but, thanks to pydantic, we avoid reflection
    and preserve rich type information at runtime.
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
    # However, we want to preserve certain conveniences (singleton values, fake python evaluation),
    # so we also make use of BeforeValidators to do so, and we pass over their preferences into the JSON schema.
    # (Note: This function does not worry about getting the cartesian product of this.)

    # Map our fields to a list (assuming we have no nested keys),
    # and specify our user convenience validators
    mapped_list_field: dict[str, Annotated] = {
        name: (Annotated[
            list[field.annotation],
            # This order isn't arbitrary.
            # https://docs.pydantic.dev/latest/concepts/validators/#ordering-of-validators
            # This runs second. This coerces any singletons to lists.
            BeforeValidator(list_coerce),
            # This runs first. This evaluates numpy utils for integer/float lists
            BeforeValidator(
                python_evalish_coerce(field.annotation),
                # json_schema_input_type (sensibly) overwrites, so we only specify it here.
                json_schema_input_type=Union[field.annotation, list[field.annotation], str] if is_numpy_friendly(field.annotation) else \
                                       Union[field.annotation, list[field.annotation]]
            )
        ], field) for name, field in model.model_fields.items()
    }

    # Runtime assertion check: mapped_list_field does not contain any `__-prefixed` fields
    for key in mapped_list_field.keys():
        assert not key.startswith("__"), f"A private key has been passed from {name}'s argument schema. " + \
            "This should have been caught by the Snakemake CI step."

    # Pass this as kwargs to create_model, which usually takes in parameters field_name=type.
    # We do need to cast create_model, since otherwise the type-checker complains that we may
    # have had a key that starts with __ in mapped_list_fields. The above assertion prevents this.
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
        name=Literal[name],
        include=bool,
        # For algorithms that have a default parameter config, we allow arbitrarily running an algorithm
        # if no runs are specified. For example, the following config
        #   name: pathlinker
        #   include: true
        # will run, despite there being no entries in `runs`.
        # (create_model entries take in either a type or (type, default)).
        runs=dict[str, run_model] if model_default is None else (dict[str, run_model], {"default": model_default})
    )

algorithm_models: list[type[BaseModel]] = [construct_algorithm_model(name, model, model_default) for name, (_, model, model_default) in algorithms.items()]
AlgorithmUnion = Union[tuple(algorithm_models)]
