# GDash port helpers

Game 1's rules engine is a port of [GDash](https://github.com/meonwax/gdash) (MIT, Copyright (c) 2007-2013
Czirkos Zoltan), the most accurate Boulder Dash engine. `tools/fetch-tools.sh` checks out the pinned source in
`.tools/ref/gdash` (git-ignored, read-only).

- `gen_elements.py` generates `godot/games/rocks/engine/cave_elements.gd` (element list, flags, BDCFF names).
- `gen_properties.py` generates `godot/games/rocks/engine/cave_properties.gd` (BDCFF cave properties and
  their defaults).

The other engine files are hand-ported and name the GDash file they come from. The MIT notice is kept in
`godot/games/rocks/engine/GDASH_LICENSE.txt`.

The reference tests (`godot/games/rocks/tests/test_*_reference.gd`) load GDash's cave files, which include
original caves, straight from `.tools/ref/gdash`. Those files are never copied into the repo, and the tests
skip when the checkout is missing.
