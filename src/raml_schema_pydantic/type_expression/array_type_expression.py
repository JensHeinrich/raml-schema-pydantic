# pyright: basic
#  #strict
from __future__ import annotations

import json
import logging
from abc import abstractmethod
from collections import UserString
from sys import version_info
from typing import Any
from typing import ClassVar
from typing import Dict
from typing import List
from typing import Literal
from typing import Mapping
from typing import NoReturn
from typing import Optional
from typing import overload
from typing import Sequence
from typing import Tuple
from typing import Type
from typing import TYPE_CHECKING
from typing import TypeAlias
from typing import TypeVar
from typing import Union

from pydantic import errors as PydanticErrors
from pydantic import PydanticTypeError
from pydantic import PydanticValueError
from pydantic import root_validator
from pydantic import StrError
from pydantic import validator
from pydantic.error_wrappers import ErrorList
from pydantic.error_wrappers import ErrorWrapper
from pydantic.fields import ModelField
from pydantic.main import BaseModel
from pydantic.utils import ROOT_KEY
from typing_extensions import deprecated
from typing_extensions import override

from .._errors import ValidationError
from .._helpers import _ValuesType
from .._helpers import debug
from .._helpers import debug_advanced
from ..types._IType import IType
from ..types._IType import RamlTypeProto
from ..types.array_type import ArrayType
from ..types.type_declaration import IInlineTypeDeclaration
from ..types.type_declaration import TypeDeclaration
from ._base_type_expression_type import BaseTypeExpressionType
from ._shunt import ITree  # , Tree
from ._shunt import Operator
from ._shunt import OperatorNode
from ._shunt import postfix_to_ast
from ._shunt import shunt
from ._shunt import Token
from ._shunt import ValueNode
from ._util import *
from .type_expression import TypeExpression
from .type_name import TypeName

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


if TYPE_CHECKING:
    from pydantic.error_wrappers import ErrorList
    from pydantic.fields import ValidateReturn


logger = logging.getLogger(__name__)
LOG_LEVEL = logging.WARNING  # INFO


_T = TypeVar("_T")


class ArrayTypeExpression(
    # UserString,
    # BaseTypeExpressionType,
    OperatorNode[Token, Token],
):
    # | `(type expression)[]`
    # | The array, a unary, postfix operator placed after another type expression, enclosed in parentheses as needed, indicates the resulting type is an array of instances of that type expression.
    # |
    # `string[]:` an array of strings<br><br>
    # `Person[][]:` an array of arrays of Person instances
    _regex: Pattern[str] = re.compile(
        # r"^\s*(?P<typecandidate>.*)\[\]\s*$"
        # r"^\s*(?P<typecandidate>([\w-]+|\((?#Manual override for allowing nested).+\)))\[\]\s*$"
        r"^\s*(?P<typecandidate>([\w\[\]-]+|\((?#Manual override for allowing nested).+\)))\[\]\s*$"
    )

    item_type: (
        # BaseTypeExpressionType |
        TypeExpression
        | TypeName
        # | TypeName
        # | str
    )

    @validator("item_type")
    def validate_item_type(
        cls, v: TypeExpression | TypeName | str
    ) -> TypeExpression | TypeName:
        if isinstance(v, TypeName):
            return v
        if isinstance(v, TypeExpression):
            return v

        return TypeExpression.parse_obj(v)

    def __repr__(self) -> str:
        return f"ArrayTypeExpression(item_type={self.item_type})"

    def __str__(self) -> str:
        if self.item_type:
            return f"{self.item_type}[]"
        return "array"

    @overload
    def __init__(self, seq: object | TypeExpression) -> None:
        ...

    @overload
    def __init__(self, *, item_type: str) -> None:
        ...

    def __init__(
        self,
        seq: object | TypeExpression | None = None,
        *,
        item_type: str | None = None,
    ) -> None:
        if seq is None and item_type is None:
            raise ValueError("Either a sequence or an item_type have to be provided")
        if seq is not None and item_type is not None:
            raise ValueError("Providing sequence and item_type is not supported")

        if isinstance(seq, TypeExpression):
            ...

        else:
            logger.warning(f"Expected TypeExpression, not {type(seq)}")

        # if isinstance(seq, TypeExpressionType):
        #     if isinstance(seq, (TypeName, ArrayTypeExpression)):
        #         logger.log(level=LOG_LEVEL, msg=f"{seq} will be followed by []")
        #         super().__init__(f"{seq}[]")
        #     elif isinstance(seq, NestedTypeExpression):
        #         super().__init__(f"({seq})[]")
        #     elif isinstance(seq, UnionTypeExpression):
        #         logger.log(
        #             level=LOG_LEVEL,
        #             msg=f"Pure UnionTypeExpressions as item types are not clearly defined: {seq}",
        #         )
        #         super().__init__(f"({seq})[]")
        #     elif isinstance(seq, InheritanceExpression):
        #         raise NotImplementedError("not implemented for inheritence types.")

        #     self.item_type = TypeExpression(seq)
        # elif isinstance(seq, TypeExpression):
        #     self.item_type = seq
        # elif seq is not None:
        #     _item_type, _errors = self._extract_and_parse_item_type(str(seq))
        #     if _errors:
        #         raise ValidationError(errors=_errors, model=self.__class__)
        #     self._item_type = _item_type
        #     super().__init__(seq)

        # if item_type is not None:
        #     self._item_type = item_type
        #     super().__init__(f"{item_type}[]")

    @classmethod
    def _extract_and_parse_item_type(
        cls, v: str
    ) -> (
        Tuple[TypeExpression, Sequence[Any] | ErrorWrapper | None]
        | Tuple[None, Sequence[Any] | ErrorWrapper]
    ):  # "ValidateReturn":
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

        # for t in [
        #     ArrayTypeExpression,
        #     TypeName,
        #     NestedTypeExpression,
        # ]:
        #     try:
        #         _parsed = t.parse_obj(_candidate)
        #         continue
        #     except PydanticValueError as exc:
        #         _errors.append(ErrorWrapper(exc, loc=cls.__name__))

        # if isinstance(_parsed, TypeExpressionType):
        #     assert _parsed is not None
        #     return _parsed, None

        _parsed = TypeExpression.parse_obj(v)

        # return TypeExpression(_parsed),None
        if isinstance(_parsed, TypeExpression):  # or issubclass(type(_parsed), str):
            assert _parsed != False  # Only for typing
            assert _parsed is not None
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
        assert _instance is not None  # ignore[B101] # for typechecking
        return _instance

    def __eq__(self: Self, other: Type[Self] | TypeExpression | object) -> bool:
        if isinstance(other, type(self)):
            return all((other.item_type == self.item_type,))

        # if isinstance(other, BaseTypeExpressionType):  # implicitely not ArrayType
        #     if isinstance(other, NestedTypeExpression):
        #         return other == self
        #     return False
        # if isinstance(other, TypeExpression):
        #     return other == self
        # if isinstance(other, str):
        #     return TypeExpression(other) == self
        raise TypeError(f"Cannot compare {type(self)} to {type(other)}")

    def as_type(self) -> IType:
        from ..types.array_type import ArrayType

        return ArrayType(items=self.item_type).as_type()

    def as_typedeclaration(self: Self) -> "TypeDeclaration":
        ...

    def as_raml(self):
        return ArrayType(items=self)

    @classmethod
    def __modify_schema__(cls, field_schema: dict[str, Any], field: ModelField | None):
        field_schema["type"] = "string"

    @classmethod
    def __get_validators__(
        cls,
    ):
        yield cls.validate

    # @classmethod
    # def parse_obj(cls, obj: str| Any) -> Self:
    #     if isinstance(obj, str):
    #         return cls(obj)
    #     raise ValueError(f"Only stringlike objects are supported, was given {obj}")
