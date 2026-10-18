"""Durable draft generations and opaque tokens, independent of presentation."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

MAX_SQL_DRAFT_GENERATION = 2**63 - 1


class SqlDraftMetadataError(ValueError):
    """Stored draft state is invalid; never replace it with an initial revision."""


class SqlDraftRevisionLimitError(ValueError):
    """The durable generation cannot advance without overflowing BIGINT."""


def require_draft_generation(value: object) -> int:
    if type(value) is not int or not 0 <= value <= MAX_SQL_DRAFT_GENERATION:
        raise SqlDraftMetadataError("Invalid stored SQL draft generation")
    return value


def next_draft_generation(value: object) -> int:
    generation = require_draft_generation(value)
    if generation == MAX_SQL_DRAFT_GENERATION:
        raise SqlDraftRevisionLimitError("SQL draft generation exhausted")
    return generation + 1


@dataclass(frozen=True)
class SqlDraftSnapshot:
    dashboard_id: str
    source: str
    generation: int

    @property
    def revision(self) -> str:
        encoded = json.dumps(
            [self.dashboard_id, self.generation, self.source],
            ensure_ascii=True, separators=(",", ":"),
        )
        return "sql-draft-v1:" + hashlib.sha256(encoded.encode("utf-8")).hexdigest()

    @property
    def initialized(self) -> bool:
        # Historical generation zero cannot prove an intentionally empty draft.
        return self.generation > 0 or self.source != ""
