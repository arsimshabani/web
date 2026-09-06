from src.analyzer import analyze_theme


def test_analyze_theme_scores_matching_posts():
    pages = [
        {
            "id": "1",
            "name": "Green News",
            "username": "greennews",
            "category": "Media",
            "fan_count": 1000,
            "link": "https://facebook.com/greennews",
            "about": "Climate coverage",
        }
    ]
    posts = {
        "1": [
            {
                "id": "1_1",
                "message": "New investment in solar energy across the region",
                "created_time": "2026-01-01T10:00:00+0000",
                "permalink_url": "https://facebook.com/1",
                "reactions": {"summary": {"total_count": 40}},
                "comments": {"summary": {"total_count": 5}},
                "shares": {"count": 3},
            },
            {
                "id": "1_2",
                "message": "Football match highlights tonight",
                "created_time": "2026-01-02T10:00:00+0000",
                "reactions": {"summary": {"total_count": 90}},
                "comments": {"summary": {"total_count": 20}},
                "shares": {"count": 8},
            },
        ]
    }

    report = analyze_theme("solar energy", pages, posts)
    assert report.pages_scanned == 1
    assert report.posts_scanned == 2
    assert report.matching_posts == 1
    assert report.top_posts[0]["post_id"] == "1_1"
    assert "solar" in report.top_posts[0]["matched_terms"]
    assert report.total_reactions == 130


def test_analyze_theme_handles_empty_corpus():
    report = analyze_theme("kosove", [], {})
    assert report.matching_posts == 0
    assert report.pages_scanned == 0
