"""Module for RAML File types."""
import base64
import binascii
import logging
from typing import Annotated
from typing import Any
from typing import Collection
from typing import List
from typing import Literal
from typing import Optional
from typing import Sequence
from typing import Type
from typing import TYPE_CHECKING

from pydantic import ConstrainedBytes
from pydantic import Field
from pydantic.error_wrappers import ErrorWrapper
from pydantic.types import _registered
from typing_extensions import Self

from ...MediaType import MediaType
from .._type_dict import register_type_declaration
from ..any_type import AnyType

if TYPE_CHECKING:
    from pydantic.fields import ModelField
    from pydantic.typing import CallableGenerator
    from typing_extensions import Self


logger = logging.getLogger(__name__)


class ConstrainedFile(ConstrainedBytes):
    """Type for fields represented by the `file` type."""

    content_types: List[MediaType]
    # File content SHOULD be a base64-encoded string.
    format: Literal["base64"] | Literal["binary"] = "base64"

    @classmethod
    def __get_validators__(cls) -> "CallableGenerator":
        """Yield validators for use with pydantic.

        Yields:
            Generator[AnyCallable, None, None]: Validators for the type
        """
        # handle encoding
        yield cls.validate_encoding
        # handle byte properties
        yield from ConstrainedBytes.__get_validators__()
        # handle content type
        yield cls.validate_content_type

    def __str__(self) -> str:
        """Create the informal string representation.

        Returns:
            str: 'informal' string representation of the object.
        """
        return super().__str__()

    def __repr__(self) -> str:
        """Create the official string representation.

        Returns:
            str: 'official' string representation of the object.
        """
        return f"FileTypeType(content_types='{self.content_types}', format='{self.format}', )"

    @classmethod
    def validate_all(cls, v: "str | bytes | Self") -> "Self":
        """Run all validators for the provided type.

        Args:
            v (str | bytes | Self): value to coerce into the type

        Raises:
            TypeError: Exception for incoercible type

        Returns:
            Self: Type
        """
        _errors: List[ErrorWrapper] = []
        for validator in cls.__get_validators__():
            try:
                v = validator(v)
            except (TypeError, AssertionError, ValueError) as exc:
                _errors.append(ErrorWrapper(exc=exc, loc=validator.__name__))

        if not isinstance(v, ConstrainedFile):
            raise TypeError(f"{str(v)} could not be coerced into {type(cls)}")

        return v  # type: ignore[return-value] # FIXME

    @classmethod
    def validate_encoding(
        cls, v: "ConstrainedBytes | bytes | Self", field: "ModelField"
    ) -> "Self | bytes | ConstrainedBytes":
        """Validate the encoding of the provided file.

        Args:
            v (ConstrainedBytes | bytes | Self): value
            field (ModelField): model field containing additional information

        Raises:
            TypeError: Exception for wrong encoding
            TypeError: Exception for unsupported type

        Returns:
            Self| bytes | ConstrainedBytes: bytes-like object
        """

        if field and (_encoding := field.field_info.extra["encoding"]):
            try:
                if _encoding == "base64":
                    if isinstance(v, str):
                        # a string needs to be decoded to bytes
                        logger.info("Trying to decode base64 string to bytes")
                        v = base64.b64decode(v)
                if _encoding == "binary":
                    logger.warning("Can not validate encoding for encoding `binary`.")
            except binascii.Error as exc:
                raise TypeError("Wrong encoding") from exc

        else:
            logger.warning(f"Can not validate encoding for {str(v)}")

        if not isinstance(
            v,
            (bytes, ConstrainedBytes, ConstrainedFile),
        ):
            raise TypeError(f"Unsupported type {type(v)}")

        return v

    @classmethod
    def validate_content_type(
        cls, v: "bytes | Self | ConstrainedFile", field: "ModelField"
    ) -> "Self":
        """Validate the content type of the provided file.

        Args:
            v ( bytes | Self| ConstrainedFile): value
            field (ModelField): model field containing additional information

        Raises:
            TypeError: Exception for wrong content type
            TypeError: Exception for unsupported type

        Returns:
            Self: Instance of the class
        """
        if field:
            content_types: None | List[MediaType] = field.field_info.extra["file_types"]
            if content_types:
                _content_type: str | MediaType = getattr(v, "content_type", "*/*")

                if _content_type not in set(
                    str(content_type) for content_type in content_types
                ) | {"*/*"}:
                    raise TypeError(f"Wrong content type {_content_type}")

        if isinstance(v, bytes):
            v = cls(v)
        if isinstance(v, ConstrainedFile):
            return v

        raise TypeError(f"Unsupported type {type(v)}")

    def __eq__(self: "Self", o: "bytes | Self | Any") -> bool:
        """Evaluate the equality of a type and a supported other input.

        Args:
            self (Self): type
            o (bytes | Self | Any): other input

        Returns:
            bool: equality of type and input
        """
        return str(self.validate_all(o)) == str(self)

    @classmethod
    def __modify_schema__(
        cls, field_schema: dict[str, Any], field: "ModelField | None" = None
    ):
        """Update the schema of a field specified as this type.

        Args:
            field_schema (dict[str, Any]): Schema of the field.
            field (ModelField | None): Field in the model. Defaults to None.
        """
        super().__modify_schema__(field_schema=field_schema)
        field_schema["type"] = "string"
        if field:
            field_schema["format"] = field.field_info.extra["encoding"]


def confile(
    *,
    min_length: Optional[int] = None,
    max_length: Optional[int] = None,
    content_types: Optional[List[MediaType]] = None,
    format: Literal["base64"] | Literal["binary"] | None = None,
) -> Type[bytes]:
    """Create a new type for the constrained file.

    Args:
        min_length (Optional[int], optional): minimum length in bytes. Defaults to None.
        max_length (Optional[int], optional): maximum length in bytes. Defaults to None.
        content_types (Optional[List[MediaType]], optional): MIME Type. Defaults to None.
        format (Literal[&quot;base64&quot;] | Literal[&quot;binary&quot;] | None, optional): encoding of the file. Defaults to None.

    Returns:
        Type[bytes]: Constrained file
    """
    # use kwargs then define conf in a dict to aid with IDE type hinting
    namespace = dict(
        min_length=min_length,
        max_length=max_length,
        content_types=content_types,
        format=format,
    )
    return _registered(type("ConstrainedFileValue", (ConstrainedFile,), namespace))


class FileType(AnyType):
    """The ​**file**​ type can constrain the content to send through forms."""

    # The ​**file**​ type can constrain the content to send through forms.
    # When this type is used in the context of web forms it SHOULD be represented as a valid file upload in JSON format.
    # File content SHOULD be a base64-encoded string.

    type_: Annotated[
        Optional[Literal["file"]],
        Field(
            alias="type",
            required=True,
            include=True,
            exclude=False,
            const=True,
        ),
    ] = "file"

    # | fileTypes?
    # | A list of valid content-type strings for the file.
    # The file type `*/*` MUST be a valid value.
    fileTypes: Optional[List[MediaType]] = []  # noqa: N815

    # | minLength?
    # | Specifies the minimum number of bytes for a parameter value.
    # The value MUST be equal to or greater than 0.
    # <br /><br />**Default:** `0`
    minLength: int = Field(default=0, ge=0)  # noqa: N815

    # | maxLength?
    # | Specifies the maximum number of bytes for a parameter value.
    # The value MUST be equal to or greater than 0.<br /><br />
    # **Default:** `2147483647`
    maxLength: int = Field(default=2147483647, ge=0)  # noqa: N815

    def as_type(self) -> Type:
        """Return the type represented by the RAML definition.

        Returns:
            Type: Type described by the TypeDeclaration
        """
        return confile(
            min_length=self.minLength,
            max_length=self.maxLength,
            content_types=self.fileTypes or [MediaType("*/*")],
        )

    @property
    def _facets(self) -> Collection[str]:
        return (
            {
                "minLength",
                "maxLength",
            }
            | {"fileTypes"}
            if self.fileTypes != []
            else {}
        )

    @property
    def _properties(self: Self) -> Sequence[str]:
        return ()


register_type_declaration("datetime-only", FileType())
