"""Module for boolean type."""
import logging
from typing import Annotated
from typing import Literal
from typing import Optional
from typing import Type

from pydantic import Extra
from pydantic import Field

from .._type_dict import TYPES
from ..any_type import AnyType

logger = logging.getLogger(__name__)


class BooleanType(AnyType):
    """A JSON boolean without any additional facets."""

    type_: Annotated[
        Optional[Literal["boolean"]],
        Field(
            alias="type",
            required=True,
            include=True,
            exclude=False,
            const=True,
        ),
    ] = "boolean"

    class Config:  # noqa: D106
        extra = Extra.forbid

    def as_type(self) -> Type:
        """Return the type represented by the RAML definition.

        Returns:
            Type: Type described by the TypeDeclaration
        """
        namespace = dict()
        return type("BooleanType", (bool,), namespace)


TYPES.update({t.__fields__["type_"].default: t for t in {BooleanType}})
