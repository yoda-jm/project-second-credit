# Credits

Second Credit stands on the work of many people. Everything below is free and open; thank you.

## Game 1 (rocks and diamonds)

- **GDash** by Czirkos Zoltan and contributors, MIT licence: <https://bitbucket.org/czirkoszoltan/gdash>
  (mirror used: <https://github.com/meonwax/gdash>). The rules engine, the BDCFF loader, the cave objects and the
  element table are ports of GDash; the notice is in `godot/games/glimmerdeep/engine/GDASH_LICENSE.txt`. GDash's
  replays are what prove our engine exact.
- **BDCFF**, the Boulder Dash Common File Format, designed by the Boulder Dash fan community, which also keeps
  thousands of caves alive.
- The original *Boulder Dash* (1984) by Peter Liepa and Chris Gray, First Star Software, which inspired it.
  None of its code, graphics, sounds or caves are in this repo.

## Game 2 (Bastion Coast, working title)

- Inspired by *Rampart* (Atari Games, 1990). None of its code, graphics, sounds or maps are in this repo; the
  rules are rewritten from how the game plays.

## Game 3 (Fruitburrow, working title)

- Inspired by *Fruity Frank* (Kuma Computers, 1984), itself in the family of Universal's *Mr. Do!* (1982). None of
  its code, graphics, sounds or levels are in this repo; the rules are rewritten from how the game plays, and the
  gardens are our own (`godot/games/fruitburrow/gardens/`, CC BY-SA 4.0).
- The gardener, fruit and monsters are built by scripts in `tools/blender/` (the gardener is the collection's first
  rigged and animated character); sound effects and the garden theme are synthesised by `tools/audio/`.

## Textures and fonts

- **ambientCG** by Lennart Demes, CC0 1.0: grass, sand, soil, rock, stone bricks, planks and metal PBR texture
  sets (<https://ambientcg.com>; the list is in `godot/core/art/textures/README.md`).
- **Kenney Fonts** by Kenney, CC0 1.0: Kenney Future and Kenney Future Narrow (<https://kenney.nl>).

## Engine and libraries

- **Godot Engine** 4.7, MIT: <https://godotengine.org>
- **GdUnit4** by Mike Schulze, MIT (unit tests): <https://github.com/godot-gdunit-labs/gdUnit4>
- **Godot AI** (hi-godot), MIT (editor MCP bridge): <https://github.com/hi-godot/godot-ai>
- **GLib**'s random number generator (GRand, Mersenne Twister by Makoto Matsumoto and Takuji Nishimura), ported
  so replays match GDash.

## Tools

- **Blender** 5.2, GPL-2.0-or-later: <https://www.blender.org>
- **Blender Lab MCP**, GPL-3.0-or-later: <https://projects.blender.org/lab/blender_mcp>
- **uv** by Astral, MIT or Apache-2.0: <https://github.com/astral-sh/uv>
- **GitHub CLI** and **Git LFS**, MIT
- **FluidSynth** (LGPL-2.1) and the **FluidR3_GM** SoundFont (MIT); **VICE** (GPL-2.0) for reference captures
- **Xvfb** (X.Org, MIT/X11 licence) for headless screenshots

## Made with

- **Claude Code** (Anthropic), which wrote most of the code, and the owner, who directed and tested it.

Everything else (all 3D models, sound effects, music, maps, caves, the water normal map) is original to this
project, made with the scripts in `tools/` (Blender, NumPy, FluidSynth), and licensed CC BY-SA 4.0. Each asset
folder has a README with its provenance.
