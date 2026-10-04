class_name FlowBot
extends RefCounted
## The Brassflow autopilot (the demo). It plans a long winding route from the source over the free cells (a depth-first
## search that prefers the cells with fewest ways on, so the route hugs the walls and fills the board), which says the
## piece each route cell needs. Then, with each piece the dispenser gives it, it walks the cursor (a cell at a time,
## like a player) to the first route cell needing that piece (a cross fits any straight), or, if none does, to a spare
## cell off the route. Once the route is laid well past the length it presses fast flow.

const F = preload("res://games/brassflow/engine/flow_engine.gd")
const MOVE_EVERY := 5

var route: Array[Vector2i] = []
var need: Array[Array] = []       ## per route cell: the two sides it must open
var _t := 0
var _planned := false


func drive(e: FlowEngine) -> void:
	e.place_pressed = false
	e.fast_pressed = false
	if e.phase != F.Phase.PLAY:
		return
	if not _planned:
		_plan(e)
		_planned = true
	var goal := _goal(e)
	if goal == Vector2i(-1, -1):
		return
	_t -= 1
	if _t > 0:
		return
	_t = MOVE_EVERY
	if e.cursor != goal:
		var d := goal - e.cursor
		if d.x != 0:
			e.cursor.x += signi(d.x)
		else:
			e.cursor.y += signi(d.y)
		return
	if e.cool <= 0.0:
		e.place_pressed = true
	if _laid(e) >= e.length + 3 or _laid(e) >= route.size():
		e.fast_pressed = true


## Route cells laid with the right piece, from the start, unbroken.
func _laid(e: FlowEngine) -> int:
	var n := 0
	for i in route.size():
		var g: Dictionary = e.grid.get(route[i], {})
		if g.is_empty() or not _fits(g["piece"], need[i]):
			break
		n += 1
	return n


static func _fits(piece: String, sides: Array) -> bool:
	if piece == "x":
		return (sides[0] + 2) % 4 == sides[1]
	var o: Array = F.PIECES[piece]
	return o.has(sides[0]) and o.has(sides[1])


func _goal(e: FlowEngine) -> Vector2i:
	var piece: String = e.queue[0]
	for i in route.size():
		var c := route[i]
		var g: Dictionary = e.grid.get(c, {})
		if not g.is_empty() and _fits(g["piece"], need[i]):
			continue
		if not g.is_empty() and not (g["filled"] as Array).is_empty():
			continue
		if _fits(piece, need[i]):
			return c
	# no route cell wants it: a spare cell off the route, near the cursor
	var best := Vector2i(-1, -1)
	var bd := 1 << 20
	for y in F.ROWS:
		for x in F.COLS:
			var c := Vector2i(x, y)
			if route.has(c) or not e.can_place(c) or e.grid.has(c):
				continue
			var d: int = absi(c.x - e.cursor.x) + absi(c.y - e.cursor.y)
			if d < bd:
				bd = d
				best = c
	if best != Vector2i(-1, -1):
		return best
	# nowhere spare: the furthest unfilled route cell (it can be replaced later)
	for i in range(route.size() - 1, -1, -1):
		if e.can_place(route[i]):
			return route[i]
	return Vector2i(-1, -1)


func _plan(e: FlowEngine) -> void:
	var start: Vector2i = e.source + F.DIRS[e.source_dir]
	var best: Array[Vector2i] = []
	var path: Array[Vector2i] = [start]
	var seen := {start: true}
	var budget := [20000]
	_dfs(e, path, seen, best, budget, e.length + 8)
	route = best
	need.clear()
	for i in route.size():
		var c := route[i]
		var prev := e.source if i == 0 else route[i - 1]
		var into := F.DIRS.find(prev - c)
		var outd := F.DIRS.find(route[i + 1] - c) if i + 1 < route.size() else F.opposite(into)
		need.append([into, outd])
	# the last cell: whatever continues it if it can, else straight on (the flow ends there anyway)


func _dfs(e: FlowEngine, path: Array[Vector2i], seen: Dictionary, best: Array[Vector2i], budget: Array, want: int) -> bool:
	budget[0] -= 1
	if path.size() > best.size():
		best.assign(path)
	if path.size() >= want or budget[0] <= 0:
		return true
	var c := path.back() as Vector2i
	var nexts := []
	for d in F.DIRS:
		var n: Vector2i = c + d
		if F.inside(n) and not e.blocked.has(n) and n != e.source and not seen.has(n):
			nexts.append(n)
	nexts.sort_custom(func(a, b): return _onward(e, a, seen) < _onward(e, b, seen))
	for n in nexts:
		path.append(n)
		seen[n] = true
		if _dfs(e, path, seen, best, budget, want):
			return true
		path.pop_back()
		seen.erase(n)
	return false


static func _onward(e: FlowEngine, c: Vector2i, seen: Dictionary) -> int:
	var k := 0
	for d in F.DIRS:
		var n: Vector2i = c + d
		if F.inside(n) and not e.blocked.has(n) and n != e.source and not seen.has(n):
			k += 1
	return k
