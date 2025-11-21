"""
Dynamic construction of algorithm parameters with runtime type information for
parameter combinations. This has been isolated from schema.py as it is not declarative,
and rather mainly contains validators and lower-level pydantic code.
"""
import ast
import copy
from typing import Annotated, Any, Callable, Literal, Optional, Union, cast, get_args

import numpy as np
from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, create_model

from spras.runner import algorithms

# This contains the dynamically generated algorithm schema for use in `schema.py`
__all__ = ['AlgorithmUnion']

def is_numpy_friendly(type: type[Any] | None) -> bool:
    """
    Whether the passed in type can have any numpy helpers.
    This is mainly used to provide hints in the JSON schema.
    """
    allowed_types = (int, float)

    # check basic types, then check optional types
    return type in allowed_types or \
        any([arg for arg in get_args(type) if arg in allowed_types])

def python_evalish_coerce(value: Any) -> Any:
    """
    Allows for using numpy and python calls.

    **Safety Note**: This does not prevent availability attacks: this can still exhaust
    resources if wanted. This only prevents secret leakage.
    """

    if not isinstance(value, str):
        return value

    # These strings are in the form of function calls `function.name(param1, param2, ...)`.
    # Since we want to avoid `eval` (since this might be running in the secret-sensitive HTCondor),
    # we need to parse these functions.
    functions_dict: dict[str, Callable[[list[Any]], list[Union[int, float]]]] = {
        'range': lambda params: list(range(*params)),
        "np.linspace": lambda params: list(np.linspace(*params)),
        "np.arange": lambda params: list(np.arange(*params)),
        "np.logspace": lambda params: list(np.logspace(*params)),
    }

    # To do this, we get the AST of our string as an expression
    # (filename='<string>' is to make the error message more closely resemble that of eval.)
    value_ast = ast.parse(value, mode='eval', filename='<string>')

    # Then we do some light parsing - we're only looking to do some literal evaluation
    # (allowing light python notation) and some basic function parsing. Full python programs
    # should just generate a config.yaml.

    # This should always be an Expression whose body is Call (a function).
    if not isinstance(value_ast.body, ast.Call):
        raise ValueError(f'The python code "{value}" should be calling a function directly. Is this meant to be python code?')

    # We get the function name back as a string
    function_name = ast.unparse(value_ast.body.func)

    # and we use the (non-availability) safe `ast.literal_eval` to support literals passed into functions.
    arguments = [ast.literal_eval(arg) for arg in value_ast.body.args]

    if function_name not in functions_dict:
        raise ValueError(f"{function_name} is not an allowed function to be run!")

    return functions_dict[function_name](arguments)

def list_coerce(value: Any) -> Any:
    """
    Coerces to a value to a list if it isn't already.
    Used as a BeforeValidator.
    """
    if not isinstance(value, list):
        return [value]
    return value

# This is the most 'hacky' part of this code, but, thanks to pydantic, we avoid reflection
# and preserve rich type information at runtime.
def construct_algorithm_model(name: str, model: type[BaseModel], model_default: Optional[BaseModel]) -> type[BaseModel]:
    """
    Dynamically constructs a parameter-combination model based on the original args model.
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
    mapped_list_field: dict[str, Annotated] = dict()
    for field_name, field in model.model_fields.items():
        # We need to create a copy of the field,
        # as we need to make sure that it gets mapped to the list coerced version of the field.
        new_field = copy.deepcopy(field)
        new_field.validate_default = True

        mapped_list_field[field_name] = (Annotated[
            list[field.annotation],
            # This order isn't arbitrary.
            # https://docs.pydantic.dev/latest/concepts/validators/#ordering-of-validators
            # This runs second. This coerces any singletons to lists.
            BeforeValidator(list_coerce, json_schema_input_type=Union[field.annotation, list[field.annotation]]),
            # This runs first. This evaluates numpy utils for integer/float lists
            BeforeValidator(
                python_evalish_coerce,
                # json_schema_input_type (sensibly) overwrites, so we have to specify the entire union again here.
                json_schema_input_type=Union[field.annotation, list[field.annotation], str]
            ) if is_numpy_friendly(field.annotation) else None
        ], new_field)

    # Runtime assertion check: mapped_list_field does not contain any `__-prefixed` fields
    for key in mapped_list_field.keys():
        assert not key.startswith("__"), f"A private key has been passed from {name}'s argument schema. " + \
            "This should have been caught by the Snakemake CI step."

    # Pass this as kwargs to create_model, which usually takes in parameters field_name=type.
    # We do need to cast create_model, since otherwise the type-checker complains that we may
    # have had a key that starts with __ in mapped_list_fields. The above assertion prevents this.
    run_model = (cast(Any, create_model))(
        f'{name}RunModel',
        __config__=ConfigDict(extra='forbid'),
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
        runs=dict[str, run_model] if model_default is None else (dict[str, run_model], {"default": model_default}),
        __config__=ConfigDict(extra='forbid')
    )

algorithm_models: list[type[BaseModel]] = [construct_algorithm_model(name, model, model_default) for name, (_, model, model_default) in algorithms.items()]
# name differentriates algorithms
AlgorithmUnion = Annotated[Union[tuple(algorithm_models)], Field(discriminator='name')]
