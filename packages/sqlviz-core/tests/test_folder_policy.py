"""Folder hierarchy and patch policy without DuckDB or FastAPI."""

from __future__ import annotations

from typing import cast

import pytest
from sqlviz_core.models.folders import (
    FolderChanges,
    FolderError,
    validate_folder_changes,
    validate_folder_parent,
)


@pytest.mark.parametrize("parent", [None, "root", "sibling"])
def test_valid_destinations(parent) -> None:
    parents = {"root": None, "child": "root", "sibling": "root"}
    validate_folder_parent(parent, parents, folder_id="child")


@pytest.mark.parametrize("parent", ["a", "b", "c"])
def test_self_and_descendants_are_rejected(parent) -> None:
    parents = {"a": None, "b": "a", "c": "b"}
    before = dict(parents)
    with pytest.raises(FolderError) as error:
        validate_folder_parent(parent, parents, folder_id="a")
    assert error.value.code == "folder_cycle"
    assert parents == before


@pytest.mark.parametrize("parents,code", [
    ({}, "folder_parent_not_found"),
    ({"target": "missing"}, "folder_hierarchy_invalid"),
    ({"target": "other", "other": "target"}, "folder_hierarchy_invalid"),
    ({"target": "target"}, "folder_hierarchy_invalid"),
])
def test_missing_and_corrupt_legacy_ancestry_terminate(parents, code) -> None:
    with pytest.raises(FolderError) as error:
        validate_folder_parent("target", parents, folder_id="moving")
    assert error.value.code == code


def test_deep_tree_does_not_depend_on_python_recursion_limit() -> None:
    parents = {str(i): str(i - 1) if i else None for i in range(5000)}
    validate_folder_parent("4999", parents, folder_id="new")
    with pytest.raises(FolderError) as error:
        validate_folder_parent("4999", parents, folder_id="0")
    assert error.value.code == "folder_cycle"


def test_explicit_detach_can_repair_one_folder_without_rewriting_others() -> None:
    parents = {"a": "b", "b": "a", "other": "missing"}
    validate_folder_parent(None, parents, folder_id="a")
    assert parents == {"a": "b", "b": "a", "other": "missing"}


@pytest.mark.parametrize("changes", [
    {"name": None}, {"name": ""}, {"name": "   "},
    {"parent_id": 123}, {"parent_id": []},
    {"sort_order": None}, {"sort_order": True}, {"sort_order": "1"},
    {"sort_order": 2**31}, {"sort_order": -(2**31) - 1},
    {"name = 'bad' --": "bad"},
])
def test_invalid_values_and_unknown_write_columns_are_rejected(changes) -> None:
    with pytest.raises(FolderError) as error:
        validate_folder_changes(cast(FolderChanges, changes))
    assert error.value.code == "folder_values_invalid"


@pytest.mark.parametrize("changes", [
    {}, {"parent_id": None}, {"parent_id": ""},
    {"name": "  Keep spacing  "}, {"sort_order": -(2**31)}, {"sort_order": 2**31 - 1},
])
def test_legal_patch_values(changes) -> None:
    validate_folder_changes(changes)
