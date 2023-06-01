"""Module for RAML types."""
from typing import List
from typing import Type
from typing import TYPE_CHECKING
from typing import TypeAlias

from pydantic import BaseModel

from .._IType import IType
from ..any_type import AnyType
from .boolean_type import BooleanType
from .date_type import DateOnlyType
from .date_type import DateTimeOnlyType
from .date_type import DateTimeType
from .date_type import TimeOnlyType
from .file_type import FileType
from .integer_type import IntegerType
from .nil_type import NilType
from .number_type import NumberType
from .string_type import StringType

if TYPE_CHECKING:
    from typing_extensions import Self

ScalarType: TypeAlias = (
    NumberType  # number,
    | BooleanType  # boolean,
    | StringType  # string,
    | DateOnlyType  # date-only,
    | TimeOnlyType  # time-only,
    | DateTimeOnlyType  # datetime-only,
    | DateTimeType  # datetime,
    | FileType  # file,
    | IntegerType  # integer,
    | NilType  # or nil
)


ScalarTypeNames: List[str] = [
    t.__fields__["type_"].default  # FIXME
    for t in {
        AnyType,
        StringType,
        IntegerType,
        NumberType,
        BooleanType,
        DateTimeType,
        DateOnlyType,
        DateTimeOnlyType,
        FileType,
        TimeOnlyType,
        NilType,
    }
]


class ScalarTypeContainer(BaseModel, IType):
    """Container for scalar types."""

    __root__: ScalarType

    def as_type(self: "Self") -> Type:
        """Return the type represented by the RAML definition.

        Returns:
            Type: Type described by the TypeDeclaration
        """
        return self.__root__.as_type()


__all__ = [
    "StringType",
    "ScalarType",
    "IntegerType",
    "NumberType",
    "BooleanType",
    "DateTimeType",
    "DateOnlyType",
    "DateTimeOnlyType",
    "ScalarTypeContainer",
    "FileType",
    "TimeOnlyType",
    "NilType",
    "ScalarTypeNames",
]
