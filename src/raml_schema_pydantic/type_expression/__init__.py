"""Module for handling Type Expressions."""
# pyright: basic
#  #strict
from __future__ import annotations

import logging
from abc import abstractmethod
from sys import version_info
from typing import Any
from typing import NoReturn
from typing import overload
from typing import TYPE_CHECKING
from typing import TypeVar

from pydantic import PydanticTypeError

from ._shunt import INode
from .array_type_expression import ArrayTypeExpression as ArrayTypeExpression
from .type_name import TypeName as TypeName

if TYPE_CHECKING:
    from ..types._IType import IType


# prevent no-redef type errors, see https://github.com/python/mypy/issues/1153#issuecomment-1207333806
if TYPE_CHECKING:
    if version_info < (3, 11):
        pass

        from typing_extensions import Self
    else:
        pass

        from typing import Self


logger = logging.getLogger(__name__)
LOG_LEVEL = logging.WARNING  # INFO


_T = TypeVar("_T")


class IComparableNode(INode):
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


__all__ = ("ArrayTypeExpression", "TypeName")
