#!/usr/bin/env python3
"""
LITELAB — Interactive Slide Deck Generator
Generates an interactive, luxury architectural presentation deck (posts/<post>/deck/index.html)
from a post's post.json specification and composited Instagram 4:5 slides.
"""

import json
import argparse
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def build_deck(post_name: str = "Post_TEMPLATE"):
    post_dir = REPO_ROOT / "posts" / post_name
    if not post_dir.exists():
        print(f"[!] Post directory not found: {post_dir}")
        return

    post_json = post_dir / "post.json"
    if not post_json.exists():
        print(f"[!] post.json not found in {post_dir}")
        return

    with open(post_json, "r", encoding="utf-8") as f:
        meta = json.load(f)

    product = meta.get("product", post_name)
    title = meta.get("title", f"LITELAB — {product}")
    slides = meta.get("slides", [])

    deck_dir = post_dir / "deck"
    deck_dir.mkdir(parents=True, exist_ok=True)
    html_path = deck_dir / "index.html"

    slide_cards_html = "\n".join(
        [
            f'    <div class="slide-card"><img class="slide-img" src="../instagram/{product}_IG_{s.get("index", idx):02d}.png" alt="Slide {s.get("index", idx):02d}"></div>'
            for idx, s in enumerate(slides, start=1)
        ]
    )

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>LITELAB — {title}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;700&display=swap" rel="stylesheet">
  <style>
    :root {{
      --litelab-gold: #D4AF37;
      --obsidian: #0F1114;
      --slate: #94A3B8;
      --card-bg: #16191E;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Plus Jakarta Sans', sans-serif;
      background: var(--obsidian);
      color: #FFFFFF;
      display: flex;
      flex-direction: column;
      align-items: center;
      min-height: 100vh;
      padding: 28px 16px 48px;
    }}
    .header-bar {{
      font-family: 'Space Grotesk', sans-serif;
      color: var(--slate);
      font-size: 13px;
      letter-spacing: 0.18em;
      text-transform: uppercase;
      margin-bottom: 24px;
      display: flex;
      gap: 12px;
      align-items: center;
    }}
    .header-bar span {{
      color: var(--litelab-gold);
      font-weight: 700;
    }}
    .deck-container {{
      width: 100%;
      max-width: 520px;
      display: flex;
      flex-direction: column;
      gap: 28px;
    }}
    .slide-card {{
      position: relative;
      width: 100%;
      aspect-ratio: 1080 / 1350;
      background: var(--card-bg);
      border: 1px solid rgba(212, 175, 55, 0.18);
      border-radius: 12px;
      overflow: hidden;
      box-shadow: 0 16px 40px rgba(0, 0, 0, 0.55);
    }}
    .slide-img {{
      width: 100%;
      height: 100%;
      object-fit: cover;
      display: block;
    }}
  </style>
</head>
<body>
  <div class="header-bar">
    <span>LITELAB LIGHTING STUDIO</span> · {product}
  </div>
  <div class="deck-container">
{slide_cards_html}
  </div>
</body>
</html>
"""
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"[✓] Interactive LITELAB Deck generated: {html_path.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LITELAB Slide Deck Builder")
    parser.add_argument("--post", type=str, default="Post_TEMPLATE")
    args = parser.parse_args()
    build_deck(args.post)
