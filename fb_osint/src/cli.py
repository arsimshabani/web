from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .collector import collect_theme_intelligence
from .config import load_settings
from .facebook_client import FacebookClient

app = typer.Typer(
    add_completion=False,
    help="Collect public Facebook page stats for a theme via Meta Graph API.",
)
console = Console()


@app.command("scan")
def scan(
    theme: str = typer.Argument(..., help="Theme / keywords, e.g. 'electric cars' or 'kosove,ekonomi'"),
    pages: Optional[str] = typer.Option(
        None,
        "--pages",
        "-p",
        help="Comma-separated public page usernames or IDs",
    ),
    posts: int = typer.Option(25, "--posts", help="Max posts per page"),
    out: Optional[Path] = typer.Option(None, "--out", "-o", help="Write JSON report to file"),
    no_search: bool = typer.Option(
        False,
        "--no-search",
        help="Do not attempt Graph pages/search when --pages is empty",
    ),
) -> None:
    """Scan public pages and produce a theme intelligence report."""
    settings = load_settings()
    page_list = [p.strip() for p in (pages or "").split(",") if p.strip()]
    if not page_list:
        page_list = list(settings.default_pages)

    client = FacebookClient(settings)
    with console.status("Collecting public page data..."):
        report = collect_theme_intelligence(
            client,
            theme,
            page_list,
            posts_per_page=posts,
            try_search=not no_search,
        )

    _print_report(report.to_dict())
    if out:
        out.write_text(json.dumps(report.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        console.print(f"\n[green]Saved report:[/green] {out}")


@app.command("page")
def page_info(
    page: str = typer.Argument(..., help="Public page username or ID"),
) -> None:
    """Fetch metadata for one public page."""
    settings = load_settings()
    client = FacebookClient(settings)
    data = client.get_page(page)
    console.print_json(data=data)


def _print_report(report: dict) -> None:
    console.print(
        Panel.fit(
            f"[bold]{report['theme']}[/bold]\n"
            f"Pages: {report['pages_scanned']} | Posts scanned: {report['posts_scanned']} | "
            f"Matches: {report['matching_posts']}\n"
            f"Reactions: {report['total_reactions']} | Comments: {report['total_comments']} | "
            f"Shares: {report['total_shares']}",
            title="Theme report",
        )
    )

    pages_table = Table(title="Pages")
    pages_table.add_column("Name")
    pages_table.add_column("Fans", justify="right")
    pages_table.add_column("Hits", justify="right")
    pages_table.add_column("Category")
    for page in report["page_summaries"]:
        pages_table.add_row(
            str(page.get("name") or ""),
            str(page.get("fan_count") or "-"),
            str(page.get("theme_hits") or 0),
            str(page.get("category") or "-"),
        )
    console.print(pages_table)

    if report["top_posts"]:
        posts_table = Table(title="Top matching posts")
        posts_table.add_column("Page")
        posts_table.add_column("Score", justify="right")
        posts_table.add_column("R/C/S", justify="right")
        posts_table.add_column("Snippet")
        for post in report["top_posts"][:10]:
            snippet = (post.get("message") or "").replace("\n", " ")
            if len(snippet) > 90:
                snippet = snippet[:87] + "..."
            posts_table.add_row(
                str(post.get("page_name") or ""),
                f"{post.get('score', 0):.2f}",
                f"{post.get('reactions', 0)}/{post.get('comments', 0)}/{post.get('shares', 0)}",
                snippet,
            )
        console.print(posts_table)

    for note in report.get("notes") or []:
        console.print(f"[yellow]note:[/yellow] {note}")


if __name__ == "__main__":
    app()
