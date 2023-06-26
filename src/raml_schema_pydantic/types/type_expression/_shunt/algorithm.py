"""Implementation of the shunting yard algorithm."""
from typing import Dict
from typing import Iterable
from typing import List
from typing import Sequence

from .exceptions import CaseNotImplementedException
from .exceptions import NonMatchingDelimitersException
from .exceptions import StartsWithClosingDelimiterException
from .exceptions import StartsWithNonPrefixUnaryOperatorException
from .exceptions import UnexpectedValueException
from .exceptions import UnusedTokensException
from .token_types import _OperatorType_co
from .token_types import ClosingDelim
from .token_types import DelimPair
from .token_types import OpeningDelim
from .token_types import Operator
from .token_types import Token
from .tokenizer import DEFAULT_DELIMS
from .tokenizer import tokenize_from_generator
from .util import check_in


def shunt_tokens(  # noqa: [C901]
    input_data: List[Token],
    ops: Sequence[_OperatorType_co],
    delim_pairs: Iterable[DelimPair] = DEFAULT_DELIMS,
) -> List[Token | _OperatorType_co]:
    """Parse a list of tokens into postfix notation by the shunting yard algorithm.

    Args:
        input_data (str): expression to parse into postfix notation
        ops (Sequence[Operator]): Operators of the expression
        delim_pairs (Iterable[DelimPair], optional): delimiters for nested expressions. Defaults to DEFAULT_DELIMS.

    Raises:
        CaseNotImplementedException: Exception for placeholder cases
        StartsWithNonPrefixUnaryOperatorException: Exception for data starting with a unary postfix operator
        StartsWithClosingDelimiterException: Exception for data starting with a closing delimiter
        NonMatchingDelimitersException: Exception for data containing delimiters which have not been matched pairwise
        UnexpectedValueException: _description_
        UnusedTokensException: Exception for not exhausting the operator stack

    Returns:
        List[Token | Operator]: Postfix notation of the parsed string
    """
    _opening_delim_dict: Dict[OpeningDelim, ClosingDelim] = {
        d.opening: d.closing for d in delim_pairs
    }
    _closing_delim_dict: Dict[ClosingDelim, OpeningDelim] = {
        d.closing: d.opening for d in delim_pairs
    }
    _operator_dict: Dict[Token, _OperatorType_co] = {Token(op.value): op for op in ops}

    _output_stack: List[Token | _OperatorType_co] = []
    _op_stack: List[_OperatorType_co | OpeningDelim] = []

    _next: Token
    _op: _OperatorType_co
    _data = input_data

    while len(_data) > 0:
        # algorithm based on https://en.wikipedia.org/wiki/Shunting_yard_algorithm
        _next, _data = _data[0], _data[1:]
        if _next is None:  # this would be the number case
            raise CaseNotImplementedException
        elif _next is None:  # this would be the function case
            raise CaseNotImplementedException
        elif check_in(_next, _operator_dict):  # _next in _operator_dict:
            _op = _operator_dict[_next]
            if _output_stack == [] and not (
                _op.unary and _op.unary_position == "prefix"
            ):
                raise StartsWithNonPrefixUnaryOperatorException(
                    input_data=" ".join(input_data), op=_op
                )
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
                raise StartsWithClosingDelimiterException(
                    input_data="".join(input_data), delim=_next
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
        if not isinstance(_tail, OpeningDelim):
            _output_stack.append(_tail)
        else:  # elif _check_in(_tail, _op_stack):  # _tail in _opening_delim_dict:
            raise UnusedTokensException from ValueError(
                f"Op stack still contains the following elements: {_tail}"
            )

    return _output_stack


def shunt(
    input_data: str,
    ops: Sequence[_OperatorType_co],
    delim_pairs: Iterable[DelimPair] = DEFAULT_DELIMS,
) -> List[Token | _OperatorType_co]:
    """Parse a string into postfix notation by the shunting yard algorithm.

    Args:
        input_data (str): expression to parse into postfix notation
        ops (Sequence[Operator]): Operators of the expression
        delim_pairs (Iterable[DelimPair], optional): delimiters for nested expressions. Defaults to DEFAULT_DELIMS.

    Raises:
        CaseNotImplementedException: Exception for placeholder cases
        StartsWithNonPrefixUnaryOperatorException: Exception for data starting with a unary postfix operator
        StartsWithClosingDelimiterException: Exception for data starting with a closing delimiter
        NonMatchingDelimitersException: Exception for data containing delimiters which have not been matched pairwise
        UnexpectedValueException: _description_
        UnusedTokensException: Exception for not exhausting the operator stack

    Returns:
        List[Token | Operator]: Postfix notation of the parsed string
    """
    _data: List[Token] = tokenize_from_generator(
        input_data=input_data,
        predefined_tokens=(
            {delim.opening for delim in delim_pairs}
            | {delim.closing for delim in delim_pairs}
            | {op.value for op in ops}
        ),
    )

    return shunt_tokens(input_data=_data, ops=ops, delim_pairs=delim_pairs)
