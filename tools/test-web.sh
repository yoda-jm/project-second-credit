#!/bin/bash
# Builds the web version and the site, serves them like GitHub Pages (static files, the /project-second-credit/
# sub-path, no special headers) and plays the launcher and each web game in headless Chrome: each game downloads its
# pack, then the first one comes back from the browser's storage. Screenshots and the console log go to
# build/web-test/. Exit 1 on any console error.
# Usage: tools/test-web.sh [--no-build] [id ...]   (default: every game in tools/web-games.txt)  Spec: docs/updater.md
set -euo pipefail
cd "$(dirname "$0")/.."
if [ "${1:-}" = "--no-build" ]; then shift; else tools/build-web.sh; fi
tools/build-site.sh
port=$((20000 + RANDOM % 20000))
tools/serve-web.sh $port >/dev/null 2>&1 &
server=$!
trap 'kill $server 2>/dev/null' EXIT
sleep 1
games=${*:-$(grep -vE '^\s*(#|$)' tools/web-games.txt | xargs)}
rm -rf build/web-test
node tools/web_test.mjs "http://127.0.0.1:$port/project-second-credit/play/" build/web-test $games
