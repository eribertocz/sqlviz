"""Source-preserving SQL script contract; no parsing engine or database here."""

from __future__ import annotations

from dataclasses import dataclass

MAX_SQL_SCRIPT_BYTES = 1024 * 1024
MAX_SQL_SCRIPT_STATEMENTS = 256


class SqlScriptError(ValueError):
    def __init__(self, code: str, detail: str):
        super().__init__(detail)
        self.code = code
        self.detail = detail


@dataclass(frozen=True)
class SqlStatement:
    """An original source slice; offsets are UTF-16 units for Monaco/JavaScript."""

    sql: str
    start_offset: int
    end_offset: int


def validate_sql_script(sql: str) -> None:
    if not isinstance(sql, str):
        raise SqlScriptError("sql_script_invalid", "SQL must be text")
    # Native parsers may treat NUL as the end of the source and ignore its tail.
    if "\x00" in sql:
        raise SqlScriptError("sql_script_invalid", "SQL must not contain NUL characters")
    try:
        size = len(sql.encode("utf-8"))
    except UnicodeEncodeError:
        raise SqlScriptError("sql_script_invalid", "SQL must be valid UTF-8 text") from None
    if size > MAX_SQL_SCRIPT_BYTES:
        raise SqlScriptError("sql_script_limit", "SQL script exceeds the UTF-8 size limit")
