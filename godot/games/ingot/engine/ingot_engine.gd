class_name IngotEngine
extends RefCounted
## Ingot Run rules (inspired by Lode Runner, 1983; our own timings), at fixed 60 Hz ticks, seeded. Actors move from
## cell to cell; every choice is made at a cell. The runner runs, climbs ladders, goes hand over hand along bars,
## falls when nothing holds them, and blasts a hole in the brick below-left or below-right. Holes stay open a few
## seconds, then refill: whoever is inside is buried. Guards hunt the runner along the shortest way, pick up gold
## and drop it again, fall into holes and stay stuck a moment (the runner can walk over their heads), climb out, and
## come back at the top when buried. Take all the gold: the hidden ladders appear; climb out at the top to win.
## Events: "gold", "dig", "refill", "trapped", "escape", "crushed", "respawn", "all_gold", "died", "cleared", "land".

signal event(kind: String, data: Dictionary)

enum Phase { PLAY, DEAD, CLEARED }
const T = IngotLevel.T
const TICK := 1.0 / 60.0
const RUNNER_SPEED := 4.6   ## cells per second
const GUARD_SPEED := 2.7
const FALL_SPEED := 7.5
const DIG_TIME := 0.28
const HOLE_OPEN := 6.5      ## seconds a hole stays open
const HOLE_REFILL := 0.9    ## then it closes over this long
const TRAPPED := 2.6        ## seconds a guard stays stuck in a hole
const RESPAWN := 1.2
const DIRS := {"left": Vector2i(-1, 0), "right": Vector2i(1, 0), "up": Vector2i(0, -1), "down": Vector2i(0, 1)}

var level: IngotLevel
var tiles := PackedByteArray()
var holes := {}          ## cell -> seconds since dug
var gold := {}           ## cell -> true (on the ground)
var runner := {}
var guards: Array[Dictionary] = []
var phase := Phase.PLAY
var time := 0.0
var ticks := 0
var score := 0
var revealed := false
var input := Vector2i.ZERO   ## held direction
var dig_left := false
var dig_right := false
var rng := RandomNumberGenerator.new()


func _init(lv: IngotLevel, seed_: int) -> void:
	level = lv
	rng.seed = seed_
	tiles = lv.tiles.duplicate()
	for c in lv.gold:
		gold[c] = true
	runner = _actor(lv.runner, true)
	for c in lv.guards:
		guards.append(_actor(c, false))


func _actor(c: Vector2i, is_runner: bool) -> Dictionary:
	return {"cell": c, "to": c, "t": 0.0, "state": "stand", "face": 1, "runner": is_runner, "gold": false,
		"timer": 0.0, "gold_hold": 0.0, "speed": RUNNER_SPEED if is_runner else GUARD_SPEED * rng.randf_range(0.92, 1.05)}


# ------------------------------------------------------------------ the grid

func at(c: Vector2i) -> int:
	if c.x < 0 or c.x >= level.w or c.y >= level.h:
		return T.SOLID
	if c.y < 0:
		return T.EMPTY
	var t: int = tiles[c.y * level.w + c.x]
	if t == T.HIDDEN_LADDER:
		return T.LADDER if revealed else T.EMPTY
	if t == T.BRICK and holes.has(c):
		return T.EMPTY
	return t


## Can an actor stand in or pass through this cell?
func passable(c: Vector2i) -> bool:
	var t := at(c)
	return t != T.BRICK and t != T.SOLID


func guard_at(c: Vector2i, except: Dictionary = {}) -> Dictionary:
	for g in guards:
		if g != except and g["state"] != "respawn" and (g["cell"] == c or (g["state"] == "move" and g["to"] == c)):
			return g
	return {}


## Does something hold an actor in cell c (no fall)?
func supported(c: Vector2i, a: Dictionary) -> bool:
	var here := at(c)
	if here == T.LADDER or here == T.BAR:
		return true
	var below := c + Vector2i(0, 1)
	var b := at(below)
	if b == T.BRICK or b == T.SOLID or b == T.LADDER:
		return true
	var g := guard_at(below, a)
	if not g.is_empty() and (g["state"] == "trapped" or g["state"] == "stand" or g["state"] == "move"):
		return true  # standing on a guard's head
	if not a.get("runner", false) and holes.has(c):
		return true  # a guard in a hole stays there
	return false


func pos(a: Dictionary) -> Vector2:
	return Vector2(a["cell"]).lerp(Vector2(a["to"]), a["t"])


# ------------------------------------------------------------------ the tick

func tick() -> void:
	ticks += 1
	time += TICK
	if phase != Phase.PLAY:
		return
	_tick_holes()
	_step_runner()
	for g in guards:
		_step_guard(g)
	_collide()


func _tick_holes() -> void:
	for c in holes.keys():
		holes[c] += TICK
		if holes[c] >= HOLE_OPEN + HOLE_REFILL:
			holes.erase(c)
			event.emit("refill", {"cell": c})
			if runner["cell"] == c or (runner["state"] == "move" and runner["to"] == c and runner["t"] > 0.5):
				_die("buried")
			for g in guards:
				if g["cell"] == c and g["state"] != "respawn":
					_bury(g)


func _step_runner() -> void:
	var a := runner
	if a["state"] == "dig":
		a["timer"] -= TICK
		if a["timer"] <= 0.0:
			a["state"] = "stand"
		return
	if a["state"] == "move" or a["state"] == "fall":
		_advance(a)
		return
	# at a cell: fall, dig, or take the held direction
	var c: Vector2i = a["cell"]
	if revealed and c.y == 0 and at(c) == T.LADDER and input.y < 0:
		phase = Phase.CLEARED
		score += 1500
		event.emit("cleared", {})
		return
	if not supported(c, a):
		_start(a, c + Vector2i(0, 1), true)
		return
	if dig_left or dig_right:
		var side := -1 if dig_left else 1
		dig_left = false
		dig_right = false
		if _can_dig(c, side):
			var target := c + Vector2i(side, 1)
			holes[target] = 0.0
			a["face"] = side
			a["state"] = "dig"
			a["timer"] = DIG_TIME
			event.emit("dig", {"cell": target, "side": side})
			return
	if input != Vector2i.ZERO:
		var d := input
		if d.x != 0:
			a["face"] = d.x
		var n := c + d
		if _can_move(c, d, a):
			_start(a, n, false)


func _can_dig(c: Vector2i, side: int) -> bool:
	var target := c + Vector2i(side, 1)
	var above := c + Vector2i(side, 0)
	if target.x < 0 or target.x >= level.w or target.y >= level.h or tiles[target.y * level.w + target.x] != T.BRICK:
		return false  # only plain brick digs (not stone, not a trap brick)
	if holes.has(target):
		return false
	var ab := at(above)
	if ab == T.BRICK or ab == T.SOLID or ab == T.LADDER or gold.has(above):
		return false
	return guard_at(above).is_empty() and guard_at(target).is_empty()


func _can_move(c: Vector2i, d: Vector2i, a: Dictionary) -> bool:
	var n := c + d
	if not passable(n):
		return false
	if d.y < 0:
		return at(c) == T.LADDER
	if d.y > 0:
		return true  # down a ladder, off a bar, or into the open
	return true


func _start(a: Dictionary, to: Vector2i, falling: bool) -> void:
	a["to"] = to
	a["t"] = 0.0
	a["state"] = "fall" if falling else "move"


func _advance(a: Dictionary) -> void:
	var speed: float = FALL_SPEED if a["state"] == "fall" else a["speed"]
	a["t"] += speed * TICK
	if a["t"] < 1.0:
		return
	var was_falling: bool = a["state"] == "fall"
	a["cell"] = a["to"]
	a["t"] = 0.0
	a["state"] = "stand"
	var c: Vector2i = a["cell"]
	if a["runner"]:
		if gold.has(c):
			gold.erase(c)
			score += 250
			event.emit("gold", {"cell": c, "left": _gold_left()})
			_check_all_gold()
		if was_falling and supported(c, a):
			event.emit("land", {"cell": c})
	else:
		if holes.has(c):
			_trap(a)  # a guard that lands in a hole is stuck there
		elif gold.has(c) and not a["gold"] and rng.randf() < 0.5:
			gold.erase(c)
			a["gold"] = true
			a["gold_hold"] = rng.randf_range(2.0, 7.0)


func _gold_left() -> int:
	var n := gold.size()
	for g in guards:
		if g["gold"]:
			n += 1
	return n


func _check_all_gold() -> void:
	if not revealed and _gold_left() == 0:
		revealed = true
		event.emit("all_gold", {})


# ------------------------------------------------------------------ guards

func _trap(g: Dictionary) -> void:
	g["state"] = "trapped"
	g["timer"] = TRAPPED
	score += 75
	if g["gold"]:  # the gold pops out onto the cell above
		g["gold"] = false
		var up: Vector2i = g["cell"] + Vector2i(0, -1)
		if passable(up) and not gold.has(up):
			gold[up] = true
	event.emit("trapped", {"cell": g["cell"]})


func _bury(g: Dictionary) -> void:
	score += 75
	event.emit("crushed", {"cell": g["cell"]})
	g["gold"] = false
	g["state"] = "respawn"
	g["timer"] = RESPAWN


func _step_guard(g: Dictionary) -> void:
	match g["state"]:
		"respawn":
			g["timer"] -= TICK
			if g["timer"] <= 0.0:
				var spot := _respawn_spot()
				g["cell"] = spot
				g["to"] = spot
				g["t"] = 0.0
				g["state"] = "stand"
				event.emit("respawn", {"cell": spot})
			return
		"trapped":
			g["timer"] -= TICK
			if g["timer"] <= 0.0:
				var up: Vector2i = g["cell"] + Vector2i(0, -1)
				if passable(up) and guard_at(up, g).is_empty():
					_start(g, up, false)
					g["state"] = "climb_out"
					event.emit("escape", {"cell": g["cell"]})
				else:
					g["timer"] = 0.3
			return
		"climb_out":
			g["t"] += g["speed"] * 0.8 * TICK
			if g["t"] >= 1.0:
				g["cell"] = g["to"]
				g["t"] = 0.0
				g["state"] = "stand"
				# step off the hole's edge, towards the runner
				var side := 1 if runner["cell"].x > g["cell"].x else -1
				for d in [side, -side]:
					var n: Vector2i = g["cell"] + Vector2i(d, 0)
					if passable(n) and not holes.has(n + Vector2i(0, 1)) and guard_at(n, g).is_empty():
						_start(g, n, false)
						g["face"] = d
						break
			return
		"move", "fall":
			_advance(g)
			return
	var c: Vector2i = g["cell"]
	if not supported(c, g):
		if guard_at(c + Vector2i(0, 1), g).is_empty():
			_start(g, c + Vector2i(0, 1), true)
		return
	if g["gold"]:
		g["gold_hold"] -= TICK
		if g["gold_hold"] <= 0.0 and at(c) == T.EMPTY and not gold.has(c) and not passable(c + Vector2i(0, 1)):
			g["gold"] = false
			gold[c] = true
	if rng.randf() < 0.12:  # a guard sometimes hesitates at a crossing
		return
	var d := _hunt(c, g)
	if d != Vector2i.ZERO:
		var n := c + d
		if guard_at(n, g).is_empty():
			if d.x != 0:
				g["face"] = d.x
			_start(g, n, false)


## The first step along the shortest way to the runner (guards chase smartly but a little slower).
func _hunt(from: Vector2i, g: Dictionary) -> Vector2i:
	var goal: Vector2i = runner["to"] if runner["state"] == "move" else runner["cell"]
	var first := {from: Vector2i.ZERO}
	var queue: Array[Vector2i] = [from]
	var head := 0
	while head < queue.size() and head < 600:
		var c := queue[head]
		head += 1
		if c == goal:
			return first[c]
		for d in [Vector2i(-1, 0), Vector2i(1, 0), Vector2i(0, -1), Vector2i(0, 1)]:
			var n: Vector2i = c + d
			if first.has(n) or n.x < 0 or n.x >= level.w or n.y < 0 or n.y >= level.h:
				continue
			if not _guard_can(c, d):
				continue
			first[n] = d if c == from else first[c]
			queue.append(n)
	# no way there: at least close the gap sideways
	var dx := signi(goal.x - from.x)
	if dx != 0 and _guard_can(from, Vector2i(dx, 0)):
		return Vector2i(dx, 0)
	return Vector2i.ZERO


func _guard_can(c: Vector2i, d: Vector2i) -> bool:
	var n := c + d
	if not passable(n):
		return false
	if holes.has(n) and d.y == 0:
		return true  # guards walk into holes (and get stuck)
	# a cell with nothing to hold is only reached by falling: the path follows the fall straight down
	if not supported(c, {}) and d != Vector2i(0, 1):
		return false
	if d.y < 0:
		return at(c) == T.LADDER
	return true


func _respawn_spot() -> Vector2i:
	for tries in 60:
		var x := rng.randi_range(0, level.w - 1)
		var c := Vector2i(x, 0)
		if at(c) == T.EMPTY and guard_at(c).is_empty() and Vector2(c).distance_to(Vector2(runner["cell"])) > 4.0:
			return c
	return Vector2i(0, 0)


# ------------------------------------------------------------------ touch

func _collide() -> void:
	if phase != Phase.PLAY:
		return
	var rp := pos(runner)
	for g in guards:
		if g["state"] == "respawn" or g["state"] == "trapped":
			continue
		if pos(g).distance_to(rp) < 0.55:
			_die("caught")
			return


func _die(how: String) -> void:
	if phase != Phase.PLAY:
		return
	phase = Phase.DEAD
	runner["state"] = "dead"
	event.emit("died", {"cell": runner["cell"], "how": how})
