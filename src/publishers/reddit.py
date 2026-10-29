"""
Reddit Publisher for LITELAB.

Publishes architectural lighting guides, case studies, and discussions to targeted subreddits
(e.g., r/architecture, r/InteriorDesign, r/lightingdesign) or profile.
"""

from __future__ import annotations

import logging
from typing import Any

from .base import Publisher, PublishResult

logger = logging.getLogger(__name__)


class RedditPublisher(Publisher):
    """Publish to Reddit via official Reddit API / PRAW."""

    def __init__(
        self,
        client_id: str = "",
        client_secret: str = "",
        username: str = "",
        password: str = "",
        user_agent: str = "LITELAB-SMM-Bot/1.0",
        default_subreddit: str = "u_Litelab",
        dry_run: bool = False,
    ) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.username = username
        self.password = password
        self.user_agent = user_agent
        self.default_subreddit = default_subreddit
        self.dry_run = dry_run

    @property
    def platform_name(self) -> str:
        return "Reddit"

    def is_enabled(self) -> bool:
        return bool(self.client_id and self.client_secret and self.username and self.password) or self.dry_run

    def publish(self, content: dict[str, Any]) -> PublishResult:
        title = content.get("title") or content.get("caption", "")[:80]
        body = content.get("caption") or content.get("body", "")
        subreddit_name = content.get("subreddit") or self.default_subreddit
        url = content.get("url") or content.get("video_url", "")

        if self.dry_run or not (self.client_id and self.client_secret):
            logger.info(
                "[Reddit DRY-RUN] Would submit to r/%s: Title='%s' (Body length=%d chars)",
                subreddit_name,
                title,
                len(body),
            )
            return PublishResult(
                platform=self.platform_name,
                success=True,
                post_url=f"https://reddit.com/r/{subreddit_name}/mock_post",
                post_id="mock_reddit_id_123",
            )

        try:
            import praw  # type: ignore

            reddit = praw.Reddit(
                client_id=self.client_id,
                client_secret=self.client_secret,
                username=self.username,
                password=self.password,
                user_agent=self.user_agent,
            )

            sub = reddit.subreddit(subreddit_name)
            if url:
                submission = sub.submit(title=title, url=url)
            else:
                submission = sub.submit(title=title, selftext=body)

            post_url = f"https://reddit.com{submission.permalink}"
            return PublishResult(platform=self.platform_name, success=True, post_url=post_url, post_id=submission.id)
        except Exception as exc:
            logger.error("Reddit publication failed: %s", exc)
            return PublishResult(platform=self.platform_name, success=False, error=str(exc))
