# pyright: basic
#  #strict
from __future__ import annotations

import logging
from abc import abstractmethod
from sys import version_info
from typing import Any
from typing import NoReturn
from typing import overload
from typing import Type
from typing import TYPE_CHECKING
from typing import TypeAlias
from typing import TypeVar
from typing import Union

from pydantic import PydanticTypeError

from ..types._IType import IType
from ._shunt import ITree  # , Tree
from ._shunt import OperatorNode
from ._shunt import ValueNode
from ._util import *

# prevent no-redef type errors, see https://github.com/python/mypy/issues/1153#issuecomment-1207333806
if TYPE_CHECKING:
    from typing_extensions import Self
else:
    if version_info < (3, 11):
        pass

        from typing_extensions import Self
    else:
        pass

        from typing import Self


if TYPE_CHECKING:
    pass


logger = logging.getLogger(__name__)
LOG_LEVEL = logging.WARNING  # INFO


_T = TypeVar("_T")


def IComparableNode(INode):
    """Interface to make INodes comparable."""

    @overload
    @abstractmethod
    def __eq__(self: INode, other: INode) -> bool:
        ...

    @overload
    @abstractmethod
    def __eq__(self: INode, other: Any) -> bool | NoReturn:
        ...

    @overload
    @abstractmethod
    def __eq__(self: "Self", other: "Self") -> bool:  # type: ignore[misc]
        ...

    @abstractmethod
    def __eq__(
        self: "INode | IType | Any", other: "INode | IType | Any"
    ) -> bool | NoReturn:
        ...


class MappingNotAllowedError(PydanticTypeError):
    msg_template = "Mapping type is not allowed"


from .type_expression import TypeExpression
from .type_name import TypeName
from .nested_type_expression import NestedTypeExpression
from .array_type_expression import ArrayTypeExpression
from .union_type_expression import UnionTypeExpression
from .inheritance_type_expression import InheritanceExpression


# # TODO: this could probably be done via an elegant regex
# def split_brackets(v: str) -> List[str]:
#     _candidates: List[str] = v.split("|")
#     _candidate: str | None = None
#     _collected_candidates: List[str] = []
#     while _candidates:
#         _c = _candidates.pop(0)
#         if _candidate is None:
#             _candidate = _c
#         else:
#             _candidate += "|" + _c

#         if _candidate.count("(") == _candidate.count(")"):
#             _collected_candidates.append(_candidate)
#             # yield _candidate
#             _candidate = None
#         elif _candidate.count("(") < _candidate.count(")"):
#             raise PydanticErrors.PydanticValueError(msg_template="Illegal brackets")
#     return _collected_candidates


from .type_expression_type import TypeExpressionType as TypeExpressionType
from ._base_type_expression_type import BaseTypeExpressionType

_TypeExpression = TypeVar("_TypeExpression", bound=TypeExpressionType)


def tree_from_typeexpressiontype_or_typeexpression(
    type_expression_type: TypeExpression
    | BaseTypeExpressionType,  # TypeExpressionType | TypeExpression,
) -> ITree:
    if isinstance(type_expression_type, TypeExpression):
        # if len(type_expression_type.trees) > 1:
        #     raise ValueError("Nested inheritance not supported")
        # return type_expression_type.trees[0]
        return type_expression_type.type_

    assert isinstance(type_expression_type, TypeExpressionType)

    if isinstance(type_expression_type, TypeName):
        return ValueNode(value=str(type_expression_type))
        # return Tree(__root__=ValueNode(value=str(type_expression_type)))
    elif isinstance(type_expression_type, ArrayTypeExpression):
        return OperatorNode(
            **OPERATOR_ARRAY.dict(),
            children=tree_from_typeexpressiontype_or_typeexpression(
                type_expression_type.item_type
            ),
        )
    elif isinstance(type_expression_type, UnionTypeExpression):
        return OperatorNode(
            **OPERATOR_UNION.dict(),
            children=[
                tree_from_typeexpressiontype_or_typeexpression(t).__root__
                for t in type_expression_type.types
            ],
        )
    elif isinstance(type_expression_type, NestedTypeExpression):
        # unwrap the type
        return tree_from_typeexpressiontype_or_typeexpression(
            type_expression_type.inner
        )
    # elif isinstance(type_expression_type, NestedTypeExpression):
    #     ...
    elif isinstance(
        type_expression_type, InheritanceExpression
    ):  # pyright: ignore[reportUnnecessaryIsInstance]
        raise NotImplementedError("Nested iheritance is not yet supported")
    else:
        raise TypeError(
            f"{type_expression_type} is of type {type(type_expression_type)}. Supported are: ArrayTypeExpression,UnionTypeExpression,NestedTypeExpression,InheritanceExpression "
        )


from .array_type_expression import ArrayTypeExpression as ArrayTypeExpression
from .type_name import TypeName as TypeName

__all__ = ("ArrayTypeExpression", "TypeName")
