from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


class YAMLLoader:
    """
    Loads and caches YAML rule files from the rules/ directory.
    All modules use this singleton — never load YAML directly.
    Files are loaded once and cached; restart to pick up changes.
    """

    def __init__(self) -> None:
        # yaml_loader.py lives at sqlviz_inference/utils/yaml_loader.py
        # Two .parent calls → sqlviz_inference/ (works in dev and installed wheel)
        self._rules_dir = Path(__file__).parent.parent / "rules"
        self._cache: dict[str, Any] = {}

    def load(self, filename: str) -> Any:
        """Load a YAML file from rules/. Returns cached version on repeat calls."""
        if filename not in self._cache:
            path = self._rules_dir / filename
            if not path.exists():
                raise FileNotFoundError(
                    f"Rules file not found: {path}\n"
                    f"Expected directory: {self._rules_dir}"
                )
            with open(path, encoding="utf-8") as f:
                self._cache[filename] = yaml.safe_load(f)
        return self._cache[filename]

    def reload(self, filename: str) -> Any:
        """Force reload a file, bypassing the cache."""
        self._cache.pop(filename, None)
        return self.load(filename)

    def reload_all(self) -> None:
        """Force reload all cached files."""
        self._cache.clear()


# Global singleton — import this everywhere
yaml_loader = YAMLLoader()
