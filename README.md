# Second Credit

[![CI](https://github.com/yoda-jm/project-second-credit/actions/workflows/ci.yml/badge.svg)](https://github.com/yoda-jm/project-second-credit/actions/workflows/ci.yml)
[![Release builds](https://github.com/yoda-jm/project-second-credit/actions/workflows/release.yml/badge.svg)](https://github.com/yoda-jm/project-second-credit/releases/tag/latest)

**Website: https://yoda-jm.github.io/project-second-credit/** · **Download: [latest build](https://github.com/yoda-jm/project-second-credit/releases/tag/latest)** (Linux AppImage, Windows, macOS)

Free, open-source remakes of simple 80s and 90s games. The original rules stay intact, and the presentation is
fully modern: lighting, materials, particles, sound and music, in the spirit of Pac-Man Championship Edition
and Tetris Effect.

- **Same rules.** Recognisable to anyone who played the original.
- **Compatible maps.** Where original or community maps exist, the remake loads them. The repo ships only free levels.
- **All-new art and audio**, under open licences.
- **AI-built.** Developed mostly with Claude Code, driving Godot and Blender.

> Status: thirty-three games are playable, in 3D with sound
> and music, from **Glimmerdeep** (game 1) to **Bloomwand** (game 33), all working titles. Download a build above, or run `tools/fetch-tools.sh`, then `.tools/bin/godot --path godot`.
>
> The macOS build is not notarised: right-click the app and choose Open the first time.

## Build order

Games 1 to 8 are the ladder that built the stack; games 9 onwards follow the catalog, each reusing it.


| # | Inspired by | Adds to the stack |
|---|---|---|
| 1 | Boulder Dash (1984): **Glimmerdeep** | Shared core, grid engine, level packs (BDCFF), editor, procedural props, the AI test loop |
| 2 | Rampart (1990): **Bastion Coast** | Real-time phases, wall-piece placement, cannon battles, local versus |
| 3 | Fruity Frank (1984): **Fruitburrow** | Rigged characters, enemy AI, deformable soil |
| 4 | Alley Cat (1984): **Whisker Alley** | Platformer physics, character animation, multiple scenes |
| 5 | Winter Games (1985): **Frostpeak Games** | Outdoor environments, event framework, advanced input, hot-seat play |
| 6 | Cannon Fodder (1993): **Muddy Boots** | Top-down terrain, squads, pathfinding, map importer |
| 7 | Double Dragon (1987): **Neon Knuckles** | Melee combat, hit-stop, grabs and throws, weapons, co-op |
| 8 | Z (1996): **Iron Flags** | RTS layer: territories, factories, squads, AI; Zod Engine map importer |
| 9 | Bomberman (1983): **Blastyard** | Party battle for 1-4 players with bots, solo stages, sudden death |
| 10 | Lode Runner (1983): **Ingot Run** | Digging, guard hunting by shortest path, the free remakes' level format |
| 11 | Sokoban (1982): **Crate Keeper** | Puzzle solver for our levels, undo/redo, the standard .xsb format |
| 12 | Pac-Man (1980): **Nightbite** | Maze chase with four spirit temperaments, neon look |
| 13 | Arkanoid (1986): **Prism Breaker** | Ball physics, capsules, a 3D neon arena; LBreakout2 level sets |
| 14 | Qix (1981): **Inkstorm** | Territory claiming with flood fill, a relief shader rising as land is claimed |
| 15 | Lemmings (1991): **Mossfolk** | Destructible pixel terrain as 3D rock, eight skills, recorded solutions |
| 16 | Frogger (1981): **Hopline** | Lanes as functions of time (the autopilot plans through time), times of day |
| 17 | Pengo (1982): **Slipfloe** | Sliding and shattering blocks, generated mazes |
| 18 | Bubble Bobble (1986): **Fizzlings** | Bubble physics and chains, two-player co-op, caustics |
| 19 | Rick Dangerous (1989): **Relic Run** | Flip-screen platforming with traps, pistol and dynamite, demo routes |
| 20 | Chuckie Egg (1983): **Henhouse Heist** | Ladders, lifts, wandering hens and the goose, a graph-planning autopilot |
| 21 | Manic Miner (1983): **Deep Breath** | Single-screen caverns, air running out, fixed-arc jumps, conveyors, crumbling floors, a helmet lamp in the dark |
| 22 | Q*bert (1982): **Tumbletop** | A pyramid of cubes to recolour under four rules, bouncing balls, a chasing serpent, cloud-discs, a sky per level |
| 23 | Pang (1989): **Pop Voyage** | A harpoon wire against bouncing, splitting balloons, blocks and items, eight landmark dioramas from a lighthouse to the aurora |
| 24 | Blobby Volley (2000): **Jelly Spike** | Jelly-blob beach volleyball, a CPU that reads the ball, two players on one keyboard, a beach from noon to a moonlit luau |
| 25 | Space Invaders (1978): **Nova Wardens** | The marching fleet (a ripple that quickens), eroding voxel shields, the mothership, a night coast whose alarm rises as the fleet descends |
| 26 | Mini-Putt (1987), Zany Golf (1988): **Lantern Links** | Nine holes of mini-golf in a lantern garden from golden hour into the night: a windmill, a loop, a jump, glass pipes, bumpers; 1-4 players with CPU seats |
| 27 | Marble Madness (1984): **Marble Drift** | A glass marble racing the clock down six floating courses: slopes, drops that shatter it, glass and rough floors, acid, a steelie and hoppers, a sky per course |
| 28 | Bomb Jack (1984): **Fuseflight** | Leap and glide over five festival stages at night collecting fireworks, the lit fuse in order for double, walkers that take wing, the power star |
| 29 | Pipe Mania (1989): **Brassflow** | Lead the glow from the boiler to the engine with brass pipe, in a steam workshop at night: pieces to turn, blocked cells, crosses for loops, fast flow |
| 30 | Scorched Earth (1991): **Ridgefire** | Turn-based artillery for 2-4 tanks on ground that blasts carve and slump, wind, a weapon shop, a new landscape each round |
| 31 | Super Sprint (1986): **Tinplate Turbo** | Tin toy cars drifting round six tabletop tracks, a bridge, ramps, oil, wrenches for upgrades, a championship for 1-2 players |
| 32 | Dig Dug (1982): **Tunnel Pop** | Dig a garden's earth in four layers and pump the burrow creatures till they pop, drop rocks on them, the vegetable bonus, eyes drifting through the earth |
| 33 | Rod Land (1990): **Bloomwand** | A fairy's wand catches creatures and slams them to bits; rainbow ladders, flowers, E X T R A letters, six storybook levels, two players |

Each remake will get its own original name. The names above only refer to the inspiration.

## Documentation

- [docs/vision.md](docs/vision.md): goals and principles
- [docs/roadmap.md](docs/roadmap.md): build order and reasoning
- [docs/catalog.md](docs/catalog.md): all the candidate games (53), with loop, pitch and remake ideas
- [docs/games/](docs/games/): a brief for each game (gameplay, levels, challenge, map compatibility, existing free versions)
- [docs/level-packs.md](docs/level-packs.md): level packs and map compatibility
- [docs/multiplayer.md](docs/multiplayer.md): multiplayer ideas for every game (ghosts, local, network)
- [docs/stack.md](docs/stack.md): tools and pipeline (open-source, no paid services)
- [docs/setup.md](docs/setup.md): development setup (system packages, portable tools, MCP servers)
- [docs/legal.md](docs/legal.md): licensing and what never goes in the repo
- [research/](research/): raw research (stack report, survey of existing free versions)
- [catalog/](catalog/): source for the candidate catalog page (53 games)

## Licence

- **Code:** GNU GPL v3.0 or later. See [LICENSE](LICENSE).
- **Assets** (graphics, 3D models, audio, music, levels, documentation): Creative Commons Attribution-ShareAlike 4.0
  (CC BY-SA 4.0). See [LICENSES/CC-BY-SA-4.0.txt](LICENSES/CC-BY-SA-4.0.txt).
- Third-party assets keep their own licences (CC0 or CC-BY) and are listed in `CREDITS.md`.

More in [docs/legal.md](docs/legal.md).
All game names mentioned are trademarks of their respective owners. This project is not affiliated with them.
