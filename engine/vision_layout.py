#!/usr/bin/env python3
"""
LITELAB — Automated Vision Negative Space Analyzer
Analyzes any architectural lighting render or photograph, computes saliency/detail occupancy
in the upper 40% working zone, and writes optimal bounding box coordinates for editorial typography.
"""

import json
import argparse
from pathlib import Path
from PIL import Image
import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent


def analyze_negative_space(image_path: Path, target_size: tuple[int, int] = (1080, 1350)) -> dict:
    """
    Computes foreground detail mask and evaluates left vs. right occupancy
    in the upper 40% working area to return optimal coordinates for LITELAB typography.
    """
    im = Image.open(image_path).convert("RGB")
    if im.size != target_size:
        im = im.resize(target_size, Image.Resampling.LANCZOS)
    arr = np.array(im)
    w, h = target_size

    bg = np.median(arr[:30, :30], axis=(0, 1))
    diff = np.abs(arr.astype(float) - bg).max(axis=2)
    active = diff > 25

    upper_active = active[110:560, :]
    left_occ = upper_active[:, : w // 2].sum()
    right_occ = upper_active[:, w // 2 :].sum()

    if left_occ <= right_occ:
        align = "left"
        x_pos = 55
        max_width = 500
    else:
        align = "right"
        x_pos = 540
        max_width = 480

    return {
        "align": align,
        "x_pos": int(x_pos),
        "y_pos": 120,
        "max_width": int(max_width),
        "headline_size": 42,
        "sub_size": 24,
    }


def analyze_post_canvases(post_name: str = "Post_TEMPLATE"):
    post_dir = REPO_ROOT / "posts" / post_name
    canvases_dir = post_dir / "canvases"
    post_json = post_dir / "post.json"

    if not post_json.exists():
        print(f"[!] post.json not found in {post_dir}")
        return

    with open(post_json, "r", encoding="utf-8") as f:
        meta = json.load(f)

    slides = meta.get("slides", [])
    print(f"Analyzing {len(slides)} slides for {post_name}...")
    for slide in slides:
        cname = slide.get("canvas_name", f"slide_{slide.get('index', 1):02d}.jpg")
        cpath = canvases_dir / cname
        if not cpath.exists():
            continue

        layout = analyze_negative_space(cpath)
        slide.update(layout)
        print(f"  ✓ Slide {slide['index']:02d}: {layout}")

    with open(post_json, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    print(f"\n[✓] Updated {post_json} with automated vision layout coordinates!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LITELAB Automated Vision Negative Space Analyzer")
    parser.add_argument("--post", type=str, default="Post_TEMPLATE")
    args = parser.parse_args()
    analyze_post_canvases(args.post)
