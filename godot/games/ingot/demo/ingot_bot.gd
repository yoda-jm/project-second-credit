class_name IngotBot
extends RefCounted
## The Ingot Run autopilot (the demo, and the check that a level can be won). At each cell it searches the shortest
## way to the nearest gold (or, once all is taken, to the exit at the top), over runs, climbs, bars, falls and
## dig-and-drop shortcuts, keeping clear of the guards; a guard coming along the same floor gets a hole dug in its way.

const T = IngotLevel.T
const SIDES := [Vector2i(-1, 0), Vector2i(1, 0), Vector2i(0, -1), Vector2i(0, 1)]

var _rng := RandomNumberGenerator.new()
var _plan := ""  ## "move" or "dig_left" / "dig_right"
var _dir := Vector2i.ZERO
var _reach := {}
var _reach_at := -99


func _init(seed_ := 1) -> void:
	_rng.seed = seed_


func drive(e: IngotEngine) -> void:
	e.dig_left = false
	e.dig_right = false
	var r := e.runner
	if e.phase != IngotEngine.Phase.PLAY:
		e.input = Vector2i.ZERO
		return
	if r["state"] != "stand":
		return  # the engine finishes the step; the held direction stays
	var c: Vector2i = r["cell"]
	if e.revealed and c.y == 0 and e.at(c) == T.LADDER:
		e.input = Vector2i(0, -1)
		return
	# a guard walking at us along this floor: blast a hole between
	for g in e.guards:
		if g["state"] in ["stand", "move"] and g["cell"].y == c.y:
			var dx: int = g["cell"].x - c.x
			if absi(dx) >= 1 and absi(dx) <= 5 and e._can_dig(c, signi(dx)):
				if signi(dx) < 0:
					e.dig_left = true
				else:
					e.dig_right = true
				e.input = Vector2i.ZERO
				return
	if e.ticks - _reach_at >= 4:
		_reach = _guard_times(e)
		_reach_at = e.ticks
	var reach := _reach
	var step := _search(e, c, reach, 0.45)
	if step == "":
		step = _search(e, c, reach, 0.0)  # no comfortable way: take the tight one
	if step == "":
		step = _search(e, c, {}, 0.0)  # every way is watched: go anyway, the guards may slip
		if step != "" and _guard_near(e, c, 2.5):
			step = _flee(e, c)
	match step:
		"dig_left": e.dig_left = true; e.input = Vector2i.ZERO
		"dig_right": e.dig_right = true; e.input = Vector2i.ZERO
		"left": e.input = Vector2i(-1, 0)
		"right": e.input = Vector2i(1, 0)
		"up": e.input = Vector2i(0, -1)
		"down": e.input = Vector2i(0, 1)
		_: e.input = Vector2i.ZERO


## For every cell, the soonest (seconds) any free guard could be there, moving as guards move.
func _guard_times(e: IngotEngine) -> Dictionary:
	var best := {}
	var open: Array = []  # [time, cell], kept sorted
	for g in e.guards:
		var start := 0.0
		match g["state"]:
			"respawn": continue
			"trapped": start = g["timer"] + 0.4
			"climb_out": start = 0.2
		for c in [g["cell"], g["to"]]:
			if not best.has(c) or best[c] > start:
				best[c] = start
				open.append([start, c])
	open.sort_custom(func(a, b): return a[0] < b[0])
	var step_t := 1.0 / IngotEngine.GUARD_SPEED
	var fall_t := 1.0 / IngotEngine.FALL_SPEED
	while not open.is_empty():
		var top: Array = open.pop_front()
		var t: float = top[0]
		var c: Vector2i = top[1]
		if t > best.get(c, INF) or t > 6.0:
			continue
		var held := e.supported(c, {})
		for d in SIDES:
			if not held and d != Vector2i(0, 1):
				continue
			if not e._guard_can(c, d):
				continue
			var n: Vector2i = c + d
			var nt := t + (fall_t if not held else step_t)
			if nt < best.get(n, INF):
				best[n] = nt
				var i := open.bsearch_custom([nt, n], func(a, b): return a[0] < b[0])
				open.insert(i, [nt, n])
	return best


func _guard_near(e: IngotEngine, c: Vector2i, r: float) -> bool:
	for g in e.guards:
		if g["state"] in ["stand", "move", "fall", "climb_out"] and Vector2(g["cell"]).distance_to(Vector2(c)) < r:
			return true
	return false


## Nothing to aim for: step away from the nearest guard.
func _flee(e: IngotEngine, c: Vector2i) -> String:
	var near := Vector2i(-99, -99)
	for g in e.guards:
		if g["state"] != "respawn" and Vector2(g["cell"]).distance_to(Vector2(c)) < Vector2(near).distance_to(Vector2(c)):
			near = g["cell"]
	var away := signi(c.x - near.x)
	if away != 0 and e.passable(c + Vector2i(away, 0)):
		return "left" if away < 0 else "right"
	if e.at(c) == T.LADDER and e.passable(c + Vector2i(0, -1)):
		return "up"
	return "down" if e.passable(c + Vector2i(0, 1)) else ""


## Breadth-first over the runner's moves; returns the first action towards the best goal.
func _search(e: IngotEngine, from: Vector2i, guard_t: Dictionary, margin: float) -> String:
	var first := {from: ""}
	var when := {from: 0.0}
	var queue: Array[Vector2i] = [from]
	var head := 0
	var dummy := {"runner": true}
	while head < queue.size() and head < 2000:
		var c := queue[head]
		head += 1
		var goal := (e.gold.has(c)) if not e.revealed else (c.y == 0 and e.at(c) == T.LADDER)
		if goal and c != from:
			return first[c]
		if goal and c == from and e.revealed:
			return "up"
		var held := e.supported(c, dummy)
		var moves := []  # [action, cell]
		if not held:
			moves.append(["down", c + Vector2i(0, 1)])
		else:
			for side in [-1, 1]:
				var n := c + Vector2i(side, 0)
				if e.passable(n):
					moves.append(["left" if side < 0 else "right", n])
			if e.at(c) == T.LADDER and e.passable(c + Vector2i(0, -1)):
				moves.append(["up", c + Vector2i(0, -1)])
			if e.passable(c + Vector2i(0, 1)):
				moves.append(["down", c + Vector2i(0, 1)])
			if true:  # dig a way down (the plan digs when it gets there)
				for side in [-1, 1]:
					if e._can_dig(c, side):
						moves.append(["dig_left" if side < 0 else "dig_right", c + Vector2i(side, 1)])
		for mv in moves:
			var n: Vector2i = mv[1]
			if first.has(n) or n.x < 0 or n.x >= e.level.w or n.y < 0 or n.y >= e.level.h:
				continue
			var dt := 1.0 / IngotEngine.FALL_SPEED if mv[0] == "down" and not held else 1.0 / IngotEngine.RUNNER_SPEED
			if str(mv[0]).begins_with("dig"):
				dt = IngotEngine.DIG_TIME + 2.0 / IngotEngine.RUNNER_SPEED
			var t: float = when[c] + dt
			if t + margin >= guard_t.get(n, INF):
				continue  # a guard could be there first
			first[n] = mv[0] if c == from else first[c]
			when[n] = t
			queue.append(n)
	# nowhere to go safely: step away from the nearest guard
	return ""
