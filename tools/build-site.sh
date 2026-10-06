#!/bin/bash
# Assembles the GitHub Pages site into build/site (site/ plus the shared fonts). Preview:
#   tools/build-site.sh && python3 -m http.server -d build/site 8000
set -euo pipefail
cd "$(dirname "$0")/.."
rm -rf build/site && mkdir -p build/site/fonts
cp -r site/. build/site/
cp godot/core/fonts/*.ttf godot/core/fonts/KENNEY_LICENSE.txt build/site/fonts/
touch build/site/.nojekyll
# the web build, when there is one (tools/build-web.sh), is played from play/ (the games' packs in play/packs/)
if [ -s build/web/index.pck ]; then
  mkdir -p build/site/play && cp -r build/web/. build/site/play/
fi
