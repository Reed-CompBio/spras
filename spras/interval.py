"""
Utilities for defining inequality intervals (e.g. l < x <= u)

For graph heuristics, we allow inequality intervals of the form (num) < (id)?. For example,
we can say "1500 <" for "1500 < x", or "1000 < x < 2000", etc.

[If there is ever a library that does this, we should replace this code with that library.]
"""

import tokenize
from enum import Enum
from io import BytesIO
from typing import Any, Optional, Self, cast

from pydantic import BaseModel, model_validator


class Operand(Enum):
    LT = "<"
    LTE = "<="
    EQ = "="
    GTE = ">="
    GT = ">"

    @classmethod
    def from_str(cls, string: str) -> Optional[Self]:
        return next((enum for enum in list(cls) if enum.value == string), None)

    def is_closed(self) -> bool:
        """Whether this is a closed inequality. We consider = to be closed."""
        match self:
            case Operand.LTE: return True
            case Operand.EQ: return True
            case Operand.GTE: return True
        return False

    def as_closed(self):
        """Closes an operand. Eq does not get modified."""
        match self:
            case Operand.LT: return Operand.LTE
            case Operand.GT: return Operand.GTE
        return self

    def as_opened(self):
        """Opens an operand. Eq does not get modified."""
        match self:
            case Operand.LTE: return Operand.LT
            case Operand.GTE: return Operand.GT
        return self

    def with_closed(self, closed: bool): return self.as_closed() if closed else self.as_opened()

    def compare(self, left, right) -> bool:
        match self:
            case Operand.LT: return left < right
            case Operand.LTE: return left <= right
            case Operand.EQ: return left == right
            case Operand.GTE: return left >= right
            case Operand.GT: return left > right

    def flip(self):
        match self:
            case Operand.LT: return Operand.GT
            case Operand.LTE: return Operand.GTE
            case Operand.EQ: return Operand.EQ
            case Operand.GTE: return Operand.LTE
            case Operand.GT: return Operand.LT

    @classmethod
    def combine(cls, left: Self, right: Self):
        """Combines two operands, returning None if the operands don't combine well."""
        match (left, right):
            case (Operand.LTE, Operand.LTE): return Operand.LTE
            case (Operand.LT, Operand.LTE): return Operand.LT
            case (Operand.LTE, Operand.LT): return Operand.LT
            case (Operand.LT, Operand.LT): return Operand.LT
            case (Operand.EQ, op): return op
            case (op, Operand.EQ): return op
            case (Operand.GTE, Operand.GTE): return Operand.GTE
            case (Operand.GT, Operand.GTE): return Operand.GT
            case (Operand.GTE, Operand.GT): return Operand.GT
            case (Operand.GT, Operand.GT): return Operand.GT
        return None

class Interval(BaseModel):
    lower: Optional[float]
    upper: Optional[float]
    lower_closed: bool
    upper_closed: bool

    def mem(self, num: float) -> bool:
        if self.lower is not None:
            meets_lower = self.lower <= num if self.lower_closed else self.lower < num
        else:
            meets_lower = True

        if self.upper is not None:
            meets_upper = num <= self.upper if self.upper_closed else num < self.upper
        else:
            meets_upper = True

        return meets_lower and meets_upper

    @classmethod
    def single(cls, num: float) -> Self:
        return cls(lower=num, upper=num, lower_closed=True, upper_closed=True)

    @classmethod
    def left_operand(cls, operand: Operand, num: float) -> Self:
        """Creates an interval whose operand is on the left (e.g. <300)"""
        match operand:
            case Operand.LT: return cls(lower=None, upper=num, lower_closed=False, upper_closed=False)
            case Operand.LTE: return cls(lower=None, upper=num, lower_closed=True, upper_closed=False)
            case Operand.EQ: return cls.single(num)
            case Operand.GTE: return cls(lower=num, upper=None, lower_closed=False, upper_closed=False)
            case Operand.GT: return cls(lower=num, upper=None, lower_closed=False, upper_closed=True)

    @classmethod
    def right_operand(cls, num: float, operand: Operand) -> Self:
        """Creates an interval whose operand is on the right (e.g. 300<)"""
        # TODO: remove cast?
        return cast(Self, Interval.left_operand(operand.flip(), num))

    @classmethod
    def from_string(cls, input: str) -> Self:
        # We can't do a normal string#split here for cases like "1500<"
        tokens = [t.string for t in tokenize.tokenize(BytesIO(input.encode('utf-8')).readline) if t.string != ""]
        tokens.pop(0) # drop utf-8 indicator

        assert len(tokens) != 0

        def parse_num(numstr: str) -> Optional[int]:
            # Allow pythonic separators
            try:
                return int(numstr.replace("_", ""))
            except:
                return None

        def is_id(idstr: str) -> bool: return idstr.isidentifier()

        # Case 1: (id?) operand number
        if is_id(tokens[0]):
            # No other cases have an id at the beginning: we get rid of it.
            tokens.pop(0)

        operand = Operand.from_str(tokens[0])
        if operand is not None:
            # (cont.) Case 1: (id?) operand number
            number = parse_num(tokens[1])
            assert number is not None, f"found operand {operand.value} and expected a number, but found {tokens[1]} instead."
            return cls.left_operand(operand, number)

        # All other cases have a number
        number = parse_num(tokens.pop(0))
        assert number is not None, f"expected a number, got {input} instead"

        # Case 2: number
        if len(tokens) == 0:
            return cls.single(number)

        # All other cases have an operand
        operand = Operand.from_str(tokens.pop(0))
        assert operand is not None, f"got {number}, expected an operand afterward."

        # Case 3: number operand (id?)
        if len(tokens) == 0 or len(tokens) == 1:
            if len(tokens) == 1: assert is_id(tokens[0])
            return cls.right_operand(number, operand)

        # Case 4: number operand id operand number
        id = tokens.pop(0)
        assert is_id(id), f"got an inequality of the form {number} {operand.value} and expected nothing or another identifier, but got {id} instead."

        second_operand_str = tokens.pop(0)
        second_operand = Operand.from_str(second_operand_str)
        assert second_operand is not None, f"got an inequality of the form {number} {operand.value} {id} and was expecting an operand, but got {second_operand_str} instead."

        second_number_str = tokens.pop(0)
        second_number = parse_num(second_number_str)
        assert second_number is not None, f"got an inequality of the form {number} {operand.value} {id} {second_operand.value} and was expecting a number, but got {second_number_str} instead."

        # don't want equals operands in a double inequality (a < b < c)
        assert operand is not Operand.EQ and second_operand is not Operand.EQ, f"in a double inequality, neither operand can be '='!"

        # are our two numbers valid?
        combined_operand = Operand.combine(operand, second_operand)
        assert combined_operand is not None, f"operands {operand.value} and {second_operand.value} must combine well with each other!"
        assert combined_operand.compare(number, second_number), f"{number} {operand.value} {second_number} does not hold!"

        if combined_operand.as_opened() == Operand.LT:
            return cls(
                lower=number,
                upper=second_number,
                lower_closed=operand.is_closed(),
                upper_closed=second_operand.is_closed()
            )
        else:
            return cls(
                lower=second_number,
                upper=number,
                lower_closed=second_operand.is_closed(),
                upper_closed=operand.is_closed()
            )

    def __str__(self) -> str:
        if not self.lower and not self.upper: return "{empty interval}"
        if not self.lower:
            return Operand.LT.with_closed(self.upper_closed).value + " " + str(self.upper)
        if not self.upper:
            return str(self.lower) + " " + Operand.LT.with_closed(self.lower_closed).value

        if self.lower == self.upper and self.lower_closed and self.upper_closed: return str(self.lower)

        return str(self.lower) + " " + Operand.LT.with_closed(self.lower_closed).value + " x " \
            + Operand.LT.with_closed(self.upper_closed).value + " " + str(self.upper)

    def __repr__(self) -> str:
        return f"Interval[{str(self)}]"

    # For parsing Intervals automatically with pydantic.
    @model_validator(mode="before")
    @classmethod
    def from_literal(cls, data: Any) -> Any:
        if isinstance(data, str):
            return cls.from_string(data)
        return data
