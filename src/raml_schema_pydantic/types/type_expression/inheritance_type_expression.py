"""Module for inheritance expressions."""
# pyright: basic
#  #strict
import json
import logging
from sys import version_info
from typing import ForwardRef
from typing import List
from typing import TYPE_CHECKING
from typing import TypeVar

from pydantic import root_validator
from pydantic.main import BaseModel
from pydantic.utils import ROOT_KEY
from typing_extensions import deprecated

from ..._helpers import _ValuesType

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


logger = logging.getLogger(__name__)
LOG_LEVEL = logging.WARNING  # INFO


_T = TypeVar("_T")

TypeExpression = ForwardRef("TypeExpression")


@deprecated("This class is replaced by recursive parsing of the referenced types.")
class InheritanceExpression(BaseModel):  # noqa: ignore[D101]
    __root__: List["TypeExpression"]

    @root_validator
    def _check_length(cls, values: _ValuesType) -> _ValuesType:
        logger.warning(f"checking length for {values}")
        if values:
            assert (  # nosec
                len(values[ROOT_KEY]) > 1
            ), f"InheritanceExpression is only defined for more than one type"
            return values
        return values

    # If a sub-type inherits properties having the same name from at least two of its parent types, the sub-type SHALL keep all restrictions applied to those properties with two exceptions:
    #  1) a `pattern` facet when a parent type already declares a `pattern` facet
    #  2) a user-defined facet when another user-defined facet has the same value.
    #  In these cases, an invalid type declaration occurs.
    # TODO Implement validation logic

    def __repr__(self: Self) -> str:  # noqa: ignore[D105]
        return f"InheritanceExpression(__root__={self.__root__})"

    def __str__(self: Self) -> str:  # noqa: ignore[D105]
        return json.dumps(map(str, self.__root__))
