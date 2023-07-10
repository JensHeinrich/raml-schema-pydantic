"""Custom exceptions."""
from typing import TYPE_CHECKING

from pydantic import PydanticValueError


if TYPE_CHECKING:
    from .token_types import ClosingDelim
    from .token_types import RPNToken, Token


class NonMatchingDelimitersException(ValueError):
    """Exception for a delimiter closed by an unexpected delimiter."""

    msg = "The delimiters need to be matched."


class NonMatchingPlaceholderCount(PydanticValueError):
    """Exception for a mismatch between the expected and the provided number of placeholders."""

    msg_template = "wrong placeholder count {actual_count}, expected {expected_count}"

    def __init__(self, *, actual_count: int, expected_count: int) -> None:
        """Initialize exception.

        Args:
            actual_count (int): Expected number of placeholders.
            expected_count (int): Provided number of placeholders.
        """
        super().__init__(actual_count=actual_count, expected_count=expected_count)


# TODO Replace all those lists with tuples
class ListLengthError(PydanticValueError):
    """Exception for a list of unexpected length."""

    code = "list.length"
    msg_template = "wrong list length {actual_length}, expected {expected_length}"

    def __init__(self, *, actual_length: int, expected_length: int) -> None:
        """Initialize exception.

        Args:
            actual_length (int): Length of the provided list.
            expected_length (int): Expected length of the list.
        """
        super().__init__(actual_length=actual_length, expected_length=expected_length)


UnexpectedValueException = ValueError("Unexpected value")
UnusedTokensException = ValueError("Unused tokens")
CaseNotImplementedException = NotImplementedError(
    "This is not implemented and should never happen!"
)


class InvalidTokenException(TypeError):
    """Exception for invalid tokens in data."""

    pass


class UnaryPrefixOperatorExpected(InvalidTokenException):
    """Exception for wrong operator type."""

    def __init__(self, token: "Token"):
        """Initialize exception.

        Args:
            input_data (str): string being parsed.
            op (Token): invalid operator.
        """
        super().__init__(
            f"Expected an unary prefix operator. but got unary postfix or binary operator {token}."
        )


class BinaryOrUnaryPostfixOperatorExpected(InvalidTokenException):
    """Exception for wrong operator type."""

    def __init__(self, token: "Token"):
        """Initialize exception.

        Args:
            input_data (str): string being parsed.
            op (Token): invalid operator.
        """
        super().__init__(
            f"Expected an unary postfix or an binary operator, but got unary prefix operator {token}."
        )


class StartsWithNonPrefixUnaryOperatorException(InvalidTokenException):
    """Exception for data starting with a unary postfix operator."""

    def __init__(self, input_data: str, op: "RPNToken"):
        """Initialize exception.

        Args:
            input_data (str): string being parsed.
            op (Operator): invalid operator.
        """
        super().__init__(
            f"Input sequence {input_data} may not start with operator {op}."
        )


class StartsWithClosingDelimiterException(InvalidTokenException):
    """Exception for data starting with a closing delimiter."""

    def __init__(self, input_data: str, delim: "ClosingDelim"):
        """Initialize exception.

        Args:
            input_data (str): string being parsed.
            op (Operator): invalid delimiter.
        """
        super().__init__(
            f"Input sequence {input_data} may not start with closing delimiter {delim}."
        )


__all__ = (
    "BinaryOrUnaryPostfixOperatorExpected",
    "CaseNotImplementedException",
    "ListLengthError",
    "NonMatchingDelimitersException",
    "NonMatchingPlaceholderCount",
    "StartsWithClosingDelimiterException",
    "StartsWithNonPrefixUnaryOperatorException",
    "UnaryPrefixOperatorExpected",
    "UnexpectedValueException",
    "UnusedTokensException",
)
