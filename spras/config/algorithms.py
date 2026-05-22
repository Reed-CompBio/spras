"""
Dynamic construction of algorithm parameters with runtime type information for
parameter combinations. This has been isolated from schema.py as it is not declarative,
and rather mainly contains validators and lower-level pydantic code.
"""
import copy
from typing import Annotated, Any, Literal, Union, cast, get_args, get_origin

from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    PlainSerializer,
    ValidationError,
    create_model,
)

from spras.config.runs import RunSettings
from spras.config.tunable import FloatTunable, IntegerTunable, TunableList
from spras.runner import algorithms

# This contains the dynamically generated algorithm schema for use in `schema.py`
__all__ = ['AlgorithmUnion']

def determine_inner_type(outer_type: type):
    # TODO: this doesn't handle annotated types.
    if get_args(outer_type) != () and get_origin(outer_type) == Union:
        # We map arbitrary unions Union[A, ...] -> Union[determine_inner_type(A), ..., TunableSet[Union[A, ...]]],
        # where we include the extra entry at the end to allow for heterogeneous lists.
        return Union[*(determine_inner_type(arg) for arg in get_args(outer_type)), TunableList[outer_type]]

    if outer_type == float: return FloatTunable
    if outer_type == int: return IntegerTunable
    # We fall back to base `TunableSet` otherwise.
    return TunableList[outer_type]

# This is the most 'hacky' part of this code, but, thanks to pydantic, we avoid reflection
# and preserve rich type information at runtime.
def construct_algorithm_model(name: str, model: type[BaseModel]) -> type[BaseModel]:
    """
    Dynamically constructs a parameter-combination model based on the original args model.

    Parameter arguments such as `int` get turned into `list[int]`, and have extra conveniences attached:
    - Values can be passed as lists (1 -> [1])
    - Ranges and other convenient calls are expanded (see `python_evalish_coerce`)
    """

    # First, we need to take our 'model' and coerce it to permit parameter combinations.
    # This assumes that all of the keys are flattened, so we only get a structure like so:
    # class AlgorithmParams(BaseModel):
    #   key1: int
    #   key2: list[str]
    #   ...
    # and we want to transform this to:
    # class AlgorithmParamsCombination(BaseModel):
    #   key1: TunableInteger
    #   key2: TunableSet[list[str]]
    #   ...
    # where all key-types are children of `Tunable`.
    # However, we want to preserve certain conveniences (singleton values, fake python evaluation),
    # so we also make use of BeforeValidators to do so, and we pass over their preferences into the JSON schema.
    # (Note: This function does not worry about getting the cartesian product of this.)

    # Map our fields to `Tunable`s (assuming we have no nested keys),
    # and specify our user convenience validators
    mapped_list_field: dict[str, tuple] = dict()
    for field_name, field in model.model_fields.items():
        # We need to create a copy of the field,
        # as we need to make sure that it gets mapped to the list coerced version of the field.
        new_field = copy.deepcopy(field)
        new_field.validate_default = True

        assert field.annotation is not None, f"Field {field.title} ({field}) has a None annotation, but we require type annotations on fields."
        field_type = determine_inner_type(field.annotation)

        mapped_list_field[field_name] = (
            Annotated[
                Union[
                    # We first try to validate the type directly
                    field_type,
                    # If that fails, we coerce it into a list beforehand then validate it again.
                    Annotated[
                        field_type,
                        BeforeValidator(
                            lambda value: [value],
                            # and we ensure that in a JSON schema, this is properly marked
                            # as a singleton value.
                            json_schema_input_type=field.annotation
                        ),
                    ]
                ],
                # For cleaner serialization, we also serialize singleton types
                # as single arrays rather than full arrays. This is especially useful
                # for parameter tuning output.
                PlainSerializer(
                    lambda value: value.to_list()[0] if len(value.to_list()) == 1 else value
                )
            ],
            new_field
        )

    # Runtime assertion check: mapped_list_field does not contain any `__-prefixed` fields
    for key in mapped_list_field.keys():
        assert not key.startswith("__"), f"A private key has been passed from {name}'s argument schema. " + \
            "This should have been caught by the Snakemake CI step."

    # Pass this as kwargs to create_model, which usually takes in parameters field_name=type.
    # We do need to cast create_model, since otherwise the type-checker complains that we may
    # have had a key that starts with __ in mapped_list_fields. The above assertion prevents this.
    params_model = (cast(Any, create_model))(
        f'{name}ParamModel',
        __config__=ConfigDict(extra='forbid'),
        **mapped_list_field
    )

    # Get the default model instance by trying to serialize the empty dictionary
    try:
        params_model_default = params_model.model_validate({})
    except ValidationError:
        params_model_default = None

    # Then, we create a wrapping `run_model` which contains our params_model,
    # as well as any associated options with an individual run.
    run_model = create_model(
        f'{name}RunModel',
        params=(params_model, params_model_default),
        __base__=RunSettings,
        __config__=ConfigDict(extra='forbid')
    )

    # We use `model_validate` instead of the `run_model` constructor since `run_model` is based off of `RunSettings`
    run_model_default = None if params_model_default is None else run_model.model_validate({"params": params_model_default})

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
        runs=dict[str, run_model] if run_model_default is None else (dict[str, run_model], {"default": run_model_default}),
        __config__=ConfigDict(extra='forbid'),
        # Note that both entire algorithms and their runs inherit from `RunSettings`, to allow default runs such as
        # `allpairs` to have run-specific settings (e.g. allpairs with timeout.)
        __base__=RunSettings
    )

algorithm_models: list[type[BaseModel]] = [construct_algorithm_model(name, model.get_params_generic()) for name, model in algorithms.items()]
# name differentiates algorithms
AlgorithmUnion = Annotated[Union[tuple(algorithm_models)], Field(discriminator='name')]
