"""Tokenizer functions."""
import logging
import re
from typing import cast
from typing import Generator
from typing import Iterable
from typing import List
from typing import TypeVar

from .token_types import _TokenType_co
from .token_types import ClosingDelim
from .token_types import DelimPair
from .token_types import OpeningDelim
from .token_types import Operator
from .token_types import Token


logger = logging.getLogger(__name__)


DEFAULT_DELIMS = [
    DelimPair(opening=OpeningDelim("("), closing=ClosingDelim(")")),
]
WHITESPACE_REGEXP = re.compile(r"\s")

_StrType_co = TypeVar("_StrType_co", bound=str, covariant=True)


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
    candidates: Iterable[_StrType_co],
    input_string: str,
) -> _StrType_co:
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
        if (matched := cast("_StrType_co", input_string[: i + 1])) in candidates:
            return matched
    raise ValueError("No match found!")


def yield_longest_match(
    input_data: str, symbols: Iterable[_TokenType_co]
) -> Generator[Token, None, None]:
    """Yield longest matching sequences.

    String sequences are assumed to be separated by tokens and the longest matching tokens are preferred.

    Args:
        input_data (str): String to yield from.
        symbols (Iterable[_TokenType_co]): Known tokens.

    Raises:
        StopIteration: Exception for an exhausted generator.

    Yields:
        Generator[_TokenType_co | Token, None, None]: Generator yielding the matching sequences.
    """
    _sorted_symbols: List[_TokenType_co] = sorted(symbols, key=len, reverse=True)
    _input_data: str = input_data
    _current: str | None = None

    while len(_input_data) > 0:
        for token in _sorted_symbols:
            if _input_data.startswith(token):
                if _current is not None:
                    yield Token(_current)
                yield token
                _input_data = _input_data.removeprefix(token)
                _current = None
                break
        else:  # Nothing found
            _current, _input_data = (
                f"{ '' if _current is None else _current }{ _input_data[:1] }",
                _input_data[1:],
            )
    if _current is not None:
        yield Token(_current)
    # Exhausted generators should just return
    # Sources:
    #   - https://stackoverflow.com/questions/31719068/how-to-handle-an-exhausted-iterator
    #   - https://peps.python.org/pep-0479/
    return


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
        List[Token]: List of recognized tokens.
    """
    # TODO: Evaluate if this really should be done
    input_data = re.sub(WHITESPACE_REGEXP, "", input_data)
    return [
        Token(token)
        for token in yield_longest_match(
            input_data=input_data,
            symbols={delim.opening for delim in delim_pairs}
            | {delim.closing for delim in delim_pairs}
            | {op.value for op in ops},
        )
    ]


__all__ = (
    "any_starts_with",
    "yield_longest_match",
    "get_longest_match",
    "tokenize_from_generator",
)
