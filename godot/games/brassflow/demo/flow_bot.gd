class_name FlowBot
extends RefCounted
## The Brassflow autopilot (the demo). It plans the way from the boiler to the engine (a breadth-first search over the
## free cells), which says the piece each cell of it needs. With each piece the dispenser gives it, it walks the cursor
## (a cell at a time, like a player) to the first cell of the way that piece can fill once turned (a cross fits any
## straight), turns it to fit and lays it; a piece nothing wants goes on a spare cell off the way. Once the whole way
## is laid it presses fast flow.

const F = preload("res://games/brassflow/engine/flow_engine.gd")
const MOVE_EVERY := 5

var route: Array[Vector2i] = []
var need: Array[Array] = []       ## per route cell: the two sides it must open
var _t := 0
var _planned := false


func drive(e: FlowEngine) -> void:
	e.place_pressed = false
	e.fast_pressed = false
	e.rotate_pressed = false
	if e.phase != F.Phase.PLAY:
		return
	if not _planned:
		_plan(e)
		_planned = true
	if not route.is_empty() and _laid(e) >= route.size():
		e.fast_pressed = true
		return
	var goal := _goal(e)
	if goal[0] == Vector2i(-1, -1):
		return
	_t -= 1
	if _t > 0:
		return
	_t = MOVE_EVERY
	var at: Vector2i = goal[0]
	if e.cursor != at:
		var d := at - e.cursor
		if d.x != 0:
			e.cursor.x += signi(d.x)
		else:
			e.cursor.y += signi(d.y)
		return
	var want: Array = goal[1]
	if not want.is_empty() and not _fits(e.queue[0], want):
		e.rotate_pressed = true
		return
	if e.cool <= 0.0:
		e.place_pressed = true


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


## Whether some turn of the piece fits.
static func _fits_turned(piece: String, sides: Array) -> bool:
	var p := piece
	for k in 4:
		if _fits(p, sides):
			return true
		p = F.TURN[p]
	return false


## [the cell to go to, the sides it must open (empty for a spare cell)].
func _goal(e: FlowEngine) -> Array:
	var piece: String = e.queue[0]
	for i in route.size():
		var c := route[i]
		var g: Dictionary = e.grid.get(c, {})
		if not g.is_empty() and _fits(g["piece"], need[i]):
			continue
		if not g.is_empty() and not (g["filled"] as Array).is_empty():
			continue
		if _fits_turned(piece, need[i]):
			return [c, need[i]]
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
	return [best, []]


func _plan(e: FlowEngine) -> void:
	route.clear()
	need.clear()
	var start: Vector2i = e.source + F.DIRS[e.source_dir]
	var prev := {start: start}
	var q: Array[Vector2i] = [start]
	while not q.is_empty():
		var c: Vector2i = q.pop_front()
		if c == e.feed():
			break
		for d in F.DIRS:
			var n: Vector2i = c + d
			if e.open_cell(n) and not prev.has(n):
				prev[n] = c
				q.append(n)
	if not prev.has(e.feed()):
		return
	var c := e.feed()
	while true:
		route.push_front(c)
		if c == start:
			break
		c = prev[c]
	for i in route.size():
		var cell := route[i]
		var back := e.source if i == 0 else route[i - 1]
		var into := F.DIRS.find(back - cell)
		var onto := e.exit_cell if i == route.size() - 1 else route[i + 1]
		need.append([into, F.DIRS.find(onto - cell)])
