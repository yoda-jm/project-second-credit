# Level packs and map compatibility

## Principles

1. **Compatible first.** Where a map or level format already exists (BDCFF for Boulder Dash, Open Fodder or
   original Cannon Fodder files, Zod Engine maps), our game reads it as-is. Existing community levels must just work.
2. **The repo ships only free levels.** These are levels we design, licensed CC BY-SA 4.0. Original levels
   (the 1984 caves, the Cannon Fodder campaign) are **never** committed, even though the engine can play them.
3. **Players bring their own originals.** Importers read the player's own game files (disk images, data
   folders) and produce a local pack. The importer code is open; the data never enters the repo.
4. **Packs are data only.** They contain no scripts or code, so sharing packs is safe.
5. **Level editors** for grid-based games, so anyone can make packs, including recreations of classic
   layouts shared outside this repo at their own responsibility.

## Pack layout

Built: `godot/core/packs/pack.gd` loads packs, `godot/core/ui/story_card.gd` shows the story between levels and
`godot/core/ui/pack_chooser.gd` lets the player pick a campaign. In use: Muddy Boots (*First Tour*, *The Long
Monsoon*), Glimmerdeep (*The Descent*, eight caves) and Bastion Coast (*The Coastline*, five islands; *Versus
Coasts*, maps for 2-3 players, whose castles are marked with the player's number: `players=` in the header).

```
my-pack/                     (folder or .zip)
  pack.json                  manifest
  levels/                    level files, in our format or a supported foreign one
  preview.png                optional
```

`pack.json`:

```json
{
  "format": 1,
  "game": "boots",
  "id": "long-monsoon",
  "name": "The Long Monsoon",
  "version": "1.0.0",
  "author": "Second Credit",
  "licence": "CC-BY-SA-4.0",
  "description": "Five missions through the rainy season...",
  "levels": ["long-monsoon.boots"],
  "intro": {"title": "The Long Monsoon", "text": "The rains came early this year..."},
  "story": [{"level": 1, "title": "River Of Mud", "text": "..."}],
  "outro": {"title": "The Rains Stop", "text": "..."}
}
```

Level paths are relative to the pack folder and may not leave it. `story` cards show before level N (0-based);
`intro` before the first level, `outro` after the last is won.

Where packs load from:
- the game's own `godot/games/<game>/packs/<id>/` folders (free packs shipped with the game)
- the user folder `user://packs/` (Godot's per-user data dir)
- a pack path given on the command line

## Campaigns and mods (shared by every game)

Several games need more than a list of levels: an ordered **campaign** with a storyline, and **mods** that
players can load or make. This is one shared system in the core, not a per-game feature:

- A pack can declare a campaign: ordered levels, story text or cutscene cards between them, unlock rules,
  and optional per-level settings (starting lives, time, briefing). Packs stay data only.
- Each game gets an **original campaign with its own story**, using everything the remake can do, in the
  spirit of the original's campaign: Cannon Fodder above all (missions, phases, recruits, Boot Hill), but
  also multi-level runs for Glimmerdeep (a descent through themed caverns) and Bastion Coast (a coastline to
  hold, island by island).
- Where a game has original levels or community mods (BDCFF caves, Open Fodder campaigns), the same system
  loads them from the player's files, next to ours.
- Level editors write packs in the same format, so a player's campaign can be shared like ours.

## Downloading known collections

The game menu will offer to download well-known community collections (for example GDash's cave sets or the
big BDCFF archives) straight into `user://packs/`. The player asks for it, the files come from their usual
home, and nothing is copied into this repo. That way we don't duplicate what others already maintain.
Each entry in the list records its source URL and, when known, its licence. Planned for game 1.

## Per game

| Game | Native or foreign formats to support | Importer from original files |
|---|---|---|
| Boulder Dash | BDCFF (read and write) | C64/Atari images → BDCFF (GDash has converters to study) |
| Rampart | our coast maps (`.map`, text grid: water, land, rock, castles; `rounds=N` to hold an island), in packs | none |
| Fruity Frank | our garden packs (`.gdn`, text grid in BDCFF style: several `[garden]` sections per file; spec in `godot/games/fruitburrow/engine/garden_map.gd`) | CPC disk image (later, optional) |
| Cannon Fodder | original CF1/CF2 `.map` + `.spt` + the tileset `.hit` tables (read by `godot/games/boots/engine/cf_import.gd`; format notes in its header, after Open Fodder), OpenFodder Editor output (same format); our campaigns: packs of `.boots` text files | user's Amiga/DOS data folder (local only) |
| Z | Zod Engine `.map` + planet `.tileinfo`, read locally (`godot/games/flags/engine/zod_import.gd`) | original Z data (to investigate) |
| Lode Runner | the plain-text tile format of the free remakes (`#` `@` `H` `-` `X` `S` `$` `0` `&`), read by `godot/games/ingot/engine/ingot_level.gd`; our sets use it with `[level]` headers | original disks (later, optional) |
| Sokoban | the standard text format (`.xsb`/`.sok`: `#` `$` `.` `*` `@` `+`), read by `godot/games/crates/engine/crates_level.gd`; our set adds `par=` and `solution=` comments | n/a |
| Alley Cat, Winter Games, Double Dragon | none (fixed content) | n/a |

## Open questions

- Should our native format simply *be* BDCFF for Boulder Dash? Probably yes: read and write it, with an
  extension block for our extras (lighting themes, music).
- Would packs benefit from Godot `.pck` resource packs (for custom art)? That allows code, so for now: data only.
