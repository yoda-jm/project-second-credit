# Multiplayer: ideas for every game

Every Second Credit engine is deterministic: fixed 60 Hz ticks, a seeded random generator, and the player's input as
the only outside influence. That makes three kinds of multiplayer cheap, and they share one toolkit:

- **Ghosts** (race against the clock with the shadow of someone else): record the input stream of a run (a few bytes
  a tick, compressed), then replay it in a second copy of the engine on the same seed and draw that run as a
  translucent "shadow". Works for local best runs, a friend's run from a file, or a daily challenge (same seed for
  everyone, ghosts shared as small files). Already done for Glimmerdeep's race (F2).
- **Local play**: shared screen (everyone in one view) when the game fits one screen; split screen (two or four
  viewports, as Glimmerdeep's race does) when players go their own way.
- **Network play**: lockstep over Godot's ENet peers: each tick, each peer sends its input; the engine advances
  when it has everyone's input for that tick. With deterministic engines nothing else needs syncing (a checksum of the
  state every second catches drift). Add rollback later for fast action games; lockstep is fine for most of these
  (an input delay of 2-4 ticks on a LAN or a good connection). Lobby: host/join by address first, then a small
  relay or matchmaking list if the owner wants it (free options only).

Legend: **Co-op** (together against the game), **Versus** (at the same time, against each other), **Ghost** (the same
level, apart in time or space, racing the clock and each other's shadow), **Split** (split screen), **Net** (network).

| # | Game | Best local mode | More ideas | Network |
|---|---|---|---|---|
| 1 | **Glimmerdeep** (Boulder Dash) | Ghost race on the same cave, split screen (done, F2) | Co-op on one cave with two diggers (one screen, the camera frames both; a rock can crush your friend); a mirrored "duel" cave where both collect the same count and the first out wins | Ghost race and co-op, lockstep |
| 2 | **Bastion Coast** (Rampart) | Versus 2-3 players, each with a castle on the shared coast (versus done, F2) | Co-op: two players share one castle, one builds while the other aims | Versus, lockstep |
| 3 | **Fruitburrow** (Fruity Frank) | Co-op in the same garden (two gardeners, shared or separate scores) | Versus: two gardens split screen, fruit you drop falls into the other's garden as a nasty; ghost race on garden 1 | Co-op |
| 4 | **Whisker Alley** (Alley Cat) | Versus: two cats on the same alley, first to the lady cat; windows are shared, rooms are split screen | Ghost race through a fixed room sequence; "cat and dog": one player is the bulldog | Versus |
| 5 | **Frostpeak Games** (Winter Games) | Hot seat (done); simultaneous speed skating side by side (split lanes, both players at once) | Ski jump with ghosts of every jumper so far drawn in the air; a biathlon relay | Simultaneous events |
| 6 | **Muddy Boots** (Cannon Fodder) | Co-op: two squads, one mouse each, or split the squad (two groups) | Versus skirmish on a map: two squads hunt each other | Co-op campaign |
| 7 | **Neon Knuckles** (Double Dragon) | Co-op brawl (done, 1-2 players) | Up to four on one street; a versus arena between stages (like the original's end) | Co-op, rollback preferred |
| 8 | **Iron Flags** (Z) | Versus RTS, split screen or one screen with separate cursors | Two players against the AI general; king of the hill on one flag | Versus, lockstep (the natural RTS model) |
| 9 | **Blastyard** (Bomberman) | Versus 1-4 (done) | Team battles 2 v 2; co-op solo stages | Versus, lockstep with input delay |
| 10 | **Ingot Run** (Lode Runner) | Co-op on the same level (two runners, holes shared) | Ghost race: fastest clear with the other's shadow; versus with gold stealing | Co-op |
| 11 | **Crate Keeper** (Sokoban) | Ghost race on the same puzzle: fewest moves or fastest, with the other's shadow pushing its own crates | Co-op puzzles designed for two keepers (crates only two can move) | Ghost / async (share solutions) |
| 12 | **Nightbite** (Pac-Man) | Versus: two eaters in the same maze, eating each other's pellets (Pac-Man Battle Royale style) | Up to four; co-op where one is the eater and the other steers a friendly spirit | Versus |
| 13 | **Prism Breaker** (Arkanoid) | Split screen duel: bricks you break drop "junk" rows onto the other's wall (Tetris-attack style) | Co-op: two paddles on one wall (top and bottom, or side by side); ghost score race on the same wall | Duel |
| 14 | **Inkstorm** (Qix) | Versus on the same board: two pens claiming land in their own colours; cut the other's line to break it | Co-op: two pens share a target percentage | Versus |
| 15 | **Mossfolk** (Lemmings) | Split screen race: two players with mirrored levels and a shared exit in the middle (the original's two-player mode idea), steal the other's mosslings into your burrow | Co-op on a big level with two cursors | Versus, lockstep (deterministic terrain) |
| 16 | **Hopline** (Frogger) | Versus: two frogs at once, race for the bays (a filled bay is yours) | Co-op: fill all five together against the clock; ghost race | Versus |
| 17 | **Slipfloe** (Pengo) | Co-op in the same maze (two otters), or versus: crush the other's mites, block the other with ice | Ghost race for the fastest clear | Co-op/versus |
| 18 | **Fizzlings** (Bubble Bobble) | Co-op for two (done); up to four | Versus: bubbles trap the other player too; a chain race | Co-op |
| 19 | **Relic Run** (Rick Dangerous) | Ghost race through the same level (speedrun with the other's shadow) | Co-op: two explorers, traps affect both; split screen when apart | Ghost / co-op |
| 20 | **Henhouse Heist** (Chuckie Egg) | Versus: two farmhands on the same screen, eggs are claimed by whoever grabs them | Ghost race; co-op against the goose | Versus |
| 21 | **Deep Breath** (Manic Miner) | Ghost race per cavern (air left as the score) | Co-op: two miners share one air supply (tension!) | Ghost |
| 22 | **Tumbletop** (Q*bert) | Versus on one pyramid: each player paints cubes their own colour, stealing the other's | Co-op: two hoppers share the pyramid, the serpent chases the nearer; ghost race for the fastest round | Versus |
| 23 | **Pop Voyage** (Pang) | Co-op for two travellers (the original's two-player mode) | Versus: split screen, balloons you pop drop onto the other's stage | Co-op |
| 24 | **Jelly Spike** (Blobby Volley) | Versus on one keyboard (done, F2) | 2 v 2 with four blobs; a ghost-free tournament ladder against CPU temperaments | Versus, rollback preferred (fast physics) |
| 25 | **Nova Wardens** (Space Invaders) | Alternating turns (the original two-player mode) | Co-op: two cannons defend together; versus: the second player steers the mothership | Ghost / co-op |
| 26 | **Lantern Links** (Mini-Putt, Zany Golf) | Hot seat for 1-4, any seat the CPU (done) | Everyone putting at once on the same hole (ghost balls), match play, a ghost of your best round | Ghost / turns |
| 27 | **Marble Drift** (Marble Madness) | Two marbles racing down the same course (the original's two-player race), knocking each other off | Ghost race against your best run | Race, lockstep |
| 28 | **Fuseflight** (Bomb Jack) | Alternating turns (the original two-player mode) | Co-op: two heroes on one stage, the lit-fuse bonus shared | Co-op / turns |
| 29 | **Brassflow** (Pipe Mania) | Two players on one board, each with a cursor, sharing one dispenser (the original's co-op) | Versus: two boards side by side, a leak sends blocks to the rival | Co-op, lockstep |

## Suggested order

1. **Ghost toolkit** (input recording and replay, ghost rendering, save/load of ghost files): one shared piece in
   `core/`, then turned on game by game. Cheapest, and it makes every game replayable against friends.
2. **Local versus/co-op** where the engine already takes several players (Blastyard, Fizzlings, Neon Knuckles, Bastion
   Coast): mostly done; extend to Nightbite, Hopline, Henhouse Heist and Inkstorm (one screen each).
3. **Split screen helper** in `core/` (from Glimmerdeep's race): for Prism Breaker's duel, Mossfolk's race, Whisker
   Alley, Frostpeak's simultaneous events.
4. **Network lockstep** in `core/` (ENet peers, input exchange, state checksums, host/join by address): first for the
   games whose local multiplayer is done.
