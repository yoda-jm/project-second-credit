# Web build: specification

Status: in progress on the `web-build` branch. Goal: play Second Credit in a browser from the project's site, with no
install, hosted for free on GitHub Pages next to the existing site.

## Constraints

- **Hosting: GitHub Pages**, static files only, served under a sub-path (`https://yoda-jm.github.io/project-second-credit/`).
  Pages cannot send custom headers, so no `Cross-Origin-Opener-Policy` / `Cross-Origin-Embedder-Policy`: no
  `SharedArrayBuffer`, so **the single-threaded web template** (`web_nothreads_release.zip`). Godot 4.7 supports it fully;
  audio runs on the main thread (a little choppier under heavy load).
- **Rendering: WebGL 2**, so Godot's **Compatibility** renderer in the browser. Desktop builds keep Forward+ (the project
  setting has a per-platform override: `rendering/renderer/rendering_method.web`). Not available in Compatibility:
  SSAO, SSIL, SSR, SDFGI, volumetric fog, some glow modes and post-processing; games still run, with flatter light.
- **Size**: the whole project imports to about 160 MB. Browsers download the `.pck` before anything shows, so the web
  build ships **a selection of games**, with a budget of about **60 MB** for the first version (the page shows progress).
- **Textures**: desktop browsers decode S3TC/BPTC (the desktop import); the web preset exports that format only.
- **Input**: keyboard, mouse and gamepads work in browsers (gamepads after the first button press). Audio starts after
  the first click or key press (the browser's autoplay rule): the page shows a "click to start" overlay.
- **No paid services**, same licences: the web build is built in CI from the repo, like the desktop releases.

## Design

1. **Renderer override** in `project.godot`: `rendering/renderer/rendering_method.web="gl_compatibility"`.
2. **Export preset "Web"** (`export_presets.cfg`): single-threaded template, S3TC/BPTC textures, the same include
   filter as desktop, and an exclude filter that leaves out the games not in the web selection (plus tests, tools,
   editor add-ons). Output: `build/web/index.html` (+ `.js`, `.wasm`, `.pck`, icons).
3. **Web selection**: a list in one place (`tools/web-games.txt`), used by the export script to write the exclude
   filter. The launcher already reads every game from `GameRegistry`; on the web it **skips games whose scene is not
   in the pack** (`ResourceLoader.exists(scene)`), so the selection needs no second list in GDScript.
   First selection (light scenes that hold up in Compatibility): Tumbletop, Crate Keeper, Nightbite, Inkstorm,
   Hopline. More once each is checked in the browser.
4. **Web-only behaviour** (`OS.has_feature("web")`):
   - Settings: no frame cap fiddling (the browser paces frames), no fullscreen toggle (the page has its own button),
     no "Quit" in the launcher or pause menu (there is nowhere to quit to).
   - A line in the launcher: "More games in the desktop download".
   - Features that read the player's own files (Iron Flags' Zod maps, Muddy Boots' original missions, BDCFF caves)
     stay desktop-only.
5. **The page**: Godot's generated `index.html` with our own shell (`site/play-shell.html` as the export's custom HTML
   shell): the Second Credit look, a progress bar with the size, a click-to-start overlay, a fullscreen button, a
   fallback message when WebGL 2 is missing, and a link back to the site and the downloads.
6. **Site**: `tools/build-site.sh` copies `build/web/` into `build/site/play/` when it exists; the site gets a "Play in
   your browser" button next to the downloads. `pages.yml` fetches Godot and the templates (cached), exports the web
   build, then builds the site.

## Testing

- `tools/build-web.sh`: imports, exports the Web preset into `build/web/`, prints the sizes.
- `tools/serve-web.sh [port]`: serves `build/site/` with Python's `http.server` (static files, no special headers:
  the same conditions as GitHub Pages), under the same sub-path as Pages (`/project-second-credit/`).
- `tools/test-web.sh`: builds the site, serves it, opens `play/` in headless Chrome (WebGL 2 through SwiftShader),
  clicks to start, waits, saves screenshots of the launcher and of each web game's demo, and fails on JavaScript or
  Godot errors in the console.

## Acceptance (first version)

- The launcher and the five selected games run in desktop Chrome and Firefox from a static server, with sound after
  the first click, keyboard and gamepad input, and no console errors.
- The download is under ~60 MB and the page shows its progress.
- Desktop builds are unchanged (Forward+, all games); `tools/test.sh` and `tools/check.sh` pass.

## Later

- **Per-game packs** loaded on demand (`ProjectSettings.load_resource_pack` on a downloaded `.pck`), so every game can be
  on the web without a huge first download.
- A "web quality" pass per game: replace lost Forward+ effects with cheaper ones (baked light, emissive cards, fog
  planes) where a game looks too flat in Compatibility.
- Touch controls (shared with an Android build).
