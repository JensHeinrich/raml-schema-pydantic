"""Custom exceptions."""
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from .token_types import ClosingDelim
    from .token_types import Operator

NonMatchingDelimitersException = ValueError("The delimiters need to be matched.")
UnexpectedValueException = ValueError("Unexpected value")
UnusedTokensException = ValueError("Unused tokens")
CaseNotImplementedException = NotImplementedError(
    "This is not implemented and should never happen!"
)


class InvalidTokenException(TypeError):
    """Exception for invalid tokens in data."""

    pass


class StartsWithNonPrefixUnaryOperatorException(InvalidTokenException):
    """Exception for data starting with a unary postfix operator."""

    def __init__(self, input_data: str, op: "Operator"):
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
    "NonMatchingDelimitersException",
    "UnexpectedValueException",
    "UnusedTokensException",
    "CaseNotImplementedException",
    "StartsWithNonPrefixUnaryOperatorException",
    "StartsWithClosingDelimiterException",
)
