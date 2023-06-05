"""Module for boolean type."""
import logging
from typing import Annotated
from typing import Any
from typing import Collection
from typing import Dict
from typing import Literal
from typing import Optional
from typing import Sequence
from typing import Type

from pydantic import Extra
from pydantic import Field
from typing_extensions import Self

from .._type_dict import register_type_declaration
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
        namespace: Dict[str, Any] = dict()
        return type("BooleanType", (bool,), namespace)

    @property
    def _facets(self: Self) -> Collection[str]:
        return ()

    @property
    def _properties(self: Self) -> Collection[str]:
        return ()


register_type_declaration("boolean", BooleanType())
