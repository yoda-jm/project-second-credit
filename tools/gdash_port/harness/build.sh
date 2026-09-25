#!/bin/bash
# Builds a command-line GDash replay player from the reference checkout (.tools/ref/gdash), linked against the
# system GLib. It plays the replays of a BDCFF file with GDash's own engine; tools/gdash_port/reference.sh uses it
# to produce the expected results our port is tested against. Needs g++ and GLib development files.
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
G=$(cd "$here/../../../.tools/ref/gdash" && pwd)
out="$here/../../../.tools/ref/gdash-harness"
srcs=$(ls "$G"/src/cave/*.cpp "$G"/src/cave/object/*.cpp "$G"/src/cave/helper/*.cpp | grep -v "gamerender\|gamecontrol\|titleanimation")
srcs="$srcs $G/src/fileops/bdcffload.cpp $G/src/fileops/bdcffsave.cpp $G/src/fileops/bdcffhelper.cpp $G/src/fileops/c64import.cpp"
srcs="$srcs $G/src/misc/logger.cpp $G/src/misc/printf.cpp $G/src/misc/util.cpp"
g++ -std=c++98 -w -O2 -I"$here" -I"$G/src" -I"$G/include" $(pkg-config --cflags glib-2.0) \
  "$here/harness.cpp" "$here/stubs.cpp" $srcs $(pkg-config --libs glib-2.0) -o "$out"
echo "built $out"
