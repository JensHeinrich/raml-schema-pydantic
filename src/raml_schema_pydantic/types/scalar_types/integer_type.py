"""Module for RAML integer types."""
import logging
from typing import Annotated
from typing import Any
from typing import Literal
from typing import Optional
from typing import Type
from typing import TYPE_CHECKING

from pydantic import conint
from pydantic import Field
from pydantic import IntegerError
from pydantic import validator

from .._type_dict import TYPES
from .number_type import NumberType

if TYPE_CHECKING:
    from typing_extensions import Self
    from pydantic.fields import ModelField

logger = logging.getLogger(__name__)


class IntegerType(NumberType):
    """Any JSON number that is a positive or negative multiple of 1.

    # The integer type inherits its facets from the [number type](#number).
    """

    # Any JSON number with the following additional facets:
    type_: Annotated[
        Optional[Literal["integer"]],
        Field(
            alias="type",
            required=True,
            include=True,
            exclude=False,
            const=True,
        ),
    ] = "integer"

    @validator("minimum", "maximum", "multipleOf")
    def sanity_check_numbers(cls, v: int | float | Any, field: ModelField) -> Self:
        """Validate the facets as integers.

        Args:
            v (int | float | Any): value to validate
            field (ModelField): additional information on restraints of the field

        Raises:
            IntegerError: Exception for non-integer values

        Returns:
            Self: instance of the class
        """
        if v:
            if v % 1 != 0:
                raise IntegerError
        return cls(v)

    def as_type(self) -> Type:
        """Return the type represented by the RAML definition.

        Returns:
            Type: Type described by the TypeDeclaration
        """
        # TODO Remove annotation after https://github.com/pydantic/pydantic/pull/5499 is merged
        return conint(
            ge=self.minimum, le=self.maximum, multiple_of=self.multipleOf
        )  # pyright: reportGeneralTypeIssues=false


TYPES.update(
    {
        t.__fields__["type_"].default: t
        for t in {
            IntegerType,
        }
    }
)
