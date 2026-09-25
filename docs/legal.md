# Legal and licensing rules

Not legal advice. These are the working rules for the project.

## What we never put in the repo

- Original **names and logos** as product titles. Boulder Dash (BBG Entertainment), Cannon Fodder
  (Codemasters/EA), Z (Rebellion), Double Dragon (Arc System Works), Winter Games (Epyx IP holders),
  Arkanoid and Qix (Taito) are all still owned. Each remake gets an **original working title**. Descriptions
  may say "inspired by" or "compatible with".
- Original **sprites, graphics, music, sound effects, code**.
- Original **level and map data**. The engine may *load* originals the player supplies (see
  [level-packs.md](level-packs.md)), but we never distribute them.
- The **catalog screenshots** (`catalog/shots/`, `catalog/index.html`). They are fair-use Wikipedia images for
  private reference and are git-ignored.

## What is fine

- Re-implementing **game rules and mechanics** from observation, documentation, and GPL/MIT reference engines
  (GDash, Open Fodder, Zod Engine), respecting their licences.
- Reading original file formats for **interoperability** (importers).
- Avoid copying the overall look and feel too closely (see *Tetris Holding v. Xio*, 2012). Our distinct
  modern art style helps here.

## Project licences (decided 2026-09-25)

- **Code: GPL-3.0-or-later** (`LICENSE`). Compatible with the GPL-3.0 references we will study or port (Open Fodder, Zod
  Engine) and with MIT code (GDash, Godot).
- **Assets (art, 3D models, audio, music, levels, docs): CC BY-SA 4.0** (`LICENSES/CC-BY-SA-4.0.txt`).
- Third-party assets: **CC0 or CC-BY only** (Kenney, Quaternius, Poly Haven, ambientCG, CC0 Freesound clips).
  Every one gets listed in a `CREDITS.md`.
- AI-generated assets: record the tool and prompt in provenance notes. Use only tools whose terms give us
  the output (see [stack.md](stack.md)).

## Tools and models to avoid (licence reasons)

- **Mixamo:** raw assets can't be redistributed.
- **Stable Audio Open and Stable Fast 3D:** community licence, not an open licence.
- **FLUX.2 [dev] and klein 9B weights:** non-commercial licence.
- **Hunyuan3D open weights:** the licence excludes the EU, UK and South Korea.
- **Suno and Udio free tiers, ElevenLabs free tier:** non-commercial use or no ownership of the output.
