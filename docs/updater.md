# The launcher, the game packs and updates

Status: in place (desktop and web). Android: not started (see the end).

## What the player sees

- The download is the launcher alone (about 20 MB of core plus the Godot runtime). Every game is on the shelf.
- A game that isn't on the computer says **NOT DOWNLOADED** with its size; floppy disks, clouds and download arrows
  float behind it, and its card picture is dimmed under a big download badge. Enter downloads it (a filling ring on
  the card); Enter again plays it. A `?game=<id>` link (the site) downloads then plays.
- At start the launcher checks the update channel in the background, never waiting for it. It **never installs
  anything by itself**: when something is new, a notice slides in ("NEW: new versions of Fuseflight, Biosurge...
  Press U"), the status pill in the corner says "LATEST · 3 UPDATES · PRESS U", and the cards say **NEW VERSION**.
- Enter on a game with a new version asks: **UPDATE** or **PLAY THIS VERSION**, with what changed.
- **LIBRARY** (menu, or U) lists every game: its state, size and what changed, and DOWNLOAD / UPDATE / CANCEL /
  REMOVE / PLAY per game, **UPDATE ALL**, **DOWNLOAD ALL**, CHECK NOW, and the launcher's own update (UPDATE AND
  RESTART). A game updated since it was last played says UPDATED until then.
- Settings: "Look for updates at start" (on) and "Stable releases only" (off: the **latest** channel is the default).

## How it's built

| Piece | Holds | Size |
|---|---|---|
| Launcher (`tools/export.sh`) | the Godot runtime, `core/`, the add-ons, `core/library/build.json` | 19 MB pack; downloads of 44 MB (Linux), 55 MB (Windows), 78 MB (macOS) |
| Game pack (`tools/export-packs.sh`) | `games/<id>/` only, through the "Pack" export preset | 2 to 26 MB, 211 MB in all |
| Web launcher (`tools/build-web.sh`) | the same core for the browser (Compatibility renderer, single-threaded template) | 19 MB pack |

- `Library` (autoload, `core/library/library.gd`) keeps the downloaded packs in `user://library/` with
  `installed.json`, mounts them at start (`ProjectSettings.load_resource_pack`), fetches the manifest, downloads
  (in the browser through its own `fetch()`, `core/library/web_fetch.gd`: GitHub Pages gzips everything and Godot's
  HTTPRequest there reads bodies by their compressed length),
  checks size and SHA-256, mounts. The rules are pure functions in `core/library/library_catalog.gd` (tested in
  `core/tests/test_library.gd`); the screens are `core/ui/library_ui.gd`.
- Godot 4.7 mounts a pack with its own `class_name` scripts and UIDs at run time: no restart. A game already played
  this session keeps its old scripts loaded, so its update asks for a restart.
- Development runs (editor, `tools/test.sh`, `tools/capture.sh`) have every game in `res://` and never touch the
  network. `--library-preview` fakes a channel to look at every state. `--no-update` and `--demo` skip the check.
- An "all games" build (every game inside the launcher) still works: games found in `res://` at start count as
  installed and can be updated by a pack.

### Rules the build enforces (`core/tests/test_packs.gd`)

- A game uses only `core/` and its own folder (Fruitburrow got its own copies of the Bastion trees, the launcher its
  own gem shader). `core/` never needs a game, except the registry and the campaign packs' lookup.
- Card art lives in `core/ui/cards/`; a game's floating props come from its pack once it's downloaded.

## The channel

`tools/make_manifest.py` writes `manifest.json` and copies each pack as `<id>-<version>.pck`:

```json
{
 "format": 1, "channel": "latest", "build": "m8-flags-171-g10ee5ad", "commit": "...", "godot": "4.7.2",
 "launcher": {"core": 108, "build": "...", "files": {"linux": {"file": "SecondCredit-linux-x86_64.AppImage", "sha256": "...", "size": 0}}},
 "games": {"fuseflight": {"version": "af9e044815", "file": "fuseflight-af9e044815.pck", "sha256": "...", "size": 8300000,
   "min_core": 106, "web": false, "changes": ["Fuseflight: ..."], "date": "..."}}
}
```

- **version**: the git tree of `godot/games/<id>` and the Godot version. Same folder, same version: nobody downloads
  a game again for nothing.
- **core serial**: how many commits changed the launcher's code (`godot/core`, `project.godot`, `addons`, the icon).
  `launcher.core` is the serial of this build; a launcher with a lower one is offered the update.
- **min_core**: the serial when the game last changed. An older launcher was never tested with that version: it
  keeps the game it has and says "NEEDS THE NEW LAUNCHER" for the new one. No manual version bump to forget.
- **changes**: commit subjects that touched the game since the previous manifest (they are captions already).
- **web**: listed in `tools/web-games.txt` (checked in the browser).

### Hosting

- Desktop: GitHub Releases. `latest` channel: `releases/download/latest/manifest.json` (the rolling pre-release);
  `stable`: `releases/latest/download/manifest.json` (GitHub's newest full release, i.e. the newest tag). Files
  are found beside the manifest. No GitHub API (60 requests an hour per IP).
- `tools/publish-channel.sh` keeps the `latest` release (its tag moves), uploads only packs it doesn't have,
  replaces the launchers, uploads the manifest last, and removes packs listed neither now nor in the previous
  manifest.
- Web: GitHub Pages, `play/` (launcher) and `play/packs/` (manifest and the web games' packs). Release downloads
  have no CORS headers, Pages has `Access-Control-Allow-Origin: *`. The browser keeps downloaded packs in
  IndexedDB (`user://`).
- `release.yml`: packs, launchers, web build, then `tools/test-library.sh` (an exported launcher downloads, checks,
  mounts and runs every game from a local channel, again offline, refuses damaged files, and replaces itself), and
  only then publishes; then the site (`pages.yml`, reusable) takes the web build from the release.

## The launcher's own update

| Platform | How |
|---|---|
| Linux AppImage | download, check, write beside `$APPIMAGE`, `chmod +x`, rename over it, start it, quit (tested) |
| Windows | unzip the `.exe` beside the running one, rename the running one to `.old` (allowed), the new one in its place; `.old` goes at the next start |
| macOS | `ditto` unzips the app beside the running one, the running one becomes `.old`, the new one takes its place, `open -n`; not from a translocated (never moved) app |
| Web | "RELOAD THE PAGE" |
| Anything else | the library says a new launcher is out and opens the download page |

The restart repeats the launcher's arguments plus `--relaunched`. Windows and macOS are written but not yet tried on
those systems: try them before relying on them.

## Testing

- `tools/test.sh -a res://core/tests`: the rules, the dependency check, the launcher.
- `tools/test-library.sh [id ...]`: the end-to-end check above (about 10 minutes for every game).
- `tools/test-web.sh [--no-build] [id ...]`: builds the web version and the site, serves them like Pages and plays
  the launcher and each web game in headless Chrome (each downloads its pack, the first one comes back from the
  browser's storage), screenshots in `build/web-test/`.
- `CAPTURE_ARGS="--library-preview --open-library" tools/capture.sh -s res://core/ui/launcher.tscn`: the screens.

## Android (later)

Packs need no change (textures aren't VRAM-compressed, so one pack serves desktop, web and phones). The APK would be
the launcher alone (~50 MB) and download games like the desktop. The app itself can't update itself outside a store:
distribute it on GitHub Releases with Obtainium or F-Droid; the library would only say a new version is out. Touch
controls and per-game renderer checks are the real work.
