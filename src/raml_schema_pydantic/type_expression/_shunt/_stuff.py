from abc import abstractmethod
from typing import List
from typing import Type
from typing import Union

from pydantic import BaseModel
from typing_extensions import Self

from .ast import *
from .util import *


class Tree(BaseModel, ITree):
    __root__: Union[
        ValueNode,
        OperatorNode,  # needed explicitly to have pydantic check against both
    ]

    def as_dot(self) -> str:
        return self.__root__.as_dot()

    @property
    def nodename(self) -> str:
        return self.__root__.nodename

    def draw(self):
        return f"""
            digraph {{

                {self.__root__.as_dot()}
            }}
            """

    def __repr__(self: Self) -> str:
        return f"Tree(__root__={self.__root__.__repr__()})"

    def __str__(self) -> str:
        return str(self.__root__)

    @property
    def children(self) -> List[Type[INode]] | None:
        return getattr(self.__root__, "children", None)


class Node(INode):
    def as_dot(self) -> str:
        raise NotImplementedError("`as_dot` not implemented")

    @property
    @abstractmethod
    def nodename(self) -> str:
        ...

    @classmethod
    def validate_root_type(cls, values):
        if issubclass(type(values), Node):
            return values
        raise TypeError("Invalid root type")

    @classmethod
    def __get_validators__(cls):
        yield cls.validate_root_type

    @abstractmethod
    def __str__(self) -> str:
        raise NotImplementedError("`__str__` is not implemented")
