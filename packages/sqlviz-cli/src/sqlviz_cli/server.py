"""Server startup — uvicorn + optional Quack HTTP server + browser."""

from __future__ import annotations

import threading
import time
import webbrowser

import duckdb
import uvicorn
from sqlviz_api.main import create_app

_HOST = "127.0.0.1"
_PORT = 4000


def _open_browser(url: str, delay: float = 1.2) -> None:
    time.sleep(delay)
    webbrowser.open(url)


def _try_start_quack(admin_conn: duckdb.DuckDBPyConnection) -> None:
    """Start Quack HTTP server via DuckDB core extension (v1.5.3+), or degrade gracefully."""
    try:
        admin_conn.execute("INSTALL quack FROM core_nightly")
        admin_conn.execute("LOAD quack")
        admin_conn.execute("CALL quack_serve('quack:localhost', token = 'token')")
        print("  Quack:    quack://localhost")
    except Exception:  # noqa: BLE001
        print("  [warn] quack not available — requires DuckDB v1.5.3+")


def serve(
    conn: duckdb.DuckDBPyConnection,
    *,
    db_path: str | None,
    host: str = _HOST,
    port: int = _PORT,
    open_browser: bool = True,
) -> None:
    """Start FastAPI + uvicorn.  Blocks until Ctrl+C.

    Args:
        conn:         Open read/write DuckDB connection (admin).
        db_path:      Filesystem path to the .sqlviz file, or None for
                      demo mode (in-memory, no read-only viewer conn).
        host:         Bind host (default 127.0.0.1).
        port:         HTTP port (default 4000).
        open_browser: Open the default browser automatically.
    """
    demo_mode = db_path is None

    # Phase 6 — read-only viewer connection for non-admin requests.
    viewer_conn: duckdb.DuckDBPyConnection | None = None
    if db_path is not None:
        try:
            viewer_conn = duckdb.connect(db_path, read_only=True)
        except Exception as exc:  # noqa: BLE001
            print(f"  [warn] Could not open read-only viewer connection: {exc}")

    app = create_app(conn, viewer_conn=viewer_conn, demo_mode=demo_mode)

    # Try to start the Quack HTTP server (DuckDB core extension).
    _try_start_quack(conn)

    url = f"http://{host}:{port}"
    print(f"  Listening on {url}")

    if open_browser:
        print("  Opening browser...")
        threading.Thread(
            target=_open_browser, args=(url,), daemon=True
        ).start()

    print("  Press Ctrl+C to stop.\n")

    config = uvicorn.Config(
        app=app,
        host=host,
        port=port,
        log_level="warning",   # suppress INFO noise; our banner is the UI
    )
    server = uvicorn.Server(config)

    try:
        server.run()
    except KeyboardInterrupt:
        pass
    finally:
        if viewer_conn is not None:
            try:
                viewer_conn.close()
            except Exception:  # noqa: BLE001
                pass
        print("\nServer stopped.")
