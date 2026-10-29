#!/usr/bin/env python3
"""
LITELAB — Architectural Lighting Visual & Brand Conditioning Engine
Implements strict prompt conditioning for Higgsfield AI (GPT Image 2.5, Seedance 2.5,
Product Photoshoot), negative space composition, and anti-slop copy validation
across LITELAB's three content pillars: portfolio, thesaurus, and atelier.
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
PORTFOLIO_EXTRACT_DIR = Path(r"D:\hussain\thesaurusxportfolio\LITELAB_Portfolio_Extract\images")

# Mandatory architectural realism lock phrase appended to generative prompts
ARCHITECTURAL_LOCK_PHRASE = (
    "Photorealistic architectural photography, shot on Hasselblad H6D-100c with 24mm tilt-shift lens, "
    "perfect vertical lines, authentic 2700K-3000K warm architectural illumination, CRI 98, "
    "concealed light sources, zero visible glare, natural shadow falloff across tactile stone, timber, "
    "and brushed brass surfaces. Render ZERO text, letters, numbers, or logos inside the image."
)

# Strictly banned words in architectural image prompts
BANNED_PROMPT_WORDS = ["cartoon", "anime", "neon cyberpunk", "clay", "claymation", "plasticine", "sci-fi hologram"]

# Strictly banned AI clichés in copywriting
BANNED_COPY_WORDS = [
    "delve",
    "tapestry",
    "game-changer",
    "unleash",
    "revolutionary",
    "testament",
    "in today's fast-paced digital landscape",
    "transformative",
    "seamlessly",
    "elevate your space",
]

NEGATIVE_SPACE_MANDATE = (
    "Compose the architectural subject in the lower 60% of the frame, leaving a clean, "
    "uncluttered 40% negative space plane (smooth Venetian plaster wall, dark nocturnal sky, "
    "or calm shadow gradient) in the upper third for editorial typography."
)

PILLAR_SPECS = {
    "portfolio": {
        "name": "Architectural Monograph (Portfolio)",
        "tag_default": "RESIDENTIAL MONOGRAPH",
        "domain": "Luxury Residential Villas, Penthouses, Hospitality, Facades & Landscape Lighting",
        "higgsfield_image_model": "gpt_image_2_5",
        "higgsfield_video_model": "seedance_2_5",
        "style_directive": (
            "Ultra-luxury contemporary residential architecture at dusk, warm 2700K cove illumination, "
            "subtle wall grazing on natural travertine stone, dramatic focal accent lighting on sculpture, "
            "serene architectural reflection pool"
        ),
        "voice": "Refined, editorial monograph tone — architectural poetry grounded in spatial precision (<12 words per slide headline).",
    },
    "thesaurus": {
        "name": "The Lighting Thesaurus (Education & Science)",
        "tag_default": "LIGHTING THESAURUS",
        "domain": "3-Tier Layered Illumination, Glare Control (UGR <16), CRI 97+, Beam Angles, Circadian Design",
        "higgsfield_image_model": "gpt_image_2_5",
        "higgsfield_video_model": "seedance_2_5",
        "style_directive": (
            "Minimalist architectural interior study demonstrating precision beam spread, "
            "deep-recessed anti-glare pinhole downlights casting crisp 15-degree scalloped light cones "
            "on textured limestone wall, warm 2700K vs 3000K layered contrast"
        ),
        "voice": "Authoritative principal lighting consultant — technical clarity (Kelvin, CRI, UGR, lux) made intuitive for architects and homeowners.",
    },
    "atelier": {
        "name": "Luminaire & Product Atelier",
        "tag_default": "LUMINAIRE ATELIER",
        "domain": "Precision Trimless Fixtures, Magnetic Track Systems, Bespoke Brass & Alabaster Luminaires",
        "higgsfield_image_model": "gpt_image_2_5",
        "higgsfield_video_model": "seedance_2_5",
        "style_directive": (
            "Macro studio product photography of a precision-machined anodized black and brushed brass "
            "architectural luminaire resting on a dark basalt stone plinth, subtle warm 2700K optical lens glow, "
            "dramatic rim lighting, dark obsidian #0F1114 studio backdrop"
        ),
        "voice": "Craftsmanship-focused, highlighting optical engineering, thermal management, and Italian-inspired minimalist hardware.",
    },
}


def sanitize_prompt(raw_prompt: str) -> Tuple[str, List[str]]:
    """Strips banned words and returns cleaned prompt and detected violations."""
    violations = []
    cleaned = raw_prompt
    for banned in BANNED_PROMPT_WORDS:
        pattern = re.compile(rf"\b{re.escape(banned)}\b", re.IGNORECASE)
        if pattern.search(cleaned):
            violations.append(banned)
            cleaned = pattern.sub("", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned, violations


def build_litelab_prompt(
    pillar_key: str = "portfolio",
    scene_description: str = "",
    lighting_technique: str = "2700K warm architectural cove and accent grazing",
    negative_space_zone: str = "top-left third",
    aspect_ratio: str = "4:5",
) -> Dict:
    """
    Builds a fully-conditioned architectural lighting prompt for Higgsfield AI
    (GPT Image 2.5 / Seedance 2.5 / Product Photoshoot).
    """
    pk = pillar_key.lower().strip()
    if pk not in PILLAR_SPECS:
        raise ValueError(f"Unknown pillar '{pillar_key}'. Must be one of: portfolio, thesaurus, atelier.")

    spec = PILLAR_SPECS[pk]
    subject = scene_description.strip() if scene_description.strip() else spec["style_directive"]

    raw_scene = (
        f"LITELAB Architectural Lighting Study ({spec['name']}). "
        f"Scene: {subject}. "
        f"Lighting Specification: {lighting_technique}. "
        f"Framing: Primary illuminated subject anchored in lower frame with clean negative space in the {negative_space_zone}. "
        f"{NEGATIVE_SPACE_MANDATE} "
        f"{ARCHITECTURAL_LOCK_PHRASE}"
    )

    clean_prompt, violations = sanitize_prompt(raw_scene)

    return {
        "pillar": spec["name"],
        "key": pk,
        "recommended_image_model": spec["higgsfield_image_model"],
        "recommended_video_model": spec["higgsfield_video_model"],
        "prompt": clean_prompt,
        "violations_removed": violations,
        "negative_space_zone": negative_space_zone,
        "aspect_ratio": aspect_ratio,
    }


def validate_copy(text: str, max_headline_words: int = 14) -> Tuple[bool, List[str]]:
    """Validates copywriting against banned AI slop words and editorial length rules."""
    issues = []
    lower_text = text.lower()

    for banned in BANNED_COPY_WORDS:
        if banned in lower_text:
            issues.append(f"Contains banned AI slop word/phrase: '{banned}'")

    words = text.strip().split()
    if max_headline_words and len(words) > max_headline_words:
        issues.append(f"Headline exceeds {max_headline_words} words ({len(words)} words)")

    return len(issues) == 0, issues


if __name__ == "__main__":
    import argparse
    import sys

    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    parser = argparse.ArgumentParser(
        description="LITELAB — Architectural Lighting Prompt Engine for Higgsfield AI"
    )
    parser.add_argument(
        "--pillar",
        choices=["portfolio", "thesaurus", "atelier"],
        default="portfolio",
        help="Target LITELAB content pillar (portfolio, thesaurus, atelier)",
    )
    parser.add_argument(
        "--scene",
        type=str,
        default="Double-height luxury residential living room in Chennai with travertine feature wall",
        help="Architectural scene or luminaire description",
    )
    parser.add_argument(
        "--lighting",
        type=str,
        default="2700K concealed perimeter cove lighting paired with 15-degree narrow-beam artwork spots",
        help="Specific architectural lighting technique",
    )
    parser.add_argument(
        "--zone",
        type=str,
        default="top-left third",
        help="Negative space zone for typography (e.g. top-left third, top-right third)",
    )

    args = parser.parse_args()
    res = build_litelab_prompt(
        pillar_key=args.pillar,
        scene_description=args.scene,
        lighting_technique=args.lighting,
        negative_space_zone=args.zone,
    )

    print("\n" + "=" * 68)
    print(f"✨ LITELAB HIGGSFIELD PROMPT — {res['pillar'].upper()}")
    print("=" * 68)
    print(f"📌 Image Model: {res['recommended_image_model']} | Video Model: {res['recommended_video_model']}")
    if res["violations_removed"]:
        print(f"⚠️  Stripped banned words: {res['violations_removed']}")
    print("-" * 68)
    print(res["prompt"])
    print("=" * 68 + "\n")
