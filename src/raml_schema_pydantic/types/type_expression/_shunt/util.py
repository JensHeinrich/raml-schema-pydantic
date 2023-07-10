from __future__ import annotations

import logging
from typing import Any
from typing import Dict
from typing import Generic
from typing import List
from typing import Mapping
from typing import Sequence
from typing import Tuple
from typing import TYPE_CHECKING
from typing import TypeGuard
from typing import TypeVar

from pydantic import Field
from pydantic import PydanticTypeError
from pydantic import root_validator
from pydantic import validator
from pydantic.generics import GenericModel

from .ast import INode
from .token_types import _SymbolType
from .token_types import _ValueType
from .token_types import Operator
from .token_types import RPNToken
from .token_types import Token

if TYPE_CHECKING:
    from typing_extensions import Self


logger = logging.getLogger(__name__)

_RPNTokenType = TypeVar("_RPNTokenType", bound=RPNToken)


class RPNNode(GenericModel, INode, Generic[_RPNTokenType]):
    arg_count: int = Field(
        default=0,
        # ge=0,
        required=True,
    )  # needs to be defined first

    def __eq__(self, __value: object) -> bool:
        if isinstance(__value, RPNNode):
            return (
                self.arg_count == __value.arg_count
                and self.value == __value.value
                and len(self.children) == len(__value.children)
                and all(
                    [
                        self.children[i] == __value.children[i]
                        for i in range(len(self.children))
                    ]
                )
            )
        logger.warning(f"Trying to compare {type(self)} to {type(__value)}")
        return False

    @validator("arg_count")
    def _validate_arg_count(cls, v) -> int:
        if 0 <= v:
            return v
        raise ValueError()

    value: _RPNTokenType = Field(
        default=...,
        required=True,
        description="An RPNToken"  # list of symbols using `None` as placeholder for the children",
        # i.e.
        # [Token("A")] for a value
        # [Token("!"), None] for an unary prefix operator
        # [None, Token("[]")] for an unary suffix operator
        # [None, Token("*"), None] for a binary operator
        # [None. Token("?"), None, Token(":"), None] for a ternary operator
        #
    )
    children: List[RPNNode[_RPNTokenType]] = Field(default=..., required=False)

    @validator("children")
    def _validate_child_count(cls, v: None | Any, values) -> None | int:
        if v is None:
            return v
        if len(v) == values["arg_count"]:
            return v
        if values["arg_count"] == len(list(filter(lambda p: p is None, v))):
            return v

        raise ValueError(
            f"{' '.join(values['value'])} expects {values['arg_count']} children, but got {len(v)} children: {v}"
        )

    @property
    def nodename(self) -> str:
        """Create a unique and reusable name for the node.

        Returns:
            str: unique name for the node
        """
        return f"RPNNode{id(self)}"

    def as_dot(self) -> str:
        """Return a dot representation of the node and its children.

        Returns:
            str: dot representation of the node and its children.
        """
        return "\n".join(
            (
                # f"""{self.nodename} [label = "{self.op.symbol}"];""",
                f"""{self.nodename} [label = "{self.value}"];""",
            )
            + (
                "// edges to children",
                f"""{self.nodename} -> {{ {str(' '.join(c.nodename for c in self.children))} }}""",
                "// child definitions",
                *(c.as_dot() for c in self.children),
            )
            if self.arg_count > 0
            else ()
        )

    def __str__(self) -> str:  # noqa: ignore[C901] # FIXME
        _ret: str = ""
        _v: Token | None
        # FIXME ternary operators are not yet supported
        if self.arg_count == 0:
            return str(self.value)

        # arg_count is at least one, so a left child is defined
        _left_child: RPNNode[_RPNTokenType] = self.children[0]
        _left_child_string: str

        if _left_child.arg_count > 1 and (
            _left_child.value.precedence < self.value.precedence
            or (
                _left_child.value.precedence == self.value.precedence
                and _left_child.value.associativity == "right"
            )
            or _left_child.value.associativity == "none"
        ):
            logger.warning(
                f"""{repr(_left_child.value)}
            {repr(self.value)}
            {[str(child) for child in self.children]}"""
            )
            _left_child_string = f"({_left_child})"
        else:
            _left_child_string = f"{_left_child}"

        if self.arg_count == 1:
            assert len(self.value.values) == 2  # nosec: ignore[B101]
            logger.warning(
                f"Handling unary operator {self.value} with {[ str(child) for child in self.children]}"
            )

            if self.value.values[-1] is None:
                return f"{self.value.values[0]}{_left_child_string}"
            return f"{_left_child_string}{self.value.values[1]}"

        # arg_count is at least 2, so a left child is defined
        _right_child: RPNNode[_RPNTokenType] = self.children[1]
        _right_child_string: str

        if (
            not pop_before(
                _right_child.value,
                self.value,
            )
            # 0 <= _right_child.value.precedence < self.value.precedence
            and _right_child.arg_count > 1
        ):
            _right_child_string = f"({_right_child})"
        else:
            _right_child_string = f"{_right_child}"

        if self.arg_count == 2:
            # TODO handle associativity
            logger.warning(
                f"Handling binary operator {self.value} with {[ str(child) for child in self.children]}"
            )

            return f"{_left_child_string}{self.value}{_right_child_string}"

        j = 0
        for _v in self.value.values:
            if _v is None:
                if self.children[j].arg_count > 1:
                    _ret += f"({self.children[j]})"
                else:
                    _ret += f"{self.children[j]}"
                j += 1
            else:
                _ret += str(_v)
        return _ret

    def __hash__(self) -> int:
        return self.__str__().__hash__()

    def dirty_tree_str(self) -> str:
        return (
            f"|{self.value}|"
            + f"[{','.join([child.dirty_tree_str() for child in self.children])}]"
            if len(self.children) > 0
            else ""
        )


def pop_before(op1: RPNToken, op2: RPNToken) -> bool:
    """Return wether op1 should be evaluated before op2.

    The structure is expected to be like
        a op1 b op2 c

    If op1 has higher precedence than op2 or the same precedence and is left associative,
    then op1 has to be evaluated before op2, so it needs to be popped first.

    If the structure is
        a op1 op2 b
    than the following cases are possible:
        op1 is an unary postfix operator and op2 is a binary operator
        => op1 is evaluated before op2  => True
        op1 is a binary operator and op2 is an unary prefix operator
        => op2 is evaluated before op1  => False

    If the structure is
        op1 op2 b
    than
        op1 and op2 have to be unary prefix operators and op2 is to be evaluated before op1
        => True

    Args:
        op1 (RPNToken): first operator
        op2 (RPNToken): second operator

    Returns:
        bool: wether op1 should be evaluated before op2
    """
    if op2.arg_count == 1:
        # Unary operators.
        # These generally work just like any binary operators except that they only pop one operand when they’re applied.
        # There is one extra rule that needs to be followed, though:
        # when processing a unary operator, it’s only allowed to pop-and-apply other unary operators—never any binary ones, regardless of precedence.
        # This rule is to ensure that formulas like a ^ -b are handled correctly, where ^ (exponentiation) has a higher precedence than - (negation).
        # (In a ^ -b there’s only one correct parse, but in -a^b you want to apply the ^ first.)
        # Source: https://www.reedbeta.com/blog/the-shunting-yard-algorithm/
        if op1.arg_count == 2:
            logger.debug("unary operator can not be evaluated before binary")
            return False

    elif op1.arg_count == 1:
        if op1.values[0] is None:  # postfix operator needs to be applied first
            # if op2.arg_count != 1:
            logger.debug(
                "unary operator postfix followed by binary has to be evaluated first"
            )
            return True

    return op1.precedence > op2.precedence or (
        op1.precedence == op2.precedence and op2.associativity == "left"
    )


class ValueNode(GenericModel, INode, Generic[_ValueType]):
    """Dedicated class for values nodes."""

    value: _ValueType
    precedence: int = -1

    @root_validator(pre=True)
    def _pass_str_as_value(cls, values):
        if isinstance(values, str):
            return {"value": values}
        logger.error(f"Non string value {values}")
        return values

    def as_dot(self) -> str:
        """Return a dot representation of the node and its children.

        Returns:
            str: dot representation of the node and its children.
        """
        return f'{self.nodename} [label="{self.value}"]'

    @property
    def nodename(self) -> str:
        """Create a unique and reusable name for the node.

        Returns:
            str: unique name for the node
        """
        return f"ValueNode{id(self)}"

    def __str__(self) -> str:
        """Create the informal string representation.

        Returns:
            str: 'informal' string representation of the object.
        """
        return str(self.value)

    def __repr__(self: Self) -> str:
        """Create the official string representation.

        Returns:
            str: 'official' string representation of the object.
        """
        try:
            return f"ValueNode(value='{self.value}')"
        except ValueError:
            return "ValueNode(value='UNKNOWN VALUE')"


class OperatorOrValueNode(GenericModel, Generic[_SymbolType, _ValueType]):
    __root__: OperatorNode[_SymbolType, _ValueType] | ValueNode[_ValueType]


class OperatorNode(Operator[_SymbolType], INode, Generic[_SymbolType, _ValueType]):
    """Dedicated class for operator nodes."""

    class Config:  # noqa [D106]
        orm_mode = False

    # op: Operator
    children: List[
        OperatorNode[_SymbolType, _ValueType] | ValueNode[_ValueType]
    ]  # Ordering might be important for non commutative Operations

    @root_validator(pre=True)
    def _unpack_provided_op(cls, values) -> Dict[str, Any]:
        if isinstance(values, Mapping):
            _values: Dict[str, Any] = {k: values[k] for k in values if k != "op"}
            if "op" in values:
                _values.update(_values["op"])
            return _values
        raise PydanticTypeError(msg_template=f"Expected Mapping, got {type(values)}")

    @validator("children")
    @classmethod
    def _validate_child_count(cls, v: Any, values: Dict[str, Any]):
        # if values["op"].unary == True:
        if values["unary"]:
            if not len(v) == 1:
                raise ValueError("Unary Operator has exactly one child")

        # if values["op"].unary == False:
        if not values["unary"]:
            if not len(v) == 2:
                raise ValueError("Binary Operator has exactly two children")

        return v

    @property
    def nodename(self) -> str:
        """Create a unique and reusable name for the node.

        Returns:
            str: unique name for the node
        """
        return f"OperatorNode{id(self)}"

    def as_dot(self) -> str:
        """Return a dot representation of the node and its children.

        Returns:
            str: dot representation of the node and its children.
        """
        return "\n".join(
            (
                # f"""{self.nodename} [label = "{self.op.symbol}"];""",
                f"""{self.nodename} [label = "{self.value}"];""",
                "// edges to children",
                f"""{self.nodename} -> {{ {str(' '.join(c.nodename for c in self.children))} }}""",
                "// child definitions",
                *(c.as_dot() for c in self.children),
            )
        )

    def __str__(self) -> str:
        """Create the informal string representation.

        Returns:
            str: 'informal' string representation of the object.
        """
        if self.unary is False:
            # binary operator
            # TODO handle associativity
            _left_child = self.children[0]
            _right_child = self.children[1]
            if 0 <= _left_child.precedence < self.precedence or (
                0 <= _left_child.precedence <= self.precedence
                and self.associativity == "right"
            ):
                _left_child_string = f"({_left_child})"
            else:
                _left_child_string = f"{_left_child}"

            if 0 <= _right_child.precedence < self.precedence:
                _right_child_string = f"({_right_child})"
            else:
                _right_child_string = f"{_right_child}"

            return f"{_left_child_string}{self.value}{_right_child_string}"

        elif self.unary == "both":
            raise NotImplementedError(
                "str representation of operator usable for unary and binary expressions is not implemented"
            )
        else:  # elif self.op.unary is True:
            _child = self.children[0]
            logger.warning(
                f"Handling child {_child}. Current precedence {self.precedence}"
            )
            if 0 <= _child.precedence <= self.precedence:
                # parentheses need to be inserted to keep the order
                _child_string = f"({self.children[0]})"
            else:
                _child_string = f"{self.children[0]}"

            if self.unary_position == "prefix":
                return f"{self.value}{_child_string}"
            else:  # if self.op.unary_position == "postfix":
                return f"{_child_string}{self.value}"


_OperatorNodeType = TypeVar("_OperatorNodeType", bound=OperatorNode)
_OperatorNodeType_co = TypeVar(
    "_OperatorNodeType_co", bound=OperatorNode, covariant=True
)
_OperatorNodeType_contra = TypeVar(
    "_OperatorNodeType_contra", bound=OperatorNode, contravariant=True
)
_ValueNodeType = TypeVar("_ValueNodeType", bound=ValueNode)
_ValueNodeType_co = TypeVar("_ValueNodeType_co", bound=ValueNode, covariant=True)
_ValueNodeType_contra = TypeVar(
    "_ValueNodeType_contra", bound=ValueNode, contravariant=True
)


def postfix_to_ast(
    input_data: List[Operator[_SymbolType] | _ValueType],
) -> ValueNode[_ValueType] | OperatorNode[_SymbolType, _ValueType]:
    """Convert a tree in postfix notation into a "proper" Tree.

    Args:
        input_data (List[str  |  Operator]): Operators and Values in postfix notation

    Returns:
        ITree: Tree matching the input
    """

    def _parse_as_far_as_possible(
        input_data: List[Operator[_SymbolType] | _ValueType],
    ) -> Tuple[
        OperatorNode[_SymbolType, _ValueType] | ValueNode[_ValueType],
        List[Operator[_SymbolType] | _ValueType],
    ]:
        """Parse a list of operators and values into a Tree and a list of unused entries.

        Args:
            input_data (List[Token | Operator]):  Operators and Values in postfix notation

        Raises:
            NotImplementedError: Exception for unclear operators

        Returns:
            Tuple[ITree, List[str | Operator]]: Subtree and unused entries
        """
        _current: _ValueType | Operator[_SymbolType] = input_data.pop()
        if isinstance(_current, Operator):
            children: List[
                ValueNode[_ValueType] | OperatorNode[_SymbolType, _ValueType]
            ]
            if _current.unary is True:
                child, input_data = _parse_as_far_as_possible(input_data)
                children = [child]
            elif _current.unary is False:
                right, input_data = _parse_as_far_as_possible(
                    input_data
                )  # the right hand side is put on the stack last
                left, input_data = _parse_as_far_as_possible(
                    input_data
                )  # the left hand side is put on the stack first
                children = [left, right]
            else:
                raise NotImplementedError("Mixed operators are not yet supported")

            return (
                OperatorNode(
                    children=children,
                    **_current.dict(by_alias=True),
                ),
                input_data,
            )
        if isinstance(_current, Token):
            return ValueNode(value=_current), input_data

        raise PydanticTypeError(msg_template="ValueNode or Operator required")

    def _parse(
        input_data: List[Operator[_SymbolType] | _ValueType],
    ) -> OperatorNode[_SymbolType, _ValueType] | ValueNode[_ValueType]:
        _node, input_data = _parse_as_far_as_possible(input_data)
        if input_data:
            raise ValueError("Postfix notation was not resolvable")
        return _node

    return _parse(input_data)


_K = TypeVar("_K")


def check_in(instance: Any, d: Mapping[_K, Any] | Sequence[_K]) -> TypeGuard[_K]:
    """Typeguard for determining the type of instance by checking if it is in a mapping or a dict of that type.

    Args:
        instance (Any): instance to check
        d (Mapping[_K, Any] | Sequence[_K]): Mapping with _K-typed keys or Sequence of _K-typed vales to check against

    Returns:
        TypeGuard[_K]: wether instance is of type _K
    """
    if instance in d:
        return True
    return False


__all__ = (
    "_OperatorNodeType_co",
    "_OperatorNodeType_contra",
    "_OperatorNodeType",
    "_ValueNodeType_co",
    "_ValueNodeType_contra",
    "_ValueNodeType",
    "check_in",
    "OperatorNode",
    "postfix_to_ast",
    "ValueNode",
)
