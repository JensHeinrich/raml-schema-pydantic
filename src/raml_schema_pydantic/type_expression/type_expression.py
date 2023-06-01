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
from ..types._IType import RamlTypeProto
from ..types._IType import TypeDeclarationProtocol
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

    from ._shunt.token_types import Token
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
    # BaseTypeExpressionType,
    # BaseModel,
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

    # type_: BaseTypeExpressionType
    type_: RamlTypeProto  # InternalType_
    type_declaration: TypeDeclarationProtocol

    def schema(self: Self) -> Dict[str, Any]:
        return self.type_declaration.schema()

    # def as_type(self: Self) -> "AnyType":
    #     return self.type_.as_type()

    # def as_raml(self: Self):
    #     return self.type_.as_raml()

    def __repr__(self) -> str:
        return f"TypeExpression(type_={repr(self.type_)})"

    @classmethod
    def _parse(
        cls: Type[Self], v: str
    ) -> Tuple[Self, None] | Tuple[None, List[ErrorWrapper]]:  #  "ValidateReturn":
        _errors: List[ErrorWrapper] = []
        _parsed: None | ValueNode[Token] | OperatorNode[Token, Token] = None
        logger.log(level=LOG_LEVEL, msg=f"Parsing {v}")

        if not isinstance(v, str):
            raise StrError()

        try:
            _shunted: List[Token | Operator[Token]] = shunt(input_data=v, ops=OPS)
            _parsed = postfix_to_ast(_shunted)
            cls(type_=_parsed)
        except (ValueError, ValidationError, TypeError) as e:
            _errors.append(ErrorWrapper(exc=e, loc=(f"{v}@TypeExpression")))
        return _parsed, _errors if len(_errors) > 0 else None

    def __init__(self, type_: BaseTypeExpressionType) -> None:
        self.type_ = type_
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

            return cls(type_=_parsed)

        raise ValueError(f"Unsupported type {type(v)}")

    @classmethod
    def __get_validators__(cls):
        # one or more validators may be yielded which will be called in the
        # order to validate the input, each validator will receive as an input
        # the value returned from the previous validator
        def _debug_advanced(cls: Type[Self], values: _ValuesType) -> "ValidateReturn":
            return debug_advanced(cls=cls, values=values, caller="TypeExpression")

        yield _debug_advanced
        yield cls.validate

    class Config:
        arbitrary_types_allowed = True  # TODO

    def __iter__(self):
        return self.type_.__iter__()

    def _properties(self: Self) -> Sequence[str]:
        return self.type_._properties

    @override
    def _facets(self: Self) -> Sequence[str]:
        return self.type_._facets

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

        assert isinstance(obj, (TypeExpression, str))
        return cls.validate(obj)


# class TypeExpressionOld(
#     # UserString, # A TypeExpression is NOT a string or a UserString, but can be created from one
#     ITypeDeclaration,
#     # BaseTypeExpressionType,
# ):
#     """Class for type expressions used as a container.

#     Type expressions provide a powerful way of referring to, and even defining, types.
#     Type expressions MAY be used wherever a type is expected.
#     The simplest type expression is the name of a type.
#     Using type expressions, you MAY devise type unions, arrays, maps, and other things.

#     Comment: A TypeExpression is also a TypeDeclaration by definition
#     > A type declaration references another type, or wraps or extends another type by adding functional facets (e.g. properties) or non-functional facets (e.g. a description),
#     > or is a type expression that uses other types.

#     """

#     # tree: Tree
#     trees: List[ITree]
#     type_: BaseTypeExpressionType
#     __config__ = None

#     # def __iter__(self: Self):
#     #     ...

#     @overload
#     def __init__(self: Self, seq: str) -> None:
#         ...

#     @overload
#     def __init__(self, seq: str | ITree | BaseTypeExpressionType) -> None:
#         ...

#     @overload
#     def __init__(self, seq: List[str | ITree | BaseTypeExpressionType]) -> None:
#         ...

#     # @overload  # TODO Remove __root__ references
#     # @deprecated("Do not provide a __root__ argument")
#     # def __init__(self, *, __root__: TypeExpressionType) -> NoReturn:
#     #     """Raises DeprecationWarning"""
#     #     ...

#     def __init__(
#         self,
#         seq: Optional[
#             object
#             | str
#             | OperatorNode
#             | ValueNode
#             | BaseTypeExpressionType
#             | List[str | OperatorNode | ValueNode | BaseTypeExpressionType]
#         ] = None,
#         # TODO Remove __root__ references
#         # __root__: Optional[TypeExpressionType] = None,
#     ) -> None:
#         """Initialize an instance of the class."""
#         # # TODO Remove __root__ references
#         # if __root__ is not None:
#         #     super().__init__(seq=str(__root__))
#         #     _warning = DeprecationWarning(
#         #         "Calling with __root__ arguments is deprecated"
#         #     )
#         #     logger.log(
#         #         level=LOG_LEVEL,
#         #         msg="Called TypeExpression with __root__",
#         #         exc_info=_warning,
#         #     )
#         #     raise _warning

#         _type, _error = self.validate(seq)
#         if _error:
#             raise _error
#         # super().__init__(seq)
#         self.type_ = _type
#         # if isinstance(seq,str):
#         # self.data = seq

#     @overload
#     @classmethod
#     def validate(cls, seq: TypeExpression) -> Self:
#         # Case a
#         ...

#     @overload
#     @classmethod
#     def validate(cls, seq: str) -> Self:
#         # Case b
#         ...

#     @overload
#     @classmethod
#     def validate(cls, seq: Sequence[str]) -> Self:
#         ...
#         # Case c i

#     @overload
#     @classmethod
#     def validate(cls, seq: Sequence[TypeExpression]) -> Self:
#         ...
#         # Case c ii

#     # @overload
#     # def validate(
#     #     self, seq: str | ITree | TypeExpressionType
#     # ) -> (
#     #     Self
#     # ):  # Type[Tuple[Self | None, Sequence[ErrorWrapper] | ErrorWrapper | None]]:
#     #     ...

#     # @overload
#     # def validate(
#     #     self, seq: List[str | ITree | TypeExpressionType]
#     # ) -> (
#     #     Self
#     # ):  # Type[Tuple[Self | None, Sequence[ErrorWrapper] | ErrorWrapper | None]]:
#     #     ...

#     @classmethod
#     def validate(cls, seq: Any) -> TypeExpressionOld:
#         # Tuple[
#         #     List[OperatorNode | ValueNode] | None,
#         #     str | None,  # The textual representation for the expression
#         #     ValidationError | None,
#         # ]:  # ->"ValidateReturn":
#         """Coerce the input_data into a TypeExpression.

#         The following cases are possible:
#         a) input_data is already a typeexpression
#         b) input_data is a string
#         c) input_data is a list of
#             i) string
#             ii) type expression
#             ~iii) base type expression type~
#             ~iv) -> c)~

#         Raises:
#             ValueError: _description_
#             ValidationError: _description_
#             ValueError: _description_
#             TypeError: _description_
#             StrError: _description_
#             TypeError: _description_

#         Returns:
#             TypeExpression: An instance of the class
#         """

#         if isinstance(seq, TypeExpression):
#             return seq

#         if isinstance(seq, str):
#             return cls.parse_obj(seq)

#         @overload
#         def _handle_types(
#             s: TypeExpression,
#         ) -> Tuple[TypeExpression, None]:
#             ...

#         @overload
#         def _handle_types(
#             s: BaseTypeExpressionType,
#         ) -> Tuple[BaseTypeExpressionType, None]:
#             ...

#         @overload
#         def _handle_types(
#             s: str,
#         ) -> (
#             Tuple[BaseTypeExpressionType, None]
#             | Tuple[None, List[ErrorWrapper] | ErrorWrapper]
#         ):
#             ...

#         def _handle_types(s) -> "ValidateReturn":
#             if isinstance(s, TypeExpression):
#                 return s, None

#             if isinstance(s, BaseTypeExpressionType):
#                 return s, None

#             if isinstance(s, str):
#                 _parsed_string, _errors = cls._parse(s)
#                 logger.warning(
#                     f"Parsed string: {_parsed_string} type: {type(_parsed_string)} errors: {_errors}"
#                 )
#                 return (_parsed_string, _errors)

#             if isinstance(s, Sequence):
#                 logger.warning(
#                     f"Trying to parse Iterable as InheritanceTypeExpression. {s}{type(s)}"
#                 )
#                 _results = []
#                 _error_list: List[ErrorWrapper] = []
#                 for i, v in enumerate(s):
#                     logger.warning(f"Handling {type(v)}{v} {v.__repr__()}")
#                     if isinstance(v, tuple):
#                         for _v in v:
#                             logger.warning(f"Tuple {_v}, {type(_v)}")
#                     if isinstance(v, str):
#                         _rr, _ee = _handle_types(v)
#                         if _ee:
#                             _error_list += [
#                                 ErrorWrapper(exc=_e.exc, loc=(*_e.loc, i)) for _e in _ee
#                             ]
#                             for _e in _ee:
#                                 logger.error(exc=_e)
#                         else:
#                             _results.append(_rr)
#                             logger.warning(
#                                 f"result: {_rr} type: {type(_rr)} {_rr.__repr__()} {_rr.__str__()}"
#                             )
#                     assert isinstance(v, TypeExpression)
#                 logger.warning(f"Parsed Iterable to {_results} raising {_error_list}")
#                 try:
#                     _type = InheritanceExpression(__root__=_results)
#                     return _type, None
#                 except (ValueError, TypeError, AssertionError) as exc:
#                     _error_list.append(
#                         ErrorWrapper(exc=exc, loc=("InheritanceExpression"))
#                     )

#             return None, [
#                 ErrorWrapper(
#                     exc=PydanticTypeError(
#                         msg_template="TypeExpression or string or list of these expected"
#                     ),
#                     loc=("TypeName"),
#                 )
#             ]

#         _instance, _errors = _handle_types(seq)
#         if _errors:
#             return None, ValidationError(
#                 errors=_errors,
#                 model=self.__class__,
#             )
#         return _instance, None
#         _type: BaseTypeExpressionType  # the type the expression is referencing

#         if any(
#             {
#                 isinstance(seq, t)
#                 for t in {
#                     ITree,
#                     str,
#                     TypeExpressionType,
#                     Mapping,
#                 }
#             }
#         ):
#             print("Converting input to list of inputs")
#             logger.log(level=LOG_LEVEL, msg="Converting input to list of inputs")
#             _seq = [seq]
#         else:
#             logger.log(level=LOG_LEVEL, msg=type(seq))
#             _seq = seq

#         if is_iterable_of(_seq, ITree):
#             print(f"Iterable of ITree")

#             self.trees = _seq
#         elif is_iterable_of(_seq, str):
#             _parsed = [self._parse(v) for v in _seq]
#             _errors: List[Exception] = []
#             _trees: List[Tree] = []
#             for v in _parsed:
#                 if _e := v[1] is not None:
#                     if isinstance(_e, ErrorWrapper):
#                         _errors.append(_e)
#                     else:
#                         _errors += _e
#                 elif v[0] is None:
#                     # This technically shouldn't happen
#                     raise ValueError(
#                         "Couldn't parse an entry but didn't return an exception either."
#                     )
#                 else:
#                     _trees.append(v[0])

#             if len(_errors) > 0:
#                 print(_errors)
#                 raise ValidationError(errors=_errors, model=Tree)

#             print(f"Iterable of str parsed to {_trees}")
#             if len(_trees) < len(_seq):
#                 raise ValueError(
#                     f"Could not parse all entries of {_seq}. Parsed {_trees}"
#                 )
#             self.trees: List[Tree] = _trees
#         elif is_iterable_of(_seq, TypeExpressionType):
#             print(f"Iterable of TypeExpressionType")
#             self.trees = [
#                 tree_from_typeexpressiontype_or_typeexpression(v) for v in _seq
#             ]

#         else:
#             logger.error(
#                 f"the argument needs to be a list of Tree or str objects. "
#                 f"(was: {list(type(v) for v in _seq or [])})"
#                 f"{_seq}"
#             )
#             print(
#                 f"the argument needs to be a list of Tree or str objects. "
#                 f"(was: {list(type(v) for v in _seq or [])})"
#                 f"{_seq}"
#             )
#             assert False, (
#                 f"the argument needs to be a list of Tree or str objects. ",
#                 f"(was: {list(type(v) for v in _seq or [])})",
#                 f"{_seq}",
#             )
#             raise TypeError(f"the argument needs to be a list of Tree or str objects.")
#             raise StrError

#         assert getattr(
#             self, "trees", False
#         ), f"{_seq} {type(_seq)} {list(type(x) for x in _seq) if isinstance(_seq,Sequence) else type(_seq)}"

#         if len(self.trees) > 1:
#             super().__init__(str(self.trees))
#         elif len(self.trees) == 1:
#             assert self.trees[0]  # Helper for typechecking # bandit:
#             logger.log(
#                 level=LOG_LEVEL, msg=f"Using first tree {self.trees[0].__str__()}"
#             )
#             super().__init__(str(self.trees[0]))
#         else:
#             raise TypeError["no types were defined"]

#     def as_type(self: Self) -> Type:
#         return self.type_.as_type()
#         ...

#     def __eq__(self: Self, other: Self | str) -> bool:
#         return self.type_ == other

#     @classmethod
#     def __get_validators__(cls):
#         # one or more validators may be yielded which will be called in the
#         # order to validate the input, each validator will receive as an input
#         # the value returned from the previous validator
#         def _debug_advanced(cls: Type[Self], values: _ValuesType) -> "ValidateReturn":
#             return debug_advanced(cls=cls, values=values, caller="TypeExpression")

#         yield _debug_advanced
#         yield cls.validator

#     @classmethod
#     def __modify_schema__(cls, field_schema: Dict[str, Any]):
#         # __modify_schema__ should mutate the dict it receives in place,
#         # the returned value will be ignored
#         # field_schema.update(
#         #     # simplified regex here for brevity, see the wikipedia link above
#         #     pattern='^[A-Z]{1,2}[0-9][A-Z0-9]? ?[0-9][A-Z]{2}$',
#         #     # some example postcodes
#         #     examples=['SP11 9DG', 'w1j7bu'],
#         # )
#         field_schema.update({"type": "string"})

#     @classmethod
#     def _parse(cls, v: str) -> "ValidateReturn":
#         _errors: List[ErrorWrapper] = []
#         _parsed: ITree | None = None
#         logger.log(level=LOG_LEVEL, msg=f"Parsing {v}")

#         assert isinstance(v, str)

#         try:
#             _parsed = postfix_to_ast(shunt(input_data=v, ops=OPS))
#         except (ValueError, ValidationError, TypeError) as e:
#             _errors.append(ErrorWrapper(exc=e, loc=(f"{v}@TypeExpression")))
#         return _parsed, _errors if len(_errors) > 0 else None

#     @classmethod
#     def parse_obj(cls, obj: object) -> Self:
#         """Parse an object as a model-like class.

#         Args:
#             obj (object): Object to parse as type

#         Raises:
#             ValidationError: Error containing the location of the sub errors additionally

#         Returns:
#             Self: Instance of the class
#         """
#         # _instance: Self
#         # _errors: List[Exception]
#         # _instance, _errors= cls.validate(obj)
#         # if _errors:
#         #     raise ValidationError(errors = _errors, loc="TypeExpression")

#         return cls.validate(obj)

#     @overload
#     @classmethod
#     def validator(cls, v: str | ITree | TypeName) -> Self:
#         ...

#     @overload
#     @classmethod
#     def validator(cls, v: List[str | ITree | TypeName]) -> Self:
#         ...

#     @classmethod
#     def validator(
#         cls,
#         v: (
#             str | TypeExpression | List[str] | List[ITree] | List[TypeExpression] | Any
#         ),
#     ) -> Self:
#         if isinstance(v, cls):
#             return v

#         if isinstance(v, Mapping):
#             print("MAPPING!")
#             logger.error(MappingNotAllowedError)
#             return None, [ErrorWrapper(exc=MappingNotAllowedError(), loc="TypeName")]

#         _instance: Self
#         _errors: List[Exception] = []

#         try:
#             _instance = cls(v)
#             return _instance, None
#         except TypeError as e:
#             # _errors.append(e)
#             raise e.with_traceback(e.__traceback__)
#             return None, ErrorWrapper(exc=e, loc="TypeExpression")

#         if isinstance(v, str):
#             _tree, __errors = cls._parse(v)
#             _instance = cls(_tree)
#             _errors = __errors
#         elif isinstance(v, TypeExpression):
#             _instance = v
#         elif isinstance(v, List):
#             assert False, f"Plain list {v} {type(v)}"
#         else:
#             raise TypeError(
#                 f"string or TypeExpression or List of str or TypeExpression required. ({v})"
#             )

#         return _instance, _errors

#     def __repr__(self) -> str:
#         return f"TypeExpression({self.type_.__repr__()})"
#         logger.warning(f"Using {str(self.type_)},{type(self.type_)} for __repr__")
#         return f"TypeExpression('{str(self.type_)}')"
#         return f"TypeExpression({super().__repr__()})"

#     def __str__(self) -> str:
#         if not getattr(self, "trees", False):
#             logger.warning("Using type for __str__")
#             return str(self.type_)
#             return "BROKEN"
#         if len(self.trees) > 1:
#             return json.dumps([str(tree) for tree in self.trees])
#         else:
#             logger.warning("Falling back to first tree for __str__")
#             return str(self.trees[0])

# __root__: (
#     InheritanceExpression
#     | TypeName
#     | NestedTypeExpression
#     | ArrayTypeExpression
#     | UnionTypeExpression
#    # | str
# )

# _debug = root_validator(pre=True, allow_reuse=True)(debug)

# @root_validator(pre=True)
# def _print_data(cls, values):
#     print(f"root_validator typeexpression{values}")
#     return values

# def __str__(self) -> str:
#     return str(self.__root__)

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
