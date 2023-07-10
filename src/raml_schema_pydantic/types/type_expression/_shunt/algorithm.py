"""Implementation of the shunting yard algorithm."""
from typing import cast
from typing import Dict
from typing import Generic
from typing import Iterable
from typing import List
from typing import Sequence
from typing import Set
from typing import TypeVar

from pydantic import Field
from pydantic.generics import GenericModel

from .exceptions import BinaryOrUnaryPostfixOperatorExpected
from .exceptions import CaseNotImplementedException
from .exceptions import NonMatchingDelimitersException
from .exceptions import StartsWithClosingDelimiterException
from .exceptions import StartsWithNonPrefixUnaryOperatorException
from .exceptions import UnaryPrefixOperatorExpected
from .exceptions import UnexpectedValueException
from .exceptions import UnusedTokensException
from .token_types import _OperatorType_co
from .token_types import _SymbolType
from .token_types import ClosingDelim
from .token_types import DelimPair
from .token_types import OpeningDelim
from .token_types import Operator
from .token_types import RPNToken
from .token_types import Token
from .tokenizer import DEFAULT_DELIMS
from .tokenizer import tokenize_from_generator
from .util import check_in
from .util import pop_before


_FunctionType_co = TypeVar("_FunctionType_co", bound=Operator, contravariant=True)


class Sentinel(GenericModel, Generic[_SymbolType]):
    """Sentinel for awaiting another operator."""

    awaits: _SymbolType = Field(default=..., description="Value which is awaited")


def function_to_rpn_token(fun: _FunctionType_co) -> RPNToken:
    """Create an RPNToken from an function.

    Args:
        fun (_FunctionType_co): Function to convert

    Returns:
        RPNToken: Matching RPNToken
    """
    raise


def op_supports_prefix(op: Operator) -> bool:
    """Return wether the operator can be used as a prefix.

    Args:
        op (Operator): operator to check

    Returns:
        bool: wether it can be used as a prefix
    """
    return op.unary and op.unary_position == "prefix"


# def prefix_expected(
#     op: Token,
#     previous: RPNToken,
#     operators: Set[Token],
#     closing_delims: Set[Token],
# ) -> bool:
#     # Both prefix and postfix unary operators can be used.
#     # The way to tell whether you’re in a position to allow prefix or postfix operators is to look at the previous token;
#     # if it’s an operand, you’re looking for binary and postfix unary operators,
#     # and if the previous token is an operator (or there’s no previous token) you’re looking for prefix unary operators.
#     # Note that a left parent counts as an operator and a right paren as an operand for this purpose.
#     # This rule also allows you to tell whether - is a negation (unary) or a subtraction (binary)—
#     # it’s a negation if it appears when looking for a prefix unary operator, and a subtraction otherwise.

#     # Source: https://www.reedbeta.com/blog/the-shunting-yard-algorithm/
#     # Examples:
#     #   ( - A )     -> - is prefix / unary              (Follows paren)
#     #   A ? - B : C -> - is prefix / unary              (Follows non-unary operator)
#     #   A + - B     -> - is prefix / unary              (Follows non-unary operator)
#     #   + - A       -> - is prefix / unary (as is +)    (Follows unary prefix operator)
#     #   A - B       -> - is binary                      (Follows operand)
#     #   A [] - B    -> - is binary                      (Follows unary postfix operator)
#     # Correction: Unary postfix operators behave like operands too

#     # RPNToken example values:
#     #                                                   followed by prefix ?
#     #   ["A"]               ->  value token         ->  False
#     #   ["A", None]         ->  prefix operator     ->  True
#     #   [None, "A"]         ->  postfix operator    ->  False
#     #   [None, "A", None]   ->  binary operator     ->  True
#     #   ["(", None, ")"]
#     #   => If the value is a None value it is expected to be replaced => prefix operators are expected

#     # previous.values[-1] is None
#     # assert previous.unary != "both"
#     return (
#         previous is None
#         or not ((previous.unary and previous.unary_position == "postfix"))
#         or previous in closing_delims
#     )
#     return (
#         True
#         if (
#             previous is None
#             or (
#                 check_in(previous, _operator_dict)
#                 and (
#                     not getattr(
#                         op,  # pyright: ignore[reportUnboundVariable]
#                         "unary",
#                         True,
#                     )
#                 )  # FIXME THIS IS DIRTY!
#             )
#             or check_in(previous, _opening_delim_dict)
#         )
#         else False
#     )


def _sanity_check_operators(
    ops: Sequence[_OperatorType_co],
):
    if intersection := {
        op.value for op in ops if op.unary_position == "postfix"
    }.intersection(op.value for op in ops if op.unary_position != "postfix"):
        raise ValueError(
            f"An operator may not be used as a postfix operator AND either a prefix of a binary operator. {intersection}"
        )


def shunt_tokens(  # noqa: [C901]
    input_data: List[Token],
    ops: Sequence[_OperatorType_co],
    delim_pairs: Iterable[DelimPair] = DEFAULT_DELIMS,
    functions: Iterable[_FunctionType_co] | None = None,
) -> List[RPNToken]:
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
        List[RPNToken]: Postfix notation of the parsed string
    """
    _opening_delim_dict: Dict[OpeningDelim, ClosingDelim] = {
        d.opening: d.closing for d in delim_pairs
    }
    _closing_delim_dict: Dict[ClosingDelim, OpeningDelim] = {
        d.closing: d.opening for d in delim_pairs
    }

    _functions_dict: Dict[Token, _FunctionType_co] = {}

    _sanity_check_operators(ops)

    # new logic
    _operator_tokens: Set[Token] = {op.value for op in ops}
    _unary_postfix_operator_dict: Dict[Token, RPNToken] = {
        op.value: RPNToken(
            arg_count=1,
            values=[None, op.value],
            precedence=op.precedence,
            associativity=op.associativity,
        )
        for op in ops
        if op.unary and op.unary_position == "postfix"
    }
    _unary_prefix_operator_dict: Dict[Token, RPNToken] = {
        op.value: RPNToken(
            arg_count=1,
            values=[op.value, None],
            precedence=op.precedence,
            associativity=op.associativity,
        )
        for op in ops
        if op.unary and op.unary_position == "prefix"
    }
    _non_unary_operator_dict: Dict[Token, RPNToken] = {
        op.value: RPNToken(
            arg_count=2,
            values=[None, op.value, None],
            precedence=op.precedence,
            associativity=op.associativity,
        )
        for op in ops
        if op.unary is not True
    }
    _non_unary_operators: Set[RPNToken] = {
        RPNToken(
            arg_count=2,
            associativity=op.associativity,
            values=[None, op.value, None],
            precedence=op.precedence,
        )
        for op in ops
    }
    _unary_postfix_operators: Set[RPNToken] = {
        RPNToken(
            arg_count=1,
            precedence=op.precedence,
            associativity="none",
            values=[None, op.value],
        )
        for op in ops
        if op.unary_position == "postfix"
    }
    _unary_prefix_operators: Set[RPNToken] = {
        RPNToken(
            arg_count=1,
            precedence=op.precedence,
            associativity="none",
            values=[op.value, None],
        )
        for op in ops
        if op.unary_position == "prefix"
    }

    _closing_delims: Set[Token] = {d.closing for d in delim_pairs}
    _opening_delims: Set[Token] = {d.opening for d in delim_pairs}

    _output_queue: List[RPNToken] = []
    _op_rpn_stack: List[RPNToken | Sentinel[Token]] = []
    _token: Token
    _previous: RPNToken | None = None
    _rpn_token: RPNToken | None = None
    _data = input_data

    while len(_data) > 0:
        # algorithm based on https://en.wikipedia.org/wiki/Shunting_yard_algorithm
        # unary / both handling logic from https://www.reedbeta.com/blog/the-shunting-yard-algorithm/
        _token, _data = _data[0], _data[1:]

        if _token is None:  # this would be the number case
            raise CaseNotImplementedException
            _output_queue.append(_token)
        elif check_in(_token, _functions_dict):  # _token in _functions_dict
            _rpn_token = function_to_rpn_token(_functions_dict[_token])
            _op_rpn_stack.append(_rpn_token)
        elif (
            _token in _operator_tokens
        ):  # check_in(_token, _operator_dict):  # _token in _operator_dict:
            # Both prefix and postfix unary operators can be used.
            # The way to tell whether you’re in a position to allow prefix or postfix operators is to look at the previous token;
            # if it’s an operand, you’re looking for binary and postfix unary operators,
            # and if the previous token is an operator (or there’s no previous token) you’re looking for prefix unary operators.
            # Note that a left parent counts as an operator and a right paren as an operand for this purpose.
            # This rule also allows you to tell whether - is a negation (unary) or a subtraction (binary)—
            # it’s a negation if it appears when looking for a prefix unary operator, and a subtraction otherwise.

            # Source: https://www.reedbeta.com/blog/the-shunting-yard-algorithm/
            # Examples:
            #                                                                                           previous in:    operators   unary_prefix    unary_postfix   opening_delim   closing_delim   |   prefix_expected
            #   ( - A )     -> - is prefix / unary              (Follows opening paren)                                 False       False           False           True            False           |   True
            #   A ? - B : C -> - is prefix / unary              (Follows non-unary operator)                            True        False           False           False           False           |   True
            #   A + - B     -> - is prefix / unary              (Follows non-unary operator)                            True        False           False           False           False           |   True
            #   + - A       -> - is prefix / unary (as is +)    (Follows unary prefix operator)                         True        True            False           False           False           |   True
            #   ( A ) - B   -> - is binary                      (Follows closing paren)                                 False       False           False           False           True            |   False
            #   A - B       -> - is binary                      (Follows operand)                                       False       False           False           False           False           |   False
            #   A [] - B    -> - is binary                      (Follows unary postfix operator)                        True        False           True            False           False           |   False
            # Correction: Unary postfix operators behave like operands too

            _prefix_unary: bool
            if (
                _previous is None
                or _previous in _opening_delims
                or _previous in _unary_prefix_operators
                or _previous in _non_unary_operators
            ):
                _prefix_unary = True
            elif (
                _previous not in _operator_tokens
                or _previous in _closing_delims
                or _previous in _unary_postfix_operators
                or _previous.values[0] == Token("SENTINEL")
            ):
                _prefix_unary = False
            else:
                raise ValueError(f"Could not handle {_token} after {_previous}")

            if _prefix_unary:
                try:
                    _rpn_token = _unary_prefix_operator_dict[_token]
                except KeyError:
                    raise UnaryPrefixOperatorExpected(token=_token)

            else:  # not _prefix_unary
                try:
                    _rpn_token = _unary_postfix_operator_dict[_token]
                    # if _previous is not None and _previous.values[0] == Token("SENTINEL"):
                    #     _output_queue.append(_rpn_token)
                    #     break

                except KeyError:
                    try:
                        _rpn_token = _non_unary_operator_dict[_token]
                    except KeyError:
                        raise BinaryOrUnaryPostfixOperatorExpected(token=_token)

                # TODO evaluate if this is still needed
                if len(_output_queue) == 0:
                    raise StartsWithNonPrefixUnaryOperatorException(
                        input_data=" ".join(input_data), op=_rpn_token
                    )

            while (
                len(_op_rpn_stack) > 0
                and isinstance(_op_rpn_stack[-1], RPNToken)
                and pop_before(
                    _op_rpn_stack[-1],
                    _rpn_token,
                )
            ):
                _popped = _op_rpn_stack.pop()
                assert not isinstance(_popped, Sentinel)  # nosec: ignore=[B101]
                _output_queue.append(_popped)

            _op_rpn_stack.append(_rpn_token)

        elif check_in(_token, _opening_delim_dict):  # _token in _opening_delim_dict:
            _op_rpn_stack.append(Sentinel[Token](awaits=_opening_delim_dict[_token]))
        elif check_in(_token, _closing_delim_dict):  # _token in _closing_delim_dict:
            if len(_output_queue) == 0:
                raise StartsWithClosingDelimiterException(
                    input_data="".join(input_data), delim=_token
                )

            while not isinstance(_op_rpn_stack[-1], Sentinel):
                _rpn_token = cast("RPNToken", _op_rpn_stack.pop())
                _output_queue.append(_rpn_token)
            _sentinel: Sentinel[Token] = cast("Sentinel[Token]", _op_rpn_stack.pop())
            if not (_sentinel.awaits == _token):
                raise NonMatchingDelimitersException from ValueError(
                    f"Invalid input {input_data}: Awaited {_sentinel.awaits} but got {_token}."
                )
            _rpn_token = RPNToken(
                arg_count=0,
                values=[Token("SENTINEL")],
                precedence=0,
                associativity="none",
            )

        elif isinstance(_token, Token):
            # A unknown string will be "basic" token for our use case
            _rpn_token = RPNToken(values=[_token], arg_count=0, associativity="none")
            _output_queue.append(_rpn_token)
        else:
            raise UnexpectedValueException from ValueError(
                f"Got {_token} of type {type(_token)}"
            )
        _previous = _rpn_token

    while len(_op_rpn_stack) > 0:
        _rpn_tail = _op_rpn_stack.pop()
        if isinstance(_rpn_tail, Sentinel):
            raise UnusedTokensException from ValueError(f"Awaited {_rpn_tail.awaits}")
        else:
            _output_queue.append(_rpn_tail)

    if not len(_output_queue) == (
        expected_length := len(
            [x for x in input_data if x not in _closing_delims | _opening_delims]
        )
    ):
        raise ValueError(
            f"There was an error processing {input_data}. Expected {expected_length} tokens, but got {_output_queue}"
        )
    return _output_queue


def shunt(
    input_data: str,
    ops: Sequence[_OperatorType_co],
    delim_pairs: Iterable[DelimPair] = DEFAULT_DELIMS,
) -> List[RPNToken]:
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
        List[RPNToken]: Postfix notation of the parsed string
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
