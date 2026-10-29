#!/usr/bin/env bash
# Generate one hand-drawn fineliner/stick-figure sketch on transparent ground.
# Prepends the fixed LITELAB style contract to the brief you supply.
#
# Usage: sketch.sh -o OUT.png -b "content brief" [-a ASPECT] [-r STYLE_REF.png] [-s 1k] [-q high]
#
# -a/--aspect  default 16:9. Use the aspect ratio of the box the image lands in
#              (see references/layout-rules.md). 21:9 or 16:9 suit section details.
# -r/--ref     style reference image. Defaults to assets/style-reference.png.
#              Pass an empty string to omit the reference.
# -d/--dry-run print the exact higgsfield command instead of submitting it.
set -u

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
brief="" out="" aspect="16:9" res="1k" qual="high" dry=""
ref="$SKILL_DIR/assets/style-reference.png"
[ -f "$ref" ] || ref=""

while [ $# -gt 0 ]; do
  case "$1" in
    -o|--out) out="$2"; shift 2;;
    -b|--brief) brief="$2"; shift 2;;
    -a|--aspect) aspect="$2"; shift 2;;
    -r|--ref) ref="$2"; shift 2;;
    -s|--resolution) res="$2"; shift 2;;
    -q|--quality) qual="$2"; shift 2;;
    -d|--dry-run) dry=1; shift;;
    *) echo "unknown arg: $1" >&2; exit 2;;
  esac
done

if [ -z "$brief" ]; then
  echo "missing -b \"content brief\"" >&2
  exit 2
fi

command -v higgsfield >/dev/null 2>&1 || export PATH="$PATH:/c/Users/LITELAB/AppData/Local/Programs/nodejs"
if ! command -v higgsfield >/dev/null 2>&1; then
  echo "higgsfield CLI not found. Install: curl -fsSL https://raw.githubusercontent.com/higgsfield-ai/cli/main/install.sh | sh" >&2
  exit 1
fi

# The CLI is a Windows Node binary; it cannot read a git-bash /c/... path.
winpath() { if command -v cygpath >/dev/null 2>&1; then cygpath -m "$1"; else printf '%s' "$1"; fi; }

STYLE='Loose hand-drawn lighting-designer notebook study drawn with a fine black fineliner pen on plain paper. Deliberately imperfect wobbly linework, uneven double-stroke outlines, simple stick figures with round heads and thin limbs, hand-drawn slightly curved leader lines and open arrowheads, sparse diagonal cross-hatching for shading, dotted and dashed construction lines. Only two accents, used sparingly: muted terracotta red-brown and warm ochre, applied as light hand-coloured marker strokes over the ink. Absolutely no words, no letters, no numbers, no dimension text, no labels, no title block, no legend text. No gradients, no digital polish, no CAD precision, no 3D render. Flat transparent background, nothing but the sketch.'

PROMPT="$STYLE $brief"

args=(generate create gpt_image_2_5 --prompt "$PROMPT" --aspect_ratio "$aspect" --resolution "$res" --quality "$qual" --background transparent --wait)
if [ -n "$ref" ] && [ "$ref" != "none" ]; then
  args+=(--image-references "$(winpath "$ref")")
fi

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

# Tighten the alpha bbox so a mostly-empty 21:9 canvas does not shrink the sketch on the page.
python - "$out" <<'PY' 2>/dev/null || true
import sys
try:
    from PIL import Image
except Exception:
    sys.exit(0)
p = sys.argv[1]
im = Image.open(p)
if im.mode != "RGBA":
    sys.exit(0)
bb = im.getbbox()
if bb:
    im.crop(bb).save(p)
PY

echo "OK $out"
echo "$url"
