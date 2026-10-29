# LITELAB — Social Media Management, Higgsfield Visual Engine & Zoho Social Suite ✨

> **Autonomous Architectural Lighting Content Engine, Editorial Compositor & Zoho Social Scheduler**  
> **Brand:** **LITELAB Lighting Studio** (`@litelab.in` · [litelab.in](https://litelab.in))  
> **Content Pillars:** `portfolio` (Architectural Monograph) · `thesaurus` (The Lighting Thesaurus) · `atelier` (Luminaire & Product Atelier)

---

## 🏛️ Executive Summary

**LITELAB SMM (`litelab-smm`)** is the unified creative visual engine, editorial carousel compositor, and multi-platform scheduling hub built exclusively for **LITELAB**. It combines **Higgsfield AI** automated visual/video generation and LITELAB's **252-project portfolio archive** with deterministic Pillow typography compositing and **Zoho Social** multi-channel scheduling:

1. **Higgsfield AI & Portfolio Visual Engine (`engine/generator.py` & `engine/brand_engine.py`)**:
   - **Higgsfield AI Primary Integration (`--provider higgsfield`)**: Generates photorealistic architectural lighting scenes via `gpt_image_2_5`, cinematic day-to-night lighting reels via `seedance_2_5`, and luminaire studio shots via `product_photoshoot`.
   - **LITELAB Portfolio Ingestor (`engine/ingest.py`)**: Directly ingests photography from LITELAB's 252 executed projects (`D:\hussain\thesaurusxportfolio\LITELAB_Portfolio_Extract\images`) and Thesaurus lighting guides.
   - **Conditioned Prompt & Anti-Slop Guardrails**: Enforces realistic Kelvin/CRI lighting physics (`2700K–3000K`, `CRI 97+`, `UGR < 16`), 40% upper negative space reservation, and bans AI slop tropes.

2. **Adaptive Architectural Editorial Compositor (`engine/compositor.py`)**:
   - **Smart Luminance Contrast**: Automatically measures background luminance in the negative space region and adapts headline typography between **Alabaster White (`#FFFFFF`)** on nocturnal lighting photography and **Obsidian Noir (`#0F1114`)** on light gallery diagrams.
   - **Architectural Gold Accents (`#D4AF37`)**: Renders vertical kickers (`|  LIGHTING THESAURUS`), `[bracketed]` headline emphasis, pagination numbers, and geometric vector arrows in LITELAB Gold.
   - **Official LITELAB Stamp**: Automatically generates and stamps the concentric circular `LITELAB LIGHTING STUDIO` emblem (`assets/branding/brand_logo_round.png`).
   - **One-Command Multi-Format Deliverables**: Outputs `1080×1350` Instagram 4:5 PNGs, `1080×1080` WhatsApp 1:1 squares, multi-page LinkedIn Document Carousel PDFs, and interactive HTML presentation decks (`deck/index.html`).

3. **Zoho Social Scheduler & Multi-Platform Autopilot (`src/publishers/zoho_social.py` & `src/main.py`)**:
   - **Zoho Social REST API (`social.zoho.in`)**: Publishes immediately or schedules posts across Instagram, LinkedIn, Facebook, X/Twitter, YouTube, and Google Business Profile using Zoho OAuth2 (auto-detecting LITELAB's Zoho India Client ID/Secret from `~/.zoho-hr-mcp/credentials.json` or `.env`).
   - **Zoho Social Bulk Scheduler CSV Generator**: Every run automatically generates `posts/<Post_ID>/zoho_social_schedule.csv` and updates the master queue at `posts/zoho_social_master_queue.csv` for 1-click batch scheduling in Zoho Social.
   - **Direct Platform Connectors**: Also includes direct publishers for LinkedIn (`feedshare-document` native PDF carousels), Instagram Graph API, YouTube Shorts, WhatsApp Business Catalog (`INR`), X/Twitter, and Reddit.

---

## 📂 Clean Repository Architecture

```text
litelab-smm/
├── .antigravity/
│   └── rules.md                              # Workspace rules for LITELAB SMM
├── .agents/
│   └── skills/
│       ├── litelab-smm-pipeline/
│       │   └── SKILL.md                      # Antigravity skill for Higgsfield + Zoho Social workflow
│       └── higgsfield-hand-sketch/
│           ├── SKILL.md                      # Hand-drawn fineliner / stick-figure sketch + pen-markup skill
│           ├── scripts/                      # sketch.sh (transparent diagrams) · markup.sh (markup over renders)
│           ├── references/                   # Prompt contracts, crop math, print verification
│           └── assets/style-reference.png    # 7 Eleven linework reference
├── .github/
│   └── workflows/
│       └── social_media_post.yml             # Daily 6:30 PM IST GitHub Actions scheduler
├── assets/
│   ├── branding/
│   │   └── brand_logo_round.png              # Concentric Obsidian & Gold LITELAB stamp
│   └── pillars/
│       └── LITELAB_VISUAL_BIBLE.md           # Content pillars, color tokens & lighting rules
├── engine/
│   ├── brand_engine.py                       # Higgsfield prompt conditioning & anti-slop validator
│   ├── compositor.py                         # Adaptive Obsidian/White + Gold #D4AF37 compositor
│   ├── deck_builder.py                       # Interactive HTML presentation deck builder
│   ├── generator.py                          # Higgsfield AI, Pollinations & Hugging Face generator
│   ├── ingest.py                             # Portfolio & Higgsfield ZIP/folder ingestion tool
│   └── vision_layout.py                      # Automated negative-space bounding box analyzer
├── posts/
│   └── Post_TEMPLATE/                        # Clean LITELAB starter blueprint
│       ├── canvases/                         # Raw 4:5 architectural images go here
│       ├── copy.md                           # Slide-by-slide editorial copy deck
│       ├── post.json                         # Campaign manifest, Zoho schedule & slide specs
│       └── README.md                         # 4-step quickstart guide
├── src/
│   ├── ai_enhancer.py                        # Gemini caption enhancer with LITELAB tone profiles
│   ├── config.py                             # Centralized environment & Zoho Social config
│   ├── data_source.py                        # Posts directory, Google Sheets & JSON manifest loader
│   ├── main.py                               # Main publishing & Zoho Social scheduling orchestrator
│   ├── notifier.py                           # Discord & Slack webhook alerts
│   └── publishers/
│       ├── zoho_social.py                    # Zoho Social API + Bulk Schedule CSV publisher
│       ├── linkedin.py                       # Native LinkedIn PDF Carousel & image publisher
│       ├── instagram.py                      # Instagram Graph API & Reels publisher
│       ├── whatsapp_catalog.py               # WhatsApp Business Catalog sync (INR)
│       ├── youtube.py                        # YouTube Shorts resumable uploader
│       ├── twitter.py                        # X / Twitter API v2 publisher
│       ├── reddit.py                         # Reddit publisher
│       └── buffer_cli.py                     # Buffer CLI publisher
├── AGENTS.md                                 # Agent operating instructions
├── .env.example                              # Clean LITELAB environment template
├── requirements.txt                          # Python dependencies
└── README.md                                 # Documentation
```

---

## ⚡ Quick Start Commands

```powershell
# 1. Generate conditioned Higgsfield prompt for a lighting concept:
python -m engine.brand_engine --pillar thesaurus --scene "Luxury villa courtyard in Chennai"

# 2. Generate canvases via Higgsfield AI (or ingest from LITELAB portfolio):
python -m engine.generator --post Post_TEMPLATE --provider higgsfield
# OR ingest real project photos:
python -m engine.ingest "D:/hussain/thesaurusxportfolio/LITELAB_Portfolio_Extract/images/01_Azure-The-Oceanic_Chennai" --post Post_TEMPLATE

# 3. Composite Instagram 4:5, WhatsApp 1:1, LinkedIn PDF & HTML Deck:
python -m engine.compositor --post Post_TEMPLATE

# 4. Schedule via Zoho Social (Dry-Run exports zoho_social_schedule.csv):
python -m src.main --post Post_TEMPLATE --dry-run
```
