"""
AI Caption Enhancer for LITELAB using Google Gemini.

Adapts architectural lighting captions for Zoho Social, LinkedIn, Instagram, and YouTube
with principal lighting design authority and anti-slop discipline.
"""

from __future__ import annotations

import logging
import time
from typing import Optional

logger = logging.getLogger(__name__)

PLATFORM_TONES = {
    "zohosocial": (
        "Architectural luxury and technical authority for LITELAB. Highlight spatial depth, "
        "layered illumination (2700K-3000K, CRI 97+, glare control), and bespoke architectural mood. "
        "Keep it crisp and editorial."
    ),
    "linkedin": (
        "Principal architectural lighting consultant tone for LITELAB. Speak to architects, "
        "interior designers, and luxury developers. Reference precision optics, UGR <16 glare control, "
        "and spatial hierarchy. End with an insightful architectural question."
    ),
    "youtube": (
        "High-impact architectural lighting reveal hook in the first 5 words. "
        "Focus on how light transforms residential and monumental spaces."
    ),
    "instagram": (
        "Refined architectural monograph aesthetic for @litelab.in. Evocative, sensory, and minimal. "
        "Include a subtle CTA to save the lighting study or book a consultation at litelab.in."
    ),
}

MAX_RETRIES = 3
RETRY_DELAY = 2


def _build_prompt(caption: str, platform: str, hashtags: list[str]) -> str:
    tone = PLATFORM_TONES.get(platform.lower(), PLATFORM_TONES["instagram"])
    hashtag_str = " ".join(hashtags) if hashtags else ""

    return (
        f"You are the Principal Editorial Director at LITELAB (litelab.in), "
        f"an elite architectural lighting design studio.\n"
        f"Refine the following caption for {platform.upper()}.\n\n"
        f"TONE GUIDELINES:\n{tone}\n\n"
        f"ORIGINAL CAPTION:\n\"{caption}\"\n\n"
        f"HASHTAGS TO INCLUDE:\n{hashtag_str}\n\n"
        f"RULES:\n"
        f"- Return ONLY the enhanced caption text.\n"
        f"- Never use AI clichés like 'delve', 'tapestry', 'unleash', 'game-changer', or 'elevate'.\n"
        f"- Append the hashtags cleanly at the end.\n"
    )


def enhance_caption(
    caption: str,
    platform: str,
    hashtags: list[str] | None = None,
    api_key: str = "",
) -> str:
    if not api_key:
        return _append_hashtags(caption, hashtags)

    hashtags = hashtags or []
    prompt = _build_prompt(caption, platform, hashtags)

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            import urllib.request
            import json

            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
            payload = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode("utf-8")
            req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                res_data = json.loads(resp.read().decode())
                enhanced = res_data["candidates"][0]["content"]["parts"][0]["text"].strip()
                if enhanced:
                    return enhanced
        except Exception as exc:
            logger.warning("Gemini enhancement attempt %d/%d failed: %s", attempt, MAX_RETRIES, exc)
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY * attempt)

    return _append_hashtags(caption, hashtags)


def _append_hashtags(caption: str, hashtags: Optional[list[str]]) -> str:
    if not hashtags:
        return caption
    tag_str = " ".join(hashtags)
    if tag_str in caption:
        return caption
    return f"{caption}\n\n{tag_str}"
