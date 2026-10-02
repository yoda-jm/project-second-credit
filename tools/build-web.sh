#!/bin/bash
# Exports the web build into build/web/ (index.html, .js, .wasm, .pck): Godot's single-threaded web template (GitHub
# Pages sends no cross-origin isolation headers) and the Compatibility renderer (WebGL 2). Only the games listed in
# tools/web-games.txt go in: the Web preset's exclude filter is rewritten from that list each time.
# Needs Godot and its export templates: tools/fetch-tools.sh godot templates.  Spec: docs/web.md
set -euo pipefail
cd "$(dirname "$0")/.."
GODOT=${GODOT_BIN:-$PWD/.tools/bin/godot}

sel=" $(grep -vE '^\s*(#|$)' tools/web-games.txt | xargs) "
# the editor add-ons stay out, except godot_ai's runtime helper (an autoload the plugin registers; idle in exported
# builds, but missing it is an error at start) and the utils it preloads
ex="addons/gdUnit4/*, tools/*, */tests/*, reports/*"
for f in godot/addons/godot_ai/*; do
  n=$(basename "$f")
  [ "$n" = runtime ] || [ "$n" = utils ] && continue
  if [ -d "$f" ]; then ex="$ex, addons/godot_ai/$n/*"; else ex="$ex, addons/godot_ai/$n"; fi
done
for d in godot/games/*/; do
  id=$(basename "$d")
  if [[ $sel != *" $id "* ]]; then
    ex="$ex, games/$id/*"
    [ -f "godot/core/ui/cards/$id.png" ] && ex="$ex, core/ui/cards/$id.png"
  fi
done
python3 - "$ex" <<'PY'
import re, sys
p = "godot/export_presets.cfg"
s = open(p).read()
head = s.index('name="Web"')
start = s.index('exclude_filter="', head)
end = s.index('"\n', start + len('exclude_filter="'))
s = s[:start] + 'exclude_filter="' + sys.argv[1] + s[end:]
open(p, "w").write(s)
PY

timeout 900 "$GODOT" --headless --path godot --import >/dev/null 2>&1 || true
rm -rf build/web && mkdir -p build/web
"$GODOT" --headless --path godot --export-release Web "$PWD/build/web/index.html" 2>&1 | grep -vE '^\s*$|savepack' | tail -20
[ -s build/web/index.pck ] || { echo "web export failed" >&2; exit 1; }
echo "web build:$sel"
du -h build/web/* | sort -h
