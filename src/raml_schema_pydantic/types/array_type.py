import logging
from typing import Annotated
from typing import Any
from typing import Dict
from typing import Generic
from typing import Literal
from typing import Mapping
from typing import Optional
from typing import TYPE_CHECKING
from typing import TypeAlias
from typing import TypeVar

from pydantic import Field
from pydantic import root_validator
from pydantic import validator
from pydantic.fields import ModelField
from pydantic.generics import GenericModel

from ._type_dict import _TYPE_DECLARATIONS
from ._TypeDeclarationProtocol import TypeDeclarationProtocol
from .any_type import AnyType
from .type_declaration import IInlineTypeDeclaration

# InlineTypeDeclaration = ForwardRef("InlineTypeDeclaration", is_class=True)

logger = logging.getLogger(__name__)

# TODO Gather known types and use proper type expression
# ArrayTypeName: TypeAlias = ArrayTypeExpression

RootType = TypeVar("RootType")
NestedDict: TypeAlias = Dict[str, "str | NestedDict"]
NestedMapping: TypeAlias = Mapping[str, "str | NestedDict"]


class ArrayTypeType(GenericModel, Generic[RootType]):
    __root__: RootType


class ArrayType(AnyType):
    # Array types MUST be declared by using
    # either the array qualifier `[]` at the end of a [type expression](#type-expressions)
    # or `array` as the value of a `type` facet.
    type_: Annotated[
        Optional[Literal["array"]],  # | ArrayTypeName
        Field(
            alias="type",
            required=False,  # items faces implies array
            include=True,
            exclude=False,
            const=True,
        ),
    ] = "array"

    # If you are defining a top-level array type, such as the `Emails` in the examples below, you MAY declare the following facets in addition to those previously described to further restrict the behavior of the array type.

    # | uniqueItems?
    # | Boolean value that indicates if items in the array MUST be unique.
    uniqueItems: bool = False
    # | items?
    # | Indicates the type all items in the array are inherited from.
    # Can be a reference to an existing type or an inline [type declaration](#type-declarations).
    # items: Optional[Union[TypeName, InlineTypeDeclaration]]
    items: Optional[
        "TypeName | IInlineTypeDeclaration | TypeDeclarationProtocol"
    ] = AnyType()

    # | minItems? |
    # Minimum amount of items in array.
    # Value MUST be equal to or greater than 0.<br /><br />
    # **Default:** `0`.
    minItems: int = Field(default=0, ge=0)
    # | maxItems?
    # | Maximum amount of items in array.
    # Value MUST be equal to or greater than 0.<br /><br />
    # **Default:** `2147483647`.
    maxItems: int = Field(default=2147483647, ge=0)

    @validator("items", always=True)
    def check_items_from_array_type_expression(cls, v: Any, values):
        if False:  # isinstance(values["type_"], ArrayTypeExpression):
            if v and v != values["type_"].items:
                logger.warning("Items type is defined in `items` and `type`.")
        return v

    @root_validator(pre=True)
    def set_items_from_typename(
        cls: "ArrayType", values: NestedMapping
    ) -> NestedDict:  # Dict[str, str | Dict]:
        _type = values["type"] if "type" in values else "array"
        assert isinstance(_type, str)  # nosec B101

        _items = values["items"] if "items" in values else None

        if _type.endswith("[]"):
            logger.warning("`type_` should be `array` not `ArrayTypeExpression`")
            if _items:
                logger.warning("Items type is defined in `items` and `type`.")
            else:
                _items = _type.removesuffix("[]")

        _values = dict(values) | {"type": "array"}

        if isinstance(_items, str):
            _values["items"] = _items

        return _values

    @classmethod
    def __modify_schema__(cls, field_schema: dict[str, Any], field: ModelField | None):
        field_schema["type"] = "array"


if TYPE_CHECKING:
    from .type_expression.type_name import TypeName
    from .type_declaration import IInlineTypeDeclaration

_TYPE_DECLARATIONS.update(
    {
        t.__fields__["type_"].default: t
        for t in {
            ArrayType,
        }
    }
)
