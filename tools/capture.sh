#!/bin/bash
# Runs a scene for a number of frames and saves PNG screenshots, so an agent can look at the result.
# Usage: tools/capture.sh [-s res://scene.tscn] [-f frames] [-e every] [-r WxH] [-o outdir] [--gpu]
#   -s  scene to run (default: the project's main scene)
#   -f  frames to run at a fixed 60 fps (default 60, i.e. one second)
#   -e  keep every Nth frame (default: only the last frame)
#   -r  resolution (default 1920x1080; 960x540 is about 4x faster in software)
#   -o  output folder (default: captures/<timestamp>, git-ignored)
#   --gpu  render on the current display with the real GPU and the project's renderer (opens a window).
#          The default is a private Xvfb display with software OpenGL (Compatibility renderer): no window,
#          but no Forward+ effects and slower.
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
source "$here/xvfb.sh"
GODOT=${GODOT_BIN:-$here/../.tools/bin/godot}
scene="" frames=60 every="" res=1920x1080 out="" gpu=0
while [ $# -gt 0 ]; do
  case $1 in
    -s) scene=$2; shift 2 ;;
    -f) frames=$2; shift 2 ;;
    -e) every=$2; shift 2 ;;
    -r) res=$2; shift 2 ;;
    -o) out=$2; shift 2 ;;
    --gpu) gpu=1; shift ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
done
every=${every:-$frames}
out=${out:-$here/../captures/$(date +%Y%m%d-%H%M%S)}
mkdir -p "$out"; out=$(cd "$out" && pwd)
log=$(mktemp); trap 'rm -f "$log"' EXIT

cmd=("$GODOT" --path "$here/../godot" --fixed-fps 60 --resolution "$res")
user=(res://tools/capture/capture.tscn -- --frames="$frames" --every="$every" --out="$out")
[ -n "$scene" ] && user+=(--scene="$scene")
rc=0
if [ $gpu -eq 1 ]; then
  "${cmd[@]}" "${user[@]}" >"$log" 2>&1 || rc=$?
else
  with_xvfb "${cmd[@]}" --rendering-method gl_compatibility "${user[@]}" >"$log" 2>&1 || rc=$?
  [ $rc -eq 127 ] && { echo "Xvfb not installed; use --gpu" >&2; exit 1; }
fi
[ $rc -eq 0 ] || echo "godot exited with $rc" >&2
grep -iE "^(ERROR|SCRIPT ERROR|WARNING)" "$log" | grep -v "V-Sync" >&2 || true
ls "$out"/frame*.png 2>/dev/null || { echo "no frames written; log:" >&2; tail -20 "$log" >&2; exit 1; }
