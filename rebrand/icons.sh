#!/usr/bin/env bash
# Put Buildflow's icon in place of upstream's, in every size the app and installers use.
#
#   rebrand/icons.sh
#
# The artwork is rebrand/icon.svg: the Buildflow mark (brand/logo color.svg) in lime on an ink tile.
# The outputs keep upstream's file names under assets/app-icon/, because the code and the packaging
# scripts refer to them by those names. They are committed, so a build never needs these tools.
#
# Needs rsvg-convert (brew install librsvg) or resvg; iconutil (macOS) for the .icns.
# Run it again only when rebrand/icon.svg changes, or if an upstream merge brings their icon back.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$ROOT/rebrand/icon.svg"
DIR="$ROOT/assets/app-icon"
SVG="$DIR/craft-anything.svg"
ID="ai.storyteller.craft-anything"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

if command -v rsvg-convert >/dev/null; then
  render() { rsvg-convert -w "$2" -h "$2" "$1" -o "$3"; }
elif command -v resvg >/dev/null; then
  render() { resvg -w "$2" -h "$2" "$1" "$3" </dev/null; }
else
  echo "error: need rsvg-convert (brew install librsvg) or resvg" >&2
  exit 1
fi

grep -q 'viewBox="0 0 512 512"' "$SRC" || { echo "error: $SRC must be a 512 tile" >&2; exit 1; }
cp "$SRC" "$SVG"

# macOS icons follow Apple's grid: the tile is 824/1024 of the canvas with a transparent margin.
MAC="$TMP/mac.svg"
sed 's/viewBox="0 0 512 512"/viewBox="-62.136 -62.136 636.272 636.272"/' "$SVG" >"$MAC"

render "$SVG" 1024 "$DIR/craft-anything-1024.png"
for s in 16 24 32 48 64 128 256 512; do
  mkdir -p "$DIR/hicolor/${s}x${s}/apps"
  render "$SVG" "$s" "$DIR/hicolor/${s}x${s}/apps/$ID.png"
done
mkdir -p "$DIR/hicolor/scalable/apps"
cp "$SVG" "$DIR/hicolor/scalable/apps/$ID.svg"

ICO_PNGS=()
for s in 16 20 24 32 40 48 64 128 256; do
  render "$SVG" "$s" "$TMP/ico-$s.png"
  ICO_PNGS+=("$TMP/ico-$s.png")
done
(cd "$ROOT" && cargo run -q -p xtask -- ico "$DIR/craft-anything.ico" "${ICO_PNGS[@]}")

if command -v iconutil >/dev/null; then
  SET="$TMP/craft-anything.iconset"
  mkdir -p "$SET"
  for s in 16 32 128 256 512; do
    render "$MAC" "$s" "$SET/icon_${s}x${s}.png"
    render "$MAC" $((s * 2)) "$SET/icon_${s}x${s}@2x.png"
  done
  iconutil -c icns -o "$DIR/craft-anything.icns" "$SET"
else
  echo "warning: iconutil not found (macOS only); craft-anything.icns not regenerated" >&2
fi

cat >"$DIR/LICENSE.txt" <<'TXT'
Buildflow app icon (craft-anything.svg and every file derived from it in this directory:
craft-anything-1024.png, craft-anything.icns, craft-anything.ico and hicolor/).

This is the Buildflow mark. It replaces the icon of the project Buildflow is forked from, as that
project's brand terms ask forks to do. It is NOT covered by the repository's MIT OR Apache-2.0
license: forks and modified versions of Buildflow must replace it with their own icon.

The files keep their original names only because the code refers to them by name.
trace.py is a tool from the original project, covered by the repository's MIT OR Apache-2.0 license.
TXT
cat >"$DIR/README.md" <<'TXT'
# Buildflow app icon

The Buildflow mark in lime `#d1fb8c` on an ink `#100e0a` tile (512 units, 110-unit corners).
The source is `rebrand/icon.svg`; `rebrand/icons.sh` makes every file here from it. The file names
are the original project's, because the code and packaging scripts refer to them by name.
TXT
echo "icons written to $DIR"
