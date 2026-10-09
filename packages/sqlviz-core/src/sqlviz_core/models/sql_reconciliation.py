"""Explicit SQL-to-panel identity decisions, independent of storage and renderers.

Statement indexes address this parsed source only. They never establish identity.
The application supplies confirmed author choices or tracked edit provenance.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from .sql_script import MAX_SQL_SCRIPT_STATEMENTS, SqlStatement, validate_sql_script


class SqlReconciliationError(ValueError):
    def __init__(self, code: str, detail: str) -> None:
        super().__init__(detail)
        self.code = code
        self.detail = detail


@dataclass(frozen=True)
class ExistingSqlPanel:
    panel_id: str
    sql: str


@dataclass(frozen=True)
class KeepSqlPanel:
    statement_index: int
    panel_id: str


@dataclass(frozen=True)
class CreateSqlPanel:
    statement_index: int
    creation_key: str


@dataclass(frozen=True)
class RemoveSqlPanel:
    panel_id: str


SqlIdentityDecision = KeepSqlPanel | CreateSqlPanel | RemoveSqlPanel


@dataclass(frozen=True)
class SqlPanelUpdate:
    statement_index: int
    panel_id: str
    previous_sql: str
    statement: SqlStatement

    @property
    def sql_changed(self) -> bool:
        return self.previous_sql != self.statement.sql


@dataclass(frozen=True)
class SqlPanelCreation:
    statement_index: int
    creation_key: str
    statement: SqlStatement


@dataclass(frozen=True)
class SqlReconciliationPlan:
    source: str
    statements: tuple[SqlPanelUpdate | SqlPanelCreation, ...]
    removed_panel_ids: tuple[str, ...]
    unresolved_statement_indexes: tuple[int, ...]
    unresolved_panel_ids: tuple[str, ...]

    @property
    def complete(self) -> bool:
        return not self.unresolved_statement_indexes and not self.unresolved_panel_ids

    def require_complete(self) -> None:
        """Admission guard for a future atomic writer; does not perform writes."""
        if not self.complete:
            raise SqlReconciliationError(
                "sql_reconciliation_unresolved", "SQL identity decisions are still required"
            )


def _invalid(detail: str) -> SqlReconciliationError:
    return SqlReconciliationError("sql_reconciliation_invalid", detail)


def _identifier(value: str) -> None:
    # IDs are opaque. Never normalize, derive from SQL, or allocate persistence IDs here.
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or any(ord(char) < 32 or 127 <= ord(char) <= 159 for char in value)
    ):
        raise _invalid("Identity must be nonempty text without surrounding space or controls")
    try:
        encoded = value.encode("utf-8")
    except UnicodeEncodeError:
        raise _invalid("Identity must be valid UTF-8 text") from None
    if len(encoded) > 256:
        raise _invalid("Identity exceeds the UTF-8 byte budget")


def reconcile_sql_script(
    source: str,
    statements: Sequence[SqlStatement],
    existing_panels: Sequence[ExistingSqlPanel],
    decisions: Sequence[SqlIdentityDecision] = (),
) -> SqlReconciliationPlan:
    """Build a bounded, immutable proposal from native parsing and explicit decisions.

    The caller loads panels from one authorized dashboard and supplies parsing for
    this exact source. Equal SQL, position, labels and fingerprints are deliberately
    not matching rules. Missing choices remain unresolved, including old panels
    that would otherwise be silently discarded. A creation key identifies a draft
    choice, not a persisted panel or an HTTP idempotency guarantee.
    """
    validate_sql_script(source)
    for items, maximum in (
        (statements, MAX_SQL_SCRIPT_STATEMENTS),
        (existing_panels, MAX_SQL_SCRIPT_STATEMENTS),
        (decisions, MAX_SQL_SCRIPT_STATEMENTS * 2),
    ):
        if not isinstance(items, Sequence) or isinstance(items, (str, bytes)):
            raise _invalid("Reconciliation inputs must be sequences")
        if len(items) > maximum:
            raise SqlReconciliationError("sql_reconciliation_limit", "Too many identity entries")

    parsed = tuple(statements)
    previous = tuple(existing_panels)
    choices = tuple(decisions)
    utf16_source = source.encode("utf-16-le")
    last_end = 0
    for statement in parsed:
        if not isinstance(statement, SqlStatement):
            raise _invalid("Expected a parsed SQL statement")
        if (
            type(statement.start_offset) is not int
            or type(statement.end_offset) is not int
            or statement.start_offset < last_end
            or statement.end_offset <= statement.start_offset
            or statement.end_offset * 2 > len(utf16_source)
            or not isinstance(statement.sql, str)
            or not statement.sql.strip()
        ):
            raise _invalid("Parsed SQL source span is invalid")
        try:
            fragment = statement.sql.encode("utf-16-le")
        except UnicodeEncodeError:
            raise _invalid("Parsed SQL must be valid UTF-16 text") from None
        if utf16_source[statement.start_offset * 2 : statement.end_offset * 2] != fragment:
            raise _invalid("Parsed SQL does not match the supplied source")
        last_end = statement.end_offset

    panels: dict[str, ExistingSqlPanel] = {}
    for panel in previous:
        if not isinstance(panel, ExistingSqlPanel):
            raise _invalid("Expected an existing SQL panel")
        _identifier(panel.panel_id)
        validate_sql_script(panel.sql)
        if panel.panel_id in panels:
            raise _invalid("Existing panel identities must be unique")
        panels[panel.panel_id] = panel

    assigned: dict[int, SqlPanelUpdate | SqlPanelCreation] = {}
    decided_panels: set[str] = set()
    removed: set[str] = set()
    creation_keys: set[str] = set()
    for choice in choices:
        if not isinstance(choice, (KeepSqlPanel, CreateSqlPanel, RemoveSqlPanel)):
            raise _invalid("Unknown identity decision")
        if isinstance(choice, (KeepSqlPanel, RemoveSqlPanel)):
            _identifier(choice.panel_id)
            if choice.panel_id not in panels:
                raise _invalid("Decision references a panel outside this snapshot")
            if choice.panel_id in decided_panels:
                raise _invalid("An existing panel cannot be kept or removed more than once")
            decided_panels.add(choice.panel_id)
        if isinstance(choice, RemoveSqlPanel):
            removed.add(choice.panel_id)
            continue
        index = choice.statement_index
        if type(index) is not int or not 0 <= index < len(parsed):
            raise _invalid("Decision references a statement outside this source")
        if index in assigned:
            raise _invalid("A statement cannot have more than one identity decision")
        if isinstance(choice, KeepSqlPanel):
            assigned[index] = SqlPanelUpdate(
                index,
                choice.panel_id,
                panels[choice.panel_id].sql,
                parsed[index],
            )
        else:
            _identifier(choice.creation_key)
            if choice.creation_key in creation_keys:
                raise _invalid("Creation keys must be unique within a proposal")
            creation_keys.add(choice.creation_key)
            assigned[index] = SqlPanelCreation(index, choice.creation_key, parsed[index])

    return SqlReconciliationPlan(
        source=source,
        statements=tuple(assigned[index] for index in sorted(assigned)),
        removed_panel_ids=tuple(panel.panel_id for panel in previous if panel.panel_id in removed),
        unresolved_statement_indexes=tuple(
            index for index in range(len(parsed)) if index not in assigned
        ),
        unresolved_panel_ids=tuple(
            panel.panel_id for panel in previous if panel.panel_id not in decided_panels
        ),
    )
