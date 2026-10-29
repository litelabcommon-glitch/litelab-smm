# Post Template — LITELAB Social Media & Visual Engine

Follow this 4-step workflow to generate, composite, and schedule any LITELAB architectural lighting campaign via **Higgsfield AI** and **Zoho Social**.

---

### Step 1: Duplicate this template folder
```powershell
Copy-Item -Recurse posts\Post_TEMPLATE posts\Post_01_YourCampaignName
```

### Step 2: Generate or Ingest Architectural Canvases
Choose any of the three methods below:

**Method A: Higgsfield AI Automated Generation (Recommended for New Visuals & Reels)**
```powershell
python -m engine.generator --post Post_01_YourCampaignName --provider higgsfield
```
- Uses `gpt_image_2_5` for editorial/architectural 4:5 canvases and `seedance_2_5` for cinematic lighting reels.

**Method B: Ingest from LITELAB's 252-Project Portfolio (`D:\hussain\thesaurusxportfolio`)**
```powershell
python -m engine.ingest "D:/hussain/thesaurusxportfolio/LITELAB_Portfolio_Extract/images/01_Azure-The-Oceanic_Chennai" --post Post_01_YourCampaignName
```

**Method C: Free Zero-Key FLUX Fallback**
```powershell
python -m engine.generator --post Post_01_YourCampaignName --provider pollinations
```

### Step 3: Run the LITELAB Editorial Compositor
```powershell
python -m engine.compositor --post Post_01_YourCampaignName
```
Automatically produces:
1. `instagram/` → Vertical 4:5 slides (`1080x1350`) with adaptive Obsidian/White contrast, Architectural Gold (`#D4AF37`) highlights, and the circular `LITELAB` stamp.
2. `whatsapp/` → Square 1:1 catalog slides (`1080x1080`).
3. `pdf/` → Multi-page LinkedIn Document Carousel PDF.
4. `deck/` → Interactive browser presentation deck (`index.html`).

### Step 4: Publish or Schedule via Zoho Social
```powershell
# Export Zoho Social Bulk Schedule CSV & test pipeline in dry-run mode:
python -m src.main --post Post_01_YourCampaignName --dry-run

# Publish / schedule live to Zoho Social & connected channels:
python -m src.main --post Post_01_YourCampaignName
```
