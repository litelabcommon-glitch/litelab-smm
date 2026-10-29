# LITELAB — Architectural Lighting Visual & Content Bible

**Brand:** LITELAB (`@litelab.in` · [litelab.in](https://litelab.in))  
**Domain:** Architectural Lighting Design, Engineering & Bespoke Luminaires (Milano · Chennai · Pan-India)  
**Core Philosophy:** *"At LITELAB, lighting has evolved far beyond utility. It is the defining architectural medium that gives form, emotional depth, and soul to spaces. Light establishes the rhythm of living."*

---

## 1. Content Pillars & Visual Routing Matrix

All LITELAB social campaigns route through one of three core pillars:

| Pillar Key | Pillar Name | Primary Focus & Storytelling | Target Channels | Visual Engine Mode |
| :--- | :--- | :--- | :--- | :--- |
| **`portfolio`** | **Architectural Monograph** | Luxury residential villas, penthouses, hospitality, heritage & commercial projects (252+ executed projects). | Instagram Carousel, LinkedIn PDF, Zoho Social | Portfolio Photography + Higgsfield `seedance_2_5` (Day-to-Night Reels) |
| **`thesaurus`** | **The Lighting Thesaurus** | Lighting design education: 3-tier layered lighting, CRI >95, glare control (UGR <16), warm dimming (2700K–3000K), beam angles. | LinkedIn Carousel, Instagram Educational Saves, YouTube Shorts | Higgsfield `gpt_image_2_5` Architectural Diagrams & Comparisons |
| **`atelier`** | **Luminaire & Product Atelier** | Precision architectural fixtures, magnetic track systems, recessed trimless downlights, bespoke brass & alabaster luminaires. | Instagram, WhatsApp Business Catalog, Zoho Social | Higgsfield `product_photoshoot` & `marketing_studio` |

---

## 2. Brand Design Tokens & Color Hierarchy

| Token | Hex | RGB | Usage |
| :--- | :--- | :--- | :--- |
| **Architectural Gold** | `#D4AF37` | `RGB(212, 175, 55)` | Primary brand accent, vertical kickers (`\|  TAG`), `[bracketed]` headline emphasis, pagination index |
| **Obsidian Noir** | `#0F1114` | `RGB(15, 17, 20)` | Dark-mode canvas surface, primary headline text on light canvases |
| **Alabaster White** | `#FFFFFF` | `RGB(255, 255, 255)` | Primary headline text on dark nocturnal lighting canvases |
| **Warm Gallery Stone** | `#F8F7F4` | `RGB(248, 247, 244)` | Light-mode editorial background surface |
| **Architectural Slate** | `#4B5563` / `#CBD5E1` | Adaptive | Subheadline & technical specification copy (auto-contrasts on dark vs. light scenes) |

---

## 3. Strict Visual & Higgsfield Generation Rules

1. **Zero On-Canvas AI Text:** Never render typography, watermarks, or fake UI labels inside raw Higgsfield or Gemini image generations. All typography is composited deterministically via `engine/compositor.py`.
2. **Negative Space Reservation (Top 40%):** Frame architectural scenes and luminaire compositions with clean negative space in the upper-left (`x: 55..555px, y: 120..520px`) or upper-right (`x: 540..1020px, y: 120..520px`) zone (smooth plastered walls, nocturnal sky, shadow planes, or travertine stone) so editorial typography reads effortlessly.
3. **Authentic Lighting Physics:** Always specify realistic color temperatures (`2700K warm architectural glow`, `3000K museum-grade halogen warmth`), concealed light sources (`recessed trimless architectural coves`), and natural grazing across tactile materials (travertine, fluted timber, brushed brass, raw concrete).
4. **Strictly No Capsules:** Never use rounded pill/capsule badges around tags or swipe cues. Always use LITELAB's signature vertical architectural kicker (`|  PILLAR TAG`).

---

## 4. Anti-Slop Copywriting Rules

### Banned AI Vocabulary
Never use generic AI clichés:
`"delve"`, `"tapestry"`, `"game-changer"`, `"unleash"`, `"revolutionary"`, `"testament"`, `"in today's fast-paced digital landscape"`, `"transformative"`, `"seamlessly"`, `"elevate your space"`.

### Editorial Tone Guidelines
* **Architectural Authority:** Speak like a principal lighting architect. Reference real metrics where helpful (`2700K`, `CRI 97+`, `UGR < 16`, `15° narrow spot`, `wall grazing vs. wall washing`).
* **Restraint & Precision:** Keep slide headlines under 10 words per slide. Let `[bracketed gold keywords]` carry the visual punch.
