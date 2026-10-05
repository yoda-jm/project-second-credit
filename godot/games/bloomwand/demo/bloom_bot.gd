class_name BloomBot
extends RefCounted
## A Bloomwand autopilot for one fairy (the demo, and a CPU partner). It plans on a graph of the level's places to
## stand (walking, dropping off edges, ladders up and down, a magic ladder up to the floor above) and goes for the
## nearest creature, or a flower close by when no creature is near. A creature on its floor within the wand's reach
## and in the clear is turned to and caught, then slammed until it bursts; one that comes too close is faced and zapped.

const B = preload("res://games/bloomwand/engine/bloom_engine.gd")

var me := 0
var _cool := 0
var _path: Array[Vector2i] = []
var _replan := 0
var _skip := {}                 ## goals out of reach for now -> ticks left


func _init(who := 0) -> void:
	me = who


func drive(e: BloomEngine) -> void:
	var f := e.fairies[me]
	f["move"] = 0
	f["climb_in"] = 0
	f["cast_pressed"] = false
	f["ladder_pressed"] = false
	if e.phase != B.Phase.PLAY or f["dead"]:
		f["cast_held"] = false
		return
	if f["holding"] >= 0:
		f["cast_held"] = true
		return
	f["cast_held"] = false
	_cool -= 1
	var p: Vector2 = f["pos"]
	# a creature on this floor within reach: face it and cast
	var near := _in_reach(e, p)
	if not near.is_empty():
		var dir := 1 if near["pos"].x > p.x else -1
		if f["face"] != dir:
			if f["climbing"]:
				f["face"] = dir   # on a ladder she just turns
			else:
				f["move"] = dir
		elif _cool <= 0:
			f["cast_pressed"] = true
			f["cast_held"] = true
			_cool = 12
		return
	# otherwise go for a target
	var goal := _goal(e, p)
	if goal == Vector2i(-99, -99):
		return
	_replan -= 1
	var here := _cell(e, p, f["climbing"])
	if _replan <= 0 or _path.is_empty():
		_replan = 15
		_path = _route(e, here, goal)
		if _path.is_empty() and goal != here:
			_skip[goal] = 300   # can't get there from here: try something else for a while
	while not _path.is_empty() and _path[0] == here:
		_path.pop_front()
	if _path.is_empty():
		return
	var nxt: Vector2i = _path[0]
	if nxt.y > here.y:
		if e.ladder_at(here.x + 0.5, here.y + 0.5) or f["climbing"]:
			_center_then(f, p, here, 1)
		elif absf(p.x - (here.x + 0.5)) > 0.12:
			f["move"] = 1 if here.x + 0.5 > p.x else -1
		else:
			f["ladder_pressed"] = true
	elif nxt.y < here.y and nxt.x == here.x and e.ladder_at(here.x + 0.5, here.y - 0.5):
		_center_then(f, p, here, -1)
	else:
		f["move"] = signi(nxt.x - here.x) if nxt.x != here.x else (1 if nxt.x + 0.5 > p.x else -1)


func _center_then(f: Dictionary, p: Vector2, here: Vector2i, dir: int) -> void:
	if absf(p.x - (here.x + 0.5)) > 0.2 and not f["climbing"]:
		f["move"] = 1 if here.x + 0.5 > p.x else -1
	else:
		f["climb_in"] = dir


## Where she is on the graph: on a ladder, the rung below her feet (she hasn't arrived until she's off it).
## Standing at a gap's edge, she is on the column whose floor holds her.
func _cell(e: BloomEngine, p: Vector2, climbing := false) -> Vector2i:
	if climbing:
		return Vector2i(floori(p.x), floori(p.y + 0.05))
	var y := roundi(p.y)
	for dx in [0.0, -0.3, 0.3]:
		var x: float = p.x + dx
		if e.solid_at(x, y - 0.5) or e.tile(x, y - 0.5) == "H":
			return Vector2i(floori(x), y)
	return Vector2i(floori(p.x), y)


func _in_reach(e: BloomEngine, p: Vector2) -> Dictionary:
	var best := {}
	var bd := INF
	for c in e.foes:
		if c["dead"] or c["held_by"] >= 0:
			continue
		var d: Vector2 = c["pos"] - p
		if absf(d.y) < 0.6 and absf(d.x) < B.REACH and absf(d.x) < bd:
			var clear := true
			var k := 0.5
			while k < absf(d.x):
				if e.solid_at(p.x + signf(d.x) * k, p.y + 0.5):
					clear = false
				k += 0.5
			if clear:
				bd = absf(d.x)
				best = c
	return best


func _goal(e: BloomEngine, p: Vector2) -> Vector2i:
	for k in _skip.keys():
		_skip[k] -= 1
		if _skip[k] <= 0:
			_skip.erase(k)
	var best := Vector2i(-99, -99)
	var bd := INF
	for c in e.foes:
		if c["dead"] or c["held_by"] >= 0:
			continue
		var d := (c["pos"] as Vector2).distance_to(p)
		var g := Vector2i(floori(c["pos"].x), roundi(c["pos"].y))
		if d < bd and not _skip.has(g):
			bd = d
			best = g
	for fl in e.flowers:
		var d := fl.distance_to(p) * 1.8
		var g := Vector2i(floori(fl.x), roundi(fl.y - 0.3))
		if d < bd and d < 7.0 and not _skip.has(g):
			bd = d
			best = g
	return best


## A route over the places to stand: walk a tile, drop off an edge, a ladder a tile up or down, a magic ladder up to
## the floor above (dearer).
func _route(e: BloomEngine, from: Vector2i, to: Vector2i) -> Array[Vector2i]:
	var prev := {from: from}
	var cost := {from: 0.0}
	var open: Array = [[0.0, from]]
	var best_end := from
	var best_d := INF
	while not open.is_empty():
		open.sort_custom(func(a, b): return a[0] < b[0])
		var cur: Array = open.pop_front()
		var c: Vector2i = cur[1]
		var dist := Vector2(c).distance_to(Vector2(to))
		if dist < best_d:
			best_d = dist
			best_end = c
		if c == to:
			break
		for step in _steps(e, c):
			var n: Vector2i = step[0]
			var nc: float = cost[c] + step[1]
			if nc < cost.get(n, INF):
				cost[n] = nc
				prev[n] = c
				open.append([nc, n])
	var path: Array[Vector2i] = []
	var c := best_end
	while c != from:
		path.push_front(c)
		c = prev[c]
	return path


func _steps(e: BloomEngine, c: Vector2i) -> Array:
	var out := []
	var x := c.x + 0.5
	var y := float(c.y)
	var ladder_here := e.ladder_at(x, y + 0.5) or e.ladder_at(x, y - 0.5)
	var stands := e.solid_at(x, y - 0.5) or (e.tile(x, y - 0.5) == "H")
	if stands or ladder_here:
		for dx in [-1, 1]:
			var nx: float = x + dx
			if nx < 0.0 or nx > 20.0 or e.solid_at(nx, y + 0.5):
				continue
			var ny := y
			while ny > 0.0 and not e.solid_at(nx, ny - 0.5) and e.tile(nx, ny - 0.5) != "H":
				ny -= 1.0
			out.append([Vector2i(c.x + dx, int(ny)), 1.0 + (y - ny) * 0.3])
	if e.ladder_at(x, y + 0.5):
		out.append([Vector2i(c.x, c.y + 1), 1.0])
	if e.ladder_at(x, y - 0.5) or e.tile(x, y - 0.5) == "H":
		out.append([Vector2i(c.x, c.y - 1), 1.0])
	if stands:
		for up in range(2, 8):
			var ty := y + up
			if ty >= 15.0:
				break
			if e.solid_at(x, ty - 0.5) and not e.solid_at(x, ty + 0.5):
				out.append([Vector2i(c.x, int(ty)), 2.5 + up * 0.5])
				break
	return out
