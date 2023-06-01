"""Module for type declarations."""
# A type declaration references another type, or wraps or extends another type by adding functional facets (e.g. properties) or non-functional facets (e.g. a description), or is a type expression that uses other types.
# Here are the facets that all type declarations can have;
# certain type declarations might have other facets:
import logging
from abc import abstractmethod
from typing import Annotated
from typing import Any
from typing import ForwardRef
from typing import Generic
from typing import List
from typing import Mapping
from typing import Optional
from typing import overload
from typing import Type
from typing import TYPE_CHECKING
from typing import TypeAlias
from typing import Union

from pydantic import BaseModel
from pydantic import Extra
from pydantic import Field
from pydantic import root_validator
from pydantic import validator
from pydantic.generics import GenericModel
from typing_extensions import Self

from .._config import DefaultConfig
from .._helpers import _ValuesType
from .._helpers import debug
from .._helpers import debug_advanced
from .._helpers import deprecate_schema_key
from .._helpers import gather_annotations
from .._helpers import mutually_exclusive_schema_and_type
from .._types import _T
from .._types import Facets
from .._types import JsonSchema
from .._types import XMLType
from ..examples import Example
from ..examples import Examples
from ..xml_serialization import XMLSerialization
from ._IType import IType


if TYPE_CHECKING:
    from pydantic.main import Model
# from ..annotations import Annotations

# from .data_type_declaration import BuiltinDataType
# BuiltinDataType = ForwardRef("BuiltinDataType")


# Annotations = ForwardRef("Annotations", is_class=True)


class Annotations(str):
    pass


logger = logging.getLogger(__name__)
LOG_LEVEL = logging.WARNING


class GenericTypeDeclaration(
    GenericModel,
    Generic[_T]
    # BaseModel
):
    name_: Annotated[
        Optional[str],
        Field(
            exclude=True,
        ),
    ] = None

    # | default?
    # | A default value for a type.
    # When an API request is completely missing the instance of a type, for example when a query parameter described by a type is entirely missing from the request, then the API must act as if the API client had sent an instance of that type with the instance value being the value in the default facet.
    # Similarly, when the API response is completely missing the instance of a type, the client must act as if the API server had returned an instance of that type with the instance value being the value in the default facet.
    # A special case is made for URI parameters: for these, the client MUST substitute the value in the default facet if no instance of the URI parameter was given.
    default: Optional[
        _T
        # _Type
    ] = None

    # | schema?
    # | An alias for the equivalent "type" facet for compatibility with RAML 0.8.
    # Deprecated - API definitions SHOULD use the "type" facet because the "schema" alias for that facet name might be removed in a future RAML version.
    # The "type" facet supports XML and JSON schemas.
    schema_: Annotated[
        "Optional[TypeName]",
        Field(
            alias="schema",
            include=False,
            exclude=True,
        ),
    ] = None
    _deprecate_schema_key = root_validator(pre=True)(deprecate_schema_key)

    # | type?
    # | The type which the current type extends or just wraps.
    # The value of a type node MUST be either
    # a) the name of a user-defined type or
    # b) the name of a built-in RAML data type (object, array, or one of the scalar types) or
    # c) an inline type declaration.
    type_: Annotated[
        Optional[
            Union[
                "TypeExpression",
                # TypeName,
                # | GenericTypeDeclaration  # TypeDeclaration
                # | BuiltinTypeName
                # BuiltinDataType,
                XMLType,
                JsonSchema,
            ]
            # GenericTypeDeclaration[_T]
        ],
        Field(
            alias="type",
        ),
    ] = None
    # The "schema" and "type" facets are mutually exclusive and synonymous: processors MUST NOT allow both to be specified, explicitly or implicitly, inside the same type declaration.
    _mutually_exclusive_schema_and_type = root_validator(pre=True)(
        mutually_exclusive_schema_and_type
    )

    # | example?
    # | An example of an instance of this type that can be used, for example, by documentation generators to generate sample values for an object of this type.
    # The "example" facet MUST NOT be available when the "examples" facet is already defined.
    # See section [Examples](#defining-examples-in-raml) for more information.
    example: Optional[Example] = None

    # | examples?
    # |  Examples of instances of this type.
    # This can be used, for example, by documentation generators to generate sample values for an object of this type.
    # The "examples" facet MUST NOT be available when the "example" facet is already defined.
    # See section [Examples](#defining-examples-in-raml) for more information.
    examples: Optional[Examples] = None

    # | displayName?
    # | An alternate, human-friendly name for the type

    # | description?
    # | A substantial, human-friendly description of the type.
    # Its value is a string and MAY be formatted using [markdown](#markdown).

    # | (&lt;annotationName&gt;)?
    # | [Annotations](#annotations) to be applied to this API.
    # An annotation is a map having a key that begins with "(" and ends with ")" where the text enclosed in parentheses is the annotation name, and the value is an instance of that annotation.
    annotations_: "Optional[Annotations]" = None
    _gather_annotations = root_validator(pre=True, allow_reuse=True)(gather_annotations)

    # | facets?
    # | A map of additional, user-defined restrictions that will be inherited and applied by any extending subtype.
    # See section [User-defined Facets](#user-defined-facets) for more information.

    # | xml?
    # | The capability to configure [XML serialization of this type instance](#xml-serialization-of-type-instances).
    xml: Optional[XMLSerialization] = None

    # | enum?
    # | An enumeration of all the possible values of instances of this type.
    # The value is an array containing representations of these possible values; an instance of this type MUST be equal to one of these values.

    _debug_pre = root_validator(pre=True, allow_reuse=True)(
        lambda cls, values: debug_advanced(
            cls=cls, values=values, pre=True, caller="GenericTypeDeclaration"
        )
    )
    _debug_post = root_validator(pre=False, allow_reuse=True)(
        lambda cls, values: debug_advanced(
            cls=cls, values=values, pre=False, caller="GenericTypeDeclaration"
        )
    )

    @validator("examples", always=True, check_fields=False)  # FIXME
    def mutually_exclusive_example_and_examples(cls, v, values):
        if "example" in values and values["example"] is not None and v:
            raise ValueError("'example' and 'examples' are mutually exclusive.")
        return v

    _debug = root_validator(pre=True, allow_reuse=True)(debug)

    # def __eq__(self, other: GenericTypeDeclaration):
    #     # if other.__parameters__ == _T:
    #     #     return all(
    #     #         self[_key] == other[_key] for _key in self.key if _key not in ["type_"]
    #     #     )

    #     return False

    # ### Determine Default Types

    @validator("type_")
    def determine_default_type(
        cls,
        v,
        values,
    ):
        # A RAML processor MUST be able to determine the default type of a type declaration by using the following rules:

        # * If, and only if, a type declaration contains a facet that is unique to that type, its default type is then inferred to be the only one with support for the facet being used.

        # For example, if a type declaration contains a `properties` facet, its default type is `object`. The following snippet exemplifies this rule:

        # ```yaml
        # types:
        #   Person:
        #     # default type is "object" because "properties" is unique to that type
        #     # i.e. no need to explicitly define it, "type: object" is inferred
        #     properties:
        # ```

        # * If, and only if, a type declaration contains a facet that is neither unique to a given type, as described in the previous rule above, nor a `type` or `schema` facet, then the default type is `string`. The following snippet exemplifies this rule:

        # ```yaml
        # types:
        #   Person:
        #     properties:
        #       name: # no type or schema necessary since the default type is `string`
        # ```

        # * The default type `any` is applied to any `body` node that does not contain `properties`, `type`, or `schema`. For example:

        # ```yaml
        # body:
        #   application/json:
        #     # default type is `any`
        # ```

        # Or, if a default media type has been defined, no need to declare it here:

        # ```yaml
        # body:
        #   # default type is `any`
        # ```

        # Of course, each rule can be overridden by explicitly defining a type. For example:

        return v

    @root_validator
    def _register_type(cls, values: _ValuesType) -> _ValuesType:
        if "name_" in values or "name_" in values:
            ...
        return values

    class Config(DefaultConfig):
        # allow_population_by_field_name = True
        extra = Extra.allow


class ITypeDeclaration(
    # BaseModel,
    IType
):
    name_: Annotated[
        Optional[str],
        Field(
            exclude=True,
        ),
    ] = None

    # | default?
    # | A default value for a type.
    # When an API request is completely missing the instance of a type, for example when a query parameter described by a type is entirely missing from the request, then the API must act as if the API client had sent an instance of that type with the instance value being the value in the default facet.
    # Similarly, when the API response is completely missing the instance of a type, the client must act as if the API server had returned an instance of that type with the instance value being the value in the default facet.
    # A special case is made for URI parameters: for these, the client MUST substitute the value in the default facet if no instance of the URI parameter was given.
    default: Optional[
        Any
        # _Type
    ] = None

    # | schema?
    # | An alias for the equivalent "type" facet for compatibility with RAML 0.8.
    # Deprecated - API definitions SHOULD use the "type" facet because the "schema" alias for that facet name might be removed in a future RAML version.
    # The "type" facet supports XML and JSON schemas.
    schema_: Annotated[
        Optional[str],
        Field(
            alias="schema",
            include=False,
            exclude=True,
        ),
    ] = None
    _deprecate_schema_key = root_validator(pre=True, allow_reuse=True)(
        deprecate_schema_key
    )

    # | type?
    # | The type which the current type extends or just wraps.
    # The value of a type node MUST be either
    # a) the name of a user-defined type or
    # b) the name of a built-in RAML data type (object, array, or one of the scalar types) or
    # c) an inline type declaration.
    type_: Annotated[
        Optional[
            Union[
                "TypeExpression",
                # TypeName,
                # | GenericTypeDeclaration  # TypeDeclaration
                # | BuiltinTypeName
                # BuiltinDataType,
                XMLType,
                JsonSchema,
            ]
            # GenericTypeDeclaration[_T]
        ],
        Field(
            alias="type",
        ),
    ] = None
    # The "schema" and "type" facets are mutually exclusive and synonymous: processors MUST NOT allow both to be specified, explicitly or implicitly, inside the same type declaration.
    _mutually_exclusive_schema_and_type = root_validator(pre=True, allow_reuse=True)(
        mutually_exclusive_schema_and_type
    )

    # | example?
    # | An example of an instance of this type that can be used, for example, by documentation generators to generate sample values for an object of this type.
    # The "example" facet MUST NOT be available when the "examples" facet is already defined.
    # See section [Examples](#defining-examples-in-raml) for more information.
    example: Optional[Example] = None

    # | examples?
    # |  Examples of instances of this type.
    # This can be used, for example, by documentation generators to generate sample values for an object of this type.
    # The "examples" facet MUST NOT be available when the "example" facet is already defined.
    # See section [Examples](#defining-examples-in-raml) for more information.
    examples: Optional[Examples] = None

    # | displayName?
    # | An alternate, human-friendly name for the type

    # | description?
    # | A substantial, human-friendly description of the type.
    # Its value is a string and MAY be formatted using [markdown](#markdown).

    # | (&lt;annotationName&gt;)?
    # | [Annotations](#annotations) to be applied to this API.
    # An annotation is a map having a key that begins with "(" and ends with ")" where the text enclosed in parentheses is the annotation name, and the value is an instance of that annotation.
    annotations_: "Optional[Annotations]" = None
    _gather_annotations = root_validator(pre=True, allow_reuse=True)(gather_annotations)

    # | facets?
    # | A map of additional, user-defined restrictions that will be inherited and applied by any extending subtype.
    # See section [User-defined Facets](#user-defined-facets) for more information.
    facets: Optional[Facets] = None
    # | xml?
    # | The capability to configure [XML serialization of this type instance](#xml-serialization-of-type-instances).
    xml: Optional[XMLSerialization] = None

    # | enum?
    # | An enumeration of all the possible values of instances of this type.
    # The value is an array containing representations of these possible values; an instance of this type MUST be equal to one of these values.
    enum: Optional[List[Any]] = None

    _debug_pre = root_validator(pre=True, allow_reuse=True)(
        lambda cls, values: debug_advanced(
            cls=cls, values=values, pre=True, caller="GenericTypeDeclaration"
        )
    )
    _debug_post = root_validator(pre=False, allow_reuse=True)(
        lambda cls, values: debug_advanced(
            cls=cls, values=values, pre=False, caller="GenericTypeDeclaration"
        )
    )

    @validator("examples", always=True, check_fields=False)  # FIXME
    def mutually_exclusive_example_and_examples(cls, v, values):
        if "example" in values and values["example"] is not None and v:
            raise ValueError("'example' and 'examples' are mutually exclusive.")
        return v

    _debug = root_validator(pre=True, allow_reuse=True)(debug)

    @overload
    def __eq__(self: Self, other: Self | Mapping[str, Any]) -> bool:
        ...

    @overload
    def __eq__(self: Self, other: object) -> bool:
        ...

    def __eq__(self: Self, other: object | Type[Self] | Mapping[str, Any]) -> bool:
        logger.warning(f"Comparing {self.__repr__()} to {other.__repr__()}")
        # if other.__parameters__ == _T:
        #     return all(
        #         self[_key] == other[_key] for _key in self.key if _key not in ["type_"]
        #     )

        if isinstance(other, IType):
            return self.as_type() == other.as_type()

        # TODO prevent different TypeDeclarations from being compared
        if isinstance(other, type(self)):
            if dict(self) == dict(other):
                return True

        # FIXME
        if self.__repr__() == other.__repr__():
            return True

        return False

    # @abstractmethod
    # def as_type(self) -> Type:
    #     ...
    # return self.schema_json(by_alias=False)

    # class Config(DefaultConfig):
    #     # allow_population_by_field_name = True
    #     extra = Extra.allow

    @root_validator
    def _register_type(cls, values: _ValuesType) -> _ValuesType:
        if "name_" in values or "name_" in values:
            logger.warning(f"Registering {values['name_']} as type")

        return values

    def type_name(self) -> str:
        return self.name_ or str(id(self))


class TypeDeclaration(BaseModel, ITypeDeclaration):
    # ### Determine Default Types

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls: Type["Model"], value: Any) -> "Model":
        return super().validate(value)

    # A RAML processor MUST be able to determine the default type of a type declaration by using the following rules:

    # * If, and only if, a type declaration contains a facet that is unique to that type, its default type is then inferred to be the only one with support for the facet being used.

    # For example, if a type declaration contains a `properties` facet, its default type is `object`. The following snippet exemplifies this rule:

    # ```yaml
    # types:
    #   Person:
    #     # default type is "object" because "properties" is unique to that type
    #     # i.e. no need to explicitly define it, "type: object" is inferred
    #     properties:
    # ```

    # * If, and only if, a type declaration contains a facet that is neither unique to a given type, as described in the previous rule above, nor a `type` or `schema` facet, then the default type is `string`. The following snippet exemplifies this rule:

    # ```yaml
    # types:
    #   Person:
    #     properties:
    #       name: # no type or schema necessary since the default type is `string`
    # ```

    # * The default type `any` is applied to any `body` node that does not contain `properties`, `type`, or `schema`. For example:

    # ```yaml
    # body:
    #   application/json:
    #     # default type is `any`
    # ```

    # Or, if a default media type has been defined, no need to declare it here:

    # Of course, each rule can be overridden by explicitly defining a type. For example:


# class TypeDeclaration(
#     GenericTypeDeclaration
#     #[_Type]
#     ):


#     @root_validator(pre=True, allow_reuse=True)
#     def _debug(cls, values):
#         print(f"Creating {cls.__name__} using {values}")
#         return values

#     @root_validator(pre=False, allow_reuse=True)
#     def _debug_post(cls, values):
#         print(f"Creating {cls.__name__} using {values}")
#         return values

#     def __eq__(self, other: TypeDeclaration):
#         return False

# TypeDeclaration: TypeAlias = GenericTypeDeclaration
# class TypeDeclaration(GenericTypeDeclaration):
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args,**kwargs)

from ..type_expression.type_name import TypeName
from ..type_expression.type_expression import TypeExpression

# TypeDeclaration = GenericTypeDeclaration[Any]

GenericTypeDeclaration.update_forward_refs()

# ITypeDeclaration.update_forward_refs()


# TypeDeclaration = GenericTypeDeclaration[_Type]
#: TypeDeclaration used inline instead of in Types Mapping
IInlineTypeDeclaration: TypeAlias = ITypeDeclaration


### Inline Type Declarations
# class InlineTypeDeclaration(TypeDeclaration):
#     # You MAY declare inline/anonymous types everywhere a type can be referenced except in a Type Expression.
#     name_: Annotated[
#         Optional[None],
#         Field(
#             exclude=True,
#             required=False,
#             const=True,
#         )
#     ] = None


TypeDeclaration.update_forward_refs()
