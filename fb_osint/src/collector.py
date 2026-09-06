from __future__ import annotations

from typing import Any

from .analyzer import ThemeReport, analyze_theme
from .facebook_client import FacebookClient, FacebookGraphError


def collect_theme_intelligence(
    client: FacebookClient,
    theme: str,
    pages: list[str],
    *,
    posts_per_page: int = 25,
    try_search: bool = True,
) -> ThemeReport:
    """
    Collect public page metadata + posts, then score them against a theme.

    `pages` should be public page usernames or IDs. If empty and try_search=True,
    the tool attempts Graph pages/search (permission-dependent).
    """
    discovered: list[dict[str, Any]] = []
    notes: list[str] = []
    page_inputs = [p.strip() for p in pages if p and p.strip()]

    if not page_inputs and try_search:
        try:
            discovered = client.search_pages(theme, limit=8)
            page_inputs = [str(p.get("id")) for p in discovered if p.get("id")]
            if not page_inputs:
                notes.append(
                    "pages/search returned no results. Provide page usernames/IDs explicitly."
                )
        except FacebookGraphError as exc:
            notes.append(
                "pages/search unavailable for this token/app "
                f"({exc}). Provide page usernames/IDs with --pages."
            )

    page_docs: list[dict[str, Any]] = []
    posts_by_page: dict[str, list[dict[str, Any]]] = {}

    # Keep search metadata if we already have it
    discovered_by_id = {str(p.get("id")): p for p in discovered if p.get("id")}

    for raw in page_inputs:
        try:
            page = client.get_page(raw)
            page_docs.append(page)
            page_id = str(page["id"])
            try:
                posts_by_page[page_id] = client.get_page_posts(
                    page_id, limit=posts_per_page, max_pages=3
                )
            except FacebookGraphError as exc:
                posts_by_page[page_id] = []
                notes.append(f"Could not read posts for {raw}: {exc}")
        except FacebookGraphError as exc:
            # Fall back to search stub if present
            stub = discovered_by_id.get(raw)
            if stub:
                page_docs.append(stub)
                posts_by_page[str(stub.get("id"))] = []
            notes.append(f"Could not read page {raw}: {exc}")

    report = analyze_theme(theme, page_docs, posts_by_page)
    report.notes.extend(notes)
    return report
