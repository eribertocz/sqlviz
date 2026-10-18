"""Bound API bodies before JSON parsing, including chunked requests."""

from __future__ import annotations

from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

MAX_API_BODY_BYTES = 1024 * 1024
MAX_FILTER_BODY_BYTES = 128 * 1024


class RequestBodyLimitMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or not scope["path"].startswith(("/api/v1/", "/view/")):
            await self.app(scope, receive, send)
            return
        path = scope["path"]
        limit = (
            MAX_FILTER_BODY_BYTES
            if path.endswith(("/execute", "/filter-domain"))
            else MAX_API_BODY_BYTES
        )
        for name, value in scope.get("headers", []):
            if name == b"content-length":
                try:
                    declared = int(value)
                    if declared < 0:
                        raise ValueError
                except ValueError:
                    await JSONResponse({"detail": "Invalid content length"}, status_code=400)(
                        scope, receive, send
                    )
                    return
                if declared > limit:
                    await self._reject(scope, receive, send)
                    return
        chunks: list[bytes] = []
        total = 0
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            chunk = message.get("body", b"")
            total += len(chunk)
            if total > limit:
                await self._reject(scope, receive, send)
                return
            chunks.append(chunk)
            if not message.get("more_body", False):
                break
        delivered = False

        async def replay() -> Message:
            nonlocal delivered
            if delivered:
                return await receive()
            delivered = True
            return {"type": "http.request", "body": b"".join(chunks), "more_body": False}

        await self.app(scope, replay, send)

    @staticmethod
    async def _reject(scope: Scope, receive: Receive, send: Send) -> None:
        await JSONResponse(
            {"detail": "Request body exceeds the size limit", "code": "body_limit"}, status_code=413
        )(scope, receive, send)
