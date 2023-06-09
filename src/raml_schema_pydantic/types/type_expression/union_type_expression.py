# pyright: basic
#  #strict
# from __future__ import annotations
import json
import logging
from abc import abstractmethod
from collections import UserString
from sys import version_info
from typing import Any
from typing import cast
from typing import ClassVar
from typing import Dict
from typing import ForwardRef
from typing import Iterable
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
from pydantic import PydanticValueError
from pydantic import StrError

from .type_name import TypeName

Token: TypeAlias = TypeName
# from ._shunt import Token

from ..._errors import ValidationError
from ..._helpers import _ValuesType
from ..._helpers import debug
from ..._helpers import debug_advanced
from .._IType import IType, TypeDeclarationProtocol
from ..union_type import UnionType

# from ._base_type_expression_type import BaseTypeExpressionType
from ._shunt import ITree  # , Tree
from ._shunt import Operator
from ._shunt import OperatorNode
from ._shunt import postfix_to_ast
from ._shunt import shunt
from ._shunt import ValueNode
from ._util import OPS, OPERATOR_UNION, is_iterable_of

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
from pydantic.fields import ModelField


# from .type_expression import TypeExpression
TypeExpression = ForwardRef("TypeExpression")
logger = logging.getLogger(__name__)
LOG_LEVEL = logging.WARNING  # INFO


_T = TypeVar("_T")


class UnionTypeExpression(
    # UserString, # A UnionTypeExpression is not a string, but can be created from one
    # Operator[Token],
    # OperatorNode[Token, Token],
    TypeDeclarationProtocol,
):
    # | `(type expression 1) \| (type expression 2)`
    # | An infix union operator indicates the resulting type might be either of type expression 1 or of type expression 2.
    # Multiple union operators can be combined between pairs of type expressions.
    # |
    # `string \| number:` either a string or a number <br><br>
    # `X \| Y \| Z`: either an X or a Y or a Z <br><br>
    # `(Manager \| Admin)[]:` an array whose members consist of Manager or Admin instances<br><br>
    # `Manager[] \| Admin[]:` an array of Manager instances or an array of Admin instances.
    super_types: Sequence[TypeExpression]  # TODO should only allow ordered ?

    # FIXME overload for pyright
    # @overload
    # def __init__(
    #     self,
    #     seq: str
    #     | List[
    #         str
    #         | TypeExpression
    #         # | ArrayTypeExpression
    #         # | UnionTypeExpression
    #         # | TypeName
    #         # | NestedTypeExpression
    #     ],
    # ) -> None:
    #     ...

    # @overload
    # def __init__(self, seq: List[str]) -> None:
    #     ...

    # @overload
    # def __init__(self, seq: List[TypeExpression]) -> None:
    #     ...

    # @overload
    # def __init__(
    #     self,
    #     seq: List[
    #         ArrayTypeExpression | UnionTypeExpression | TypeName | NestedTypeExpression
    #     ],
    # ) -> None:
    #     ...

    # @overload
    # def __init__(self, seq: str) -> None:  # type: ignore[misc]
    #     ...

    # def __init__(
    #     self,
    #     super_types: List[TypeExpression],
    #     # seq: (
    #     #     object
    #     #     | List[
    #     #         ArrayTypeExpression
    #     #         | UnionTypeExpression
    #     #         | TypeName
    #     #         | NestedTypeExpression
    #     #     ]
    #     #     | List[TypeExpression]
    #     #     | List[str]
    #     #     | str
    #     # ),
    # ) -> None:
    #     self.super_types = super_types
    #     super().__init__(**dict(OPERATOR_UNION))
    #     assert getattr(self, "types", False)

    def __init__(self: Self, super_types: Sequence[TypeExpression]) -> None:
        self.super_types = super_types

    _regex: Pattern[str] = re.compile(r"^.+\|.+$")

    @classmethod
    def _extract_and_parse_types(cls, v: str) -> List[TypeExpression]:
        if not isinstance(v, str):
            raise StrError()

        _match = cls._regex.fullmatch(v)
        if not _match:
            raise PydanticErrors.StrRegexError(pattern=cls._regex.pattern)

        _reverse_polish_notation: List[Token | Operator] = shunt(v, ops=OPS)
        if _reverse_polish_notation[-1] != OPERATOR_UNION:
            raise PydanticValueError(
                msg_template="The expression was not parsed to an union type."
            )

        _errors: List[Exception] = []
        _parsed: ValueNode[Token] | OperatorNode[Token, Token] | None = None
        logger.log(level=LOG_LEVEL, msg=f"Parsing {v}")
        try:
            _parsed = postfix_to_ast(_reverse_polish_notation)
        except (ValueError, ValidationError, TypeError) as e:
            _errors.append(e)

        if _errors:
            _exc = ValidationError(errors=_errors, model=cls)
            logger.log(level=logging.ERROR, msg=f"{_errors}")
            raise _exc

        if not isinstance(_parsed, OperatorNode):
            raise PydanticValueError(
                msg_template=f"{_parsed} should be a UnionTypeExpression"
            )

        return [TypeExpression(type_declaration=child) for child in _parsed.children]

    @overload
    @classmethod
    def validate(
        cls: Type[Self], v: str, field: Optional[ModelField] = None
    ) -> Tuple[Self, None] | Tuple[None, Sequence[Exception]]:
        ...

    @overload
    @classmethod
    def validate(
        cls: Type[Self], v: List[TypeExpression], field: Optional[ModelField] = None
    ) -> Tuple[Self, None] | Tuple[None, Sequence[Exception]]:
        ...

    @classmethod
    def validate(
        cls: Type[Self],
        v: str | List[TypeExpression] | Any,
        field: Optional[ModelField] = None,
    ) -> Tuple[Self, None] | Tuple[None, Sequence[Exception]]:
        if isinstance(v, str):
            # An expression like "A|B" has been supplied
            return cls(super_types=cls._extract_and_parse_types(v)), None
            # super_types = cls._extract_and_parse_types(v)

        elif isinstance(v, List) and is_iterable_of(
            v, TypeExpression
        ):  # and not isinstance(seq, str):
            return cls(super_types=v), None
            # super_types = v
            # if is_iterable_of(
            #     v,
            #     # Type: List[Union[ArrayTypeExpression,UnionTypeExpression,TypeName,NestedTypeExpression,]]
            #     # pyright: ignore[reportUnknownArgumentType]
            #     (
            #         ArrayTypeExpression,
            #         UnionTypeExpression,
            #         TypeName,
            #         NestedTypeExpression,
            #     ),
            # ):
            #     self.types = [TypeExpression(v) for v in seq]
            # elif is_iterable_of(seq, TypeExpression):
            #     # FIXME
            #     self.types = seq  # type: ignore[assignment] # pyright: ignore[reportGeneralTypeIssues]
            # # super().__init__("|".join(str(v) for v in seq))
        # elif isinstance(seq, str):
        #     self.types = self._extract_and_parse_types(str(seq))
        #     # super().__init__(seq)
        # if isinstance(v, str):
        #     types = cls._extract_and_parse_types(v)
        #     return cls(types), None
        elif isinstance(v, UnionTypeExpression):
            return cast(Self, v), None

        return None, [StrError()]

    @classmethod
    def validator(cls: Type[Self], v: Any) -> Self:
        _instance, _errors = cls.validate(v)
        if _errors:
            raise ValidationError(errors=_errors, model=cls)

        assert _instance is not None  # nosec: ignore[assert_used] # type checking only
        return _instance

    def __str__(self) -> str:
        return "|".join(str(t) for t in self.super_types)

    def __repr__(self) -> str:
        return f"UnionTypeExpression({list([str(t) for t in self.super_types])})"

    def __eq__(
        self: Self, other: Self | TypeExpression | str | Any  # | BaseTypeExpressionType
    ) -> bool:
        if isinstance(other, type(self)):
            return (
                # comparing the two lists is the easiest way
                self.super_types
                == other.super_types
                # TODO implement associative comparison
            )
        # if isinstance(other, BaseTypeExpressionType):  # implicitely not ArrayType
        #     if isinstance(other, NestedTypeExpression):
        #         return other == self
        #     return False
        if isinstance(other, TypeExpression):
            return other == self
        raise TypeError(f"Cannot compare {type(self)} to {type(other)}")

    # Handle a list of TypeExpressions
    @overload
    @classmethod
    def parse_obj(cls: Type[Self], obj: List[TypeExpression]) -> Self:
        ...

    # Handle a string
    @overload
    @classmethod
    def parse_obj(cls: Type[Self], obj: str) -> Self:
        ...

    @classmethod
    def parse_obj(cls: Type[Self], obj: str | List[TypeExpression] | Any) -> Self:
        logger.log(level=LOG_LEVEL, msg=f"Parsing {obj} to {cls.__qualname__}")
        if isinstance(obj, str):
            return cls(super_types=cls._extract_and_parse_types(obj))
        elif is_iterable_of(obj, TypeExpression):
            return cls(super_types=obj)
        elif (
            is_iterable_of(obj, str)
            # or is_iterable_of(obj, TypeExpressionType)
        ):
            return cls(super_types=[TypeExpression.parse_obj(t) for t in obj])
        elif isinstance(obj, cls):
            return obj
        raise PydanticValueError(
            msg_template=f"Only string-like objects or sequences of such are are supported, was given {obj} of type {type(obj)}"
        )

    @classmethod
    def __get_validators__(
        cls,
    ):
        yield cls.validate

    def __iter__(self):
        ...

    # def _facets(self: Self) -> Sequence[str]:  # TODO
    #     return super()._facets

    # def _properties(self: Self) -> Sequence[str]:  # TODO
    #     return super()._properties

    def schema(self, by_alias=..., ref_template=...) -> Dict[str, Any]:
        return UnionType(super_types=self.super_types).schema()


# from .array_type_expression import ArrayTypeExpression
# from .type_name import TypeName
# from .nested_type_expression import NestedTypeExpression
# from .array_type_expression import ArrayTypeExpression
