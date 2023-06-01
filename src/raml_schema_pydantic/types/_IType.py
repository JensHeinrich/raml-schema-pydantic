from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from typing import Any
from typing import Dict
from typing import Iterable
from typing import Protocol
from typing import Sequence
from typing import Type
from typing import TYPE_CHECKING

from pydantic import BaseModel


if TYPE_CHECKING:
    from typing_extensions import Self


class TypeDeclarationProtocol(Protocol):
    """Protocol for objects representing type declarations."""

    @abstractmethod
    def schema(self: Self) -> Dict[str, Any]:
        ...


class RamlTypeProto(Iterable, Protocol):
    """Protocol for objects representing types."""

    # RAML Types in a nutshell:

    # - Types are similar to Java classes.
    #   - Types borrow additional features from JSON Schema, XSD, and more expressive object oriented languages.
    # - You can define types that inherit from other types.
    #   - Multiple inheritance is allowed.
    # - Types are split into four families: external, object, array, and scalar.
    # - Types can define two types of members: **properties** and **facets**. Both are inherited.
    #   - **Properties** are regular, object oriented properties.

    @property
    @abstractmethod
    def _properties(self: Self) -> Sequence[str]:
        ...

    #   - **Facets** are special _configurations_. You specialize types based on characteristics of facet values.
    #     Examples: minLength, maxLength
    @property
    @abstractmethod
    def _facets(self: Self) -> Sequence[str]:
        ...

    # - Only object types can declare properties. All types can declare facets.
    # - To specialize a scalar type, you implement facets, giving already defined facets a concrete value.
    # - To specialize an object type, you define properties.

    # TODO evaluate Name / Interface
    @abstractmethod
    def as_type(self: Self) -> "AnyType":
        """Return the type represented by the RAML definition.

        Returns:
            Type: Type described by the TypeDeclaration
        """
        ...

    @abstractmethod
    def as_raml(self: Self):
        """Return a TypeDeclaration for self.

        Returns:
            TypeDeclaration: Declaration for use in a RAML file.
        """
        ...

    def __eq__(self: Self, o: IType | Self | object) -> bool:
        """Evaluate the equality of two interfaces or an interface and a type.

        Args:
            self (Self): left interface
            o (IType | Self): right interface or type

        Returns:
            bool: equality of interfaces
        """
        if hasattr(o, "name_") and hasattr(self, "name_"):
            return self.name_ == o.name_  # pyright: ignore [reportGeneralTypeIssues]

        if isinstance(o, IType):
            return self.as_type() == o.as_type()
        if isinstance(o, type):
            return self.as_type() == o
        return super().__eq__(o)  # TODO FIXME


class IType(ABC, Iterable):
    """Interface for objects representing types."""

    # RAML Types in a nutshell:

    # - Types are similar to Java classes.
    #   - Types borrow additional features from JSON Schema, XSD, and more expressive object oriented languages.
    # - You can define types that inherit from other types.
    #   - Multiple inheritance is allowed.
    # - Types are split into four families: external, object, array, and scalar.
    # - Types can define two types of members: **properties** and **facets**. Both are inherited.
    #   - **Properties** are regular, object oriented properties.
    @property
    @abstractmethod
    def _properties(self: Self) -> Sequence[str]:
        ...

    #   - **Facets** are special _configurations_. You specialize types based on characteristics of facet values.
    #     Examples: minLength, maxLength
    @property
    @abstractmethod
    def _facets(self: Self) -> Sequence[str]:
        ...

    # - Only object types can declare properties. All types can declare facets.
    # - To specialize a scalar type, you implement facets, giving already defined facets a concrete value.
    # - To specialize an object type, you define properties.

    # TODO evaluate Name / Interface
    @abstractmethod
    def as_type(self: Self) -> Type:  # "AnyType":
        """Return the type represented by the RAML definition.

        Returns:
            Type: Type described by the TypeDeclaration
        """
        ...

    def __eq__(self: Self, o: IType | Self | object) -> bool:
        """Evaluate the equality of two interfaces or an interface and a type.

        Args:
            self (Self): left interface
            o (IType | Self): right interface or type

        Returns:
            bool: equality of interfaces
        """
        if hasattr(o, "name_") and hasattr(self, "name_"):
            return self.name_ == o.name_  # pyright: ignore [reportGeneralTypeIssues]

        if isinstance(o, IType):
            return self.as_type() == o.as_type()
        if isinstance(o, type):
            return self.as_type() == o
        return super().__eq__(o)  # TODO FIXME


if TYPE_CHECKING:
    from .any_type import AnyType
