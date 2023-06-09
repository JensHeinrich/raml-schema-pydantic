"""Module for Union Types."""
# from __future__ import annotations
import logging
from typing import Any
from typing import Dict
from typing import Self
from typing import Sequence
from typing import TYPE_CHECKING

from pydantic import BaseModel
from pydantic import validator
from pydantic.errors import ListMinLengthError
from typing_extensions import override

from ._TypeDeclarationProtocol import TypeDeclarationProtocol
from .type_declaration import ProtocolModel

# from ..type_expression import UnionTypeExpression
# from .any_type import AnyType
# from .type_declaration import ITypeDeclaration, TypeDeclaration

logger = logging.getLogger(__name__)


class UnionType(
    BaseModel,
    TypeDeclarationProtocol,
    metaclass=ProtocolModel
    # AnyType
):
    """A union type MAY be used to allow instances of data to be described by any of several types."""

    # A union type MUST be declared via a type expression that combines 2 or more types delimited by pipe (`|`) symbols;
    # type_: Annotated[
    #     UnionTypeExpression,
    #     Field(
    #         alias="type",
    #         required=True,
    #         include=True,
    #         exclude=False,
    #         # const=True
    #     ),
    # ]
    # these combined types are referred to as the union type's super types.
    super_types: "Sequence[TypeExpression]"  # | ITypeDeclaration

    @validator("super_types")
    def _check_super_type_count(cls, v):
        if len(v) == 2:
            return v
        raise ListMinLengthError(limit_value=2)

    @override
    def schema(  # type: ignore[override]
        self: Self, by_alias: bool = ..., ref_template: str = ...  # type: ignore[assignment]
    ) -> Dict[str, Any]:
        """Return the type represented by the RAML definition.

        Returns:
            Dict[str, Any]: Schema for the UnionType
        """
        # An instance of a union type SHALL be considered valid if and only if it meets all restrictions associated with at least one of the super types.
        # More generally, an instance of a type that has a union type in its type hierarchy SHALL be considered valid if and only if it is a valid instance of at least one of the super types obtained by expanding all unions in that type hierarchy.
        return {"anyOf": [t.schema for t in self.super_types]}

    class Config:  # type: ignore[D106]
        # Such an instance is deserialized by performing this expansion and then matching the instance against all the super types, starting from the left-most and proceeding to the right;
        # the first successfully-matching base type is used to deserialize the instance.
        smart_union = False


if TYPE_CHECKING:
    from .type_expression import TypeExpression
