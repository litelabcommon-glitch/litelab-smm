---
name: litelab-smm-pipeline
description: End-to-end LITELAB Social Media Management skill integrating Higgsfield AI visual/video generation, LITELAB Portfolio & Lighting Thesaurus ingestion, deterministic Pillow editorial compositing (Obsidian #0F1114 & Architectural Gold #D4AF37), and Zoho Social multi-channel scheduling.
---

# LITELAB Social Media Management & Visual Engine Skill

Use this skill whenever the user asks to create, design, generate, composite, or schedule social media posts, carousels, reels, or content calendars for **LITELAB** (`@litelab.in` · `litelab.in`).

---

## 1. Visual Generation: Higgsfield AI + LITELAB Portfolio Archive

### A. Higgsfield AI Generation (`higgsfield` CLI / MCP)
- **Editorial & Architectural Carousel Canvases (4:5)**:
  - Model: `gpt_image_2_5`
  - Prompt conditioning (`engine/brand_engine.py`):
    ```powershell
    python -m engine.brand_engine --pillar thesaurus --scene "Double-height travertine living room at dusk" --lighting "2700K concealed perimeter cove + 15-degree narrow beam grazing"
    ```
  - Always enforce **zero text inside raw renders** and reserve **40% negative space** in the upper-left or upper-right third for typography.
- **Architectural Lighting Video Reels (9:16)**:
  - Model: `seedance_2_5` (Day-to-night lighting transitions, luminaire reveal sequences, architectural walkthroughs).
- **Luminaire & Hardware Studio Shots**:
  - Use `higgsfield-product-photoshoot` (`gpt_image_2`) or `marketing_studio` for precision fixture showcases.

### B. LITELAB Portfolio & Thesaurus Archive Ingestion
- LITELAB's 252 executed projects and Thesaurus assets live locally at:
  - `D:\hussain\thesaurusxportfolio\LITELAB_Portfolio_Extract\images\`
  - `D:\hussain\thesaurusxportfolio\Thesaurus_Extract\`
- Ingest any project folder into a post campaign with:
  ```powershell
  python -m engine.ingest "D:/hussain/thesaurusxportfolio/LITELAB_Portfolio_Extract/images/01_Azure-The-Oceanic_Chennai" --post Post_01_Azure_Oceanic
  ```

---

## 2. Deterministic Editorial Compositing (`engine/compositor.py`)

Run the compositor to generate all multi-platform deliverables in one pass:
```powershell
python -m engine.compositor --post Post_01_Azure_Oceanic
```
- **Brand Tokens**:
  - Architectural Gold: `#D4AF37` (`RGB(212, 175, 55)`) — applied to `|  TAG` kickers, `[bracketed]` headline words, top-right swipe cues, and slide index numbers.
  - Adaptive Luminance Contrast: Automatically switches primary headline text between **Alabaster White (`#FFFFFF`)** on dark architectural scenes and **Obsidian Noir (`#0F1114`)** on light gallery scenes.
  - Watermark Stamp: Stamps `assets/branding/brand_logo_round.png` (`LITELAB LIGHTING STUDIO`) at the bottom-right corner.
- **Outputs Generated**:
  - `instagram/<Product>_IG_01..08.png` (`1080×1350` 4:5 vertical)
  - `whatsapp/<Product>_WA_01..08.png` (`1080×1080` 1:1 square)
  - `pdf/<Product>_LinkedIn_Carousel.pdf` (Multi-page LinkedIn Document Carousel)
  - `deck/index.html` (Interactive HTML presentation deck)

---

## 3. Zoho Social Scheduling & Publishing (`src/publishers/zoho_social.py`)

Run the orchestrator to schedule or publish via **Zoho Social** (and direct channels):
```powershell
# Generate Zoho Social Bulk Schedule CSV (posts/<Post>/zoho_social_schedule.csv & posts/zoho_social_master_queue.csv):
python -m src.main --post Post_01_Azure_Oceanic --dry-run

# Live API publish/schedule to Zoho Social (social.zoho.in):
python -m src.main --post Post_01_Azure_Oceanic --platform zohosocial
```
- Automatically reuses LITELAB's Zoho India (`in`) OAuth Client ID and Client Secret from `~/.zoho-hr-mcp/credentials.json` or `.env`.
