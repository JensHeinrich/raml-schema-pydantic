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

from pydantic import PydanticTypeError
from pydantic import root_validator
from pydantic import validator
from pydantic.generics import GenericModel

from .ast import INode
from .token_types import _SymbolType
from .token_types import _ValueType
from .token_types import Operator
from .token_types import Token

if TYPE_CHECKING:
    from typing_extensions import Self


logger = logging.getLogger(__name__)


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
