from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from contextlib import suppress
from typing import Any
from typing import Dict
from typing import Iterable
from typing import Protocol
from typing import Sequence
from typing import Type
from typing import TYPE_CHECKING

from pydantic import BaseModel


if TYPE_CHECKING:
    from typing_extensions import Self


class TypeDeclarationProtocol(Protocol):
    """Protocol for objects representing type declarations."""

    @abstractmethod
    def schema(self: Self) -> Dict[str, Any]:
        ...
