"""
Zoho Social Publisher & Bulk Scheduler for LITELAB.

Supports two complementary workflows:
  1. Zoho Social REST API Direct & Scheduled Publishing:
     - Uses Zoho OAuth2 (Client ID, Client Secret, Refresh Token) with regional
       support (default: 'in' for LITELAB India — accounts.zoho.in / social.zoho.in).
     - Publishes immediately or schedules posts for a future date/time across
       all channels connected to the Zoho Social Brand (Instagram, LinkedIn,
       Facebook, X/Twitter, YouTube, Google Business Profile).
  2. Zoho Social Bulk Scheduler CSV Export (Automatic Fallback & Batch Mode):
     - Automatically generates a Zoho Social Bulk Scheduler-compliant CSV
       (`posts/<Post_ID>/zoho_social_schedule.csv` and `posts/zoho_social_master_queue.csv`)
       formatted to Zoho Social's exact specification:
       [Date (MM/DD/YYYY), Time (HH:MM AM/PM), Message, Link URL, Image Path/URL].
"""

from __future__ import annotations

import csv
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import requests

from .base import Publisher, PublishResult

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
LOCAL_ZOHO_CREDS_PATH = Path.home() / ".zoho-hr-mcp" / "credentials.json"


class ZohoSocialPublisher(Publisher):
    """Publish and schedule multi-channel posts via Zoho Social API + Bulk Schedule CSV."""

    def __init__(
        self,
        client_id: str = "",
        client_secret: str = "",
        refresh_token: str = "",
        brand_id: str = "",
        portal_id: str = "",
        region: str = "in",
        default_schedule_time: str = "06:30 PM",
        dry_run: bool = False,
    ) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.brand_id = brand_id
        self.portal_id = portal_id
        self.region = (region or "in").lower().strip(".")
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
    def social_api_base_url(self) -> str:
        return f"https://social.zoho.{self.region}/api/v1"

    def is_enabled(self) -> bool:
        has_api = bool(self.client_id and self.client_secret and self.refresh_token and self.brand_id)
        return has_api or self.dry_run

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

    def export_bulk_schedule_csv(self, content: dict[str, Any]) -> Path:
        """
        Exports a Zoho Social Bulk Scheduler-compliant CSV for the post and updates
        the master queue at `posts/zoho_social_master_queue.csv`.
        """
        post_id = content.get("id") or "Post_TEMPLATE"
        post_dir = REPO_ROOT / "posts" / post_id
        post_dir.mkdir(parents=True, exist_ok=True)

        raw_date = content.get("date") or datetime.now().strftime("%Y-%m-%d")
        try:
            dt = datetime.strptime(raw_date, "%Y-%m-%d")
            formatted_date = dt.strftime("%m/%d/%Y")
        except ValueError:
            formatted_date = datetime.now().strftime("%m/%d/%Y")

        sched_time = content.get("time") or self.default_schedule_time
        caption = content.get("caption", "")
        hashtags = content.get("hashtags", [])
        if hashtags:
            tag_str = " ".join(hashtags)
            if tag_str not in caption:
                caption = f"{caption}\n\n{tag_str}"

        link_url = content.get("url", "https://litelab.in")
        media_paths = content.get("media_paths", [])
        first_media = media_paths[0] if media_paths else content.get("pdf_path", "")

        row = {
            "Date": formatted_date,
            "Time": sched_time,
            "Message": caption,
            "Link URL": link_url,
            "Media Path": first_media,
            "Post ID": post_id,
        }

        post_csv = post_dir / "zoho_social_schedule.csv"
        fieldnames = ["Date", "Time", "Message", "Link URL", "Media Path", "Post ID"]
        with open(post_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerow(row)

        # Also update master queue CSV
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

    def publish(self, content: dict[str, Any]) -> PublishResult:
        """
        Publish or schedule a post via Zoho Social REST API, and always generate
        the Zoho Social Bulk Schedule CSV alongside it.
        """
        csv_path = self.export_bulk_schedule_csv(content)
        caption = content.get("caption", "")
        sched_date = content.get("date", "")
        sched_time = content.get("time") or self.default_schedule_time
        networks = content.get("zoho_networks") or content.get("platforms", ["instagram", "linkedin"])

        if self.dry_run or not (self.client_id and self.client_secret and self.refresh_token and self.brand_id):
            logger.info(
                "[Zoho Social] Scheduled CSV ready (%s) | Target networks=%s | Scheduled=%s %s",
                csv_path.name,
                networks,
                sched_date or "Immediate",
                sched_time,
            )
            return PublishResult(
                platform=self.platform_name,
                success=True,
                post_id=f"zoho_schedule_{content.get('id', 'post')}",
                post_url=f"https://social.zoho.{self.region}/",
                raw_response={"bulk_csv": str(csv_path), "scheduled_date": sched_date, "time": sched_time},
            )

        try:
            access_token = self._get_access_token()
            headers = {
                "Authorization": f"Zoho-oauthtoken {access_token}",
                "Content-Type": "application/json",
            }

            payload: dict[str, Any] = {
                "content": caption,
                "networks": networks,
            }

            if sched_date:
                payload["schedule_time"] = f"{sched_date} {sched_time}"
                payload["is_scheduled"] = True

            media_paths = content.get("media_paths", [])
            if content.get("video_url"):
                payload["media_url"] = content["video_url"]
            elif media_paths:
                payload["local_media"] = media_paths

            endpoint = f"{self.social_api_base_url}/{self.brand_id}/post"
            resp = requests.post(endpoint, headers=headers, json=payload, timeout=45)
            resp.raise_for_status()
            data = resp.json()
            post_id = str(data.get("post_id") or data.get("id") or "zoho_published")

            logger.info("Zoho Social post published/scheduled successfully: %s", post_id)
            return PublishResult(
                platform=self.platform_name,
                success=True,
                post_id=post_id,
                post_url=f"https://social.zoho.{self.region}/",
                raw_response=data,
            )

        except Exception as exc:
            logger.error("Zoho Social API publish failed (Bulk CSV still saved at %s): %s", csv_path, exc)
            return PublishResult(
                platform=self.platform_name,
                success=False,
                error=f"{exc} (Fallback CSV saved at {csv_path.name})",
            )
