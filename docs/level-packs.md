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
