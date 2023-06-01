"""Module for RAML nil types."""
import logging
from typing import Annotated
from typing import Literal
from typing import Optional
from typing import Type
from typing import TypeAlias

from pydantic import Extra
from pydantic import Field

from .._type_dict import _TYPE_DECLARATIONS
from ..any_type import AnyType

ContentType: TypeAlias = str  # TODO
logger = logging.getLogger(__name__)


class NilType(AnyType):
    """In RAML, the type `nil` is a scalar type that SHALL allow only nil data values."""

    # Specifically, in YAML, it allows only YAML's `null` (or its equivalent representations, such as `~`).
    # In JSON, it allows only JSON's `null`, and in XML, it allows only XML's `xsi:nil`.
    # In headers, URI parameters, and query parameters, the `nil` type SHALL only allow the string value "nil" (case-sensitive); and in turn, an instance having the string value "nil" (case-sensitive), when described with the `nil` type, SHALL deserialize to a nil value.

    # Using the type `nil` in a union makes a type definition nilable, which means that any instance of that union MAY be a nil data value.
    # When such a union is composed of only one type in addition to `| nil`, use of a trailing question mark `?` instead of the union syntax is equivalent.
    # The use of that equivalent, alternative syntax SHALL be restricted to [scalar types](#scalar-types) and references to user-defined types, and SHALL NOT be used in [type expressions](#type-expressions).

    type_: Annotated[
        Optional[Literal["nil"]],
        Field(
            alias="type",
            required=True,
            include=True,
            exclude=False,
            const=True,
        ),
    ] = "nil"

    class Config:  # noqa: D106
        extra = Extra.forbid

    def __repr__(self) -> str:
        """Create the official string representation.

        Returns:
            str: 'official' string representation of the object.
        """
        return "NilType()"

    def __str__(self) -> str:
        """Create the informal string representation.

        Returns:
            str: 'informal' string representation of the object.
        """
        return "nil"

    def as_type(self) -> Type:
        """Return the type represented by the RAML definition.

        Returns:
            Type: Type described by the TypeDeclaration
        """
        return None.__class__


from .._type_dict import register_type_declaration

register_type_declaration("nil", NilType())
