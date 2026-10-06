#!/usr/bin/env python3
"""Writes an update channel (docs/updater.md): manifest.json plus each game's pack named with its version, from
build/packs/<id>.pck (tools/export-packs.sh) and the launcher downloads in build/dist/.

  tools/make_manifest.py --channel latest [--prev old-manifest.json] [--out build/channel] [--web-only]

- A game's version comes from its folder's git tree and the Godot version: the same folder gives the same version,
  so players never download a game again for nothing.
- min_core: the core serial (commits that changed the launcher's code, see core_serial) at the commit that last
  changed the game. A launcher older than that hasn't been tested with this version of the game.
- changes: commit subjects that touched the game since the previous manifest's version (or its last three).
- web: the game is listed in tools/web-games.txt (checked in the browser's Compatibility renderer).
Also writes build info for the launcher export: --build-info godot/core/library/build.json
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
CORE_PATHS = ["godot/core", "godot/project.godot", "godot/addons", "godot/icon.png"]
LAUNCHERS = {"linux": "SecondCredit-linux-x86_64.AppImage", "windows": "SecondCredit-windows-x86_64.zip",
             "macos": "SecondCredit-macos.zip"}


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()


def core_serial(commit="HEAD"):
    """How many commits up to `commit` changed the launcher's own code: rises with every launcher change."""
    return int(git("rev-list", "--count", commit, "--", *CORE_PATHS) or 0)


def godot_version():
    m = re.search(r'^GODOT=\$\{GODOT_VERSION:-([0-9.]+)\}|^GODOT=([0-9.]+)', open(os.path.join(ROOT, "tools/fetch-tools.sh")).read(), re.M)
    return (m.group(1) or m.group(2)) if m else "4"


def game_ids():
    return sorted(d for d in os.listdir(os.path.join(ROOT, "godot/games")) if os.path.isdir(os.path.join(ROOT, "godot/games", d)))


# raised when every pack must get a new name (2: the first channel's checksums didn't match its files)
PACK_SERIES = 2


def version_of(gid, godot):
    tree = git("rev-parse", f"HEAD:godot/games/{gid}")
    return hashlib.sha1(f"{tree} {godot} {PACK_SERIES}".encode()).hexdigest()[:10]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def web_games():
    p = os.path.join(ROOT, "tools/web-games.txt")
    if not os.path.exists(p):
        return set()
    return {l.strip() for l in open(p) if l.strip() and not l.startswith("#")}


def build_name():
    return git("describe", "--tags", "--always", "--exclude", "latest")


def build_info(path, bundled):
    godot = godot_version()
    info = {"build": build_name(), "commit": git("rev-parse", "--short", "HEAD"), "core": core_serial(), "godot": godot,
            "date": git("show", "-s", "--format=%cI", "HEAD"),
            "games": {g: version_of(g, godot) for g in game_ids()} if bundled else {}}
    with open(path, "w") as f:
        json.dump(info, f, indent=1)
    print(f"build info: {info['build']}, core {info['core']}, {len(info['games'])} games bundled")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--channel", default="latest")
    ap.add_argument("--packs", default="build/packs")
    ap.add_argument("--dist", default="build/dist")
    ap.add_argument("--out", default="build/channel")
    ap.add_argument("--prev", help="the channel's current manifest (for what changed, and to keep old notes)")
    ap.add_argument("--web-only", action="store_true", help="only the games checked in the browser (the Pages copy)")
    ap.add_argument("--keep-published", action="store_true",
                    help="a game whose version is already in --prev keeps that entry (its file is already published: "
                         "Godot's exports are not byte-for-byte the same twice, so a new copy would not match)")
    ap.add_argument("--all-web", action="store_true", help="mark every game as playable in the browser (to try them there)")
    ap.add_argument("--build-info", help="write the launcher's build info here instead")
    ap.add_argument("--bundled", action="store_true", help="with --build-info: the launcher holds every game")
    a = ap.parse_args()
    os.chdir(ROOT)
    if a.build_info:
        build_info(a.build_info, a.bundled)
        return
    godot = godot_version()
    prev = {}
    if a.prev and os.path.exists(a.prev):
        try:
            prev = json.load(open(a.prev))
        except ValueError:
            prev = {}
    os.makedirs(a.out, exist_ok=True)
    web = set(game_ids()) if a.all_web else web_games()
    games = {}
    for gid in game_ids():
        pck = os.path.join(a.packs, gid + ".pck")
        if not os.path.exists(pck):
            print(f"no pack for {gid}: skipped", file=sys.stderr)
            continue
        if a.web_only and gid not in web:
            continue
        ver = version_of(gid, godot)
        last = git("log", "-1", "--format=%H", "--", f"godot/games/{gid}")
        old = prev.get("games", {}).get(gid, {})
        if old.get("version") == ver:
            changes = old.get("changes", [])
        else:
            since = prev.get("commit", "")
            rng = [f"{since}..HEAD"] if since and subprocess.run(["git", "cat-file", "-e", since], cwd=ROOT).returncode == 0 else ["-3"]
            changes = [s for s in git("log", "--format=%s", *rng, "--", f"godot/games/{gid}").splitlines() if s][:6]
        if a.keep_published and old.get("version") == ver and old.get("file") and old.get("sha256") and old.get("size"):
            games[gid] = dict(old, web=gid in web, min_core=core_serial(last))
            continue
        name = f"{gid}-{ver}.pck"
        dest = os.path.join(a.out, name)
        if not os.path.exists(dest):
            shutil.copyfile(pck, dest)
        games[gid] = {"version": ver, "file": name, "sha256": sha256(dest), "size": os.path.getsize(dest),
                      "min_core": core_serial(last), "web": gid in web, "changes": changes,
                      "date": git("show", "-s", "--format=%cI", last)}
    files = {}
    for plat, fname in LAUNCHERS.items():
        p = os.path.join(a.dist, fname)
        if os.path.exists(p) and not a.web_only:
            files[plat] = {"file": fname, "sha256": sha256(p), "size": os.path.getsize(p)}
    manifest = {"format": 1, "channel": a.channel, "build": build_name(), "commit": git("rev-parse", "HEAD"),
                "date": git("show", "-s", "--format=%cI", "HEAD"), "godot": godot,
                "launcher": {"core": core_serial(), "build": build_name(), "files": files}, "games": games}
    with open(os.path.join(a.out, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=1)
    total = sum(g["size"] for g in games.values())
    print(f"channel {a.channel}: {len(games)} games, {total / 1e6:.1f} MB, launcher core {manifest['launcher']['core']}, "
          f"{len(files)} launcher downloads -> {a.out}/manifest.json")


if __name__ == "__main__":
    main()
