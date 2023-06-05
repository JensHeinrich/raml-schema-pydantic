"""Module for Array Type Expressions."""
# pyright: basic
#  #strict
from __future__ import annotations

import logging
from sys import version_info
from typing import Any
from typing import Dict
from typing import List
from typing import Literal
from typing import Optional
from typing import Sequence
from typing import Tuple
from typing import Type
from typing import TYPE_CHECKING

from pydantic import errors as PydanticErrors
from pydantic import PydanticValueError
from pydantic import StrError
from pydantic import validator
from pydantic.error_wrappers import ErrorWrapper
from pydantic.fields import ModelField

from .._errors import ValidationError
from ..types._TypeDeclarationProtocol import TypeDeclarationProtocol
from ._shunt import shunt
from .type_expression import TypeExpression

# prevent no-redef type errors, see https://github.com/python/mypy/issues/1153#issuecomment-1207333806
if TYPE_CHECKING:
    import regex as re
    from regex import Pattern

    from typing_extensions import Self
else:
    if version_info < (3, 11):
        import regex as re
        from regex import Pattern

        from typing_extensions import Self
    else:
        import re
        from re import Pattern

        from typing import Self


logger = logging.getLogger(__name__)
LOG_LEVEL = logging.WARNING  # INFO


class ArrayTypeExpression(
    TypeDeclarationProtocol,
):
    # | `(type expression)[]`
    # | The array, a unary, postfix operator placed after another type expression, enclosed in parentheses as needed, indicates the resulting type is an array of instances of that type expression.
    # |
    # `string[]:` an array of strings<br><br>
    # `Person[][]:` an array of arrays of Person instances
    _regex: Pattern[str] = re.compile(
        r"^\s*(?P<typecandidate>([\w\[\]-]+|\((?#Manual override for allowing nested).+\)))\[\]\s*$"
    )

    items: TypeDeclarationProtocol

    @validator("item_type")
    def validate_item_type(
        cls, v: TypeExpression | str  # | TypeName
    ) -> TypeExpression:
        if isinstance(v, TypeExpression):
            return v

        return TypeExpression.parse_obj(v)

    def __repr__(self) -> str:
        return f"ArrayTypeExpression(items={repr(self.items)})"

    def __str__(self) -> str:
        return f"{str(self.items)}[]"

    def __init__(
        self,
        items: TypeExpression,
    ) -> None:
        if isinstance(items, TypeExpression):
            self.items = items
        else:
            logger.warning(f"Expected TypeExpression, not {type(items)}")

    @classmethod
    def _extract_and_parse_item_type(
        cls, v: str
    ) -> (
        Tuple[TypeExpression, Sequence[Any] | ErrorWrapper | None]
        | Tuple[None, Sequence[Any] | ErrorWrapper]
    ):
        _match = cls._regex.fullmatch(v)
        if not _match:
            return None, [
                ErrorWrapper(
                    exc=PydanticErrors.StrRegexError(pattern=cls._regex.pattern),
                    loc="ArrayTypeExpression",
                )
            ]

        if shunt(v, ops=OPS).pop() != OPERATOR_ARRAY:
            return None, [
                PydanticValueError(
                    msg="The expression was not parsed to an array type."
                )
            ]
        _candidate = _match.groupdict()["typecandidate"]

        # This reimplements the try and except logic of an
        _errors: List[Exception] = []
        _parsed: Literal[False] | TypeExpression = False

        _parsed = TypeExpression.parse_obj(v)

        # return TypeExpression(_parsed),None
        if isinstance(_parsed, TypeExpression):  # or issubclass(type(_parsed), str):
            assert _parsed != False  # nosec: ignore[B101] # for typechecking
            assert _parsed is not None  # nosec: ignore[B101] # for typechecking
            return _parsed, None

        return None, _errors

    @classmethod
    def validate(  # type: ignore[override]
        cls, v: Any, field: Optional[ModelField] = None
    ) -> (
        Tuple[ArrayTypeExpression, Sequence[Any] | ErrorWrapper | None]
        | Tuple[None, Sequence[Any] | ErrorWrapper]
    ):
        if isinstance(v, str):
            _item_type = cls._extract_and_parse_item_type(v)
            return ArrayTypeExpression(_item_type), None
        elif isinstance(v, ArrayTypeExpression):
            return v, None
        return None, ErrorWrapper(exc=StrError(), loc="ArrayTypeExpression")

    @classmethod
    def validator(cls: Type[Self], v: Any) -> Self | ArrayTypeExpression:
        _instance, _errors = cls.validate(v)
        if _errors:
            raise ValidationError(errors=_errors, model=cls)
        assert _instance is not None  # nosec: ignore[B101] # for typechecking
        return _instance

    @classmethod
    def __get_validators__(
        cls,
    ):
        yield cls.validate

    def schema(self: Self) -> Dict[str, Any]:
        return {
            "type": "array",
            "items": self.items.schema(),
        }

    # @classmethod
    # def parse_obj(cls, obj: str| Any) -> Self:
    #     if isinstance(obj, str):
    #         return cls(obj)
    #     raise ValueError(f"Only stringlike objects are supported, was given {obj}")
