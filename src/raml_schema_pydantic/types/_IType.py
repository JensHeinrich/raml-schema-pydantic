from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from typing import Type

from typing_extensions import Self


class IType(ABC):
    """Interface for objects representing types."""

    # TODO evaluate Name / Interface
    @abstractmethod
    def as_type(self: Self) -> Type:
        """Return the type represented by the RAML definition.

        Returns:
            Type: Type described by the TypeDeclaration
        """
        ...

    def __eq__(self: Self, o: IType | Self) -> bool:
        """Evaluate the equality of two interfaces or an interface and a type.

        Args:
            self (Self): left interface
            o (IType | Self): right interface or type

        Returns:
            bool: equality of interfaces
        """
        if hasattr(o, "name_") and hasattr(self, "name_"):
            return self.name_ == o.name_  # pyright: reportGeneralTypeIssues=false

        if isinstance(o, IType):
            return self.as_type() == o.as_type()
        if isinstance(o, Type):
            return self.as_type() == o
        super(type(self)).__eq__(o)  # TODO FIXME
