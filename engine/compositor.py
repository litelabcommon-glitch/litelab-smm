#!/usr/bin/env python3
"""
LITELAB — Official Architectural Editorial Slide Compositor (v6.0)
Brand: LITELAB (@litelab.in · litelab.in)

Layout Architecture:
- Instagram & LinkedIn Vertical (4:5 Aspect Ratio — 1080x1350):
    - Top-Left HUD: @litelab.in (24pt Bold, Adaptive Obsidian/White) at (55, 45)
    - Top-Right HUD: Swipe → / Book Lighting Consult → (24pt Bold, Architectural Gold #D4AF37)
    - Bottom-Left HUD: 01 / 08 Pagination (28pt Bold: 01 in Gold #D4AF37, / 08 in Adaptive Slate/White)
    - Bottom-Right HUD: Concentric Circular LITELAB Logo Stamp (110x110) at (915, 1205)
    - Smart Luminance Contrast: Automatically adapts headline & subheadline colors for dark nocturnal
      lighting photography vs. light gallery diagrams while keeping [bracketed] keywords in Gold (#D4AF37).
- WhatsApp Business & Zoho Social Square (1:1 Aspect Ratio — 1080x1080):
    - Bottom-aligned square crop preserving architectural subjects and luminaire details.
"""

import os
import sys
import re
import json
import shutil
import argparse
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

REPO_ROOT = Path(__file__).resolve().parent.parent

# LITELAB Brand Color Tokens
GOLD = (212, 175, 55, 255)          # #D4AF37 — Architectural Brass / Gold Accent
DARK_OBSIDIAN = (15, 17, 20, 255)   # #0F1114 — Primary Dark Surface / Light-Mode Headline
GRAY_SUB_DARK = (71, 85, 105, 255)  # #475569 — Light-Mode Subtext
GRAY_SUB_LIGHT = (203, 213, 225, 255)  # #CBD5E1 — Dark-Mode Subtext
WHITE = (255, 255, 255, 255)        # #FFFFFF — Dark-Mode Headline


def load_font(size: int, bold: bool = False):
    """Cross-platform font loader supporting custom repo fonts, Windows, macOS, and Linux."""
    custom_bold = REPO_ROOT / "assets" / "fonts" / "Poppins-Bold.ttf"
    custom_reg = REPO_ROOT / "assets" / "fonts" / "Poppins-Regular.ttf"
    paths = [
        str(custom_bold if bold else custom_reg),
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "/root/.fonts/Poppins-Bold.ttf" if bold else "/root/.fonts/Poppins-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for p in paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def ensure_litelab_logo_stamp() -> Path:
    """
    Ensures assets/branding/brand_logo_round.png exists.
    Generates a crisp 440x440 concentric Obsidian & Architectural Gold LITELAB stamp if missing.
    """
    logo_path = REPO_ROOT / "assets" / "branding" / "brand_logo_round.png"
    if logo_path.exists():
        return logo_path

    logo_path.parent.mkdir(parents=True, exist_ok=True)
    size = 440
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Outer Obsidian circle with subtle border
    draw.ellipse((8, 8, size - 8, size - 8), fill=DARK_OBSIDIAN, outline=GOLD, width=6)
    # Inner concentric Architectural Gold ring
    draw.ellipse((28, 28, size - 28, size - 28), outline=(212, 175, 55, 140), width=2)

    # Center typography: LITELAB + MILANO
    f_main = load_font(56, bold=True)
    f_sub = load_font(22, bold=True)

    b_main = draw.textbbox((0, 0), "LITELAB", font=f_main)
    w_main = b_main[2] - b_main[0]
    h_main = b_main[3] - b_main[1]
    draw.text(((size - w_main) // 2, (size // 2) - h_main + 4), "LITELAB", font=f_main, fill=WHITE)

    sub_text = "LIGHTING STUDIO"
    b_sub = draw.textbbox((0, 0), sub_text, font=f_sub)
    w_sub = b_sub[2] - b_sub[0]
    draw.text(((size - w_sub) // 2, (size // 2) + 22), sub_text, font=f_sub, fill=GOLD)

    # Top geometric light beam accent dot
    draw.ellipse(((size // 2) - 8, 68, (size // 2) + 8, 84), fill=GOLD)

    img.save(logo_path, "PNG")
    return logo_path


def sample_region_luminance(img: Image.Image, box: tuple[int, int, int, int]) -> float:
    """Compute mean luminance (0..255) inside a bounding box."""
    x1, y1, x2, y2 = (
        max(0, box[0]),
        max(0, box[1]),
        min(img.width, box[2]),
        min(img.height, box[3]),
    )
    if x2 <= x1 or y2 <= y1:
        return 200.0
    crop = img.crop((x1, y1, x2, y2)).convert("L")
    return float(np.array(crop).mean())


def parse_spans(text: str):
    spans = []
    tokens = re.split(r"(\[[^\]]+\])", text)
    for token in tokens:
        if not token:
            continue
        if token.startswith("[") and token.endswith("]"):
            spans.append((token[1:-1], True))
        else:
            clean = token.replace("[", "").replace("]", "")
            if clean:
                spans.append((clean, False))
    return spans


def wrap_text(draw, text: str, font, max_width: int):
    words = text.split()
    lines = []
    current_line = []
    for word in words:
        test_line = " ".join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=font)
        w = bbox[2] - bbox[0]
        if w <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(" ".join(current_line))
                current_line = [word]
            else:
                lines.append(word)
    if current_line:
        lines.append(" ".join(current_line))
    return lines


def draw_vector_arrow(draw, start_x: int, start_y: int, length: int = 22, color=GOLD, stroke: int = 3):
    """Draws a pixel-perfect geometric vector arrow."""
    stroke = int(round(stroke))
    end_x = start_x + length
    end_y = start_y
    draw.line([(start_x, end_y), (end_x, end_y)], fill=color, width=stroke)
    head = 7
    draw.line([(end_x - head, end_y - head), (end_x, end_y)], fill=color, width=stroke)
    draw.line([(end_x - head, end_y + head), (end_x, end_y)], fill=color, width=stroke)


def draw_top_hud(
    img: Image.Image,
    brand_handle: str = "@litelab.in",
    is_last_slide: bool = False,
    cue_text: str = None,
    has_arrow: bool = None,
    default_last_cue: str = "Book Lighting Consult →",
    x_pad: int = 55,
    y_pad: int = 45,
    font_size: int = 24,
):
    draw = ImageDraw.Draw(img)
    f_handle = load_font(font_size, bold=True)

    # Adaptive handle color based on top-left background luminance
    top_luma = sample_region_luminance(img, (x_pad, y_pad, x_pad + 220, y_pad + 40))
    handle_fill = WHITE if top_luma < 130 else DARK_OBSIDIAN
    draw.text((x_pad, y_pad), brand_handle, font=f_handle, fill=handle_fill)

    if cue_text is None:
        cue_text = default_last_cue if is_last_slide else "Swipe →"
    if has_arrow is None:
        has_arrow = ("→" in cue_text or cue_text.endswith("->"))

    cue_clean = cue_text.replace("→", "").replace("->", "").strip()
    f_cue = load_font(font_size, bold=True)
    b = draw.textbbox((0, 0), cue_clean, font=f_cue)
    tw = b[2] - b[0]
    th = b[3] - b[1]

    if has_arrow:
        arrow_len = int(font_size * 0.9)
        gap = 10
        total_w = tw + gap + arrow_len
        swipe_x = img.width - x_pad - total_w
        swipe_y = y_pad
        draw.text((swipe_x, swipe_y), cue_clean, font=f_cue, fill=GOLD)
        draw_vector_arrow(draw, swipe_x + tw + gap, swipe_y + (th // 2), length=arrow_len, color=GOLD, stroke=3)
    else:
        swipe_x = img.width - x_pad - tw
        swipe_y = y_pad
        draw.text((swipe_x, swipe_y), cue_clean, font=f_cue, fill=GOLD)


def draw_bottom_hud(
    img: Image.Image,
    slide_idx: int,
    total_slides: int,
    logo_img: Image.Image,
    inpaint_watermark: bool = False,
    x_pad: int = 55,
    y_pad: int = 1265,
    logo_pos: tuple[int, int] = (915, 1205),
    stamp_size: int = 110,
    font_size: int = 28,
):
    draw = ImageDraw.Draw(img)

    if inpaint_watermark:
        center_x = logo_pos[0] + stamp_size // 2
        center_y = logo_pos[1] + stamp_size // 2
        floor_color = img.getpixel((min(img.width - 20, center_x + 50), center_y))[:3]
        patch_radius = int(stamp_size * 0.45)
        draw.ellipse(
            [
                center_x - patch_radius,
                center_y - patch_radius,
                center_x + patch_radius,
                center_y + patch_radius,
            ],
            fill=floor_color,
        )

    if logo_img:
        logo_stamp = logo_img.resize((stamp_size, stamp_size), Image.Resampling.LANCZOS)
        img.paste(logo_stamp, logo_pos, logo_stamp)

    f_pag = load_font(font_size, bold=True)
    curr_str = f"{slide_idx:02d}"
    tot_str = f" / {total_slides:02d}"
    b_curr = draw.textbbox((0, 0), curr_str, font=f_pag)
    tw_curr = b_curr[2] - b_curr[0]

    avg_luma = sample_region_luminance(img, (x_pad, y_pad, x_pad + 140, y_pad + 35))
    tot_fill = WHITE if avg_luma < 130 else DARK_OBSIDIAN

    draw.text((x_pad, y_pad), curr_str, font=f_pag, fill=GOLD)
    draw.text((x_pad + tw_curr, y_pad), tot_str, font=f_pag, fill=tot_fill)


def composite_vertical(
    canvas_path: Path,
    spec: dict,
    logo_img: Image.Image,
    brand_handle: str = "@litelab.in",
    total_slides: int = 8,
    default_last_cue: str = "Book Lighting Consult →",
    inpaint_watermark: bool = False,
    target_size: tuple[int, int] = (1080, 1350),
) -> Image.Image:
    raw = Image.open(canvas_path).convert("RGBA")
    w, h = raw.size
    target_w, target_h = target_size

    crop_h = int(w * target_h / target_w)
    if h > crop_h:
        img = raw.crop((0, h - crop_h, w, h)).resize(target_size, Image.Resampling.LANCZOS)
    else:
        img = raw.resize(target_size, Image.Resampling.LANCZOS)

    idx = spec["index"]
    is_last = idx == total_slides

    cue_text = spec.get("cue_word")
    has_arrow = spec.get("has_arrow")
    draw_top_hud(
        img,
        brand_handle=brand_handle,
        is_last_slide=is_last,
        cue_text=cue_text,
        has_arrow=has_arrow,
        default_last_cue=default_last_cue,
        x_pad=55,
        y_pad=45,
        font_size=24,
    )
    draw_bottom_hud(
        img,
        idx,
        total_slides,
        logo_img,
        inpaint_watermark=spec.get("inpaint_watermark", inpaint_watermark),
        x_pad=55,
        y_pad=target_h - 85,
        logo_pos=(target_w - 165, target_h - 145),
        stamp_size=110,
        font_size=28,
    )

    draw = ImageDraw.Draw(img)

    x_start = spec.get("x_pos", 55)
    y_pos = spec.get("y_pos", 120)
    max_text_width = spec.get("max_width", 500)
    headline_size = spec.get("headline_size", 42)
    sub_size = spec.get("sub_size", 24)
    tag_size = spec.get("tag_size", 20)

    # Smart Luminance Contrast Detection in the negative space region
    text_luma = sample_region_luminance(img, (x_start, y_pos, x_start + max_text_width, y_pos + 320))
    is_dark_bg = text_luma < 128
    primary_text_col = WHITE if is_dark_bg else DARK_OBSIDIAN
    sub_text_col = GRAY_SUB_LIGHT if is_dark_bg else GRAY_SUB_DARK

    f_tag = load_font(tag_size, bold=True)
    f_head = load_font(headline_size, bold=True)
    f_sub = load_font(sub_size, bold=False)

    line_h = int(headline_size * 1.28)
    sub_line_h = int(sub_size * 1.42)

    # Category Tag (|  TAG)
    tag_str = f"|  {spec['tag']}"
    draw.text((x_start, y_pos), tag_str, font=f_tag, fill=GOLD)
    y_pos += int(tag_size * 1.8)

    # Multi-line Headline
    for line in spec["headline_lines"]:
        spans = parse_spans(line)
        cx = x_start
        for text_part, is_gold in spans:
            col = GOLD if is_gold else primary_text_col
            draw.text((cx, y_pos), text_part, font=f_head, fill=col)
            b = draw.textbbox((0, 0), text_part, font=f_head)
            cx += b[2] - b[0]
        y_pos += line_h

    # Subheadline with Word Wrapping
    y_pos += 18
    sub_lines = wrap_text(draw, spec.get("subheadline", ""), f_sub, max_text_width)
    for s_line in sub_lines:
        draw.text((x_start, y_pos), s_line, font=f_sub, fill=sub_text_col)
        y_pos += sub_line_h

    return img.convert("RGB")


def composite_square(
    canvas_path: Path,
    spec: dict,
    logo_img: Image.Image,
    brand_handle: str = "@litelab.in",
    total_slides: int = 8,
    default_last_cue: str = "Book Lighting Consult →",
    inpaint_watermark: bool = False,
) -> Image.Image:
    """1:1 Square Compositor (1080x1080) for WhatsApp Catalog & Square Social Feeds."""
    raw = Image.open(canvas_path).convert("RGBA")
    w, h = raw.size

    crop_sq = raw.crop((0, max(0, h - w), w, h)).resize((1080, 1080), Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(crop_sq)
    idx = spec["index"]
    is_last = idx == total_slides

    draw_top_hud(
        crop_sq,
        brand_handle=brand_handle,
        is_last_slide=is_last,
        cue_text=spec.get("cue_word"),
        has_arrow=spec.get("has_arrow"),
        default_last_cue=default_last_cue,
        x_pad=55,
        y_pad=45,
        font_size=24,
    )

    draw_bottom_hud(
        crop_sq,
        idx,
        total_slides,
        logo_img,
        inpaint_watermark=inpaint_watermark,
        x_pad=55,
        y_pad=995,
        logo_pos=(915, 915),
        stamp_size=110,
        font_size=28,
    )

    align = spec.get("align", "left")
    x_start = 540 if align == "right" else 55
    max_w = 480 if align == "right" else 490
    y_pos = 110

    text_luma = sample_region_luminance(crop_sq, (x_start, y_pos, x_start + max_w, y_pos + 280))
    is_dark_bg = text_luma < 128
    primary_text_col = WHITE if is_dark_bg else DARK_OBSIDIAN
    sub_text_col = GRAY_SUB_LIGHT if is_dark_bg else GRAY_SUB_DARK

    sq_tag_size = 18
    sq_h_size = 34
    sq_s_size = 20

    f_tag = load_font(sq_tag_size, bold=True)
    f_head = load_font(sq_h_size, bold=True)
    f_sub = load_font(sq_s_size, bold=False)

    line_h = int(sq_h_size * 1.28)
    sub_line_h = int(sq_s_size * 1.40)

    tag_str = f"|  {spec['tag']}"
    draw.text((x_start, y_pos), tag_str, font=f_tag, fill=GOLD)
    y_pos += 32

    for line in spec["headline_lines"]:
        spans = parse_spans(line)
        cx = x_start
        for text_part, is_gold in spans:
            col = GOLD if is_gold else primary_text_col
            draw.text((cx, y_pos), text_part, font=f_head, fill=col)
            b = draw.textbbox((0, 0), text_part, font=f_head)
            cx += b[2] - b[0]
        y_pos += line_h

    y_pos += 14
    sub_lines = wrap_text(draw, spec.get("subheadline", ""), f_sub, max_w)
    for s_line in sub_lines:
        draw.text((x_start, y_pos), s_line, font=f_sub, fill=sub_text_col)
        y_pos += sub_line_h

    return crop_sq.convert("RGB")


def build_post(post_name: str = "Post_TEMPLATE"):
    campaign_dir = REPO_ROOT / "posts" / post_name
    if not campaign_dir.exists():
        print(f"[!] Post directory not found: {campaign_dir}")
        return

    canvases_dir = campaign_dir / "canvases"
    ig_dir = campaign_dir / "instagram"
    wa_dir = campaign_dir / "whatsapp"
    pdf_dir = campaign_dir / "pdf"

    ig_dir.mkdir(parents=True, exist_ok=True)
    wa_dir.mkdir(parents=True, exist_ok=True)
    pdf_dir.mkdir(parents=True, exist_ok=True)

    post_json_path = campaign_dir / "post.json"
    with open(post_json_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
        slides_spec = meta.get("slides", [])
        product_name = meta.get("product", post_name)
        brand_handle = meta.get("brand_handle", os.getenv("BRAND_HANDLE", "@litelab.in"))
        default_last_cue = meta.get("last_cue", "Book Lighting Consult →")
        inpaint_watermark = meta.get("inpaint_watermark", False)
        canvas_size = tuple(meta.get("canvas_size", [1080, 1350]))

    total_slides = len(slides_spec)
    logo_path = ensure_litelab_logo_stamp()
    logo_img = Image.open(logo_path).convert("RGBA") if logo_path.exists() else None

    ig_images = []
    wa_images = []

    print(f"Compositing {total_slides} LITELAB slides for {post_name} ({product_name}) at {canvas_size}...")
    for spec in slides_spec:
        idx = spec["index"]
        cpath = canvases_dir / spec.get("canvas_name", f"slide_{idx:02d}.jpg")

        if not cpath.exists():
            print(f"  [!] Canvas not found for slide {idx}: {cpath.name}. Skipping...")
            continue

        # 1. Vertical 4:5 Slide
        img_ig = composite_vertical(
            cpath,
            spec,
            logo_img,
            brand_handle=brand_handle,
            total_slides=total_slides,
            default_last_cue=default_last_cue,
            inpaint_watermark=inpaint_watermark,
            target_size=canvas_size,
        )
        out_ig = ig_dir / f"{product_name}_IG_{idx:02d}.png"
        img_ig.save(out_ig, quality=95)
        ig_images.append(img_ig)

        # 2. Square 1:1 Catalog Slide
        img_wa = composite_square(
            cpath,
            spec,
            logo_img,
            brand_handle=brand_handle,
            total_slides=total_slides,
            default_last_cue=default_last_cue,
            inpaint_watermark=inpaint_watermark,
        )
        out_wa = wa_dir / f"{product_name}_WA_{idx:02d}.png"
        img_wa.save(out_wa, quality=95)
        wa_images.append(img_wa)

        print(f"  ✓ Slide {idx:02d} [{spec.get('align', 'left').upper()}]: {out_ig.name} & {out_wa.name}")

    # Generate LinkedIn Carousel PDF
    if ig_images:
        pdf_path = pdf_dir / f"{product_name}_LinkedIn_Carousel.pdf"
        first, rest = ig_images[0], ig_images[1:]
        first.save(pdf_path, "PDF", resolution=150.0, save_all=True, append_images=rest)
        print(f"\n[✓] LinkedIn Carousel PDF generated: {pdf_path} ({len(ig_images)} pages)")

    # Generate Overview Contact Sheets inside post folder
    if ig_images:
        cols = min(4, len(ig_images))
        rows = (len(ig_images) + cols - 1) // cols
        w, h = ig_images[0].size
        thumb_w, thumb_h = w // 4, h // 4
        sheet_ig = Image.new("RGB", (thumb_w * cols + 30 * (cols + 1), thumb_h * rows + 30 * (rows + 1)), (15, 17, 20))
        for i, im in enumerate(ig_images):
            c, r = i % cols, i // cols
            thumb = im.resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
            sheet_ig.paste(thumb, (30 + c * (thumb_w + 30), 30 + r * (thumb_h + 30)))
        sheet_ig_path = campaign_dir / f"{product_name}_IG_overview.jpg"
        sheet_ig.save(sheet_ig_path, quality=90)
        print(f"[✓] Instagram Overview saved: {sheet_ig_path}")

    # Build Interactive HTML Presentation Deck automatically
    try:
        from engine.deck_builder import build_deck
        build_deck(post_name)
    except Exception as exc:
        print(f"[!] Note: Deck build skipped: {exc}")

    print(f"\n[✓] All LITELAB assets generated and packaged inside {campaign_dir}!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LITELAB Editorial Slide Compositor")
    parser.add_argument("--post", type=str, default="Post_TEMPLATE")
    args = parser.parse_args()
    ensure_litelab_logo_stamp()
    build_post(args.post)
