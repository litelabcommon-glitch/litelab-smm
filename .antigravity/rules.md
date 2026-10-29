# LITELAB — Social Media Management, Higgsfield Visual Engine & Zoho Social Rules

## 1. DEDICATED POST FOLDERS
- Every campaign / lighting study MUST live inside its own isolated folder under `posts/` (e.g. `posts/Post_01_Azure_Oceanic/`, `posts/Post_02_Layered_Lighting/`).
- Each post folder contains:
  - `post.json` (metadata, `pillar`, `scheduled_date`, `time`, `zoho_networks`, captions, tags, slide coordinates)
  - `copy.md` (editorial copy deck and slide text)
  - `canvases/` (raw 4:5 architectural photos or Higgsfield AI renders with zero embedded text)
  - `instagram/` (`1080×1350` 4:5 vertical PNGs)
  - `whatsapp/` (`1080×1080` 1:1 square PNGs)
  - `pdf/` (high-DPI multi-page PDF carousel for LinkedIn)
  - `deck/` (interactive HTML presentation deck `index.html`)
  - `zoho_social_schedule.csv` (auto-generated Zoho Social Bulk Scheduler row)
- Never dump media or outputs loose globally.

## 2. HIGGSFIELD AI + PORTFOLIO VISUAL PIPELINE
- Primary visual & video generation uses **Higgsfield AI** (`python -m engine.generator --post <folder> --provider higgsfield` or the Antigravity `higgsfield-generate` / `higgsfield-product-photoshoot` skills):
  - **Architectural & Thesaurus Canvases**: `gpt_image_2_5` (`4:5` aspect ratio, zero embedded text, upper 40% negative space).
  - **Architectural Lighting Reels / Day-to-Night Transitions**: `seedance_2_5` (`9:16` vertical video).
  - **Luminaire & Fixture Studio Shots**: `product_photoshoot` or `marketing_studio`.
- Can also ingest directly from LITELAB's 252-project archive at `D:\hussain\thesaurusxportfolio\LITELAB_Portfolio_Extract\images` via `python -m engine.ingest <source_folder> --post <folder>`.

## 3. TYPOGRAPHY & LITELAB DESIGN SYSTEM
- **Strictly No Capsules**: No pill/capsule shapes around tags, page numbers, or swipe cues.
- **Editorial Kickers**: Use vertical architectural kickers (`|  LIGHTING THESAURUS`).
- **Bracketed Gold Highlights**: Words wrapped in `[brackets]` inside `headline_lines` automatically render in **Architectural Gold (`#D4AF37`)**.
- **Smart Luminance Contrast**: `engine/compositor.py` automatically measures background luminance in the negative space region and switches headline text between **Alabaster White (`#FFFFFF`)** on nocturnal lighting scenes and **Obsidian Noir (`#0F1114`)** on light studio/gallery canvases.

## 4. ZOHO SOCIAL SCHEDULING & MULTI-PLATFORM AUTOPILOT
- Publishing and scheduling is driven by `python -m src.main`.
- **Zoho Social Integration (`src/publishers/zoho_social.py`)**:
  - Connects to Zoho Social India (`social.zoho.in` / `accounts.zoho.in`, reusing LITELAB's Zoho OAuth Client ID & Secret from `~/.zoho-hr-mcp/credentials.json` or `.env`).
  - Automatically exports `posts/<Post_ID>/zoho_social_schedule.csv` and updates `posts/zoho_social_master_queue.csv` on every run (including `--dry-run`) so batches can also be uploaded in 1 click to the Zoho Social Bulk Scheduler.
