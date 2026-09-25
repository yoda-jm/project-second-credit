#!/bin/bash
# Parses every GDScript file of the project and prints errors. Usage: tools/check.sh [res://folder ...]
cd "$(dirname "$0")/../godot"
GODOT=${GODOT_BIN:-../.tools/bin/godot}
timeout 300 "$GODOT" --headless --import >/dev/null 2>&1
timeout 300 "$GODOT" --headless -s res://tools/check_scripts.gd -- "$@" 2>&1 | grep -E "Parse Error|Compile Error|FAILED|checked|^\s+at: GDScript::reload"
exit ${PIPESTATUS[0]}
