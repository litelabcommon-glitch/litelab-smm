---
name: higgsfield-hand-sketch
description: Generate LITELAB hand-drawn designer-notebook imagery with Higgsfield - loose fineliner stick-figure sketches on transparent ground for technical diagrams, and white paint-pen markup drawn over existing renders to identify light sources, beam paths and sightlines. Use when asked for hand-drawn / hand-sketched / stick-man illustrations, annotated concept renders, pen studies, lighting sketches, or when a layout needs illustrations that read as the designer's own working sketches rather than polished vector infographics.
when_to_use: The user wants hand-drawn sketch imagery (fineliner linework, stick figures, hand-marked light rays over a render) generated through Higgsfield.
argument-hint: <what to sketch, or <plate.png> to mark up>
---

# Higgsfield hand-drawn sketch

Produces two kinds of image in one visual language (loose black fineliner, stick figures, hand-drawn leader lines, terracotta + ochre hand accents):

1. **Sketch** — a pure technical diagram on transparent ground (sections, geometry, system chains).
2. **Markup** — hand annotations drawn *on top of* an existing photoreal render (ringed fixtures, dashed beam paths, circled numerals, stick-figure sightlines).

Both run on GPT Image 2.5 through the `higgsfield` CLI. Everything else (labels, dimension text, spec data, captions) stays in the layout as real type — never baked into the image.

## Why this style

Code-drawn SVG diagrams and rectangular callout boxes read as "nothing in it" — they don't show where light comes from or where it lands. The fix is a designer's own pen study: every source gets a hand ring, every beam gets a dashed path with an arrowhead ending where the light lands, every "is it visible?" question gets a stick figure with a dashed sightline.

## Step 0 — Bootstrap

1. `higgsfield account status` must succeed. If not authenticated, ask the user to run `higgsfield auth login`.
2. A private Pro workspace must be selected or calls fail with `workspace_membership_required`:
   `higgsfield workspace set <workspace_id>` (list with `higgsfield workspace list`).
3. Use the installed binary on `$PATH`. Do **not** use `npx --yes @higgsfield/cli` (fails to resolve).
4. Budget: GPT Image 2.5 is ~2.75 credits at 1k/high, more at 2k. Check with `higgsfield generate cost gpt_image_2_5 ...` before a batch.

## Step 1 — Choose the mode

| Need | Mode | Script |
|---|---|---|
| Explains a mechanism (section, geometry, signal chain) with no photo behind it | Sketch | `scripts/sketch.sh` |
| An existing render must show which fitting throws which light | Markup | `scripts/markup.sh` |
| Words, numbers, spec tables | Neither — write them in HTML | — |

## Step 2 — Fix the frame geometry before generating

This is the most common failure. **The generated aspect ratio must match the box the image is placed into.** `object-fit: cover` crops hard: a 16:9 render inside a portrait A4 page shows only the centre ~40% of its width, so annotations drawn against the full frame fall off the page.

- Full-bleed portrait page → generate `3:4`.
- Landscape plate frame (e.g. 84mm tall in a 112.5mm column) → generate `4:3`.
- Wide detail band across a column → generate `16:9` or `21:9`.
- Markup mode: tell the model to reframe, e.g. `Reframe this exact <scene> into a 4:3 view keeping <list of must-stay-visible elements>` — otherwise it crops the very fixtures being numbered.

Measure the CSS box first, then pass `--aspect`. Details and the crop math: `references/layout-rules.md`.

## Step 3 — Write the brief

Append only the content; the style contract is already in the script. For sketch mode write **one continuous descriptive sentence group**, no lists, naming objects by shape and light by behaviour:

- what is drawn and from which viewpoint (`cross-section study of a cantilevered stone stair tread seen from the side`)
- the hidden source as a mark (`a tiny concealed light shown as a small dark dot with a tiny ink starburst`)
- the beam as a path (`dashed terracotta rays fan steeply down and forward, grazing the vertical riser and pooling as a hatch-shaded glow on the tread below`)
- one arrow for direction, one double-headed ink arrow for the dimension
- a stick figure + dashed sightline wherever visibility/concealment is the point
- for markup: number each fixture (`Number 01: ... ring the fitting and draw ...`) and end each ray where the light lands

Never ask the model to write words, labels or dimension text. Handwritten circled numerals are the one exception, and only in markup mode.

## Step 4 — Generate

```bash
scripts/sketch.sh -o ./assets/hf_20_tread_sketch.png -a 21:9 -b "Cross-section study of ..."
scripts/markup.sh -s ./assets/hf_01_facade_hero.png -o ./assets/hf_21_facade_marked.jpg -a 4:3 -b "Annotate four sources. Number 01: ..."
```

Add `-d` to print the exact CLI command without spending credits. `-g light` switches markup from white paint-pen to black fineliner (use it for bright renders). `-r none` drops the style reference.

The style reference (`assets/style-reference.png`, extracted from the LITELAB 7 Eleven sheets) is passed as the last reference and keeps the linework on theme; the plate is always reference #1 so the model preserves the render.

Jobs fail transiently with `request failed (no response received)`, and a benign sketch can be refused with terminal status `nsfw` — both are false signals here. The scripts retry 4 times and test the captured output for `https://` — do not test a pipeline's exit status (`| tail` always succeeds). If `nsfw` survives retries, reword the brief (drop words like `grazing`, `nosing`, `body` and describe the shapes instead).

## Step 5 — Post-process

- Sketches: `sketch.sh` autocrops the alpha bbox; a mostly-empty 21:9 canvas otherwise shrinks the drawing on the page.
- Photographic markups: convert PNG → JPEG (quality 92, subsampling 0, ~1600px wide) before printing. Four 2k PNGs can triple a book's PDF size.
- Place sketches with `object-fit: contain` in a fixed-height box; place markups with the aspect you generated.
- Do not put a dark gradient scrim over annotated areas — it erases the lower pen marks.

## Step 6 — Verify before delivery

Check every page at print scale, not just the source HTML: broken images, per-page vertical overflow, and whether the annotations are actually inside the frame. A headless-Chrome print plus a contact-sheet review catches crop and overflow defects that reading the HTML cannot. Workflow: `references/layout-rules.md`.

## Resources

- `scripts/sketch.sh` — transparent-background diagram sketch (style contract + retry + download + autocrop).
- `scripts/markup.sh` — pen markup over a render (plate as reference #1, style ref #2, 2k).
- `assets/style-reference.png` — the fineliner/stick-figure linework reference.
- `references/prompt-blocks.md` — the verbatim STYLE and ASTYLE contracts and eight worked briefs from a shipped book.
- `references/layout-rules.md` — crop math, frame recipes, print/PDF verification.
