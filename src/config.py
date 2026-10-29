"""
Centralized configuration loader for LITELAB SMM Suite.

All secrets and config values are pulled from environment variables
or .env. Supports Zoho Social, Higgsfield AI, LinkedIn, Instagram,
YouTube, WhatsApp Catalog, X/Twitter, and Reddit.
"""

from __future__ import annotations

import base64
import json
import logging
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Config:
    """Immutable configuration loaded from environment variables."""

    # ── LITELAB Brand Identity ──
    brand_name: str = "LITELAB"
    brand_handle: str = "@litelab.in"
    brand_website: str = "https://litelab.in"

    # ── Zoho Social (Primary Scheduler & Multi-Channel Publisher) ──
    zoho_client_id: str = ""
    zoho_client_secret: str = ""
    zoho_refresh_token: str = ""
    zoho_social_brand_id: str = ""
    zoho_social_portal_id: str = ""
    zoho_region: str = "in"
    zoho_default_schedule_time: str = "06:30 PM"
    zoho_social_always_export_csv: bool = True

    # ── Higgsfield AI & Generative Providers ──
    default_ai_provider: str = "higgsfield"
    higgsfield_image_model: str = "gpt_image_2_5"
    higgsfield_video_model: str = "seedance_2_5"
    gemini_api_key: str = ""

    # ── Google Sheets ──
    google_sheet_id: str = ""
    google_sheets_credentials_b64: str = ""

    # ── LinkedIn ──
    linkedin_access_token: str = ""
    linkedin_person_urn: str = ""
    linkedin_organization_urn: str = ""
    linkedin_mode: str = "direct"
    buffer_profile_linkedin: str = ""

    # ── Buffer Universal ──
    buffer_access_token: str = ""

    # ── YouTube ──
    youtube_client_secret_b64: str = ""
    youtube_refresh_token: str = ""

    # ── Instagram ──
    instagram_access_token: str = ""
    instagram_account_id: str = ""
    instagram_mode: str = "graph"
    buffer_profile_id: str = ""

    # ── Reddit ──
    reddit_client_id: str = ""
    reddit_client_secret: str = ""
    reddit_username: str = ""
    reddit_password: str = ""
    reddit_default_subreddit: str = "u_Litelab"

    # ── Twitter / X ──
    twitter_api_key: str = ""
    twitter_api_secret: str = ""
    twitter_access_token: str = ""
    twitter_access_token_secret: str = ""
    twitter_bearer_token: str = ""

    # ── WhatsApp Catalog ──
    whatsapp_access_token: str = ""
    whatsapp_catalog_id: str = ""
    whatsapp_currency: str = "INR"

    # ── Notifications ──
    discord_webhook_url: str = ""
    slack_webhook_url: str = ""

    # ── Runtime ──
    dry_run: bool = False
    log_level: str = "INFO"

    # ── Derived ──
    _google_sheets_credentials: Optional[dict] = field(default=None, repr=False, compare=False)
    _youtube_client_config: Optional[dict] = field(default=None, repr=False, compare=False)

    def __post_init__(self) -> None:
        if self.google_sheets_credentials_b64:
            try:
                decoded = base64.b64decode(self.google_sheets_credentials_b64)
                object.__setattr__(self, "_google_sheets_credentials", json.loads(decoded))
            except Exception as exc:
                logger.warning("Failed to decode Google Sheets credentials: %s", exc)

        if self.youtube_client_secret_b64:
            try:
                decoded = base64.b64decode(self.youtube_client_secret_b64)
                object.__setattr__(self, "_youtube_client_config", json.loads(decoded))
            except Exception as exc:
                logger.warning("Failed to decode YouTube client secret: %s", exc)

    @property
    def google_sheets_credentials(self) -> Optional[dict]:
        return self._google_sheets_credentials

    @property
    def youtube_client_config(self) -> Optional[dict]:
        return self._youtube_client_config

    # ── Platform availability checks ──
    @property
    def zoho_social_enabled(self) -> bool:
        has_api = bool(self.zoho_client_id and self.zoho_client_secret and self.zoho_refresh_token and self.zoho_social_brand_id)
        return has_api or self.zoho_social_always_export_csv or self.dry_run

    @property
    def linkedin_enabled(self) -> bool:
        has_direct = bool(self.linkedin_access_token and (self.linkedin_person_urn or self.linkedin_organization_urn))
        has_buffer = bool((self.buffer_access_token or self.instagram_access_token) and self.buffer_profile_linkedin)
        return has_direct or has_buffer or self.dry_run

    @property
    def youtube_enabled(self) -> bool:
        return bool(self.youtube_client_secret_b64 and self.youtube_refresh_token) or self.dry_run

    @property
    def instagram_enabled(self) -> bool:
        return bool(self.instagram_access_token and self.instagram_account_id) or self.dry_run

    @property
    def reddit_enabled(self) -> bool:
        return bool(self.reddit_client_id and self.reddit_client_secret) or self.dry_run

    @property
    def twitter_enabled(self) -> bool:
        return bool((self.twitter_api_key and self.twitter_access_token) or self.twitter_bearer_token) or self.dry_run

    @property
    def whatsapp_catalog_enabled(self) -> bool:
        return bool(self.whatsapp_access_token and self.whatsapp_catalog_id) or self.dry_run

    @property
    def sheets_enabled(self) -> bool:
        return bool(self.google_sheets_credentials_b64 and self.google_sheet_id)

    @property
    def notifications_enabled(self) -> bool:
        return bool(self.discord_webhook_url or self.slack_webhook_url)


def load_dotenv() -> None:
    """Load variables from local .env into os.environ if not already present."""
    env_file = REPO_ROOT / ".env"
    if env_file.exists():
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def load_config(dry_run_override: bool = False) -> Config:
    """Build a Config from current environment variables."""
    load_dotenv()
    is_dry = dry_run_override or (os.getenv("DRY_RUN", "false").lower() == "true")

    cfg = Config(
        brand_name=os.getenv("BRAND_NAME", "LITELAB"),
        brand_handle=os.getenv("BRAND_HANDLE", "@litelab.in"),
        brand_website=os.getenv("BRAND_WEBSITE", "https://litelab.in"),
        zoho_client_id=os.getenv("ZOHO_CLIENT_ID", ""),
        zoho_client_secret=os.getenv("ZOHO_CLIENT_SECRET", ""),
        zoho_refresh_token=os.getenv("ZOHO_REFRESH_TOKEN", ""),
        zoho_social_brand_id=os.getenv("ZOHO_SOCIAL_BRAND_ID", ""),
        zoho_social_portal_id=os.getenv("ZOHO_SOCIAL_PORTAL_ID", ""),
        zoho_region=os.getenv("ZOHO_REGION", "in"),
        zoho_default_schedule_time=os.getenv("ZOHO_DEFAULT_SCHEDULE_TIME", "06:30 PM"),
        zoho_social_always_export_csv=os.getenv("ZOHO_SOCIAL_ALWAYS_EXPORT_CSV", "true").lower() == "true",
        default_ai_provider=os.getenv("DEFAULT_AI_PROVIDER", "higgsfield"),
        higgsfield_image_model=os.getenv("HIGGSFIELD_IMAGE_MODEL", "gpt_image_2_5"),
        higgsfield_video_model=os.getenv("HIGGSFIELD_VIDEO_MODEL", "seedance_2_5"),
        google_sheet_id=os.getenv("GOOGLE_SHEET_ID", ""),
        google_sheets_credentials_b64=os.getenv("GOOGLE_SHEETS_CREDENTIALS", ""),
        gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
        linkedin_access_token=os.getenv("LINKEDIN_ACCESS_TOKEN", ""),
        linkedin_person_urn=os.getenv("LINKEDIN_PERSON_URN", ""),
        linkedin_organization_urn=os.getenv("LINKEDIN_ORGANIZATION_URN", ""),
        linkedin_mode=os.getenv("LINKEDIN_MODE", "direct").lower(),
        buffer_profile_linkedin=os.getenv("BUFFER_PROFILE_LINKEDIN", ""),
        buffer_access_token=os.getenv("BUFFER_ACCESS_TOKEN", ""),
        youtube_client_secret_b64=os.getenv("YOUTUBE_CLIENT_SECRET", ""),
        youtube_refresh_token=os.getenv("YOUTUBE_REFRESH_TOKEN", ""),
        instagram_access_token=os.getenv("INSTAGRAM_ACCESS_TOKEN", ""),
        instagram_account_id=os.getenv("INSTAGRAM_ACCOUNT_ID", ""),
        instagram_mode=os.getenv("INSTAGRAM_MODE", "graph").lower(),
        buffer_profile_id=os.getenv("BUFFER_PROFILE_ID", ""),
        reddit_client_id=os.getenv("REDDIT_CLIENT_ID", ""),
        reddit_client_secret=os.getenv("REDDIT_CLIENT_SECRET", ""),
        reddit_username=os.getenv("REDDIT_USERNAME", ""),
        reddit_password=os.getenv("REDDIT_PASSWORD", ""),
        reddit_default_subreddit=os.getenv("REDDIT_DEFAULT_SUBREDDIT", "u_Litelab"),
        twitter_api_key=os.getenv("TWITTER_API_KEY", ""),
        twitter_api_secret=os.getenv("TWITTER_API_SECRET", ""),
        twitter_access_token=os.getenv("TWITTER_ACCESS_TOKEN", ""),
        twitter_access_token_secret=os.getenv("TWITTER_ACCESS_TOKEN_SECRET", ""),
        twitter_bearer_token=os.getenv("TWITTER_BEARER_TOKEN", ""),
        whatsapp_access_token=os.getenv("WHATSAPP_ACCESS_TOKEN", ""),
        whatsapp_catalog_id=os.getenv("WHATSAPP_CATALOG_ID", ""),
        whatsapp_currency=os.getenv("WHATSAPP_CURRENCY", "INR"),
        discord_webhook_url=os.getenv("DISCORD_WEBHOOK_URL", ""),
        slack_webhook_url=os.getenv("SLACK_WEBHOOK_URL", ""),
        dry_run=is_dry,
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
    )

    enabled = []
    if cfg.zoho_social_enabled:
        enabled.append("ZohoSocial")
    if cfg.linkedin_enabled:
        enabled.append("LinkedIn")
    if cfg.youtube_enabled:
        enabled.append("YouTube")
    if cfg.instagram_enabled:
        enabled.append("Instagram")
    if cfg.reddit_enabled:
        enabled.append("Reddit")
    if cfg.twitter_enabled:
        enabled.append("Twitter")
    if cfg.whatsapp_catalog_enabled:
        enabled.append("WhatsAppCatalog")

    if not enabled:
        logger.error("No publishing platforms configured. Check your .env or secrets.")
        sys.exit(1)

    logger.info("LITELAB SMM Platforms enabled: %s", ", ".join(enabled))
    return cfg
