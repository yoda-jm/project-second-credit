# Roadmap: build order

The order is chosen so that **we build the stack while we build the games**. The first game must be good to
play and look great, but need the simplest pipeline. Each following game adds only a few new capabilities
on top of what already works. There is no throwaway prototype: game 1's first milestone *is* the pipeline test.

Other rules for the order:
- **Map compatibility is mandatory.** If maps or levels exist for a game, we must load them ([level-packs.md](level-packs.md)). Original graphics don't matter; ours are new.
- Where the free versions stand is recorded in `research/existing_*.json` and in each game brief.

## The ladder

Rampart moved up to game 2 on 2026-09-25, at the owner's request.

| # | Game (working title TBD) | New stack capabilities it introduces | Map compatibility | Effort |
|---|---|---|---|---|
| 1 | **Boulder Dash** (our title: *Glimmerdeep*) | Shared Godot core (menus, input, audio, settings). Deterministic grid engine. Level-pack loader + **BDCFF** reader. Level editor. Procedural Blender *props* (boulders, gems, dirt, walls; no rigged characters). Glow, emissive and particle look. jsfxr sound effects. MIDI-to-FluidSynth music. Xvfb capture and GdUnit4 test loop for the AI. | BDCFF: GDash (MIT) ships the classic caves in BDCFF and is the exact rules reference. Hundreds of fan caves exist. | small |
| 2 | **Rampart** (our title: *Bastion Coast*) | **Real-time phases** (build, battle, repair) on a shared clock. Polyomino wall pieces with rotation, territory enclosure (flood fill), cannon ballistics with an aiming cursor, ship AI. Local versus for 2-3 players. Water and a coastal diorama. | None: fixed maps; our coastlines are data files that can be shared as packs. | medium |
| 3 | **Fruity Frank** (our title: *Fruitburrow*) | First **rigged and animated character** (Rigify or Quaternius base). Enemy AI in player-dug tunnels. Deformable soil. Reuses the whole grid core. | No existing format; our text-grid format in BDCFF style. | small |
| 4 | **Alley Cat** (our title: *Whisker Alley*) | **Platformer physics** and a character with many animations. Several scenes (the alley plus window mini-game rooms). 2.5D camera. | None: fixed rooms (rhuizer/alleycat, GPL-3.0, documents the behaviour). | small |
| 5 | **Winter Games** (our title: *Frostpeak Games*) | **Outdoor environments** (snow and ice shaders, sky, crowds). An event framework. Advanced input (analogue timing, gyro, rumble). Hot-seat multiplayer and a results/medals flow. | None: fixed events. | medium |
| 6 | **Cannon Fodder** (our title: *Muddy Boots*) | **Top-down 3D terrain** from tile maps. Squads, pathfinding, projectiles, destructible buildings, vehicles. First **binary map importer** (original CF1/CF2 files). | Original `.map`/`.spt` files as read by Open Fodder (GPL-3.0) + OpenFodder Editor maps. The free Amiga demo data is legal test data. | medium |
| 7 | **Double Dragon** (our title: *Neon Knuckles*) | **Melee combat** (hitboxes, hit-stop, grabs, throws). Weapon physics. Heavy animation work. Co-op. | None worth targeting (OpenBOR mods contain the original IP). | medium |
| 8 | **Z** (our title: *Iron Flags*) | **RTS layer**: territory capture, production, unit AI, fog, minimap. Reuses #6's terrain and units. | Zod Engine maps (GPL-3.0; the fenio fork has 34 campaign maps). Original Z data importer if the format is documented (unverified). | large |

### Why Boulder Dash first
- Very simple rules on a grid: easy for an AI to get exactly right and to test automatically.
- The best existing map ecosystem, with a clean, documented text format (BDCFF) and an MIT reference engine.
- A strong visual showcase without hard assets: glowing gems, rock materials, crumbling dirt, explosions,
  dynamic light. Rockford can be a small, stylised character with minimal animation at first.

## After the ladder: games 9 to 20

With the ladder done (2026-09-26), the owner asked to keep going through the catalog, always the next relevant
game, and to polish each one to the same standard (3D, lighting, camera, juice). Each brings a little new tech:

| # | Inspired by | Our title | What it brought |
|---|---|---|---|
| 9 | Bomberman (1983) | *Blastyard* | Party battle for 1-4 players with bots, solo stages, sudden death |
| 10 | Lode Runner (1983) | *Ingot Run* | Digging, guard hunting by shortest path, the free remakes' level format |
| 11 | Sokoban (1982) | *Crate Keeper* | Puzzle solver for our levels, undo/redo, the standard .xsb format |
| 12 | Pac-Man (1980) | *Nightbite* | Maze chase with four spirit temperaments, neon look |
| 13 | Arkanoid (1986) | *Prism Breaker* | Ball physics, capsules, a 3D neon arena; LBreakout2 level sets |
| 14 | Qix (1981) | *Inkstorm* | Territory claiming with flood fill, a relief shader rising as land is claimed |
| 15 | Lemmings (1991) | *Mossfolk* | Destructible pixel terrain as 3D rock, eight skills, recorded solutions |
| 16 | Frogger (1981) | *Hopline* | Lanes as functions of time (the autopilot plans through time), times of day |
| 17 | Pengo (1982) | *Slipfloe* | Sliding and shattering blocks, generated mazes |
| 18 | Bubble Bobble (1986) | *Fizzlings* | Bubble physics and chains, two-player co-op, caustics |
| 19 | Rick Dangerous (1989) | *Relic Run* | Flip-screen platforming with traps, pistol and dynamite, demo routes |
| 20 | Chuckie Egg (1983) | *Henhouse Heist* | Ladders, lifts, wandering hens and the goose, a graph-planning autopilot |
| 21 | Manic Miner (1983) | *Deep Breath* | Air supply, fixed-arc jumps, conveyors, crumbling floors, patrolling guardians, lamplit caverns |
| 22 | Q*bert (1982) | *Tumbletop* | Diagonal hops on a cube pyramid, painting rules (two-step, undo), a chasing serpent lured off discs |
| 23 | Pang (1989) | *Pop Voyage* | Splitting-ball physics, a look-ahead autopilot, a diorama per stage with its own sky, light and grade |
| 24 | Blobby Volley (2000) | *Jelly Spike* | Ball-and-blob physics, the three-touch rule, a CPU with reading delay and aim noise, local versus |
| 25 | Space Invaders (1978) | *Nova Wardens* | The ripple march, per-pixel shields as voxels, an autopilot that leads its targets, a reactive night backdrop |

Level compatibility: Crate Keeper reads `.xsb` collections, Ingot Run the free remakes' tile format, Prism Breaker
LBreakout2 level sets; Mossfolk's importer for the original level files is still to do (it needs the player's own
graphics sets). See [level-packs.md](level-packs.md).

### Bonus games that the stack makes almost free
After each step some catalog games need little new tech and could be slotted in:
- after #1: Sokoban (big free `.xsb` level corpus), Dig Dug-like, Pengo-like, Lode Runner-like
- after #4: Bomb Jack-like, Rod Land-like
- after #6: Gauntlet-like, Chaos Engine-like

The rest of the catalog is parked.

**On reference engines and licences:** reusing or closely porting GPL code (Open Fodder, Zod Engine) means our code must be GPL-3.0-compatible. This
is one reason [legal.md](legal.md) recommends GPL-3.0-or-later.
