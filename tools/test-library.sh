#!/bin/bash
# End-to-end check of the launcher download and the game packs (docs/updater.md): exports the packs and a slim
# Linux launcher, serves a channel on a local web server, then runs the exported launcher three times with a private
# user folder:
#   1. it downloads every game from the channel, checks and mounts each one, and runs it for a moment
#   2. started again offline, it mounts the downloaded games and runs each one
#   3. from a fresh folder, a channel with damaged files: nothing may be installed
# Needs Godot and its export templates (tools/fetch-tools.sh godot templates).
# Usage: tools/test-library.sh [id ...]   (default: every game)   SKIP_PACKS=1 reuses build/packs/
set -euo pipefail
cd "$(dirname "$0")/.."
GODOT=${GODOT_BIN:-$PWD/.tools/bin/godot}
T=build/test-library
rm -rf "$T" && mkdir -p "$T/channel" "$T/bad" "$T/home" "$T/home2"

[ "${SKIP_PACKS:-}" ] || tools/export-packs.sh "$@"
python3 tools/make_manifest.py --build-info godot/core/library/build.json
"$GODOT" --headless --path godot --export-release Linux "$PWD/$T/launcher.x86_64" 2>&1 | grep -E "^ERROR" | grep -v "godot_ai\|plugin.gd\|savepack" | head -5 || true
[ -s "$T/launcher.x86_64" ] || { echo "launcher export failed" >&2; exit 1; }
python3 tools/pck_list.py "$T/launcher.x86_64" --sum 2>&1 | grep -E "games/|Godot" | head -3
if python3 tools/pck_list.py "$T/launcher.x86_64" 2>/dev/null | grep -q " games/"; then
  echo "the slim launcher holds game files" >&2; exit 1
fi

if [ $# -gt 0 ]; then  # only these games in the channel
  mkdir -p "$T/packs" && for id in "$@"; do cp "build/packs/$id.pck" "$T/packs/"; done
  python3 tools/make_manifest.py --packs "$T/packs" --dist "$T/none" --out "$T/channel"
else
  python3 tools/make_manifest.py --dist "$T/none" --out "$T/channel"
fi
# the damaged channel: the same manifest, two packs with flipped bytes
python3 - "$T" <<'PY'
import json, os, shutil, sys
t = sys.argv[1]
m = json.load(open(f"{t}/channel/manifest.json"))
m["games"] = dict(list(m["games"].items())[:2])
for g in m["games"].values():
    data = bytearray(open(f"{t}/channel/{g['file']}", "rb").read())
    data[len(data) // 2] ^= 0xFF
    open(f"{t}/bad/{g['file']}", "wb").write(data)
json.dump(m, open(f"{t}/bad/manifest.json", "w"))
PY

port=$((20000 + RANDOM % 20000))
python3 -m http.server "$port" --bind 127.0.0.1 -d "$T" >/dev/null 2>&1 &
server=$!
trap 'kill $server 2>/dev/null' EXIT
sleep 1

run() {  # home, step, channel
  echo "== $2"
  XDG_DATA_HOME="$PWD/$T/$1" timeout 1200 "$T/launcher.x86_64" --headless --audio-driver Dummy -- \
    --channel-url="http://127.0.0.1:$port/$3/manifest.json" --library-selftest="$2" 2>&1 | tee "$T/$2.log" | grep -E "^SELFTEST" || true
  if grep -E "^(SCRIPT ERROR|ERROR: .*(Parse|Cannot|load))" "$T/$2.log" | grep -v "godot_ai" | head -5 | grep .; then
    echo "script errors in $2 (see $T/$2.log)"; return 1
  fi
  grep -q "^SELFTEST $2: PASSED" "$T/$2.log"
}
ok=0
run home download channel || ok=1
run home reopen channel || ok=1
run home2 damaged bad || ok=1
[ $ok -eq 0 ] && echo "library test: PASSED" || echo "library test: FAILED (logs in $T/)"
exit $ok
