from __future__ import annotations

import logging
from contextlib import suppress
from typing import Any
from typing import cast
from typing import ChainMap
from typing import Generic
from typing import Literal
from typing import Optional
from typing import Sequence
from typing import Type
from typing import TYPE_CHECKING
from typing import TypeVar

from pydantic import BaseModel
from pydantic import Field
from pydantic import StrError
from pydantic import validator
from pydantic.generics import GenericModel

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

    value: _SymbolType = Field(..., alias="symbol")

    @validator("value")
    def _cast_to_token(cls, v: Any) -> None | Token:
        if isinstance(v, Token):
            return v
        if isinstance(v, str):
            return Token(v)
        raise TypeError(f"Unsupported type {type(v)}")

    name: Optional[str] = None
    precedence: int = 0
    unary: Literal[True, False, "both"] = False
    unary_position: Literal["prefix", "postfix", None] = None
    associativity: Literal["left", "right", "none"] = "left"

    @validator("unary_position")
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

    def __repr__(self: Self) -> str:
        """Create the official string representation.

        Returns:
            str: 'official' string representation of the object.
        """
        return f"""Operator(
            value={self.value},
            name={self.name},
            precedence={self.precedence},
            unary={self.unary},
            unary_position={self.unary_position},
            associativity={self.associativity},
        )"""

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
)


if HYPOTHESIS_AVAILABLE:
    from hypothesis import strategies as st

    if TYPE_CHECKING:
        from hypothesis.strategies import SearchStrategy

    non_empty_string_strategy: st.SearchStrategy[str] = st.text(
        st.characters(blacklist_categories=("C", "Z")), min_size=1
    )
    st.register_type_strategy(
        Token,
        st.builds(Token, object=non_empty_string_strategy),
    )

    # The following strategies are based upon the code generated by the `hypothesis.extra.ghostwriter` module
    def operator_strategy_from_symbol_strategy(
        symbol_strategy: SearchStrategy[_SymbolType],
    ) -> SearchStrategy[Operator[_SymbolType]]:
        operator_unary_strategy: SearchStrategy[Operator[_SymbolType]] = st.builds(
            Operator[_SymbolType],
            value=symbol_strategy,
            associativity=st.one_of(
                st.just("left"), st.sampled_from(["none", "right", "left"])
            ),
            name=st.one_of(st.none(), st.one_of(st.none(), st.text())),
            precedence=st.one_of(st.just(0), st.integers()),
            unary=st.one_of(
                st.just(True),  # only unary operators
            ),
            unary_position=st.one_of(
                st.sampled_from(["postfix", "prefix"]),
            ),
        )
        operator_both_strategy: SearchStrategy[Operator[_SymbolType]] = st.builds(
            Operator[_SymbolType],
            value=symbol_strategy,
            associativity=st.one_of(
                st.just("left"), st.sampled_from(["none", "right", "left"])
            ),
            name=st.one_of(st.none(), st.one_of(st.none(), st.text())),
            precedence=st.one_of(st.just(0), st.integers()),
            unary=st.one_of(
                st.just("both"),  # only both operators
            ),
            unary_position=st.one_of(
                st.sampled_from(["postfix", "prefix"]),
            ),
        )
        operator_binary_strategy: SearchStrategy[Operator[_SymbolType]] = st.builds(
            Operator[_SymbolType],
            value=symbol_strategy,
            associativity=st.one_of(
                st.just("left"), st.sampled_from(["none", "right", "left"])
            ),
            name=st.one_of(st.none(), st.one_of(st.none(), st.text())),
            precedence=st.one_of(st.just(0), st.integers()),
            unary=st.one_of(
                st.just(False),  # only binary operators
            ),
            unary_position=st.one_of(st.none()),
        )
        operator_element_strategy: SearchStrategy[Operator[_SymbolType]] = st.one_of(
            operator_unary_strategy,
            operator_binary_strategy,
            operator_both_strategy,
        )
        return operator_element_strategy

    non_empty_token_operator_strategy = operator_strategy_from_symbol_strategy(
        symbol_strategy=st.one_of(
            cast(
                "SearchStrategy[Token]",
                st.builds(Token, object=non_empty_string_strategy),
            )
        )
    )

    st.register_type_strategy(Operator, non_empty_token_operator_strategy)

    def operator_from_symbol_type_strategy(
        symbol_type: Type[_SymbolType],
    ) -> SearchStrategy[Operator[_SymbolType]]:
        symbol_strategy: SearchStrategy[_SymbolType] = st.from_type(symbol_type)
        return operator_strategy_from_symbol_strategy(symbol_strategy=symbol_strategy)

    st.register_type_strategy(
        Operator[Token], operator_from_symbol_type_strategy(Token)
    )

    def operators_strategy_from_symbol_strategy(
        symbol_strategy: SearchStrategy[_SymbolType], min_size: int = 1
    ) -> SearchStrategy[Sequence[Operator[_SymbolType]]]:
        operator_element_strategy = operator_strategy_from_symbol_strategy(
            symbol_strategy=symbol_strategy
        )

        return st.one_of(
            st.lists(
                operator_element_strategy,
                min_size=min_size,
            ),
            st.sets(
                operator_element_strategy,
                min_size=min_size,
            ),
            st.frozensets(
                operator_element_strategy,
                min_size=min_size,
            ),
            st.dictionaries(
                keys=operator_element_strategy,
                values=operator_element_strategy,
                min_size=min_size,
            ),
            st.dictionaries(
                keys=operator_element_strategy,
                values=st.none(),
                min_size=min_size,
            ).map(
                dict.keys  # type: ignore[arg-type]
            ),
            st.dictionaries(
                keys=st.integers(),
                values=operator_element_strategy,
                min_size=min_size,
            ).map(
                dict.values  # type: ignore[arg-type]
            ),
            st.iterables(
                operator_element_strategy,
                min_size=min_size,
            ),
            st.dictionaries(
                keys=operator_element_strategy,
                values=operator_element_strategy,
                min_size=min_size,
            ).map(
                ChainMap  # type: ignore[arg-type]
            ),
        )

    def operators_from_symbol_type_strategy(
        symbol_type: Type[_SymbolType],
    ) -> SearchStrategy[Sequence[Operator[_SymbolType]]]:
        symbol_strategy: SearchStrategy[_SymbolType] = st.from_type(symbol_type)
        return operators_strategy_from_symbol_strategy(symbol_strategy=symbol_strategy)

    def _hypothesis_setup_hook() -> None:  # pyright: ignore[reportUnusedFunction]
        logger.debug("Registering strategies")

        non_empty_string_strategy: st.SearchStrategy[str] = st.text(
            st.characters(blacklist_categories=("C", "Z")), min_size=1
        )
        st.register_type_strategy(
            Token,
            st.builds(Token, non_empty_string_strategy),
        )

        st.register_type_strategy(
            Operator[Token], operator_from_symbol_type_strategy(Token)
        )

    _hypothesis_setup_hook()
