from __future__ import annotations

from abc import abstractclassmethod
from abc import abstractmethod
from typing import Any
from typing import Dict
from typing import Protocol
from typing import runtime_checkable
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from typing_extensions import Self
    from pydantic.typing import CallableGenerator


@runtime_checkable
class PydanticValidatable(Protocol):
    @abstractclassmethod
    def __get_validators__(cls) -> "CallableGenerator":
        ...


@runtime_checkable
class TypeDeclarationProtocol(PydanticValidatable, Protocol):
    """Protocol for objects representing type declarations."""

    @abstractmethod
    def schema(self: Self) -> Dict[str, Any]:
        ...

    @abstractclassmethod
    def __get_validators__(cls) -> "CallableGenerator":
        yield from []

    # def __iter__(self):
    #     print("Iter")
