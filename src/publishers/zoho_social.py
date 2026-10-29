"""
Zoho Social Publisher & Direct Scheduler for LITELAB (`src/publishers/zoho_social.py`).

Supports all three official Zoho Social scheduling pathways directly from `litelab-smm`:

1. Pathway A — Zoho Social REST API v2 (`https://social.zoho.in/social/v2`):
   - Required Scopes:
     `ZohoSocial.Publish.ALL,ZohoSocial.Media.ALL,ZohoSocial.Organization.READ,ZohoSocial.Integration.READ`
   - Auto-discovers `portal_id` (`GET /social/v2/socialportals`), `brand_id` (`GET /social/v2/socialbrands`),
     and connected `channels` (`GET /social/v2/channels`).
   - Uploads local composited slides via `POST /social/v2/medias/upload` to obtain `file_path`
     identifiers, then schedules the post via `POST /social/v2/posts/schedules` (or publishes
     immediately via `POST /social/v2/posts/publish` / saves draft via `POST /social/v2/posts/drafts`).

2. Pathway B — Zoho Flow Webhook -> Zoho Social "Schedule Post" Action (`ZOHO_FLOW_WEBHOOK_URL`):
   - Zero-wait integration using Zoho Flow (`flow.zoho.in`) Webhook Trigger routed to
     Zoho Social's native "Schedule post" or "Publish post" action.
   - Automatically maps local composited PNGs/PDFs to public GitHub raw HTTPS URLs
     (`https://raw.githubusercontent.com/litelabcommon-glitch/litelab-smm/main/...`)
     and dispatches the structured JSON payload (`caption`, `schedule_time_iso`,
     `schedule_time_epoch`, `media_urls`, `pdf_url`, `networks`).

3. Pathway C — Zoho Social Bulk Scheduler CSV (`zoho_social_schedule.csv`):
   - Always exports `posts/<Post_ID>/zoho_social_schedule.csv` and updates
     `posts/zoho_social_master_queue.csv` with public Image URLs for 1-click Bulk Scheduling.
"""

from __future__ import annotations

import csv
import json
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Optional

import requests

from .base import Publisher, PublishResult

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
LOCAL_ZOHO_CREDS_PATH = Path.home() / ".zoho-hr-mcp" / "credentials.json"
GITHUB_RAW_BASE = "https://raw.githubusercontent.com/litelabcommon-glitch/litelab-smm/main"
IST_TZ = timezone(timedelta(hours=5, minutes=30))


class ZohoSocialPublisher(Publisher):
    """Publish and schedule multi-channel posts via Zoho Social API v2, Zoho Flow Webhook, and Bulk CSV."""

    def __init__(
        self,
        client_id: str = "",
        client_secret: str = "",
        refresh_token: str = "",
        brand_id: str = "",
        portal_id: str = "",
        region: str = "in",
        zoho_flow_webhook_url: str = "",
        action_mode: str = "schedule",  # "schedule", "publish", or "draft"
        default_schedule_time: str = "06:30 PM",
        dry_run: bool = False,
    ) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.brand_id = brand_id
        self.portal_id = portal_id
        self.region = (region or "in").lower().strip(".")
        self.zoho_flow_webhook_url = zoho_flow_webhook_url
        self.action_mode = action_mode.lower()
        self.default_schedule_time = default_schedule_time
        self.dry_run = dry_run
        self._access_token: str = ""

        # Auto-discover shared LITELAB Zoho OAuth Client ID/Secret if stored locally
        if not (self.client_id and self.client_secret) and LOCAL_ZOHO_CREDS_PATH.exists():
            try:
                with open(LOCAL_ZOHO_CREDS_PATH, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                self.client_id = self.client_id or saved.get("clientId", "")
                self.client_secret = self.client_secret or saved.get("clientSecret", "")
                self.region = self.region or saved.get("region", "in")
            except Exception:
                pass

    @property
    def platform_name(self) -> str:
        return "ZohoSocial"

    @property
    def accounts_base_url(self) -> str:
        return f"https://accounts.zoho.{self.region}"

    @property
    def social_v2_base_url(self) -> str:
        return f"https://social.zoho.{self.region}/social/v2"

    def is_enabled(self) -> bool:
        has_api = bool(self.client_id and self.client_secret and self.refresh_token)
        has_webhook = bool(self.zoho_flow_webhook_url)
        return has_api or has_webhook or self.dry_run

    # ─────────────────────────────────────────────────────────────────
    # OAuth 2.0 & Auto-Discovery Helpers (Zoho Social REST API v2)
    # ─────────────────────────────────────────────────────────────────

    def _get_access_token(self) -> str:
        """Exchange Zoho OAuth2 refresh_token for a fresh access_token."""
        if self._access_token:
            return self._access_token

        token_url = f"{self.accounts_base_url}/oauth/v2/token"
        resp = requests.post(
            token_url,
            params={
                "refresh_token": self.refresh_token,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "refresh_token",
            },
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
        if "access_token" not in data:
            raise RuntimeError(f"Zoho OAuth token refresh failed: {data}")
        self._access_token = data["access_token"]
        return self._access_token

    def discover_portal_and_brand(self) -> tuple[str, str]:
        """
        Auto-discovers `portal_id` (`GET /social/v2/socialportals`) and
        `brand_id` (`GET /social/v2/socialbrands`) if not explicitly set in .env.
        """
        token = self._get_access_token()
        headers = {"Authorization": f"Zoho-oauthtoken {token}"}

        if not self.portal_id:
            resp = requests.get(
                f"{self.social_v2_base_url}/socialportals",
                headers=headers,
                params={"fields": "id,portal_name,plan"},
                timeout=20,
            )
            resp.raise_for_status()
            portals = resp.json().get("data") or resp.json().get("socialportals") or []
            if portals:
                self.portal_id = str(portals[0].get("id"))
                logger.info("Auto-discovered Zoho Social Portal ID: %s (%s)", self.portal_id, portals[0].get("portal_name"))

        if self.portal_id and not self.brand_id:
            headers["portal_id"] = str(self.portal_id)
            resp = requests.get(
                f"{self.social_v2_base_url}/socialbrands",
                headers=headers,
                timeout=20,
            )
            resp.raise_for_status()
            brands = resp.json().get("data") or resp.json().get("socialbrands") or []
            if brands:
                self.brand_id = str(brands[0].get("id"))
                logger.info("Auto-discovered Zoho Social Brand ID: %s (%s)", self.brand_id, brands[0].get("brand_name"))

        return self.portal_id, self.brand_id

    def discover_channels(self) -> list[dict[str, str]]:
        """
        Fetches active connected social channels for the brand via `GET /social/v2/channels`.
        Returns list of `{"network": ..., "channel_id": ...}` objects.
        """
        portal_id, brand_id = self.discover_portal_and_brand()
        token = self._get_access_token()
        headers = {
            "Authorization": f"Zoho-oauthtoken {token}",
            "portal_id": str(portal_id),
            "brand_id": str(brand_id),
        }
        resp = requests.get(f"{self.social_v2_base_url}/channels", headers=headers, timeout=20)
        resp.raise_for_status()
        raw_channels = resp.json().get("data") or resp.json().get("channels") or []
        channels = []
        for ch in raw_channels:
            if ch.get("status") in (None, "token_active", "active", True):
                channels.append({
                    "network": ch.get("network") or ch.get("channel_type", ""),
                    "channel_id": str(ch.get("channel_id") or ch.get("id", "")),
                })
        return channels

    def upload_media_v2(self, local_path: Path) -> Optional[str]:
        """
        Uploads a local image/media file to Zoho Social (`POST /social/v2/medias/upload`)
        and returns the internal `file_path` string required for scheduled post payloads.
        """
        if not local_path.exists():
            return None
        portal_id, brand_id = self.discover_portal_and_brand()
        token = self._get_access_token()
        headers = {
            "Authorization": f"Zoho-oauthtoken {token}",
            "portal_id": str(portal_id),
            "brand_id": str(brand_id),
        }
        with open(local_path, "rb") as f:
            files = {"file": (local_path.name, f, "image/png" if local_path.suffix.lower() == ".png" else "image/jpeg")}
            resp = requests.post(f"{self.social_v2_base_url}/medias/upload", headers=headers, files=files, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            file_path = (
                data.get("file_path")
                or (data.get("data", {}) if isinstance(data.get("data"), dict) else {}).get("file_path")
            )
            return file_path

    # ─────────────────────────────────────────────────────────────────
    # Timestamp & Public URL Helpers
    # ─────────────────────────────────────────────────────────────────

    def _compute_schedule_timestamps(self, date_str: str, time_str: str) -> tuple[int, str, str]:
        """
        Parses `YYYY-MM-DD` and `HH:MM AM/PM` into:
          - Unix epoch seconds (int) for Zoho Social API v2 `schedule_time`
          - ISO 8601 string (`YYYY-MM-DDTHH:MM:SS+05:30`) for Zoho Flow
          - Zoho Bulk CSV date (`MM/DD/YYYY`)
        """
        raw_date = (date_str or "").strip() or (datetime.now(IST_TZ) + timedelta(days=1)).strftime("%Y-%m-%d")
        raw_time = (time_str or "").strip() or self.default_schedule_time

        dt = None
        for fmt in ("%Y-%m-%d %I:%M %p", "%Y-%m-%d %H:%M", "%d-%m-%Y %I:%M %p"):
            try:
                dt = datetime.strptime(f"{raw_date} {raw_time}", fmt).replace(tzinfo=IST_TZ)
                break
            except ValueError:
                continue

        if dt is None:
            dt = (datetime.now(IST_TZ) + timedelta(days=1)).replace(hour=18, minute=30, second=0, microsecond=0)

        epoch_sec = int(dt.timestamp())
        iso_str = dt.isoformat()
        csv_date = dt.strftime("%m/%d/%Y")
        return epoch_sec, iso_str, csv_date

    def _to_public_github_url(self, rel_path: str) -> str:
        """Converts a repo-relative media path into a public GitHub raw HTTPS URL."""
        clean = str(rel_path).replace("\\", "/").lstrip("/")
        if clean.startswith("http://") or clean.startswith("https://"):
            return clean
        return f"{GITHUB_RAW_BASE}/{clean}"

    # ─────────────────────────────────────────────────────────────────
    # Pathway C: Zoho Social Bulk Scheduler CSV Export
    # ─────────────────────────────────────────────────────────────────

    def export_bulk_schedule_csv(self, content: dict[str, Any]) -> Path:
        """
        Exports a Zoho Social Bulk Scheduler-compliant CSV for the post and updates
        the master queue at `posts/zoho_social_master_queue.csv`.
        """
        post_id = content.get("id") or "Post_TEMPLATE"
        post_dir = REPO_ROOT / "posts" / post_id
        post_dir.mkdir(parents=True, exist_ok=True)

        sched_time = content.get("time") or self.default_schedule_time
        _, _, formatted_date = self._compute_schedule_timestamps(content.get("date", ""), sched_time)

        caption = content.get("caption", "")
        hashtags = content.get("hashtags", [])
        if hashtags:
            tag_str = " ".join(hashtags)
            if tag_str not in caption:
                caption = f"{caption}\n\n{tag_str}"

        link_url = content.get("url", "https://litelab.in")
        media_paths = content.get("media_paths", [])
        first_media = media_paths[0] if media_paths else content.get("pdf_path", "")
        public_image_url = self._to_public_github_url(first_media) if first_media else ""

        row = {
            "Date": formatted_date,
            "Time": sched_time,
            "Message": caption,
            "Link URL": link_url,
            "Image URL": public_image_url,
            "Local Media Path": first_media,
            "Post ID": post_id,
        }

        post_csv = post_dir / "zoho_social_schedule.csv"
        fieldnames = ["Date", "Time", "Message", "Link URL", "Image URL", "Local Media Path", "Post ID"]
        with open(post_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerow(row)

        master_csv = REPO_ROOT / "posts" / "zoho_social_master_queue.csv"
        existing_rows = []
        if master_csv.exists():
            try:
                with open(master_csv, "r", newline="", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    existing_rows = [r for r in reader if r.get("Post ID") != post_id]
            except Exception:
                existing_rows = []

        existing_rows.append(row)
        with open(master_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(existing_rows)

        logger.info("Zoho Social Bulk Schedule CSV exported: %s", post_csv.relative_to(REPO_ROOT))
        return post_csv

    # ─────────────────────────────────────────────────────────────────
    # Main Publish / Schedule Execution (Pathways A, B & C)
    # ─────────────────────────────────────────────────────────────────

    def publish(self, content: dict[str, Any]) -> PublishResult:
        """
        Executes scheduling/publishing in priority order:
          1. Always exports Zoho Social Bulk Schedule CSV (`zoho_social_schedule.csv`)
          2. If `ZOHO_FLOW_WEBHOOK_URL` is configured, triggers Zoho Flow -> Zoho Social Schedule Post
          3. If Zoho Social REST API v2 credentials (`ZOHO_REFRESH_TOKEN`) are configured,
             uploads media and calls `POST /social/v2/posts/schedules` (or `/publish` / `/drafts`)
        """
        csv_path = self.export_bulk_schedule_csv(content)
        caption = content.get("caption", "")
        sched_date = content.get("date", "")
        sched_time = content.get("time") or self.default_schedule_time
        epoch_sec, iso_str, _ = self._compute_schedule_timestamps(sched_date, sched_time)

        media_paths = content.get("media_paths", [])
        public_media_urls = [self._to_public_github_url(p) for p in media_paths]
        pdf_url = self._to_public_github_url(content["pdf_path"]) if content.get("pdf_path") else ""
        networks = content.get("zoho_networks") or content.get("platforms", ["instagram", "linkedin"])

        if self.dry_run:
            logger.info(
                "[Zoho Social DRY-RUN] CSV ready (%s) | ISO=%s (epoch=%d) | Media=%d files",
                csv_path.name,
                iso_str,
                epoch_sec,
                len(media_paths),
            )
            return PublishResult(
                platform=self.platform_name,
                success=True,
                post_id=f"zoho_schedule_{content.get('id', 'post')}",
                post_url=f"https://social.zoho.{self.region}/",
                raw_response={
                    "bulk_csv": str(csv_path),
                    "schedule_time_iso": iso_str,
                    "schedule_time_epoch": epoch_sec,
                    "public_media_urls": public_media_urls,
                },
            )

        # Pathway B: Zoho Flow Incoming Webhook -> Zoho Social "Schedule Post" Action
        if self.zoho_flow_webhook_url:
            try:
                webhook_payload = {
                    "post_id": content.get("id", ""),
                    "title": content.get("title", ""),
                    "caption": caption,
                    "schedule_time_iso": iso_str,
                    "schedule_time_epoch": epoch_sec,
                    "networks": networks,
                    "cover_image_url": public_media_urls[0] if public_media_urls else "",
                    "media_urls": public_media_urls,
                    "pdf_url": pdf_url,
                    "brand_website": "https://litelab.in",
                }
                resp = requests.post(self.zoho_flow_webhook_url, json=webhook_payload, timeout=30)
                resp.raise_for_status()
                logger.info("Dispatched scheduled post to Zoho Flow Webhook successfully (%s).", iso_str)
                return PublishResult(
                    platform=f"{self.platform_name} (Zoho Flow)",
                    success=True,
                    post_id=f"zohoflow_{content.get('id', 'post')}",
                    post_url=f"https://social.zoho.{self.region}/",
                    raw_response={"status": resp.status_code, "schedule_time_iso": iso_str},
                )
            except Exception as exc:
                logger.error("Zoho Flow webhook dispatch failed: %s", exc)

        # Pathway A: Direct Zoho Social REST API v2 (`/social/v2/posts/schedules`)
        if self.client_id and self.client_secret and self.refresh_token:
            try:
                portal_id, brand_id = self.discover_portal_and_brand()
                token = self._get_access_token()
                headers = {
                    "Authorization": f"Zoho-oauthtoken {token}",
                    "portal_id": str(portal_id),
                    "brand_id": str(brand_id),
                    "Content-Type": "application/json",
                }

                # Discover connected channels
                channels = content.get("zoho_channels") or self.discover_channels()

                # Upload media files via /social/v2/medias/upload
                uploaded_media = []
                for rel_p in media_paths:
                    abs_p = Path(rel_p) if Path(rel_p).is_absolute() else (REPO_ROOT / rel_p)
                    file_path_token = self.upload_media_v2(abs_p)
                    if file_path_token:
                        uploaded_media.append({"file_path": file_path_token})

                message_obj: dict[str, Any] = {
                    "content": caption,
                    "channels": channels,
                }
                if uploaded_media:
                    message_obj["media"] = uploaded_media

                payload: dict[str, Any] = {"messages": [message_obj]}
                if self.action_mode == "schedule":
                    payload["schedule_time"] = epoch_sec
                    endpoint = f"{self.social_v2_base_url}/posts/schedules"
                elif self.action_mode == "draft":
                    endpoint = f"{self.social_v2_base_url}/posts/drafts"
                else:
                    endpoint = f"{self.social_v2_base_url}/posts/publish"

                resp = requests.post(endpoint, headers=headers, json=payload, timeout=45)
                resp.raise_for_status()
                data = resp.json()
                post_id = str(data.get("id") or data.get("post_id") or "zoho_v2_scheduled")

                logger.info("Zoho Social API v2 scheduled post created: %s", post_id)
                return PublishResult(
                    platform=self.platform_name,
                    success=True,
                    post_id=post_id,
                    post_url=f"https://social.zoho.{self.region}/",
                    raw_response=data,
                )
            except Exception as exc:
                logger.error("Zoho Social REST API v2 call failed (Bulk CSV saved at %s): %s", csv_path.name, exc)
                return PublishResult(
                    platform=self.platform_name,
                    success=False,
                    error=f"{exc} (Fallback Bulk CSV ready at {csv_path.name})",
                )

        # Fallback: CSV-only mode when live API token / webhook is not yet set in .env
        logger.info("Zoho Social Bulk Schedule CSV ready at %s (Add ZOHO_REFRESH_TOKEN or ZOHO_FLOW_WEBHOOK_URL for live push).", csv_path)
        return PublishResult(
            platform=f"{self.platform_name} (CSV Queue)",
            success=True,
            post_id=f"csv_{content.get('id', 'post')}",
            post_url=f"https://social.zoho.{self.region}/",
            raw_response={"bulk_csv": str(csv_path)},
        )
