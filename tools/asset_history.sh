#!/bin/bash
# Renders the evolution of a game's 3D models: for every commit that changed its model generator
# (tools/blender/<game>_models.py, following renames), rebuild that version's models in a temporary folder
# and render a studio contact sheet to captures/assets/<game>/<NNN>-<commit>.png. Also renders a turntable of
# the current models to captures/assets/<game>/turntable/. Usage: tools/asset_history.sh <game> [--no-turntable]
set -euo pipefail
root=$(cd "$(dirname "$0")/.." && pwd)
game=${1:?usage: asset_history.sh <game>}
script="tools/blender/${game}_models.py"
out="$root/captures/assets/$game"
mkdir -p "$out"
blender="$root/.tools/bin/blender"
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
n=0
git -C "$root" log --follow --format="%h" --name-only -- "$script" | awk 'NF' | paste - - | tac | \
while read -r sha path; do
  h=$(git -C "$root" show "$sha:$path" | sha1sum | cut -c1-12)
  [ "$h" = "${prev:-}" ] && continue   # a rename or unrelated change: same models
  prev=$h
  n=$((n + 1))
  png=$(printf "%s/%03d-%s.png" "$out" "$n" "$sha")
  [ -f "$png" ] && continue
  git -C "$root" show "$sha:$path" > "$tmp/gen.py"
  rm -rf "$tmp/models"; mkdir -p "$tmp/models"
  "$blender" -b --factory-startup -P "$tmp/gen.py" -- "$tmp/models" > "$tmp/gen.log" 2>&1 || { echo "skip $sha"; continue; }
  subject=$(git -C "$root" log -1 --format="%ad" --date=short "$sha")
  "$blender" -b --factory-startup -P "$root/tools/blender/render_models.py" -- "$tmp/models" "$png" \
    "$game models, version $n ($subject)" > "$tmp/render.log" 2>&1
  echo "$png"
done
if [ "${2:-}" != "--no-turntable" ]; then
  mkdir -p "$out/turntable"
  "$blender" -b --factory-startup -P "$root/tools/blender/render_models.py" -- \
    "$root/godot/games/$game/art/models" "$out/turntable/frame_" "$game models, current" --turntable 48 > "$tmp/turn.log" 2>&1
  ffmpeg -v error -y -framerate 24 -i "$out/turntable/frame_%04d.png" -c:v libx264 -pix_fmt yuv420p "$out/turntable.mp4"
  echo "$out/turntable.mp4"
fi
