#!/bin/bash
# Assembles the GitHub Pages site into build/site (site/ plus the shared fonts). Preview:
#   tools/build-site.sh && python3 -m http.server -d build/site 8000
set -euo pipefail
cd "$(dirname "$0")/.."
rm -rf build/site && mkdir -p build/site/fonts
cp -r site/. build/site/
cp godot/core/fonts/*.ttf godot/core/fonts/KENNEY_LICENSE.txt build/site/fonts/
touch build/site/.nojekyll
