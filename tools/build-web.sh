#!/bin/bash
# Exports the web build into build/web/: the launcher alone (index.html, .js, .wasm, .pck: Godot's single-threaded
# template, since GitHub Pages sends no cross-origin isolation headers, and the Compatibility renderer for WebGL 2),
# plus build/web/packs/: the channel's manifest and the pack of every game listed in tools/web-games.txt. The
# launcher downloads a game's pack the first time it's played and keeps it in the browser (IndexedDB).
# Needs Godot and its export templates (tools/fetch-tools.sh godot templates) and the packs (tools/export-packs.sh,
# or SKIP_PACKS= unset to export them here).  Spec: docs/updater.md
set -euo pipefail
cd "$(dirname "$0")/.."
GODOT=${GODOT_BIN:-$PWD/.tools/bin/godot}
presets=godot/export_presets.cfg

ids=$(grep -vE '^\s*(#|$)' tools/web-games.txt | xargs)
[ "${SKIP_PACKS:-}" ] || tools/export-packs.sh $ids

# the godot_ai add-on registers an autoload (its runtime helper, idle in exported builds): keep runtime/ and utils/
# so it loads, leave its editor parts out
ex="games/*, addons/gdUnit4/*, tools/*, */tests/*, reports/*"
for f in godot/addons/godot_ai/*; do
  n=$(basename "$f")
  [ "$n" = runtime ] || [ "$n" = utils ] && continue
  if [ -d "$f" ]; then ex="$ex, addons/godot_ai/$n/*"; else ex="$ex, addons/godot_ai/$n"; fi
done
mkdir -p build && cp "$presets" build/export_presets.web.orig
trap 'cp build/export_presets.web.orig "$presets"' EXIT
python3 - "$presets" "$ex" <<'PY'
import sys
p, ex = sys.argv[1], sys.argv[2]
s = open(p).read()
head = s.index('name="Web"')
start = s.index('exclude_filter="', head)
end = s.index('"\n', start + len('exclude_filter="'))
open(p, "w").write(s[:start] + 'exclude_filter="' + ex + s[end:])
PY
python3 tools/make_manifest.py --build-info godot/core/library/build.json
[ "${SKIP_IMPORT:-}" ] || timeout 900 "$GODOT" --headless --path godot --import >/dev/null 2>&1 || true
rm -rf build/web && mkdir -p build/web
"$GODOT" --headless --path godot --export-release Web "$PWD/build/web/index.html" 2>&1 | grep -E "^ERROR" | grep -v "savepack" | head -5 || true
[ -s build/web/index.pck ] || { echo "web export failed" >&2; exit 1; }
python3 tools/make_manifest.py --channel web --web-only ${PREV_MANIFEST:+--prev "$PREV_MANIFEST"} --out build/web/packs
echo "web build: launcher $(du -sh build/web/index.pck | cut -f1), games: $ids"
du -sh build/web build/web/packs
