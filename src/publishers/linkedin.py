import logging
import time
from pathlib import Path
from typing import Any, List
import requests
from .base import Publisher, PublishResult

logger = logging.getLogger(__name__)

LINKEDIN_API_BASE = "https://api.linkedin.com/v2"

class LinkedInPublisher(Publisher):
    """Publish posts to a LinkedIn personal profile or company page via direct REST API or Buffer."""

    def __init__(
        self,
        access_token: str = "",
        person_urn: str = "",
        organization_urn: str = None,
        mode: str = "direct",
        buffer_profile_id: str = "",
        dry_run: bool = False,
    ) -> None:
        self.access_token = access_token
        self.person_urn = person_urn
        self.organization_urn = organization_urn
        self.mode = mode.lower()
        self.buffer_profile_id = buffer_profile_id
        self.dry_run = dry_run
        self._headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
        }

    @property
    def platform_name(self) -> str:
        return "LinkedIn"

    def is_enabled(self) -> bool:
        if self.mode == "buffer":
            return bool(self.access_token and self.buffer_profile_id) or self.dry_run
        return bool(self.access_token and (self.person_urn or self.organization_urn)) or self.dry_run

    def publish(self, content: dict[str, Any]) -> PublishResult:
        """
        Create a LinkedIn post via direct REST API or Buffer.
        """
        if self.mode == "buffer":
            return self._publish_via_buffer(content)

        caption = content.get("caption", "")
        pdf_path = content.get("pdf_path")
        media_paths = content.get("media_paths", [])
        title = content.get("title") or "LITELAB Architectural Lighting Carousel"

        try:
            text, attributes = self._parse_mentions(caption)

            # 1. Native PDF Document Carousel
            if pdf_path and Path(pdf_path).exists():
                logger.info("Publishing as LinkedIn Document Carousel: %s", pdf_path)
                return self._post_document(text, attributes, pdf_path, title)

            # 2. Multi-image post
            if media_paths:
                logger.info("Publishing as LinkedIn Multi-Image post (%d images)", len(media_paths))
                return self._post_with_images(text, attributes, media_paths)

            # 3. Text only
            return self._post_text(text, attributes)
        except Exception as exc:
            logger.error("LinkedIn publish failed: %s", exc)
            return PublishResult(
                platform=self.platform_name,
                success=False,
                error=str(exc),
            )

    def _post_text(self, text: str, attributes: List[dict] = None) -> PublishResult:
        """Create a text-only post."""
        share_content = {
            "shareCommentary": {"text": text},
            "shareMediaCategory": "NONE",
        }
        if attributes:
            share_content["shareCommentary"]["attributes"] = attributes

        payload = {
            "author": self.organization_urn or self.person_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": share_content
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            },
        }
        resp = requests.post(f"{LINKEDIN_API_BASE}/ugcPosts", headers=self._headers, json=payload, timeout=30)
        if resp.status_code != 201:
            logger.error(f"LinkedIn UGC Post (Text) Error Body: {resp.text}")
        resp.raise_for_status()
        return self._format_result(resp.json())

    def _post_document(self, text: str, attributes: List[dict], pdf_path: str, title: str) -> PublishResult:
        """Handle upload of a native PDF document for LinkedIn swipeable carousels."""
        abs_path = Path(pdf_path)
        if not abs_path.is_absolute():
            abs_path = Path.cwd() / pdf_path

        if not abs_path.exists():
            return PublishResult(success=False, platform="LinkedIn", error=f"PDF not found at {abs_path}")

        # Step 1: Register document upload
        register_payload = {
            "registerUploadRequest": {
                "recipes": ["urn:li:digitalmediaRecipe:feedshare-document"],
                "owner": self.person_urn,
                "serviceRelationships": [{"relationshipType": "OWNER", "identifier": "urn:li:userGeneratedContent"}]
            }
        }
        reg_resp = requests.post(f"{LINKEDIN_API_BASE}/assets?action=registerUpload", headers=self._headers, json=register_payload)
        if reg_resp.status_code != 200:
            logger.error(f"LinkedIn Register Document Error Body: {reg_resp.text}")
        reg_resp.raise_for_status()

        data = reg_resp.json()
        upload_url = data['value']['uploadMechanism']['com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest']['uploadUrl']
        asset_urn = data['value']['asset']

        # Step 2: Upload Binary PDF
        with open(abs_path, 'rb') as f:
            headers = {"Authorization": f"Bearer {self.access_token}", "Content-Type": "application/pdf"}
            put_resp = requests.put(upload_url, data=f, headers=headers, timeout=60)
            put_resp.raise_for_status()

        logger.info(f"Uploaded LinkedIn Document PDF: {abs_path} -> {asset_urn}")

        # Step 3: Create UGC Post with DOCUMENT category
        share_content = {
            "shareCommentary": {"text": text},
            "shareMediaCategory": "DOCUMENT",
            "media": [{
                "status": "READY",
                "media": asset_urn,
                "title": {"text": title}
            }]
        }
        if attributes:
            share_content["shareCommentary"]["attributes"] = attributes

        payload = {
            "author": self.organization_urn or self.person_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": share_content
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }

        resp = requests.post(f"{LINKEDIN_API_BASE}/ugcPosts", headers=self._headers, json=payload, timeout=30)
        if resp.status_code != 201:
            logger.error(f"LinkedIn UGC Post (Document) Error Body: {resp.text}")
        resp.raise_for_status()
        return self._format_result(resp.json())

    def _post_with_images(self, text: str, attributes: List[dict], paths: List[str]) -> PublishResult:
        """Handle the 3-step handshake to upload multiple images and post."""
        media_urns = []
        for path in paths:
            abs_path = Path(path)
            if not abs_path.is_absolute():
                abs_path = Path.cwd() / path

            if not abs_path.exists():
                logger.warning(f"Media file not found: {abs_path}. Skipping.")
                continue

            # Step 1: Register Upload
            register_payload = {
                "registerUploadRequest": {
                    "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                    "owner": self.person_urn,
                    "serviceRelationships": [{"relationshipType": "OWNER", "identifier": "urn:li:userGeneratedContent"}]
                }
            }
            reg_resp = requests.post(f"{LINKEDIN_API_BASE}/assets?action=registerUpload", headers=self._headers, json=register_payload)
            if reg_resp.status_code != 200:
                logger.error(f"LinkedIn Register Upload Error Body: {reg_resp.text}")
            reg_resp.raise_for_status()

            data = reg_resp.json()
            upload_url = data['value']['uploadMechanism']['com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest']['uploadUrl']
            asset_urn = data['value']['asset']

            # Step 2: Upload Binary
            with open(abs_path, 'rb') as f:
                requests.put(upload_url, data=f)

            media_urns.append(asset_urn)
            logger.info(f"Uploaded image: {abs_path} -> {asset_urn}")

        if not media_urns and paths:
            return PublishResult(success=False, platform="LinkedIn", error="Failed to upload any images.")

        # Step 3: Create UGC Post with all assets
        media_content = []
        for urn in media_urns:
            media_content.append({
                "status": "READY",
                "media": urn,
                "title": {"text": "LITELAB Architectural Lighting Slide"}
            })

        share_content = {
            "shareCommentary": {"text": text},
            "shareMediaCategory": "IMAGE",
            "media": media_content
        }
        if attributes:
            share_content["shareCommentary"]["attributes"] = attributes

        payload = {
            "author": self.organization_urn or self.person_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": share_content
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }

        resp = requests.post(f"{LINKEDIN_API_BASE}/ugcPosts", headers=self._headers, json=payload, timeout=30)
        if resp.status_code != 201:
            logger.error(f"LinkedIn UGC Post (Images) Error Body: {resp.text}")
        resp.raise_for_status()
        return self._format_result(resp.json())

    def _format_result(self, data: dict) -> PublishResult:
        post_id = data.get("id", "")
        return PublishResult(
            platform=self.platform_name,
            success=True,
            post_id=post_id,
            post_url=f"https://www.linkedin.com/feed/update/{post_id}/",
            raw_response=data
        )

    def _parse_mentions(self, text: str) -> tuple[str, List[dict]]:
        """
        Replaces custom mention syntax @[urn:li:person:XXXX:0] or @[urn:li:organization:XXXX:0]
        with clean display names.
        """
        import re
        pattern = r"@\[(urn:li:(person|organization):[\w-]+):0\]"

        def replace_mention(match):
            urn = match.group(1)
            display_text = "LITELAB" if "organization:" in urn else urn
            return display_text

        cleaned_text = re.sub(pattern, replace_mention, text)
        return cleaned_text, []

    def _publish_via_buffer(self, content: dict[str, Any]) -> PublishResult:
        """Publish via Buffer's API for LinkedIn."""
        caption = content.get("caption", "")
        if self.dry_run or not self.access_token:
            logger.info("[LinkedIn Buffer DRY-RUN] Would publish via Buffer to profile: %s", self.buffer_profile_id)
            return PublishResult(
                platform=f"{self.platform_name} (Buffer)",
                success=True,
                post_id="mock_buffer_linkedin_id",
                post_url="https://www.linkedin.com/feed/",
            )

        payload = {
            "text": caption,
            "profile_ids": [self.buffer_profile_id],
            "now": True,
        }
        try:
            resp = requests.post(
                "https://api.bufferapp.com/1/updates/create.json",
                params={"access_token": self.access_token},
                json=payload,
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            update_id = ""
            if "updates" in data and data["updates"]:
                update_id = data["updates"][0].get("id", "")
            return PublishResult(
                platform=f"{self.platform_name} (Buffer)",
                success=data.get("success", False),
                post_id=update_id,
                raw_response=data,
            )
        except Exception as exc:
            logger.error("Buffer LinkedIn publication failed: %s", exc)
            return PublishResult(
                platform=f"{self.platform_name} (Buffer)",
                success=False,
                error=str(exc),
            )
