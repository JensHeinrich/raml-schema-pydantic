"""Module for shunting yard algorithm."""
from __future__ import annotations

import logging
import re
from contextlib import suppress
from typing import cast
from typing import Dict
from typing import Generator
from typing import Iterable
from typing import List
from typing import Sequence
from typing import Set
from typing import TypeVar

from .ast import ITree as ITree
from .token_types import ClosingDelim as ClosingDelim
from .token_types import DelimPair as DelimPair
from .token_types import OpeningDelim as OpeningDelim
from .token_types import Operator as Operator
from .token_types import Token as Token
from .util import check_in
from .util import INode as INode
from .util import OperatorNode as OperatorNode
from .util import postfix_to_ast as postfix_to_ast
from .util import ValueNode as ValueNode

__all__ = (
    "ClosingDelim",
    "DelimPair",
    "INode",
    "ITree",
    "OpeningDelim",
    "Operator",
    "OperatorNode",
    "postfix_to_ast",
    "Token",
    "ValueNode",
)

logger = logging.getLogger(__name__)


DEFAULT_DELIMS = [
    DelimPair(opening=OpeningDelim("("), closing=ClosingDelim(")")),
]

_TokenType = TypeVar("_TokenType", bound=str)


def any_starts_with(
    candidates: Iterable[str],
    prefix: str,
) -> bool:
    """Evaluate wether any of the candidates starts with the provided prefix.

    Args:
        candidates (Iterable[str]): Iterable of candidates to evaluate
        prefix (str): prefix to check for

    Returns:
        bool: any candidate starts with the prefix
    """
    return any(t.startswith(prefix) for t in candidates)


def get_longest_match(
    candidates: Iterable[str],
    input_string: str,
) -> str:
    """Get the longest part of the input_string which is still a valid candidate.

    Args:
        candidates (Iterable[str]): Iterable of candidates to evaluate
        input_string (str): string to find the longest match for

    Raises:
        ValueError: Exception if no match can be found

    Returns:
        str: longest matching prefix
    """
    for i in range(
        min(  # only iterate through the possible values
            max([len(t) for t in candidates]),  # maximum candidate length
            len(input_string),  #
        )
        - 1,  # index starts at 0
        0,
        -1,  # decrease index
    ):
        if (matched := input_string[: i + 1]) in candidates:
            return matched
    raise ValueError("No match found!")


def yield_longest_match(
    input_data: str, symbols: Iterable[_TokenType]
) -> Generator[_TokenType, None, None]:
    """Yield longest matching sequences.

    String sequences are assumed to be separated by tokens and the longest matching tokens are preferred.

    Args:
        input_data (str): String to yield from.
        symbols (Iterable[_TokenType]): Known tokens.

    Raises:
        StopIteration: Exception for an exhausted generator.

    Yields:
        Generator[_TokenType, None, None]: Generator yielding the matching sequences.
    """
    _sorted_symbols: List[_TokenType] = sorted(symbols, key=len, reverse=True)
    _input_data: str = input_data
    _current: str | None = None

    while len(_input_data) > 0:
        for token in _sorted_symbols:
            if _input_data.startswith(token):
                if _current is not None:
                    yield cast("_TokenType", _current)
                yield token
                _input_data = _input_data.removeprefix(token)
                _current = None
                break
        else:  # Nothing found
            _current, _input_data = (
                ("" if _current is None else _current) + _input_data[:1],
                _input_data[1:],
            )
    if _current is not None:
        yield cast("_TokenType", _current)
    raise StopIteration()


def tokenize_from_generator(
    input_data: str,
    ops: Iterable[Operator],
    delim_pairs: Iterable[DelimPair] = DEFAULT_DELIMS,
) -> List[Token]:
    """Create a list of tokens from a string splitting on operators and delimiters.

    Args:
        input_data (str): String to split.
        ops (Iterable[Operator]): Supported operators.
        delim_pairs (Iterable[DelimPair], optional): Supported delimiters. Defaults to DEFAULT_DELIMS.

    Returns:
        List[Token]: _description_
    """
    input_data = input_data.replace(" ", "")
    return [
        Token(token)
        for token in yield_longest_match(
            input_data=input_data,
            symbols={delim.opening for delim in delim_pairs}
            | {delim.closing for delim in delim_pairs}
            | {op.value for op in ops},
        )
    ]


def tokenize(  # noqa: [C901]
    input_data: str,
    ops: Sequence[Operator],
    delim_pairs: Iterable[DelimPair] = DEFAULT_DELIMS,
) -> List[Token]:
    _opening_delims: Set[Token] = {delim.opening for delim in delim_pairs}
    _closing_delims: Set[Token] = {delim.closing for delim in delim_pairs}
    _operator_symbols: Set[Token] = {op.value for op in ops}

    _multi_letter_tokens: Set[Token] = {
        t for t in _opening_delims | _closing_delims | _operator_symbols if len(t) > 1
    }

    _tokens: List[Token] = []

    _data: str = re.sub(r"\s", "", input_data)
    if _data != input_data:
        logger.warning("Removed spaces")

    _current: str = ""
    _next: str
    while len(_data) > 0:
        _next, _data = _data[0], _data[1:]

        if _next in _operator_symbols | _opening_delims | _closing_delims:
            if _current != "":
                # flush current token
                _tokens.append(Token(_current))
                _current = ""
            # flush op-like
            _tokens.append(Token(_next))
        else:
            if any_starts_with(_multi_letter_tokens, _next):
                _match: str = ""
                with suppress(ValueError):
                    _match = get_longest_match(_multi_letter_tokens, _next + _data)
                    if _match != "":
                        _data = _data.removeprefix(_match[1:])
                        if _current != "":
                            # flush current token
                            _tokens.append(Token(_current))
                            _current = ""
                        # flush op-like
                        _tokens.append(Token(_match))
                        continue

            else:
                _current += _next

    if _current != "":
        _tokens.append(Token(_current))

    return _tokens


NonMatchingDelimitersException = ValueError("The delimiters need to be matched.")
UnexpectedValueException = ValueError("Unexpected value")
UnusedTokensException = ValueError("Unused tokens")


def shunt(  # noqa: [C901]
    input_data: str,
    ops: Sequence[Operator],
    delim_pairs: Iterable[DelimPair] = DEFAULT_DELIMS,
) -> List[Token | Operator]:
    """Parse a string into postfix notation by the shunting yard algorithm.

    Args:
        input_data (str): expression to parse into postfix notation
        ops (Sequence[Operator]): Operators of the expression
        delim_pairs (Iterable[DelimPair], optional): delimiters for nested expressions. Defaults to DEFAULT_DELIMS.

    Raises:
        NotImplementedError: _description_
        NotImplementedError: _description_
        TypeError: _description_
        TypeError: _description_
        ValueError: _description_
        ValueError: _description_
        ValueError: _description_

    Returns:
        List[Token | Operator]: _description_
    """
    _opening_delim_dict: Dict[OpeningDelim, ClosingDelim] = {
        d.opening: d.closing for d in delim_pairs
    }
    _closing_delim_dict: Dict[ClosingDelim, OpeningDelim] = {
        d.closing: d.opening for d in delim_pairs
    }
    _operator_dict: Dict[Token, Operator] = {Token(op.value): op for op in ops}

    _output_stack: List[Token | Operator] = []
    _op_stack: List[Operator | OpeningDelim] = []

    _data: List[Token] = tokenize(
        input_data=input_data,
        ops=ops,
        delim_pairs=delim_pairs,
    )

    _next: Token
    _op: Operator

    while _data:
        # algorithm based on https://en.wikipedia.org/wiki/Shunting_yard_algorithm
        _next, _data = _data[0], _data[1:]
        if _next is None:  # this would be the number case
            raise NotImplementedError(
                "This is not implemented and should never happen!"
            )
        elif _next is None:  # this would be the function case
            raise NotImplementedError(
                "This is not implemented and should never happen!"
            )
        elif check_in(_next, _operator_dict):  # _next in _operator_dict:
            if _output_stack == []:
                raise TypeError(
                    f"Input sequence {input_data} may not start with operator {_next}."
                )
            _op = _operator_dict[_next]
            while (
                _op_stack
                and isinstance(_op_stack[-1], Operator)
                and (
                    _op_stack[-1].precedence > _op.precedence
                    or (
                        _op_stack[-1].precedence == _op.precedence
                        and _op.associativity == "left"
                    )
                )
            ):
                _output_stack.append(_op_stack.pop())
            _op_stack.append(_op)
        elif check_in(_next, _opening_delim_dict):  # _next in _opening_delim_dict:
            _op_stack.append(_next)
        elif check_in(_next, _closing_delim_dict):  # _next in _closing_delim_dict:
            if _output_stack == []:
                raise TypeError(
                    f"Input sequence {input_data} may not start with closing delimiter {_next}."
                )
            _awaited_delim: str = _closing_delim_dict[_next]
            while isinstance(_op_stack[-1], Operator):
                _output_stack.append(_op_stack.pop())
            if (_opening_delim := _op_stack.pop()) != _awaited_delim:
                raise NonMatchingDelimitersException from ValueError(
                    f"Invalid input {input_data}: {_opening_delim} was closed by {_next}."
                )
        elif isinstance(_next, Token):
            # A unknown string will be "basic" token for our use case
            _output_stack.append(_next)
        else:
            raise UnexpectedValueException from ValueError(
                f"Got {_next} of type {type(_next)}"
            )

    while _op_stack:
        _tail = _op_stack.pop()
        if isinstance(_tail, Operator):
            _output_stack.append(_tail)
        else:  # elif _check_in(_tail, _op_stack):  # _tail in _opening_delim_dict:
            raise UnusedTokensException from ValueError(
                f"Op stack still contains the following elements: {_tail}"
            )

    return _output_stack
