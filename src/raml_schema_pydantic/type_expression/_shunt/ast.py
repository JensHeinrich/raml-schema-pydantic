"""Module describing tree and node interfaces."""
from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from typing_extensions import Self


class ITree(ABC):
    """Abstract tree interface."""

    @abstractmethod
    def as_dot(self: "Self") -> str:
        """Return a dot representation of the node and its children.

        Returns:
            str: dot representation of the node and its children.
        """
        ...

    def draw(self: "Self") -> str:
        """Return a complete representation of the tree in dot representation.

        Returns:
            str: complete representation of the tree in dot representation.
        """
        return "\n".join(("digraph {", self.as_dot(), "}"))


# Every node can be seen as a tree
class INode(ITree):
    """Abstract Node Interface."""

    @abstractmethod
    def as_dot(self: "Self") -> str:
        """Return a dot representation of the node and its children.

        Returns:
            str: dot representation of the node and its children.
        """
        ...

    @property
    @abstractmethod
    def nodename(self: "Self") -> str:
        """Create a unique and reusable name for the node.

        Returns:
            str: unique name for the node
        """
        ...

    # # pydantic compatibility
    # @classmethod
    # def validate_root_type(cls, values: INode | Any) -> INode:
    #     """Validate the INode.

    #     Args:
    #         values (INode | Any): Value of the INode.

    #     Raises:
    #         TypeError: Exception for an unsupported type.

    #     Returns:
    #         INode: Instance of the class.
    #     """
    #     if issubclass(type(values), cls):
    #         return values
    #     raise TypeError("Invalid root type")

    # @classmethod
    # def __get_validators__(
    #     cls,
    # ) -> Generator[Callable[[INode | Any], INode], None, None]:
    #     """Yield validators for INode.

    #     Yields:
    #         Generator[Callable[[INode | Any], INode], None, None]: Generator for INode validators
    #     """
    #     yield cls.validate_root_type


__all__ = ("INode", "ITree")
