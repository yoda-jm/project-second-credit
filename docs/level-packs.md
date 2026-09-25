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

## Pack layout (draft)

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
  "game": "boulderdash",
  "id": "example-caves",
  "name": "Example Caves",
  "version": "1.0.0",
  "author": "someone",
  "licence": "CC-BY-SA-4.0",
  "levels": ["levels/set.bd"],
  "level_format": "bdcff"
}
```

Where packs load from:
- the built-in `packs/` folder (free packs shipped with the game)
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
| Fruity Frank | our text-grid format | CPC disk image (later, optional) |
| Cannon Fodder | original CF1/CF2 `.map` + `.spt` (see Open Fodder), OpenFodder Editor output | user's Amiga/DOS data folder |
| Z | Zod Engine map format | original Z data (to investigate) |
| Alley Cat, Winter Games, Double Dragon | none (fixed content) | n/a |

## Open questions

- Should our native format simply *be* BDCFF for Boulder Dash? Probably yes: read and write it, with an
  extension block for our extras (lighting themes, music).
- Would packs benefit from Godot `.pck` resource packs (for custom art)? That allows code, so for now: data only.
