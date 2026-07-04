"""Phase 0 smoke test — verifies the workspace is correctly set up."""
import sys


def test_python_version() -> None:
    assert sys.version_info >= (3, 12), f"Python 3.12+ required, got {sys.version}"


def test_sqlviz_core_importable() -> None:
    import sqlviz_core  # noqa: F401


def test_sqlviz_inference_importable() -> None:
    import sqlviz_inference  # noqa: F401


def test_sqlviz_storage_importable() -> None:
    import sqlviz_storage  # noqa: F401


def test_sqlviz_api_importable() -> None:
    import sqlviz_api  # noqa: F401


def test_sqlviz_cli_importable() -> None:
    import sqlviz_cli  # noqa: F401
