# Frame geometry, placement and verification

## The crop rule

`object-fit: cover` scales an image to fill the frame and crops the rest. When the image is wider than the frame:

```
visible fraction of the source width = frameAspect / imageAspect
```

Measured on a 297×210mm landscape sheet split into two 148.5×210mm logical pages (`.page-night` padding `16mm 18mm 14mm 18mm` → content width 112.5mm):

| Source aspect | Displayed in | Frame aspect | Width actually shown |
|---|---|---|---|
| 16:9 | full-bleed portrait page 148.5×210 | 0.707 | 39.8% |
| 16:9 | 112.5×118mm gallery frame | 0.953 | 53.6% |
| 16:9 | 112.5×84mm plate frame | 1.339 | 75.3% |
| 4:3 | 112.5×84mm plate frame | 1.339 | 100% |
| 3:4 | full-bleed portrait page | 0.707 | 94.3% |

Consequence: a markup drawn against the full 16:9 frame loses its outer annotations inside a portrait page — rings and numbers land off-page and the plate looks empty, which is exactly the defect that motivated hand markup. Fix the aspect at generation time; do not fight it with `object-position`.

## Frame recipes

| Placement | Generate | Place with |
|---|---|---|
| Full-bleed portrait page (148.5×210mm) | `3:4` | `object-fit: cover`, `width/height: 100%` |
| Landscape plate in a bordered frame | match the frame, usually `4:3` for a `height:84mm` frame at 112.5mm wide | `object-fit: cover` |
| Detail band spanning a column | `16:9` or `21:9` | `object-fit: contain` inside a fixed `height:26–46mm` box |
| Transparent sketch in a text column | widest aspect the band allows, then autocrop | `object-fit: contain` |

For markup mode, add the reframe sentence so the generator supplies that aspect without cutting the fixtures being numbered.

## Sketch height budget

After autocrop, a transparent sketch fills its box differently every time. Set the image box height generously and let `contain` centre it, then re-measure:

- `26mm` for a horizontal chain with few rows (control diagram)
- `37mm` for a section plus a 3-column key
- `46mm` for a hero detail on a page with little other copy

Any page that grows past its frame prints with the bottom cut. Re-run the overflow check after every insert.

## Overlays on annotated plates

A gradient scrim for caption legibility destroys pen marks. Keep the dark stop below the annotation zone:

```css
background: linear-gradient(180deg, rgba(18,18,17,.08) 0%, rgba(18,18,17,0) 62%, rgba(18,18,17,.88) 100%);
```

62% on a 3:4 page, 64% on a taller crop. Put the legend at `bottom:25mm`, not at the very bottom, so the last ring and its numeral are not dimmed.

## File size

- Four 2k photographic PNGs can push a 32-page book PDF past 50MB. Re-encode markups to JPEG, `quality=92`, `subsampling=0`, ~1600px on the long edge → about half the size with no visible banding on ink lines.
- Do **not** PNG-quantize markups to 256 colours to save more; antialiased fineliner strokes band visibly.
- Keep sketches as PNG — transparency is required.

## Pre-print verification

Print with headless Chrome against a local HTTP server (never `file://`, which is unreliable for relative images):

```bash
".../chrome.exe" --headless=new --disable-gpu --no-sandbox --hide-scrollbars \
  --run-all-compositor-stages-before-draw --virtual-time-budget=40000 --no-pdf-header-footer \
  --print-to-pdf="D:/out/book.pdf" "http://127.0.0.1:8765/<project>/<book>.html"
```

Then check, in this order:

1. **DOM audit** against the served page via Chrome DevTools Protocol (launch Chrome with `--remote-debugging-port=9223`). Report: sheet count, images with `naturalWidth === 0`, per-page `scrollHeight - clientHeight` overflow in px, duplicate `src` values, `document.fonts.status`. Add `document.body.dataset.ready = "true"` at the end of the page script and wait for it before measuring.
2. **Contact sheet** of every printed sheet at fit-to-window scale — catches whole-page problems the DOM audit cannot (a ring sitting on a crop seam, a stick figure overlapping type).
3. **Per-page crops at print scale** for every page that changed. Judge the annotations against the printed frame, not against the source image.

Only sign off when the DOM audit is clean **and** the changed pages were looked at individually. A clean check with no visual review still ships cropped annotations; a visual review with no DOM check still ships silent overflow.

## Reuse across agents

The style contract travels in `assets/style-reference.png` plus the two prompt blocks. A different machine needs only: the `higgsfield` CLI on PATH, an authenticated session, a selected workspace, and the reference image reachable by an absolute Windows-style path (`C:/...` — the CLI is a Node binary and cannot read `/c/...`).
