from __future__ import annotations

import logging
from contextlib import suppress
from typing import Any
from typing import Generic
from typing import List
from typing import Literal
from typing import Optional
from typing import TYPE_CHECKING
from typing import TypeVar
from warnings import warn

from pydantic import BaseModel
from pydantic import Field
from pydantic import StrError
from pydantic import validator
from pydantic.generics import GenericModel

from .exceptions import ListLengthError
from .exceptions import NonMatchingPlaceholderCount

HYPOTHESIS_AVAILABLE: bool = False
with suppress(ImportError):
    from hypothesis import strategies  # noqa [F401] # done to check for availability

    HYPOTHESIS_AVAILABLE = True

if TYPE_CHECKING:
    from pydantic.utils import GetterDict
    from typing_extensions import Self


logger = logging.getLogger(__name__)


# isinstance is not supported with NewType
# Token = NewType("Token", str)
# OpeningDelim = NewType("OpeningDelim", Token)
# ClosingDelim = NewType("ClosingDelim", Token)
class Token(str):
    """Custom str type."""

    @classmethod
    def _ensure_str(cls, values: str | Any) -> str:
        if isinstance(values, str):
            return values

        raise StrError(**{"loc": ("Token",)})

    @classmethod
    def _strip_spaces(cls, values: str) -> str:
        _stripped_values: str = values.replace(" ", "")
        return _stripped_values

    @classmethod
    def _ensure_not_empty(cls, values: str) -> str:
        if len(values) > 0:
            return values

        raise ValueError("Empty string not allowed")

    @classmethod
    def __get_validators__(cls):
        """Return a generator of validation functions for use as pydantic model.

        Yields:
            ((values: str | Any) -> str) | ((values: str) -> str): Validation function
        """
        yield cls._ensure_str
        yield cls._strip_spaces
        yield cls._ensure_not_empty

    def __repr__(self) -> str:
        """Create the official string representation.

        Returns:
            str: 'official' string representation of the object.
        """
        return "Token(" + super().__repr__() + ")"


_TokenType = TypeVar("_TokenType", bound=Token)
_TokenType_co = TypeVar("_TokenType_co", bound=Token, covariant=True)
_TokenType_contra = TypeVar("_TokenType_contra", bound=Token, contravariant=True)


class OpeningDelim(Token):
    """Subtype for opening delimiters."""


class ClosingDelim(Token):
    """Subtype for closing delimiters."""


class DelimPair(BaseModel):
    """Pair of delimiters marking a nested expression."""

    opening: OpeningDelim
    closing: ClosingDelim

    if HYPOTHESIS_AVAILABLE:
        # make type hashable for hypothesis
        def __hash__(self) -> int:
            """Create a hash of the object for use in dictionaries.

            Returns:
                int: hash for looking up the object
            """
            return self.opening.__hash__() + self.closing.__hash__()


_SymbolType = TypeVar("_SymbolType", bound=Token)
_SymbolType_contra = TypeVar("_SymbolType_contra", bound=Token, contravariant=True)
_SymbolType_co = TypeVar("_SymbolType_co", bound=Token, covariant=True)

_ValueType = TypeVar("_ValueType", bound=Token)
_ValueType_co = TypeVar("_ValueType_co", bound=Token, covariant=True)
_ValueType_contra = TypeVar("_ValueType_contra", bound=Token, contravariant=True)


class Operator(GenericModel, Generic[_SymbolType]):
    """Operator for grammar expressions."""

    value: _SymbolType = Field(
        default=..., description="Value representing the operator"
    )

    @validator("value")
    def _cast_to_token(cls, v: Any) -> None | Token:
        if isinstance(v, Token):
            return v
        if isinstance(v, str):
            return Token(v)
        raise TypeError(f"Unsupported type {type(v)}")

    name: Optional[str] = None
    precedence: int = 0
    unary: Literal[True, False, "both"]
    unary_position: Literal["prefix", "postfix", None] = None
    associativity: Literal["left", "right", "none"]

    @validator("associativity")
    def _sanity_check_associativity(cls, v, values) -> Literal["left", "right", "none"]:
        if values["unary"] is True and not v == "none":
            raise ValueError("Associativity is only defined for binary operators")
        else:
            warn(
                "Binary values should be associative for ease of use",
                category=UserWarning,
            )
        return v

    @validator("unary_position", always=True)
    def _ensure_position_is_defined(
        cls,
        v: Literal["postfix"] | Literal["prefix"] | str | bool | None | Any,
        values: GetterDict,
    ) -> str | None:
        if "unary" in values and values["unary"] in [True, "both"]:
            if v == "postfix" or v == "prefix":
                # only for typechecking
                assert isinstance(v, str)  # nosec B101
                return v
            raise ValueError(
                "`unary_position` needs to be defined for unary operators."
            )
        else:
            if v is None:
                return v
            raise ValueError(
                "`unary_position` shouldn't be defined for binary operators."
            )

    @validator("unary")
    def _warn_on_both(cls, v: Literal[True, False, "both"]):
        if v == "both":
            warn(
                "This using 'both' is deprecated. Just add the operator multiple times.",
                DeprecationWarning,
                stacklevel=2,
            )
        return v

    def __str__(self) -> str:
        """Create a simple string for the operator."""
        return str(self.value)

    def __repr__(self: Self) -> str:
        """Create the official string representation.

        Returns:
            str: 'official' string representation of the object.
        """
        return (
            "Operator("
            f"""value="{str(self.value)}","""
            f"""name="{str(self.name)}","""
            f"""precedence="{str(self.precedence)}","""
            f"""unary={self.unary},"""
            f"""unary_position="{str(self.unary_position)}","""
            f"""associativity="{str(self.associativity)}","""
            ")"
        )

    if HYPOTHESIS_AVAILABLE:
        # make type hashable for hypothesis
        def __hash__(self) -> int:
            """Create a hash of the object for use in dictionaries.

            Returns:
                int: hash for looking up the object
            """
            return self.value.__hash__()


_OperatorType = TypeVar("_OperatorType", bound=Operator)
_OperatorType_co = TypeVar("_OperatorType_co", bound=Operator, covariant=True)
_OperatorType_contra = TypeVar(
    "_OperatorType_contra", bound=Operator, contravariant=True
)


class RPNToken(BaseModel):
    """Class for tokens used in the reverse polish notation.

    The token has to know it's argument count, so an operator token, which can be used as a unary or a binary operator has to be fixed to one.

    Source:
    - https://github.com/mgenware/go-shunting-yard/blob/master/evaluate.go
    - https://en.wikipedia.org/wiki/Reverse_Polish_notation
    """

    arg_count: int = Field(
        default=..., description="Number of arguments the token takes", required=True
    )

    @validator("arg_count")
    def _check_for_valid_arg_count(cls, v):
        if v >= 0:
            return v
        raise ValueError(
            f"arg_count needs to be an int between 0 and infinity, but was {v}"
        )

    values: List[Token | None] = Field(
        default=..., description="Value to show", required=True
    )

    @validator("values")
    def _check_value_count(cls, v, values):
        _arg_count = values["arg_count"]
        _expected_length = (
            1
            if (_arg_count == 0)
            else 2
            if (_arg_count == 1)
            else (2 * (_arg_count - 1) + 1)
        )  # FIXME define formula without 'if'; 0-> 1, 1 -> 2,  >2 => 2*(_arg_count - 1) +1 : 2->2+1, 3 -> 3+2, 4 -> 4 + 3
        if len(list(filter(lambda x: x is None, v))) == _arg_count and (
            len(v) == _expected_length
        ):
            if (_none_count := len([x for x in v if x is None])) == _arg_count:
                return v
            raise NonMatchingPlaceholderCount(
                actual_count=_none_count, expected_count=_arg_count
            )

        raise ListLengthError(actual_length=len(v), expected_length=_expected_length)

    precedence: int = Field(default=0, required=False)
    associativity: Literal["left", "right", "none"]  # = "none"

    def __str__(self) -> str:
        """Return the generic string representation of the Token.

        Returns:
            str: generic string representation
        """
        _ret: str = ""
        for _v in self.values:
            if _v is not None:
                _ret += _v
        return _ret
        return str(self.values)

    def __hash__(self) -> int:
        """Create a hash of the object for use in dictionaries.

        Returns:
            int: hash for looking up the object
        """
        return self.__repr__().__hash__()

    def __eq__(self, __value: object) -> bool:
        """Compare self to another object.

        Args:
            __value (object): Object to compare to.

        Raises:
            TypeError: Unsupported Type.

        Returns:
            bool: Wether both objects are equal.
        """
        if isinstance(__value, RPNToken):
            return (
                self.arg_count == __value.arg_count
                and self.values == __value.values
                and self.associativity == __value.associativity
            )
        raise TypeError(f"Can only compare RPNToken to RPNToken, not {type(__value)}")


__all__ = (
    "_OperatorType_co",
    "_OperatorType_contra",
    "_OperatorType",
    "_SymbolType_co",
    "_SymbolType_contra",
    "_SymbolType",
    "_TokenType_co",
    "_TokenType_contra",
    "_TokenType",
    "_ValueType_co",
    "_ValueType_contra",
    "_ValueType",
    "ClosingDelim",
    "DelimPair",
    "OpeningDelim",
    "Operator",
    "Token",
    "RPNToken",
)


if HYPOTHESIS_AVAILABLE:
    from .hypothesis_strategies import _hypothesis_setup_hook

    _hypothesis_setup_hook()
