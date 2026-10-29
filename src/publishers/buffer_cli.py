"""
Buffer CLI Publisher for LITELAB.
Publishes directly to Instagram, LinkedIn, and Twitter/X via official @bufferapp/cli.
"""

from __future__ import annotations

import json
import logging
import subprocess
from typing import Any

from .base import Publisher, PublishResult

logger = logging.getLogger(__name__)


class BufferCliPublisher(Publisher):
    """Publish posts to social channels using the official Buffer CLI."""

    def __init__(
        self,
        channel_id: str,
        channel_name: str = "Buffer Channel",
        service: str = "social",
        mode: str = "addToQueue",
        dry_run: bool = False,
    ) -> None:
        self.channel_id = channel_id
        self.channel_name = channel_name
        self.service = service.lower()
        self.mode = mode
        self.dry_run = dry_run

    @property
    def platform_name(self) -> str:
        return self.service.capitalize()

    def is_enabled(self) -> bool:
        return bool(self.channel_id) or self.dry_run

    def publish(self, content: dict[str, Any]) -> PublishResult:
        text = content.get("caption") or content.get("text", "")
        mode = content.get("buffer_mode") or self.mode
        due_at = content.get("due_at") or content.get("scheduled_at")

        cmd = [
            "buffer",
            "posts",
            "create",
            "--channel-id",
            self.channel_id,
            "--scheduling-type",
            "automatic",
            "--mode",
            mode,
            "--text",
            text,
            "--output",
            "json",
        ]

        if due_at:
            cmd.extend(["--due-at", str(due_at)])

        if self.dry_run:
            cmd.append("--dry-run")

        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
            if res.returncode != 0:
                return PublishResult(
                    platform=self.platform_name,
                    success=False,
                    error=res.stderr.strip() or res.stdout.strip(),
                )

            data = json.loads(res.stdout) if res.stdout.strip().startswith("{") else {}
            post_id = data.get("post", {}).get("id", "dry_run_validated" if self.dry_run else "")
            return PublishResult(
                platform=self.platform_name,
                success=True,
                post_id=post_id,
                post_url="https://publish.buffer.com/",
                raw_response=data,
            )
        except Exception as exc:
            return PublishResult(platform=self.platform_name, success=False, error=str(exc))
