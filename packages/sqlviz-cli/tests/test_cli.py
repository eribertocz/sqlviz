"""Startup policy at the public CLI boundary, without opening network services."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import Mock

import duckdb
import pytest
from sqlviz_cli import cli
from sqlviz_cli.quack import QUACK_TOKEN_ENV, QuackStartupError


@pytest.fixture
def startup(monkeypatch: pytest.MonkeyPatch) -> tuple[Mock, Mock]:
    conn = Mock(spec=duckdb.DuckDBPyConnection)
    serve = Mock()
    monkeypatch.setattr(cli, "create_project", Mock(return_value=conn))
    monkeypatch.setattr(cli, "open_project", Mock(return_value=conn))
    monkeypatch.setattr(cli, "is_sqlviz_project", Mock(return_value=True))
    monkeypatch.setattr(cli, "_setup_password", Mock())
    monkeypatch.setattr(cli, "serve", serve)
    monkeypatch.delenv(QUACK_TOKEN_ENV, raising=False)
    return conn, serve


@pytest.mark.parametrize("mode", ["demo", "new", "existing"])
def test_all_modes_default_to_loopback_without_quack(
    mode: str, startup: tuple[Mock, Mock], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    conn, serve = startup
    project = tmp_path / "local.sqlviz"
    if mode == "existing":
        project.touch()
    args = [] if mode == "demo" else [str(project)]
    monkeypatch.setattr(sys, "argv", ["sqlviz", *args, "--no-browser"])
    # A credential alone must never enable another listener.
    monkeypatch.setenv(QUACK_TOKEN_ENV, "a" * 32)

    cli.main()

    serve.assert_called_once_with(
        conn=conn,
        db_path=None if mode == "demo" else str(project),
        host="127.0.0.1",
        port=4000,
        open_browser=False,
        quack_token=None,
    )
    conn.close.assert_called_once()


def test_explicit_lan_and_port_remain_available(
    startup: tuple[Mock, Mock], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(sys, "argv", ["sqlviz", "--host", "0.0.0.0", "--port", "4100"])
    cli.main()
    assert startup[1].call_args.kwargs["host"] == "0.0.0.0"
    assert startup[1].call_args.kwargs["port"] == 4100
    assert startup[1].call_args.kwargs["open_browser"] is True


@pytest.mark.parametrize("token", [None, "", "token", " " * 32, " " + "x" * 31])
def test_quack_requires_credential_before_creating_a_project(
    token: str | None,
    startup: tuple[Mock, Mock],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    project = tmp_path / "not-created" / "project.sqlviz"
    monkeypatch.setattr(sys, "argv", ["sqlviz", str(project), "--quack"])
    if token is not None:
        monkeypatch.setenv(QUACK_TOKEN_ENV, token)
    with pytest.raises(SystemExit) as exc:
        cli.main()
    assert exc.value.code == 2
    cli.create_project.assert_not_called()
    cli.open_project.assert_not_called()
    startup[1].assert_not_called()
    assert not project.parent.exists()
    assert QUACK_TOKEN_ENV in capsys.readouterr().err


def test_quack_opt_in_uses_environment_without_logging_it(
    startup: tuple[Mock, Mock], monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    token = "test-only-credential-" + "x" * 32
    monkeypatch.setenv(QUACK_TOKEN_ENV, token)
    monkeypatch.setattr(sys, "argv", ["sqlviz", "--quack", "--no-browser"])
    cli.main()
    assert startup[1].call_args.kwargs["quack_token"] == token
    output = capsys.readouterr()
    assert token not in output.out + output.err


@pytest.mark.parametrize(
    "failure", [RuntimeError("startup failed"), KeyboardInterrupt(), SystemExit(1)]
)
def test_cli_closes_owned_connection_on_server_failure(
    failure: BaseException, startup: tuple[Mock, Mock], monkeypatch: pytest.MonkeyPatch
) -> None:
    conn, serve = startup
    serve.side_effect = failure
    monkeypatch.setattr(sys, "argv", ["sqlviz", "--no-browser"])
    with pytest.raises(type(failure)):
        cli.main()
    conn.close.assert_called_once()


def test_explicit_quack_failure_exits_instead_of_continuing(
    startup: tuple[Mock, Mock], monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    startup[1].side_effect = QuackStartupError("Could not start local Quack.")
    monkeypatch.setattr(sys, "argv", ["sqlviz", "--no-browser"])
    with pytest.raises(SystemExit) as exc:
        cli.main()
    assert exc.value.code == 1
    startup[0].close.assert_called_once()
    assert "Could not start local Quack" in capsys.readouterr().err


def test_password_prompt_interruption_closes_new_project(
    startup: tuple[Mock, Mock], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(cli, "_setup_password", Mock(side_effect=KeyboardInterrupt))
    monkeypatch.setattr(sys, "argv", ["sqlviz", str(tmp_path / "new.sqlviz")])
    with pytest.raises(KeyboardInterrupt):
        cli.main()
    startup[0].close.assert_called_once()
    startup[1].assert_not_called()
