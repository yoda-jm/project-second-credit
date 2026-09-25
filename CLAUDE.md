# Second Credit: context for Claude

Free, open-source remakes of simple 80s and 90s games with modern, polished presentation (Pac-Man Championship
Edition is the reference). Claude Code does most of the work. Read `docs/` before proposing anything; the
decisions below are settled unless the owner reopens them.

## Settled decisions

- **Build order** ([docs/roadmap.md](docs/roadmap.md)): Boulder Dash → Fruity Frank → Alley Cat → Winter Games →
  Cannon Fodder → Double Dragon → Z. It's a *stack ladder*: game 1 must look and play great on the simplest
  pipeline, and each later game adds a few new capabilities. We build the stack while building the games.
  There is no throwaway prototype.
- **Maps:** if maps or levels exist for a game, we **must** be compatible (BDCFF for Boulder Dash, Open Fodder
  and original files for Cannon Fodder, Zod Engine maps for Z). The original graphics don't matter; ours are new.
  See [docs/level-packs.md](docs/level-packs.md).
- **Stack** ([docs/stack.md](docs/stack.md)): Godot 4 (GDScript), Blender + MCP, CC0 asset kits, jsfxr and
  synthesised sound, MIDI or tracker music rendered with FluidSynth, and ACE-Step or small local image models.
  **No paid services**; only the existing Claude and ChatGPT accounts.
- **Licences (decided):** code GPL-3.0-or-later (`LICENSE`), assets and levels CC BY-SA 4.0 (`LICENSES/`).
  Third-party inputs must be CC0 or CC-BY. See [docs/legal.md](docs/legal.md) for tools to avoid.

## Hard rules

- Never commit original names as titles, or original sprites, audio, code or **level data**. Importers read
  the player's own files locally instead.
- Never commit `catalog/shots/` or `catalog/index.html`: they hold fair-use screenshots (already git-ignored).
- Keep personal information (hardware, accounts, names, paths) out of committed files. Private context lives in
  `CLAUDE.local.md` (git-ignored).
- Prefer tools and models that fit about 6 GB of VRAM for anything run locally.
- Record provenance (tool, prompt, licence) for every generated or third-party asset.

## Working style

- The owner writes in English, sometimes French, and prefers concise answers with a clear recommendation.
- Descriptions in `catalog/desc_*.json` and `docs/games/` were drafted from memory. Verify numbers (level
  counts, timings) against the originals in an emulator before relying on them.

## Repo map

- Remote: https://github.com/yoda-jm/project-second-credit (branch `main`)
- `docs/`: vision, roadmap, level packs, stack, setup, legal, the readable candidate list (`catalog.md`) and a
  brief per game (`docs/games/`)
- `godot/`: the single Godot project (shared core plus one folder per game); vendored add-ons in `godot/addons/`,
  the capture scene in `godot/tools/capture/`
- `tools/`: `fetch-tools.sh` (portable tools), `test.sh`, `capture.sh`
- `research/`: `stack-report.md` (full tool research with sources, including rejected paid options) and
  `existing_{A,B,C}.json` (survey of existing free versions for all 49 catalog games)
- `catalog/`: the candidate catalog page. `python3 build.py` (run in `catalog/`) builds `index.html`.
  `python3 catalog/tools/make_briefs.py` (run from the repo root) regenerates `docs/games/` and `docs/catalog.md`. Data: `games.json`,
  `desc_*.json`, `map_compat.json`, `shots_meta.json`.

## Next steps

1. Setup is in [docs/setup.md](docs/setup.md) (portable tools in `.tools/` via `tools/fetch-tools.sh`; prepend
   `.tools/bin` to `PATH`). The Blender MCP is registered. Still to do: connect the Godot MCP from the editor
   dock (`godot --path godot -e`, Configure, local scope).
2. Check your work with `tools/test.sh` (GdUnit4) and `tools/capture.sh` (PNG screenshots).
3. Game 1: BDCFF parser + exact Boulder Dash rules (reference: GDash, MIT), then the presentation.
