#!/bin/bash
# Serves the built site (tools/build-site.sh, with the web build in play/) the way GitHub Pages does: plain static
# files, no special headers, under the same sub-path (/project-second-credit/). Open http://127.0.0.1:PORT/project-second-credit/
# Usage: tools/serve-web.sh [port]   (default 8060)
set -euo pipefail
cd "$(dirname "$0")/.."
port=${1:-8060}
[ -d build/site ] || { echo "no build/site: run tools/build-web.sh and tools/build-site.sh first" >&2; exit 1; }
mkdir -p build/serve
ln -sfn ../site build/serve/project-second-credit
echo "http://127.0.0.1:$port/project-second-credit/  (play: .../play/, a game: .../play/?game=tumbletop)"
exec python3 -m http.server "$port" --bind 127.0.0.1 --directory build/serve
