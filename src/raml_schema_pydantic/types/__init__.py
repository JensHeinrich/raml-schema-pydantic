"""Module for RAML types."""
from typing import Any
from typing import Collection
from typing import Dict
from typing import Type
from typing import TypeAlias

from pydantic import BaseModel
from typing_extensions import override
from typing_extensions import Self

from ._IType import IType
from ._type_dict import _TYPE_DECLARATIONS
from ._TypeDeclarationProtocol import TypeDeclarationProtocol
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
from .type_declaration import ProtocolModel
from .type_declaration import TypeDeclarationModel
from .type_expression import ArrayTypeExpression as ArrayTypeExpression
from .type_expression import TypeExpression
from .type_expression import TypeExpression as TypeExpression
from .type_expression import TypeName
from .type_expression import TypeName as TypeName
from .type_expression import UnionTypeExpression as UnionTypeExpression
from .union_type import UnionType

# from ._type_dict import register_type_declarations


class TypeContainer(BaseModel, IType, TypeDeclarationProtocol, metaclass=ProtocolModel):
    __root__: ScalarTypeContainer | ArrayType | ObjectType | AnyType

    @override
    def schema(self, by_alias: bool = ..., ref_template: str = ...) -> Dict[str, Any]:  # type: ignore[assignment,override]
        return self.__root__.schema()

    def _properties(self: Self) -> Collection[str]:
        return self.__root__._properties

    def _facets(self: Self) -> Collection[str]:
        return self.__root__._facets


InlineTypeDeclaration: TypeAlias = TypeContainer


ArrayType.update_forward_refs(TypeName=TypeName, TypeExpression=TypeExpression)


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
    "TypeExpression",
    "TypeName",
    "ArrayTypeExpression",
    "TypeName",
    "TypeExpression",
    "UnionTypeExpression",
]
