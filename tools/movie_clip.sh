#!/bin/bash
# Records a clip (video and game audio) of a game's current build for the construction movie:
# captures/movie/<game>/<NNN>-<commit>/clip.avi, using Godot's Movie Maker (nothing plays on the speakers).
# Usage: tools/movie_clip.sh <game> [seconds] [resolution]    e.g. tools/movie_clip.sh glimmerdeep 14 1280x720
# The game's scene runs its demo (--demo). Software rendering under Xvfb is slow: a few minutes per clip.
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
source "$here/xvfb.sh"
game=${1:?usage: movie_clip.sh <game> [seconds] [resolution]}
secs=${2:-14}
res=${3:-1280x720}
scene="res://games/$game/scenes/${game}_game.tscn"
cd "$here/.."
n=$( (ls -d captures/movie/"$game"/*/ 2>/dev/null || true) | wc -l)
dir=$(printf "captures/movie/%s/%03d-%s" "$game" $((n + 1)) "$(git rev-parse --short HEAD)")
mkdir -p "$dir"
fps=30
with_xvfb .tools/bin/godot --path godot --rendering-method gl_compatibility --resolution "$res" \
  --write-movie "$PWD/$dir/clip.avi" --fixed-fps $fps --quit-after $((secs * fps)) "$scene" -- --demo \
  > "$dir/log.txt" 2>&1 || true
git log -1 --format="%h %ci%n%s" > "$dir/commit.txt"
[ -s "$dir/clip.avi" ] || { echo "no clip written, see $dir/log.txt" >&2; exit 1; }
echo "$dir/clip.avi"
