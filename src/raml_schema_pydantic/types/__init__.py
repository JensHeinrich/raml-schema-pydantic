"""Module for RAML types."""
from typing import Type
from typing import TypeAlias

from pydantic import BaseModel
from typing_extensions import Self

from ._IType import IType
from ._type_dict import _TYPE_DECLARATIONS
from .any_type import AnyType
from .array_type import ArrayType
from .object_type import ObjectType
from .scalar_types import BooleanType
from .scalar_types import DateOnlyType
from .scalar_types import DateTimeOnlyType
from .scalar_types import DateTimeType
from .scalar_types import FileType
from .scalar_types import IntegerType
from .scalar_types import NilType
from .scalar_types import NumberType
from .scalar_types import ScalarType
from .scalar_types import ScalarTypeContainer
from .scalar_types import ScalarTypeNames
from .scalar_types import StringType
from .scalar_types import TimeOnlyType
from .type_declaration import GenericTypeDeclaration
from .type_declaration import IInlineTypeDeclaration
from .type_declaration import ITypeDeclaration
from .union_type import UnionType

# from ._type_dict import register_type_declarations


class TypeContainer(BaseModel, IType):
    __root__: ScalarTypeContainer | ArrayType | ObjectType | AnyType

    def as_type(self: Self) -> Type:
        return self.__root__.as_type()


InlineTypeDeclaration: TypeAlias = TypeContainer


ArrayType.update_forward_refs()


# register_type_declarations(
#     {
#         t().__fields__["type_"].default: t()  # FIXME
#         for t in {
#             AnyType,
#             StringType,
#             IntegerType,
#             NumberType,
#             BooleanType,
#             DateTimeType,
#             DateOnlyType,
#             DateTimeOnlyType,
#             FileType,
#             TimeOnlyType,
#             NilType,
#             ArrayType,
#             ObjectType,
#         }
#     }.items()
# )

__all__ = [
    "AnyType",
    "ObjectType",
    "ArrayType",
    "StringType",
    "NumberType",
    "IntegerType",
    "BooleanType",
    "DateTimeType",
    "DateOnlyType",
    "DateTimeOnlyType",
    "ScalarTypeContainer",
    "ScalarType",
    "TimeOnlyType",
    "FileType",
    "NilType",
    "ScalarTypeNames",
    "_TYPE_DECLARATIONS",
    "UnionType",
    "ITypeDeclaration",
    "IInlineTypeDeclaration",
    "GenericTypeDeclaration",
]
