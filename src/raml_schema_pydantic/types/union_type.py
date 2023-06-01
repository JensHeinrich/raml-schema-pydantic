# from __future__ import annotations
import logging
from typing import Annotated
from typing import List
from typing import Type
from typing import Union

from pydantic import create_model
from pydantic import Field
from pydantic import validator

from ..type_expression import TypeExpression
from ..type_expression import UnionTypeExpression
from .any_type import AnyType
from .type_declaration import ITypeDeclaration

logger = logging.getLogger(__name__)


class UnionType(AnyType):
    # A union type MAY be used to allow instances of data to be described by any of several types.
    # A union type MUST be declared via a type expression that combines 2 or more types delimited by pipe (`|`) symbols;
    type_: Annotated[
        UnionTypeExpression,
        Field(
            alias="type",
            required=True,
            include=True,
            exclude=False,
            # const=True
        ),
    ]
    # these combined types are referred to as the union type's super types.
    super_types: List[TypeExpression]  # | ITypeDeclaration

    @validator("super_types")
    def _check_super_type_count(cls, v):
        assert len(v) == 2
        return v

    def as_type(self) -> Type:
        """Return the type represented by the RAML definition.

        Returns:
            Type: Type described by the TypeDeclaration
        """
        # import in function to ensure the newest state

        _union_types = tuple(self.super_types)
        assert self.super_types

        # An instance of a union type SHALL be considered valid if and only if it meets all restrictions associated with at least one of the super types.
        # More generally, an instance of a type that has a union type in its type hierarchy SHALL be considered valid if and only if it is a valid instance of at least one of the super types obtained by expanding all unions in that type hierarchy.
        return create_model(
            getattr(self, "name", "|".join(str(t) for t in self.super_types)),
            __root__=Union[
                (
                    t1
                    if isinstance((t1 := self.super_types[0]), ITypeDeclaration)
                    else t1.as_type(),
                    t2
                    if isinstance((t2 := self.super_types[1]), ITypeDeclaration)
                    else t2.as_type(),
                    # Type[self.super_types[0].as_type()], Type[self.super_types[1].as_type()]
                )
            ],
        )

    class Config:
        # Such an instance is deserialized by performing this expansion and then matching the instance against all the super types, starting from the left-most and proceeding to the right;
        # the first successfully-matching base type is used to deserialize the instance.
        smart_union = False
