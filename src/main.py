#!/usr/bin/env python3
"""
LITELAB Social Media Automation Engine — Main Orchestrator.

Coordinates: config → data source → AI enhancement → Zoho Social & Direct Publishers → notifications.
Supports both scheduled CRON execution and on-demand post folder publishing/scheduling.
"""

from __future__ import annotations

import argparse
import logging
import sys
import os
from typing import Any

from src.config import Config, load_config
from src.data_source import get_todays_content, get_post_by_id
from src.ai_enhancer import enhance_caption
from src.notifier import Level, send_alert, send_summary
from src.publishers.base import PublishResult
from src.publishers.zoho_social import ZohoSocialPublisher
from src.publishers.buffer_cli import BufferCliPublisher
from src.publishers.linkedin import LinkedInPublisher
from src.publishers.youtube import YouTubePublisher
from src.publishers.instagram import InstagramPublisher
from src.publishers.reddit import RedditPublisher
from src.publishers.twitter import TwitterPublisher
from src.publishers.whatsapp_catalog import WhatsAppCatalogPublisher


def setup_logging(level: str = "INFO") -> None:
    """Configure structured UTF-8 logging."""
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        format="%(asctime)s | %(levelname)-7s | %(name)-20s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def build_publishers(cfg: Config) -> list[Any]:
    """Instantiate all enabled LITELAB publishers."""
    publishers = []

    if cfg.zoho_social_enabled:
        publishers.append(
            ZohoSocialPublisher(
                client_id=cfg.zoho_client_id,
                client_secret=cfg.zoho_client_secret,
                refresh_token=cfg.zoho_refresh_token,
                brand_id=cfg.zoho_social_brand_id,
                portal_id=cfg.zoho_social_portal_id,
                region=cfg.zoho_region,
                default_schedule_time=cfg.zoho_default_schedule_time,
                dry_run=cfg.dry_run,
            )
        )

    if cfg.linkedin_enabled:
        if cfg.linkedin_mode == "buffer" or cfg.buffer_profile_linkedin:
            publishers.append(
                BufferCliPublisher(
                    channel_id=cfg.buffer_profile_linkedin,
                    service="linkedin",
                    dry_run=cfg.dry_run,
                )
            )
        else:
            publishers.append(
                LinkedInPublisher(
                    access_token=cfg.linkedin_access_token,
                    person_urn=cfg.linkedin_person_urn,
                    organization_urn=cfg.linkedin_organization_urn,
                    dry_run=cfg.dry_run,
                )
            )

    if cfg.youtube_enabled:
        publishers.append(
            YouTubePublisher(
                client_config=cfg.youtube_client_config,
                refresh_token=cfg.youtube_refresh_token,
            )
        )

    if cfg.instagram_enabled:
        if cfg.instagram_mode == "buffer" and cfg.buffer_profile_id:
            publishers.append(
                BufferCliPublisher(
                    channel_id=cfg.buffer_profile_id,
                    service="instagram",
                    dry_run=cfg.dry_run,
                )
            )
        else:
            publishers.append(
                InstagramPublisher(
                    access_token=cfg.instagram_access_token,
                    account_id=cfg.instagram_account_id,
                    mode=cfg.instagram_mode,
                    buffer_profile_id=cfg.buffer_profile_id,
                )
            )

    if cfg.reddit_enabled:
        publishers.append(
            RedditPublisher(
                client_id=cfg.reddit_client_id,
                client_secret=cfg.reddit_client_secret,
                username=cfg.reddit_username,
                password=cfg.reddit_password,
                default_subreddit=cfg.reddit_default_subreddit,
                dry_run=cfg.dry_run,
            )
        )

    if cfg.twitter_enabled:
        twitter_buffer_id = os.getenv("BUFFER_CHANNEL_TWITTER", "")
        if twitter_buffer_id:
            publishers.append(
                BufferCliPublisher(
                    channel_id=twitter_buffer_id,
                    service="twitter",
                    dry_run=cfg.dry_run,
                )
            )
        else:
            publishers.append(
                TwitterPublisher(
                    api_key=cfg.twitter_api_key,
                    api_secret=cfg.twitter_api_secret,
                    access_token=cfg.twitter_access_token,
                    access_token_secret=cfg.twitter_access_token_secret,
                    bearer_token=cfg.twitter_bearer_token,
                    dry_run=cfg.dry_run,
                )
            )

    if cfg.whatsapp_catalog_enabled:
        publishers.append(
            WhatsAppCatalogPublisher(
                access_token=cfg.whatsapp_access_token,
                catalog_id=cfg.whatsapp_catalog_id,
                currency=cfg.whatsapp_currency,
                dry_run=cfg.dry_run,
            )
        )

    return publishers


def process_content_item(
    item: dict[str, Any],
    publishers: list[Any],
    cfg: Config,
    platform_filter: str | None = None,
) -> dict[str, bool]:
    """Process a single LITELAB content item through the publishing & Zoho Social scheduling pipeline."""
    logger = logging.getLogger("orchestrator")
    results: dict[str, bool] = {}
    target_platforms = [p.lower() for p in item.get("platforms", [])]

    for publisher in publishers:
        platform_key = publisher.platform_name.lower()

        if platform_filter and platform_filter.lower() != platform_key:
            continue

        # Always allow ZohoSocial if configured or targeted
        if target_platforms and platform_key not in target_platforms and platform_key != "zohosocial":
            logger.info("Skipping %s — not in target platforms.", publisher.platform_name)
            continue

        enhanced_caption = item.get("caption", "")
        if cfg.gemini_api_key:
            try:
                enhanced_caption = enhance_caption(
                    caption=item.get("caption", ""),
                    platform=platform_key,
                    hashtags=item.get("hashtags", []),
                    api_key=cfg.gemini_api_key,
                )
            except Exception as exc:
                logger.warning("AI enhancement failed for %s — using original: %s", publisher.platform_name, exc)

        enhanced_item = {**item, "caption": enhanced_caption}

        if cfg.dry_run and platform_key != "zohosocial":
            logger.info("[DRY RUN] Would publish to %s: %s", publisher.platform_name, enhanced_caption[:80])
            results[publisher.platform_name] = True
            continue

        try:
            result: PublishResult = publisher.publish(enhanced_item)
            results[publisher.platform_name] = result.success
            logger.info(str(result))

            if not result.success:
                send_alert(
                    message=f"Failed to publish to **{publisher.platform_name}**.\nError: {result.error}",
                    level=Level.ERROR,
                    discord_url=cfg.discord_webhook_url,
                    slack_url=cfg.slack_webhook_url,
                    platform=publisher.platform_name,
                )
        except Exception as exc:
            results[publisher.platform_name] = False
            logger.error("%s publish error: %s", publisher.platform_name, exc)
            send_alert(
                message=f"**{publisher.platform_name}** publish crashed.\nError: `{exc}`",
                level=Level.ERROR,
                discord_url=cfg.discord_webhook_url,
                slack_url=cfg.slack_webhook_url,
                platform=publisher.platform_name,
                error=exc,
            )

    return results


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="LITELAB SMM & Zoho Social Orchestrator")
    parser.add_argument("--post", help="Specific post ID or folder to publish/schedule (e.g. Post_TEMPLATE)")
    parser.add_argument("--platform", help="Filter target platform (e.g. zohosocial, linkedin, instagram)")
    parser.add_argument("--dry-run", action="store_true", help="Force dry run mode")
    args = parser.parse_args()

    cfg = load_config(dry_run_override=args.dry_run)
    setup_logging(cfg.log_level)
    logger = logging.getLogger("orchestrator")

    logger.info("=" * 60)
    logger.info("  LITELAB — Social Media & Zoho Social Autopilot")
    logger.info("  Dry Run: %s", cfg.dry_run)
    logger.info("=" * 60)

    content_items: list[dict[str, Any]] = []
    if args.post:
        logger.info("Targeting single post: %s", args.post)
        item = get_post_by_id(args.post)
        if item:
            content_items = [item]
        else:
            logger.error("Could not find post manifest for: %s", args.post)
            sys.exit(1)
    else:
        try:
            content_items = get_todays_content(
                sheets_credentials=cfg.google_sheets_credentials,
                sheet_id=cfg.google_sheet_id,
            )
        except Exception as exc:
            logger.error("Content fetch failed: %s", exc)
            sys.exit(1)

    if not content_items:
        logger.info("No content scheduled for today. Exiting cleanly.")
        return

    publishers = build_publishers(cfg)
    all_results: dict[str, bool] = {}
    for i, item in enumerate(content_items, 1):
        logger.info("─── Processing item %d/%d ───", i, len(content_items))
        item_results = process_content_item(item, publishers, cfg, platform_filter=args.platform)
        all_results.update(item_results)

    logger.info("=" * 60)
    logger.info("  Results Summary")
    for platform, success in all_results.items():
        icon = "✅" if success else "❌"
        logger.info("  %s  %s", icon, platform)
    logger.info("=" * 60)

    send_summary(
        results=all_results,
        discord_url=cfg.discord_webhook_url,
        slack_url=cfg.slack_webhook_url,
    )


if __name__ == "__main__":
    main()
