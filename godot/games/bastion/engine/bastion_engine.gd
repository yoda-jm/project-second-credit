class_name BastionEngine
extends RefCounted
## Rules of Bastion Coast (inspired by Rampart, 1990), one player against the sea. Pure logic, advanced in fixed
## ticks with a seeded random generator, so a game can be replayed from its inputs and tested without a view.
##
## A round is: CANNONS (place new cannons inside your territory), BATTLE (ships shell your walls, you shoot them),
## BUILD (repair with random wall pieces; at the end at least one castle must be enclosed or the game is over).
## The first round starts with CHOOSE (pick a home castle; walls are raised around it).
## Timings and counts are constants below; they are our own tuning, to be checked against the arcade game.
##
## Versus (2 or 3 players, a map with `players=`): every player builds in their own region of the coast, the
## phases run for everyone at once, there is no fleet and the cannons shoot at each other's walls and cannons.
## A player with no enclosed castle at the end of a repair phase is out; the last one standing wins (or the best
## score once the map's rounds are played). Per-player state lives in `players`; the solo game is player 0 and
## the old single-player fields (cursor, piece, score...) read and write player 0.

signal event(kind: String, data: Dictionary)  ## for the view and audio: "wall_placed", "cannon_placed", "shot",
## "impact", "ship_hit", "ship_sunk", "wall_destroyed", "phase", "enclosed", "game_over", "castle_claimed";
## versus adds "cannon_hit", "cannon_destroyed", "player_out". Player events carry "player" (index).

enum Phase { CHOOSE, CANNONS, BATTLE, BUILD, GAME_OVER }
enum Cell { EMPTY, WALL, CANNON, RUBBLE }

const TICK := 1.0 / 60.0
const CHOOSE_SECONDS := 12.0
const CANNON_SECONDS := 12.0
const BATTLE_SECONDS := 18.0
const BUILD_SECONDS := 22.0
const FIRST_ROUND_CANNONS := 3
const CANNONS_PER_ROUND := 2
const CANNONS_PER_CASTLE := 1
const CANNON_RELOAD := 1.1
const BALL_SPEED := 14.0  ## cells per second
const RUBBLE_ROUNDS := 1  ## rubble blocks building during the next repair phase only (to check against the arcade)
const SHIP_SPEED := 1.6
const SHIP_FIRE_EVERY := 2.4
const SHIP_RANGE := 11.0
const PLAY_MARGIN := 2  ## ships only anchor and fire inside the map minus this margin (always on screen)
const HOME_RING := 3  ## the first walls are raised this far around the home castle (room for cannons)
const CANNON_HP := 3  ## versus: hits a cannon takes before it is destroyed
const WALL_POINTS := 25  ## versus: an enemy wall knocked down
const CANNON_POINTS := 300  ## versus: an enemy cannon destroyed

var map: CoastMap
var rng := RandomNumberGenerator.new()
var cells := PackedByteArray()   ## Cell per map cell
var owner := PackedByteArray()   ## the player whose wall or cannon stands on a cell
var rubble := PackedByteArray()  ## build phases left before rubble clears
var territory := PackedByteArray()  ## 0, or the player + 1 whose walls enclose the land (1: ours, solo)
var cannons: Array[Dictionary] = []  ## {pos: Vector2i (top-left of 2x2), reload: float, active: bool, player: int, hp: int}
var ships: Array[Dictionary] = []    ## {pos: Vector2, target: Vector2, hp: int, size: int, fire_in: float, id: int}
var balls: Array[Dictionary] = []    ## {from: Vector2, to: Vector2, t: float, dur: float, ours: bool, player: int}
var players: Array[BastionPlayer] = [BastionPlayer.new(0)]
var versus := false  ## two or three players against each other (no fleet)
var fleet := true    ## ships sail in during battles (solo)
var winner := -1     ## versus: the player who won the match

var phase := Phase.CHOOSE
var phase_left := CHOOSE_SECONDS
var round_number := 0
var won := false  ## the map's rounds were held (a campaign island)
var ships_sunk := 0
var _next_ship_id := 1
const HOLE_LIMIT := 12  ## a castle listed with more than this many holes is wide open

# Player 0's state under the solo game's names (the solo game, its view, HUD, bot and tests use these).
var score: int:
	get: return players[0].score
	set(v): players[0].score = v
var home_castle: int:
	get: return players[0].home_castle
	set(v): players[0].home_castle = v
var enclosed_castles: Array[int]:
	get: return players[0].enclosed_castles
	set(v): players[0].enclosed_castles = v
## For the home castle and every castle being walled in: castle index -> holes (cells to wall to seal it).
var castle_holes: Dictionary:
	get: return players[0].castle_holes
	set(v): players[0].castle_holes = v
var cursor: Vector2:  ## in cells; during battle it is a free aim point
	get: return players[0].cursor
	set(v): players[0].cursor = v
var piece: Array[Vector2i]:
	get: return players[0].piece
	set(v): players[0].piece = v
var piece_turns: int:
	get: return players[0].piece_turns
	set(v): players[0].piece_turns = v
var cannons_to_place: int:
	get: return players[0].cannons_to_place
	set(v): players[0].cannons_to_place = v
var _piece_shape: int:
	get: return players[0].piece_shape
	set(v): players[0].piece_shape = v


## `player_count` 2 or 3 plays versus (the map should have regions for that many players).
func _init(m: CoastMap = null, seed: int = 1, player_count: int = 1) -> void:
	if m == null:
		return
	map = m
	rng.seed = seed
	cells.resize(map.w * map.h)
	owner.resize(map.w * map.h)
	rubble.resize(map.w * map.h)
	territory.resize(map.w * map.h)
	versus = player_count > 1
	fleet = not versus
	for i in range(1, player_count):
		players.append(BastionPlayer.new(i))
	for pl in players:
		var mine: Array[int] = []
		if versus:
			mine = map.castles_of(pl.index)
		if not mine.is_empty():
			pl.cursor = Vector2(map.castles[mine[0]])
		else:
			pl.cursor = Vector2(map.castles[0]) if not map.castles.is_empty() else Vector2(map.w / 2, map.h / 2)


# ------------------------------------------------------------------ queries

func cell(x: int, y: int) -> int:
	return cells[y * map.w + x] if map.inside(x, y) else Cell.EMPTY


func is_ours(x: int, y: int, p: int = 0) -> bool:
	return map.inside(x, y) and territory[y * map.w + x] == p + 1


## The player whose wall or cannon stands on (x, y), or -1.
func owner_at(x: int, y: int) -> int:
	if not map.inside(x, y):
		return -1
	var i := y * map.w + x
	return owner[i] if cells[i] == Cell.WALL or cells[i] == Cell.CANNON else -1


## Player `p` (versus) may only build in their own region; -1 means anyone (the solo game).
func buildable(x: int, y: int, p: int = -1) -> bool:
	if not map.is_land(x, y) or map.castle_at(x, y) >= 0:
		return false
	if versus and p >= 0 and map.region_of(x, y) != p:
		return false
	var i := y * map.w + x
	if cells[i] != Cell.EMPTY:
		return false
	for s in ships:
		if Vector2i(s["pos"].round()) == Vector2i(x, y):
			return false
	return true


func piece_cells_at(origin: Vector2i, p: int = 0) -> Array[Vector2i]:
	var out: Array[Vector2i] = []
	for c in players[p].piece:
		out.append(origin + c)
	return out


func can_place_piece(origin: Vector2i, p: int = 0) -> bool:
	for c in piece_cells_at(origin, p):
		if not buildable(c.x, c.y, p):
			return false
	return true


func can_place_cannon(origin: Vector2i, p: int = 0) -> bool:
	for dy in 2:
		for dx in 2:
			var x := origin.x + dx
			var y := origin.y + dy
			if not buildable(x, y, p) or not is_ours(x, y, p):
				return false
	return true


## True if the player's current wall piece fits somewhere on the map, in any rotation.
func piece_fits_anywhere(p: int = 0) -> bool:
	for turns in 4:
		var cells_r := WallPieces.rotated(WallPieces.SHAPES[players[p].piece_shape], turns)
		for y in map.h:
			for x in map.w:
				var ok := true
				for c in cells_r:
					if not buildable(x + c.x, y + c.y, p):
						ok = false
						break
				if ok:
					return true
	return false


## True if a 2x2 cannon still fits somewhere inside the player's territory.
func cannon_fits_anywhere(p: int = 0) -> bool:
	for y in map.h:
		for x in map.w:
			if can_place_cannon(Vector2i(x, y), p):
				return true
	return false


## "piece" or "cannon" when the player's current placement is impossible anywhere (the timer keeps running).
func blocked(p: int = 0) -> String:
	var pl := players[p]
	if not pl.alive:
		return ""
	if phase == Phase.BUILD and not pl.piece.is_empty() and not piece_fits_anywhere(p):
		return "piece"
	if phase == Phase.CANNONS and pl.cannons_to_place > 0 and not cannon_fits_anywhere(p):
		return "cannon"
	return ""


## Active cannons of player `p`, or of everyone with -1.
func active_cannons(p: int = -1) -> int:
	var n := 0
	for c in cannons:
		if c["active"] and (p < 0 or c["player"] == p):
			n += 1
	return n


## The players still in the game (versus), in order.
func alive_players() -> Array[int]:
	var out: Array[int] = []
	for pl in players:
		if pl.alive:
			out.append(pl.index)
	return out


# ------------------------------------------------------------------ player actions

func move_cursor(delta: Vector2, p: int = 0) -> void:
	players[p].cursor = (players[p].cursor + delta).clamp(Vector2.ZERO, Vector2(map.w - 1, map.h - 1))


func rotate_piece(p: int = 0) -> void:
	var pl := players[p]
	if phase == Phase.BUILD and pl.alive:
		pl.piece_turns = (pl.piece_turns + 1) % 4
		pl.piece = WallPieces.rotated(WallPieces.SHAPES[pl.piece_shape], pl.piece_turns)
		_emit("rotated", {"player": p})


## The main button of player `p`: choose a castle, place a cannon or a wall piece, or fire, depending on the phase.
func act(p: int = 0) -> bool:
	var pl := players[p]
	if not pl.alive:
		return false
	var at := Vector2i(pl.cursor.round())
	match phase:
		Phase.CHOOSE:
			if pl.home_castle >= 0:
				return false  # versus: already chosen, waiting for the others
			var c := map.castle_at(at.x, at.y)
			if c < 0 or (versus and map.region_of(at.x, at.y) != p):
				c = _nearest_castle(pl.cursor, p)
			_claim_home(c, p)
			if _all_claimed():
				_start_cannons()
			return true
		Phase.CANNONS:
			if pl.cannons_to_place > 0 and can_place_cannon(at, p):
				_place_cannon(at, p)
				return true
		Phase.BUILD:
			if can_place_piece(at, p):
				for c in piece_cells_at(at, p):
					cells[c.y * map.w + c.x] = Cell.WALL
					owner[c.y * map.w + c.x] = p
				_emit("wall_placed", {"cells": piece_cells_at(at, p), "player": p})
				_compute_territory(false, p if versus else -1)
				_next_piece(p)
				return true
		Phase.BATTLE:
			return fire_at(pl.cursor, p)
	return false


func fire_at(target: Vector2, p: int = 0) -> bool:
	if not target.is_finite() or phase != Phase.BATTLE or phase_left <= 0.0 or not players[p].alive:
		return false  # no new shots once the battle clock is out: the round ends when the last balls land
	# the player's ready cannon closest to the target fires (one ball in flight per cannon)
	var best := -1
	var best_d := INF
	for i in cannons.size():
		var c := cannons[i]
		if not c["active"] or c["reload"] > 0.0 or c["player"] != p:
			continue
		var d := (Vector2(c["pos"]) + Vector2(0.5, 0.5)).distance_to(target)
		if d < best_d:
			best_d = d
			best = i
	if best < 0:
		return false
	var from := Vector2(cannons[best]["pos"]) + Vector2(0.5, 0.5)
	var dur := maxf(0.35, from.distance_to(target) / BALL_SPEED)
	# versus: a cannon reloads once its ball has landed (one ball in flight per cannon, as in the arcade game)
	cannons[best]["reload"] = CANNON_RELOAD + (dur if versus else 0.0)
	balls.append({"from": from, "to": target, "t": 0.0, "dur": dur, "ours": true, "player": p})
	_emit("shot", {"from": from, "to": target, "ours": true, "dur": dur, "player": p})
	return true


# ------------------------------------------------------------------ time

func tick() -> void:
	if phase == Phase.GAME_OVER:
		return
	phase_left -= TICK
	match phase:
		Phase.BATTLE:
			_tick_battle()
		Phase.CANNONS:
			var left := 0
			for pl in players:
				if pl.alive:
					left += pl.cannons_to_place
			if left <= 0:
				phase_left = minf(phase_left, 0.0)
	_tick_balls()
	if phase_left <= 0.0:
		_end_phase()


func _end_phase() -> void:
	match phase:
		Phase.CHOOSE:
			for pl in players:
				if pl.home_castle < 0:
					_claim_home(_nearest_castle(pl.cursor, pl.index), pl.index)
			_start_cannons()
		Phase.CANNONS:
			_start_battle()
		Phase.BATTLE:
			if balls.is_empty():
				_start_build()
			else:
				phase_left = 0.0  # wait for the last balls to land
		Phase.BUILD:
			_compute_territory(true)
			if versus:
				_end_versus_round()
			elif enclosed_castles.is_empty():
				phase = Phase.GAME_OVER
				_emit("game_over", {"score": score, "rounds": round_number})
			elif map.rounds > 0 and round_number >= map.rounds:
				won = true  # the island is held: the campaign sails on
				phase = Phase.GAME_OVER
				_emit("island_held", {"score": score, "rounds": round_number})
			else:
				_start_cannons()


## Versus: players without an enclosed castle are out; the last one standing (or the best score once the map's
## rounds are played) wins.
func _end_versus_round() -> void:
	var fell: Array[int] = []
	for pl in players:
		if pl.alive and pl.enclosed_castles.is_empty():
			pl.alive = false
			pl.out_round = round_number
			pl.piece.clear()
			pl.cannons_to_place = 0
			fell.append(pl.index)
			_ruin(pl.index)
			_emit("player_out", {"player": pl.index, "round": round_number})
	var alive := alive_players()
	if alive.size() > 1 and not (map.rounds > 0 and round_number >= map.rounds):
		_start_cannons()
		return
	var pool := alive if not alive.is_empty() else fell  # everyone fell at once: the best of them
	winner = pool[0]
	for p in pool:
		if players[p].score > players[winner].score:
			winner = p
	phase = Phase.GAME_OVER
	_emit("game_over", {"winner": winner, "score": players[winner].score, "rounds": round_number})


## A fallen player's walls crumble (ruins that stay for the next round) and their cannons are blown up.
func _ruin(p: int) -> void:
	for i in cells.size():
		if cells[i] == Cell.WALL and owner[i] == p:
			cells[i] = Cell.RUBBLE
			rubble[i] = RUBBLE_ROUNDS + 1
	for c in cannons.duplicate():
		if c["player"] != p:
			continue
		cannons.erase(c)
		var at: Vector2i = c["pos"]
		for dy in 2:
			for dx in 2:
				var j := (at.y + dy) * map.w + at.x + dx
				cells[j] = Cell.RUBBLE
				rubble[j] = RUBBLE_ROUNDS + 1
		_emit("cannon_destroyed", {"pos": c["pos"], "player": p})
	territory.fill(0)
	for pl in players:
		if pl.alive:
			_territory_of(pl, false)


func _all_claimed() -> bool:
	for pl in players:
		if pl.alive and pl.home_castle < 0:
			return false
	return true


func _set_phase(p: int, seconds: float) -> void:
	phase = p
	phase_left = seconds
	_emit("phase", {"phase": p, "round": round_number})


# ------------------------------------------------------------------ phases

func _claim_home(c: int, p: int = 0) -> void:
	players[p].home_castle = c
	var pos := map.castles[c]
	var r := HOME_RING
	for y in range(pos.y - r, pos.y + 2 + r):
		for x in range(pos.x - r, pos.x + 2 + r):
			var edge := y == pos.y - r or y == pos.y + 1 + r or x == pos.x - r or x == pos.x + 1 + r
			if edge and buildable(x, y, p) and cells[y * map.w + x] == Cell.EMPTY:
				cells[y * map.w + x] = Cell.WALL
				owner[y * map.w + x] = p
	_compute_territory(false)
	_emit("castle_claimed", {"castle": c, "player": p})


func _start_cannons() -> void:
	round_number += 1
	for i in rubble.size():
		if rubble[i] > 0:
			rubble[i] -= 1
			if rubble[i] == 0 and cells[i] == Cell.RUBBLE:
				cells[i] = Cell.EMPTY
	for pl in players:
		var extra := maxi(0, pl.enclosed_castles.size() - 1)
		pl.cannons_to_place = 0 if not pl.alive else (FIRST_ROUND_CANNONS if round_number == 1
			else CANNONS_PER_ROUND + CANNONS_PER_CASTLE * extra)
	for c in cannons:
		c["active"] = players[c["player"]].alive and is_ours(c["pos"].x, c["pos"].y, c["player"])
	# point each cursor at free space inside the player's territory
	for pl in players:
		if not pl.alive:
			continue
		var found := false
		for y in map.h:
			for x in map.w:
				if not found and can_place_cannon(Vector2i(x, y), pl.index):
					pl.cursor = Vector2(x, y)
					found = true
		if not found:
			pl.cannons_to_place = 0
	_set_phase(Phase.CANNONS, CANNON_SECONDS)


func _place_cannon(at: Vector2i, p: int = 0) -> void:
	for dy in 2:
		for dx in 2:
			cells[(at.y + dy) * map.w + at.x + dx] = Cell.CANNON
			owner[(at.y + dy) * map.w + at.x + dx] = p
	cannons.append({"pos": at, "reload": 0.0, "active": true, "player": p, "hp": CANNON_HP})
	players[p].cannons_to_place -= 1
	_emit("cannon_placed", {"pos": at, "player": p})


func _start_battle() -> void:
	if fleet:
		var count := 2 + round_number / 2  # a gentle ramp: one more ship every second round
		for i in count:
			_spawn_ship()
	_set_phase(Phase.BATTLE, BATTLE_SECONDS)


func _start_build() -> void:
	ships.clear()
	for pl in players:
		if pl.alive:
			_next_piece(pl.index)
	if versus:
		_compute_territory(false)  # the battle broke walls: fresh holes for the repair
	_set_phase(Phase.BUILD, BUILD_SECONDS)


func _next_piece(p: int = 0) -> void:
	var pl := players[p]
	pl.piece_shape = rng.randi_range(0, WallPieces.SHAPES.size() - 1)
	pl.piece_turns = rng.randi_range(0, 3)
	pl.piece = WallPieces.rotated(WallPieces.SHAPES[pl.piece_shape], pl.piece_turns)


# ------------------------------------------------------------------ battle

func _spawn_ship() -> void:
	# ships come in from a random water cell on the map edge and head for water near our walls
	var edge: Array[Vector2i] = []
	for x in map.w:
		for y in [0, map.h - 1]:
			if map.at(x, y) == CoastMap.Terrain.WATER:
				edge.append(Vector2i(x, y))
	for y in map.h:
		for x in [0, map.w - 1]:
			if map.at(x, y) == CoastMap.Terrain.WATER:
				edge.append(Vector2i(x, y))
	if edge.is_empty():
		return
	var start := edge[rng.randi_range(0, edge.size() - 1)]
	var size := 1 + mini(2, rng.randi_range(0, round_number) / 2)
	ships.append({"pos": Vector2(start), "target": _ship_anchor(), "hp": size, "size": size,
		"fire_in": SHIP_FIRE_EVERY * rng.randf_range(0.8, 1.6), "id": _next_ship_id})
	_next_ship_id += 1


func _ship_anchor() -> Vector2:
	# a water cell within range of one of our walls
	var walls := _our_walls()
	for attempt in 60:
		var x := rng.randi_range(PLAY_MARGIN, map.w - 1 - PLAY_MARGIN)
		var y := rng.randi_range(PLAY_MARGIN, map.h - 1 - PLAY_MARGIN)
		if map.at(x, y) != CoastMap.Terrain.WATER:
			continue
		for w in walls:
			if Vector2(w).distance_to(Vector2(x, y)) < SHIP_RANGE * 0.8:
				return Vector2(x, y)
	return Vector2(rng.randi_range(PLAY_MARGIN, map.w - 1 - PLAY_MARGIN), PLAY_MARGIN)


## The walls of player `p`, or everyone's with -1 (the solo game: all walls are ours).
func _our_walls(p: int = -1) -> Array[Vector2i]:
	var out: Array[Vector2i] = []
	for y in map.h:
		for x in map.w:
			var i := y * map.w + x
			if cells[i] == Cell.WALL and (p < 0 or owner[i] == p):
				out.append(Vector2i(x, y))
	return out


func _tick_battle() -> void:
	for c in cannons:
		c["reload"] = maxf(0.0, c["reload"] - TICK)
	for s in ships:
		var to_target: Vector2 = s["target"] - s["pos"]
		if to_target.length() > 0.1:
			var step := to_target.normalized() * SHIP_SPEED * TICK
			var next: Vector2 = s["pos"] + step
			if map.at(roundi(next.x), roundi(next.y)) == CoastMap.Terrain.WATER:
				s["pos"] = next
			else:
				s["target"] = _ship_anchor()
		s["fire_in"] -= TICK
		if s["fire_in"] <= 0.0 and phase_left > 0.5 and _in_play_area(s["pos"]):
			s["fire_in"] = SHIP_FIRE_EVERY * rng.randf_range(0.8, 1.3)
			var walls := _our_walls()
			var in_range: Array[Vector2i] = []
			for wc in walls:
				if Vector2(wc).distance_to(s["pos"]) < SHIP_RANGE:
					in_range.append(wc)
			if not in_range.is_empty():
				var target := Vector2(in_range[rng.randi_range(0, in_range.size() - 1)])
				var dur := maxf(0.5, target.distance_to(s["pos"]) / (BALL_SPEED * 0.7))
				balls.append({"from": s["pos"], "to": target, "t": 0.0, "dur": dur, "ours": false})
				_emit("shot", {"from": s["pos"], "to": target, "ours": false, "dur": dur, "ship": s["id"]})


func _tick_balls() -> void:
	var landed: Array[Dictionary] = []
	var flying: Array[Dictionary] = []
	for b in balls:
		b["t"] += TICK
		if not (b["t"] < b["dur"]):  # also lands a ball whose flight time is not a number, so no battle waits forever
			landed.append(b)
		else:
			flying.append(b)
	balls = flying
	for b in landed:
		if b["to"].is_finite():
			_impact(b)


func _impact(b: Dictionary) -> void:
	var at: Vector2 = b["to"]
	_emit("impact", {"at": at, "ours": b["ours"]})
	if b["ours"]:
		var hit_ship := false
		for s in ships.duplicate():
			if s["pos"].distance_to(at) < 0.5 + 0.25 * s["size"]:
				s["hp"] -= 1
				_emit("ship_hit", {"id": s["id"], "at": s["pos"]})
				if s["hp"] <= 0:
					ships.erase(s)
					ships_sunk += 1
					players[b.get("player", 0)].score += 100 * s["size"]
					_emit("ship_sunk", {"id": s["id"], "at": s["pos"], "size": s["size"]})
				hit_ship = true
				break
		if not hit_ship:
			if versus:  # players shell each other: walls break, cannons take hits, the land is cratered
				_damage_land(at, true, b.get("player", 0))
			else:
				_damage_land(at, false)  # friendly fire: our own walls break too (empty land is not cratered)
	else:
		_damage_land(at, true)


## A ball lands on the land: a wall there becomes rubble; empty land becomes a crater when `crater`. In versus a
## cannon hit loses a point of strength and turns to rubble at zero; `shooter` scores the enemy's losses.
func _damage_land(at: Vector2, crater: bool, shooter: int = -1) -> void:
	var c := Vector2i(at.round())
	if not map.inside(c.x, c.y) or not map.is_land(c.x, c.y) or map.castle_at(c.x, c.y) >= 0:
		return
	var i := c.y * map.w + c.x
	if versus and cells[i] == Cell.CANNON:
		_hit_cannon(c, shooter)
		return
	if cells[i] == Cell.WALL or (crater and cells[i] == Cell.EMPTY):
		var was_wall := cells[i] == Cell.WALL
		var wall_owner: int = owner[i]
		cells[i] = Cell.RUBBLE
		rubble[i] = RUBBLE_ROUNDS
		if was_wall:
			if versus and shooter >= 0 and wall_owner != shooter:
				players[shooter].score += WALL_POINTS
				players[shooter].walls_broken += 1
			_emit("wall_destroyed", {"at": c, "player": wall_owner})


func _hit_cannon(c: Vector2i, shooter: int) -> void:
	for k in cannons.size():
		var cn := cannons[k]
		var p: Vector2i = cn["pos"]
		if c.x < p.x or c.y < p.y or c.x > p.x + 1 or c.y > p.y + 1:
			continue
		cn["hp"] -= 1
		_emit("cannon_hit", {"pos": p, "player": cn["player"], "hp": cn["hp"]})
		if cn["hp"] <= 0:
			cannons.remove_at(k)
			for dy in 2:
				for dx in 2:
					var j := (p.y + dy) * map.w + p.x + dx
					cells[j] = Cell.RUBBLE
					rubble[j] = RUBBLE_ROUNDS
			if shooter >= 0 and shooter != cn["player"]:
				players[shooter].score += CANNON_POINTS
				players[shooter].cannons_broken += 1
			_emit("cannon_destroyed", {"pos": p, "player": cn["player"]})
		return


# ------------------------------------------------------------------ territory

## Enclosed land: every land cell not reachable from the water or the map edge without crossing a wall
## (4-connected, so walls touching at a corner still seal). Each player's own walls enclose their territory.
## Scores the territory when `final`. `only` >= 0: only that player's walls changed (their holes are updated).
func _compute_territory(final: bool, only: int = -1) -> void:
	territory.fill(0)
	var counts: Array[int] = []
	for pl in players:
		counts.append(_territory_of(pl, final) if pl.alive else 0)
	_update_holes(only)
	for pl in players:
		if pl.alive:
			var data := {"castles": pl.enclosed_castles.duplicate(), "cells": counts[pl.index], "final": final}
			if versus:
				data["player"] = pl.index
			_emit("enclosed", data)


func _territory_of(pl: BastionPlayer, final: bool) -> int:
	var p := pl.index
	var reach := PackedByteArray()
	reach.resize(map.w * map.h)
	var stack: Array[int] = []
	for y in map.h:
		for x in map.w:
			var i := y * map.w + x
			var outside := x == 0 or y == 0 or x == map.w - 1 or y == map.h - 1 or map.at(x, y) == CoastMap.Terrain.WATER
			if outside and _open(i, p):
				reach[i] = 1
				stack.append(i)
	while not stack.is_empty():
		var i: int = stack.pop_back()
		var x := i % map.w
		var y := i / map.w
		for d in [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]:
			var nx: int = x + d.x
			var ny: int = y + d.y
			if not map.inside(nx, ny):
				continue
			var j := ny * map.w + nx
			if reach[j] == 0 and _open(j, p):
				reach[j] = 1
				stack.append(j)
	# territory: only the enclosed areas that contain a castle (a sealed pocket without a castle is not ours)
	var mark := p + 1
	pl.enclosed_castles.clear()
	var cells_owned := 0
	for c in map.castles.size():
		var cp := map.castles[c]
		if versus and map.region_of(cp.x, cp.y) != p:
			continue
		var start := cp.y * map.w + cp.x
		if reach[start] == 1 or territory[start] != 0:
			if territory[start] == mark:
				pl.enclosed_castles.append(c)
			continue
		pl.enclosed_castles.append(c)
		var fill: Array[int] = [start]
		territory[start] = mark
		while not fill.is_empty():
			var i: int = fill.pop_back()
			cells_owned += 1
			var x := i % map.w
			var y := i / map.w
			for d in [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]:
				var nx: int = x + d.x
				var ny: int = y + d.y
				if not map.inside(nx, ny):
					continue
				var j := ny * map.w + nx
				if territory[j] == 0 and reach[j] == 0 and _open(j, p):
					territory[j] = mark
					fill.append(j)
	if final:
		pl.score += cells_owned * 2 + pl.enclosed_castles.size() * 250
	return cells_owned


func _in_play_area(p: Vector2) -> bool:
	return p.x >= PLAY_MARGIN and p.y >= PLAY_MARGIN and p.x <= map.w - 1 - PLAY_MARGIN and p.y <= map.h - 1 - PLAY_MARGIN


## Cells the outside can flow through for player `p`: anything but their walls and rocks.
func _open(i: int, p: int = 0) -> bool:
	return not (cells[i] == Cell.WALL and owner[i] == p) and map.terrain[i] != CoastMap.Terrain.ROCK


func _update_holes(only: int = -1) -> void:
	for pl in players:
		if only >= 0 and pl.index != only:
			continue
		pl.castle_holes.clear()
		if not pl.alive:
			continue
		for c in map.castles.size():
			var p := map.castles[c]
			if versus and map.region_of(p.x, p.y) != pl.index:
				continue
			if pl.enclosed_castles.has(c):
				pl.castle_holes[c] = [] as Array[Vector2i]
				continue
			# only castles the player is building around: the home castle, or their walls within 4 cells
			var near := c == pl.home_castle
			for y in range(p.y - 4, p.y + 6):
				for x in range(p.x - 4, p.x + 6):
					if not near and cell(x, y) == Cell.WALL and owner[y * map.w + x] == pl.index:
						near = true
			if near:
				pl.castle_holes[c] = holes_around(c, HOLE_LIMIT, pl.index)


## The holes of a castle's enclosure: the smallest set of cells that still need a wall so that the castle is
## sealed off from the sea (a minimum vertex cut between the castle and the outside, by max-flow). Empty if the
## castle is already enclosed; `limit` + 1 cells means "wide open" (more than `limit` holes). Cells that cannot
## take a wall (rubble, cannons) cannot be part of the cut, so the answer is a set you can actually build.
func holes_around(castle: int, limit: int = 12, player: int = 0) -> Array[Vector2i]:
	var n := map.w * map.h
	# node 2i = cell entry, 2i+1 = cell exit; SINK = 2n
	var sink := 2 * n
	var cap := {}  # edge key (a * 4 * n + b) -> residual capacity
	var adj: Array[PackedInt32Array] = []
	adj.resize(2 * n + 1)
	var big := 1 << 20

	var add_edge := func(a: int, b: int, c: int) -> void:
		var k1 := a * (2 * n + 1) + b
		var k2 := b * (2 * n + 1) + a
		if not cap.has(k1):
			adj[a].append(b)
			adj[b].append(a)
			cap[k1] = 0
			cap[k2] = cap.get(k2, 0)
		cap[k1] += c

	var castle_cells := {}
	var cp := map.castles[castle]
	for dy in 2:
		for dx in 2:
			castle_cells[(cp.y + dy) * map.w + cp.x + dx] = true
	for y in map.h:
		for x in map.w:
			var i := y * map.w + x
			if map.at(x, y) == CoastMap.Terrain.WATER:
				continue
			if _own_wall(i, player) or map.terrain[i] == CoastMap.Terrain.ROCK:
				continue
			var cuttable := cells[i] == Cell.EMPTY and not castle_cells.has(i) and map.castle_at(x, y) < 0 \
				and (not versus or map.region_of(x, y) == player)
			# closing a gap next to an existing wall is cheaper, so the cut follows the wall line
			var touches_wall := false
			for d in [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]:
				if cell(x + d.x, y + d.y) == Cell.WALL and owner_at(x + d.x, y + d.y) == player:
					touches_wall = true
			add_edge.call(2 * i, 2 * i + 1, (1 if touches_wall else 2) if cuttable else big)
			if x == 0 or y == 0 or x == map.w - 1 or y == map.h - 1:
				add_edge.call(2 * i + 1, sink, big)
			for d in [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]:
				var nx: int = x + d.x
				var ny: int = y + d.y
				if not map.inside(nx, ny):
					continue
				var j := ny * map.w + nx
				if map.at(nx, ny) == CoastMap.Terrain.WATER:
					add_edge.call(2 * i + 1, sink, big)
				elif not _own_wall(j, player) and map.terrain[j] != CoastMap.Terrain.ROCK:
					add_edge.call(2 * i + 1, 2 * j, big)
	var sources: Array[int] = []
	for i in castle_cells:
		if not _own_wall(i, player):
			sources.append(2 * i)
	# Edmonds-Karp from all castle cells to the sink
	var flow := 0
	while flow <= 2 * limit:
		var prev := {}
		var queue: Array[int] = []
		for src in sources:
			prev[src] = -1
			queue.append(src)
		var head := 0
		var found := false
		while head < queue.size() and not found:
			var u: int = queue[head]
			head += 1
			for v in adj[u]:
				if not prev.has(v) and cap.get(u * (2 * n + 1) + v, 0) > 0:
					prev[v] = u
					if v == sink:
						found = true
						break
					queue.append(v)
		if not found:
			break
		var bottleneck := big
		var v := sink
		while prev[v] != -1:
			bottleneck = mini(bottleneck, cap[prev[v] * (2 * n + 1) + v])
			v = prev[v]
		v = sink
		while prev[v] != -1:
			var u: int = prev[v]
			cap[u * (2 * n + 1) + v] -= bottleneck
			cap[v * (2 * n + 1) + u] = cap.get(v * (2 * n + 1) + u, 0) + bottleneck
			v = u
		flow += bottleneck
	var out: Array[Vector2i] = []
	if flow == 0:
		return out
	if flow > 2 * limit:
		for k in limit + 1:
			out.append(Vector2i(-1, -1))
		return out
	# the cut closest to the sea (so holes are the gaps in the wall line itself): cells whose exit can still
	# reach the sea in the residual graph but whose entry cannot
	var to_sea := {sink: true}
	var queue2: Array[int] = [sink]
	var h2 := 0
	while h2 < queue2.size():
		var v: int = queue2[h2]
		h2 += 1
		for u in adj[v]:
			if not to_sea.has(u) and cap.get(u * (2 * n + 1) + v, 0) > 0:
				to_sea[u] = true
				queue2.append(u)
	for i in n:
		if to_sea.has(2 * i + 1) and not to_sea.has(2 * i) and cap.get((2 * i) * (2 * n + 1) + 2 * i + 1, -1) == 0:
			out.append(Vector2i(i % map.w, i / map.w))
	if out.size() > limit:
		out.resize(limit + 1)
	return out


func _own_wall(i: int, p: int) -> bool:
	return cells[i] == Cell.WALL and owner[i] == p


## The castle nearest to `p`; in versus, among the castles of `player`'s region.
func _nearest_castle(p: Vector2, player: int = -1) -> int:
	var best := 0
	var best_d := INF
	var pool: Array[int] = []
	if versus and player >= 0:
		pool = map.castles_of(player)
	if pool.is_empty():
		for i in map.castles.size():
			pool.append(i)
	best = pool[0]
	for i in pool:
		var d := (Vector2(map.castles[i]) + Vector2(0.5, 0.5)).distance_to(p)
		if d < best_d:
			best_d = d
			best = i
	return best


func _emit(kind: String, data: Dictionary) -> void:
	event.emit(kind, data)
