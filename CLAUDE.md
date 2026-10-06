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
7. Game 5, **Frostpeak Games** (working title, `godot/games/frostpeak/`): playable with speed skating, the ski jump,
   the biathlon sprint and the four-man bobsled (push start, banked curves, brake, crash card), 1-4 players in hot seat, CPU rivals, podium and medal table, and a practice menu for any
   single event. One continuous camera (`view3d/jump_camera.gd`, flights in `camera_flight.gd`), a TV replay of each
   jump (`view3d/replay.gd`). `--event=N` starts a capture at an event, `--practice` at the menu. Open items: the two-man
   bob, hot dog, figure skating; a steady 60 fps (bob and biathlon run about 55 at 1080p); the opening ceremony; the biathlon scope overlay wants polish.
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
19. Game 17, **Slipfloe** (Pengo-like, `godot/games/slipfloe/`): a maze of ice generated per stage, sliding and
   shattering blocks, eggs, wall shakes, three gem blocks; the autopilot looks for blocks with mites in their lane.
20. Game 18, **Fizzlings** (Bubble Bobble-like, `godot/games/fizzlings/`): one or two heroes (W/F joins), six
   toybox levels in `levels/*.fizz` (32 x 26 text grids), bubble chains, treats, hurry and the ghost, two autopilots.
21. Game 19, **Relic Run** (Rick Dangerous-like, `godot/games/relic/`): flip-screen temple levels in
   `levels/*.relic` (screens of 20 x 12 tiles), spikes, darts, the boulder, crushers, pistol and dynamite; each level
   carries a route the demo plays and a test checks. `--level=N`.
22. Game 20, **Henhouse Heist** (Chuckie Egg-like, `godot/games/henhouse/`): three farm levels in `levels/*.hen`
   (32 x 26), ladders, lifts, grain that stops the clock, wandering hens, the goose; the autopilot plans on a graph of
   walks, climbs, drops and jumps.
23. Owner feedback pass (2026-09-27): Prism Breaker became a 3D neon arena (grid tunnel, refractive bricks, ball
   lights); Mossfolk a solid 3D rock slab (`view3d/moss_slab.gd`) with a directed camera, drag to pan and wheel to
   zoom; Hopline got a following camera, afternoon/sunset/night stages (`--stage=N`) and a canal shader with wakes;
   Fizzlings gold-glowing full bubbles, caustics and camera punches; Inkstorm draws by stepping off the edge (shift for
   slow); Ingot Run catches ladders easily; Blastyard fast-forwards once the players are out; Whisker Alley opens the
   least-played room and its bird flies freely. Henhouse Heist still wants the same visual pass. Frostpeak's ski jump is a real
   large hill (K 120, HS 134; `engine/events/ski_hill.gd` shared by rules and view), with an alpine valley
   (`view3d/valley.gd`, `tools/blender/frostpeak_valley.py`) and camera flights that never pass through anything
   (`view3d/camera_flight.gd`); its frame rate is still to be checked on the GPU (about 12M triangles, culled in cells).
24. Game 21, **Deep Breath** (Manic Miner-like, `godot/games/deepbreath/`): single-screen caverns (32 x 16) in
   `levels/caverns.deep` (made by a scratchpad script), air, keys, the lift, conveyors, crumbling floors, guardians on
   patrol; each cavern carries a route the demo plays and a test checks. `--level=N`.
25. Game 22, **Tumbletop** (Q*bert-like, `godot/games/tumbletop/`): a 28-cube pyramid, four painting rules cycling
   by level (one step, two steps, and both with undo), red/green/purple balls, the serpent lured off cloud-discs,
   imps undoing colours; the autopilot plans safe paths (Dijkstra) and a test checks it clears each rule. `--level=N`.
26. Game 23, **Pop Voyage** (Pang-like, `godot/games/popvoyage/`): eight stages in `stages/voyage.pop` (our format:
   balloons, blocks), four balloon sizes, items, the clock; a look-ahead autopilot (a test checks it clears every
   stage); a landmark diorama per stage (`view3d/pop_backdrop.gd`, `tools/blender/popvoyage_backdrops.py`). `--level=N`.
27. Game 24, **Jelly Spike** (Blobby Volley-like, `godot/games/jellyspike/`): blob volleyball, the three-touch rule
   (reset when the ball crosses), rally points to 15 by two; a CPU that reads the ball now and then with aim noise;
   F2 or `--versus` for two players; the beach diorama (`view3d/spike_beach.gd`) cycles noon, sunset and night.
28. Game 25, **Nova Wardens** (Space Invaders-like, `godot/games/novawardens/`): the classic rules in the arcade's
   224 x 256 pixel space (ripple march, bombs, the mothership's 23rd shot, pixel shields shown as voxels); an
   autopilot that leads its targets; the night coast (`view3d/nova_backdrop.gd`) with `alarm()` as the fleet descends.
29. Game 26, **Lantern Links** (mini-golf, after Mini-Putt and Zany Golf, `godot/games/lanternlinks/`): nine holes in
   `courses/lantern_garden.links` (our text format: cells, heights, ramps, bumps, gadgets; spec in
   `docs/games/lanternlinks.md`), arcade 2.5D ball physics (`engine/links_physics.gd`), windmill, loop, jump, pipes,
   bumpers, movers, a turnstile; 1-4 seats, any the CPU (`demo/links_bot.gd`, plans on a worker thread); golden hour
   to night across the round. `--hole=N`, `--players=N`.
30. Game 27, **Marble Drift** (Marble Madness-like, `godot/games/marbledrift/`): a marble on height-field courses
   (`courses/courses.drift`, made by `tools/marble_courses.py` from primitives), flights and shattering falls, glass and
   rough floors, acid, a steelie and hoppers, checkpoints, time carried over; screen-relative controls and a mouse
   trackball; a sky per course (`view3d/drift_sky.gd`). `--level=N`.
31. Game 28, **Fuseflight** (Bomb Jack-like, `godot/games/fuseflight/`): leap, glide and collect the fireworks on
   five festival stages (`stages/festival.fuse`), the lit fuse to follow, walkers that take wing, orbs, the power star,
   B and E letters; a backdrop per stage (`view3d/fuse_backdrop.gd`); the autopilot looks ahead on copies of the
   engine (`demo/fuse_bot.gd`). `--level=N`.
32. Game 29, **Brassflow** (Pipe Mania-like, `godot/games/brassflow/`): lead the glow from the boiler to the engine
   with brass pipe from the dispenser (pieces turn: R, right click, wheel) before it flows; the engine further, the
   glow quicker and more blocked cells each level, crosses for loop bonuses, fast flow; a map of the board in the HUD;
   a steam workshop at night (`view3d/brass_workshop.gd`); the autopilot follows the shortest way (`demo/flow_bot.gd`).
   `--level=N`.
33. Game 30, **Ridgefire** (Scorched Earth-like, `godot/games/ridgefire/`): turn-based artillery for 2-4 tanks, any seat
   the CPU (`demo/ridge_bot.gd` aims by flying test shells, on a worker thread); ground as a height per column (blasts
   carve and the earth above slumps), wind, falls, shields, a shop between rounds (heavy, MIRV, roller, dirt ball, digger,
   nuke); a landscape per round (`view3d/ridge_backdrop.gd`). `--players=N`, `--humans=N`, `--rounds=N`, `--land=N`.
34. Game 31, **Tinplate Turbo** (Super Sprint-like, `godot/games/tinplate/`): tin toy cars on six tabletop tracks
   (`tracks/tracks.tin`, made and checked by `tools/tinplate_tracks.py`), drifting arcade physics, a bridge, ramps, oil,
   puddles, wrenches for upgrades, a championship; CPU drivers on a racing line (`demo/tin_bot.gd`); 1-2 players (F2).
   `--track=N`, `--players=2`.
35. Game 32, **Tunnel Pop** (Dig Dug-like, `godot/games/tunnelpop/`): dig a garden's earth in four layers (a grid of cells
   and links, carved in the view at a quarter cell), pump creatures till they pop, rocks that fall when dug under, eyes
   drifting through earth, drakes' fire, the vegetable, the last one running; levels generated per round; the autopilot
   plans over tunnels and earth (`demo/dig_bot.gd`). `--level=N`.
36. Game 33, **Bloomwand** (Rod Land-like, `godot/games/bloomwand/`): a fairy catches creatures with her wand and slams
   them to bits, conjures rainbow ladders (up where there is none), picks flowers, collects E X T R A; six levels in `levels/garden.bloom` (made
   and checked by `tools/bloomwand_levels.py`), a backdrop per level (`view3d/bloom_backdrop.gd`), 1-2 players (F2), the
   autopilot plans on a graph of walks, drops, ladders and magic ladders (`demo/bloom_bot.gd`). `--level=N`, `--players=2`.
37. Game 34, **Biosurge** (Xenon 2-like, `godot/games/biosurge/`): a vertical shooter through living caverns (wall profiles
   and islands generated per level, drawn by `view3d/bio_world.gd`), enemy waves, wall turrets, worms, pods, a boss per
   level, credits and the trader's shop between levels (gun levels, side pods, rear gun, homing, laser, drone); the
   autopilot dodges by predicting shots half a second ahead (`demo/bio_bot.gd`). `--level=N`.
38. Game 35, **Four Torches** (Gauntlet-like, `godot/games/fourtorches/`): a co-op dungeon crawl for 1-4 heroes (knight,
   shieldmaiden, mage, ranger; any seat the CPU, F2-F4), generated dungeons with doors and keys, generators, six
   monster kinds, health draining, food, potions, the exit; CPU heroes plan on distance maps (`demo/torch_bot.gd`).
   `--players=N`, `--humans=N`, `--level=N`.
39. Checks: `godot/tools/leak/leak_probe.tscn` runs a game's demo headless and prints node, object, resource and
   static-memory counts (`--scene=... --frames=N --every=N`); a Label3D whose font size changes each frame leaks a
   glyph atlas per size (the Whisker Alley 660 MB leak): animate `scale`, never `font_size`. Iron Flags creeps about
   1 MB a minute (to look at). GPU media and launcher cards: record with the monitor awake, one game at a time.
40. Next: the shared campaign/mod system ([docs/level-packs.md](docs/level-packs.md)), the level editors, and
   polish passes over every game.
41. **The library** ([docs/updater.md](docs/updater.md)): the download is the launcher alone; each game is its own pack
   (`tools/export-packs.sh`, only `games/<id>/`: a game may use `core/` and its own folder, never another game's,
   checked by `core/tests/test_packs.gd`), downloaded on first play from the update channel (`latest` by default,
   `stable` = tags). The launcher finds new versions at start and only installs them when asked (U, LIBRARY). CI
   (`release.yml`) runs `tools/test-library.sh` (an exported launcher downloads and runs every game) before publishing.
   The web build (`tools/build-web.sh`, `play/` on the site) downloads the games of `tools/web-games.txt` the same way;
   check new ones with `tools/test-web.sh <id>` before adding them. `--library-preview` fakes a channel for captures.
