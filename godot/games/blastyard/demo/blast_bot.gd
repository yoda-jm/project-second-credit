class_name BlastBot
extends RefCounted
## A Blastyard bomber played by the computer (the empty seats, and the demo). Every few ticks it maps the danger
## (every cell each bomb will burn, and when, chains included), then: if it stands in danger it runs to the nearest
## cell that stays safe; else it fetches a power-up, or walks to a spot next to crates or in line with a rival or an
## enemy and drops a bomb there, but only when a safe hideout is still reachable after the bang.

const T = ArenaMap.T
const DIRS: Array[Vector2i] = [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]

var slot := 0
var boldness := 1.0  ## lower: waits longer between bombs
var _path: Array = []
var _bomb_at := Vector2i(-1, -1)
var _think := 0
var _rng := RandomNumberGenerator.new()


func _init(slot_: int, seed_: int, boldness_ := 1.0) -> void:
	slot = slot_
	boldness = boldness_
	_rng.seed = seed_ * 7 + slot_


func drive(e: BlastEngine) -> void:
	var p := e.player(slot)
	if p.is_empty() or not p["alive"] or e.phase != BlastEngine.Phase.PLAY:
		return
	var here := e.cell_of(p["pos"])
	_think -= 1
	if _think <= 0:
		_think = 6
		_plan(e, p, here)
	var bomb := false
	if here == _bomb_at and _path.is_empty():
		bomb = true
		_bomb_at = Vector2i(-1, -1)
		_think = 0  # plan the escape at once
	while not _path.is_empty() and _path[0] == here:
		_path.pop_front()
	var dir := Vector2i.ZERO
	if not _path.is_empty():
		var n: Vector2i = _path[0]
		dir = n - here
		if absi(dir.x) + absi(dir.y) != 1:
			_path.clear()
			dir = Vector2i.ZERO
	else:
		# settle on the cell's centre so the next turn is clean
		var off: Vector2 = p["pos"] - (Vector2(here) + Vector2(0.5, 0.5))
		if absf(off.x) > 0.08:
			dir = Vector2i(-signi(int(signf(off.x))), 0)
		elif absf(off.y) > 0.08:
			dir = Vector2i(0, -signi(int(signf(off.y))))
	if p["skull"] > 0.0:
		dir = -dir  # the engine reverses it back
	e.set_input(slot, dir, bomb)


## Seconds before each cell burns (flames now: 0), for the bombs on the board plus an optional extra one.
static func danger(e: BlastEngine, extra := {}) -> Dictionary:
	var out := {}
	for c in e.flames:
		out[c] = 0.0
	var list: Array = e.bombs.duplicate()
	if not extra.is_empty():
		list.append(extra)
	var fuse := {}
	for b in list:
		fuse[b["cell"]] = b["fuse"]
	# chains: a bomb in another's blast goes off no later than that one
	for pass_ in 3:
		for b in list:
			for c in _blast(e, b["cell"], b["fire"]):
				if fuse.has(c) and fuse[c] > fuse[b["cell"]]:
					fuse[c] = fuse[b["cell"]]
	for b in list:
		var t: float = fuse[b["cell"]]
		for c in _blast(e, b["cell"], b["fire"]):
			out[c] = minf(out.get(c, INF), t)
	# enemies: where they are and the cells they could step into next are no place to be
	for en in e.enemies:
		if not en["alive"]:
			continue
		var c := e.cell_of(en["pos"])
		out[c] = 0.0
		for d in DIRS:
			var n: Vector2i = c + d
			if e.map.at(n) != T.PILLAR:
				out[n] = minf(out.get(n, INF), 0.0 if d == en["dir"] else 0.3)
	return out


static func _blast(e: BlastEngine, c: Vector2i, fire: int) -> Array[Vector2i]:
	var cells: Array[Vector2i] = [c]
	for d in DIRS:
		for k in range(1, fire + 1):
			var cc: Vector2i = c + d * k
			var t := e.map.at(cc)
			if t == T.PILLAR:
				break
			cells.append(cc)
			if t == T.CRATE or not e.bomb_at(cc).is_empty():
				break
	return cells


## Breadth-first from `from` over walkable cells whose danger comes later than we would pass through them.
func _reach(e: BlastEngine, from: Vector2i, speed: float, dz: Dictionary) -> Dictionary:
	var first := {from: from}
	var dist := {from: 0}
	var queue: Array[Vector2i] = [from]
	var head := 0
	while head < queue.size():
		var c := queue[head]
		head += 1
		for d in DIRS:
			var n: Vector2i = c + d
			if first.has(n) or e.map.at(n) != T.FLOOR or not e.bomb_at(n).is_empty():
				continue
			var arrive := float(dist[c] + 1) / speed
			if dz.has(n) and dz[n] <= arrive + 0.35 and dz[n] >= arrive - FLAME_WINDOW:
				continue  # we would be standing in it when it burns
			if dz.has(n) and dz[n] < 0.05:
				continue
			first[n] = c
			dist[n] = dist[c] + 1
			queue.append(n)
	return {"prev": first, "dist": dist}

const FLAME_WINDOW := 0.7


func _path_to(reach: Dictionary, to: Vector2i) -> Array[Vector2i]:
	var out: Array[Vector2i] = []
	var prev: Dictionary = reach["prev"]
	var c := to
	while prev.has(c) and prev[c] != c:
		out.push_front(c)
		c = prev[c]
	return out


func _plan(e: BlastEngine, p: Dictionary, here: Vector2i) -> void:
	var speed: float = p["speed"]
	var dz := danger(e)
	var reach := _reach(e, here, speed, dz)
	var dist: Dictionary = reach["dist"]
	# 1. in danger: the nearest cell no blast will touch
	if dz.has(here):
		var best := Vector2i(-1, -1)
		var bd := 999
		for c in dist:
			if not dz.has(c) and dist[c] < bd:
				bd = dist[c]
				best = c
		_path = _path_to(reach, best) if best.x >= 0 else []
		_bomb_at = Vector2i(-1, -1)
		return
	# 2. the open exit (solo), then a power-up (not the skull)
	if e.exit_open and dist.has(e.map.exit_cell):
		_path = _path_to(reach, e.map.exit_cell)
		_bomb_at = Vector2i(-1, -1)
		return
	var goal := Vector2i(-1, -1)
	var gd := 999
	for c in e.powerups:
		if e.powerups[c] != "skull" and dist.has(c) and dist[c] < gd and dist[c] < 9:
			gd = dist[c]
			goal = c
	if goal.x >= 0:
		_path = _path_to(reach, goal)
		_bomb_at = Vector2i(-1, -1)
		return
	# 3. somewhere worth a bomb, with a way out
	var out := e.bombs.filter(func(b): return b["owner"] == slot).size()
	if out < p["bombs"] and _rng.randf() < 0.35 + 0.5 * boldness:
		var spots: Array = []
		for c in dist:
			var v := _value(e, c, p["fire"])
			if v > 0:
				spots.append([dist[c] * 1.0 - v * 2.5 + _rng.randf() * 0.8, c])
		spots.sort_custom(func(a, b): return a[0] < b[0])
		for s in spots.slice(0, 6):
			var c: Vector2i = s[1]
			if _escape_after(e, c, p, dz):
				_path = _path_to(reach, c)
				_bomb_at = c
				return
	# 4. nothing to do: drift towards the middle, staying safe
	if _path.is_empty() and _rng.randf() < 0.3:
		var cells := dist.keys()
		var c: Vector2i = cells[_rng.randi_range(0, cells.size() - 1)]
		if not dz.has(c):
			_path = _path_to(reach, c)


## What a bomb here would hit: crates next to it, rivals or enemies in its lines.
func _value(e: BlastEngine, c: Vector2i, fire: int) -> float:
	var v := 0.0
	for cc in _blast(e, c, fire):
		if e.map.at(cc) == T.CRATE:
			v += 1.0
		for o in e.players:
			if o["alive"] and o["slot"] != slot and e.cell_of(o["pos"]) == cc:
				v += 2.5
		for en in e.enemies:
			if en["alive"] and e.cell_of(en["pos"]) == cc:
				v += 2.0
	return v


func _escape_after(e: BlastEngine, c: Vector2i, p: Dictionary, dz: Dictionary) -> bool:
	var extra := {"cell": c, "fire": p["fire"], "fuse": BlastEngine.FUSE}
	var dz2 := danger(e, extra)
	var reach := _reach(e, c, p["speed"], dz2)
	for cell in reach["dist"]:
		if not dz2.has(cell) and float(reach["dist"][cell]) / p["speed"] < BlastEngine.FUSE - 0.6:
			return true
	return false
