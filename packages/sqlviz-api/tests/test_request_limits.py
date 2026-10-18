"""ASGI tests exercise actual streaming, rather than TestClient buffering."""

from __future__ import annotations

import asyncio
import json

import pytest
from sqlviz_api.request_limits import MAX_FILTER_BODY_BYTES, RequestBodyLimitMiddleware


def run(chunks, headers=(), path="/api/v1/panels/p/execute", disconnect=False):
    sent, accepted, consumed = [], [], []
    iterator = iter(chunks)

    async def receive():
        chunk = next(iterator)
        consumed.append(chunk)
        return (
            {"type": "http.disconnect"}
            if disconnect
            else {
                "type": "http.request",
                "body": chunk,
                "more_body": len(consumed) < len(chunks),
            }
        )

    async def send(message):
        sent.append(message)

    async def downstream(scope, receive, send):
        accepted.append((await receive())["body"])

    asyncio.run(
        RequestBodyLimitMiddleware(downstream)(
            {"type": "http", "path": path, "method": "POST", "headers": list(headers)},
            receive,
            send,
        )
    )
    return sent, accepted, consumed


def test_stream_limit_stops_consuming_before_end():
    sent, accepted, consumed = run([b"x" * 65536] * 4)
    assert accepted == []
    assert len(consumed) == 3
    assert sent[0]["status"] == 413
    assert json.loads(sent[1]["body"])["code"] == "body_limit"


def test_content_length_cannot_bypass_actual_byte_limit():
    sent, accepted, _ = run([b"x" * 65536] * 3, [(b"content-length", b"1")])
    assert accepted == []
    assert sent[0]["status"] == 413


def test_declared_oversize_is_rejected_before_receiving():
    sent, accepted, consumed = run(
        [], [(b"content-length", str(MAX_FILTER_BODY_BYTES + 1).encode())]
    )
    assert accepted == []
    assert consumed == []
    assert sent[0]["status"] == 413


@pytest.mark.parametrize("length", [b"oops", b"-1"])
def test_invalid_length_is_bad_request(length):
    sent, accepted, _ = run([b""], [(b"content-length", length)])
    assert accepted == []
    assert sent[0]["status"] == 400


def test_under_budget_body_is_delivered_once_intact():
    sent, accepted, consumed = run([b"{", b"}"])
    assert sent == []
    assert accepted == [b"{}"]
    assert len(consumed) == 2


def test_disconnect_does_not_parse_partial_json():
    _, accepted, _ = run([b"{"], disconnect=True)
    assert accepted == []
