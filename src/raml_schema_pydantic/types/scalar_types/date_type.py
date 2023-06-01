"""Module for RAML Date types."""
import datetime
import logging
from email.utils import parsedate_to_datetime
from time import gmtime
from time import strftime
from typing import Annotated
from typing import Any
from typing import Literal
from typing import Optional
from typing import Type
from typing import TYPE_CHECKING

from dateutil import parser
from pydantic import Field

from .._type_dict import register_type_declaration
from ..any_type import AnyType

if TYPE_CHECKING:
    from pydantic.fields import ModelField
    from pydantic.typing import CallableGenerator
    from typing_extensions import Self


logger = logging.getLogger(__name__)


class RFC3339DateOnly(datetime.date):
    """Type for fields representing the `date-only` type."""

    @classmethod
    def __get_validators__(cls) -> "CallableGenerator":
        """Yield validators for use with pydantic.

        Yields:
            Generator[AnyCallable, None, None]: Validators for the type
        """
        yield cls.validate_string_format

    def __str__(self) -> str:
        """Create the informal string representation.

        Returns:
            str: 'informal' string representation of the object.
        """
        return self.isoformat()

    @classmethod
    def validate_string_format(cls, v: "datetime.date | Self | str | Any") -> "Self":
        """Validate a provided value against the field type.

        Args:
            v (datetime.date | Self | str | Any): provided value

        Raises:
            TypeError: Exception for an unsupported type

        Returns:
            Self: Instance of class
        """
        if isinstance(v, datetime.date):
            return cls.fromisoformat(v.isoformat())
        if isinstance(v, str):
            return cls.fromisoformat(v)

        raise TypeError(f"Unsupported type {type(v)}")

    def __eq__(self: "Self", o: "datetime.date | Self | str | Any") -> bool:
        """Evaluate the equality of a type and a supported other input.

        Args:
            self (Self): type
            o (datetime.date | Self | str | Any): other input

        Returns:
            bool: equality of type and input
        """
        return str(self.validate_string_format(o)) == str(self)

    @classmethod
    def __modify_schema__(
        cls, field_schema: dict[str, Any], field: "ModelField | None"
    ):
        """Update the schema of a field specified as this type.

        Args:
            field_schema (dict[str, Any]): Schema of the field
            field (ModelField | None): Field in the model
        """
        field_schema["type"] = "string"
        field_schema["format"] = "date"


class RFC3339DateTimeOnly(datetime.datetime):
    """Type for fields representing the `datetime-only` type."""

    @classmethod
    def __get_validators__(cls) -> "CallableGenerator":
        """Yield validators for use with pydantic.

        Yields:
            Generator[AnyCallable, None, None]: Validators for the type
        """
        yield cls.validate_string_format

    def __str__(self) -> str:
        """Create the informal string representation.

        Returns:
            str: 'informal' string representation of the object.
        """
        return self.isoformat()

    @classmethod
    def validate_string_format(
        cls, v: "datetime.datetime | Self | str | Any"
    ) -> "Self":
        """Validate a provided value against the field type.

        Args:
            v (datetime.datetime | Self | str | Any): provided value

        Raises:
            TypeError: Exception for an unsupported type

        Returns:
            Self: Instance of class
        """
        if isinstance(v, datetime.datetime):
            return cls.fromisoformat(v.isoformat())
        if isinstance(v, str):
            return cls.fromisoformat(v)

        raise TypeError(f"Unsupported type {type(v)}")

    def __eq__(self: "Self", o: "datetime.datetime | Self | str | Any") -> bool:
        """Evaluate the equality of a type and a supported other input.

        Args:
            self (Self): type
            o (datetime.datetime | Self | str | Any): other input

        Returns:
            bool: equality of type and input
        """
        return str(self.validate_string_format(o)) == str(self)

    @classmethod
    def __modify_schema__(
        cls, field_schema: dict[str, Any], field: "ModelField | None"
    ):
        """Update the schema of a field specified as this type.

        Args:
            field_schema (dict[str, Any]): Schema of the field
            field (ModelField | None): Field in the model
        """
        field_schema["type"] = "string"
        field_schema["format"] = "date-time"


class RFC3339TimeOnly(datetime.time):
    """Type for fields representing the `time-only` type."""

    @classmethod
    def __get_validators__(cls) -> "CallableGenerator":
        """Yield validators for use with pydantic.

        Yields:
            Generator[AnyCallable, None, None]: Validators for the type
        """
        yield cls.validate_string_format

    def __str__(self) -> str:
        """Create the informal string representation.

        Returns:
            str: 'informal' string representation of the object.
        """
        return self.isoformat(timespec="seconds")

    @classmethod
    def validate_string_format(cls, v: "datetime.time | Self | str | Any") -> "Self":
        """Validate a provided value against the field type.

        Args:
            v (datetime.time | Self | str | Any): provided value

        Raises:
            TypeError: Exception for an unsupported type

        Returns:
            Self: Instance of class
        """
        if isinstance(v, datetime.time):
            return cls.fromisoformat(v.isoformat())
        if isinstance(v, (str, int)):
            try:
                return cls.fromisoformat(str(v))
            except ValueError:
                return cls.fromisoformat(
                    datetime.datetime.fromtimestamp(int(v)).time().isoformat()
                )

        raise TypeError(f"Unsupported type {type(v)}")

    def __eq__(self: "Self", o: "datetime.time | Self | str | Any") -> bool:
        """Evaluate the equality of a type and a supported other input.

        Args:
            self (Self): type
            o (datetime.time | Self | str | Any): other input

        Returns:
            bool: equality of type and input
        """
        return str(self.validate_string_format(o)) == str(self)

    @classmethod
    def __modify_schema__(
        cls, field_schema: dict[str, Any], field: "ModelField | None"
    ):
        """Update the schema of a field specified as this type.

        Args:
            field_schema (dict[str, Any]): Schema of the field
            field (ModelField | None): Field in the model
        """
        field_schema["type"] = "string"
        # TODO check if it shouldn't be `partial-time` according to https://datatracker.ietf.org/doc/html/rfc3339#section-5.6
        field_schema["format"] = "time"


class RFC3339DateTime(datetime.datetime):
    """Type for fields representing the `datetime` type formatted as RFC 3339."""

    @classmethod
    def __get_validators__(cls) -> "CallableGenerator":
        """Yield validators for use with pydantic.

        Yields:
            Generator[AnyCallable, None, None]: Validators for the type
        """
        yield cls.validate_string_format

    def __str__(self) -> str:
        """Create the informal string representation.

        Returns:
            str: 'informal' string representation of the object.
        """
        return self.isoformat(timespec="seconds")

    @classmethod
    def validate_string_format(
        cls, v: "datetime.datetime | Self | str | Any"
    ) -> "Self":
        """Validate a provided value against the field type.

        Args:
            v (datetime.datetime | Self | str | Any): provided value

        Raises:
            TypeError: Exception for an unsupported type

        Returns:
            Self: Instance of class
        """
        if isinstance(v, datetime.datetime):
            return cls.fromisoformat(v.isoformat())
        if isinstance(v, str):
            return cls.fromisoformat(parser.isoparse(v).isoformat())

        raise TypeError(f"Unsupported type {type(v)}")

    def __eq__(self: "Self", o: "datetime.datetime | Self | str | Any") -> bool:
        """Evaluate the equality of a type and a supported other input.

        Args:
            self (Self): type
            o (datetime.datetime | Self | str | Any): other input

        Returns:
            bool: equality of type and input
        """
        return str(self.validate_string_format(o)) == str(self)

    @classmethod
    def __modify_schema__(
        cls, field_schema: dict[str, Any], field: "ModelField | None"
    ):
        """Update the schema of a field specified as this type.

        Args:
            field_schema (dict[str, Any]): Schema of the field
            field (ModelField | None): Field in the model
        """
        field_schema["type"] = "string"
        field_schema["format"] = "date-time"


class RFC2616DateTime(datetime.datetime):
    """Type for fields representing the `datetime` type formatted as RFC 2616."""

    @classmethod
    def __get_validators__(cls) -> "CallableGenerator":
        """Yield validators for use with pydantic.

        Yields:
            Generator[AnyCallable, None, None]: Validators for the type
        """
        yield cls.validate_string_format

    def __str__(self) -> str:
        """Create the informal string representation.

        Returns:
            str: 'informal' string representation of the object.
        """
        # Source: https://docs.python.org/3/library/time.html#time.time
        return strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime())

    @classmethod
    def validate_string_format(
        cls, v: "datetime.datetime | Self | str | Any"
    ) -> "Self":
        """Validate a provided value against the field type.

        Args:
            v (datetime.datetime | Self | str | Any): provided value

        Raises:
            TypeError: Exception for an unsupported type

        Returns:
            Self: Instance of class
        """
        if isinstance(v, datetime.datetime):
            return cls.fromisoformat(v.isoformat())
        if isinstance(v, str):
            return cls.fromisoformat(parsedate_to_datetime(v).isoformat())

        raise TypeError(f"Unsupported type {type(v)}")

    def __eq__(self: "Self", o: "datetime.datetime | Self | str | Any") -> bool:
        """Evaluate the equality of a type and a supported other input.

        Args:
            self (Self): type
            o (datetime.datetime | Self | str | Any): other input

        Returns:
            bool: equality of type and input
        """
        return str(self.validate_string_format(o)) == str(self)

    @classmethod
    def __modify_schema__(
        cls, field_schema: dict[str, Any], field: "ModelField | None"
    ):
        """Update the schema of a field specified as this type.

        Args:
            field_schema (dict[str, Any]): Schema of the field
            field (ModelField | None): Field in the model
        """
        field_schema["type"] = "string"
        # TODO research correct format
        field_schema["format"] = "date-time"


# The following date type representations MUST be supported:
class DateOnlyType(AnyType):
    """The "full-date" notation of [RFC3339](http://xml2rfc.ietf.org/public/rfc/html/rfc3339.html#anchor14), namely `yyyy-mm-dd`."""

    type_: Annotated[
        Optional[Literal["date-only"]],
        Field(
            alias="type",
            required=True,
            include=True,
            exclude=False,
            const=True,
        ),
    ] = "date-only"

    # | date-only
    # | The "full-date" notation of [RFC3339](http://xml2rfc.ietf.org/public/rfc/html/rfc3339.html#anchor14), namely `yyyy-mm-dd`.
    # Does not support time or time zone-offset notation.

    def as_type(self) -> Type:
        """Return the type represented by the RAML definition.

        Returns:
            Type: Type described by the TypeDeclaration
        """
        return type("DateOnly", (RFC3339DateOnly,), {})


register_type_declaration("date-only", DateOnlyType())


class TimeOnlyType(AnyType):
    r"""The "partial-time" notation of [RFC3339](http://xml2rfc.ietf.org/public/rfc/html/rfc3339.html#anchor14), namely hh:mm:ss\[.ff...\]."""

    type_: Annotated[
        Optional[Literal["time-only"]],
        Field(
            alias="type",
            required=True,
            include=True,
            exclude=False,
            const=True,
        ),
    ] = "time-only"

    # | time-only
    # | The "partial-time" notation of [RFC3339](http://xml2rfc.ietf.org/public/rfc/html/rfc3339.html#anchor14), namely hh:mm:ss\[.ff...\].
    # Does not support date or time zone-offset notation.

    def as_type(self) -> Type:
        """Return the type represented by the RAML definition.

        Returns:
            Type: Type described by the TypeDeclaration
        """
        return type("TimeOnly", (RFC3339TimeOnly,), {})


register_type_declaration("time-only", TimeOnlyType())


class DateTimeOnlyType(AnyType):
    r"""Combined date-only and time-only with a separator of "T", namely yyyy-mm-ddThh:mm:ss\[.ff...\]."""

    type_: Annotated[
        Optional[Literal["datetime-only"]],
        Field(
            alias="type",
            required=True,
            include=True,
            exclude=False,
            const=True,
        ),
    ] = "datetime-only"

    # | datetime-only
    # | Combined date-only and time-only with a separator of "T", namely yyyy-mm-ddThh:mm:ss\[.ff...\].
    # Does not support a time zone offset.

    def as_type(self) -> Type:
        """Return the type represented by the RAML definition.

        Returns:
            Type: Type described by the TypeDeclaration
        """
        return type("DateTimeOnly", (RFC3339DateTimeOnly,), {})


register_type_declaration("datetime-only", DateTimeOnlyType())


class DateTimeType(AnyType):
    """A timestamp in either RFC3339 oder RFC2616 format."""

    type_: Annotated[
        Optional[Literal["datetime"]],
        Field(
            alias="type",
            required=True,
            include=True,
            exclude=False,
            const=True,
        ),
    ] = "datetime"

    # | datetime
    # | A timestamp in one of the following formats:
    # if the _format_ is omitted or set to `rfc3339`, uses the "date-time" notation of [RFC3339](http://xml2rfc.ietf.org/public/rfc/html/rfc3339.html#anchor14);
    # if _format_ is set to `rfc2616`, uses the format defined in [RFC2616](https://www.ietf.org/rfc/rfc2616.txt).

    # The additional facet `format` MUST be available only when the type equals `datetime`:

    # | format?
    # | The format of the value of a type `datetime`.
    # The value MUST be either `rfc3339` or `rfc2616`.
    # Any other values are invalid.
    format_: Annotated[
        Optional[Literal["rfc3339"] | Literal["rfc2616"]],
        Field(
            alias="format",
            required=False,
            include=True,
            exclude=False,
            const=False,
        ),
    ] = "rfc3339"

    def as_type(self) -> Type:
        """Return the type represented by the RAML definition.

        Returns:
            Type: Type described by the TypeDeclaration
        """
        if self.format_ == "rfc3339":
            return type("DateTime", (RFC3339DateTime,), {})
        else:
            return type("DateTime", (RFC2616DateTime,), {})


register_type_declaration("datetime", DateTimeType())
