#!/usr/bin/env python3
"""
LITELAB — Multi-Provider AI & Higgsfield Visual/Video Generator
Supported Providers:
1. higgsfield (Primary for LITELAB: GPT Image 2.5 for editorial/architectural visuals,
   Seedance 2.5 for architectural lighting video reels, Product Photoshoot for luminaires)
2. gemini (Google Gemini / Imagen via GEMINI_API_KEY)
3. pollinations (100% Free fallback, zero key needed, FLUX architectural model)
4. huggingface (FLUX.1-schnell via HF_TOKEN)
5. Portfolio & Local Ingestion (--ingest from D:\\hussain\\thesaurusxportfolio or Higgsfield downloads)
"""

import os
import sys
import json
import time
import shutil
import subprocess
import urllib.parse
import urllib.request
import argparse
from pathlib import Path
from PIL import Image

from engine.brand_engine import build_litelab_prompt

REPO_ROOT = Path(__file__).resolve().parent.parent


def load_dotenv():
    env_file = REPO_ROOT / ".env"
    if env_file.exists():
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


load_dotenv()


def generate_with_higgsfield(
    prompt: str,
    output_path: Path,
    model: str = "gpt_image_2_5",
    aspect_ratio: str = "4:5",
    media_type: str = "image",
    reference_image: str = None,
) -> bool:
    """
    Generate architectural lighting images or videos via Higgsfield CLI.
    - Image models: gpt_image_2_5 (default), soul_cinematic, nano_banana_pro
    - Video models: seedance_2_5 (default for reels), kling_2_0
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["higgsfield", "generate", "create", "--model", model, "--prompt", prompt, "--aspect_ratio", aspect_ratio, "--wait"]
    if reference_image and os.path.exists(reference_image):
        cmd.extend(["--image", reference_image])

    print(f"[*] Invoking Higgsfield AI ({model}, aspect={aspect_ratio})...")
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        output_text = (res.stdout or "") + "\n" + (res.stderr or "")
        # Extract generated media URL from Higgsfield CLI output
        urls = [token.strip() for token in output_text.split() if token.startswith("https://")]
        if urls:
            media_url = urls[-1]
            print(f"[*] Downloading Higgsfield asset: {media_url}")
            req = urllib.request.Request(media_url, headers={"User-Agent": "LITELAB-SMM/1.0"})
            with urllib.request.urlopen(req, timeout=120) as resp:
                with open(output_path, "wb") as f:
                    f.write(resp.read())
            print(f"[✓] Saved Higgsfield output: {output_path.name}")
            return True
        else:
            print(f"[!] Higgsfield CLI did not return a direct URL. Output:\n{output_text.strip()[:400]}")
            return False
    except FileNotFoundError:
        print("[!] 'higgsfield' CLI binary not found on PATH. Falling back to Pollinations FLUX...")
        return generate_with_pollinations(prompt, output_path)
    except Exception as exc:
        print(f"[!] Higgsfield generation error: {exc}")
        return False


def generate_with_pollinations(
    prompt: str,
    output_path: Path,
    width: int = 1080,
    height: int = 1350,
    model: str = "flux",
    seed: int = None,
) -> bool:
    """Generate an architectural lighting image using Pollinations.ai (FLUX)."""
    if seed is None:
        seed = int(time.time() * 1000) % 10000000

    encoded_prompt = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&model={model}&seed={seed}&nologo=true"

    print(f"[*] Calling Pollinations AI ({model})...")
    req = urllib.request.Request(url, headers={"User-Agent": "LITELAB-SMM/1.0"})

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = resp.read()
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(data)
        print(f"[✓] Saved canvas: {output_path.name} ({len(data)} bytes)")
        return True
    except Exception as exc:
        print(f"[!] Pollinations generation failed: {exc}")
        return False


def generate_with_huggingface(
    prompt: str,
    output_path: Path,
    model_id: str = "black-forest-labs/FLUX.1-schnell",
) -> bool:
    """Generate image via Hugging Face Inference API."""
    hf_token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_API_KEY")
    if not hf_token:
        print("[!] HF_TOKEN not found in .env. Falling back to Pollinations...")
        return generate_with_pollinations(prompt, output_path)

    url = f"https://api-inference.huggingface.co/models/{model_id}"
    headers = {"Authorization": f"Bearer {hf_token}", "Content-Type": "application/json"}
    payload = json.dumps({"inputs": prompt}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            data = resp.read()
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(data)
        print(f"[✓] Saved canvas via Hugging Face: {output_path.name}")
        return True
    except Exception as exc:
        print(f"[!] Hugging Face generation failed: {exc}")
        return False


def ingest_local_images(source_dir: Path, target_dir: Path, prefix: str = "slide") -> int:
    """Ingest LITELAB portfolio photographs or Higgsfield renders into a post's canvases folder."""
    if not source_dir.exists():
        print(f"[!] Source folder does not exist: {source_dir}")
        return 0

    target_dir.mkdir(parents=True, exist_ok=True)
    valid_exts = {".jpg", ".jpeg", ".png", ".webp"}
    images = sorted(
        [f for f in source_dir.iterdir() if f.is_file() and f.suffix.lower() in valid_exts and not f.name.startswith(".")],
        key=lambda f: f.stat().st_mtime,
    )

    if not images:
        print(f"[!] No valid image files found in {source_dir}")
        return 0

    count = 0
    for idx, img_file in enumerate(images, start=1):
        target_name = f"{prefix}_{idx:02d}.jpg"
        target_path = target_dir / target_name
        with Image.open(img_file) as im:
            rgb_im = im.convert("RGB")
            rgb_im.save(target_path, quality=95)
        print(f"  -> Ingested: {img_file.name} -> {target_name}")
        count += 1

    print(f"[✓] Successfully ingested {count} images into {target_dir}")
    return count


def generate_post_canvases(post_dir: Path, provider: str = "higgsfield"):
    """Generate or verify raw architectural lighting canvases for a LITELAB post."""
    post_json = post_dir / "post.json"
    canvases_dir = post_dir / "canvases"
    canvases_dir.mkdir(parents=True, exist_ok=True)

    if not post_json.exists():
        print(f"[!] post.json not found in {post_dir}")
        return

    with open(post_json, "r", encoding="utf-8") as f:
        meta = json.load(f)

    pillar = meta.get("pillar", "portfolio")
    slides = meta.get("slides", [])
    print(f"[*] Processing {len(slides)} slides for {post_dir.name} (pillar={pillar}, provider={provider})...")

    for slide in slides:
        idx = slide.get("index", 1)
        canvas_name = slide.get("canvas_name", f"slide_{idx:02d}.jpg")
        dest_path = canvases_dir / canvas_name

        if dest_path.exists():
            print(f"  [✓] Slide {idx:02d} canvas already exists: {dest_path.name}")
            continue

        raw_prompt = slide.get("image_prompt", "")
        align = slide.get("align", "left")
        neg_zone = "top-right third" if align == "right" else "top-left third"

        if not raw_prompt:
            tag = slide.get("tag", "ARCHITECTURAL LIGHTING")
            head = " ".join(slide.get("headline_lines", []))
            conditioned = build_litelab_prompt(
                pillar_key=pillar,
                scene_description=f"{tag} — {head}",
                negative_space_zone=neg_zone,
            )
            prompt = conditioned["prompt"]
        else:
            conditioned = build_litelab_prompt(
                pillar_key=pillar,
                scene_description=raw_prompt,
                negative_space_zone=neg_zone,
            )
            prompt = conditioned["prompt"]

        print(f"  [*] Generating Slide {idx:02d} canvas via {provider}...")
        if provider == "higgsfield":
            model = slide.get("higgsfield_model", os.getenv("HIGGSFIELD_IMAGE_MODEL", "gpt_image_2_5"))
            success = generate_with_higgsfield(prompt, dest_path, model=model, aspect_ratio="4:5")
        elif provider == "huggingface":
            success = generate_with_huggingface(prompt, dest_path)
        else:
            success = generate_with_pollinations(prompt, dest_path)

        if not success:
            print(f"  [!] Failed to generate slide {idx:02d}. Drop {canvas_name} into {canvases_dir}")


def main():
    parser = argparse.ArgumentParser(description="LITELAB Multi-Provider AI & Higgsfield Generator")
    parser.add_argument("--post", type=str, default="Post_TEMPLATE", help="Post folder name")
    parser.add_argument(
        "--provider",
        type=str,
        default=os.getenv("DEFAULT_AI_PROVIDER", "higgsfield"),
        choices=["higgsfield", "pollinations", "huggingface"],
        help="AI Provider (default: higgsfield)",
    )
    parser.add_argument("--prompt", type=str, default=None, help="Generate a single image/video from prompt")
    parser.add_argument("--model", type=str, default="gpt_image_2_5", help="Higgsfield model (e.g. gpt_image_2_5, seedance_2_5)")
    parser.add_argument("--output", type=str, default=None, help="Output path for single generation")
    parser.add_argument("--ingest", type=str, default=None, help="Source directory of LITELAB portfolio or Higgsfield images to ingest")

    args = parser.parse_args()

    if args.ingest:
        target_dir = REPO_ROOT / "posts" / args.post / "canvases"
        ingest_local_images(Path(args.ingest), target_dir)
        return

    if args.prompt and args.output:
        out_p = Path(args.output)
        if args.provider == "higgsfield":
            generate_with_higgsfield(args.prompt, out_p, model=args.model)
        elif args.provider == "huggingface":
            generate_with_huggingface(args.prompt, out_p)
        else:
            generate_with_pollinations(args.prompt, out_p)
        return

    post_dir = REPO_ROOT / "posts" / args.post
    generate_post_canvases(post_dir, provider=args.provider)


if __name__ == "__main__":
    main()
