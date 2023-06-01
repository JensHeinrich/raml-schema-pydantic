# pyright: basic
#  #strict
from __future__ import annotations

import json
import logging
from abc import abstractmethod
from collections import UserString
from sys import version_info
from typing import Any
from typing import ClassVar
from typing import Dict
from typing import List
from typing import Literal
from typing import Mapping
from typing import NoReturn
from typing import Optional
from typing import overload
from typing import Sequence
from typing import Tuple
from typing import Type
from typing import TYPE_CHECKING
from typing import TypeAlias
from typing import TypeVar
from typing import Union

from pydantic import errors as PydanticErrors
from pydantic import PydanticTypeError
from pydantic import PydanticValueError
from pydantic import root_validator
from pydantic import StrError
from pydantic.error_wrappers import ErrorList
from pydantic.error_wrappers import ErrorWrapper
from pydantic.fields import ModelField
from pydantic.main import BaseModel
from pydantic.utils import ROOT_KEY
from typing_extensions import deprecated
from typing_extensions import override

from .._errors import ValidationError
from .._helpers import _ValuesType
from .._helpers import debug
from .._helpers import debug_advanced
from ..types._IType import IType
from ._base_type_expression_type import BaseTypeExpressionType
from ._shunt import ITree  # , Tree
from ._shunt import Operator
from ._shunt import OperatorNode
from ._shunt import postfix_to_ast
from ._shunt import shunt
from ._shunt import ValueNode
from ._util import *
from .type_expression import TypeExpression

# prevent no-redef type errors, see https://github.com/python/mypy/issues/1153#issuecomment-1207333806
if TYPE_CHECKING:
    import regex as re
    from regex import Pattern

    from typing_extensions import Self
else:
    if version_info < (3, 11):
        import regex as re
        from regex import Pattern

        from typing_extensions import Self
    else:
        import re
        from re import Pattern

        from typing import Self


if TYPE_CHECKING:
    from pydantic.error_wrappers import ErrorList
    from pydantic.fields import ValidateReturn


logger = logging.getLogger(__name__)
LOG_LEVEL = logging.WARNING  # INFO


_T = TypeVar("_T")


class InheritanceExpression(BaseModel):
    __root__: List[
        TypeExpression
        # | BaseTypeExpressionTyped
    ]

    @root_validator
    def _check_length(cls, values: _ValuesType) -> _ValuesType:
        logger.warning(f"checking length for {values}")
        if values:
            assert (
                len(values[ROOT_KEY]) > 1
            ), f"InheritanceExpression is only defined for more than one type"
            return values
        return values

    # If a sub-type inherits properties having the same name from at least two of its parent types, the sub-type SHALL keep all restrictions applied to those properties with two exceptions:
    #  1) a `pattern` facet when a parent type already declares a `pattern` facet
    #  2) a user-defined facet when another user-defined facet has the same value.
    #  In these cases, an invalid type declaration occurs.

    # def as_type(self) -> Type:
    #     ...

    def __repr__(self: Self) -> str:
        return f"InheritanceExpression(__root__={self.__root__})"

    def __str__(self: Self) -> str:
        return json.dumps(map(str, self.__root__))
