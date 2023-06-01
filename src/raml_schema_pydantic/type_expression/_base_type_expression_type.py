from __future__ import annotations

import logging
from abc import ABC
from abc import abstractmethod
from sys import version_info
from typing import Any
from typing import Generator
from typing import Optional
from typing import Protocol
from typing import Type
from typing import TYPE_CHECKING

from pydantic import PydanticTypeError
from pydantic.fields import ModelField
from typing_extensions import Self

from .._helpers import debug
from ..pydantic_interface import PydanticValidatable
from ..types._IType import IType

# prevent no-redef type errors, see https://github.com/python/mypy/issues/1153#issuecomment-1207333806
if TYPE_CHECKING:
    from ..pydantic_interface import ValidatorCallable

    pass
else:
    if version_info.major == 3 and version_info.minor >= 11:
        pass
    else:
        pass

if TYPE_CHECKING:
    from pydantic.fields import ValidateReturn


logger = logging.getLogger(__name__)
LOG_LEVEL = logging.WARNING  # INFO


# class BaseTypeExpressionType(PydanticValidatable, Protocol):
# class BaseTypeExpressionType(Protocol):
class BaseTypeExpressionType(IType):
    """Base class for TypeExpressions."""

    # __config__ = None

    # # @abstractmethod
    # def __init__(self, *args, **kwargs) -> None:
    #     super().__init__(*args, **kwargs)

    @classmethod
    @abstractmethod
    def validator(
        cls, v: str | Type[Self] | Any, field: Optional[ModelField] = None
    ) -> "ValidateReturn":
        raise NotImplementedError("validate not implemented for meta class")

    @classmethod
    @abstractmethod
    def validate(cls, v: Any) -> Self:
        raise NotImplementedError("validator not implemented for meta class")

    @abstractmethod
    def __eq__(self: Self, other: BaseTypeExpressionType | str | Any) -> bool:
        ...

    @abstractmethod
    def __str__(self: Self) -> str:
        ...

    @abstractmethod
    def __repr__(self: Self) -> str:
        # return f"XXX{self.__class__}({self.__str__()})"
        ...

    # @classmethod
    # def __get_validators__(
    #     cls,
    # ) -> Generator[ValidatorCallable, None, None]:
    #     if isinstance(cls, BaseTypeExpressionType):
    #         # raise NotImplementedError("validators not implemented for meta class")
    #         logger.log(
    #             level=LOG_LEVEL,
    #             msg="`__get_validators__` is not implemented for metaclass",
    #         )
    #     else:
    #         yield debug
    #         yield cls.validator
    #         yield debug

    # @classmethod
    # def parse_obj(cls, obj: str | Any) -> Self:
    #     logger.log(level=LOG_LEVEL, msg=f"Parsing {obj} to {cls.__qualname__}")
    #     if isinstance(obj, str):
    #         return cls(obj)
    #     elif isinstance(obj, cls):
    #         return obj
    #     raise PydanticTypeError(
    #         loc=f"{cls.__qualname__}",
    #         msg=f"Only stringlike objects are supported, was given {obj}",
    #     )
