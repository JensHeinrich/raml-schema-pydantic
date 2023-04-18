"""Module for RAML string types."""
import logging
import re
from typing import Annotated
from typing import Literal
from typing import Optional
from typing import Type

from pydantic import constr
from pydantic import Field

from .._type_dict import TYPES
from ..any_type import AnyType

logger = logging.getLogger(__name__)


class StringType(AnyType):
    """A JSON string."""

    # A JSON string with the following additional facets:

    type_: Annotated[
        Optional[Literal["string"]],
        Field(
            alias="type",
            required=True,
            include=True,
            exclude=False,
            const=True,
        ),
    ] = "string"

    # | pattern?
    # | Regular expression that this string MUST match.
    pattern: re.Pattern | None = None

    # | minLength?
    # | Minimum length of the string.
    # Value MUST be equal to or greater than 0.<br /><br />
    # **Default:** `0`
    minLength: int = Field(default=0, ge=0)  # noqa: N815

    # | maxLength?
    # | Maximum length of the string.
    # Value MUST be equal to or greater than 0.<br /><br />
    # **Default:** `2147483647`
    maxLength: int = Field(default=2147483647, ge=0)  # noqa: N815

    def as_type(self) -> Type:
        """Return the type represented by the RAML definition.

        Returns:
            Type: Type described by the TypeDeclaration
        """
        return constr(
            min_length=self.minLength,
            max_length=self.maxLength,
            # TODO Remove annotation after https://github.com/pydantic/pydantic/pull/5499 is merged
            regex=self.pattern.pattern
            if self.pattern is not None
            else None,  # pyright: reportGeneralTypeIssues=false
        )


TYPES.update(
    {
        t.__fields__["type_"].default: t
        for t in {
            StringType,
        }
    }
)
