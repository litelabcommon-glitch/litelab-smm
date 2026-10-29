"""
WhatsApp Business Catalog Publisher for LITELAB.

Syncs architectural luminaire collections, residential packages, and consultation offerings
directly into the WhatsApp Business Catalog via Meta Commerce Management API.
"""

from __future__ import annotations

import logging
from typing import Any

import requests

from .base import Publisher, PublishResult

logger = logging.getLogger(__name__)

GRAPH_API_BASE = "https://graph.facebook.com/v19.0"


class WhatsAppCatalogPublisher(Publisher):
    """Sync LITELAB products & lighting consultation services into the WhatsApp Business Catalog."""

    def __init__(
        self,
        access_token: str = "",
        catalog_id: str = "",
        currency: str = "INR",
        dry_run: bool = False,
    ) -> None:
        self.access_token = access_token
        self.catalog_id = catalog_id
        self.currency = currency
        self.dry_run = dry_run

    @property
    def platform_name(self) -> str:
        return "WhatsAppCatalog"

    def is_enabled(self) -> bool:
        return bool(self.access_token and self.catalog_id) or self.dry_run

    def publish(self, content: dict[str, Any]) -> PublishResult:
        name = content.get("name") or content.get("title", "LITELAB Architectural Luminaire")
        description = content.get("description") or content.get("caption", "")
        retailer_id = content.get("retailer_id") or f"litelab-{int(hash(name)) % 100000}"
        image_url = content.get("image_url") or content.get("asset_url", "")
        product_url = content.get("url", "https://litelab.in")
        price = content.get("price", 25000)

        if self.dry_run or not (self.access_token and self.catalog_id):
            logger.info(
                "[WhatsApp Catalog DRY-RUN] Would sync SKU='%s': '%s' (%s %s) to Catalog %s",
                retailer_id,
                name,
                self.currency,
                price,
                self.catalog_id or "MOCK_CATALOG_ID",
            )
            return PublishResult(
                platform=self.platform_name,
                success=True,
                post_url=f"https://wa.me/c/product/{retailer_id}",
                post_id=retailer_id,
            )

        try:
            url = f"{GRAPH_API_BASE}/{self.catalog_id}/products"
            headers = {"Authorization": f"Bearer {self.access_token}"}
            payload = {
                "retailer_id": retailer_id,
                "name": name[:100],
                "description": description[:5000],
                "availability": "in stock",
                "condition": "new",
                "price": str(price),
                "currency": self.currency,
                "url": product_url,
                "image_url": image_url,
            }

            res = requests.post(url, json=payload, headers=headers, timeout=30)
            res.raise_for_status()
            data = res.json()
            product_id = data.get("id", retailer_id)

            return PublishResult(
                platform=self.platform_name,
                success=True,
                post_url=f"https://wa.me/c/product/{product_id}",
                post_id=product_id,
                raw_response=data,
            )
        except Exception as exc:
            logger.error("WhatsApp Catalog sync failed: %s", exc)
            return PublishResult(platform=self.platform_name, success=False, error=str(exc))
