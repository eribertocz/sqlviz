"""Resource ownership and opt-in service startup under success and failure."""

from __future__ import annotations

from unittest.mock import Mock, call

import duckdb
import pytest
from sqlviz_cli import server
from sqlviz_cli.quack import QuackStartupError, quack_session

_TOKEN = "synthetic-test-only-'" + "x" * 32
_URI = "quack:127.0.0.1:9494"


@pytest.fixture
def runtime(monkeypatch: pytest.MonkeyPatch) -> tuple[Mock, Mock, Mock]:
    conn = Mock(spec=duckdb.DuckDBPyConnection)
    config = Mock()
    runner = Mock()
    monkeypatch.setattr(server, "create_app", Mock(return_value=object()))
    monkeypatch.setattr(server.uvicorn, "Config", config)
    monkeypatch.setattr(server.uvicorn, "Server", Mock(return_value=runner))
    # Windows event loop policy is process-global; these tests need no loop.
    monkeypatch.setattr(server.asyncio, "set_event_loop_policy", Mock())
    return conn, config, runner


@pytest.mark.parametrize("db_path", [None, "example.sqlviz"])
def test_default_server_has_no_extension_or_extra_listener(
    db_path: str | None, runtime: tuple[Mock, Mock, Mock]
) -> None:
    conn, config, runner = runtime
    server.serve(conn, db_path=db_path, open_browser=False)
    assert config.call_args.kwargs["host"] == "127.0.0.1"
    conn.load_extension.assert_not_called()
    conn.install_extension.assert_not_called()
    conn.execute.assert_not_called()
    runner.run.assert_called_once()
    if db_path:
        conn.cursor.return_value.close.assert_called_once()
    else:
        conn.cursor.assert_not_called()
    # serve owns only derived resources; main owns the project connection.
    conn.close.assert_not_called()


def test_opt_in_loads_only_preinstalled_extension_and_binds_token(
    runtime: tuple[Mock, Mock, Mock], capsys: pytest.CaptureFixture[str]
) -> None:
    conn, _, _ = runtime
    server.serve(conn, db_path=None, open_browser=False, quack_token=_TOKEN)
    conn.load_extension.assert_called_once_with("quack")
    conn.install_extension.assert_not_called()
    assert conn.execute.call_args_list == [
        call("CALL quack_serve(?, token = ?)", [_URI, _TOKEN]),
        call("CALL quack_stop(?)", [_URI]),
    ]
    assert _TOKEN not in capsys.readouterr().out


@pytest.mark.parametrize("failure_at", ["cursor", "app", "config", "run"])
def test_quack_stops_and_cursor_closes_after_partial_startup_failure(
    failure_at: str, runtime: tuple[Mock, Mock, Mock]
) -> None:
    conn, config, runner = runtime
    fail = RuntimeError("injected startup failure")
    target = {"cursor": conn.cursor, "app": server.create_app, "config": config, "run": runner.run}
    target[failure_at].side_effect = fail
    with pytest.raises(RuntimeError, match="injected startup failure"):
        server.serve(conn, db_path="example.sqlviz", open_browser=False, quack_token=_TOKEN)
    assert conn.execute.call_args_list[-1] == call("CALL quack_stop(?)", [_URI])
    if failure_at != "cursor":
        conn.cursor.return_value.close.assert_called_once()


@pytest.mark.parametrize("failure_at", ["load", "start"])
def test_quack_failure_is_redacted_and_does_not_start_http(
    failure_at: str, runtime: tuple[Mock, Mock, Mock], capsys: pytest.CaptureFixture[str]
) -> None:
    conn, config, runner = runtime
    target = conn.load_extension if failure_at == "load" else conn.execute
    target.side_effect = duckdb.Error("engine error includes " + _TOKEN)
    with pytest.raises(QuackStartupError) as exc:
        server.serve(conn, db_path=None, open_browser=False, quack_token=_TOKEN)
    assert _TOKEN not in str(exc.value)
    assert exc.value.__suppress_context__ is True
    assert _TOKEN not in capsys.readouterr().out
    config.assert_not_called()
    runner.run.assert_not_called()
    server.create_app.assert_not_called()
    conn.install_extension.assert_not_called()


def test_invalid_direct_service_credential_has_no_database_side_effects(
    runtime: tuple[Mock, Mock, Mock],
) -> None:
    conn, _, _ = runtime
    with pytest.raises(QuackStartupError):
        server.serve(conn, db_path=None, open_browser=False, quack_token="token")
    conn.load_extension.assert_not_called()
    conn.execute.assert_not_called()


def test_quack_cleanup_failure_does_not_mask_original_error(
    capsys: pytest.CaptureFixture[str],
) -> None:
    conn = Mock(spec=duckdb.DuckDBPyConnection)
    conn.execute.side_effect = [conn, duckdb.Error(_TOKEN)]
    with pytest.raises(RuntimeError, match="original"):
        with quack_session(conn, _TOKEN):
            raise RuntimeError("original")
    assert _TOKEN not in capsys.readouterr().out


def test_keyboard_interrupt_still_stops_quack_and_closes_cursor(
    runtime: tuple[Mock, Mock, Mock],
) -> None:
    conn, _, runner = runtime
    runner.run.side_effect = KeyboardInterrupt
    server.serve(conn, db_path="example.sqlviz", open_browser=False, quack_token=_TOKEN)
    conn.cursor.return_value.close.assert_called_once()
    assert conn.execute.call_args_list[-1] == call("CALL quack_stop(?)", [_URI])


def test_explicit_lan_binding_preserves_browser_origin(
    runtime: tuple[Mock, Mock, Mock], monkeypatch: pytest.MonkeyPatch
) -> None:
    conn, config, _ = runtime
    monkeypatch.setattr(server, "_lan_ip", Mock(return_value="192.168.1.50"))
    thread = Mock()
    monkeypatch.setattr(server.threading, "Thread", thread)
    server.serve(conn, db_path=None, host="0.0.0.0", port=4100)
    assert config.call_args.kwargs["host"] == "0.0.0.0"
    assert thread.call_args.kwargs["args"] == ("http://192.168.1.50:4100",)
