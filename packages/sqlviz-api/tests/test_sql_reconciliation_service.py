"""The native parser's source coordinates feed the pure identity policy unchanged."""

import pytest
from sqlviz_api.services.sql_scripts import SqlScriptService
from sqlviz_core.models.sql_reconciliation import (
    ExistingSqlPanel,
    KeepSqlPanel,
    SqlReconciliationError,
    reconcile_sql_script,
)


@pytest.mark.parametrize(
    "source",
    [
        "SELECT 'a;b'; -- leading;\r\nSELECT 2 /* trailing; */;",
        "SELECT '\U0001f680;a'; SELECT '\U0001f680;a'",
        "WITH x AS (SELECT ';') SELECT * FROM x; SELECT [1, 2]",
        "/* outer /* inner; */ tail; */ SELECT 1; SELECT $$a;b$$;",
    ],
)
def test_native_fragments_keep_the_explicit_panel_associations(source):
    statements = SqlScriptService().parse(source)
    previous = (ExistingSqlPanel("a", "SELECT 10"), ExistingSqlPanel("b", "SELECT 20"))
    choices = (KeepSqlPanel(0, "b"), KeepSqlPanel(1, "a"))
    plan = reconcile_sql_script(source, statements, previous, choices)
    assert plan.complete
    assert tuple(item.panel_id for item in plan.statements) == ("b", "a")
    assert tuple(item.statement for item in plan.statements) == statements
    assert all(item.sql_changed for item in plan.statements)


def test_native_parse_from_an_older_draft_cannot_reconcile_a_new_source():
    parsed = SqlScriptService().parse("SELECT 1; SELECT 2")
    with pytest.raises(SqlReconciliationError) as error:
        reconcile_sql_script("SELECT 1; SELECT 3", parsed, ())
    assert error.value.code == "sql_reconciliation_invalid"
