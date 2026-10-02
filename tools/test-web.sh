#!/bin/bash
# Builds the web version and the site, serves them like GitHub Pages (static files, the /project-second-credit/
# sub-path, no special headers) and plays the launcher and each web game in headless Chrome. Screenshots and the
# console log go to build/web-test/. Exit 1 on any console error.
# Usage: tools/test-web.sh [--no-build]   Spec: docs/web.md
set -euo pipefail
cd "$(dirname "$0")/.."
[ "${1:-}" = "--no-build" ] || tools/build-web.sh
tools/build-site.sh
port=8061
tools/serve-web.sh $port >/dev/null 2>&1 &
server=$!
trap 'kill $server 2>/dev/null' EXIT
sleep 1
games=$(grep -vE '^\s*(#|$)' tools/web-games.txt | xargs)
rm -rf build/web-test
node tools/web_test.mjs "http://127.0.0.1:$port/project-second-credit/play/" build/web-test $games
