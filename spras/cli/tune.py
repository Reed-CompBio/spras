"""
Generic algorithm tuning. We spend a good chunk of this file setting up configuration tuning,
then finally use it by wrapping it in a CLI subcommand that takes in a configuration.
"""

from dataclasses import dataclass, field
import itertools
from typing import Any, Callable, List, Mapping, NamedTuple, Optional
from pydantic import BaseModel, TypeAdapter
from spras.cli.util import window
from spras.config.schema import RawConfig
from spras.config.tunable import Tunable
from spras.util import NpHashEncoder, hash_params_sha1_base32

class Neighborly[C, N](NamedTuple):
    """A neighborly element takes note of itself and its desired neighbors."""
    current: C
    neighbors: List[N] = field(default_factory=list)

def type_algorithm_params(params: BaseModel) -> dict[str, Tunable[Any]]:
    """
    Applies runtime assertions to `params` and coerces it down into
    the looser `dict` structure
    """
    unfolded_params: dict[str, Tunable[Any]] = vars(params)
    for key in unfolded_params.keys():
        # We assert at runtime our (implicit) cast of `unfolded_params`
        assert issubclass(type(unfolded_params[key]), Tunable)
    return unfolded_params

@dataclass
class TunableNeighborly[S](Tunable[Neighborly[S, S]]):
    """
    NOTE: This does not store data in the form of `Tunable[Neighborly[S]]`,
    but that representation can be fetched through the `TunableNeighborly#to_list` method.
    """
    wrapped: Tunable[S]
    neighborly_elements: Mapping[S, List[S]] = field(default_factory=dict)

    def tune(self):
        old_wrapped = self.wrapped.to_list()
        new_wrapped = self.wrapped.tune()
        new_neighborly_elements = dict(self.neighborly_elements)
        for prev, curr, nxt in window(new_wrapped.to_list(), n = 3):
            if curr in old_wrapped: continue
            new_neighborly_elements[curr] = [prev, nxt]

        return type(self)(new_wrapped, new_neighborly_elements)

    def to_list(self):
        return [
            Neighborly(elem, neighbors=self.neighborly_elements[elem] if elem in self.neighborly_elements else [])
            for elem in self.wrapped.to_list()
        ]

def flatten_params(
    params: Mapping[str, List[Neighborly]],
    hash_function: Callable[[dict[str, Any]], str]
) -> dict[str, Neighborly[dict[str, Any], str]]:
    """
    Turns parameter dictionary lists of the form:
    a: [Neighborly(av1, [...]), Neighborly(av2, [...]), ...]
    b: [Neighborly(bv1, [...]), Neighborly(bv2, [...]), ...]
    To a dictionary of the form
    {hash: Neighborly({a: av1, b: bv1}, [hash1, ...]), ...}

    @param params: a dictionary with a description as described above.
    @param hash_function: the hash function to use to compute hashes for the return dictionary
    """
    final_dictionary: dict[str, Neighborly[dict[str, Any], str]] = dict()
    # Each parameter is a tuple of the form (a: Neighborly(...), b: Neighborly(...), ...)
    for parameter_combination in itertools.product(*params.values()):
        # We want to collect a list of neighbors of each parameter combination
        neighbors: list[dict[str, Any]] = []
        # We transform it into {a: Neighborly(...), b: Neighborly(...), ...}
        zipped_parameter_combination = dict(zip(params.keys(), parameter_combination))
        # and create a version of it with no neighbors
        forgetful_parameter_combination = {k: v.current for k, v in zipped_parameter_combination.items()}
        for key, value in zipped_parameter_combination.items():
            for neighbor in value.neighbors:
                # Then, add the adjacent parameter combination to the `forgetful_parameter_combination`.
                adjacent_parameter_combination = dict(forgetful_parameter_combination)
                adjacent_parameter_combination[key] = neighbor
                neighbors.append(adjacent_parameter_combination)
        final_dictionary[hash_function(forgetful_parameter_combination)] = Neighborly(
            forgetful_parameter_combination,
            neighbors=[hash_function(neighbor) for neighbor in neighbors]
        )
    return final_dictionary

# The following is a list of utility functions to encapsulate the above behavior
# in decreasing granularity.

def prepare_params(
    params: Mapping[str, Tunable]
) -> dict[str, TunableNeighborly]:
    """Attatches empty neighbor information to some given parameters."""
    return {k: TunableNeighborly(v) for k, v in params.items()}

def forget_tuning_params(
    params: Mapping[str, Tunable[Neighborly]]
) -> dict[str, List[Neighborly]]:
    """Removes tuning information about some given parameters"""
    return {k: v.to_list() for k, v in params.items()}

def tune_params(
    params: Mapping[str, Tunable],
    hash_function: Callable[[dict[str, Any]], str],
    tune_count: int = 1
) -> dict[str, Neighborly[dict[str, Any], str]]:
    """
    Tunes some `params` dictionary some `tune_count` number of times.

    @param params: a dictionary of parameter names to their `Tunable` values.
    @param hash_function: The function to use to hash parameter dictionaries.
    @param tune_count: The number of times to tune.
    @returns: A dictionary from hashes to parameter combinations, with associated neighbor information
        of what runs a run should depend on (see conditional runs.)
    """
    if tune_count < 1:
        raise ValueError(f"tune_count must be a positive integer: got {tune_count} instead.")
    # We first attach empty neighbor information to associated parameters
    prepared_params = prepare_params(params)
    # Then we perform our tuning
    tune_ready_params: Optional[dict[str, TunableNeighborly]] = None
    for _ in  range(tune_count):
        tune_ready_params = {k: v.tune() for k, v in prepared_params.items()}
    assert tune_ready_params is not None, "Empty range? This should have been caught by the first assumption."
    # We then forget tuning information
    tuned_params = forget_tuning_params(tune_ready_params)
    # then finally flatten the associated parameters
    return flatten_params(tuned_params, hash_function)

def preferred_model_dump(model: BaseModel) -> Any:
    """
    A custom invokation of BaseModel#model_dump which uses some preferred defaults to keep
    generated configuration sizes to a minimum.
    """
    return model.model_dump(by_alias=True, exclude_defaults=True, exclude_unset=True)

def model_vars(model: Any) -> dict[str, Any]:
    """Ignores model variables that are the default or unset: this acts as a kind of `vars`."""
    dumped_model = preferred_model_dump(model)
    return {k: v for k, v in dict(model).items() if k in dumped_model.keys()}

# Beyond this lies code that depends on types generated in algorithms.py.
# NOTE: If algorithms.py is refactored to be type-safe, this should be refactored as well.
def tune_run(
    run: Any,
    hash_function: Callable[[dict[str, Any]], str],
    tune_count: int = 1,
    # TODO: refactor to a lambda?
    process_run: Optional[Callable[[str], str]] = None
) -> dict[str, Any]:
    """
    Takes a run (a dictionary with at least a key "params") and returns a dictionary of
    hashes to new runs, preserving the associated non-params run properties
    while adding in new conditional runs.

    @param run: A pydantic object of runs.
    @param run_prefix: The prefix to attatch to all hashed parameter combinations.
    """
    if not process_run: process_run = lambda _: ""
    tuned_params = tune_params(model_vars(run.params), hash_function, tune_count)
    other_run_settings = {k: v for k, v in preferred_model_dump(run).items() if k != "params"}
    return {process_run(k): {
        "params": v.current,
        **other_run_settings,
        "if": [
            *[process_run(neighbor) for neighbor in v.neighbors],
            *(other_run_settings["if"] if "if" in other_run_settings else [])
        ]
    } for k, v in tuned_params.items()}

def tune_runs(
    runs: Any,
    hash_function: Callable[[dict[str, Any]], str],
    tune_count: int = 1,
) -> dict[str, Any]:
    all_runs: dict[str, Any] = dict()
    for run_name, run_model in runs.items():
        all_runs = {**all_runs, **tune_run(run_model, hash_function, tune_count, lambda run: f"{run_name}_{run}")}
    return all_runs

def tune_algorithm_union(
    algorithm: Any,
    hash_function: Callable[[dict[str, Any]], str],
    tune_count: int = 1,
) -> Any:
    dumped_model = preferred_model_dump(algorithm)
    dumped_model["runs"] = tune_runs(algorithm.runs, hash_function, tune_count)
    return TypeAdapter(type(algorithm)).validate_python(dumped_model)

def tune(
    config: RawConfig,
    hash_function: Callable[[dict[str, Any]], str],
    tune_count: int = 1,
) -> RawConfig:
    return config.model_copy(update={
        "algorithms": tune_algorithm_union([algorithm for algorithm in config.algorithms], hash_function, tune_count)
    })

# TODO: isolate and deduplicate from config.py
def hash_func(hash_length: int, params: dict[str, Any]) -> str:
    """
    General algorithm parameter dictionary hasher.
    """
    return hash_params_sha1_base32(params, hash_length, cls=NpHashEncoder)

"""The curried variant of `hash_func`."""
hash_factory = lambda hash_length: lambda params: hash_func(hash_length, params)
