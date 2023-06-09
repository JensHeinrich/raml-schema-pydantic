from __future__ import annotations

import logging
from collections import UserString
from sys import version_info
from typing import Any
from typing import Dict
from typing import NoReturn
from typing import Optional
from typing import overload
from typing import Sequence
from typing import Tuple
from typing import Type
from typing import TYPE_CHECKING

from pydantic import errors as PydanticErrors
from pydantic import root_validator
from pydantic import StrError
from pydantic.error_wrappers import ErrorWrapper
from pydantic.fields import ModelField
from typing_extensions import override

from ..._errors import ValidationError
from ..._helpers import _ValuesType
from .._type_dict import lookup_type_declaration
from .._TypeDeclarationProtocol import TypeDeclarationProtocol
from ._shunt import Token
from ._shunt import ValueNode
from ._util import *

# from ..types.type_declaration import TypeDeclaration
# from ._base_type_expression_type import BaseTypeExpressionType

# prevent no-redef type errors, see https://github.com/python/mypy/issues/1153#issuecomment-1207333806
if TYPE_CHECKING:
    import regex as re
    from regex import Pattern

    from typing_extensions import Self

    # from ..types.type_declaration import ITypeDeclaration
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


# A TypeName is the non-operator token for a TypeExpression
class TypeName(
    # ValueNode[Token],
    Token,
    TypeDeclarationProtocol,
    # IType,
    # BaseTypeExpressionType,
    # UserString
):
    """A type name, the basic building block of a type expression, used alone creates the simplest expression.

    Examples:
        `number:` a built-in type<br><br>
        `Person:` a custom type
    """

    # def __init__(self, value: Token | str | Any, *args, **kwargs) -> None:
    #     if isinstance(value, Token):
    #         super().__init__(value=value)
    #     elif isinstance(value, str):
    #         super().__init__(value=Token(value))
    #     else:
    #         raise StrError(msg_template=f"seq expected to be str was {type(value)}")

    @classmethod
    def parse_obj(cls: Type[Self], obj: Any) -> Self:
        return cls(obj)

    # @root_validator(pre=True)
    # def pass_str_as_value(cls, values):
    #     if isinstance(values, str):
    #         return {"value": values}
    #     logger.info(f"Non string value {values}")
    #     return values

    # TODO Check definition of allowed type names
    _regex: Pattern[str] = re.compile(r"^\s*(?P<typename>[\w-]*)\s*$")

    @overload
    @classmethod
    def validator(
        cls, v: Self, field: Optional[ModelField] = None
    ) -> Tuple[Self, None]:
        ...

    @overload
    @classmethod
    def validator(
        cls, v: str, field: Optional[ModelField] = None
    ) -> Tuple[Self, None] | Tuple[None, "ErrorList"]:
        ...

    @overload
    @classmethod
    def validator(
        cls, v: Any, field: Optional[ModelField] = None
    ) -> Tuple[Self, None] | Tuple[None, "ErrorList"]:
        ...

    @classmethod
    def validator(cls, v: Any, field: Optional[ModelField] = None) -> "ValidateReturn":
        if isinstance(v, TypeName):
            return v, None

        if isinstance(v, str):
            _match = cls._regex.fullmatch(v)

            if _match is None or not "typename" in _match.groupdict():
                return None, [
                    ErrorWrapper(
                        exc=PydanticErrors.StrRegexError(pattern=cls._regex.pattern),
                        loc="TypeName",
                    )
                ]
            return TypeName(_match.groupdict()["typename"]), None

        return None, [
            ErrorWrapper(
                exc=TypeError("TypeName not validated"),
                loc="TypeName",
            )
        ]

    @classmethod
    def validate(cls, v: Any) -> Self:
        _instance, _errors = cls.validator(v)
        if _errors:
            raise ValidationError(errors=_errors, model=cls)
        return _instance

    @classmethod
    def __get_validators__(cls):
        """Return a generator of validation functions for use as pydantic model.

        Yields:
            ((values: str | Any) -> str) | ((values: str) -> str): Validation function
        """
        yield from super().__get_validators__()
        yield cls.validate

    # def as_declaration(self) -> "ITypeDeclaration":
    #     """Return the type declaration identified by this name.

    #     Returns:
    #         ITypeDeclaration: TypeDeclaration for the name
    #     """
    #     try:
    #         return lookup_type_declaration(self.value)
    #     except KeyError:
    #         return lookup_type_declaration(self)

    # @property
    # def _properties(self: Self) -> Sequence[str]:
    #     return self.as_declaration()._properties

    # @property
    # def _facets(self: Self) -> Sequence[str]:
    #     return self.as_declaration()._facets

    # def as_type(self) -> Type:
    #     """Return the type by looking up its declaration in the global type dict.

    #     Returns:
    #         Type: Type for the name
    #     """
    #     return self.as_declaration().as_type()

    @root_validator
    def _register_type(cls, values: _ValuesType) -> _ValuesType:
        return values

    def __repr__(self) -> str:
        return f"TypeName('{super().__str__()}')"

    # def __str__(self) -> str:
    #     return super(ValueNode, self).__str__()

    @overload
    def __eq__(self, other: Self) -> bool:
        ...

    @overload
    def __eq__(self, other: str) -> bool:
        ...

    @overload
    def __eq__(self, other: Any) -> bool | NoReturn:
        ...

    def __eq__(self, other: str | Self) -> bool | NoReturn:
        if isinstance(other, type(self)):
            return self.__str__() == other.__str__()
        if isinstance(other, str):
            return self.__str__() == other
        raise TypeError(
            f"Comparison only supported for `{type(self)}` and `str`",
        )

    def __hash__(self: Self) -> int:
        """Create a hash of the object for use in dictionaries.

        Returns:
            int: hash for looking up the object
        """
        return str(self).__hash__()

    @override
    def schema(self, by_alias: bool = ..., ref_template: str = ...) -> Dict[str, Any]:  # type: ignore[assignment,override]
        return lookup_type_declaration(self.__str__()).schema()

    @classmethod
    def __modify_schema__(cls, field_schema: dict[str, Any], field: ModelField | None):
        field_schema["type"] = "string"
        # if field:
        #     alphabet = field.field_info.extra['alphabet']
        #     field_schema['examples'] = [c * 3 for c in alphabet]
