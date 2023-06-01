from __future__ import annotations

from collections import UserString
from typing import Any
from typing import Sequence
from typing import TypeGuard

from ._shunt import Operator


# Operators
OPERATOR_UNION = Operator(
    symbol="|",
    name="Union",
)
OPERATOR_ARRAY = Operator(
    symbol="[]",
    name="Array",
    precedence=5,
    unary=True,
    unary_position="postfix",
)
OPERATOR_NOOP = Operator(
    symbol="NOOP",
    name="NOOP",
    unary=True,
)

OPS = [OPERATOR_ARRAY, OPERATOR_UNION]


def is_iterable_of(val: Sequence[Any], t: _T) -> TypeGuard[Sequence[_T]]:
    """Check all values of a list against the type.

    Args:
        val (Iterable[Any]): List of values to check
        t (_T): Type to check for

    Returns:
        TypeGuard[Iterable[_T]]: TypeGuard
    """
    assert not isinstance(val, (str, UserString))
    _bool = all(isinstance(x, t) for x in val)
    print(
        f"{val} {'is' if _bool else 'is not'} a sequence of {t}. (Type is {type(val)}) containing ({list(type(v) for v in val)})"
    )
    return _bool


__all__ = ["OPERATOR_UNION", "OPERATOR_ARRAY", "OPERATOR_NOOP", "OPS", "is_iterable_of"]
