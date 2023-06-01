from typing import TypeAlias
from typing import Union

from .array_type_expression import ArrayTypeExpression as ArrayTypeExpression
from .inheritance_type_expression import InheritanceExpression as InheritanceExpression
from .nested_type_expression import NestedTypeExpression as NestedTypeExpression
from .type_name import TypeName as TypeName
from .union_type_expression import UnionTypeExpression as UnionTypeExpression


TypeExpressionType: TypeAlias = Union[
    InheritanceExpression,
    TypeName,
    NestedTypeExpression,
    ArrayTypeExpression,
    UnionTypeExpression,
]


# TypeExpressionType.update_forward_refs()
