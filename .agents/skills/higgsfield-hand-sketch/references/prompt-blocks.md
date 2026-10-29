# Prompt contracts and worked briefs

Both blocks are baked into the scripts. They are recorded here so a brief can be written by hand if the script is not used, and so the contract survives edits.

## STYLE — pure sketch on transparent ground

Verbatim prefix used by `scripts/sketch.sh`:

```text
Loose hand-drawn lighting-designer notebook study drawn with a fine black fineliner pen on plain paper. Deliberately imperfect wobbly linework, uneven double-stroke outlines, simple stick figures with round heads and thin limbs, hand-drawn slightly curved leader lines and open arrowheads, sparse diagonal cross-hatching for shading, dotted and dashed construction lines. Only two accents, used sparingly: muted terracotta red-brown and warm ochre, applied as light hand-coloured marker strokes over the ink. Absolutely no words, no letters, no numbers, no dimension text, no labels, no title block, no legend text. No gradients, no digital polish, no CAD precision, no 3D render. Flat transparent background, nothing but the sketch.
```

Non-negotiable clauses, and why:

- `deliberately imperfect wobbly linework` + `uneven double-stroke outlines` — without them the model returns clean vector art.
- `only two accents ... terracotta ... ochre` — more colour turns it into an infographic.
- the whole `Absolutely no words ...` sentence — text baked at 1k is illegible and cannot be edited; all labels live in HTML.
- `no CAD precision, no 3D render` — otherwise the sketch reads as a technical drawing, which the client rejects.
- `flat transparent background` with `--background transparent` — lets the sketch sit on tinted paper without a white box.

## ASTYLE — pen markup over a render

Verbatim prefix used by `scripts/markup.sh` (`dark` ground; `light` swaps the ink wording to black fineliner and drops the ochre-first ordering):

```text
Over this architectural night render, draw hand-drawn lighting-design annotations directly on top of the image exactly like a designer's pen study marked up on a print: fine white paint-pen linework with a slightly wobbly imperfect hand-drawn quality, plus a few dashed rays in warm ochre and muted terracotta. The render itself must stay photorealistic and unchanged, only the pen annotations sit on top of it. For every light source draw a small hand-drawn ring around the fitting, a short leader line to a small handwritten circled number, and clear dashed rays or a beam cone starting at that fitting that shows the exact direction the light travels and where it lands, ending in a hand-drawn arrowhead. Add one simple stick figure with a dashed sightline, and a few short curved arrows showing light sweeping across a surface. Handwritten numerals only, no words, no sentences, no dimension text, no paragraphs. Annotations crisp, generous and legible, never cluttered. Keep every annotation well inside the frame.
```

Key clauses:

- `the render itself must stay photorealistic and unchanged, only the pen annotations sit on top` — without it the model repaints the whole image in sketch style.
- `white paint-pen` — the only ink that reads on a night render.
- `handwritten circled numerals only` — the one allowed exception to the no-text rule, because numbers must tie back to the HTML key beneath the plate.
- `keep every annotation well inside the frame` — marks near the edge get cut by the print crop.

## Brief-writing rules

1. One flowing sentence group per figure. No bullets, no "1) 2) 3)" inside a sketch brief.
2. Name objects by shape and material, not by product (`a thick horizontal stone slab with a softly rounded nosing`).
3. Describe light as behaviour: where it starts, the direction it travels, what it rakes, where it pools.
4. Make concealment explicit: a stick figure head/foot/body plus `a long dashed sightline that just touches ... and stops short of ...`.
5. Use ink for form, terracotta for the primary beam, ochre for a secondary wash or bounce. Cross-out marks on a small cluster of arriving arrows = "this light is absorbed here".
6. Max 3–4 numbered sources per plate. Beyond that the markup turns to clutter and the rings collide.

## Worked sketch briefs (append after STYLE)

**Tread rebate, 21:9** — `Cross-section study of a cantilevered stone stair tread seen from the side: a thick horizontal stone slab with a softly rounded nosing on its right end, and a narrow rectangular rebate channel recessed underneath the nosing holding a tiny concealed light shown as a small dark dot with a tiny ink starburst. From that dot dashed terracotta rays fan steeply down and forward, grazing the vertical stone riser and pooling as a hatch-shaded glow on the tread below; one curved hand-drawn arrow shows the beam sweeping downward along the stone. Beneath the main tread a second lower tread and a stick figure foot caught mid-step. A short double-headed ink dimension arrow measures the small setback between the nosing edge and the hidden channel. At the left a small stick figure head with a long horizontal dashed sightline that just touches the nosing and stops short of the hidden dot, showing the eye cannot see the source.`

**Cove geometry, 21:9** — `Interior ceiling cross-section study: a heavy horizontal structural slab line across the top, and below it a dropped plaster ceiling plane with a vertical drop on the right forming a shallow recessed cove. Inside the cove a tiny continuous strip of light shown as a dotted ink line with small starbursts. Broad dashed terracotta rays travel upward and sideways from the strip, wash across the underside of the slab and skimming down the wall as a soft hatch-shaded glow, with two long hand-drawn arrows curving along the washed path. A knife-edge lip at the cove opening drawn as a crisp pointed ink edge. At the lower left a stick figure standing with a long dashed sightline from its eye just grazing the knife-edge lip toward the slab, showing the lamp stays hidden. A double-headed vertical ink arrow for the cove drop and a double-headed horizontal ink arrow for the setback.`

**Acoustic slat channel, 21:9** — `Wall cross-section study through an acoustic timber screen: a wide hatch-shaded felt backing band along the top, and below it a row of vertical timber slats drawn as narrow double-line uprights with visible end grain hatching, evenly spaced with gaps. Between two slats a deep black shadow-gap channel recessed behind the slat faces, containing a thin horizontal lens line and a tiny LED dot with small ink starbursts. Short dashed terracotta rays escape downward from the lens through the slot between the slats, forming a narrow light wedge on the floor line below, where a faint hatch pool and a small stick figure foot appear. From the upper right a cluster of straight ochre arrows arrives from off-page toward the black channel and stops at its dark inner wall, each drawn with a small hand-drawn cross-out mark, showing stray projector light absorbed rather than reflected. A curved leader line points at the recessed lens.`

**Control chain, 21:9** — `Hand-drawn system chain study, four stations arranged left to right on one baseline, connected by three bold hand-drawn ink arrows with open arrowheads, drawn on transparent ground. Station one: a small square wall keypad plate with a round button, and a stick figure arm reaching to press it. Station two: a gateway drawn as a small open box with a wobbly outline and two short antenna squiggles, plus a tiny clock dial drawn beside it, connected onward by a long dashed ink arrow. Station three: a driver manifold drawn as a larger rectangular box with diagonal hatch shading on one face and four short cable stubs leaving its right side. Station four: three tiny ceiling downlights drawn as shallow cones with dashed ochre beams falling onto a floor line, plus one small wall washer cone. Every link is hand-drawn, arrow lengths slightly uneven, the whole chain reading as a pen sketch of a signal path from switch to light.`

## Worked markup briefs (append after ASTYLE)

Always start with a reframe sentence naming what must stay visible, then `Number NN:` per fixture.

**Facade, 4:3** — `Reframe this exact arrival-threshold scene into a 4:3 view so the full rough stone wall, the stepping-stone path across the reflecting pool, the timber soffit portal and the frangipani tree are all visible. Annotate four sources. Number 01: the in-grade grazer at the base of the rough stone wall on the right, ring the fitting and draw dashed terracotta rays raking steeply upward across the stone face so each joint throws a long shadow, with an upward arrow showing the grazing direction. Number 02: the concealed linear light hidden behind each stepping-stone nosing, ring one fitting and draw short dashed ochre wedges falling down onto the tread face and the water below, with an arrow showing the beam raking the tread. Number 03: the pinhole downlights in the timber soffit of the entry portal, ring them and draw narrow dashed cones dropping onto the corridor floor. Number 04: the spike uplight at the base of the frangipani tree on the left, ring it and draw a wide dashed upward cone into the canopy with an arrow, plus a cross-hatched shadow pool cast on the ground. Add a small stick figure walking on the stepping stones with one long horizontal dashed sightline passing just above the step lights and below the soffit lenses, showing no lamp sits at eye level.`

**Living stair, 3:4** — `Reframe this exact double-height living room into a portrait 3:4 view that keeps the cantilevered stone staircase with its glowing treads on the right, the black ceiling track at the top and the warm perimeter cove visible. Annotate three sources. Number 05: the trimless magnetic track in the ceiling, ring the small downlight modules in the black track and draw narrow dashed cones dropping onto the sofa and the stone coffee table below, with an arrow showing the tight beam angle. Number 06: the perimeter cove, ring the concealed cove line and draw broad dashed ochre rays washing upward and outward across the ceiling plane, with two long curved arrows showing the wash lifting the ceiling higher. Number 07: the concealed linear behind each cantilevered stair tread, ring one fitting at the back of a tread and draw dashed wedges skimming down the stone riser and pooling on the floor, with an arrow showing light spilling step by step down the flight. Add a small stick figure standing at the foot of the stairs with a dashed sightline grazing the tread edge and stopping before the fitting, showing the source stays hidden from the room.`

**Courtyard, 3:4** — `Reframe this exact courtyard with the sunken plunge pool into a portrait 3:4 view keeping the frangipani tree, the floating timber bench and the shadowed stone wall visible. Annotate three sources. Number 08: the foliage projector at the base of the tree, ring the fitting, draw a dashed upward cone into the canopy, then continue dashed rays past the leaves to the stone wall where the leaf shadow is thrown, with an arrow showing the tree-to-wall projection and a small cross-hatched shadow drawn over the cast leaf shadow. Number 09: the sub-aquatic cove behind the floating bench, ring the fitting and draw dashed ochre rays washing down the wall and across the water surface, with an arrow showing the wash and a few short wavy hatch marks where the light ripples on the water. Number 10: the basalt floor slot at the edge of the planting, ring the slot and draw a thin dashed blade of light skimming horizontally along the stone floor with an arrow showing how low and shallow it sits. Add a small stick figure seated on the bench with a dashed sightline running toward the tree base and stopping above the fixtures, showing every source stays below the eye line.`

**Cinema, 4:3** — `Reframe this exact private cinema lounge into a 4:3 view keeping the black marble bar on the left, the dark acoustic slat wall, the lounge seating and the screen visible. Annotate two sources. Number 11: the stealth slat channel between the dark acoustic battens, ring the thin glowing slot and draw a narrow dashed wedge of light skimming down the wall face with an arrow showing the grazing direction, plus a small hand-drawn cross-out mark where projector light would otherwise bounce off the lens. Number 12: the concealed rebate under the stone edge of the bar, ring the strip and draw dashed ochre rays washing down the fluted bar front and pooling on the floor, with an arrow showing the wash direction. Add a small stick figure seated in one lounge chair with a dashed sightline running from its eye toward the screen and stopping above the bar line, showing both sources sit below the sightline while the screen stays readable.`

## Pair each image with an HTML key

The image carries the visual argument; three short columns of type beneath it carry the data that would otherwise have been baked in. Pattern used across the shipped book:

```html
<div style="height:46mm;"><img class="concept-sketch" src="...sketch.png" alt="..." /></div>
<div style="display:grid; grid-template-columns:repeat(3,1fr); gap:5mm; font-size:6.9pt;">
  <div><span>THE RINGED SOURCE</span><br/>4.8W/m · 2400K opal silicone in a 14×14 mm rebate.</div>
  <div><span>THE DASHED WEDGE</span><br/>Rays leave the nosing downward, raking the riser.</div>
  <div><span>THE SIGHTLINE</span><br/>At the 35 mm setback the walking eye passes beneath the lens.</div>
</div>
```

Name each key after what the eye sees in the drawing (`THE DASHED WEDGE`, `THE CROSS-OUT`), so the reader can match type to mark.
