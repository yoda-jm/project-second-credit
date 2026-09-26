# Second Credit: context for Claude

Free, open-source remakes of simple 80s and 90s games with modern, polished presentation (Pac-Man Championship
Edition is the reference). Claude Code does most of the work. Read `docs/` before proposing anything; the
decisions below are settled unless the owner reopens them.

## Settled decisions

- **Build order** ([docs/roadmap.md](docs/roadmap.md)): Boulder Dash (*Glimmerdeep*) → Rampart → Fruity Frank →
  Alley Cat → Winter Games → Cannon Fodder → Double Dragon → Z. (Rampart moved to game 2 at the owner's request.) It's a *stack ladder*: game 1 must look and play great on the simplest
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

- **Construction movie:** the owner will make a step-by-step movie of the build from git history. Keep commits
  small, tested and runnable. The main scene must always show the current state, with a demo mode (recorded input,
  fixed seeds, fixed fps) so `tools/capture.sh` shows movement without a player. Tag milestones (`m1-...`) and
  write commit subjects that work as captions. Don't rewrite pushed history.
- **Long agent runs:** keep the Godot editor and Blender closed. Edit files and check with `tools/test.sh` and
  `tools/capture.sh`. Use the Godot and Blender MCP only when the owner opens those apps for interactive work.

## Repo map

- Remote: https://github.com/yoda-jm/project-second-credit (branch `main`)
- `docs/`: vision, roadmap, level packs, stack, setup, legal, the readable candidate list (`catalog.md`) and a
  brief per game (`docs/games/`)
- `godot/`: the single Godot project: `core/` (launcher, loading screen, settings autoload, pause menu, fonts,
  UI sounds, shared PBR textures and particle materials) plus one
  folder per game in `games/`; vendored add-ons in `godot/addons/`,
  the capture scene in `godot/tools/capture/`
- `tools/`: `fetch-tools.sh` (portable tools), `test.sh`, `check.sh`, `capture.sh`, `movie_clip.sh <game>` and
  `make_movie.py <game>` (construction movie per game), `stats.py` (tokens and time), `blender/` and `audio/`
  (asset generators)
- `research/`: `stack-report.md` (full tool research with sources, including rejected paid options) and
  `existing_{A,B,C}.json` (survey of existing free versions for the first 49 catalog games)
- `catalog/`: the candidate catalog page. `python3 build.py` (run in `catalog/`) builds `index.html`.
  `python3 catalog/tools/make_briefs.py` (run from the repo root) regenerates `docs/games/` and `docs/catalog.md`. Data: `games.json`,
  `desc_*.json`, `map_compat.json`, `shots_meta.json`.

## Next steps

1. Setup is in [docs/setup.md](docs/setup.md). Check work with `tools/check.sh`, `tools/test.sh` and
   `tools/capture.sh` (GPU captures if `.tools/capture.conf` has `CAPTURE_GPU=1`).
2. Game 1, **Glimmerdeep** (`godot/games/glimmerdeep/`): playable. Engine exact to GDash (all 306 replays,
   `GLIMMERDEEP_REFERENCE=1 tools/test.sh`). The Descent campaign (8 caves, `packs/second-credit/`, `--descent=N` for captures) is in. Open items: the cave-pack browser and
   downloads, the level editor, an optional "responsive timing".
3. Game 2, **Bastion Coast** (working title, `godot/games/bastion/`): playable (tag `m2-bastion`), with The
   Coastline campaign (5 islands, `packs/the-coastline/`, `rounds=N` per map; `--endless` for the old survival).
   Open items: grunts landing from ships, 2-3 player versus, checking timings against the arcade in MAME.
4. Game 3, **Fruitburrow** (working title, `godot/games/fruitburrow/`): playable, with the first rigged character
   (`tools/blender/fruitburrow_gardener.py`). Rules are from memory: check speeds, scoring and the ball against the
   original in an emulator. Open items: more gardens, the day-to-dusk cycle across a longer pack.
5. CI (`.github/workflows/`: tests, Linux/Windows/macOS builds, a rolling `latest` release) and the website
   (`site/`, deployed by `pages.yml`) exist: refresh `site/` whenever a game changes a lot.
6. Game 4, **Whisker Alley** (working title, `godot/games/whisker/`): playable. A platformer engine
   (`engine/platform_body.gd`), the alley hub and five rooms (`engine/rooms/`), rigged cat, lady cat and bulldog
   (`tools/blender/whisker_animals.py`). `--room=N` (user argument) starts a capture inside a room. Rules from
   memory: check against the original.
7. Game 5, **Frostpeak Games** (working title, `godot/games/frostpeak/`): playable with speed skating and the
   ski jump, 1-4 players in hot seat, CPU rivals, podium and medal table. `--event=N` starts a capture at an event.
   Open items: biathlon, bobsled, hot dog, figure skating; the opening ceremony.
8. Game 6, **Muddy Boots** (working title, `godot/games/boots/`): playable campaign of three missions; squad
   orders, grenades, rockets, huts, hostages, mines; importer for the original map files (`engine/cf_import.gd`).
   Campaign packs (`packs/`: First Tour, The Long Monsoon) with story cards and a chooser (shared: `core/packs/`,
   `core/ui/story_card.gd`, `core/ui/pack_chooser.gd`). Open items: vehicles, helicopters, the recruits hill, a
   menu to load the player's original missions.
9. Game 7, **Neon Knuckles** (working title, `godot/games/knuckles/`): playable, three stages (street, docks,
   rooftops) in `stages/*.brawl`, 1-2 players, grabs, throws, weapons, a boss. `--stage=N` starts a capture at a
   stage. Open items: more enemy moves, a stage 4, checking timings against the arcade in MAME.
   The launcher browses games by style (chips, Tab or Q and E).
10. Construction movies: `tools/movie_history.sh <game>` records a clip per commit (worktrees), then
   `tools/make_movie.py <game>`. GPU recording needs the monitor awake (a sleeping display stalls it): still to do
   for Fruitburrow through Iron Flags.
11. Game 8, **Iron Flags** (working title, `godot/games/flags/`): playable RTS, three campaign maps
   (`packs/first-war/`, The First War, with story cards; maps generated by `tools/flags_maps.py`), territories, factories, robots, vehicles, guns, an AI
   general (`demo/flags_ai.gd`, also the demo). `--map=N`, `--zod=/path/x.map` (a Zod Engine map from the player's
   files). Open items: fog of war, APC transport, a menu to pick Zod maps.
12. Game 9, **Blastyard** (working title, Bomberman-like, `godot/games/blastyard/`): battle for 1-4 players with bots,
   solo stages, sudden death; arenas in `maps/*.blast`. Glimmerdeep has a two-player race (F2); Bastion Coast versus is
   done (F2).
13. Game 10, **Ingot Run** (Lode Runner-like, `godot/games/ingot/`): five levels in the free remakes' text format
   (`levels/*.lvl`, `--level=N`); guards hunt by shortest path; the bot proves every level clearable. Game 11,
   **Crate Keeper** (Sokoban-like, `godot/games/crates/`): reads standard `.xsb` collections; our puzzles carry par and a
   solution (made by a solver script in the scratchpad history), undo/redo, stars. Characters on the new
   `humanoid.py` rig (26 bones, smooth skin) and `creature_kit.py` (animals).
14. Game 12, **Nightbite** (Pac-Man-like, `godot/games/nightbite/`): neon maze chase, `mazes/*.maze` (our format,
   mirrored halves checked for dead ends by a scratchpad script), four spirit temperaments, autopilot.
15. Game 13, **Prism Breaker** (Arkanoid-like, `godot/games/prism/`): eight walls in `levels/*.wall` (our format) or an
   LBreakout2 set (`--walls=<file>`), capsules (wide, laser, catch, slow, multi, life, break), drones, autopilot.
16. Game 14, **Inkstorm** (Qix-like, `godot/games/inkstorm/`): claim 75% of the map; land rises as a painted relief
   (`shaders/ink_board.gdshader`), one storm then two, sparks and the fuse, slow lines score double; `--stage=N`.
17. Game 15, **Mossfolk** (Lemmings-like, `godot/games/mossfolk/`): pixel terrain, eight skills, five levels in
   `levels/*.moss` (our text format, each with a recorded solution the demo plays and a test checks); `--level=N`.
   Open item: an importer for the player's original level files (it needs their graphics sets, read locally).
18. Game 16, **Hopline** (Frogger-like, `godot/games/hopline/`): lanes move as pure functions of time, so the
   autopilot plans through time (a beam search); diving turtles, a crocodile in the bays, fly and lady-frog bonuses.
19. Next: the shared campaign/mod system ([docs/level-packs.md](docs/level-packs.md)), the level editors, and
   polish passes over every game.
