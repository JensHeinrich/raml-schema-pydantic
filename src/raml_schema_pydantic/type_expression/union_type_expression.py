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
from ._base_type_expression_type import BaseTypeExpressionType
from ._shunt import ITree  # , Tree
from ._shunt import Operator
from ._shunt import OperatorNode
from ._shunt import postfix_to_ast
from ._shunt import shunt
from ._shunt import ValueNode
from ._util import *

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


from .type_expression import TypeExpression

logger = logging.getLogger(__name__)
LOG_LEVEL = logging.WARNING  # INFO


_T = TypeVar("_T")


class UnionTypeExpression(
    # UserString, # A UnionTypeExpression is not a string, but can be created from one
    BaseTypeExpressionType
):
    # | `(type expression 1) \| (type expression 2)`
    # | An infix union operator indicates the resulting type might be either of type expression 1 or of type expression 2.
    # Multiple union operators can be combined between pairs of type expressions.
    # |
    # `string \| number:` either a string or a number <br><br>
    # `X \| Y \| Z`: either an X or a Y or a Z <br><br>
    # `(Manager \| Admin)[]:` an array whose members consist of Manager or Admin instances<br><br>
    # `Manager[] \| Admin[]:` an array of Manager instances or an array of Admin instances.
    types: List[TypeExpression]  # TODO should only allow ordered ?

    # FIXME overload for pyright
    @overload
    def __init__(
        self,
        seq: str
        | List[
            str
            | TypeExpression
            # | ArrayTypeExpression
            # | UnionTypeExpression
            # | TypeName
            # | NestedTypeExpression
        ],
    ) -> None:
        ...

    @overload
    def __init__(self, seq: List[str]) -> None:
        ...

    @overload
    def __init__(self, seq: List[TypeExpression]) -> None:
        ...

    @overload
    def __init__(
        self,
        seq: List[
            ArrayTypeExpression | UnionTypeExpression | TypeName | NestedTypeExpression
        ],
    ) -> None:
        ...

    @overload
    def __init__(self, seq: str) -> None:
        ...

    def __init__(
        self,
        seq: (
            object
            | List[
                ArrayTypeExpression
                | UnionTypeExpression
                | TypeName
                | NestedTypeExpression
            ]
            | List[TypeExpression]
            | List[str]
            | str
        ),
    ) -> None:
        if isinstance(seq, str):
            # An expression like "A|B" has been supplied
            self.types = self._extract_and_parse_types(seq)
            # super().__init__(seq)

        elif isinstance(seq, List):  # and not isinstance(seq, str):
            if is_iterable_of(
                seq,
                # Type: List[Union[ArrayTypeExpression,UnionTypeExpression,TypeName,NestedTypeExpression,]]
                # pyright: reportUnknownArgumentType=false
                (
                    ArrayTypeExpression,
                    UnionTypeExpression,
                    TypeName,
                    NestedTypeExpression,
                ),
            ):
                self.types = [TypeExpression(v) for v in seq]
            elif is_iterable_of(seq, TypeExpression):
                # FIXME
                self.types = seq  # pyright: reportGeneralTypeIssues=false
            # super().__init__("|".join(str(v) for v in seq))
        elif isinstance(seq, str):
            self.types = self._extract_and_parse_types(str(seq))
            # super().__init__(seq)

        assert getattr(self, "types", False)

    _regex: Pattern[str] = re.compile(r"^.+\|.+$")

    @classmethod
    def _extract_and_parse_types(cls, v: str) -> List[TypeExpression]:
        assert isinstance(v, str)

        _match = cls._regex.fullmatch(v)
        if not _match:
            raise PydanticErrors.StrRegexError(pattern=cls._regex.pattern)

        _reverse_polish_notation: List[str | Operator] = shunt(v, ops=OPS)
        if _reverse_polish_notation[-1] != OPERATOR_UNION:
            raise PydanticValueError("The expression was not parsed to an union type.")

        _errors: List[Exception] = []
        _parsed: ITree | None = None
        logger.log(level=LOG_LEVEL, msg=f"Parsing {v}")
        try:
            _parsed = postfix_to_ast(_reverse_polish_notation)
        except (ValueError, ValidationError, TypeError) as e:
            _errors.append(e)

        if _errors:
            _exc = ValidationError(errors=_errors, model=cls)
            logger.log(level=logging.error, msg=f"{_errors}")
            raise _exc

        assert _parsed is not None, f"{_parsed} should be a UnionTypeExpression"
        assert (
            _parsed.children is not None
        ), f"{_parsed} should be a UnionTypeExpression"
        return [str(child) for child in _parsed.children]

        _candidates = split_brackets(v)
        # This reimplements the try and except logic of an
        _errors: List[Exception] = []
        _parsed: Literal[False] | TypeExpression = False
        _members: List[TypeExpression] = []
        for _candidate in _candidates:
            try:
                _parsed = TypeExpression.parse_obj(_candidate)
                _members.append(_parsed)
            except (PydanticValueError, StrError) as exc:
                _errors.append(
                    ErrorWrapper(exc, loc=cls.__name__)
                )  # TODO check if better error location is possible
        if len(_members) == len(_candidates):
            return _members
        raise ValidationError(errors=_errors, model=cls)

    @classmethod
    def validate(cls, v: Any, field: Optional[ModelField] = None) -> "ValidateReturn":
        if isinstance(v, str):
            types = cls._extract_and_parse_types(v)
            return UnionTypeExpression(types), None
        elif isinstance(v, UnionTypeExpression):
            return v, None

        return None, [StrError]

    @classmethod
    def validator(cls, v: Any) -> Self:
        _instance, _errors = cls.validate(v)
        if _errors:
            raise ValidationError(errors=_errors, model=cls)

        return _instance

    def __str__(self) -> str:
        return "|".join(str(t) for t in self.types)

    def __repr__(self) -> str:
        return f"UnionTypeExpression({list([str(t) for t in self.types])})"

    def __eq__(
        self: Self, other: Self | BaseTypeExpressionType | TypeExpression | str | Any
    ) -> bool:
        if isinstance(other, type(self)):
            return (
                # comparing the two lists is the easiest way
                self.types
                == other.types
                # TODO implement associative comparison
            )
        if isinstance(other, BaseTypeExpressionType):  # implicitely not ArrayType
            if isinstance(other, NestedTypeExpression):
                return other == self
            return False
        if isinstance(other, TypeExpression):
            return other == self
        if isinstance(other, str):
            return TypeExpression(other) == self
        raise TypeError(f"Cannot compare {type(self)} to {type(other)}")

    @classmethod
    def parse_obj(cls, obj: str | List[TypeExpression] | Any) -> Self:
        logger.log(level=LOG_LEVEL, msg=f"Parsing {obj} to {cls.__qualname__}")
        if isinstance(obj, str):
            return cls(obj)
        elif (
            is_iterable_of(obj, TypeExpression)
            or is_iterable_of(obj, str)
            or is_iterable_of(obj, TypeExpressionType)
        ):
            return cls(obj)
        elif isinstance(obj, cls):
            return obj
        raise ValueError(
            f"Only stringlike objects or sequences of such are are supported, was given {obj}"
        )

    def as_type(self) -> Type:
        ...
        # from .types.union_type import UnionType
        # return UnionType(type_=self,super_types=self.types)

    @classmethod
    def __get_validators__(
        cls,
    ):
        yield cls.validate

    def __iter__(self):
        ...

    def _facets(self: Self) -> Sequence[str]:  # TODO
        return super()._facets

    def _properties(self: Self) -> Sequence[str]:  # TODO
        return super()._properties


from .array_type_expression import ArrayTypeExpression
from .type_name import TypeName
from .nested_type_expression import NestedTypeExpression
from .array_type_expression import ArrayTypeExpression
