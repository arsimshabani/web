from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from .collector import collect_theme_intelligence
from .config import load_settings
from .facebook_client import FacebookClient, FacebookGraphError

ROOT = Path(__file__).resolve().parents[1]
templates = Jinja2Templates(directory=str(ROOT / "web" / "templates"))

app = FastAPI(
    title="FB Public OSINT",
    description="Theme-based public Facebook page intelligence via Meta Graph API.",
    version="0.1.0",
)


class ScanRequest(BaseModel):
    theme: str = Field(..., min_length=2, max_length=200)
    pages: List[str] = Field(default_factory=list)
    posts_per_page: int = Field(default=25, ge=1, le=100)
    try_search: bool = True


@app.get("/", response_class=HTMLResponse)
def home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "report": None, "error": None, "theme": "", "pages": ""},
    )


@app.get("/demo", response_class=HTMLResponse)
def demo(request: Request) -> HTMLResponse:
    """Offline sample report so the UI can be explored without a Meta token."""
    import json

    sample_path = ROOT / "samples" / "example_report.json"
    report = json.loads(sample_path.read_text(encoding="utf-8"))
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "report": report,
            "error": None,
            "theme": report.get("theme", ""),
            "pages": "greennews",
        },
    )


@app.post("/scan", response_class=HTMLResponse)
def scan_form(
    request: Request,
    theme: str = Form(...),
    pages: str = Form(""),
    posts_per_page: int = Form(25),
) -> HTMLResponse:
    page_list = [p.strip() for p in pages.replace("\n", ",").split(",") if p.strip()]
    try:
        settings = load_settings()
        client = FacebookClient(settings)
        report = collect_theme_intelligence(
            client,
            theme,
            page_list,
            posts_per_page=max(1, min(posts_per_page, 100)),
            try_search=not bool(page_list),
        )
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "report": report.to_dict(),
                "error": None,
                "theme": theme,
                "pages": pages,
            },
        )
    except Exception as exc:  # noqa: BLE001 - surface to UI
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "report": None,
                "error": str(exc),
                "theme": theme,
                "pages": pages,
            },
            status_code=400,
        )


@app.post("/api/scan")
def scan_api(body: ScanRequest) -> JSONResponse:
    try:
        settings = load_settings()
        client = FacebookClient(settings)
        report = collect_theme_intelligence(
            client,
            body.theme,
            body.pages,
            posts_per_page=body.posts_per_page,
            try_search=body.try_search and not body.pages,
        )
        return JSONResponse(report.to_dict())
    except (ValueError, FacebookGraphError) as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)


@app.get("/health")
def health() -> dict:
    return {"ok": True}
