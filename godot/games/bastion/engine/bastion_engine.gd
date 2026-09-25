class_name BastionEngine
extends RefCounted
## Rules of Bastion Coast (inspired by Rampart, 1990), one player against the sea. Pure logic, advanced in fixed
## ticks with a seeded random generator, so a game can be replayed from its inputs and tested without a view.
##
## A round is: CANNONS (place new cannons inside your territory), BATTLE (ships shell your walls, you shoot them),
## BUILD (repair with random wall pieces; at the end at least one castle must be enclosed or the game is over).
## The first round starts with CHOOSE (pick a home castle; walls are raised around it).
## Timings and counts are constants below; they are our own tuning, to be checked against the arcade game.

signal event(kind: String, data: Dictionary)  ## for the view and audio: "wall_placed", "cannon_placed", "shot",
## "impact", "ship_hit", "ship_sunk", "wall_destroyed", "phase", "enclosed", "game_over", "castle_claimed"

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

var map: CoastMap
var rng := RandomNumberGenerator.new()
var cells := PackedByteArray()   ## Cell per map cell
var rubble := PackedByteArray()  ## build phases left before rubble clears
var territory := PackedByteArray()  ## 1 where the land is enclosed by our walls
var cannons: Array[Dictionary] = []  ## {pos: Vector2i (top-left of 2x2), reload: float, active: bool}
var ships: Array[Dictionary] = []    ## {pos: Vector2, target: Vector2, hp: int, size: int, fire_in: float, id: int}
var balls: Array[Dictionary] = []    ## {from: Vector2, to: Vector2, t: float, dur: float, ours: bool}

var phase := Phase.CHOOSE
var phase_left := CHOOSE_SECONDS
var round_number := 0
var score := 0
var home_castle := -1
var enclosed_castles: Array[int] = []
var cursor := Vector2(0, 0)  ## in cells; during battle it is a free aim point
var piece: Array[Vector2i] = []
var piece_turns := 0
var cannons_to_place := 0
var ships_sunk := 0
var _piece_shape := 0
var _next_ship_id := 1


func _init(m: CoastMap = null, seed: int = 1) -> void:
	if m == null:
		return
	map = m
	rng.seed = seed
	cells.resize(map.w * map.h)
	rubble.resize(map.w * map.h)
	territory.resize(map.w * map.h)
	cursor = Vector2(map.castles[0]) if not map.castles.is_empty() else Vector2(map.w / 2, map.h / 2)


# ------------------------------------------------------------------ queries

func cell(x: int, y: int) -> int:
	return cells[y * map.w + x] if map.inside(x, y) else Cell.EMPTY


func is_ours(x: int, y: int) -> bool:
	return map.inside(x, y) and territory[y * map.w + x] == 1


func buildable(x: int, y: int) -> bool:
	if not map.is_land(x, y) or map.castle_at(x, y) >= 0:
		return false
	var i := y * map.w + x
	if cells[i] != Cell.EMPTY:
		return false
	for s in ships:
		if Vector2i(s["pos"].round()) == Vector2i(x, y):
			return false
	return true


func piece_cells_at(origin: Vector2i) -> Array[Vector2i]:
	var out: Array[Vector2i] = []
	for c in piece:
		out.append(origin + c)
	return out


func can_place_piece(origin: Vector2i) -> bool:
	for c in piece_cells_at(origin):
		if not buildable(c.x, c.y):
			return false
	return true


func can_place_cannon(origin: Vector2i) -> bool:
	for dy in 2:
		for dx in 2:
			var x := origin.x + dx
			var y := origin.y + dy
			if not buildable(x, y) or not is_ours(x, y):
				return false
	return true


func active_cannons() -> int:
	var n := 0
	for c in cannons:
		if c["active"]:
			n += 1
	return n


# ------------------------------------------------------------------ player actions

func move_cursor(delta: Vector2) -> void:
	cursor = (cursor + delta).clamp(Vector2.ZERO, Vector2(map.w - 1, map.h - 1))


func rotate_piece() -> void:
	if phase == Phase.BUILD:
		piece_turns = (piece_turns + 1) % 4
		piece = WallPieces.rotated(WallPieces.SHAPES[_piece_shape], piece_turns)
		_emit("rotated", {})


## The main button: choose a castle, place a cannon or a wall piece, or fire, depending on the phase.
func act() -> bool:
	var at := Vector2i(cursor.round())
	match phase:
		Phase.CHOOSE:
			var c := map.castle_at(at.x, at.y)
			if c < 0:
				c = _nearest_castle(cursor)
			_claim_home(c)
			return true
		Phase.CANNONS:
			if cannons_to_place > 0 and can_place_cannon(at):
				_place_cannon(at)
				return true
		Phase.BUILD:
			if can_place_piece(at):
				for p in piece_cells_at(at):
					cells[p.y * map.w + p.x] = Cell.WALL
				_emit("wall_placed", {"cells": piece_cells_at(at)})
				_compute_territory(false)
				_next_piece()
				return true
		Phase.BATTLE:
			return fire_at(cursor)
	return false


func fire_at(target: Vector2) -> bool:
	# the ready cannon closest to the target fires (one ball in flight per cannon)
	var best := -1
	var best_d := INF
	for i in cannons.size():
		var c := cannons[i]
		if not c["active"] or c["reload"] > 0.0:
			continue
		var d := (Vector2(c["pos"]) + Vector2(0.5, 0.5)).distance_to(target)
		if d < best_d:
			best_d = d
			best = i
	if best < 0:
		return false
	var from := Vector2(cannons[best]["pos"]) + Vector2(0.5, 0.5)
	cannons[best]["reload"] = CANNON_RELOAD
	var dur := maxf(0.35, from.distance_to(target) / BALL_SPEED)
	balls.append({"from": from, "to": target, "t": 0.0, "dur": dur, "ours": true})
	_emit("shot", {"from": from, "to": target, "ours": true, "dur": dur})
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
			if cannons_to_place <= 0:
				phase_left = minf(phase_left, 0.0)
	_tick_balls()
	if phase_left <= 0.0:
		_end_phase()


func _end_phase() -> void:
	match phase:
		Phase.CHOOSE:
			if home_castle < 0:
				_claim_home(_nearest_castle(cursor))
		Phase.CANNONS:
			_start_battle()
		Phase.BATTLE:
			if balls.is_empty():
				_start_build()
			else:
				phase_left = 0.0  # wait for the last balls to land
		Phase.BUILD:
			_compute_territory(true)
			if enclosed_castles.is_empty():
				phase = Phase.GAME_OVER
				_emit("game_over", {"score": score, "rounds": round_number})
			else:
				_start_cannons()


func _set_phase(p: int, seconds: float) -> void:
	phase = p
	phase_left = seconds
	_emit("phase", {"phase": p, "round": round_number})


# ------------------------------------------------------------------ phases

func _claim_home(c: int) -> void:
	home_castle = c
	var pos := map.castles[c]
	var r := HOME_RING
	for y in range(pos.y - r, pos.y + 2 + r):
		for x in range(pos.x - r, pos.x + 2 + r):
			var edge := y == pos.y - r or y == pos.y + 1 + r or x == pos.x - r or x == pos.x + 1 + r
			if edge and map.is_land(x, y) and map.castle_at(x, y) < 0:
				cells[y * map.w + x] = Cell.WALL
	_compute_territory(false)
	_emit("castle_claimed", {"castle": c})
	_start_cannons()


func _start_cannons() -> void:
	round_number += 1
	for i in rubble.size():
		if rubble[i] > 0:
			rubble[i] -= 1
			if rubble[i] == 0 and cells[i] == Cell.RUBBLE:
				cells[i] = Cell.EMPTY
	var extra := maxi(0, enclosed_castles.size() - 1)
	cannons_to_place = FIRST_ROUND_CANNONS if round_number == 1 else CANNONS_PER_ROUND + CANNONS_PER_CASTLE * extra
	for c in cannons:
		c["active"] = is_ours(c["pos"].x, c["pos"].y)
	# point the cursor at free space inside the territory
	for y in map.h:
		for x in map.w:
			if can_place_cannon(Vector2i(x, y)):
				cursor = Vector2(x, y)
				_set_phase(Phase.CANNONS, CANNON_SECONDS)
				return
	cannons_to_place = 0
	_set_phase(Phase.CANNONS, CANNON_SECONDS)


func _place_cannon(at: Vector2i) -> void:
	for dy in 2:
		for dx in 2:
			cells[(at.y + dy) * map.w + at.x + dx] = Cell.CANNON
	cannons.append({"pos": at, "reload": 0.0, "active": true})
	cannons_to_place -= 1
	_emit("cannon_placed", {"pos": at})


func _start_battle() -> void:
	var count := 2 + round_number / 2  # a gentle ramp: one more ship every second round
	for i in count:
		_spawn_ship()
	_set_phase(Phase.BATTLE, BATTLE_SECONDS)


func _start_build() -> void:
	ships.clear()
	_next_piece()
	_set_phase(Phase.BUILD, BUILD_SECONDS)


func _next_piece() -> void:
	_piece_shape = rng.randi_range(0, WallPieces.SHAPES.size() - 1)
	piece_turns = rng.randi_range(0, 3)
	piece = WallPieces.rotated(WallPieces.SHAPES[_piece_shape], piece_turns)


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


func _our_walls() -> Array[Vector2i]:
	var out: Array[Vector2i] = []
	for y in map.h:
		for x in map.w:
			if cells[y * map.w + x] == Cell.WALL:
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
	for b in balls:
		b["t"] += TICK
		if b["t"] >= b["dur"]:
			landed.append(b)
	for b in landed:
		balls.erase(b)
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
					score += 100 * s["size"]
					_emit("ship_sunk", {"id": s["id"], "at": s["pos"], "size": s["size"]})
				hit_ship = true
				break
		if not hit_ship:
			_damage_land(at, false)  # friendly fire: our own walls break too (empty land is not cratered)
	else:
		_damage_land(at, true)


## A ball lands on the land: a wall there becomes rubble; empty land becomes a crater when `crater`.
func _damage_land(at: Vector2, crater: bool) -> void:
	var c := Vector2i(at.round())
	if not map.inside(c.x, c.y) or not map.is_land(c.x, c.y) or map.castle_at(c.x, c.y) >= 0:
		return
	var i := c.y * map.w + c.x
	if cells[i] == Cell.WALL or (crater and cells[i] == Cell.EMPTY):
		var was_wall := cells[i] == Cell.WALL
		cells[i] = Cell.RUBBLE
		rubble[i] = RUBBLE_ROUNDS
		if was_wall:
			_emit("wall_destroyed", {"at": c})


# ------------------------------------------------------------------ territory

## Enclosed land: every land cell not reachable from the water or the map edge without crossing a wall
## (4-connected, so walls touching at a corner still seal). Scores the territory when `final`.
func _compute_territory(final: bool) -> void:
	var reach := PackedByteArray()
	reach.resize(map.w * map.h)
	var stack: Array[int] = []
	for y in map.h:
		for x in map.w:
			var i := y * map.w + x
			var outside := x == 0 or y == 0 or x == map.w - 1 or y == map.h - 1 or map.at(x, y) == CoastMap.Terrain.WATER
			if outside and _open(i):
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
			if reach[j] == 0 and _open(j):
				reach[j] = 1
				stack.append(j)
	var cells_owned := 0
	for i in territory.size():
		territory[i] = 1 if reach[i] == 0 and cells[i] != Cell.WALL else 0
		cells_owned += territory[i]
	enclosed_castles.clear()
	for c in map.castles.size():
		var p := map.castles[c]
		if territory[p.y * map.w + p.x] == 1:
			enclosed_castles.append(c)
	if final:
		score += cells_owned * 2 + enclosed_castles.size() * 250
	_emit("enclosed", {"castles": enclosed_castles.duplicate(), "cells": cells_owned, "final": final})


func _in_play_area(p: Vector2) -> bool:
	return p.x >= PLAY_MARGIN and p.y >= PLAY_MARGIN and p.x <= map.w - 1 - PLAY_MARGIN and p.y <= map.h - 1 - PLAY_MARGIN


## Cells the outside can flow through: anything but walls and rocks.
func _open(i: int) -> bool:
	return cells[i] != Cell.WALL and map.terrain[i] != CoastMap.Terrain.ROCK


func _nearest_castle(p: Vector2) -> int:
	var best := 0
	var best_d := INF
	for i in map.castles.size():
		var d := (Vector2(map.castles[i]) + Vector2(0.5, 0.5)).distance_to(p)
		if d < best_d:
			best_d = d
			best = i
	return best


func _emit(kind: String, data: Dictionary) -> void:
	event.emit(kind, data)
