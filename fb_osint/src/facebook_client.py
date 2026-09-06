from __future__ import annotations

from typing import Any

import requests

from .config import Settings


class FacebookGraphError(RuntimeError):
    def __init__(self, message: str, status_code: int | None = None, payload: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload


class FacebookClient:
    """Thin Meta Graph API client for public page/post reads."""

    def __init__(self, settings: Settings, session: requests.Session | None = None):
        self.settings = settings
        self.session = session or requests.Session()

    def _request_json(self, url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        response = self.session.get(url, params=params, timeout=30)
        try:
            payload = response.json()
        except ValueError as exc:
            raise FacebookGraphError(
                f"Non-JSON response from Graph API ({response.status_code})",
                status_code=response.status_code,
            ) from exc

        if response.status_code >= 400 or "error" in payload:
            err = payload.get("error", {})
            message = err.get("message") or response.text
            raise FacebookGraphError(message, status_code=response.status_code, payload=payload)
        return payload

    def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        query = dict(params or {})
        query["access_token"] = self.settings.access_token
        url = f"{self.settings.graph_base}/{path.lstrip('/')}"
        return self._request_json(url, query)

    def get_page(self, page_id_or_username: str) -> dict[str, Any]:
        fields = ",".join(
            [
                "id",
                "name",
                "username",
                "about",
                "category",
                "category_list",
                "fan_count",
                "followers_count",
                "link",
                "website",
                "verification_status",
                "location",
                "phone",
                "emails",
            ]
        )
        return self._get(page_id_or_username, {"fields": fields})

    def get_page_posts(
        self,
        page_id: str,
        *,
        limit: int = 25,
        max_pages: int = 3,
    ) -> list[dict[str, Any]]:
        fields = ",".join(
            [
                "id",
                "message",
                "story",
                "created_time",
                "permalink_url",
                "shares",
                "reactions.summary(true).limit(0)",
                "comments.summary(true).limit(0)",
            ]
        )
        params: dict[str, Any] = {
            "fields": fields,
            "limit": min(max(limit, 1), 100),
            "access_token": self.settings.access_token,
        }
        posts: list[dict[str, Any]] = []
        url: str | None = f"{self.settings.graph_base}/{page_id}/posts"
        pages_fetched = 0

        while url and pages_fetched < max_pages and len(posts) < limit:
            payload = self._request_json(url, params if pages_fetched == 0 else None)
            posts.extend(payload.get("data") or [])
            pages_fetched += 1
            url = (payload.get("paging") or {}).get("next")
            params = None  # next URL already contains query params

        return posts[:limit]

    def search_pages(self, query: str, *, limit: int = 10) -> list[dict[str, Any]]:
        """Best-effort page search. Availability depends on app permissions."""
        payload = self._get(
            "pages/search",
            {
                "q": query,
                "fields": "id,name,username,category,fan_count,link,verification_status",
                "limit": limit,
            },
        )
        return payload.get("data") or []
