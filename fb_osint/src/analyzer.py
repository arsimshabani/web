from __future__ import annotations

import re
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


WORD_RE = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ0-9_#@]{3,}")


@dataclass
class PostHit:
    page_id: str
    page_name: str
    post_id: str
    created_time: str | None
    message: str
    permalink: str | None
    reactions: int
    comments: int
    shares: int
    score: float
    matched_terms: list[str]


@dataclass
class ThemeReport:
    theme: str
    generated_at: str
    pages_scanned: int
    posts_scanned: int
    matching_posts: int
    total_reactions: int
    total_comments: int
    total_shares: int
    top_terms: list[dict[str, Any]]
    page_summaries: list[dict[str, Any]]
    top_posts: list[dict[str, Any]]
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _tokenize(theme: str) -> list[str]:
    parts = [p.strip().lower() for p in re.split(r"[,|;]+", theme) if p.strip()]
    if len(parts) == 1:
        # Also split multi-word themes into tokens for softer matching
        words = [w for w in parts[0].split() if len(w) >= 3]
        return list(dict.fromkeys(parts + words))
    return list(dict.fromkeys(parts))


def _engagement(post: dict[str, Any]) -> tuple[int, int, int]:
    reactions = int(((post.get("reactions") or {}).get("summary") or {}).get("total_count") or 0)
    comments = int(((post.get("comments") or {}).get("summary") or {}).get("total_count") or 0)
    shares = int((post.get("shares") or {}).get("count") or 0)
    return reactions, comments, shares


def _match_score(text: str, terms: list[str]) -> tuple[float, list[str]]:
    lowered = text.lower()
    matched = [t for t in terms if t and t in lowered]
    if not matched:
        return 0.0, []
    # Prefer denser matches and longer terms
    score = sum(1.5 if len(t) >= 6 else 1.0 for t in matched)
    if all(t in lowered for t in terms if len(t) >= 4):
        score += 2.0
    return score, matched


def analyze_theme(
    theme: str,
    pages: list[dict[str, Any]],
    posts_by_page: dict[str, list[dict[str, Any]]],
    *,
    top_n: int = 15,
) -> ThemeReport:
    terms = _tokenize(theme)
    hits: list[PostHit] = []
    term_counter: Counter[str] = Counter()
    page_summaries: list[dict[str, Any]] = []
    posts_scanned = 0
    notes: list[str] = []

    if not terms:
        notes.append("Theme produced no searchable terms.")

    for page in pages:
        page_id = str(page.get("id") or "")
        page_name = str(page.get("name") or page.get("username") or page_id)
        posts = posts_by_page.get(page_id, [])
        page_hits = 0
        page_reactions = 0
        page_comments = 0
        page_shares = 0

        for post in posts:
            posts_scanned += 1
            message = (post.get("message") or post.get("story") or "").strip()
            if not message:
                continue
            score, matched = _match_score(message, terms)
            reactions, comments, shares = _engagement(post)
            page_reactions += reactions
            page_comments += comments
            page_shares += shares

            for token in WORD_RE.findall(message.lower()):
                if token.startswith(("http", "www")):
                    continue
                term_counter[token] += 1

            if score <= 0:
                continue
            page_hits += 1
            hits.append(
                PostHit(
                    page_id=page_id,
                    page_name=page_name,
                    post_id=str(post.get("id") or ""),
                    created_time=post.get("created_time"),
                    message=message[:500],
                    permalink=post.get("permalink_url"),
                    reactions=reactions,
                    comments=comments,
                    shares=shares,
                    score=score + (reactions * 0.01) + (comments * 0.02) + (shares * 0.03),
                    matched_terms=matched,
                )
            )

        page_summaries.append(
            {
                "id": page_id,
                "name": page_name,
                "username": page.get("username"),
                "category": page.get("category"),
                "fan_count": page.get("fan_count") or page.get("followers_count"),
                "link": page.get("link"),
                "verification_status": page.get("verification_status"),
                "about": (page.get("about") or "")[:280],
                "posts_scanned": len(posts),
                "theme_hits": page_hits,
                "reactions": page_reactions,
                "comments": page_comments,
                "shares": page_shares,
            }
        )

    hits.sort(key=lambda h: h.score, reverse=True)
    top_posts = [asdict(h) for h in hits[:top_n]]
    # Prefer theme-related terms; fall back to corpus terms
    theme_related = [
        {"term": t, "count": term_counter[t]}
        for t in terms
        if term_counter.get(t)
    ]
    corpus_top = [
        {"term": term, "count": count}
        for term, count in term_counter.most_common(20)
        if term not in {t.lower() for t in terms}
    ]

    return ThemeReport(
        theme=theme,
        generated_at=datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        pages_scanned=len(pages),
        posts_scanned=posts_scanned,
        matching_posts=len(hits),
        total_reactions=sum(p["reactions"] for p in page_summaries),
        total_comments=sum(p["comments"] for p in page_summaries),
        total_shares=sum(p["shares"] for p in page_summaries),
        top_terms=theme_related + corpus_top[:12],
        page_summaries=sorted(page_summaries, key=lambda p: p["theme_hits"], reverse=True),
        top_posts=top_posts,
        notes=notes,
    )
