#!/bin/bash
# Exports one .pck per game into build/packs/<id>.pck: only godot/games/<id>/ (the launcher and core/ are in the
# launcher download). The "Pack" export preset's exclude filter is rewritten for each game, then restored.
# Needs Godot and its export templates: tools/fetch-tools.sh godot templates.  Spec: docs/updater.md
# Usage: tools/export-packs.sh [id ...]   (default: every game folder)
set -euo pipefail
cd "$(dirname "$0")/.."
GODOT=${GODOT_BIN:-$PWD/.tools/bin/godot}
presets=godot/export_presets.cfg
all=$(cd godot/games && ls -d */ | tr -d /)
want=${*:-$all}
mkdir -p build/packs

cp "$presets" build/export_presets.cfg.orig
trap 'cp build/export_presets.cfg.orig "$presets"' EXIT
base=$(grep -A8 '^name="Pack"' "$presets" | grep '^exclude_filter=' | sed 's/^exclude_filter="//; s/"$//')

[ "${SKIP_IMPORT:-}" ] || timeout 900 "$GODOT" --headless --path godot --import >/dev/null 2>&1 || true

for id in $want; do
  [ -d "godot/games/$id" ] || { echo "no game $id" >&2; exit 1; }
  ex="$base"
  for other in $all; do
    [ "$other" = "$id" ] || ex="$ex, games/$other/*"
  done
  python3 - "$presets" "$ex" <<'PY'
import sys
p, ex = sys.argv[1], sys.argv[2]
s = open(p).read()
head = s.index('name="Pack"')
start = s.index('exclude_filter="', head)
end = s.index('"\n', start + len('exclude_filter="'))
open(p, "w").write(s[:start] + 'exclude_filter="' + ex + s[end:])
PY
  rm -f "build/packs/$id.pck"
  "$GODOT" --headless --path godot --export-pack Pack "$PWD/build/packs/$id.pck" 2>&1 | grep -E 'ERROR|error' | grep -v savepack | head -5 || true
  [ -s "build/packs/$id.pck" ] || { echo "export of $id failed" >&2; exit 1; }
  printf '%-14s %6.1f MB\n' "$id" "$(echo "$(stat -c %s "build/packs/$id.pck") / 1000000" | bc -l)"
done
