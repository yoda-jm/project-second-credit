#!/bin/bash
# Plays every replay of the GDash checkout with GDash's own engine and writes the results to
# .tools/ref/gdash-results.txt (git-ignored: it names original caves). The engine reference test compares our
# port with this file.
set -euo pipefail
root=$(cd "$(dirname "$0")/../.." && pwd)
[ -x "$root/.tools/ref/gdash-harness" ] || "$root/tools/gdash_port/harness/build.sh"
out="$root/.tools/ref/gdash-results.txt"
: > "$out"
find "$root/.tools/ref/gdash" -name "*.bd" | sort | while read -r f; do
  "$root/.tools/ref/gdash-harness" "$f" 2>/dev/null | sed "s|^|$(basename "$f") |" >> "$out"
done
echo "$(wc -l < "$out") replays -> $out"
