"""
A collection of 'tunable' functions, or functions which can be tuned to
produce 'midpoints.'

We consider parameter tuning a first-class feature of SPRAS configs,
so all algorithm list parameters are all marked with `Tunable`.
"""

from abc import ABC, abstractmethod
from collections.abc import Set
from typing import Annotated, Any, Callable, List, Self, Union

import numpy
from pydantic import BaseModel, Field, RootModel, model_validator

from spras.config.function_parsing import python_evalish_coerce


class Tunable[T](ABC):
    @abstractmethod
    def tune(self) -> Self:
        """
        Creates a tuned version of `self` which contains some sembalance of 'midpoints' on top of `self.`

        We impose a restriction: for all `P` implementing `Tunable`, any valid implementation of `P#tune` must satisfy that 
        for all `p : P`, we can construct some `p' = p.tune()` such that:
        1. `to_list(p)` is a sublist of `to_list(p')`,
        2. for every x, y in `to_list(p)` such that no z in `to_list(p)` satisfies x < z < y, there either:
            - exists a unique a z' in `to_list(p')` such that x < z' < y.
            - no such x < z' < y exists for all z' in to_list(p').
        
        We do this for the sake of parameter tuning (to avoid situations where what runs depend on what other runs is ambiguous),
        though this can be extended in the future to avoid that.
        """
        # TODO: enforce at runtime
        pass
    
    @abstractmethod
    def to_list(self) -> List[T]:
        pass

class TunableSet[S](RootModel[List[S]], Tunable[S]):
    """
    A thin wrapper class to allow generic sets to 'pretend' to be tunable.
    Note that `Tunableset#tune` is the identity function.
    """

    def tune(self):
        # NOTE: We use `type(self)` to access the constructor [This is annoying and I'm not a particular fan of it].
        # This happens throughout this file.
        return type(self)(self.root)

    def to_list(self):
        return self.root

def parse_from_function[T](data: Any, func: Callable[..., T], desired_function_name: str) -> T:
    """Convenience wrapper around `python_evalish_coerce` for trivial before model_validator declarations."""
    if not isinstance(data, str):
        return data

    return python_evalish_coerce(data, func, desired_function_name)

class BaseTunable[T](BaseModel, Tunable[T]):
    """No-op class to avoid double inheritance issues for IntegerAdapter"""
    pass

# TODO: The way we do `parse_from_string` for these methods is lenghty and bad for types,
# and frankly, this section is a lot of length "declaring definitions" boilerplate, with the only substance
# happening in their respective `tune` methods: can we make this better?
class Range(BaseModel, Tunable[int]):
    """A `range`-backed list of integers."""
    start: int = 0
    stop: int
    step: int = 1

    @model_validator(mode='before')
    @classmethod
    def parse_from_string(cls, data: Any) -> Any:
        return parse_from_function(data, lambda start, stop, step=1: {"start": start, "stop": stop, "step": step}, "range")

    def tune(self):
        return type(self)(start=self.start, stop=self.stop, step=int(self.step / 2.0))

    def to_list(self):
        return list(range(self.start, self.stop, self.step))

class LinSpace(BaseTunable[float]):
    """
    A tuning wrapper for numpy.linspace:
    see its associated documentation for parameter information.
    """
    
    start: float
    stop: float
    num: int = 50
    endpoint: bool

    @model_validator(mode='before')
    @classmethod
    def parse_from_string(cls, data: Any) -> Any:
        return parse_from_function(
            data,
            lambda start, stop, num=50, endpoint=True: {"start": start, "stop": stop, "num": num, "endpoint": endpoint},
            "np.linspace"
        )
    
    def tune(self):
        return type(self)(start=self.start, stop=self.stop, num=self.num * 2, endpoint=self.endpoint)
    
    def to_list(self):
        return list(numpy.linspace(self.start, self.stop, self.num, endpoint=self.endpoint).tolist())

class ARange(BaseTunable[float]):
    """
    A tuning wrapper for numpy.arange:
    see its associated documentation for parameter information.
    """
    
    start: float
    stop: float
    step: float = 1.0

    @model_validator(mode='before')
    @classmethod
    def parse_from_string(cls, data: Any) -> Any:
        return parse_from_function(
            data,
            lambda start, stop, step=1.0: {"start": start, "stop": stop, "step": step},
            "np.arange"
        )
    
    def tune(self):
        return type(self)(start=self.start, stop=self.stop, step=self.step / 2)
    
    def to_list(self):
        return list(numpy.arange(self.start, self.stop, self.step).tolist())

class LogSpace(BaseTunable[float]):
    """
    A tuning wrapper for numpy.logspace:
    see its associated documentation for parameter information.
    """
    
    start: float
    stop: float
    num: int = 50
    endpoint: bool = True
    base: float = 10.0

    @model_validator(mode='before')
    @classmethod
    def parse_from_string(cls, data: Any) -> Any:
        return parse_from_function(
            data,
            lambda start, stop, num=50, endpoint=True, base=10.0:
                {"start": start, "stop": stop, "num": num, "endpoint": endpoint, "base": base},
            "np.logspace"
        )
    
    def tune(self):
        # TODO: does logspace admit a proper `tune` implementation?
        return type(self)(start=self.start, stop=self.stop, num=self.num, endpoint=self.endpoint, base=self.base)
    
    def to_list(self):
        return list(numpy.logspace(self.start, self.stop, self.num, endpoint=self.endpoint, base=self.base).tolist())

class IntegerAdapter[S : (BaseTunable[float], BaseTunable[int])](RootModel[S], Tunable[int]):
    """Takes some Tunable[float/int] backed by a BaseModel and turns it into a Tunable[int]"""

    def tune(self):
        return type(self)(self.root.tune())

    def to_list(self):
        return list({int(elem) for elem in self.root.to_list()})


FloatTunable = Annotated[Union[Range, LinSpace, ARange, LogSpace, TunableSet[float]], Field(union_mode="left_to_right")]

# We have to annoyingly spread IntegerAdapter across every type we care about, to avoid multiple inheritance issues
# TODO: maybe a better way to do this?
IntegerTunable = Annotated[Union[Range, IntegerAdapter[LinSpace], IntegerAdapter[ARange], IntegerAdapter[LogSpace], TunableSet[int]], Field(union_mode="left_to_right")]
