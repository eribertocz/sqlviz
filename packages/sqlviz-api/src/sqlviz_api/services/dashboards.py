"""Dashboard deletion and its post-commit access cleanup, independent of HTTP."""

from __future__ import annotations

from sqlviz_storage.dashboard_repository import DashboardRepository

from sqlviz_api.services.access import SessionStore


class DashboardDeletionService:
    def __init__(self, repository: DashboardRepository, viewer_sessions: SessionStore) -> None:
        self._repository = repository
        self._viewer_sessions = viewer_sessions

    def delete(self, dashboard_id: str) -> None:
        deletion = self._repository.delete(dashboard_id)
        for token in deletion.share_tokens:
            self._viewer_sessions.revoke_binding(token)
