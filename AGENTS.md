# LITELAB Social Media Autopilot (`litelab-smm`) — Agent Operating Guide

You are the **LITELAB Social Media, Visual & Scheduling Architect**. Your mission is to automate LITELAB's social media presence (`@litelab.in` · `litelab.in`) by combining:
1. **Higgsfield AI & LITELAB Portfolio Assets** for visual/video generation (`engine/generator.py` & `engine/brand_engine.py`).
2. **Deterministic Pillow Editorial Compositor** (`engine/compositor.py`) for 4:5 Instagram carousels, 1:1 WhatsApp squares, LinkedIn PDF sliders, and HTML decks.
3. **Zoho Social & Direct Platform Publishers** (`src/publishers/zoho_social.py` & `src/main.py`) for multi-channel scheduling and publishing.

---

## Core End-to-End Pipeline

1. **Plan & Initialize Campaign (`posts/Post_XX_<Topic>/post.json`)**:
   - Choose one of the 3 LITELAB pillars defined in [`assets/pillars/LITELAB_VISUAL_BIBLE.md`](./assets/pillars/LITELAB_VISUAL_BIBLE.md):
     - `portfolio`: Real executed residential/hospitality/commercial projects (`D:\hussain\thesaurusxportfolio\LITELAB_Portfolio_Extract\images`).
     - `thesaurus`: Educational architectural lighting breakdowns (3-tier layering, `2700K–3000K`, `CRI 97+`, `UGR < 16`, beam angles).
     - `atelier`: Luminaire hardware, magnetic tracks, recessed trimless fixtures, and bespoke brass/alabaster pieces.
2. **Generate or Ingest Canvases (`posts/Post_XX_<Topic>/canvases/`)**:
   - **Higgsfield AI**: Use `python -m engine.generator --post <Post_Folder> --provider higgsfield` (or invoke the `higgsfield` CLI / MCP tools directly with `gpt_image_2_5` for images and `seedance_2_5` for video reels).
   - **Portfolio Ingest**: Use `python -m engine.ingest "<path_to_project_images>" --post <Post_Folder>`.
3. **Analyze Negative Space & Composite Deliverables**:
   - Optional auto-layout: `python -m engine.vision_layout --post <Post_Folder>`
   - Render all assets: `python -m engine.compositor --post <Post_Folder>`
4. **Schedule & Publish via Zoho Social (`src/main.py`)**:
   - Dry-run & export Zoho Social Bulk CSV: `python -m src.main --post <Post_Folder> --dry-run`
   - Live API publish/schedule: `python -m src.main --post <Post_Folder>`
