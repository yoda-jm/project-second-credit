# Second Credit

Free, open-source remakes of simple 80s and 90s games. The original rules stay intact, and the presentation is
fully modern: lighting, materials, particles, sound and music, in the spirit of Pac-Man Championship Edition
and Tetris Effect.

- **Same rules.** Recognisable to anyone who played the original.
- **Compatible maps.** Where original or community maps exist, the remake loads them. The repo ships only free levels.
- **All-new art and audio**, under open licences.
- **AI-built.** Developed mostly with Claude Code, driving Godot and Blender.

> Status: planning. No game code yet.

## Build order

| # | Inspired by | Adds to the stack |
|---|---|---|
| 1 | Boulder Dash (1984) | Shared core, grid engine, level packs (BDCFF), editor, procedural props, the AI test loop |
| 2 | Fruity Frank (1984) | Rigged characters, enemy AI, deformable soil |
| 3 | Alley Cat (1984) | Platformer physics, character animation, multiple scenes |
| 4 | Winter Games (1985) | Outdoor environments, event framework, advanced input, hot-seat play |
| 5 | Cannon Fodder (1993) | Top-down terrain, squads, pathfinding, map importer |
| 6 | Double Dragon (1987) | Melee combat, co-op |
| 7 | Z (1996) | RTS layer, Zod Engine map compatibility |

Each remake will get its own original name. The names above only refer to the inspiration.

## Documentation

- [docs/vision.md](docs/vision.md): goals and principles
- [docs/roadmap.md](docs/roadmap.md): build order and reasoning
- [docs/games/](docs/games/): a brief for each game (gameplay, levels, challenge, map compatibility, existing free versions)
- [docs/level-packs.md](docs/level-packs.md): level packs and map compatibility
- [docs/stack.md](docs/stack.md): tools and pipeline (open-source, no paid services)
- [docs/legal.md](docs/legal.md): licensing and what never goes in the repo
- [research/](research/): raw research (stack report, survey of existing free versions)
- [catalog/](catalog/): source for the candidate catalog page (49 games)

## Licence

- **Code:** GNU GPL v3.0 or later. See [LICENSE](LICENSE).
- **Assets** (graphics, 3D models, audio, music, levels, documentation): Creative Commons Attribution-ShareAlike 4.0
  (CC BY-SA 4.0). See [LICENSES/CC-BY-SA-4.0.txt](LICENSES/CC-BY-SA-4.0.txt).
- Third-party assets keep their own licences (CC0 or CC-BY) and are listed in `CREDITS.md`.

More in [docs/legal.md](docs/legal.md).
All game names mentioned are trademarks of their respective owners. This project is not affiliated with them.
