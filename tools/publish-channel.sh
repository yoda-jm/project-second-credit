#!/bin/bash
# Publishes an update channel (docs/updater.md) to a GitHub release, from CI (needs GH_TOKEN):
#   latest: the rolling pre-release; its tag moves to this commit, the release stays (links keep working)
#   <tag>:  a tagged release (the "stable" channel: GitHub's latest full release)
# Packs are named with their version, so a pack already in the release is never uploaded again; the launchers are
# replaced; manifest.json goes last, so the channel switches in one step; then packs listed neither in this manifest
# nor in the previous one are removed (a player may be downloading one of the previous ones right now).
# Usage: tools/publish-channel.sh <latest|tag> [previous-manifest.json]
set -euo pipefail
shopt -s nullglob  # a build that changed no game has no new pack to upload
cd "$(dirname "$0")/.."
tag=$1
prev=${2:-}
sha=$(git rev-parse HEAD)

if [ "$tag" = latest ]; then
  git tag -f latest "$sha"
  git push -f origin refs/tags/latest
  notes="Built automatically from $sha on main. May be unstable; tagged releases are the stable ones.
The launcher downloads each game when it's first played and finds new versions at start (docs/updater.md)."
  if gh release view latest >/dev/null 2>&1; then
    gh release edit latest --prerelease --title "Latest build (main)" --notes "$notes"
  else
    gh release create latest --prerelease --title "Latest build (main)" --notes "$notes" --target "$sha"
  fi
else
  gh release view "$tag" >/dev/null 2>&1 || gh release create "$tag" --title "Second Credit $tag" \
    --notes "The launcher for Linux (AppImage), Windows and macOS; it downloads each game when it's first played."
fi

existing=$(gh release view "$tag" --json assets -q '.assets[].name')
published=$(python3 -c 'import json,sys
try: print("\n".join(g["file"] for g in json.load(open(sys.argv[1]))["games"].values()))
except (OSError, ValueError, KeyError): pass' "$prev")
for f in build/channel/*.pck; do
  n=$(basename "$f")
  # a pack the previous manifest lists is already there as described; anything else (new, or left by a cancelled
  # run with other bytes) is uploaded so the file matches this manifest
  if grep -qxF "$n" <<<"$existing" && grep -qxF "$n" <<<"$published"; then continue; fi
  gh release upload "$tag" "$f" --clobber
done
gh release upload "$tag" build/dist/SecondCredit-* build/dist/VERSION.txt --clobber
gh release upload "$tag" build/channel/manifest.json --clobber

keep=$(python3 - build/channel/manifest.json "$prev" <<'PY'
import json, sys
names = set()
for p in sys.argv[1:]:
    try:
        names |= {g["file"] for g in json.load(open(p)).get("games", {}).values()}
    except (OSError, ValueError):
        pass
print("\n".join(sorted(names)))
PY
)
for n in $(gh release view "$tag" --json assets -q '.assets[].name' | grep '\.pck$' || true); do
  grep -qxF "$n" <<<"$keep" || gh release delete-asset "$tag" "$n" -y
done
echo "published $tag: $(grep -c . <<<"$keep") packs kept"
