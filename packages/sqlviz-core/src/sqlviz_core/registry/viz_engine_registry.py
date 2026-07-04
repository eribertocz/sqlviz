from __future__ import annotations

from sqlviz_core.contracts.viz_engine import VizEngineContract


class VizEngineRegistry:
    """Global registry of available visualization engines.

    Class-level storage — one registry per process.
    V0.1: only ECharts registered at startup.
    Adding engines never requires changing core code (DOC3 Section 6).
    """

    _engines: dict[str, VizEngineContract] = {}

    @classmethod
    def register(cls, engine: VizEngineContract) -> None:
        cls._engines[engine.name] = engine

    @classmethod
    def get(cls, name: str) -> VizEngineContract:
        if name not in cls._engines:
            raise KeyError(f"VizEngine '{name}' not registered. Available: {list(cls._engines)}")
        return cls._engines[name]

    @classmethod
    def get_for_chart(cls, chart_type: str) -> VizEngineContract:
        """Return the first registered engine that supports chart_type."""
        for engine in cls._engines.values():
            if engine.supports(chart_type):
                return engine
        raise KeyError(f"No VizEngine supports chart type '{chart_type}'")

    @classmethod
    def all(cls) -> list[VizEngineContract]:
        return list(cls._engines.values())

    @classmethod
    def is_registered(cls, name: str) -> bool:
        return name in cls._engines

    @classmethod
    def clear(cls) -> None:
        """Remove all registered engines. Use only in tests."""
        cls._engines.clear()
