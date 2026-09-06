from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    access_token: str
    api_version: str = "v21.0"
    default_pages: tuple[str, ...] = ()

    @property
    def graph_base(self) -> str:
        return f"https://graph.facebook.com/{self.api_version}"


def load_settings(env_file: str | None = None) -> Settings:
    load_dotenv(env_file)
    token = (os.getenv("FACEBOOK_ACCESS_TOKEN") or "").strip()
    if not token:
        raise ValueError(
            "FACEBOOK_ACCESS_TOKEN is missing. Copy .env.example to .env "
            "and add a Meta Graph API access token."
        )
    version = (os.getenv("FACEBOOK_API_VERSION") or "v21.0").strip()
    pages_raw = (os.getenv("FACEBOOK_DEFAULT_PAGES") or "").strip()
    pages = tuple(p.strip() for p in pages_raw.split(",") if p.strip())
    return Settings(access_token=token, api_version=version, default_pages=pages)
