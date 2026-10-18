"""Bounded, app-local attestations of execution and successful composition.

No SQL, rows or long-lived bearer credentials are embedded. A restart deliberately
invalidates pending receipts; recording/recovering a Run across restarts is later work.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

from sqlviz_storage.sql_script_repository import SqlDefinitionReference


class SqlRunReceiptError(Exception):
    """Untrusted, expired or incompatible proof; never expose its contents."""


def _json_numbers(value: object) -> object:
    # JSON has one numeric type. Browser stringify emits 1 for 1.0 and 0 for
    # -0.0; signing Python's representation would reject an unchanged response.
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, dict):
        return {key: _json_numbers(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_numbers(item) for item in value]
    return value


def _canonical(value: object) -> bytes:
    return json.dumps(_json_numbers(value), sort_keys=True, ensure_ascii=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _definition(value: SqlDefinitionReference) -> str:
    # Fixed-size commitments also cover maximum-length Unicode legacy IDs.
    return _digest([value.dashboard_id, value.revision])


class SqlRunReceipts:
    TTL_SECONDS = 900
    MAX_TOKEN_LENGTH = 2048

    def __init__(self, *, clock: Callable[[], float] = time.time) -> None:
        self._key = secrets.token_bytes(32)
        self._clock = clock

    def _issue(self, kind: str, definition: SqlDefinitionReference,
               **claims: object) -> str:
        payload = _canonical({"v": 1, "kind": kind, "definition": _definition(definition),
                              "issued": self._clock(), **claims})
        encoded = base64.urlsafe_b64encode(payload).rstrip(b"=")
        signature = hmac.digest(self._key, encoded, "sha256").hex().encode("ascii")
        token = (encoded + b"." + signature).decode("ascii")
        if len(token) > self.MAX_TOKEN_LENGTH:
            raise SqlRunReceiptError("Receipt capacity exceeded")
        return token

    def _verify(self, token: str, kind: str,
                definition: SqlDefinitionReference) -> dict[str, Any]:
        try:
            if len(token) > self.MAX_TOKEN_LENGTH:
                raise ValueError
            encoded, signature = token.encode("ascii").split(b".")
            expected = hmac.digest(self._key, encoded, "sha256").hex().encode("ascii")
            if not hmac.compare_digest(signature, expected):
                raise ValueError
            claims = json.loads(base64.urlsafe_b64decode(encoded + b"=" * (-len(encoded) % 4)))
            now = self._clock()
            if (claims["v"] != 1 or claims["kind"] != kind
                    or claims["definition"] != _definition(definition)
                    or not 0 <= now - claims["issued"] <= self.TTL_SECONDS):
                raise ValueError
            return claims  # type: ignore[no-any-return]
        except (ValueError, KeyError, TypeError, UnicodeError) as exc:
            raise SqlRunReceiptError("Run proof cannot be verified") from exc

    def execution(self, definition: SqlDefinitionReference, panel_id: str,
                  inference: object, *, executed: bool) -> str:
        return self._issue("execution", definition, panel_id=_digest(panel_id), executed=executed,
                           inference=_digest(inference))

    def verify_execution(self, token: str, definition: SqlDefinitionReference,
                         panel_id: str, inference: object) -> bool:
        claims = self._verify(token, "execution", definition)
        if (claims.get("panel_id") != _digest(panel_id)
                or claims.get("inference") != _digest(inference)):
            raise SqlRunReceiptError("Execution proof is incompatible")
        return claims.get("executed") is True

    def completion(self, definition: SqlDefinitionReference) -> str:
        # Called only after complete composition of verified, actually executed queries.
        completed_at = datetime.fromtimestamp(self._clock(), timezone.utc).isoformat(
            timespec="microseconds")
        return self._issue("completion", definition, completed_at=completed_at)

    def verify_completion(self, token: str, definition: SqlDefinitionReference) -> str:
        claims = self._verify(token, "completion", definition)
        completed_at = claims.get("completed_at")
        if not isinstance(completed_at, str):
            raise SqlRunReceiptError("Completion proof is incompatible")
        return completed_at
