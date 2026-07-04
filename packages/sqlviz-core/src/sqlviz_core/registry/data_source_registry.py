from __future__ import annotations

from sqlviz_core.contracts.data_source import DataSourceContract


class DataSourceRegistry:
    """Global registry of available data sources.

    Class-level storage — one registry per process.
    V0.1: only DuckDB registered at startup.
    Adding sources never requires changing core code (DOC3 Section 6).
    """

    _sources: dict[str, DataSourceContract] = {}

    @classmethod
    def register(cls, source: DataSourceContract) -> None:
        cls._sources[source.name] = source

    @classmethod
    def get(cls, name: str) -> DataSourceContract:
        if name not in cls._sources:
            raise KeyError(f"DataSource '{name}' not registered. Available: {list(cls._sources)}")
        return cls._sources[name]

    @classmethod
    def all(cls) -> list[DataSourceContract]:
        return list(cls._sources.values())

    @classmethod
    def is_registered(cls, name: str) -> bool:
        return name in cls._sources

    @classmethod
    def clear(cls) -> None:
        """Remove all registered sources. Use only in tests."""
        cls._sources.clear()
