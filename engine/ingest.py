#!/usr/bin/env python3
"""
LITELAB — Portfolio & Higgsfield Asset Ingestion Engine

Usage:
    # 1. Ingest a LITELAB project folder from D:\hussain\thesaurusxportfolio into a Post:
    python -m engine.ingest "D:/hussain/thesaurusxportfolio/LITELAB_Portfolio_Extract/images/01_Azure-The-Oceanic_Chennai" --post Post_01_Azure_Oceanic

    # 2. Ingest a downloaded Higgsfield ZIP or folder into a Post:
    python -m engine.ingest "~/Downloads/higgsfield_renders.zip" --post Post_01_Azure_Oceanic
"""

import os
import json
import shutil
import zipfile
import tempfile
import argparse
from pathlib import Path
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parent.parent


def find_candidates(search_dir: Path) -> list[Path]:
    """Find recent zip files or image folders in search_dir."""
    if not search_dir.exists():
        return []
    valid_exts = {".png", ".jpg", ".jpeg", ".webp"}
    candidates = []
    zips = sorted(search_dir.glob("*.zip"), key=os.path.getmtime, reverse=True)
    candidates.extend(zips)
    imgs = [f for f in search_dir.iterdir() if f.is_file() and f.suffix.lower() in valid_exts]
    if imgs:
        candidates.append(search_dir)
    return candidates


def ingest_to_post(source_path: Path, post_name: str) -> int:
    """Ingest images into posts/<post_name>/canvases/ as standardized JPEGs."""
    post_dir = REPO_ROOT / "posts" / post_name
    canvases_dir = post_dir / "canvases"
    canvases_dir.mkdir(parents=True, exist_ok=True)

    extracted_files = []
    temp_dir = Path(tempfile.gettempdir()) / "litelab_ingest"
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir(parents=True, exist_ok=True)

    valid_exts = {".png", ".jpg", ".jpeg", ".webp"}

    if source_path.is_file() and source_path.suffix.lower() == ".zip":
        print(f"[*] Extracting ZIP: {source_path.name} ...")
        with zipfile.ZipFile(source_path, "r") as z:
            for member in z.namelist():
                if any(member.lower().endswith(ext) for ext in valid_exts):
                    fname = os.path.basename(member)
                    if fname and not fname.startswith("."):
                        z.extract(member, temp_dir)
                        extracted_files.append(temp_dir / member)
    elif source_path.is_dir():
        print(f"[*] Scanning folder: {source_path} ...")
        for f in sorted(source_path.iterdir(), key=lambda p: p.name):
            if f.is_file() and f.suffix.lower() in valid_exts and not f.name.startswith("."):
                extracted_files.append(f)

    if not extracted_files:
        print(f"[!] No valid images found in {source_path}")
        return 0

    post_json = post_dir / "post.json"
    canvas_names = []
    if post_json.exists():
        try:
            with open(post_json, "r", encoding="utf-8") as f:
                meta = json.load(f)
                canvas_names = [s.get("canvas_name") for s in meta.get("slides", []) if s.get("canvas_name")]
        except Exception:
            pass

    count = 0
    for idx, src in enumerate(extracted_files, start=1):
        if idx - 1 < len(canvas_names) and canvas_names[idx - 1]:
            target_name = canvas_names[idx - 1]
        else:
            target_name = f"slide_{idx:02d}.jpg"

        target_path = canvases_dir / target_name
        try:
            with Image.open(src) as im:
                rgb_im = im.convert("RGB")
                rgb_im.save(target_path, quality=95)
            print(f"  ✓ Ingested: {src.name} → {target_name}")
            count += 1
        except Exception as e:
            print(f"  [!] Failed to convert {src.name}: {e}")

    print(f"\n[✓] Successfully ingested {count} canvases into {canvases_dir}")
    print(f"Next step: python -m engine.compositor --post {post_name}")
    return count


def main():
    parser = argparse.ArgumentParser(description="LITELAB Portfolio & Higgsfield Asset Ingestion Engine")
    parser.add_argument("source", nargs="?", default=None, help="Path to ZIP or folder")
    parser.add_argument("--post", type=str, default="Post_TEMPLATE", help="Target post folder name")

    args = parser.parse_args()

    source_path = None
    if args.source:
        source_path = Path(args.source).expanduser()
    else:
        downloads = Path.home() / "Downloads"
        candidates = find_candidates(downloads)
        if candidates:
            source_path = candidates[0]
            print(f"[*] Auto-detected source from {downloads}: {source_path.name}")
        else:
            print("[!] No source path provided. Pass a folder or ZIP path.")
            return

    ingest_to_post(source_path, args.post)


if __name__ == "__main__":
    main()
