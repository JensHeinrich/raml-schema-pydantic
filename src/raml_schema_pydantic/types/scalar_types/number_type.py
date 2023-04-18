"""Module for RAML number types."""
import logging
from enum import Enum
from typing import Annotated
from typing import Literal
from typing import Optional
from typing import Type

from pydantic import confloat
from pydantic import Field

from ..any_type import AnyType

logger = logging.getLogger(__name__)


class NumberFormatEnum(str, Enum):
    """Enum of possible number formats."""

    int_ = "int"
    int8_ = "int8"
    int16_ = "int16"
    int32_ = "int32"
    int64_ = "int64"
    long_ = "long"
    float_ = "float"
    double_ = "double"


class NumberType(AnyType):
    """Any JSON number."""

    # Any JSON number with the following additional facets:

    type_: Annotated[
        Optional[Literal["number"]],
        Field(
            alias="type",
            required=True,
            include=True,
            exclude=False,
            const=True,
        ),
    ] = "number"

    # |minimum?
    # | The minimum value.
    minimum: Optional[float]

    # |maximum?
    # | The maximum value.
    maximum: Optional[float]

    # |format?
    # | The format of the value.
    # The value MUST be one of the following:
    # int, int8, int16, int32, int64, long, float, double.
    format_: Annotated[
        Optional[NumberFormatEnum],
        Field(alias="format"),
    ]
    # |multipleOf?
    # | A numeric instance is valid against "multipleOf" if the result of dividing the instance by this keyword's value is an integer. # noqa: E501
    multipleOf: Optional[float]  # noqa: N815

    def as_type(self) -> Type:
        """Return the type represented by the RAML definition.

        Returns:
            Type: Type described by the TypeDeclaration
        """
        # TODO Remove annotation after https://github.com/pydantic/pydantic/pull/5499 is merged
        return confloat(
            ge=self.minimum, le=self.maximum, multiple_of=self.multipleOf
        )  # pyright: reportGeneralTypeIssues=false
