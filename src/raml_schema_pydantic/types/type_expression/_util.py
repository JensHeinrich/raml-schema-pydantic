from __future__ import annotations

from collections import UserString
from typing import Any
from typing import Iterable
from typing import List
from typing import overload
from typing import Sequence
from typing import Tuple
from typing import Type
from typing import TypeGuard
from typing import TypeVar

from ._shunt import Operator
from ._shunt import Token

_T = TypeVar("_T")


# Operators
# class UnionOperator(Operator[Token]):
#     name = "Union"
#     symbol = Token("|")


OPERATOR_UNION: Operator[Token] = Operator[Token](
    value=Token("|"),
    name="Union",
    unary=False,
    precedence=5,
    associativity="left",
)


# class ArrayOperator(Operator[Token]):
#     symbol = Token("[]")
#     name = "Array"
#     precedence = 5
#     unary = True
#     unary_position = "postfix"


OPERATOR_ARRAY: Operator[Token] = Operator[Token](
    value=Token("[]"),
    name="Array",
    precedence=5,
    unary=True,
    unary_position="postfix",
    associativity="none",
)


# class NoopOperator(Operator[Token]):
#     symbol = Token("NOOP")
#     name = "NOOP"
#     unary = True


OPERATOR_NOOP: Operator[Token] = Operator[Token](
    value=Token("NOOP"),
    name="NOOP",
    unary=True,
    unary_position="prefix",
    associativity="none",
)

OPS: List[Operator[Token]] = [OPERATOR_ARRAY, OPERATOR_UNION]


@overload
def is_iterable_of(
    val: List[Any], t: Type[_T] | Tuple[Type[_T], ...]
) -> TypeGuard[List[_T]]:
    ...


@overload
def is_iterable_of(
    val: Tuple[Any], t: Type[_T] | Tuple[Type[_T], ...]
) -> TypeGuard[Tuple[_T]]:
    ...


@overload
def is_iterable_of(
    val: Sequence[Any], t: Type[_T] | Tuple[Type[_T], ...]
) -> TypeGuard[Sequence[_T]]:
    ...


def is_iterable_of(
    val: Iterable[Any], t: Type[_T] | Tuple[Type[_T], ...]
) -> TypeGuard[Iterable[_T]]:
    """Check all values of a sequence against the type.

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
