"""Transport-independent source budgets and immutable positions."""

from dataclasses import FrozenInstanceError

import pytest
from sqlviz_core.models.sql_script import (
    MAX_SQL_SCRIPT_BYTES,
    SqlScriptError,
    SqlStatement,
    validate_sql_script,
)


@pytest.mark.parametrize("source", [None, 1, True, [], "\ud800", "SELECT 1\x00; SELECT 2"])
def test_invalid_text_is_rejected_without_coercion(source):
    with pytest.raises(SqlScriptError) as error:
        validate_sql_script(source)
    assert error.value.code == "sql_script_invalid"


def test_byte_budget_counts_utf8_not_characters_and_accepts_the_exact_boundary():
    validate_sql_script("é" * (MAX_SQL_SCRIPT_BYTES // 2))
    with pytest.raises(SqlScriptError) as error:
        validate_sql_script("é" * (MAX_SQL_SCRIPT_BYTES // 2) + "a")
    assert error.value.code == "sql_script_limit"


def test_source_span_is_immutable():
    statement = SqlStatement("SELECT 1", 0, 8)
    with pytest.raises(FrozenInstanceError):
        statement.start_offset = 1
