"""Module for the BaseType."""
from typing import Annotated
from typing import Any
from typing import Generator
from typing import Literal
from typing import Optional
from typing import Sequence
from typing import Type

from pydantic import BaseModel
from pydantic import Extra
from pydantic import Field
from pydantic import root_validator
from pydantic.fields import ModelField
from pydantic.typing import AnyCallable
from typing_extensions import Self

from .._helpers import debug
from ._IType import TypeDeclarationProtocol
from ._type_dict import register_type_declaration
from .type_declaration import ITypeDeclaration


class AnyTypeType:
    """Type for fields representing the `any` type."""

    @classmethod
    def __get_validators__(cls) -> Generator[AnyCallable, None, None]:
        """Yield validators for use with pydantic.

        Yields:
            Generator[AnyCallable, None, None]: Validators for the type
        """
        yield from []

    @classmethod
    def __modify_schema__(cls, field_schema: dict[str, Any], field: ModelField | None):
        """Update the schema of a field specified as this type.

        Args:
            field_schema (dict[str, Any]): Schema of the field
            field (ModelField | None): Field in the model
        """
        field_schema["type"] = {
            # this is already modified to be valid in an openapi schema
            "anyOf": [
                {"type": "null"},
                {"type": "boolean"},
                {"type": "string"},
                {"type": "number"},
                {"type": "integer"},
                {"type": "object"},
                {"type": "array", "items": "{}"},
            ]
        }


class AnyType(
    BaseModel,
    ITypeDeclaration,
    TypeDeclarationProtocol
    # BaseModel
    # GenericTypeDeclaration # FIXME
):
    """Every type, whether built-in or user-defined, has the any type at the root of its inheritance tree."""

    type_: Annotated[
        Optional[Literal["any"] | str],
        Field(
            alias="type",
            include=True,
            exclude=False,
            const=True,
        ),
    ] = "any"

    # By definition, the any type is a type which imposes no restrictions, i.e. any instance of data is valid against it.
    class Config:  # noqa: D106
        extras = Extra.allow

    # The "base" type of any type is the type in its inheritance tree that directly extends the any type at the root;
    # thus, for example, if a custom type status extends the built-in type integer which extends the built-in type number which extends the any type, then the base type of status is number.
    # Note that a type may have more than one base type.

    # The any type has no additional facets.

    # TODO Check wether facets need to be passed to types
    @property
    def _facets(self) -> Sequence[str]:
        return list(self.__fields_set__)

    _debug = root_validator(pre=True, allow_reuse=True)(debug)

    def as_type(self) -> Type:
        """Return the type represented by the RAML definition.

        Returns:
            Type: Type described by the TypeDeclaration
        """
        return type("AnyTypeTypeValue", (AnyTypeType,), {})

    @property
    def _properties(self: Self) -> Sequence[str]:
        return list(self.__fields_set__ - {"type_"})


register_type_declaration("AnyType", AnyType())
