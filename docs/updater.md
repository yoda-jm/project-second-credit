# Updates and on-demand games: specification

Status: proposal (branch `updater-spec`). A readable version with diagrams is the private page linked from
`CLAUDE.local.md`.

## Goal

- The launcher checks GitHub for a newer build at start, downloads it, and relaunches itself.
- Every game stays listed in the launcher. A game that was never downloaded shows its size and downloads
  when it's first picked. Games that are installed update on their own, and the launcher says which ones changed.
- The same mechanism serves the web build (all games, without a huge first download) and an Android build.

## Today

- `release.yml` exports one 225-258 MB file per OS (Godot runtime + every game in one embedded `.pck`) and
  deletes and recreates the rolling `latest` pre-release on every push to `main`.
- The web build (`web-build` branch, `docs/web.md`) ships five games in one `.pck` to keep it under ~60 MB.
  Its "Later" section already asks for per-game packs.

## Design: one runtime, one core pack, one pack per game

| Layer | Holds | Size | Changes when |
|---|---|---|---|
| Runtime | Godot export template (exe) | 70-110 MB (25-35 MB zipped) | Godot version changes |
| Core pack | `core/`, launcher, settings, fonts, cards, a few launcher props | ~16 MB | launcher or shared code changes, a game is added |
| Game pack `<id>.pck` | `games/<id>/**` only | 3-26 MB | that game's folder changes |

The desktop runtime and core pack ship together as today's single file (embedded pack), so the
"launcher update" is a whole-file replacement. Games are separate `.pck` files mounted with
`ProjectSettings.load_resource_pack()` just before `LoadingScreen.go()` loads the scene.

**Spike (Godot 4.7.2, done):** a core pack exported without `games/*` and a game pack with two
`class_name` scripts, a texture referenced by UID and a scene. After mounting, `get_global_class_list()`
contains the game's classes, `ResourceUID.has_id()` knows its UIDs, and the scene loads and runs. No
restart and no cache tricks needed.

### Rules the build enforces

- A game references only `core/` and its own folder (a check script in CI). Today one breaks this:
  Fruitburrow loads decor from `games/bastion/art/models/`; move it to `core/` or copy it.
- The launcher's floating props and card art must live in `core/` (the launcher already skips missing props).
- `core/api.txt` holds an integer, `CORE_API`, raised by hand when a change in `core/` breaks old game packs
  (HUD kit, story cards, pack chooser, settings). Each game pack records the API it was built for.
- Packs are built with the same Godot version as the runtime (tokenized GDScript and resource formats).

## The channel manifest

One JSON file per channel (`stable`, `latest`), published last so a channel switches in one step:

```json
{
  "channel": "latest", "build": "m35-17-g396b2d0", "commit": "396b2d0", "date": "2026-10-06T00:30:00Z",
  "godot": "4.7.2", "core_api": 3,
  "launcher": {
    "linux":   {"url": ".../SecondCredit-linux-x86_64.AppImage", "sha256": "...", "size": 61000000},
    "windows": {"url": "...", "sha256": "...", "size": 0},
    "macos":   {"url": "...", "sha256": "...", "size": 0},
    "android": {"url": "...", "sha256": "...", "size": 0}
  },
  "games": {
    "fuseflight": {
      "version": "a1b2c3d4", "core_api": 3, "title": "Fuseflight",
      "desktop": {"url": ".../fuseflight-a1b2c3d4.pck", "sha256": "...", "size": 14100000},
      "mobile":  {"url": ".../fuseflight-a1b2c3d4-etc2.pck", "sha256": "...", "size": 15800000},
      "web": true,
      "changes": ["Fuseflight: walkers take wing after the third bomb", "..."]
    }
  }
}
```

- `version` = first 8 hex of the git tree hash of `godot/games/<id>` mixed with the Godot version and
  `CORE_API`. Same folder, same version: unchanged games are never downloaded again.
- `changes` = commit subjects that touched the folder since the previous version (they are written as
  captions already), shown under "What's new".
- `web` = the game is checked in the Compatibility renderer and may appear in the browser.

## Hosting (free, no API calls)

- **Manifest and web packs: GitHub Pages** (`/channel/<name>/manifest.json`, `/packs/<id>-<version>.pck`).
  Pages answers with `Access-Control-Allow-Origin: *`; the browser can fetch from it.
- **Desktop and Android files: GitHub Releases.** One long-lived release per channel; assets are named
  with their version and uploaded only when new (`gh release upload`), old ones pruned after two versions.
  Stop deleting and recreating `latest`: links would break mid-download.
- Release downloads redirect to `release-assets.githubusercontent.com` **without CORS headers** (checked), so
  the web build can't use them; hence Pages for the web.
- No GitHub API (60 requests an hour per IP unauthenticated): only plain file URLs.
- Pages limits: 1 GB site, 100 GB a month soft bandwidth. One version of every desktop pack is about 300 MB.

## Launcher behaviour

### At start

1. Show the launcher straight away from what is installed (never wait for the network).
2. In the background: fetch the manifest (`If-None-Match`, 5 s timeout). Offline: nothing happens.
3. Newer launcher: download, verify, show "Update ready: restart" (or restart at once on the
   next return to the launcher if updates are set to automatic). Never restart under a running game.
4. Installed games with a new version: download in the background, one at a time, smallest first.
5. A toast when done: "3 games updated: Fuseflight, Biosurge, Four Torches". Their cards get an
   "UPDATED" chip until played; the card shows the `changes` lines.

### Card states

| State | Card shows | Enter does |
|---|---|---|
| Installed | as today | play |
| Not downloaded | size, "DOWNLOAD" | download with progress on the card, then play |
| Downloading | progress bar, MB of MB | nothing (Esc cancels) |
| Update ready | "UPDATED" chip | play the new version |
| Needs newer launcher | "UPDATE THE LAUNCHER" | start the launcher update |
| Offline, not downloaded | greyed, "needs a connection" | nothing |

### Files

- `user://packs/<id>-<version>.pck` and `user://packs/installed.json` (id, version, sha256, date, played).
- Download to `.part`, check size and SHA-256 (`HashingContext`), rename, update `installed.json`, delete
  the old version. A failed check deletes the file and retries once.
- A pack can't be unmounted: a game already played this session switches version at the next start.
- Saves and settings stay in `user://` as today; game packs never write there except their own saves.
- A "Downloads" page in Settings: installed size per game, remove a game, "update now".

### Settings

- Updates: **Automatic** (default) / Ask / Off.
- Channel: **Stable** (tagged releases, default for players) / Latest (every push to `main`).

### Captures, tests and demos

`--no-update` and every capture/test path (`tools/capture.sh`, `tools/test.sh`, `--demo`) disable the
network entirely, so construction movies stay deterministic and CI never downloads.

## Launcher self-update per platform

| Platform | Replace | Relaunch |
|---|---|---|
| Linux AppImage | `$APPIMAGE` path: download beside it, `chmod +x`, `rename()` over it (atomic, the running copy stays mapped) | `OS.create_process($APPIMAGE, args)` then quit |
| Windows | rename running `SecondCredit.exe` to `.old`, write the new one, delete `.old` at next start | same |
| macOS | replace `Second Credit.app` contents; if it runs from a translocated read-only path (not moved to Applications), say so and open the download page | `open -n` the bundle |
| Not writable (distro package, read-only folder) | don't; show "Version X is out" with a link | - |

Downloads made by our own process carry no quarantine flag on macOS. All three keep a `--relaunched` argument so
a failed update can't loop: if the new file fails to start twice, the old one is restored.

## Builds

- `tools/export-packs.sh`: one import, then `--export-pack` per game with a preset whose exclude filter is
  rewritten (the same trick as `tools/build-web.sh`), plus the core pack. Writes `build/packs/` and the manifest.
- Desktop builds keep an **"all games" download** (packs in a `packs/` folder beside the exe, read-only,
  treated as installed and updated into `user://`): for offline players, archives and stores. The plain
  launcher download becomes about 30-60 MB.
- `release.yml`: build packs once (Linux runner), export the three launchers, upload new assets, then the
  manifest. `pages.yml`: copy the current packs and manifests into the site.

## Web build

- The page loads runtime + core pack (~25 MB instead of ~60 MB for five games). Every game whose manifest
  entry says `web: true` is listed; picking one downloads its pack from Pages with `HTTPRequest`, stores
  it in `user://` (IndexedDB, survives visits) and mounts it.
- Desktop packs serve the browser as they are (S3TC/BPTC textures, same as the web preset); no separate web packs.
- No launcher self-update: the page is always the latest. File names carry the version so caches never
  serve a stale core.
- "Updated since your last visit" uses the same toast.
- Replaces `tools/web-games.txt` with the manifest's `web` flag (coordinate with the `web-build` branch).

## Android

- Packs: a second flavor with ETC2/ASTC textures (`-etc2.pck`), same manifest. Game data lands in internal
  storage; `load_resource_pack` works there.
- APK: about 50 MB (arm64, core only) instead of 300+ MB with every game.
- **App updates are not in-app.** No paid Play account (and Play forbids self-updates), so distribute the APK
  on GitHub Releases, with Obtainium or F-Droid for app updates. The launcher only says "A new version is out"
  and opens the release page. Packs update in-app as on desktop. F-Droid may flag downloaded packs (they
  hold compiled scripts): ship an "all games" APK flavor there.
- Still needed before Android is real: touch controls, the Mobile or Compatibility renderer per game,
  performance checks.

## Security

- HTTPS only, SHA-256 per file from the manifest.
- Phase 2: sign the manifest (Godot `Crypto.sign` with an RSA key in a GitHub secret; public key in the
  core pack) so a compromised mirror can't serve code. A compromised GitHub account could change the
  source anyway, so this is defence in depth.
- No telemetry: only GET requests, no identifiers.

## Phases (small commits, each runnable)

1. **Split the build**: dependency check, `export-packs.sh`, "all games" builds mount packs from `packs/`
   beside the exe. Same player experience. Test: every game starts from its pack.
2. **Manifest and channels** in CI; stop recreating `latest`. Test: manifest schema, versions stable across
   two builds of the same tree.
3. **Launcher states and downloads**: card states, `installed.json`, verify, toast. Test against a local
   channel served by `python3 -m http.server` (fake updates, a corrupt file, offline).
4. **Self-update** per desktop OS, with rollback.
5. **Web on demand**: all `web: true` games in the browser.
6. **Android**: mobile packs, APK, touch controls (a project of its own).

## Open questions for the owner

- Default channel for players: Stable (recommended) or Latest?
- Keep the "all games" desktop download? (Recommended: yes, for offline use.)
- Updates on by default without asking? (Recommended: yes, with a toast.)
