#!/bin/bash
# Records the construction-movie clips of a game's whole history: for every commit that touched
# godot/games/<game>, a temporary worktree at that commit, then tools/movie_clip.sh there; clips land in
# captures/movie/<game>/<NNN>-<commit>/ (then: python3 tools/make_movie.py <game>). Commits before the game had
# a scene are skipped. GPU recording (CAPTURE_GPU=1) needs the display awake: a sleeping monitor stalls it.
# Usage: tools/movie_history.sh <game> [<game>...]
set -uo pipefail
repo=$(cd "$(dirname "$0")/.." && pwd)
tmp=$(mktemp -d)
trap 'git -C "$repo" worktree remove --force "$tmp/wt" >/dev/null 2>&1; git -C "$repo" worktree prune; rm -rf "$tmp"' EXIT
cd "$repo"
for g in "$@"; do
  n=0
  for c in $(git log --reverse --format=%h -- "godot/games/$g"); do
    wt=$tmp/wt
    git worktree remove --force "$wt" >/dev/null 2>&1; rm -rf "$wt"
    git worktree add --detach "$wt" "$c" >/dev/null 2>&1 || { echo "$g $c: worktree failed"; continue; }
    if [ ! -f "$wt/godot/games/$g/scenes/${g}_game.tscn" ]; then
      echo "$g $c: no scene yet, skipped"; continue
    fi
    n=$((n + 1))
    ln -s "$repo/.tools" "$wt/.tools"
    cp "$repo/tools/movie_clip.sh" "$repo/tools/xvfb.sh" "$wt/tools/"
    [ -d "$repo/godot/.godot" ] && cp -r "$repo/godot/.godot" "$wt/godot/.godot"  # reuse the import cache
    (cd "$wt" && timeout 600 .tools/bin/godot --headless --path godot --import >/dev/null 2>&1)
    out=$(cd "$wt" && timeout 900 tools/movie_clip.sh "$g" 14 1280x720 2>&1 | tail -1)
    if [ -f "$wt/$out" ]; then
      d=$(printf "captures/movie/%s/%03d-%s" "$g" "$n" "$c")
      mkdir -p "$d" && cp "$wt/$(dirname "$out")"/* "$d/"
      echo "$g step $n $c: ok"
    else
      echo "$g step $n $c: FAILED ($out)"
    fi
  done
done
