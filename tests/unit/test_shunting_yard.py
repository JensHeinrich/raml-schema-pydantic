# noqa: C0116, C0114
from typing import Sequence

import pytest
from raml_schema_pydantic.types.type_expression._shunt import DEFAULT_DELIMS
from raml_schema_pydantic.types.type_expression._shunt import Operator
from raml_schema_pydantic.types.type_expression._shunt import postfix_to_ast
from raml_schema_pydantic.types.type_expression._shunt import shunt
from raml_schema_pydantic.types.type_expression._shunt import Token
from raml_schema_pydantic.types.type_expression._shunt import tokenize
from raml_schema_pydantic.types.type_expression._shunt.tokenizer import (
    tokenize_from_generator,
)

OPERATOR_ADD = Operator[Token](value=Token("+"), precedence=5)
OPERATOR_SUBTRACT = Operator[Token](value=Token("-"), precedence=5)
OPERATOR_MULTIPLY = Operator[Token](value=Token("*"), precedence=10)
OPERATOR_DIVIDE = Operator[Token](value=Token("/"), precedence=10)
OPERATOR_UNION = Operator[Token](
    value=Token("|"),
    name="Union",
)
OPERATOR_ARRAY = Operator[Token](
    value=Token("[]"),
    name="Array",
    precedence=5,
    unary=True,
    unary_position="postfix",
    associativity="none",
)


@pytest.fixture
def default_operators() -> Sequence[Operator[Token]]:
    return (OPERATOR_ADD, OPERATOR_MULTIPLY, OPERATOR_DIVIDE, OPERATOR_SUBTRACT)


@pytest.fixture
def name_operators() -> Sequence[Operator[Token]]:
    return (OPERATOR_UNION, OPERATOR_ARRAY)


@pytest.fixture
def all_operators(name_operators, default_operators) -> Sequence[Operator[Token]]:
    return name_operators + default_operators


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
    assert shunt(input_data=input_string, ops=default_operators) == expected


def test_shunting_yard_for_syntax():
    ops = [OPERATOR_UNION, OPERATOR_ARRAY]

    assert shunt("A[]", ops=ops) == ["A", OPERATOR_ARRAY]
    assert shunt("A|B", ops=ops) == ["A", "B", OPERATOR_UNION]
    assert shunt("A|B|C", ops=ops) == ["A", "B", OPERATOR_UNION, "C", OPERATOR_UNION]
    assert shunt("A[]|B", ops=ops) == ["A", OPERATOR_ARRAY, "B", OPERATOR_UNION]


def test_shunting_yard_extra():
    ops = [OPERATOR_UNION, OPERATOR_ARRAY]

    assert shunt("A[]|B[]", ops=ops) == [
        "A",
        OPERATOR_ARRAY,
        "B",
        OPERATOR_ARRAY,
        OPERATOR_UNION,
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
    assert str(postfix_to_ast(shunt("A[] |B[]", ops=ops))) == "A[]|B[]"
    assert shunt("A|B", ops=ops) == shunt("(A|B)", ops=ops, delim_pairs=DEFAULT_DELIMS)

    assert shunt("A|B[]", ops=ops) == ["A", "B", OPERATOR_ARRAY, OPERATOR_UNION]
    assert shunt("(A|B)[]", ops=ops, delim_pairs=DEFAULT_DELIMS) == [
        "A",
        "B",
        OPERATOR_UNION,
        OPERATOR_ARRAY,
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
        "(A+B)*C",
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
def test_postfix_to_tree(input_string, default_operators):
    assert (
        str(postfix_to_ast(shunt(input_string, ops=default_operators))) == input_string
    )


@pytest.mark.parametrize(
    "input_string",
    [
        pytest.param("A[]*B+C", marks=pytest.mark.xfail(reason="TODO")),
        "A+B*C[]",
        pytest.param("(A+B)[]*C", marks=pytest.mark.xfail(reason="TODO")),
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
def test_postfix_to_tree_with_unary(input_string, all_operators):
    assert str(postfix_to_ast(shunt(input_string, ops=all_operators))) == input_string
