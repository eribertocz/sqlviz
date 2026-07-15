#!/usr/bin/env python3
"""Bump the version across all SQLviz project files.

Usage:
    python scripts/bump_version.py 0.2.2
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent

# (file path relative to ROOT, regex pattern, replacement template)
_TARGETS: list[tuple[str, str, str]] = [
    # pyproject.toml files — match only the [project] version line
    ("packages/sqlviz-api/pyproject.toml",       r'^version = "[^"]+"', 'version = "{}"'),
    ("packages/sqlviz-core/pyproject.toml",      r'^version = "[^"]+"', 'version = "{}"'),
    ("packages/sqlviz-inference/pyproject.toml", r'^version = "[^"]+"', 'version = "{}"'),
    ("packages/sqlviz-storage/pyproject.toml",   r'^version = "[^"]+"', 'version = "{}"'),
    ("packages/sqlviz-cli/pyproject.toml",       r'^version = "[^"]+"', 'version = "{}"'),
    # package.json
    ("packages/sqlviz-web/package.json",         r'"version": "[^"]+"', '"version": "{}"'),
    # meta.py — the API endpoint that exposes the version at runtime
    (
        "packages/sqlviz-api/src/sqlviz_api/routers/meta.py",
        r'^_VERSION = "[^"]+"',
        '_VERSION = "{}"',
    ),
]


def bump(new_version: str) -> None:
    # Validate semver-ish format
    if not re.fullmatch(r"\d+\.\d+\.\d+.*", new_version):
        sys.exit(f"Error: '{new_version}' is not a valid version (expected X.Y.Z)")

    changed: list[str] = []
    unchanged: list[str] = []

    for rel_path, pattern, template in _TARGETS:
        path = ROOT / rel_path
        if not path.exists():
            print(f"  SKIP  {rel_path}  (file not found)")
            continue

        original = path.read_text(encoding="utf-8")
        replacement = template.format(new_version)
        updated = re.sub(pattern, replacement, original, flags=re.MULTILINE)

        if updated == original:
            unchanged.append(rel_path)
        else:
            # Write without BOM, preserve line endings
            path.write_text(updated, encoding="utf-8")
            changed.append(rel_path)

    if changed:
        print(f"Bumped to {new_version}:")
        for p in changed:
            print(f"  ✓  {p}")
    if unchanged:
        print("Already at target version (no change):")
        for p in unchanged:
            print(f"  –  {p}")

    if not changed:
        print("Nothing to update.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(f"Usage: python {Path(__file__).name} <version>")
    bump(sys.argv[1])
