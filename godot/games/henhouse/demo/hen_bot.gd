class_name HenBot
extends RefCounted
## The Henhouse Heist autopilot (the demo). It sees the level as places to stand (a column and a row) joined by
## walks, ladder climbs, drops off edges and jumps over two-cell gaps, and goes by the shortest way to the nearest
## egg (grain when a hen is near it or the clock is low). A hen close ahead on the way makes it wait or back off; the
## goose makes it keep moving.

var _path: Array = []     ## [Vector2i node, move to it: "walk", "climb", "drop", "jump"]
var _replan := 0.0
var _rng := RandomNumberGenerator.new()
var _hold := 0.0


func _init(seed_ := 1) -> void:
	_rng.seed = seed_


func drive(e: HenEngine) -> void:
	e.move_x = 0.0
	e.up = false
	e.down = false
	if e.phase != HenEngine.Phase.PLAY:
		_path.clear()
		return
	var h: Dictionary = e.hero
	var st: String = h["state"]
	if st == "jump" or st == "fall":
		return
	var p: Vector2 = h["pos"]
	var here := Vector2i(int(floor(p.x)), int(round(p.y)))
	_replan -= HenEngine.TICK
	if _hold > 0.0:
		_hold -= HenEngine.TICK
		return
	if _path.is_empty() or _replan <= 0.0:
		_plan(e, here)
		_replan = 0.5
	if _path.is_empty():
		return
	var node: Vector2i = _path[0][0]
	var move: String = _path[0][1]
	# on a ladder between rows, and the next move is not a climb: finish the climb to the row first
	if st == "climb" and move != "climb" and absf(p.y - round(p.y)) > 0.08:
		e.up = round(p.y) < p.y
		e.down = round(p.y) > p.y
		return
	# a hen near the next place: wait for it to pass
	if _hen_near(e, Vector2(node.x + 0.5, node.y), 1.6) and not _hen_near(e, p, 1.2):
		_hold = 0.3
		return
	var target := Vector2(node.x + 0.5, node.y)
	match move:
		"walk":
			var dx := target.x - p.x
			if absf(dx) < 0.12 and absf(p.y - target.y) < 0.2:
				_path.pop_front()
			else:
				e.move_x = signf(dx)
		"climb":
			var dx := target.x - p.x
			if st != "climb" and absf(dx) > 0.15:
				e.move_x = signf(dx)
			elif absf(p.y - target.y) < 0.08 or (st == "walk" and absf(p.y - target.y) < 0.2 and absf(dx) < 0.15 and _path.size() > 1 and _path[1][1] != "climb"):
				_path.pop_front()
			else:
				e.up = target.y < p.y
				e.down = target.y > p.y
		"drop":
			var dx := target.x - p.x
			e.move_x = signf(dx) if absf(dx) > 0.1 else 0.0
			if absf(dx) < 0.3 and absf(p.y - target.y) < 0.1:
				_path.pop_front()
		"jump":
			var dir := signf(target.x - p.x)
			if absf(target.x - p.x) < 0.2:
				_path.pop_front()
			elif st == "walk":
				# line up on the edge of the start cell, then jump
				var start_x := target.x - dir * 3.0
				if absf(p.x - start_x) > 0.1:
					e.move_x = signf(start_x - p.x)
				else:
					e.move_x = dir
					e.jump_pressed = true


func _hen_near(e: HenEngine, p: Vector2, r: float) -> bool:
	for hn in e.hens:
		if (hn["pos"] as Vector2).distance_to(p) < r:
			return true
	return false


func _neighbours(e: HenEngine, c: Vector2i) -> Array:
	var out := []
	var x := c.x + 0.5
	var y := float(c.y)
	var grounded := e.standable(x, y)
	for dx in ([-1, 1] if grounded else []):  # halfway down a ladder there is nothing to step onto
		if e.standable(x + dx, y):
			out.append([Vector2i(c.x + dx, c.y), "walk"])
		elif c.x + dx >= 0 and c.x + dx < HenEngine.W:
			# a drop: straight down to the first place to stand
			for r in range(c.y + 1, HenEngine.H):
				if e.standable(x + dx, float(r)):
					out.append([Vector2i(c.x + dx, r), "drop"])
					break
			# a jump over a two-cell gap on the same row
			if c.x + dx * 3 >= 0 and c.x + dx * 3 < HenEngine.W and e.standable(x + dx * 3, y) and not e.standable(x + dx * 2, y):
				out.append([Vector2i(c.x + dx * 3, c.y), "jump"])
	if e.ladder(c.x, c.y - 1):
		out.append([Vector2i(c.x, c.y - 1), "climb"])
	if e.ladder(c.x, c.y):
		out.append([Vector2i(c.x, c.y + 1), "climb"])
	return out


func _plan(e: HenEngine, from: Vector2i) -> void:
	var goals := {}
	for c in e.eggs:
		goals[Vector2i(c.x, c.y + 1)] = true
	if e.clock < 25.0 or e.eggs.size() <= 2:
		for c in e.grain:
			goals[Vector2i(c.x, c.y + 1)] = true
	var prev := {from: null}
	var q: Array[Vector2i] = [from]
	var head := 0
	var goal := Vector2i(-1, -1)
	while head < q.size():
		var c := q[head]
		head += 1
		if goals.has(c) and c != from:
			goal = c
			break
		for nb in _neighbours(e, c):
			var n: Vector2i = nb[0]
			if prev.has(n):
				continue
			prev[n] = [c, nb[1]]
			q.append(n)
	_path.clear()
	if goal.x < 0:
		return
	var c := goal
	while prev[c] != null:
		_path.push_front([c, prev[c][1]])
		c = prev[c][0]
