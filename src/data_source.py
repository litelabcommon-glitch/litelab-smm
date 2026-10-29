"""
Data source module for LITELAB SMM Suite.

Supports three content backends:
  1. Posts Directory Source (primary) — reads from isolated posts/Post_XX/post.json folders
  2. Google Sheets (collaborative) — reads from a structured spreadsheet
  3. JSON Manifest (fallback) — reads from content_manifest.json
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

ContentItem = dict[str, Any]

def _parse_date(value: str) -> Optional[datetime]:
    """Try to parse a date string in common formats."""
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(value.strip(), fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None

def _normalize_item(raw: dict) -> ContentItem:
    """Normalize a raw row/dict into a standard ContentItem."""
    hashtags = raw.get("hashtags", [])
    if isinstance(hashtags, str):
        hashtags = [h.strip() for h in hashtags.replace(",", " ").split() if h.strip()]

    platforms = raw.get("platforms", [])
    if isinstance(platforms, str):
        platforms = [p.strip().lower() for p in platforms.split(",") if p.strip()]

    media_paths = raw.get("media_paths", [])
    pdf_path = raw.get("pdf_path") or ""

    # If post.json structure with 'media' object:
    if isinstance(raw.get("media"), dict):
        m_dict = raw["media"]
        if "pdf" in m_dict and not pdf_path:
            pdf_path = m_dict["pdf"]
        if "instagram_carousel" in m_dict and not media_paths:
            media_paths = m_dict["instagram_carousel"]

    return {
        "id": raw.get("id", ""),
        "date": raw.get("scheduled_date") or raw.get("date", ""),
        "time": raw.get("time", ""),
        "title": raw.get("title", ""),
        "caption": raw.get("caption", ""),
        "video_url": raw.get("video_url", ""),
        "media_paths": media_paths,
        "pdf_path": pdf_path,
        "hashtags": hashtags,
        "platforms": platforms,
        "status": raw.get("status", "ready"),
    }

REPO_ROOT = Path(__file__).resolve().parent.parent

# ─────────────────────────────────────────────
# 1. Posts Directory Source (Primary for Dedicated Folders)
# ─────────────────────────────────────────────

class PostsDirectorySource:
    """Reads content from dedicated post folders (posts/Post_*/post.json)."""

    def __init__(self, root_dir: str | Path = None) -> None:
        self.root_dir = Path(root_dir) if root_dir else (REPO_ROOT / "posts")

    def fetch_all(self) -> list[ContentItem]:
        items = []
        if not self.root_dir.exists():
            return items

        for post_dir in sorted(self.root_dir.iterdir()):
            if post_dir.is_dir() and not post_dir.name.startswith("."):
                manifest = post_dir / "post.json"
                if manifest.exists():
                    try:
                        with open(manifest, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        data["id"] = data.get("id") or post_dir.name
                        item = _normalize_item(data)
                        items.append(item)
                    except Exception as exc:
                        logger.warning("Could not read post manifest in %s: %s", post_dir, exc)
        return items

    def fetch_today(self) -> list[ContentItem]:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        all_items = self.fetch_all()
        return [
            item
            for item in all_items
            if _parse_date(item.get("date", ""))
            and _parse_date(item["date"]).strftime("%Y-%m-%d") == today
            and item.get("status") != "published"
        ]

def get_post_by_id(post_id_or_path: str) -> Optional[ContentItem]:
    """Retrieve a single post by folder ID or direct path."""
    p = Path(post_id_or_path)
    if p.is_dir():
        manifest = p / "post.json"
    elif p.is_file() and p.name == "post.json":
        manifest = p
    elif (REPO_ROOT / "posts" / post_id_or_path / "post.json").exists():
        manifest = REPO_ROOT / "posts" / post_id_or_path / "post.json"
    else:
        manifest = Path("posts") / post_id_or_path / "post.json"

    if manifest.exists():
        with open(manifest, "r", encoding="utf-8") as f:
            data = json.load(f)
        return _normalize_item(data)
    return None

# ─────────────────────────────────────────────
# 2. Google Sheets Source
# ─────────────────────────────────────────────

class GoogleSheetsSource:
    """Reads content rows from a Google Sheet via service account auth."""

    def __init__(self, credentials_dict: dict, sheet_id: str) -> None:
        self.credentials_dict = credentials_dict
        self.sheet_id = sheet_id

    def fetch_all(self) -> list[ContentItem]:
        try:
            import gspread
            from google.oauth2.service_account import Credentials

            scopes = [
                "https://www.googleapis.com/auth/spreadsheets.readonly",
                "https://www.googleapis.com/auth/drive.readonly",
            ]
            creds = Credentials.from_service_account_info(
                self.credentials_dict, scopes=scopes
            )
            client = gspread.authorize(creds)
            sheet = client.open_by_key(self.sheet_id)
            worksheet = sheet.sheet1
            records = worksheet.get_all_records()

            items = [_normalize_item(row) for row in records]
            logger.info("Fetched %d content items from Google Sheet '%s'.", len(items), sheet.title)
            return items
        except Exception as exc:
            logger.error("Google Sheets fetch failed: %s", exc)
            raise

    def fetch_today(self) -> list[ContentItem]:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        all_items = self.fetch_all()
        return [
            item
            for item in all_items
            if _parse_date(item.get("date", ""))
            and _parse_date(item["date"]).strftime("%Y-%m-%d") == today
        ]

# ─────────────────────────────────────────────
# 3. JSON Manifest Source
# ─────────────────────────────────────────────

class JsonManifestSource:
    """Reads content from a local JSON manifest file."""

    def __init__(self, path: str | Path = "content_manifest.json") -> None:
        self.path = Path(path)

    def fetch_all(self) -> list[ContentItem]:
        if not self.path.exists():
            return []
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
            items = [_normalize_item(entry) for entry in data]
            return items
        except Exception as exc:
            logger.error("JSON manifest read failed: %s", exc)
            raise

    def fetch_today(self) -> list[ContentItem]:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        all_items = self.fetch_all()
        return [
            item
            for item in all_items
            if _parse_date(item.get("date", ""))
            and _parse_date(item["date"]).strftime("%Y-%m-%d") == today
        ]

# ─────────────────────────────────────────────
# Smart Loader
# ─────────────────────────────────────────────

def get_todays_content(
    sheets_credentials: Optional[dict] = None,
    sheet_id: str = "",
    manifest_path: str = "content_manifest.json",
    posts_dir: str = "posts",
) -> list[ContentItem]:
    """
    Fetch today's content items.
    Priority Strategy:
      1. Dedicated post folders in posts/
      2. Google Sheets
      3. JSON manifest
    """
    # 1. Dedicated post folders
    try:
        p_source = PostsDirectorySource(posts_dir)
        items = p_source.fetch_today()
        if items:
            logger.info("Using %d item(s) from dedicated post folders.", len(items))
            return items
    except Exception as exc:
        logger.debug("Post folder check passed: %s", exc)

    # 2. Google Sheets
    if sheets_credentials and sheet_id:
        try:
            source = GoogleSheetsSource(sheets_credentials, sheet_id)
            items = source.fetch_today()
            if items:
                logger.info("Using %d item(s) from Google Sheets.", len(items))
                return items
        except Exception:
            logger.warning("Sheets check failed — falling back to JSON manifest.")

    # 3. Fallback: JSON manifest
    try:
        source = JsonManifestSource(manifest_path)
        items = source.fetch_today()
        if items:
            logger.info("Using %d item(s) from JSON manifest.", len(items))
            return items
    except Exception:
        pass

    logger.warning("No content items found for today.")
    return []
