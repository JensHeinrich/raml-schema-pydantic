# noqa: C0116, C0114
from contextlib import nullcontext as does_not_raise
from typing import ContextManager
from typing import List

import pytest
from raml_schema_pydantic.types.type_expression._shunt import DEFAULT_DELIMS
from raml_schema_pydantic.types.type_expression._shunt import Operator
from raml_schema_pydantic.types.type_expression._shunt import shunt
from raml_schema_pydantic.types.type_expression._shunt import Token
from raml_schema_pydantic.types.type_expression._shunt import tokenize
from raml_schema_pydantic.types.type_expression._shunt.algorithm import pop_before
from raml_schema_pydantic.types.type_expression._shunt.exceptions import (
    NonMatchingDelimitersException,
)
from raml_schema_pydantic.types.type_expression._shunt.predefined import OPERATOR_ADD
from raml_schema_pydantic.types.type_expression._shunt.predefined import OPERATOR_ARRAY
from raml_schema_pydantic.types.type_expression._shunt.predefined import OPERATOR_DIVIDE
from raml_schema_pydantic.types.type_expression._shunt.predefined import (
    OPERATOR_EXPONENTIATION,
)
from raml_schema_pydantic.types.type_expression._shunt.predefined import (
    OPERATOR_MULTIPLY,
)
from raml_schema_pydantic.types.type_expression._shunt.predefined import (
    OPERATOR_NEGATIVE,
)
from raml_schema_pydantic.types.type_expression._shunt.predefined import (
    OPERATOR_POSITIVE,
)
from raml_schema_pydantic.types.type_expression._shunt.predefined import (
    OPERATOR_SUBTRACT,
)
from raml_schema_pydantic.types.type_expression._shunt.predefined import OPERATOR_UNION
from raml_schema_pydantic.types.type_expression._shunt.token_types import ClosingDelim
from raml_schema_pydantic.types.type_expression._shunt.token_types import DelimPair
from raml_schema_pydantic.types.type_expression._shunt.token_types import OpeningDelim
from raml_schema_pydantic.types.type_expression._shunt.token_types import RPNToken
from raml_schema_pydantic.types.type_expression._shunt.tokenizer import (
    tokenize_from_generator,
)
from raml_schema_pydantic.types.type_expression._shunt.util import rpn_to_ast
from raml_schema_pydantic.types.type_expression._shunt.util import RPNNode


@pytest.mark.parametrize(
    "op_stack, op_next, expected",
    [
        (
            RPNToken(
                arg_count=2,
                values=[None, Token("-"), None],
                precedence=2,
                associativity="left",
            ),
            RPNToken(
                arg_count=2,
                values=[None, Token("^"), None],
                precedence=4,
                associativity="right",
            ),
            False,
        ),
        (
            RPNToken(
                arg_count=2,
                values=[None, OPERATOR_UNION.value, None],
                associativity="left",
            ),
            RPNToken(
                arg_count=1,
                values=[Token("NOT"), None],
                associativity="none",
            ),
            False,
        ),
    ],
)
def test_pop_before(op_stack: RPNToken, op_next: RPNToken, expected: bool):
    _val = pop_before(op_stack, op_next)
    assert _val == expected


def test_rpn_node_representation():
    node_a = RPNNode(
        arg_count=0,
        value=RPNToken(arg_count=0, values=[Token("A")], associativity="none"),
        children=[],
    )
    node_b = RPNNode(
        arg_count=0,
        value=RPNToken(arg_count=0, values=[Token("B")], associativity="none"),
        children=[],
    )
    node_sum = RPNNode[RPNToken](
        arg_count=2,
        value=RPNToken(
            arg_count=2,
            associativity="left",
            values=[None, Token("+"), None],
        ),
        children=[
            node_a,
            node_b,
        ],
    )
    assert str(node_sum) == "A+B"


TOKENIZE_TEST_CASES = (
    [pytest.param("0", ["0"], id="numeric")]
    + [
        pytest.param(f"A{op.value}", ["A", op.value], id=f"suffix {op.value}")
        for op in [
            OPERATOR_ADD,
            OPERATOR_MULTIPLY,
            OPERATOR_DIVIDE,
            OPERATOR_SUBTRACT,
            OPERATOR_ARRAY,
            OPERATOR_UNION,
        ]
    ]
    + [
        pytest.param(f"A{op.value}B", ["A", op.value, "B"], id=f"between {op.value}")
        for op in [
            OPERATOR_ADD,
            OPERATOR_MULTIPLY,
            OPERATOR_DIVIDE,
            OPERATOR_SUBTRACT,
            OPERATOR_ARRAY,
            OPERATOR_UNION,
        ]
    ]
    + [
        pytest.param(
            f"AAA{op.value}BBB",
            ["AAA", op.value, "BBB"],
            id=f"multi letter token between {op.value}",
        )
        for op in [
            OPERATOR_ADD,
            OPERATOR_MULTIPLY,
            OPERATOR_DIVIDE,
            OPERATOR_SUBTRACT,
            OPERATOR_ARRAY,
            OPERATOR_UNION,
        ]
    ]
    + [
        pytest.param(f"{op.value}B", [op.value, "B"], id=f"prefix {op.value}")
        for op in [
            OPERATOR_ADD,
            OPERATOR_MULTIPLY,
            OPERATOR_DIVIDE,
            OPERATOR_SUBTRACT,
            OPERATOR_ARRAY,
            OPERATOR_UNION,
        ]
    ]
    + [
        pytest.param(f"{op.value}", [op.value], id=f"only op {op.value}")
        for op in [
            OPERATOR_ADD,
            OPERATOR_MULTIPLY,
            OPERATOR_DIVIDE,
            OPERATOR_SUBTRACT,
            OPERATOR_ARRAY,
            OPERATOR_UNION,
        ]
    ]
)

# Extracted to constants for better readability
UNICODE_MINUS = "−"
UNICODE_TIMES = "×"


@pytest.mark.parametrize(
    "expression, shunted, ops, delim_pairs",
    [
        pytest.param(
            "A[]",
            [Token("A"), Token("[]")],
            [OPERATOR_ARRAY],
            DEFAULT_DELIMS,
            id="Simple postfix",
        ),
        pytest.param(
            "-A",
            [Token("A"), Token("-")],
            [OPERATOR_SUBTRACT, OPERATOR_NEGATIVE],
            # [Operator(value=Token("-"), unary=True, unary_position="prefix")],
            DEFAULT_DELIMS,
            id="Simple prefix",
        ),
        pytest.param(
            f"3 + 4 {UNICODE_TIMES} 2 ÷ ( 1 {UNICODE_MINUS} 5 ) ^ 2 ^ 3",
            [
                Token(t)
                for t in [
                    "3",
                    "4",
                    "2",
                    UNICODE_TIMES,
                    "1",
                    "5",
                    UNICODE_MINUS,
                    "2",
                    "3",
                    "^",
                    "^",
                    "÷",
                    "+",
                ]
            ],
            [
                Operator(
                    value=Token(UNICODE_TIMES),
                    unary=False,
                    precedence=3,
                    associativity="left",
                ),
                OPERATOR_EXPONENTIATION,
                Operator(
                    value=Token("÷"), precedence=3, associativity="left", unary=False
                ),
                OPERATOR_ADD,
                OPERATOR_POSITIVE,
                Operator(
                    value=Token(UNICODE_MINUS),
                    precedence=2,
                    associativity="left",
                    unary=False,
                ),
            ],
            [DelimPair(opening=OpeningDelim("("), closing=ClosingDelim(")"))],
            id="complex example",
            # Source: https://en.wikipedia.org/wiki/Shunting_yard_algorithm
        ),
        pytest.param(
            "a ^ - b",
            [
                Token("a"),
                Token("b"),
                Token("-"),
                Token("^"),
            ],
            [
                OPERATOR_EXPONENTIATION,
                OPERATOR_NEGATIVE,
                OPERATOR_SUBTRACT,
            ],
            [],
            id="unary precedence example",
            # Source: https://www.reedbeta.com/blog/the-shunting-yard-algorithm/
        ),
        pytest.param(
            "-a^b",
            [
                Token("a"),
                Token("b"),
                Token("^"),
                Token("-"),
            ],
            [
                Operator(
                    value=Token("^"), unary=False, precedence=4, associativity="right"
                ),
                OPERATOR_NEGATIVE,
                OPERATOR_SUBTRACT,
            ],
            [],
            id="unary precedence example",
            # Source: https://www.reedbeta.com/blog/the-shunting-yard-algorithm/
        ),
    ],
)
def test_unary_handling(expression: str, shunted: List[RPNToken], ops, delim_pairs):
    _shunted = list(shunt(input_data=expression, ops=ops, delim_pairs=delim_pairs))
    assert [str(v) for v in shunted] == [str(v) for v in _shunted]


@pytest.mark.parametrize("input_string,expected", TOKENIZE_TEST_CASES)
def test_tokenize(input_string, expected, all_operators):
    assert (
        tokenize(
            input_string,
            predefined_tokens=(
                {delim.opening for delim in DEFAULT_DELIMS}
                | {delim.closing for delim in DEFAULT_DELIMS}
                | {op.value for op in all_operators}
            ),
        )
        == expected
    )


@pytest.mark.parametrize("input_string,expected", TOKENIZE_TEST_CASES)
def test_tokenize_generator(input_string, expected, all_operators):
    assert (
        tokenize_from_generator(
            input_string,
            predefined_tokens=(
                {delim.opening for delim in DEFAULT_DELIMS}
                | {delim.closing for delim in DEFAULT_DELIMS}
                | {op.value for op in all_operators}
            ),
        )
        == expected
    )


@pytest.mark.parametrize(
    "input_string,expected",
    [
        pytest.param(f"A{op.value}B", ["A", "B", op], id=f"Basic {op.value}")
        for op in [OPERATOR_ADD, OPERATOR_MULTIPLY, OPERATOR_DIVIDE, OPERATOR_SUBTRACT]
    ]
    + [
        pytest.param(
            f"A{op1.value}B{op2.value}C",
            ["A", "B", op1, "C", op2],
            id=f"Higher first {op1.value},{op2.value}",
        )
        for op1 in [OPERATOR_MULTIPLY, OPERATOR_DIVIDE]
        for op2 in [OPERATOR_ADD, OPERATOR_SUBTRACT]
    ]
    + [
        pytest.param(
            f"A{op1.value}B{op2.value}C",
            ["A", "B", "C", op2, op1],
            id=f"Higher last {op1.value},{op2.value}",
        )
        for op2 in [OPERATOR_MULTIPLY, OPERATOR_DIVIDE]
        for op1 in [OPERATOR_ADD, OPERATOR_SUBTRACT]
    ],
)
def test_basic_shunting_yard_logic(input_string, expected, default_operators):
    assert sum(
        # using sum to flatten the list of lists
        # source: https://note.nkmk.me/en/python-list-flatten/
        [
            list(filter(lambda p: p is not None, t.values))
            for t in shunt(input_data=input_string, ops=default_operators)
        ],
        [],
    ) == [str(t) for t in expected]


@pytest.mark.parametrize(
    "expression, expected",
    [
        pytest.param("A[]", ["A", OPERATOR_ARRAY]),
        pytest.param("A|B", ["A", "B", OPERATOR_UNION]),
        pytest.param("A|B|C", ["A", "B", OPERATOR_UNION, "C", OPERATOR_UNION]),
        pytest.param("A[]|B", ["A", OPERATOR_ARRAY, "B", OPERATOR_UNION], id="A[]|B"),
    ],
)
def test_shunting_yard_for_syntax(
    expression: str, expected: List[str | Operator[Token]]
):
    ops = [OPERATOR_UNION, OPERATOR_ARRAY]

    assert sum(
        [
            list(filter(lambda p: p is not None, t.values))
            for t in shunt(expression, ops=ops)
        ],
        [],
    ) == [t.value if isinstance(t, Operator) else t for t in expected]


def test_shunting_yard_extra():
    ops = [OPERATOR_UNION, OPERATOR_ARRAY]

    assert [str(t) for t in shunt("A[]|B[]", ops=ops)] == [
        str(t)
        for t in [
            "A",
            OPERATOR_ARRAY,
            "B",
            OPERATOR_ARRAY,
            OPERATOR_UNION,
        ]
    ]
    assert tokenize(
        "A []|B[]",
        predefined_tokens=(
            {delim.opening for delim in DEFAULT_DELIMS}
            | {delim.closing for delim in DEFAULT_DELIMS}
            | {op.value for op in ops}
        ),
    ) == ["A", "[]", "|", "B", "[]"]
    assert tokenize(
        "A[] |B[]",
        predefined_tokens=(
            {delim.opening for delim in DEFAULT_DELIMS}
            | {delim.closing for delim in DEFAULT_DELIMS}
            | {op.value for op in ops}
        ),
    ) == ["A", "[]", "|", "B", "[]"]
    _shunted = shunt("A[] |B[]", ops=ops)
    assert len(shunt("A[] |B[]", ops=ops)) == 5
    assert [str(v) for v in shunt("A|B", ops=ops)] == ["A", "B", "|"]
    _ast = rpn_to_ast(_shunted)
    assert str(_ast) == "A[]|B[]"
    assert shunt("A|B", ops=ops) == shunt("(A|B)", ops=ops, delim_pairs=DEFAULT_DELIMS)

    assert [str(t) for t in shunt("A|B[]", ops=ops)] == [
        str(t) for t in ["A", "B", OPERATOR_ARRAY, OPERATOR_UNION]
    ]
    assert [str(t) for t in shunt("(A|B)[]", ops=ops, delim_pairs=DEFAULT_DELIMS)] == [
        str(t)
        for t in [
            "A",
            "B",
            OPERATOR_UNION,
            OPERATOR_ARRAY,
        ]
    ]
    assert shunt("A|B[]", ops=ops) == shunt(
        "(A|B[])", ops=ops, delim_pairs=DEFAULT_DELIMS
    )
    assert shunt("A|B[]", ops=ops) != shunt(
        "(A|B)[]", ops=ops, delim_pairs=DEFAULT_DELIMS
    )


@pytest.mark.parametrize(
    "input_string",
    [
        "A*B+C",
        "A+B*C",
        pytest.param(
            "(A+B)*C",
            id="parentheses support",
        ),
        pytest.param(
            "A+(B*C)",
            marks=pytest.mark.xfail(
                raises=AssertionError,
                reason="unnecessary parentheses are removed",
            ),
        ),
        pytest.param(
            "A+(B*C)+D",
            marks=pytest.mark.xfail(
                raises=AssertionError,
                reason="unnecessary parentheses are removed",
            ),
        ),
        "A+B+C",
        "A*B*C",
    ],
)
def test_rpn_to_tree(input_string, default_operators):
    assert str(rpn_to_ast(shunt(input_string, ops=default_operators))) == input_string


@pytest.mark.parametrize(
    "input_string",
    [
        pytest.param(
            "A[]*B+C",
            # marks=pytest.mark.xfail(reason="TODO")
        ),
        "A+B*C[]",
        pytest.param(
            "(A+B)[]*C",
            # marks=pytest.mark.xfail(reason="TODO")
        ),
        pytest.param(
            "A+(B*C)",
            marks=pytest.mark.xfail(
                raises=AssertionError,
                reason="unnecessary parentheses are removed",
            ),
        ),
        pytest.param(
            "A+(B*C)+D[]",
            marks=pytest.mark.xfail(
                raises=AssertionError,
                reason="unnecessary parentheses are removed",
            ),
        ),
        "A+B+C[]",
        "A*B*C[]",
    ],
)
def test_rpn_to_tree_with_unary(input_string, all_operators):
    _shunted = shunt(input_string, ops=all_operators)
    _ast: RPNNode[RPNToken] = rpn_to_ast(_shunted)
    assert str(_ast) == input_string


@pytest.mark.parametrize(
    "input_string, context",
    [
        ("(A+[B+C])", does_not_raise()),
        (
            "(A + [ B + C)]",
            pytest.raises(expected_exception=NonMatchingDelimitersException),
        ),
    ],
)
def test_complex_nested_delimiters(
    input_string, context: ContextManager, all_operators
):
    with context:
        _shunted = shunt(  # noqa: ignore=[F841]
            input_string,
            ops=all_operators,
            delim_pairs=[
                DelimPair(opening=OpeningDelim("("), closing=ClosingDelim(")")),
                DelimPair(opening=OpeningDelim("["), closing=ClosingDelim("]")),
            ],
        )
