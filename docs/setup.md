# Development setup

How to get from a fresh clone to a working environment, by hand or with an agent. Everything is free and
open-licensed ([stack.md](stack.md) explains the choices). Linux x86-64 is the tested platform.

## 1. System packages

These need the system package manager. Install them yourself; they need root.

| Tool | Why | Debian / Ubuntu | Arch | Gentoo |
|---|---|---|---|---|
| git, curl, unzip, xz, python3 | fetch script | `git curl unzip xz-utils python3` | `git curl unzip xz python` | usually present |
| Xvfb | headless capture for the AI test loop | `xvfb` | `xorg-server-xvfb` | `x11-base/xorg-server` with USE `xvfb` |
| FluidSynth + FluidR3 SoundFont | renders MIDI music | `fluidsynth fluid-soundfont-gm` | `fluidsynth soundfont-fluid` | `media-sound/fluidsynth media-sound/fluid-soundfont` |
| VICE | C64 emulator, reference captures for game 1 | `vice` | `vice` | `app-emulation/vice` |

Package names are the usual ones; check them against your distribution. On Gentoo, a set is convenient: put the
four atoms in `/etc/portage/sets/second-credit`, add `x11-base/xorg-server xvfb` to `package.use`, then run
`emerge --ask --newuse @second-credit`.

Emulators for later games (MAME, FS-UAE or Amiberry, DOSBox Staging) come when those games start.

## 2. Portable tools

```bash
tools/fetch-tools.sh
export PATH="$PWD/.tools/bin:$PATH"     # add to your shell profile, or run per session
```

The script downloads fixed versions into `.tools/` (git-ignored, about 1.7 GB). Running it again does nothing
once everything is there. To upgrade, change the version variables at the top of the script.

| Tool | Version | Source | Licence |
|---|---|---|---|
| Godot | 4.7.2 | github.com/godotengine/godot releases | MIT |
| Blender | 5.2.2 LTS | download.blender.org | GPL-2.0-or-later |
| Blender Lab MCP (add-on + `blender-mcp` server) | 1.0.3 | projects.blender.org/lab/blender_mcp | GPL-3.0-or-later |
| gh (GitHub CLI) | 2.101.0 | github.com/cli/cli releases | MIT |
| git-lfs | 3.8.0 | github.com/git-lfs/git-lfs releases | MIT |
| uv | 0.12.19 | github.com/astral-sh/uv releases | MIT / Apache-2.0 |

Nothing is written outside the repo:
- Godot runs in self-contained mode (a `._sc_` file next to the binary), so editor settings stay in `.tools/`.
- Blender runs in portable mode (a `portable/` folder next to the binary), so preferences and add-ons stay in `.tools/`.
- uv keeps its cache and Python builds in `.tools/uv-cache` and `.tools/uv-python`.

The script also installs the Blender MCP add-on into the portable Blender, turns on its auto-start, and turns
on Blender's "online access" setting. The add-on needs that setting to open its local socket (port 9876).

## 3. Connect Claude Code

Register the Blender MCP once per clone, from the repo root. Local scope keeps absolute paths out of the repo:

```bash
claude mcp add --scope local blender -- "$PWD/.tools/blender-mcp-venv/bin/blender-mcp"
```

Then start Blender (`blender`, where the add-on auto-starts) or run it headless with `blender -b --command blender_mcp`.
`claude mcp list` should show `blender ... ✔ Connected`.

**Godot MCP ([hi-godot/godot-ai](https://github.com/hi-godot/godot-ai), MIT).** The editor plugin is vendored
in `godot/addons/godot_ai/`. Open the project in the editor (`godot --path godot -e`), then in the Godot AI dock
use **Configure** for Claude Code. It registers a `godot-ai attach` command. It needs the editor to be running,
and `uvx`, which the wrapper provides. Choose the `local` scope in its settings, so the absolute path
doesn't land in a committed file.

If the dock shows no **Configure** button, check that ports 8000 (its server) and 9500 (editor WebSocket) are
free with `ss -ltn`. To move them, close the editor and set `godot_ai/http_port` and `godot_ai/ws_port` in
`.tools/godot-*/editor_data/editor_settings-*.tres`. Setting `godot_ai/mcp_client_scope = "local"` there
also makes Configure use local scope.

Telemetry is off: the `.tools/bin/godot` wrapper exports `GODOT_AI_DISABLE_TELEMETRY=true` (it also puts
`.tools/bin` on `PATH` for `uvx` and keeps uv's cache in `.tools/`), and the script
sets the `godot_ai/telemetry_enabled` editor setting to false (once the editor has created its settings file,
so run the script once more after the first editor launch).

## 4. Tests and screenshots

The Godot project is `godot/` (one project: the shared core plus a folder per game). Two scripts let a person
or an agent check the work without opening the editor:

```bash
tools/test.sh                       # GdUnit4 tests in godot/tests (exit code 0 = pass); reports in godot/reports/
tools/capture.sh -f 120 -e 30       # run the main scene for 2 s and keep 4 PNGs in captures/<timestamp>/
tools/capture.sh -r 960x540         # smaller frames, quicker to look at
tools/capture.sh -s res://boot/boot.tscn --gpu   # real GPU and Forward+ renderer (opens a window)
```

`capture.sh` runs the scene inside `godot/tools/capture/capture.tscn`, which saves only the requested frames
(a 2-second capture takes about 4 s). Both scripts use a private Xvfb display when Xvfb is installed. There, Godot uses software OpenGL (the Compatibility
renderer). It is enough to check layout and logic, but it doesn't show Forward+ effects such as glow, SDFGI or
volumetrics, so use `--gpu` for those. Without Xvfb, tests run headless, where input simulation doesn't work.

## 5. Check

```bash
godot --version && blender --version | head -1 && gh --version | head -1 && git lfs version && uv --version
command -v Xvfb fluidsynth x64sc
claude mcp list
tools/test.sh && tools/capture.sh
```

## For agents

An agent working from a fresh clone should:
1. Run `tools/fetch-tools.sh` and prepend `.tools/bin` to `PATH` in every shell command.
2. Check the system packages with `command -v Xvfb fluidsynth x64sc`. If any are missing, ask the owner to
   install them (step 1 needs root). Do not try to install them yourself.
3. Register the Blender MCP with the command in step 3, then ask the user to restart Claude Code so the new
   server loads.
4. Check your work with `tools/test.sh` and `tools/capture.sh`, then read the PNGs it lists.
5. Never commit `.tools/`, tokens, or absolute paths. Keep MCP registration in local scope.
