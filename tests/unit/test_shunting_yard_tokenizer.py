# This test code was partly written by the `hypothesis.extra.ghostwriter` module
# and is provided under the Creative Commons Zero public domain dedication.
import typing

import raml_schema_pydantic.types.type_expression._shunt.__init__
import raml_schema_pydantic.types.type_expression._shunt.token_types
from hypothesis import given
from raml_schema_pydantic.types.type_expression._shunt.hypothesis_strategies import (
    _hypothesis_setup_hook,
)
from raml_schema_pydantic.types.type_expression._shunt.hypothesis_strategies import (
    ops_and_tokens_strategy,
)

if typing.TYPE_CHECKING:
    from raml_schema_pydantic.types.type_expression._shunt import DelimPair
    from raml_schema_pydantic.types.type_expression._shunt import Token

_hypothesis_setup_hook()
min_size = 1


@given(ops_and_tokens=ops_and_tokens_strategy())
def test_tokenization_from_generator(
    ops_and_tokens: """typing.Tuple[
        typing.Sequence[
            raml_schema_pydantic.types.type_expression._shunt.token_types.Operator
        ],
        typing.List[Token],
    ]""",
):
    ops, tokens = ops_and_tokens
    input_data: str = " ".join(tokens)
    delim_pairs: "typing.List[DelimPair]" = []
    result_tokenize_from_generator = raml_schema_pydantic.types.type_expression._shunt.tokenizer.tokenize_from_generator(
        input_data=input_data,
        predefined_tokens=(
            {delim.opening for delim in delim_pairs}
            | {delim.closing for delim in delim_pairs}
            | {op.value for op in ops}
        ),
    )
    assert result_tokenize_from_generator == tokens
