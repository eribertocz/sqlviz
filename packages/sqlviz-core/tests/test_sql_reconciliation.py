"""Identity survives explicit edits; ambiguity never becomes an implicit mutation."""

from dataclasses import FrozenInstanceError
from itertools import permutations

import pytest
from sqlviz_core.models.sql_reconciliation import (
    CreateSqlPanel,
    ExistingSqlPanel,
    KeepSqlPanel,
    RemoveSqlPanel,
    SqlPanelCreation,
    SqlReconciliationError,
    reconcile_sql_script,
)
from sqlviz_core.models.sql_script import SqlScriptError, SqlStatement


def parsed_fragments(*fragments):
    """Source fixture for known fragments; never a production SQL splitter."""
    source = "\n;\n".join(fragments)
    offset = 0
    statements = []
    for fragment in fragments:
        end = offset + len(fragment.encode("utf-16-le")) // 2
        statements.append(SqlStatement(fragment, offset, end))
        offset = end + 3
    return source, statements


PANELS = (ExistingSqlPanel("sales", "SELECT 1"), ExistingSqlPanel("costs", "SELECT 2"))


@pytest.mark.parametrize("fragments", [("SELECT 1", "SELECT 2"), ("SELECT 2", "SELECT 1")])
def test_neither_position_nor_equal_sql_can_prove_identity(fragments):
    source, statements = parsed_fragments(*fragments)
    plan = reconcile_sql_script(source, statements, PANELS)
    assert plan.unresolved_statement_indexes == (0, 1)
    assert plan.unresolved_panel_ids == ("sales", "costs")
    assert not plan.statements and not plan.removed_panel_ids
    with pytest.raises(SqlReconciliationError) as error:
        plan.require_complete()
    assert error.value.code == "sql_reconciliation_unresolved"


def test_explicit_reorder_insertion_and_sql_edit_preserve_panel_identity():
    source, statements = parsed_fragments("SELECT 20", "SELECT 3", "SELECT 1")
    decisions = (KeepSqlPanel(2, "sales"), CreateSqlPanel(1, "draft-new"), KeepSqlPanel(0, "costs"))
    plan = reconcile_sql_script(source, statements, PANELS, decisions)
    plan.require_complete()
    costs, new, sales = plan.statements
    assert (costs.panel_id, costs.previous_sql, costs.statement.sql) == (
        "costs",
        "SELECT 2",
        "SELECT 20",
    )
    assert costs.sql_changed
    assert isinstance(new, SqlPanelCreation)
    assert (new.creation_key, new.statement.sql) == ("draft-new", "SELECT 3")
    assert sales.panel_id == "sales" and not sales.sql_changed
    assert not plan.removed_panel_ids
    # User choices are order-independent; source order determines execution order only.
    assert plan == reconcile_sql_script(source, statements, PANELS, tuple(reversed(decisions)))


def test_deleted_source_block_does_not_silently_delete_an_existing_panel():
    source, statements = parsed_fragments("SELECT 2")
    plan = reconcile_sql_script(source, statements, PANELS, (KeepSqlPanel(0, "costs"),))
    assert plan.unresolved_panel_ids == ("sales",)
    assert not plan.removed_panel_ids and not plan.complete
    confirmed = reconcile_sql_script(
        source, statements, PANELS, (RemoveSqlPanel("sales"), KeepSqlPanel(0, "costs"))
    )
    assert confirmed.complete and confirmed.removed_panel_ids == ("sales",)


def test_identical_queries_can_represent_distinct_panels():
    source, statements = parsed_fragments("SELECT 1", "SELECT 1")
    previous = (ExistingSqlPanel("first", "SELECT 1"), ExistingSqlPanel("second", "SELECT 1"))
    assert not reconcile_sql_script(source, statements, previous).complete
    plan = reconcile_sql_script(
        source, statements, previous, (KeepSqlPanel(0, "second"), KeepSqlPanel(1, "first"))
    )
    assert plan.complete
    assert tuple(item.panel_id for item in plan.statements) == ("second", "first")


@pytest.mark.parametrize("source", ["", "-- cleared draft;\n/* no queries */"])
def test_empty_or_comment_only_script_requires_explicit_removal(source):
    plan = reconcile_sql_script(source, (), PANELS)
    assert not plan.complete and not plan.removed_panel_ids
    assert plan.unresolved_panel_ids == ("sales", "costs")
    explicit = reconcile_sql_script(
        source, (), PANELS, (RemoveSqlPanel("costs"), RemoveSqlPanel("sales"))
    )
    assert explicit.complete and explicit.removed_panel_ids == ("sales", "costs")
    assert reconcile_sql_script(source, (), ()).complete


def test_all_reorders_keep_ids_even_when_every_query_changes():
    previous = tuple(ExistingSqlPanel(f"panel-{i}", f"SELECT {i}") for i in range(3))
    for ordering in permutations(range(3)):
        source, statements = parsed_fragments(*(f"SELECT {i + 10}" for i in ordering))
        plan = reconcile_sql_script(
            source,
            statements,
            previous,
            tuple(KeepSqlPanel(index, f"panel-{i}") for index, i in enumerate(ordering)),
        )
        assert plan.complete
        assert tuple(item.panel_id for item in plan.statements) == tuple(
            f"panel-{i}" for i in ordering
        )
        assert all(item.sql_changed for item in plan.statements)


@pytest.mark.parametrize(
    "choices",
    [
        (KeepSqlPanel(0, "foreign-dashboard-panel"),),
        (RemoveSqlPanel("unknown"),),
        (KeepSqlPanel(0, "sales"), KeepSqlPanel(1, "sales")),
        (KeepSqlPanel(0, "sales"), RemoveSqlPanel("sales")),
        (RemoveSqlPanel("sales"), RemoveSqlPanel("sales")),
        (KeepSqlPanel(0, "sales"), KeepSqlPanel(0, "costs")),
        (CreateSqlPanel(0, "new"), KeepSqlPanel(0, "sales")),
        (CreateSqlPanel(0, "new"), CreateSqlPanel(1, "new")),
        (CreateSqlPanel(True, "new"),),
        (KeepSqlPanel(-1, "sales"),),
        (KeepSqlPanel(2, "sales"),),
        (KeepSqlPanel(0.0, "sales"),),
        (CreateSqlPanel(0, ""),),
        (CreateSqlPanel(0, " new"),),
        (CreateSqlPanel(0, "new\x00"),),
        (CreateSqlPanel(0, "\ud800"),),
        (CreateSqlPanel(0, "n" * 257),),
        (CreateSqlPanel(0, "\U0001f680" * 65),),
        (object(),),
    ],
)
def test_conflicting_unknown_or_malformed_decisions_are_rejected(choices):
    source, statements = parsed_fragments("SELECT 1", "SELECT 2")
    with pytest.raises(SqlReconciliationError) as error:
        reconcile_sql_script(source, statements, PANELS, choices)
    assert error.value.code == "sql_reconciliation_invalid"


@pytest.mark.parametrize(
    "statements",
    [
        (SqlStatement("SELECT 2", 0, 8),),  # stale parse
        (SqlStatement("SELECT 1", True, 8),),
        (SqlStatement("SELECT 1", -1, 7),),
        (SqlStatement("SELECT 1", 0, 9),),
        (SqlStatement("SELECT 1", 0, 8), SqlStatement("SELECT 1", 0, 8)),
        (SqlStatement("", 0, 0),),
        (SqlStatement("\ud800", 0, 1),),
        (object(),),
    ],
)
def test_stale_or_invalid_source_positions_cannot_be_used_for_choices(statements):
    with pytest.raises(SqlReconciliationError) as error:
        reconcile_sql_script("SELECT 1", statements, ())
    assert error.value.code == "sql_reconciliation_invalid"


def test_utf16_positions_preserve_emoji_comments_and_semicolons():
    first = "SELECT '\U0001f680;a' /* ; */"
    second = "SELECT 2 -- ;"
    source, statements = parsed_fragments(first, second)
    plan = reconcile_sql_script(
        source, statements, (), (CreateSqlPanel(0, "a"), CreateSqlPanel(1, "b"))
    )
    assert plan.complete
    assert tuple(item.statement.sql for item in plan.statements) == (first, second)
    assert plan.statements[1].statement.start_offset == len(first) + 4


def test_result_is_immutable_and_detached_from_input_collections():
    source, statements = parsed_fragments("SELECT 1")
    panels = [PANELS[0]]
    decisions = [KeepSqlPanel(0, "sales")]
    plan = reconcile_sql_script(source, statements, panels, decisions)
    statements.clear()
    panels.clear()
    decisions.clear()
    assert plan.complete and plan.statements[0].panel_id == "sales"
    with pytest.raises(FrozenInstanceError):
        plan.removed_panel_ids = ("sales",)
    with pytest.raises(FrozenInstanceError):
        plan.statements[0].panel_id = "costs"


@pytest.mark.parametrize(
    "panels",
    [
        (PANELS[0], PANELS[0]),
        (ExistingSqlPanel(" sales", "SELECT 1"),),
        (object(),),
    ],
)
def test_invalid_existing_snapshot_is_rejected(panels):
    with pytest.raises(SqlReconciliationError):
        reconcile_sql_script("", (), panels)


@pytest.mark.parametrize("kind", ["statements", "panels", "decisions"])
def test_bounded_inputs_reject_over_budget_before_processing(kind):
    args = {"statements": (), "existing_panels": (), "decisions": ()}
    if kind == "statements":
        args["statements"] = [SqlStatement("SELECT 1", 0, 8)] * 257
    elif kind == "panels":
        args["existing_panels"] = [PANELS[0]] * 257
    else:
        args["decisions"] = [RemoveSqlPanel("sales")] * 513
    with pytest.raises(SqlReconciliationError) as error:
        reconcile_sql_script("SELECT 1", **args)
    assert error.value.code == "sql_reconciliation_limit"


def test_exact_statement_budget_is_supported_without_allocating_panel_ids():
    source, statements = parsed_fragments(*(f"SELECT {i}" for i in range(256)))
    plan = reconcile_sql_script(
        source, statements, (), tuple(CreateSqlPanel(i, f"draft-{i}") for i in range(256))
    )
    assert plan.complete and len(plan.statements) == 256
    assert all(isinstance(item, SqlPanelCreation) for item in plan.statements)


def test_source_budget_is_shared_with_native_parsing():
    with pytest.raises(SqlScriptError) as error:
        reconcile_sql_script("a" * (1024 * 1024 + 1), (), ())
    assert error.value.code == "sql_script_limit"


@pytest.mark.parametrize("field", ["statements", "existing_panels", "decisions"])
def test_untyped_sequences_are_not_coerced(field):
    args = {"statements": (), "existing_panels": (), "decisions": ()}
    args[field] = ""
    with pytest.raises(SqlReconciliationError):
        reconcile_sql_script("", **args)
