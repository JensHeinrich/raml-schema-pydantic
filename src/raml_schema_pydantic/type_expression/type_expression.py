# pyright: basic
#  #strict
from __future__ import annotations

import json
import logging
from abc import abstractmethod
from collections import UserString
from sys import is_finalizing
from sys import version_info
from typing import Any
from typing import Callable
from typing import ClassVar
from typing import Dict
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
from ..types._TypeDeclarationProtocol import TypeDeclarationProtocol
from ._shunt import check_in
from ._shunt import ITree  # , Tree
from ._shunt import Operator
from ._shunt import OperatorNode
from ._shunt import postfix_to_ast
from ._shunt import shunt
from ._shunt import ValueNode
from ._util import OPERATOR_ARRAY
from ._util import OPERATOR_UNION
from ._util import OPS
from .array_type_expression import ArrayTypeExpression
from .union_type_expression import UnionTypeExpression

# from ..types._IType import IType
# from ..types._IType import RamlTypeProto
# from ._base_type_expression_type import BaseTypeExpressionType
# from ._util import UnionOperator, ArrayOperator

# TODO Use Callable
OPERATOR_DICT: Dict[
    Operator[Token],
    Type[UnionTypeExpression] | Type[ArrayTypeExpression] | Type[TypeName],
] = {
    OPERATOR_ARRAY: ArrayTypeExpression,
    OPERATOR_UNION: UnionTypeExpression,
}
# OPS: List[UnionOperator | ArrayOperator] = [
#     ArrayTypeExpression(),
#     UnionTypeExpression(),
# ]


# prevent no-redef type errors, see https://github.com/python/mypy/issues/1153#issuecomment-1207333806
if TYPE_CHECKING:
    import regex as re
    from regex import Pattern

    from typing_extensions import Self

    from ._shunt import Token
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

from ..types.type_declaration import ITypeDeclaration

InternalType_: TypeAlias = "ArrayTypeExpression | TypeName"  # FIXME


class TypeExpression(
    # UserString, # A TypeExpression is NOT a string or a UserString, but can be created from one
    TypeDeclarationProtocol,
):
    """Class for type expressions used as a container.

    Type expressions provide a powerful way of referring to, and even defining, types.
    Type expressions MAY be used wherever a type is expected.
    The simplest type expression is the name of a type.
    Using type expressions, you MAY devise type unions, arrays, maps, and other things.

    Comment: A TypeExpression is also a TypeDeclaration by definition
    > A type declaration references another type, or wraps or extends another type by adding functional facets (e.g. properties) or non-functional facets (e.g. a description),
    > or is a type expression that uses other types.

    """

    type_declaration: TypeDeclarationProtocol

    def schema(self: Self) -> Dict[str, Any]:
        return self.type_declaration.schema()

    def __repr__(self) -> str:
        return f"TypeExpression(type_declaration={repr(self.type_declaration)})"

    @classmethod
    def _parse(
        cls: Type[Self], v: str
    ) -> Tuple[TypeDeclarationProtocol, None] | Tuple[None, List[ErrorWrapper]]:
        _errors: List[ErrorWrapper] = []
        _parsed: None | ValueNode[Token] | OperatorNode[Token, Token] = None
        _type_declaration: TypeDeclarationProtocol
        _unhandled_tokens: None | List[Token | Operator[Token]]
        logger.log(level=LOG_LEVEL, msg=f"Parsing {v}")

        if not isinstance(v, str):
            raise StrError()

        try:
            _shunted: List[Token | Operator[Token]] = shunt(input_data=v, ops=OPS)

            def _parse_as_far_as_possible(
                input_data: List[Token | Operator[Token]],
                operator_dict: Dict[
                    Operator[Token],
                    Type[UnionTypeExpression]
                    | Type[ArrayTypeExpression]
                    | Type[TypeName],
                    # Type[TypeDeclarationProtocol]
                ],
            ) -> Tuple[TypeDeclarationProtocol, List[Token | Operator[Token]]]:
                _current: Token | Operator[Token] = input_data.pop()
                if check_in(_current, operator_dict):
                    # assert isinstance(_current, Operator) # nosec: ignore[B101] # for typechecking
                    left: TypeDeclarationProtocol
                    right: TypeDeclarationProtocol
                    # the right part of an expression is put on the stack later so it's popped first
                    right, input_data = _parse_as_far_as_possible(
                        input_data=input_data, operator_dict=operator_dict
                    )
                    # TODO implement operator dict instead of hardcoding
                    if _current.unary is True:  # unary operators only have on child
                        if _current == OPERATOR_ARRAY:
                            return (
                                ArrayTypeExpression(
                                    items=TypeExpression(type_declaration=right)
                                ),
                                input_data,
                            )
                    elif _current.unary is False:
                        # the left part follows
                        left, input_data = _parse_as_far_as_possible(
                            input_data=input_data, operator_dict=operator_dict
                        )
                        if _current == OPERATOR_UNION:
                            return (
                                UnionTypeExpression(
                                    super_types=[
                                        TypeExpression(type_declaration=left),
                                        TypeExpression(type_declaration=right),
                                    ]
                                ),
                                input_data,
                            )
                    else:
                        raise NotImplementedError()
                else:
                    return TypeName(_current), input_data

                raise ValueError()

            _type_declaration, _unhandled_tokens = _parse_as_far_as_possible(
                input_data=_shunted, operator_dict=OPERATOR_DICT
            )

            if _unhandled_tokens is not None:
                raise ValueError("Postfix notation was not resolvable")

            return _type_declaration, None
        except (ValueError, ValidationError, TypeError) as e:
            _errors.append(ErrorWrapper(exc=e, loc=(f"{v}@TypeExpression")))
        # Mapping of Operators to inner types:

        return None, _errors  #     if len(_errors) > 0 else None

    def __init__(
        self,
        # type_: BaseTypeExpressionType
        type_declaration: TypeDeclarationProtocol,
    ) -> None:
        self.type_declaration = type_declaration
        # self.type_ = type_
        # super().__init__()

    @overload
    @classmethod
    def validate(cls: Type[Self], v: TypeExpression) -> Self:
        ...

    @overload
    @classmethod
    def validate(cls: Type[Self], v: str) -> Self:
        ...

    @classmethod
    def validate(cls: Type[Self], v) -> TypeExpression:
        """Coerce the input_data into a TypeExpression.

        The following cases are possible:
        a) v is already a typeexpression
            -> v is returned
        b) v is a string
            -> v needs to be parsed
        c) v is a iterable of
            i) string
            ii) type expression
            -> v needs to be parsed as an inheritance type expression

            ~iii) base type expression type~
            ~iv) -> c)~

        Raises:
            ValueError: _description_
            ValidationError: _description_
            ValueError: _description_
            TypeError: _description_
            StrError: _description_
            TypeError: _description_

        Returns:
            TypeExpression: An instance of the class
        """
        if isinstance(v, TypeExpression):
            return v

        if isinstance(v, str):
            errors = []
            _parsed, _errors = cls._parse(v)
            if isinstance(_errors, ErrorWrapper):
                errors.append(_errors)
            elif isinstance(_errors, list):
                errors.extend(_errors)

            if errors:
                raise ValidationError(errors=errors, model=cls)

            assert _parsed is not None  # nosec: ignore[assert_used] # type checking
            return cls(type_declaration=_parsed)

        raise ValueError(f"Unsupported type {type(v)}")

    @classmethod
    def __get_validators__(cls):
        # one or more validators may be yielded which will be called in the
        # order to validate the input, each validator will receive as an input
        # the value returned from the previous validator
        def _debug_advanced(cls: Type[Self], values: _ValuesType):
            return debug_advanced(cls=cls, values=values, caller="TypeExpression")

        yield _debug_advanced
        yield cls.validate

    class Config:
        arbitrary_types_allowed = True  # TODO

    # def __iter__(self):
    #     return self.type_.__iter__()

    def _properties(self: Self) -> Sequence[str]:
        return self.type_declaration._properties

    @override
    def _facets(self: Self) -> Sequence[str]:
        return self.type_declaration._facets

    @classmethod
    def parse_obj(cls, obj: object) -> Self:
        """Parse an object as a model-like class.

        Args:
            obj (object): Object to parse as type

        Raises:
            ValidationError: Error containing the location of the sub errors additionally

        Returns:
            Self: Instance of the class
        """
        # _instance: Self
        # _errors: List[Exception]
        # _instance, _errors= cls.validate(obj)
        # if _errors:
        #     raise ValidationError(errors = _errors, loc="TypeExpression")

        if isinstance(obj, (TypeExpression, str)):
            return cls.validate(obj)
        raise PydanticTypeError(
            **{"msg_template": "Only `TypeExpression` or `str` allowed"}
        )


# |Expression | Description |
# |:--------|:------------|
# | `Person` | The simplest type expression: A single type
# | `Person[]` | An array of Person objects
# | `string[]` | An array of string scalars
# | `string[][]` | A bi-dimensional array of string scalars
# | `string \| Person` | A union type made of members of string OR Person
# | `(string \| Person)[]` | An array of the type shown above

# #### Grammar

# Type expressions are composed of names of built-in or custom types and certain symbols, as follows:


from .type_name import TypeName as TypeName
from .nested_type_expression import NestedTypeExpression as NestedTypeExpression
from .array_type_expression import ArrayTypeExpression as ArrayTypeExpression
from .union_type_expression import UnionTypeExpression as UnionTypeExpression
from .inheritance_type_expression import InheritanceExpression as InheritanceExpression

# TypeExpression.update_forward_refs()

if TYPE_CHECKING:
    from ..types.any_type import AnyType
