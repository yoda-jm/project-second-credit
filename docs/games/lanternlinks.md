# Lantern Links (game 26, working title): spec

Inspired by the 80s mini-golf games, *Mini-Putt* (Accolade, 1987) and *Zany Golf* (Electronic Arts, 1988): a
putting course of short, walled holes with a gadget on each (windmill, loop, ramps, water, bumpers, moving walls).
None of their holes, names, graphics or sounds are used; our course, the lantern garden and the audio are new.
Neither original has a level format worth reading, so our holes are our own text format (below), CC BY-SA 4.0.

## The pitch

A mini-golf course in a lantern garden, played from golden hour into the night: the first hole under a low sun,
the last one lit only by paper lanterns, string lights, a glowing cup and the ball's own trail. Every hole has its
gadget and its own light. One to four players in hot seat, any of them the CPU.

## Rules (the usual)

- **Course:** nine holes (*The Lantern Garden*), par 2 to 4, total par 27. Holes are played in order; each player
  plays out the hole before the next one tees off (one ball on the course at a time).
- **Stroke:** aim and pull back. The shot's speed is proportional to the pull (0 to 4.6 m/s). A stroke counts
  when the ball is hit, even if it barely moves.
- **Stroke limit:** 8. If the ball is not in after the 8th stroke, it is picked up and the hole scores 8 + 1 = 9.
- **Water and chasms:** +1 stroke, the ball goes back to where the shot was played.
- **The cup:** a ball drops if it reaches the cup slowly enough (under about 1.5 m/s); faster, it lips out
  (a hop and a deflection). Near the cup the green dips gently, so a dying putt curls in.
- **Scoring:** strokes per hole, total and against par; names for each hole result (hole in one, eagle, birdie,
  par, bogey, double bogey). The winner is the lowest total; ties share the place.

## Controls (obvious, with a hint card on the first hole)

| | Mouse | Keyboard | Gamepad |
|---|---|---|---|
| Aim | move the mouse left and right (the camera orbits the ball) | left and right (shift: fine) | left stick |
| Shoot | press, pull back (down), release; pull back to zero to cancel | hold space: the meter rises and falls, release | hold A, release |
| Look | wheel zooms | tab: overview of the hole | Y: overview |

A dotted guide shows the line of the shot up to its first bank (a short stub after it), in the player's colour.

## Physics (deterministic, `engine/links_engine.gd`)

- The ball rolls on a height field: a text grid of cells (0.5 m) with a height per cell; ramp cells interpolate
  between the flat cells either side; smooth bumps can be added. Gravity pulls along the slope (5/7 g for a rolling
  ball), rolling friction slows it (felt 0.6 m/s², sand 4 m/s², ice 0.2 m/s²).
- The ball is 2.5D: it rolls on the ground, and when the ground drops away faster than it would fall (a ramp's lip,
  a step, the loop's exit) it flies ballistically and lands with a bounce. Higher cells are walls for a ball below
  their top. Walls (and bank rails) bounce it with restitution 0.72.
- Fixed ticks of 1/60 s, substeps so the ball never moves more than 2 cm in one. Moving gadgets are pure functions
  of the hole clock (like Hopline's lanes), so a shot can be simulated ahead exactly: the guide, the CPU and the
  tests all use the same simulation.
- Gadgets: **windmill** (blades sweep across the tunnel under the mill: blocked while a blade is down),
  **loop** (enter fast enough to go round, else roll back), **bumpers** (kick the ball away faster),
  **movers** (blocks sliding to and fro), **spinners** (a turning bar), **pipes** (in at one mouth, out at the
  other), **boosters** (arrows that push the ball), **water**, **sand**, **ice**, **chasms** (jump them).

## Hole format (`holes/*.links`, our text format)

```
name = Mill Lane
par = 3
map:                     # one character per 0.5 m cell
#########
#T....W.#
#####.#.#
    #...O#
    ######
height:                  # optional, same shape: 0-9 then a-z = 0.0 to 3.5 m in 0.1 m steps, '/' = ramp
...
windmill = 6 1 x 4.0     # cell, the lane's axis, seconds per turn
bump = 7.5 3.5 0.8 0.15  # centre (cells), radius (cells), height (m)
```

Map cells: `#` wall, `.` felt, `T` tee, `O` cup, `s` sand, `i` ice, `w` water, `_` chasm, `/` and `\` diagonal banks
(the solid half is on the wall side), `>` `<` `^` `v` boosters, space = outside the course. Gadgets that span
cells are lines after the grid. A test loads every hole and checks the CPU sinks it within par + 2.

## Presentation

- **The lantern garden.** Each hole sits on its own terrace of a hillside garden: felt lanes with wood or stone
  rails, stone and hedge beds around them, trees, bushes, a pond and a stream, a pavilion, the town's lights in
  the distance. The sun goes down as the round goes on (hole 1 golden hour, hole 5 dusk, hole 9 night): the sky,
  the light, the fog and the lanterns (lit one by one) follow the hole number.
- **Lighting:** a low warm sun with soft shadows, sky ambient, SSAO, glow, reflections in the ponds, paper lanterns
  and string lights as real lights (a few with shadows), a glowing cup and flag, a lit ball with a light trail.
- **Camera:** behind the ball while aiming, orbiting as you aim; it follows the rolling ball and looks ahead,
  swoops to the cup on a sink, flies over each new hole before the first shot (the hole's name and par on a card),
  and has an overview.
- **Juice:** the ball squashes a little on hard banks, sparks on bumpers, a splash and ripples in water, a sand
  puff, a rattle and a pop of light as it drops, fireworks and confetti for a hole in one, the flag lifting.
- **HUD:** hole, par, strokes, the player to play and their colour, the power meter, a scorecard between holes
  and at the end (strokes, totals, against par, the winner).
- **Audio:** a soft putt tap (pitched by power), wooden bank knocks, bumper boings, the cup's rattle and drop,
  splashes, sand, the windmill's creak, the loop's whoosh, pipes, crickets and a fountain in the garden; an evening
  lounge tune, quieter by night.
- **Demo mode:** `--demo` lets the CPU play the course (what `tools/capture.sh` records); `--hole=N` starts at a
  hole; `--players=N` for hot seat.

## Later

A course editor, more courses as packs (a beach course, a haunted course), ghost race against your best round,
putting with backspin.
