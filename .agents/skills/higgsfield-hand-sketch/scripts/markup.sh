#!/usr/bin/env bash
# Draw hand-marked lighting annotations ON TOP of an existing render (image-to-image).
# The render stays photorealistic; only paint-pen linework, rings, dashed beam paths,
# hand-circled numerals and a stick-figure sightline are added.
#
# Usage: markup.sh -s PLATE.png -o OUT.png -b "which fixtures, which rays" [-a ASPECT] [-g GROUND] [-r STYLE_REF.png] [-d]
#
# -s/--source  the render to mark up. Required. Reference #1, so the model keeps it.
# -g/--ground  dark (default, white paint-pen) or light (black fineliner).
# -a/--aspect  MUST match the frame the image is placed into. 3:4 for a portrait
#              full-bleed page, 4:3 for a landscape plate frame. See references/layout-rules.md.
# -d/--dry-run print the exact higgsfield command instead of submitting it.
set -u

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
src="" out="" brief="" aspect="4:3" ground="dark" dry=""
ref="$SKILL_DIR/assets/style-reference.png"
[ -f "$ref" ] || ref=""

while [ $# -gt 0 ]; do
  case "$1" in
    -s|--source) src="$2"; shift 2;;
    -o|--out) out="$2"; shift 2;;
    -b|--brief) brief="$2"; shift 2;;
    -a|--aspect) aspect="$2"; shift 2;;
    -g|--ground) ground="$2"; shift 2;;
    -r|--ref) ref="$2"; shift 2;;
    -d|--dry-run) dry=1; shift;;
    *) echo "unknown arg: $1" >&2; exit 2;;
  esac
done

if [ -z "$src" ] || [ ! -f "$src" ]; then
  echo "missing or unreadable -s <plate.png>" >&2
  exit 2
fi
if [ -z "$brief" ]; then
  echo 'missing -b "which fixtures, which rays"' >&2
  exit 2
fi

command -v higgsfield >/dev/null 2>&1 || export PATH="$PATH:/c/Users/LITELAB/AppData/Local/Programs/nodejs"
if ! command -v higgsfield >/dev/null 2>&1; then
  echo "higgsfield CLI not found. Install: curl -fsSL https://raw.githubusercontent.com/higgsfield-ai/cli/main/install.sh | sh" >&2
  exit 1
fi

# The CLI is a Windows Node binary; it cannot read a git-bash /c/... path.
winpath() { if command -v cygpath >/dev/null 2>&1; then cygpath -m "$1"; else printf '%s' "$1"; fi; }

if [ "$ground" = "light" ]; then
  INK='fine black fineliner-pen linework with a slightly wobbly imperfect hand-drawn quality, plus a few dashed rays in muted terracotta red-brown and warm ochre'
  PEN='black fineliner pen study marked up on a print'
else
  INK='fine white paint-pen linework with a slightly wobbly imperfect hand-drawn quality, plus a few dashed rays in warm ochre and muted terracotta'
  PEN="designer's pen study marked up on a print"
fi

ASTYLE="Over this architectural night render, draw hand-drawn lighting-design annotations directly on top of the image exactly like a $PEN: $INK. The render itself must stay photorealistic and unchanged, only the pen annotations sit on top of it. For every light source draw a small hand-drawn ring around the fitting, a short leader line to a small handwritten circled number, and clear dashed rays or a beam cone starting at that fitting that shows the exact direction the light travels and where it lands, ending in a hand-drawn arrowhead. Add one simple stick figure with a dashed sightline, and a few short curved arrows showing light sweeping across a surface. Handwritten numerals only, no words, no sentences, no dimension text, no paragraphs. Annotations crisp, generous and legible, never cluttered. Keep every annotation well inside the frame."

PROMPT="$ASTYLE $brief"

args=(generate create gpt_image_2_5 --image-references "$(winpath "$src")")
if [ -n "$ref" ] && [ "$ref" != "none" ]; then
  args+=(--image-references "$(winpath "$ref")")
fi
args+=(--prompt "$PROMPT" --aspect_ratio "$aspect" --resolution 2k --quality high --wait)

if [ -n "$dry" ]; then
  printf 'higgsfield'; printf ' %q' "${args[@]}"; printf '\n'
  exit 0
fi

url=""
for attempt in 1 2 3 4; do
  out_raw=$(higgsfield "${args[@]}" 2>&1)
  if printf '%s' "$out_raw" | grep -q 'https://'; then
    url=$(printf '%s\n' "$out_raw" | grep -o 'https://[^ ]*' | tail -1)
    break
  fi
  echo "attempt $attempt failed: $(printf '%s' "$out_raw" | tail -1)" >&2
  sleep 12
done

if [ -z "$url" ]; then
  echo "FAILED: no result URL after 4 attempts" >&2
  exit 1
fi

if [ -z "$out" ]; then
  echo "$url"
  exit 0
fi

mkdir -p "$(dirname "$out")"
curl -fsSL "$url" -o "$out" || { echo "download failed: $url" >&2; exit 1; }
echo "OK $out"
echo "$url"
