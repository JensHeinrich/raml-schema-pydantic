from __future__ import annotations

from collections import UserString
from typing import Any
from typing import List
from typing import Sequence
from typing import Type
from typing import TypeGuard
from typing import TypeVar

from ._shunt import Operator
from ._shunt.token_types import Token

_T = TypeVar("_T")

# Operators
OPERATOR_UNION: Operator[Token] = Operator(
    symbol=Token("|"),
    name="Union",
)
OPERATOR_ARRAY: Operator[Token] = Operator(
    symbol=Token("[]"),
    name="Array",
    precedence=5,
    unary=True,
    unary_position="postfix",
)
OPERATOR_NOOP: Operator[Token] = Operator(
    symbol=Token("NOOP"),
    name="NOOP",
    unary=True,
)

OPS: List[Operator[Token]] = [OPERATOR_ARRAY, OPERATOR_UNION]


def is_iterable_of(val: Sequence[Any], t: Type[_T]) -> TypeGuard[Sequence[_T]]:
    """Check all values of a list against the type.

    Args:
        val (Iterable[Any]): List of values to check
        t (_T): Type to check for

    Returns:
        TypeGuard[Iterable[_T]]: TypeGuard
    """
    if isinstance(val, (str, UserString)):
        return False
    _bool = all(isinstance(x, t) for x in val)
    print(
        f"{val} {'is' if _bool else 'is not'} a sequence of {t}. (Type is {type(val)}) containing ({list(type(v) for v in val)})"
    )
    return _bool


__all__ = ["OPERATOR_UNION", "OPERATOR_ARRAY", "OPERATOR_NOOP", "OPS", "is_iterable_of"]
