"""
X / Twitter Publisher for LITELAB.

Publishes architectural lighting threads, project reveals, and video clips via X API v2.
"""

from __future__ import annotations

import logging
from typing import Any

import requests

from .base import Publisher, PublishResult

logger = logging.getLogger(__name__)

TWITTER_API_V2_BASE = "https://api.twitter.com/2"


class TwitterPublisher(Publisher):
    """Publish to X / Twitter via API v2 endpoints or dry-run simulation."""

    def __init__(
        self,
        api_key: str = "",
        api_secret: str = "",
        access_token: str = "",
        access_token_secret: str = "",
        bearer_token: str = "",
        dry_run: bool = False,
    ) -> None:
        self.api_key = api_key
        self.api_secret = api_secret
        self.access_token = access_token
        self.access_token_secret = access_token_secret
        self.bearer_token = bearer_token
        self.dry_run = dry_run

    @property
    def platform_name(self) -> str:
        return "Twitter"

    def is_enabled(self) -> bool:
        return bool((self.api_key and self.access_token) or self.bearer_token) or self.dry_run

    def publish(self, content: dict[str, Any]) -> PublishResult:
        text = content.get("caption") or content.get("text", "")
        if len(text) > 280 and not content.get("thread"):
            logger.warning("Tweet text exceeds 280 chars; truncating.")
            text = text[:277] + "..."

        if self.dry_run or not (self.api_key and self.access_token):
            logger.info("[Twitter DRY-RUN] Would tweet to @litelab_in: '%s' (%d chars)", text, len(text))
            return PublishResult(
                platform=self.platform_name,
                success=True,
                post_url="https://twitter.com/litelab_in/status/mock_tweet_123",
                post_id="mock_tweet_123",
            )

        try:
            from requests_oauthlib import OAuth1  # type: ignore

            auth = OAuth1(
                self.api_key,
                self.api_secret,
                self.access_token,
                self.access_token_secret,
            )

            payload = {"text": text}
            if content.get("media_ids"):
                payload["media"] = {"media_ids": content["media_ids"]}

            res = requests.post(f"{TWITTER_API_V2_BASE}/tweets", json=payload, auth=auth, timeout=30)
            res.raise_for_status()
            data = res.json().get("data", {})
            tweet_id = data.get("id", "")
            tweet_url = f"https://twitter.com/litelab_in/status/{tweet_id}"

            logger.info("Tweet published successfully: %s", tweet_url)
            return PublishResult(
                platform=self.platform_name,
                success=True,
                post_url=tweet_url,
                post_id=tweet_id,
                raw_response=res.json(),
            )
        except Exception as exc:
            logger.error("Twitter publication failed: %s", exc)
            return PublishResult(platform=self.platform_name, success=False, error=str(exc))
