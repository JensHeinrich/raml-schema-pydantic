# pyright: basic
#  #strict
import logging
from sys import version_info
from typing import Any
from typing import Dict
from typing import ForwardRef
from typing import overload
from typing import Sequence
from typing import Tuple
from typing import Type
from typing import TYPE_CHECKING
from typing import TypeVar

from pydantic import errors as PydanticErrors
from pydantic import PatternError
from pydantic import StrError
from pydantic.error_wrappers import ErrorList
from typing_extensions import override

from .._errors import ValidationError
from ..types._TypeDeclarationProtocol import TypeDeclarationProtocol
from ._base_type_expression_type import BaseTypeExpressionType
from ._shunt import ITree  # , Tree
from ._shunt import OperatorNode
from ._shunt import Token
from ._util import OPERATOR_NOOP

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
    from pydantic.fields import ValidateReturn


logger = logging.getLogger(__name__)
LOG_LEVEL = logging.WARNING  # INFO


_T = TypeVar("_T")

from .type_expression import TypeExpression

# TypeExpression = ForwardRef("TypeExpression", is_class=True)


class NestedTypeExpression(
    # BaseTypeExpressionType,
    OperatorNode[Token, Token],
    TypeDeclarationProtocol,
):
    # | `(type expression)`
    # | Parentheses disambiguate the expression to which an operator applies.
    # |
    # `Person \| Animal[]` <br><br>
    # `( Person \| Animal )[]`

    inner: TypeExpression
    # op: ClassVar[Operator] = OPERATOR_NOOP

    def __repr__(self) -> str:
        return f"NestedTypeExpression({self.__str__()})"

    @overload
    def __init__(self, seq: str) -> None:
        ...

    @overload
    def __init__(self, seq: TypeExpression) -> None:
        ...

    # @overload
    # def __init__(
    #     self,
    #     seq: ArrayTypeExpression
    #     | UnionTypeExpression
    #     | TypeName
    #     | NestedTypeExpression,
    # ) -> None:
    #     ...

    def __init__(
        self,
        # seq: object | TypeExpressionType | TypeExpression
        seq: (
            # object
            # | ArrayTypeExpression
            # | UnionTypeExpression
            # | TypeName
            # | NestedTypeExpression
            # |
            TypeExpression
            | str
        ),
    ) -> None:
        _inner: TypeExpression
        _seq: str
        if isinstance(seq, TypeExpression):
            _seq = f"({seq})"
            _inner = seq
        elif isinstance(seq, BaseTypeExpressionType):
            _inner = TypeExpression(seq)
            _seq = f"({seq})"
        elif isinstance(seq, str):
            _inner = self._extract_and_parse_inner(str(seq))
            if not (seq.strip().startswith("(") and seq.strip().endswith(")")):
                raise PatternError(
                    msg_template="Expression needs to start with `(` and end with `)`"
                )
            _seq = seq
        else:
            raise TypeError(f"Unknown type {type(seq)} for {seq}")

        self.inner = _inner
        super(
            # OperatorNode,  # [Token, Token],
            # self,
        ).__init__(
            # seq=_seq,
            **dict(OPERATOR_NOOP),
            # symbol=Token("NOOP"),
            children=[_inner],
            # op=self.op,
        )

    _regex: Pattern[str] = re.compile(r"^\s*\((?P<inner>.*)\)\s*$")

    def __str__(self):
        return f"({str(self.inner)})"

    @classmethod
    def _extract_and_parse_inner(cls, v: str) -> TypeExpression:
        _match = cls._regex.fullmatch(v)
        if not _match:
            print(v)
            raise PydanticErrors.StrRegexError(pattern=cls._regex.pattern)

        _inner = _match.groupdict()["inner"]
        return TypeExpression.parse_obj(_inner)

    @override
    @classmethod
    def validate(
        cls: Type[Self],
        v: Any
        # , field: Optional[ModelField] = None
    ) -> "Tuple[Self, None] | Tuple[None, ErrorList]":  # "ValidateReturn":
        if isinstance(v, str):
            inner = cls._extract_and_parse_inner(v)
            return cls(inner), None
        elif isinstance(v, cls):
            return v, None
        return None, [StrError]

    @classmethod
    def validator(cls, v: Any) -> "NestedTypeExpression":
        _instance, _errors = cls.validate(v)
        if _errors is not None:
            raise ValidationError(errors=_errors, model=cls)
        assert isinstance(_instance, NestedTypeExpression)  # nosec: ignore[assert_used]
        return _instance

    def __eq__(
        self: Self, other: Self | BaseTypeExpressionType | TypeExpression | str | Any
    ) -> bool:
        if isinstance(other, NestedTypeExpression):
            return other == self.inner
        if isinstance(
            other, BaseTypeExpressionType
        ):  # implicitly not Nested typeexpression anymore
            # this is still correct
            return other == self.inner
        if isinstance(other, TypeExpression):
            return TypeExpression(other) == self.inner
        if isinstance(other, str):
            return other == self.inner

        raise TypeError(f"Cannot compare {type(self)} to {type(other)}")

    @classmethod
    def __get_validators__(
        cls,
    ):
        yield cls.validate

    def _facets(self) -> Sequence[str]:
        return self.inner._facets()

    def _properties(self: Self) -> Sequence[str]:
        return self.inner._properties()

    @override
    def schema(self, by_alias: bool = ..., ref_template: str = ...) -> Dict[str, Any]:  # type: ignore[override,assignment]
        return self.inner.schema()
