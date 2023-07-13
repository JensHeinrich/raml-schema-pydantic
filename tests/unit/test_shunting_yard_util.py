# This test code was written by the `hypothesis.extra.ghostwriter` module
# and is provided under the Creative Commons Zero public domain dedication.
import typing
from typing import List
from typing import Literal

import pytest
import raml_schema_pydantic.types.type_expression._shunt.token_types
import raml_schema_pydantic.types.type_expression._shunt.util
from hypothesis import example
from hypothesis import given
from hypothesis import note
from hypothesis import strategies as st
from raml_schema_pydantic.types.type_expression._shunt import Operator
from raml_schema_pydantic.types.type_expression._shunt import Token
from raml_schema_pydantic.types.type_expression._shunt.algorithm import shunt
from raml_schema_pydantic.types.type_expression._shunt.algorithm import shunt_tokens
from raml_schema_pydantic.types.type_expression._shunt.hypothesis_strategies import (
    rpn_node_strategy_recursive,
)
from raml_schema_pydantic.types.type_expression._shunt.hypothesis_strategies import (
    rpn_tree_to_ops,
)
from raml_schema_pydantic.types.type_expression._shunt.predefined import (
    OPERATOR_POSTFIX_HIGH,
)
from raml_schema_pydantic.types.type_expression._shunt.predefined import (
    OPERATOR_POSTFIX_LOW,
)
from raml_schema_pydantic.types.type_expression._shunt.predefined import (
    OPERATOR_PREFIX_HIGH,
)
from raml_schema_pydantic.types.type_expression._shunt.predefined import (
    OPERATOR_PREFIX_LOW,
)
from raml_schema_pydantic.types.type_expression._shunt.predefined import (
    RPN_OPERATOR_POSTFIX_HIGH,
)
from raml_schema_pydantic.types.type_expression._shunt.predefined import (
    RPN_OPERATOR_POSTFIX_LOW,
)
from raml_schema_pydantic.types.type_expression._shunt.predefined import (
    RPN_OPERATOR_PREFIX_HIGH,
)
from raml_schema_pydantic.types.type_expression._shunt.predefined import (
    RPN_OPERATOR_PREFIX_LOW,
)
from raml_schema_pydantic.types.type_expression._shunt.predefined import RPN_VALUE
from raml_schema_pydantic.types.type_expression._shunt.predefined import VALUE
from raml_schema_pydantic.types.type_expression._shunt.token_types import RPNToken
from raml_schema_pydantic.types.type_expression._shunt.util import rpn_to_ast
from raml_schema_pydantic.types.type_expression._shunt.util import RPNNode
from typing_extensions import deprecated


@pytest.mark.parametrize(
    "shunted, tokens",
    [
        pytest.param(
            [RPN_VALUE, RPN_OPERATOR_PREFIX_LOW, RPN_OPERATOR_PREFIX_HIGH],
            (tokens := [OPERATOR_PREFIX_HIGH, OPERATOR_PREFIX_LOW, VALUE]),
            id=" ".join(str(t) for t in tokens),
        ),
        pytest.param(
            [RPN_VALUE, RPN_OPERATOR_PREFIX_HIGH, RPN_OPERATOR_PREFIX_LOW],
            (tokens := [OPERATOR_PREFIX_LOW, OPERATOR_PREFIX_HIGH, VALUE]),
            id=" ".join(str(t) for t in tokens),
        ),
        pytest.param(
            [RPN_VALUE, RPN_OPERATOR_POSTFIX_LOW, RPN_OPERATOR_POSTFIX_HIGH],
            (tokens := [VALUE, OPERATOR_POSTFIX_LOW, OPERATOR_POSTFIX_HIGH]),
            id=" ".join(str(t) for t in tokens),
        ),
        pytest.param(
            [RPN_VALUE, RPN_OPERATOR_POSTFIX_HIGH, RPN_OPERATOR_POSTFIX_LOW],
            (tokens := [VALUE, OPERATOR_POSTFIX_HIGH, OPERATOR_POSTFIX_LOW]),
            id=" ".join(str(t) for t in tokens),
        ),
        pytest.param(
            [RPN_VALUE, RPN_OPERATOR_PREFIX_LOW, RPN_OPERATOR_POSTFIX_HIGH],
            (tokens := [OPERATOR_PREFIX_LOW, VALUE, OPERATOR_POSTFIX_HIGH]),
            id=" ".join(str(t) for t in tokens),
        ),
    ],
)
def test_unary_precedence(shunted: List[RPNToken], tokens: List[Token]):
    ops = [
        OPERATOR_POSTFIX_HIGH,
        OPERATOR_POSTFIX_LOW,
        OPERATOR_PREFIX_HIGH,
        OPERATOR_PREFIX_LOW,
    ]
    _shunted = shunt_tokens(
        input_data=[t.value if isinstance(t, Operator) else t for t in tokens], ops=ops
    )
    assert _shunted == shunted


def test_double_prefix():
    _shunted = shunt(
        "--1",
        ops=[
            Operator(
                value=Token("-"),
                unary=True,
                associativity="none",
                unary_position="prefix",
            )
        ],
    )
    assert [str(v) for v in _shunted] == ["1", "-", "-"]


@pytest.mark.parametrize(
    "node",
    [
        RPNNode(
            arg_count=1,
            value=RPNToken(
                arg_count=1,
                values=[Token("1"), None],
                precedence=1,
                associativity="none",
            ),
            children=[
                RPNNode(
                    arg_count=1,
                    value=RPNToken(
                        arg_count=1,
                        values=[Token("0"), None],
                        precedence=0,
                        associativity="none",
                    ),
                    children=[
                        RPNNode[RPNToken](
                            arg_count=0,
                            value=RPNToken(
                                arg_count=0,
                                values=[Token("2")],
                                precedence=0,
                                associativity="none",
                            ),
                            children=[],
                        )
                    ],
                )
            ],
        )
    ],
)
def test_trees_stupid(node):
    ops = rpn_tree_to_ops(node)
    assert str(node) == "102"
    assert isinstance(ops, list)
    _str = str(node)
    _shunted = shunt(_str, ops=ops)
    _from_ast = rpn_to_ast(_shunted)
    _str_from_ast = str(_from_ast)
    _str_from_node = str(node)
    _dirty_from_ast = _from_ast.dirty_tree_str()  # noqa: ignore=[F841]
    _dirty_from_node = node.dirty_tree_str()  # noqa: ignore=[F841]
    assert _str_from_ast == _str_from_node
    # assert _from_ast == node # FIXME


@given(node=rpn_node_strategy_recursive)
@example(
    node=RPNNode(
        arg_count=1,
        value=RPNToken(
            arg_count=1, values=[Token("1"), None], precedence=1, associativity="none"
        ),
        children=[
            RPNNode(
                arg_count=1,
                value=RPNToken(
                    arg_count=1,
                    values=[Token("0"), None],
                    precedence=0,
                    associativity="none",
                ),
                children=[
                    RPNNode[RPNToken](
                        arg_count=0,
                        value=RPNToken(
                            arg_count=0,
                            values=[Token("2")],
                            precedence=0,
                            associativity="none",
                        ),
                        children=[],
                    )
                ],
            )
        ],
    )
).via("discovered failure")
def test_trees(node):
    ops = rpn_tree_to_ops(node)
    note(f"ops: {ops}\nnode: {node}")
    assert isinstance(ops, list)
    _str = str(node)
    _shunted = shunt(_str, ops=ops)
    _from_ast = rpn_to_ast(_shunted)
    _str_from_ast = str(_from_ast)
    _str_from_node = str(node)
    _dirty_from_ast = _from_ast.dirty_tree_str()
    _dirty_from_node = node.dirty_tree_str()
    assert _str_from_ast == _str_from_node, (_dirty_from_ast, _dirty_from_node)
    # assert _from_ast == node # FIXME


# st.none was autogenerated; manually replaced with 'none' and refactored into dedicated strategy
associativity_strategy: st.SearchStrategy[
    Literal["none", "right", "left"]
] = st.sampled_from(["none", "right", "left"])


@pytest.mark.skip(reason="RecursionError")
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
    associativity=associativity_strategy,
    children=st.from_type(
        typing.List[
            raml_schema_pydantic.types.type_expression._shunt.util.OperatorNode
            | raml_schema_pydantic.types.type_expression._shunt.util.ValueNode
        ]
    ),
)
def test_fuzz_OperatorNode(
    value: raml_schema_pydantic.types.type_expression._shunt.token_types._SymbolType,
    name: typing.Optional[str],
    precedence: int,
    unary,
    unary_position,
    associativity,
    children: typing.List[
        typing.Union[
            raml_schema_pydantic.types.type_expression._shunt.util.OperatorNode,
            raml_schema_pydantic.types.type_expression._shunt.util.ValueNode,
        ]
    ],
) -> None:
    raml_schema_pydantic.types.type_expression._shunt.util.OperatorNode(
        value=value,
        name=name,
        precedence=precedence,
        unary=unary,
        unary_position=unary_position,
        associativity=associativity,
        children=children,
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
    precedence=st.integers(),
)
def test_fuzz_ValueNode(
    value: raml_schema_pydantic.types.type_expression._shunt.token_types._ValueType,
    precedence: int,
) -> None:
    raml_schema_pydantic.types.type_expression._shunt.util.ValueNode(
        value=value, precedence=precedence
    )


# @given(
#     instance=st.from_type(Any),
#     d=st.from_type(typing.Union[typing.Mapping[~_K, typing.Any], typing.Sequence[~_K]]),
# )
# def test_fuzz_check_in(
#     instance: typing.Any,
#     d: typing.Union[
#         typing.Mapping[
#             raml_schema_pydantic.types.type_expression._shunt.util._K, typing.Any
#         ],
#         typing.Sequence,
#     ],
# ) -> None:
#     raml_schema_pydantic.types.type_expression._shunt.util.check_in(
#         instance=instance, d=d
#     )


@pytest.mark.skip("Not used anymore")
@deprecated("Not used anymore")
@given(
    input_data=st.lists(
        st.one_of(
            st.one_of(
                st.builds(
                    Operator,
                    associativity=associativity_strategy,
                    name=st.one_of(st.none(), st.one_of(st.none(), st.text())),
                    precedence=st.one_of(st.just(0), st.integers()),
                    unary=st.just(True),
                    unary_position=st.sampled_from(["postfix", "prefix"]),
                    value=st.builds(
                        Token,
                        st.text(
                            alphabet=st.characters(blacklist_categories=("C", "Z")),
                            min_size=1,
                        ),
                    ),
                ),
                st.builds(
                    Operator,
                    associativity=associativity_strategy,
                    name=st.one_of(st.none(), st.one_of(st.none(), st.text())),
                    precedence=st.one_of(st.just(0), st.integers()),
                    unary=st.just(False),
                    unary_position=st.none(),
                    value=st.builds(
                        Token,
                        st.text(
                            alphabet=st.characters(blacklist_categories=("C", "Z")),
                            min_size=1,
                        ),
                    ),
                ),
                # REMOVED as mixed operators are not supported with postfix_to_ast
                # st.builds(
                #     Operator,
                #     associativity=associativity_strategy,
                #     name=st.one_of(st.none(), st.one_of(st.none(), st.text())),
                #     precedence=st.one_of(st.just(0), st.integers()),
                #     unary=st.just("both"),
                #     unary_position=st.sampled_from(["postfix", "prefix"]),
                #     value=st.builds(
                #         Token,
                #         st.text(
                #             alphabet=st.characters(blacklist_categories=("C", "Z")),
                #             min_size=1,
                #         ),
                #     ),
                # ),
            ),
            st.builds(
                Token,
                st.text(
                    st.characters(
                        blacklist_categories=(
                            "Zl",
                            "Zp",
                            "Co",
                            "Zs",
                            "Cf",
                            "Cn",
                            "Cc",
                            "Cs",
                        )
                    ),
                    min_size=1,
                ),
            ),
        ),
        min_size=1,
    )
)
def test_fuzz_postfix_to_ast(
    input_data: typing.List[
        typing.Union[
            raml_schema_pydantic.types.type_expression._shunt.Operator,
            raml_schema_pydantic.types.type_expression._shunt.token_types._ValueType,
        ]
    ]
) -> None:
    raml_schema_pydantic.types.type_expression._shunt.util.postfix_to_ast(
        input_data=input_data
    )
