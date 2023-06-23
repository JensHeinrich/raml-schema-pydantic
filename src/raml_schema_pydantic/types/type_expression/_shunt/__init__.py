"""Module for shunting yard algorithm."""
import logging

from .algorithm import shunt
from .ast import ITree
from .token_types import _OperatorType
from .token_types import _OperatorType_co
from .token_types import _OperatorType_contra
from .token_types import _TokenType
from .token_types import _TokenType_co
from .token_types import _TokenType_contra
from .token_types import ClosingDelim
from .token_types import DelimPair
from .token_types import OpeningDelim
from .token_types import Operator
from .token_types import Token
from .tokenizer import tokenize_from_generator as tokenize
from .util import check_in
from .util import INode
from .util import OperatorNode
from .util import postfix_to_ast
from .util import ValueNode

logger = logging.getLogger(__name__)


DEFAULT_DELIMS = [
    DelimPair(opening=OpeningDelim("("), closing=ClosingDelim(")")),
]

try:
    import hypothesis  # noqa: ignore[F401]

    from .hypothesis_strategies import _hypothesis_setup_hook

    _hypothesis_setup_hook()
except ImportError:
    logger.debug("The is no hypothesis support on this system.")

__all__ = (
    "_OperatorType_co",
    "_OperatorType_contra",
    "_OperatorType",
    "_TokenType_co",
    "_TokenType_contra",
    "_TokenType",
    "check_in",
    "ClosingDelim",
    "ClosingDelim",
    "DEFAULT_DELIMS",
    "DelimPair",
    "INode",
    "ITree",
    "OpeningDelim",
    "Operator",
    "OperatorNode",
    "postfix_to_ast",
    "shunt",
    "Token",
    "tokenize",
    "ValueNode",
)
