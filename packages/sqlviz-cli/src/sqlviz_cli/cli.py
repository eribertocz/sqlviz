"""SQLviz CLI — argument parsing and startup orchestration."""

from __future__ import annotations

import argparse
import getpass
import sys
from pathlib import Path

import duckdb
from sqlviz_storage.auth import set_admin_password
from sqlviz_storage.project_db import create_project, is_sqlviz_project, open_project

from sqlviz_cli.server import serve

_VERSION = "0.1.0"
_LINE = "-" * 42


def _banner(subtitle: str = "") -> None:
    title = f"SQLviz {_VERSION}"
    if subtitle:
        title = f"{title} - {subtitle}"
    print(f"\n{title}")
    print(_LINE)


def _setup_password(conn: duckdb.DuckDBPyConnection) -> None:
    """Interactive prompt: set admin password on first project creation."""
    print()
    while True:
        pw = getpass.getpass("  Set admin password:  ")
        if len(pw) < 4:
            print("  Password must be at least 4 characters.\n")
            continue
        pw2 = getpass.getpass("  Confirm password:    ")
        if pw != pw2:
            print("  Passwords do not match.\n")
            continue
        break
    set_admin_password(conn, pw)
    print()


def _resolve_path(raw: str) -> Path:
    """Return path with .sqlviz extension, adding it if absent."""
    p = Path(raw)
    if p.suffix != ".sqlviz":
        p = p.with_suffix(".sqlviz")
    return p


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="sqlviz",
        description="SQLviz — SQL to dashboard in seconds.",
    )
    parser.add_argument(
        "project",
        nargs="?",
        metavar="PROJECT",
        help=(
            "Path to a .sqlviz project file.  "
            "Omit to run in demo mode (in-memory, nothing saved)."
        ),
    )
    parser.add_argument(
        "--port",
        type=int,
        default=4000,
        metavar="PORT",
        help="HTTP port (default: 4000).",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        metavar="HOST",
        help="Bind address (default: 127.0.0.1).",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Do not open the browser automatically.",
    )
    args = parser.parse_args()

    if args.project is None:
        # ── Demo mode ────────────────────────────────────────────────────────
        _banner("Demo Mode")
        print("In-memory database. Nothing is saved.\n")

        conn = create_project(":memory:")

        serve(
            conn=conn,
            db_path=None,
            host=args.host,
            port=args.port,
            open_browser=not args.no_browser,
        )

    else:
        # ── Persistent mode ──────────────────────────────────────────────────
        path = _resolve_path(args.project)

        if path.exists() and not is_sqlviz_project(path):
            print(
                f"Error: '{path}' exists but is not a valid .sqlviz project.",
                file=sys.stderr,
            )
            sys.exit(1)

        if path.exists():
            # ── Open existing project ────────────────────────────────────────
            _banner()
            print(f"Opening: {path}\n")
            try:
                conn = open_project(str(path))
            except (FileNotFoundError, ValueError) as exc:
                print(f"Error: {exc}", file=sys.stderr)
                sys.exit(1)
        else:
            # ── Create new project ───────────────────────────────────────────
            _banner()
            print(f"Creating project: {path}\n")
            path.parent.mkdir(parents=True, exist_ok=True)
            conn = create_project(str(path))
            _setup_password(conn)
            print("Project created.\n")

        serve(
            conn=conn,
            db_path=str(path),
            host=args.host,
            port=args.port,
            open_browser=not args.no_browser,
        )
