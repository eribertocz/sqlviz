"""Server startup — uvicorn + optional Quack HTTP server + browser."""

from __future__ import annotations

import asyncio
import socket
import sys
import threading
import time
import webbrowser
from contextlib import ExitStack, closing

import duckdb
import uvicorn
from sqlviz_api.main import create_app

from sqlviz_cli.quack import quack_session

_HOST = "127.0.0.1"
_PORT = 4000


def _open_browser(url: str, delay: float = 1.2) -> None:
    time.sleep(delay)
    webbrowser.open(url)


def _lan_ip() -> str | None:
    """Best-effort LAN IPv4 of this machine (no packets are actually sent)."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))  # picks the outbound interface
            return str(s.getsockname()[0])
        finally:
            s.close()
    except Exception:  # noqa: BLE001
        return None


def serve(
    conn: duckdb.DuckDBPyConnection,
    *,
    db_path: str | None,
    host: str = _HOST,
    port: int = _PORT,
    open_browser: bool = True,
    quack_token: str | None = None,
) -> None:
    """Start FastAPI + uvicorn.  Blocks until Ctrl+C.

    Args:
        conn:         Open read/write DuckDB connection (admin).
        db_path:      Filesystem path to the .sqlviz file, or None for
                      demo mode (in-memory, no read-only viewer conn).
        host:         Bind host (default 127.0.0.1).
        port:         HTTP port (default 4000).
        open_browser: Open the default browser automatically.
        quack_token:  Separate database credential; None disables Quack.
                      The caller owns conn and must close it after serving.
    """
    with ExitStack() as resources:
        resources.enter_context(quack_session(conn, quack_token))

        # A cursor shares the same writable database instance. It is not a
        # read-only security boundary; authorization/isolation are separate work.
        viewer_conn = (
            resources.enter_context(closing(conn.cursor())) if db_path is not None else None
        )
        app = create_app(conn, viewer_conn=viewer_conn, demo_mode=db_path is None)

        # Explicit LAN binding keeps origin-based share URLs reachable.
        if host == "0.0.0.0":
            lan = _lan_ip()
            open_url = f"http://{lan}:{port}" if lan else f"http://127.0.0.1:{port}"
            print(f"  Local:    http://127.0.0.1:{port}")
            if lan:
                print(f"  Network:  http://{lan}:{port}")
        else:
            open_url = f"http://{host}:{port}"
            print(f"  Listening on {open_url}")

        if open_browser:
            print("  Opening browser...")
            threading.Thread(target=_open_browser, args=(open_url,), daemon=True).start()

        print("  Press Ctrl+C to stop.\n")

        # Selector avoids Proactor's noisy socket.shutdown() on reset connections.
        # This process serves plain HTTP and does not spawn asyncio subprocesses.
        if sys.platform == "win32":
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

        config = uvicorn.Config(app=app, host=host, port=port, log_level="warning")
        server = uvicorn.Server(config)
        try:
            server.run()
        except KeyboardInterrupt:
            pass
        finally:
            print("\nServer stopped.")
