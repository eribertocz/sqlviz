"""Translate validated HTTP choices into core decisions; never infer identity."""

from collections.abc import Sequence

from sqlviz_core.models.sql_reconciliation import (
    CreateSqlPanel,
    KeepSqlPanel,
    RemoveSqlPanel,
    SqlIdentityDecision,
)

from sqlviz_api.sql_script_contract import CreateSqlIdentity, KeepSqlIdentity, SqlIdentityChoice


def identity_decisions(choices: Sequence[SqlIdentityChoice]) -> tuple[SqlIdentityDecision, ...]:
    decisions: list[SqlIdentityDecision] = []
    for choice in choices:
        if isinstance(choice, KeepSqlIdentity):
            decisions.append(KeepSqlPanel(choice.statement_index, choice.panel_id))
        elif isinstance(choice, CreateSqlIdentity):
            decisions.append(CreateSqlPanel(choice.statement_index, choice.creation_key))
        else:
            decisions.append(RemoveSqlPanel(choice.panel_id))
    return tuple(decisions)
