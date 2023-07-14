# This test code was written by the `hypothesis.extra.ghostwriter` module
# and is provided under the Creative Commons Zero public domain dedication.
import typing

import raml_schema_pydantic.types.type_expression._shunt.token_types
from hypothesis import assume
from hypothesis import given
from hypothesis import strategies as st
from raml_schema_pydantic.types.type_expression._shunt import ClosingDelim
from raml_schema_pydantic.types.type_expression._shunt import OpeningDelim
from raml_schema_pydantic.types.type_expression._shunt import Token
from raml_schema_pydantic.types.type_expression._shunt.hypothesis_strategies import (
    _hypothesis_setup_hook,
)
from raml_schema_pydantic.types.type_expression._shunt.hypothesis_strategies import (
    MAX_ARGS,
)

_hypothesis_setup_hook()


@given(
    opening=st.builds(
        OpeningDelim,
        object=st.text(
            alphabet=st.characters(blacklist_categories=("C", "Z")), min_size=1
        ),
    ),
    closing=st.builds(
        ClosingDelim,
        object=st.text(
            alphabet=st.characters(blacklist_categories=("C", "Z")), min_size=1
        ),
    ),
)
def test_fuzz_DelimPair(
    opening: raml_schema_pydantic.types.type_expression._shunt.token_types.OpeningDelim,
    closing: raml_schema_pydantic.types.type_expression._shunt.token_types.ClosingDelim,
) -> None:
    raml_schema_pydantic.types.type_expression._shunt.token_types.DelimPair(
        opening=opening, closing=closing
    )


@given(
    value=st.builds(
        Token,
        st.text(
            st.characters(
                blacklist_categories=("Zl", "Zp", "Co", "Zs", "Cf", "Cn", "Cc", "Cs")
            ),
            min_size=1,
        ),
    ),
    name=st.one_of(st.none(), st.text()),
    precedence=st.integers(),
    unary=st.sampled_from(["both", False, True]),
    unary_position=st.one_of(st.none(), st.sampled_from([None, "postfix", "prefix"])),
    associativity=st.sampled_from(["none", "right", "left"]),
)
def test_fuzz_Operator(
    value: raml_schema_pydantic.types.type_expression._shunt.token_types._SymbolType,
    name: typing.Optional[str],
    precedence: int,
    unary,
    unary_position,
    associativity,
) -> None:
    if unary:
        assume(unary_position is not None)
        assume(associativity == "none")
    else:
        assume(unary_position is None)
    raml_schema_pydantic.types.type_expression._shunt.token_types.Operator(
        value=value,
        name=name,
        precedence=precedence,
        unary=unary,
        unary_position=unary_position,
        associativity=associativity,
    )


@given(
    arg_count=st.shared(st.integers(min_value=0, max_value=MAX_ARGS), key="arg_count"),
    values=st.shared(
        st.integers(min_value=0, max_value=MAX_ARGS), key="arg_count"
    ).flatmap(
        lambda arg_count: st.lists(
            st.builds(
                Token,
                st.text(
                    alphabet=st.characters(blacklist_categories=("C", "Z")), min_size=1
                ),
            ),
            min_size=max(
                arg_count - 1, 1
            ),  # ensure one value is created for value nodes
            max_size=max(
                arg_count - 1, 1
            ),  # ensure one value is created for value nodes
        ).map(
            lambda _list: _list + [None for _ in range(arg_count)]
        ),  # add placeholders
    ),
    precedence=st.integers(min_value=0),
    associativity=st.sampled_from(["none", "right", "left"]),
)
def test_fuzz_RPNToken(
    arg_count: int,
    values: typing.List[
        typing.Union[raml_schema_pydantic.types.type_expression._shunt.Token, None],
    ],
    precedence: int,
    associativity,
) -> None:
    raml_schema_pydantic.types.type_expression._shunt.token_types.RPNToken(
        arg_count=arg_count,
        values=values,
        precedence=precedence,
        associativity=associativity,
    )
