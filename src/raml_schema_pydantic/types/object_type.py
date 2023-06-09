import logging
from typing import Annotated
from typing import Any
from typing import Collection
from typing import Dict
from typing import ForwardRef
from typing import Literal
from typing import Optional
from typing import Sequence
from typing import Type
from typing import TypeAlias

import pydantic
from pydantic import ConfigError
from pydantic import create_model
from pydantic import Extra
from pydantic import Field
from pydantic import root_validator
from pydantic import validator
from typing_extensions import Self

from .._helpers import _ValuesType
from .._helpers import debug

PropertiesDeclaration = ForwardRef("PropertiesDeclaration")
PropertyName = ForwardRef("PropertyName")
# from ..properties_declaration import PropertiesDeclaration
# from ..properties_declaration import PropertyName
from ._type_dict import _TYPE_DECLARATIONS
from ._type_dict import register_type_declaration
from .any_type import AnyType
from .type_expression import TypeName

logger = logging.getLogger(__name__)

# TODO Gather the types to do validation on this
ObjectTypeName: TypeAlias = str

OBJECT_TYPE_DEFAULT_NAME = "object"


class ObjectType(AnyType):
    type_: Annotated[
        Literal["object"] | ObjectTypeName,
        Field(
            alias="type",
            required=True,
            include=True,
            exclude=False,
            # const=True
        ),
    ] = "object"

    @validator("type_")
    def check_type(cls, v):
        if v is None:
            return "object"
        return v

    # | properties?
    # | The [properties](#property-declarations) that instances of this type can or must have.
    properties: "Optional[PropertiesDeclaration]" = None
    # | minProperties?
    # | The minimum number of properties allowed for instances of this type.
    minProperties: Optional[int] = None
    # | maxProperties?
    # | The maximum number of properties allowed for instances of this type.
    maxProperties: Optional[int] = None

    @root_validator
    def _check_min_vs_max_properties(cls, values: _ValuesType) -> _ValuesType:
        if "maxProperties" in values and "minProperties" in values:
            if (
                (_max_properties := values["maxProperties"]) is not None
                and (_min_properties := values["minProperties"]) is not None
                and _max_properties < _min_properties
            ):
                raise ConfigError(
                    "`maxProperties` may not be smaller then `minProperties`."
                )
        return values

    # | additionalProperties?
    # | A Boolean that indicates whether an object instance MAY contain [additional properties](#additional-properties).<br/><br/>
    # **Default:** `true`
    additionalProperties: bool = True

    name_: Optional[str] = None  # = OBJECT_TYPE_DEFAULT_NAME

    # | discriminator?
    # | Determines the concrete type of an individual object at runtime when, for example, payloads contain ambiguous types due to unions or inheritance.
    # The value must match the name of one of the declared `properties` of a type.
    # Unsupported practices are inline type declarations and [using `discriminator`](#using-discriminator) with non-scalar properties.
    discriminator: Optional[PropertyName] = None  # Only valid for named types

    @validator("discriminator", allow_reuse=True)
    def check_discriminator(cls, v, values):
        if "properties" in values and not v in values["properties"]:
            raise ValueError(
                f"{v} is not supported as discriminator. Acceptable values are {values['properties'].keys()}"
            )
        return v

    # | discriminatorValue?
    # | Identifies the declaring type.
    # Requires including a `discriminator` facet in the type declaration.
    # A valid value is an actual value that might identify the type of an individual object and is unique in the hierarchy of the type.
    # Inline type declarations are not supported.<br/><br/>
    # **Default:** The name of the type
    discriminatorValue: Optional[TypeName] = None  # Only valid for named types

    @validator("discriminatorValue", allow_reuse=True, always=True)
    def check_discriminatorValue(cls, v, values):
        if "discriminator" in values and values["discriminator"] is not None:
            # discriminator facet is needed for discriminatorValue
            if v is None and "name_" in values:
                return values["name_"]
        return v

    _debug = root_validator(pre=True, allow_reuse=True)(debug)

    class Config:
        allow_population_by_field_name = False
        extra = Extra.forbid

    @root_validator(pre=False)
    def _register_type(cls, values: _ValuesType) -> _ValuesType:
        if values["name_"]:
            _TYPE_DECLARATIONS.update({values["name_"]: values})
        return values

    def as_type(self) -> Type:
        """Return the type represented by the RAML definition.

        Returns:
            Type: Type described by the TypeDeclaration
        """

        def _root_property_validator(cls, values):
            for _name in values:
                # If a pattern property regular expression also matches an explicitly declared property, the explicitly declared property definition prevails.
                # If two or more pattern property regular expressions match a property name in an instance of the data type, the first one prevails.
                if _name in cls.__fields_set__:
                    ...  # TODO run field validator
                else:
                    ...
            # Moreover, if `additionalProperties` is `false` (explicitly or by inheritance) in a given type definition, then explicitly setting pattern properties in that definition is not allowed.
            # If `additionalProperties` is `true` (or omitted) in a given type definition, then pattern properties are allowed and further restrict the additional properties allowed in that type.

        class Config(pydantic.config.BaseConfig):
            extra = Extra.forbid if not self.additionalProperties else Extra.allow

        if not (self.properties or self.additionalProperties):
            logger.warning(
                f"No fields were defined and additional properties are not allowed. This might be an error"
            )

        _field_definitions: None | Dict[str, Any] = None
        if self.properties:
            _field_definitions = dict(self.properties)

        return create_model(
            getattr(self, "name_", "Object").capitalize() + "Instance",
            __config__=Config,
            field_definitions=_field_definitions,
        )

    @property
    def _properties(self: "ObjectType") -> Collection[str]:
        return getattr(self.properties, "keys", [])

    @property
    def _facets(self: Self) -> Collection[str]:
        return list(self.__fields_set__ - {"properties"})


register_type_declaration("ObjectType", ObjectType())
