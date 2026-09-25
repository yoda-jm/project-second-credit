#!/bin/bash
# Runs the GdUnit4 tests of the Godot project. Usage: tools/test.sh [gdunit args]   (default: -a res://tests)
# Uses Xvfb when available (needed for input simulation); otherwise runs headless.
set -uo pipefail
source "$(dirname "$0")/xvfb.sh"
cd "$(dirname "$0")/../godot"
GODOT=${GODOT_BIN:-../.tools/bin/godot}
args=("$@"); [ ${#args[@]} -eq 0 ] && args=(-a res://tests -a res://games)

# Import first so new scripts and class names are known.
"$GODOT" --headless --import >/dev/null 2>&1

tool=(-s -d --remote-debug tcp://127.0.0.1:0 res://addons/gdUnit4/bin/GdUnitCmdTool.gd)
if command -v Xvfb >/dev/null; then
  with_xvfb "$GODOT" --path . --audio-driver Dummy --rendering-method gl_compatibility "${tool[@]}" "${args[@]}"
else
  "$GODOT" --headless --audio-driver Dummy --path . "${tool[@]}" "${args[@]}" --ignoreHeadlessMode
fi
code=$?
"$GODOT" --headless --path . --quiet -s res://addons/gdUnit4/bin/GdUnitCopyLog.gd "${args[@]}" >/dev/null 2>&1
exit $code
