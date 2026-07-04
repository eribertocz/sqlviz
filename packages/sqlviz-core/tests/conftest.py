from collections.abc import Generator

import pytest
from sqlviz_core.registry import DataSourceRegistry, VizEngineRegistry


@pytest.fixture(autouse=True)
def clean_registries() -> Generator[None, None, None]:
    """Reset both registries before every test to prevent state leakage."""
    DataSourceRegistry.clear()
    VizEngineRegistry.clear()
    yield
    DataSourceRegistry.clear()
    VizEngineRegistry.clear()
