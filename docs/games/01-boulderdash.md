# 1. Boulder Dash (1984)

*Original: First Star Software · Atari 8-bit / C64 · Puzzle / Action. Remake effort: small. Free-version gap: **partly covered**.*

The final title must be an original name (see [../legal.md](../legal.md)).

## Core loop

Dig through dirt collecting diamonds before time runs out, while boulders and gems fall under cellular-automaton physics.

## Gameplay

The player guides Rockford through a grid-based cave with the joystick, digging through dirt to collect a required quota of diamonds before a timer runs out, then reaching the exit that opens once the quota is met. Boulders and diamonds obey simple gravity: they fall when unsupported and roll off rounded objects, so every tunnel dug can trigger a chain reaction. Fireflies and butterflies patrol along walls; crushing them with a boulder causes an explosion, and butterflies explode into diamonds. Other hazards and tools include the growing amoeba (which turns into diamonds if enclosed, or boulders if it grows too large) and the magic wall that converts falling boulders into diamonds; diamonds collected beyond the quota are worth more, and remaining time converts into bonus points.

## Levels

The game contains 16 caves (A to P) plus 4 short intermission puzzle caves, each playable at five difficulty levels that tighten time and raise quotas. Caves range from open diamond fields to tightly engineered puzzles built around a single mechanic such as the amoeba, the magic wall, or creature-herding.

## The challenge

Success depends on reading the physics ahead of time: one careless dig brings a boulder onto Rockford's head or seals off the only route to the diamonds. The timer forces players to balance careful planning against speed, and later caves demand precise manipulation of enemies and boulders. Typical deaths are being crushed, touching a firefly, or running out of time after trapping the remaining diamonds.

## What makes it unique

Boulder Dash turned a simple falling-object rule set into an emergent puzzle-action hybrid where the whole cave is a live physics simulation. It spawned a huge lineage of sequels, clones and fan-made cave sets and remains the archetype of the 'rocks and diamonds' genre.

## Remake angle

Grid physics that plays perfectly in 3D: chunky dirt with volumetric crumble, rolling boulders with real weight, dynamic lighting from glowing diamonds, amoeba as animated goo. Rules are tiny and fully deterministic.

The caves could become tactile, lit dioramas with weighty boulder motion, dust and debris particles, glowing gems and dramatic chain-reaction explosions, while the discrete grid simulation stays untouched underneath. Explosion-driven dynamic lighting, camera shake and an online cave editor with leaderboards would fit naturally.

## Map compatibility

Must read (and ideally write) **BDCFF**. The classic cave sets in BDCFF come with GDash (MIT), which is also the reference for exact engine rules (cave timing, amoeba, magic wall, slime, explosions). Also check Rocks'n'Diamonds (GPL-2.0) level-set formats and the extended engines it supports.

## Existing free versions

The free/open scene is huge but entirely retro (R'n'D, GDash); the only free 'modern' attempt is the closed-source Windows freeware Boulder Rocks! 3D, and the premium look is owned by commercial BD 40th Anniversary. An open, cross-platform, Pac-Man-CE-grade take is still open, but must avoid the trademarked name.

- **Rocks'n'Diamonds** — https://www.artsoft.org/rocksndiamonds/ — GPL-2.0 · faithful clone · look: retro-faithful · last activity 2025 · original levels: no (ships own levels; community BD cave sets importable) · custom levels: yes. Most complete free BD/Emerald Mine/Supaplex/Sokoban engine; since 4.4 (Dec 2024) integrates the GDash BD engine; 4.4.1.x Dec 2025 added Krissz engine support. Built-in editor, huge level archive. Pixel-art look.
- **GDash** — https://bitbucket.org/czirkoszoltan/gdash (fork: https://github.com/meonwax/gdash) — MIT · faithful clone · look: retro-faithful · last activity unknown (sporadic; engine now lives on in Rocks'n'Diamonds) · original levels: yes (ships classic cave sets in BDCFF) · custom levels: yes. Most accurate BD engine, cave editor, OpenGL shader 'CRT' effects only; deliberately retro.
- **Boulder Rocks! 3D (GadZombie)** — https://gadzombie.itch.io/boulder-rocks-3d — freeware (closed source) · enhanced remake · look: modern/premium · last activity 2023 · original levels: unknown (multiple level sets, BDCFF-compatible) · custom levels: yes. Closest to 'modern' BD for free: 3D objects, toggleable special effects, modern + Atari sounds, complex level editor. Windows only, not open source; visual quality likely 'hobby 3D' rather than Pac-Man CE polish (unverified).
- **Boulder (rh_galaxy)** — https://rh-galaxy.itch.io/boulder — freeware (unverified) · enhanced remake · look: enhanced 2D · last activity unknown · original levels: no · custom levels: yes. Reimplementation with some new elements and a level editor (unverified details).
- **Various itch.io hobby remakes (LonelyBishop C, quadrathell PureBasic, LaurentM74, dgeph CPC-Remake)** — https://itch.io/games/free/tag-boulder-dash — freeware · faithful clone · look: retro-faithful · last activity 2018-2024 · original levels: partial · custom levels: no. Learning projects; retro look.
- **Javascript BoulderDash (jakesgordon)** — https://github.com/jakesgordon/javascript-boulderdash — MIT · faithful clone · look: retro-faithful · last activity ~2013 (unverified) · original levels: yes (original caves) · custom levels: no. Well-known small HTML5 clone.
- **Other OSGC-listed clones (Epiphany, Lucy the Diamond Girl, CAVEZ of PHEAR, ASCII DASH, minerbold, Mining Haze...)** — https://osgameclones.com/boulder-dash/ — GPL2/GPL3/MIT · faithful clone · look: retro-faithful · last activity None · original levels: mixed · custom levels: mixed. Large but retro-only ecosystem; none with modern presentation.

Official or commercial versions: Commercial: Boulder Dash 30th Anniversary (2014), Boulder Dash Deluxe (2021, BBG), Boulder Dash 40th Anniversary (BBG Entertainment, 2024/2025; Steam, Switch, PS, Xbox, Mac) with HD modern graphics plus retro modes and new 'Modern Worlds'; BBG owns the brand since 2016 (name is trademarked).
