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

## Checking the engine against GDash itself

`harness/` is a small command-line program built from GDash's own engine sources (`harness/build.sh`, needs g++
and the GLib development files). `reference.sh` plays every replay in the checkout with it and writes the
results to `.tools/ref/gdash-results.txt`. `test_engine_reference.gd` requires our port to give exactly the
same success and score for every replay.

The scores stored in the replay files are not used as the reference: about 25 of them were recorded by older
GDash versions, and today's GDash no longer reproduces them.

For one file, `godot --headless --path godot -s res://tools/replay_check.gd -- file.bd` prints our results,
and `.tools/ref/gdash-harness file.bd [cave-index]` prints GDash's; the cave index enables a per-frame trace.
