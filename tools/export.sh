#!/bin/bash
# Exports release builds into build/dist/: Linux AppImage, Windows zip and macOS zip (ad-hoc signed).
# Needs Godot and its export templates: tools/fetch-tools.sh godot templates
# Usage: tools/export.sh [linux] [windows] [macos]   (default: all three)
set -euo pipefail
cd "$(dirname "$0")/.."
GODOT=${GODOT_BIN:-$PWD/.tools/bin/godot}
T=.tools
want=" ${*:-linux windows macos} "
ver=$(git describe --tags --always 2>/dev/null || echo dev)
rm -rf build && mkdir -p build/dist

timeout 600 "$GODOT" --headless --path godot --import >/dev/null 2>&1 || true

export_preset() {  # name, output path
  mkdir -p "$(dirname "$2")"
  "$GODOT" --headless --path godot --export-release "$1" "$PWD/$2" 2>&1 | grep -vE '^\s*$|savepack' | tail -20
  [ -s "$2" ] || { echo "export of $1 failed" >&2; exit 1; }
}

if [[ $want == *" linux "* ]]; then
  export_preset Linux build/linux/AppDir/usr/bin/second-credit
  app=build/linux/AppDir
  cp godot/icon.png "$app/second-credit.png"
  cat >"$app/second-credit.desktop" <<DESK
[Desktop Entry]
Type=Application
Name=Second Credit
Comment=Free remakes of games that deserve another go
Exec=second-credit
Icon=second-credit
Categories=Game;ArcadeGame;
DESK
  cat >"$app/AppRun" <<'RUN'
#!/bin/sh
here="$(dirname "$(readlink -f "$0")")"
exec "$here/usr/bin/second-credit" "$@"
RUN
  chmod +x "$app/AppRun" "$app/usr/bin/second-credit"
  tool=$T/dl/appimagetool-x86_64.AppImage
  [ -s "$tool" ] || { mkdir -p $T/dl; curl -fsSL --retry 3 -o "$tool" \
    https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage; }
  chmod +x "$tool"
  APPIMAGE_EXTRACT_AND_RUN=1 ARCH=x86_64 "$tool" --no-appstream "$app" build/dist/SecondCredit-linux-x86_64.AppImage >/dev/null
fi

if [[ $want == *" windows "* ]]; then
  export_preset Windows build/windows/SecondCredit.exe
  (cd build/windows && zip -qr ../dist/SecondCredit-windows-x86_64.zip .)
fi

if [[ $want == *" macos "* ]]; then
  export_preset macOS build/dist/SecondCredit-macos.zip
fi
echo "$ver" >build/dist/VERSION.txt
ls -lh build/dist
