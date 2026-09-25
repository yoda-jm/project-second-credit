#!/bin/bash
# Saves screenshots of the current build for the construction movie: captures/movie/<NNN>-<commit>/.
# Usage: tools/movie_shot.sh [capture.sh options]   (default: 8 s of the demo, one frame every 2 s, 1280x720)
# The movie itself can later be rebuilt at full quality by replaying the git history (see docs/setup.md).
set -euo pipefail
cd "$(dirname "$0")/.."
n=$(ls -d captures/movie/*/ 2>/dev/null | wc -l)
dir=$(printf "captures/movie/%03d-%s" $((n + 1)) "$(git rev-parse --short HEAD)")
[ $# -gt 0 ] || set -- -f 480 -e 120 -r 1280x720
tools/capture.sh "$@" -o "$dir"
git log -1 --format="%h %ci%n%s" > "$dir/commit.txt"
echo "$dir"
