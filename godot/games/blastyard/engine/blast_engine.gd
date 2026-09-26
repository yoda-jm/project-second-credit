class_name BlastEngine
extends RefCounted
## Blastyard rules (inspired by Bomberman, 1983; our own tuning), at fixed 60 Hz ticks with a seeded generator, so
## a demo replays the same. Bombers walk the grid (cornering is helped: a bomber a little off the lane slides onto
## it), drop bombs that blow after a fuse in a cross as long as their fire, set off other bombs, burst crates (which
## may leave a power-up) and catch anyone standing in the flames. Kick sends a bomb sliding. When the round clock
## runs out, sudden death: blocks slam down in a spiral from the edge. Solo stages add enemies and an exit hidden
## under a crate that opens once every enemy is gone.
## Events for the view, HUD and audio: "bomb", "explode", "crate", "powerup", "pickup", "kick", "bump", "death",
## "enemy_die", "hurry", "block_drop", "exit_open", "stage_clear", "round_over".

signal event(kind: String, data: Dictionary)

enum Phase { PLAY, OVER }
const T = ArenaMap.T
const TICK := 1.0 / 60.0
const FUSE := 2.6
const FLAME_TIME := 0.55
const KICK_SPEED := 9.0  ## cells per second
const BASE_SPEED := 3.3
const SPEED_STEP := 0.55
const MAX_SPEED := 6.0
const ASSIST := 0.42  ## how far off a lane a bomber may be and still turn into it
const DROP_CHANCE := 0.32
const POWERUPS := ["bomb", "bomb", "fire", "fire", "speed", "kick", "skull"]
const ENEMY_SPEED := {"blob": 1.4, "bat": 2.4, "ghost": 1.3, "stomper": 2.0}

var map: ArenaMap
var rng := RandomNumberGenerator.new()
var phase := Phase.PLAY
var time := 0.0
var ticks := 0
var players: Array[Dictionary] = []
var bombs: Array[Dictionary] = []
var flames := {}      ## cell -> seconds left burning
var powerups := {}    ## cell -> kind
var enemies: Array[Dictionary] = []
var exit_open := false
var winner := -1      ## the slot that won the round, -1 draw, -2 not over
var sudden := false
var _dropped := 0
var _drop_t := 0.0
var _spiral: Array[Vector2i] = []
var _next_id := 1
var _end_t := -1.0


func _init(m: ArenaMap, slots: int, seed_: int) -> void:
	map = m
	rng.seed = seed_
	for i in mini(slots, m.starts.size()):
		players.append({"slot": i, "id": _id(), "pos": Vector2(m.starts[i]) + Vector2(0.5, 0.5), "dir": Vector2i(0, 1),
			"alive": true, "bombs": 1, "fire": 2, "speed": BASE_SPEED, "kick": false, "skull": 0.0, "moving": false,
			"input": Vector2i.ZERO, "want_bomb": false, "kills": 0})
	for e in m.enemies:
		enemies.append({"id": _id(), "kind": e["kind"], "pos": Vector2(e["cell"]) + Vector2(0.5, 0.5),
			"dir": [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)][rng.randi_range(0, 3)], "alive": true})
	_spiral = _make_spiral()
	winner = -2


func _id() -> int:
	_next_id += 1
	return _next_id - 1


## Input for a slot this tick: a direction (one axis) and whether the bomb button went down.
func set_input(slot: int, dir: Vector2i, bomb: bool) -> void:
	for p in players:
		if p["slot"] == slot:
			p["input"] = dir
			if bomb:
				p["want_bomb"] = true


func player(slot: int) -> Dictionary:
	for p in players:
		if p["slot"] == slot:
			return p
	return {}


func alive_players() -> Array[Dictionary]:
	var out: Array[Dictionary] = []
	for p in players:
		if p["alive"]:
			out.append(p)
	return out


func bomb_at(c: Vector2i) -> Dictionary:
	for b in bombs:
		if b["cell"] == c:
			return b
	return {}


func cell_of(pos: Vector2) -> Vector2i:
	return Vector2i(pos.floor())


## Can a walker enter this cell? (Bombs block, except the one the walker is still standing on.)
func open(c: Vector2i, ghost := false) -> bool:
	var t := map.at(c)
	if t == T.PILLAR or (t == T.CRATE and not ghost):
		return false
	return bomb_at(c).is_empty()


# ------------------------------------------------------------------ the tick

func tick() -> void:
	ticks += 1
	time += TICK
	if phase == Phase.OVER:
		return
	for p in players:
		if p["alive"]:
			_move_player(p)
			_place(p)
	_tick_bombs()
	_tick_flames()
	_tick_enemies()
	_touch()
	if not map.solo:
		_sudden_death()
	_check_end()


func _speed(p: Dictionary) -> float:
	var s: float = p["speed"]
	if p["skull"] > 0.0:
		s = BASE_SPEED * 0.6
	return s


func _move_player(p: Dictionary) -> void:
	p["skull"] = maxf(0.0, p["skull"] - TICK)
	var d: Vector2i = p["input"]
	if p["skull"] > 0.0:
		d = -d  # the skull scrambles the controls
	p["moving"] = d != Vector2i.ZERO
	if d == Vector2i.ZERO:
		return
	p["dir"] = d
	var step := _speed(p) * TICK
	var pos: Vector2 = p["pos"]
	var c := cell_of(pos)
	var centre := Vector2(c) + Vector2(0.5, 0.5)
	var ahead := c + d
	# the lane across the move: slide onto its centre first (turning into side passages feels easy)
	var off := (pos - centre)
	var across := off.y if d.x != 0 else off.x
	if absf(across) > 0.01:
		# if the way ahead is blocked but the next lane over is open, slide towards it (cornering assist)
		var sgn := 1 if across > 0.0 else -1
		var side := Vector2i(0, sgn) if d.x != 0 else Vector2i(sgn, 0)
		var target := centre
		if not _can_enter(p, ahead) and absf(across) > 0.12 and _can_enter(p, c + side + d) and _can_enter(p, c + side):
			target = Vector2(c + side) + Vector2(0.5, 0.5)
		if d.x != 0:
			pos.y = move_toward(pos.y, target.y, step)
		else:
			pos.x = move_toward(pos.x, target.x, step)
		if absf((pos - target).y if d.x != 0 else (pos - target).x) > 0.02:
			p["pos"] = pos
			return
	# along the move: up to the cell edge unless the next cell is open
	var along := (pos - centre).dot(Vector2(d))
	if _can_enter(p, ahead):
		pos += Vector2(d) * step
	elif along < 0.0:
		pos += Vector2(d) * minf(step, -along)
	else:
		var b := bomb_at(ahead)
		if not b.is_empty() and p["kick"] and b.get("slide", Vector2i.ZERO) == Vector2i.ZERO:
			b["slide"] = d
			event.emit("kick", {"cell": ahead, "slot": p["slot"]})
	p["pos"] = pos


func _can_enter(p: Dictionary, c: Vector2i) -> bool:
	var t := map.at(c)
	if t == T.PILLAR or t == T.CRATE:
		return false
	var b := bomb_at(c)
	if b.is_empty():
		return true
	return cell_of(p["pos"]) == c  # the bomb just dropped under your feet


func _place(p: Dictionary) -> void:
	if not p["want_bomb"]:
		return
	p["want_bomb"] = false
	var c := cell_of(p["pos"])
	if not bomb_at(c).is_empty():
		return
	var out := bombs.filter(func(b): return b["owner"] == p["slot"]).size()
	if out >= p["bombs"]:
		return
	bombs.append({"id": _id(), "cell": c, "pos": Vector2(c) + Vector2(0.5, 0.5), "owner": p["slot"], "fuse": FUSE,
		"fire": p["fire"], "slide": Vector2i.ZERO})
	event.emit("bomb", {"cell": c, "slot": p["slot"]})


func _tick_bombs() -> void:
	var boom: Array[Dictionary] = []
	for b in bombs:
		b["fuse"] -= TICK
		var s: Vector2i = b["slide"]
		if s != Vector2i.ZERO:  # a kicked bomb slides until something stops it
			var np: Vector2 = b["pos"] + Vector2(s) * KICK_SPEED * TICK
			var nc := cell_of(np + Vector2(s) * 0.49)
			var blocked: bool = map.at(nc) != T.FLOOR or (not bomb_at(nc).is_empty() and nc != b["cell"]) \
				or players.any(func(p): return p["alive"] and cell_of(p["pos"]) == nc and nc != b["cell"]) \
				or enemies.any(func(e): return e["alive"] and cell_of(e["pos"]) == nc and nc != b["cell"])
			if blocked:
				b["slide"] = Vector2i.ZERO
				b["pos"] = Vector2(b["cell"]) + Vector2(0.5, 0.5)
				event.emit("bump", {"cell": b["cell"]})
			else:
				b["pos"] = np
				b["cell"] = cell_of(np)
		if b["fuse"] <= 0.0:
			boom.append(b)
	for b in boom:
		if bombs.has(b):
			_explode(b)


func _explode(b: Dictionary) -> void:
	bombs.erase(b)
	var c: Vector2i = b["cell"]
	var cells: Array[Vector2i] = [c]
	var chain: Array[Dictionary] = []
	for d in [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]:
		for k in range(1, b["fire"] + 1):
			var cc: Vector2i = c + d * k
			var t := map.at(cc)
			if t == T.PILLAR:
				break
			cells.append(cc)
			if t == T.CRATE:
				_burst_crate(cc)
				break
			var other := bomb_at(cc)
			if not other.is_empty():
				chain.append(other)
				break
			if powerups.has(cc):
				powerups.erase(cc)  # flames eat power-ups lying in the open
				break
	for cc in cells:
		flames[cc] = FLAME_TIME
	event.emit("explode", {"cell": c, "cells": cells, "fire": b["fire"], "owner": b["owner"], "chain": not chain.is_empty()})
	for o in chain:
		if bombs.has(o):
			o["fuse"] = minf(o["fuse"], 0.08)  # the chain goes off a moment later, so it reads


func _burst_crate(c: Vector2i) -> void:
	map.set_at(c, T.FLOOR)
	var drop := ""
	if c == map.exit_cell:
		event.emit("crate", {"cell": c, "drop": "", "exit": true})
		return
	if rng.randf() < DROP_CHANCE:
		drop = POWERUPS[rng.randi_range(0, POWERUPS.size() - 1)]
		if map.solo and drop == "skull":
			drop = "bomb"
		powerups[c] = drop
	event.emit("crate", {"cell": c, "drop": drop, "exit": false})


func _tick_flames() -> void:
	for c in flames.keys():
		flames[c] -= TICK
		if flames[c] <= 0.0:
			flames.erase(c)


func _touch() -> void:
	for p in players:
		if not p["alive"]:
			continue
		var c := cell_of(p["pos"])
		if flames.has(c):
			_kill(p)
			continue
		if powerups.has(c):
			var k: String = powerups[c]
			powerups.erase(c)
			match k:
				"bomb": p["bombs"] = mini(8, p["bombs"] + 1)
				"fire": p["fire"] = mini(10, p["fire"] + 1)
				"speed": p["speed"] = minf(MAX_SPEED, p["speed"] + SPEED_STEP)
				"kick": p["kick"] = true
				"skull": p["skull"] = 10.0
			event.emit("pickup", {"cell": c, "kind": k, "slot": p["slot"]})
		for e in enemies:
			if e["alive"] and e["pos"].distance_to(p["pos"]) < 0.6:
				_kill(p)
				break
		if map.solo and exit_open and c == map.exit_cell:
			phase = Phase.OVER
			winner = p["slot"]
			event.emit("stage_clear", {"slot": p["slot"]})
			return
	for e in enemies:
		if e["alive"] and flames.has(cell_of(e["pos"])):
			e["alive"] = false
			event.emit("enemy_die", {"id": e["id"], "pos": e["pos"], "kind": e["kind"]})
	if map.solo and not exit_open and enemies.all(func(e): return not e["alive"]) and map.at(map.exit_cell) == T.FLOOR:
		exit_open = true
		event.emit("exit_open", {"cell": map.exit_cell})


func _kill(p: Dictionary) -> void:
	p["alive"] = false
	p["moving"] = false
	event.emit("death", {"slot": p["slot"], "pos": p["pos"]})


# ------------------------------------------------------------------ enemies

func _tick_enemies() -> void:
	for e in enemies:
		if not e["alive"]:
			continue
		var ghost: bool = e["kind"] == "ghost"
		var pos: Vector2 = e["pos"]
		var c := cell_of(pos)
		var centre := Vector2(c) + Vector2(0.5, 0.5)
		var d: Vector2i = e["dir"]
		var step: float = ENEMY_SPEED[e["kind"]] * TICK
		if pos.distance_to(centre) <= step:  # at a crossing: keep going, turn, or hunt
			pos = centre
			var options: Array[Vector2i] = []
			for nd in [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]:
				if _enemy_open(c + nd, ghost) and nd != -d:
					options.append(nd)
			if e["kind"] == "stomper":
				var hunt := _towards_player(c)
				if hunt != Vector2i.ZERO and _enemy_open(c + hunt, ghost):
					d = hunt
			if not _enemy_open(c + d, ghost) or (e["kind"] == "bat" and rng.randf() < 0.3) or (rng.randf() < 0.15 and not options.is_empty()):
				if options.is_empty():
					d = -d if _enemy_open(c - d, ghost) else Vector2i.ZERO
				else:
					d = options[rng.randi_range(0, options.size() - 1)]
			e["dir"] = d
		if d != Vector2i.ZERO and _enemy_open(cell_of(pos + Vector2(d) * 0.51), ghost):
			pos += Vector2(d) * step
		e["pos"] = pos


func _enemy_open(c: Vector2i, ghost: bool) -> bool:
	var t := map.at(c)
	if t == T.PILLAR or (t == T.CRATE and not ghost):
		return false
	return bomb_at(c).is_empty() and map.inside(c) and c.x > 0 and c.y > 0 and c.x < map.w - 1 and c.y < map.h - 1


## The first step of the shortest way to the nearest bomber within 7 cells, or zero.
func _towards_player(from: Vector2i) -> Vector2i:
	var targets := {}
	for p in players:
		if p["alive"]:
			targets[cell_of(p["pos"])] = true
	var first := {from: Vector2i.ZERO}
	var queue: Array[Vector2i] = [from]
	var head := 0
	while head < queue.size() and head < 200:
		var c := queue[head]
		head += 1
		if targets.has(c) and c != from:
			return first[c]
		if absi(c.x - from.x) + absi(c.y - from.y) > 7:
			continue
		for d in [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]:
			var n: Vector2i = c + d
			if not first.has(n) and _enemy_open(n, false):
				first[n] = d if c == from else first[c]
				queue.append(n)
	return Vector2i.ZERO


# ------------------------------------------------------------------ sudden death and the end

func _make_spiral() -> Array[Vector2i]:
	var out: Array[Vector2i] = []
	var x0 := 1
	var y0 := 1
	var x1 := map.w - 2
	var y1 := map.h - 2
	while x0 <= x1 and y0 <= y1 and out.size() < map.w * map.h:
		for x in range(x0, x1 + 1): out.append(Vector2i(x, y0))
		for y in range(y0 + 1, y1 + 1): out.append(Vector2i(x1, y))
		for x in range(x1 - 1, x0 - 1, -1): out.append(Vector2i(x, y1))
		for y in range(y1 - 1, y0, -1): out.append(Vector2i(x0, y))
		x0 += 1; y0 += 1; x1 -= 1; y1 -= 1
	return out


func _sudden_death() -> void:
	if time < map.time:
		return
	if not sudden:
		sudden = true
		event.emit("hurry", {})
	_drop_t -= TICK
	while _drop_t <= 0.0 and _dropped < _spiral.size():
		_drop_t += 0.22
		var c := _spiral[_dropped]
		_dropped += 1
		if map.at(c) == T.PILLAR:
			continue
		map.set_at(c, T.PILLAR)
		powerups.erase(c)
		var b := bomb_at(c)
		if not b.is_empty():
			bombs.erase(b)
		for p in players:
			if p["alive"] and cell_of(p["pos"]) == c:
				_kill(p)
		event.emit("block_drop", {"cell": c})


func _check_end() -> void:
	if map.solo:
		if alive_players().is_empty():
			phase = Phase.OVER
			winner = -1
			event.emit("round_over", {"winner": -1})
		return
	var alive := alive_players()
	if alive.size() <= 1 and _end_t < 0.0:
		_end_t = time + 1.0  # a short grace: both caught in the same blast is a draw
	if _end_t >= 0.0 and time >= _end_t:
		alive = alive_players()
		phase = Phase.OVER
		winner = alive[0]["slot"] if alive.size() == 1 else -1
		event.emit("round_over", {"winner": winner})
