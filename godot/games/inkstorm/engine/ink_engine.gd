class_name InkEngine
extends RefCounted
## Inkstorm rules (a territory game in the Qix tradition; our own tuning), fixed 60 Hz ticks, seeded.
## The board is a grid of W x H cells: FREE (open parchment), CLAIMED (land) or TRAIL (the line being drawn). The
## outer ring starts claimed. The marker runs along the edges of the land (claimed cells touching free ones); holding
## a draw button it leaves the land and draws a trail across the open area; when the trail reaches land again it
## becomes land, and every open region without a storm in it is claimed too. Slow drawing scores double.
## The storm wanders the open area: if it touches the trail (or the marker while drawing), a life is lost. Sparks run
## along the edges and hunt the marker; a fuse burns along the trail when the marker stops while drawing.
## Claim TARGET of the open area to clear the stage.
## Events: "draw_start", "claim" {cells, percent, slow, region (Array of cells)}, "split", "die", "spark_spawn",
## "fuse", "cleared", "game_over", "extra_life".

signal event(kind: String, data: Dictionary)

enum Phase { READY, PLAY, DYING, CLEARED, OVER }
const TICK := 1.0 / 60.0
const W := 128
const H := 96
const FREE := 0
const CLAIMED := 1
const TRAIL := 2
const TARGET := 0.75
const READY_TIME := 1.6
const DIE_TIME := 1.8
const FAST := 22.0       ## cells per second
const SLOW := 11.0
const STORM_R := 6.0     ## the storm's reach, in cells
const DIRS := [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]

var stage := 0
var rng := RandomNumberGenerator.new()
var grid := PackedByteArray()
var claim_time := PackedFloat32Array()  ## when each cell was claimed (for the view's rise), -1 if never
var phase := Phase.READY
var phase_t := READY_TIME
var time := 0.0
var score := 0
var lives := 3
var claimed := 0.0        ## fraction of the open area claimed
var pos := Vector2i(W / 2, H - 1)
var want := Vector2i.ZERO ## direction held
var draw_fast := false
var draw_slow := false
var trail: Array[Vector2i] = []
var trail_slow := true    ## every step of this trail was slow
var storms: Array[Dictionary] = []   ## {pos: Vector2 (cells), vel: Vector2}
var sparks: Array[Dictionary] = []   ## {cell, prev, hand (1 or -1), acc, super}
var split := false        ## the storms have been fenced apart
var fuse := -1.0          ## index along the trail the fuse has burnt to, -1 when unlit
var _still := 0.0
var _acc := 0.0
var _interior := 0
var _next_spark := 0.0
var _dist := {}           ## edge cell -> steps to the marker (for the sparks), refreshed often
var _dist_t := 0.0
var _next_life := 50000


func _init(stage_ := 0, seed_ := 1, lives_ := 3, score_ := 0) -> void:
	stage = stage_
	rng.seed = seed_
	lives = lives_
	score = score_
	_next_life = (score / 50000 + 1) * 50000
	grid.resize(W * H)
	claim_time.resize(W * H)
	claim_time.fill(-1.0)
	for y in H:
		for x in W:
			if x == 0 or y == 0 or x == W - 1 or y == H - 1:
				grid[y * W + x] = CLAIMED
				claim_time[y * W + x] = -10.0
	_interior = (W - 2) * (H - 2)
	for i in (2 if stage >= 2 else 1):
		var a := rng.randf() * TAU
		storms.append({"pos": Vector2(W * (0.35 + 0.3 * i), H * 0.4), "vel": Vector2(cos(a), sin(a)) * _storm_speed(), "turn": 0.0})
	_reset_sparks()
	_next_spark = 25.0


func _storm_speed() -> float:
	return 14.0 + minf(stage, 6) * 1.5


func at(c: Vector2i) -> int:
	if c.x < 0 or c.y < 0 or c.x >= W or c.y >= H:
		return -1
	return grid[c.y * W + c.x]


func _put(c: Vector2i, v: int) -> void:
	grid[c.y * W + c.x] = v


## A claimed cell with an open (or trail) cell among its 8 neighbours: where the marker and the sparks run.
func is_edge(c: Vector2i) -> bool:
	if at(c) != CLAIMED:
		return false
	for dy in range(-1, 2):
		for dx in range(-1, 2):
			var v := at(c + Vector2i(dx, dy))
			if v == FREE or v == TRAIL:
				return true
	return false


func drawing() -> bool:
	return not trail.is_empty()


func _reset_sparks() -> void:
	sparks.clear()
	for h in [1, -1]:
		sparks.append({"cell": Vector2i(W / 2, 0), "prev": Vector2i(W / 2, 0), "hand": h, "acc": 0.0, "super": false,
			"dir": Vector2i(h, 0)})
	for s in sparks:
		s["cell"] = _nearest_edge(s["cell"])


# ------------------------------------------------------------------ the tick

func tick() -> void:
	time += TICK
	match phase:
		Phase.READY:
			phase_t -= TICK
			if phase_t <= 0.0:
				phase = Phase.PLAY
			_move_storms()
			return
		Phase.DYING:
			phase_t -= TICK
			_move_storms()
			if phase_t <= 0.0:
				if lives <= 0:
					phase = Phase.OVER
					event.emit("game_over", {})
				else:
					phase = Phase.READY
					phase_t = 0.8
			return
		Phase.CLEARED, Phase.OVER:
			phase_t -= TICK
			return
	_move_marker()
	if phase != Phase.PLAY:
		return
	_move_storms()
	_move_sparks()
	_burn_fuse()
	_next_spark -= TICK
	if _next_spark <= 0.0 and sparks.size() < 2 + mini(stage / 2 + 1, 2):
		_next_spark = maxf(12.0, 25.0 - stage * 2.0)
		var s := {"cell": _nearest_edge(Vector2i(W / 2, 0)), "prev": Vector2i(-1, -1), "hand": [1, -1][sparks.size() % 2],
			"acc": 0.0, "super": sparks.size() >= 3, "dir": Vector2i(1, 0)}
		sparks.append(s)
		event.emit("spark_spawn", {"cell": s["cell"]})
	_check_hits()


func _move_marker() -> void:
	var drawing_key := draw_fast or draw_slow
	var speed := FAST
	if drawing() or drawing_key:
		speed = SLOW if draw_slow and not draw_fast else FAST
	var moved := false
	_acc += speed * TICK
	while _acc >= 1.0:
		_acc -= 1.0
		if want == Vector2i.ZERO:
			_acc = 0.0
			break
		if _step(want, drawing_key):
			moved = true
			if drawing() and speed == FAST:
				trail_slow = false
		else:
			_acc = 0.0
			break
		if phase != Phase.PLAY:
			return
	if drawing():
		if moved:
			_still = 0.0
		else:
			_still += TICK


## One cell of movement; false if the way is shut.
func _step(d: Vector2i, drawing_key: bool) -> bool:
	var n := pos + d
	var v := at(n)
	if v < 0:
		return false
	if not drawing():
		if v == CLAIMED:
			if not is_edge(n):
				return false
			pos = n
			return true
		if v == FREE and drawing_key and _may_draw(n, pos):
			trail = [pos, n]
			trail_slow = true
			_put(n, TRAIL)
			pos = n
			fuse = -1.0
			event.emit("draw_start", {})
			return true
		return false
	# drawing
	if v == CLAIMED:
		trail.append(n)
		pos = n
		_close()
		return true
	if v == FREE and _may_draw(n, pos):
		trail.append(n)
		_put(n, TRAIL)
		pos = n
		return true
	return false


## The trail may not touch itself: the new cell's neighbours hold no trail but the cell it comes from.
func _may_draw(n: Vector2i, from: Vector2i) -> bool:
	for d in DIRS:
		var m: Vector2i = n + d
		if m != from and at(m) == TRAIL:
			return false
	return true


## The trail reached land: it and every storm-free open region become land.
func _close() -> void:
	var t0 := time
	var cells := 0
	for c in trail:
		if at(c) == TRAIL:
			_put(c, CLAIMED)
			claim_time[c.y * W + c.x] = t0
			cells += 1
	for st in storms:
		# a storm caught on the new land (it was crossed in the same instant) steps to the nearest open cell
		var sc := Vector2i(st["pos"].floor())
		if at(sc) != FREE:
			st["pos"] = Vector2(_nearest_free(sc)) + Vector2(0.5, 0.5)
	var seen := PackedByteArray()
	seen.resize(W * H)
	var regions: Array = []
	for y in range(1, H - 1):
		for x in range(1, W - 1):
			if grid[y * W + x] == FREE and seen[y * W + x] == 0:
				regions.append(_flood(Vector2i(x, y), seen))
	var storm_regions := {}
	var claimed_cells: Array[Vector2i] = []
	for ri in regions.size():
		var r: Dictionary = regions[ri]
		var has := false
		for s in storms:
			if r["set"].has(Vector2i(s["pos"].floor())):
				has = true
				storm_regions[ri] = true
		if not has:
			for c in r["cells"]:
				_put(c, CLAIMED)
				claim_time[c.y * W + c.x] = t0
				claimed_cells.append(c)
			cells += r["cells"].size()
	var mult := 2 if trail_slow else 1
	score += cells * mult
	trail.clear()
	fuse = -1.0
	_still = 0.0
	_count()
	if storms.size() > 1 and storm_regions.size() > 1 and not split:
		split = true  # the storms are apart for good: paid once
		score += 2000
		event.emit("split", {})
	event.emit("claim", {"cells": cells, "percent": claimed, "slow": trail_slow, "region": claimed_cells})
	if score >= _next_life:
		_next_life += 50000
		lives += 1
		event.emit("extra_life", {})
	# sparks and the marker stay on the edges
	pos = _nearest_edge(pos)
	for s in sparks:
		if not is_edge(s["cell"]):
			s["cell"] = _nearest_edge(s["cell"])
			s["prev"] = s["cell"]
	_dist_t = 0.0
	if claimed >= TARGET:
		score += int((claimed - TARGET) * 100.0) * 1000
		phase = Phase.CLEARED
		phase_t = 3.5
		event.emit("cleared", {"percent": claimed})


func _flood(start: Vector2i, seen: PackedByteArray) -> Dictionary:
	var cells: Array[Vector2i] = [start]
	var set := {start: true}
	seen[start.y * W + start.x] = 1
	var head := 0
	while head < cells.size():
		var c := cells[head]
		head += 1
		for d in DIRS:
			var n: Vector2i = c + d
			if grid[n.y * W + n.x] == FREE and seen[n.y * W + n.x] == 0:
				seen[n.y * W + n.x] = 1
				cells.append(n)
				set[n] = true
	return {"cells": cells, "set": set}


func _count() -> void:
	var n := 0
	for y in range(1, H - 1):
		for x in range(1, W - 1):
			if grid[y * W + x] == CLAIMED:
				n += 1
	claimed = float(n) / _interior


func _nearest_edge(from: Vector2i) -> Vector2i:
	if is_edge(from):
		return from
	var q: Array[Vector2i] = [from]
	var seen := {from: true}
	var head := 0
	while head < q.size():
		var c := q[head]
		head += 1
		for d in DIRS:
			var n: Vector2i = c + d
			if at(n) < 0 or seen.has(n):
				continue
			if is_edge(n):
				return n
			seen[n] = true
			q.append(n)
	return from


func _nearest_free(from: Vector2i) -> Vector2i:
	var q: Array[Vector2i] = [from]
	var seen := {from: true}
	var head := 0
	while head < q.size():
		var c := q[head]
		head += 1
		if at(c) == FREE:
			return c
		for d in DIRS:
			var n: Vector2i = c + d
			if at(n) >= 0 and not seen.has(n):
				seen[n] = true
				q.append(n)
	return from


# ------------------------------------------------------------------ the storm

func _move_storms() -> void:
	for s in storms:
		var v: Vector2 = s["vel"]
		# it wanders: the heading turns by a slowly changing amount, now and then a lurch
		s["turn"] = clampf(s["turn"] + rng.randf_range(-0.5, 0.5) * TICK * 8.0, -2.5, 2.5)
		v = v.rotated(s["turn"] * TICK)
		if rng.randf() < 0.01:
			v = v.rotated(rng.randf_range(-1.5, 1.5))
		v = v.normalized() * _storm_speed()
		var p: Vector2 = s["pos"]
		var np := p + v * TICK
		# bounce off land: probe ahead at the edge of its body
		for i in 8:
			var probe := np + v.normalized() * STORM_R * 0.6
			var pc := Vector2i(probe.floor())
			var nc := Vector2i(np.floor())
			if at(pc) == FREE or at(pc) == TRAIL:
				if at(nc) == FREE or at(nc) == TRAIL:
					break
			v = v.rotated(rng.randf_range(1.2, 2.6) * (1 if rng.randf() < 0.5 else -1))
			np = p + v * TICK
		if at(Vector2i(np.floor())) == FREE or at(Vector2i(np.floor())) == TRAIL:
			s["pos"] = np
		s["vel"] = v


# ------------------------------------------------------------------ sparks and fuse

func _move_sparks() -> void:
	_dist_t -= TICK
	if _dist_t <= 0.0:
		_dist_t = 0.25
		_dist = _edge_distances(trail[0] if drawing() else pos)
	var chase := time > 8.0
	var speed := 8.5 + minf(stage, 5) * 0.6
	for s in sparks:
		s["acc"] += (speed * (1.35 if s["super"] else 1.0)) * TICK
		while s["acc"] >= 1.0:
			s["acc"] -= 1.0
			var c: Vector2i = s["cell"]
			var opts: Array[Vector2i] = []
			for d in DIRS:
				var n: Vector2i = c + d
				if n != s["prev"] and is_edge(n):
					opts.append(n)
			if opts.is_empty():
				opts.append(s["prev"] if is_edge(s["prev"]) else c)
			var pick: Vector2i = opts[0]
			if chase and (s["super"] or rng.randf() < 0.6):
				var best := INF
				for o in opts:
					var dd: float = _dist.get(o, 9999)
					if dd < best:
						best = dd
						pick = o
			else:
				# patrol: keep going, turning by the spark's hand at a corner
				var dir: Vector2i = s["dir"]
				var order := [dir, Vector2i(-dir.y, dir.x) * s["hand"], Vector2i(dir.y, -dir.x) * s["hand"]]
				for o in order:
					if opts.has(c + o):
						pick = c + o
						break
			s["prev"] = c
			s["dir"] = pick - c
			s["cell"] = pick


func _edge_distances(from: Vector2i) -> Dictionary:
	var out := {from: 0}
	var q: Array[Vector2i] = [from]
	var head := 0
	while head < q.size():
		var c := q[head]
		head += 1
		for d in DIRS:
			var n: Vector2i = c + d
			if not out.has(n) and is_edge(n):
				out[n] = out[c] + 1
				q.append(n)
	return out


func _burn_fuse() -> void:
	if not drawing():
		fuse = -1.0
		return
	if _still > 0.6:
		if fuse < 0.0:
			fuse = 0.0
			event.emit("fuse", {})
		fuse += 14.0 * TICK
	elif fuse >= 0.0:
		pass  # the fuse waits while the marker moves


func _check_hits() -> void:
	for s in sparks:
		if s["cell"].distance_squared_to(pos) <= 1:
			_die("spark")
			return
	if drawing():
		if fuse >= trail.size() - 1:
			_die("fuse")
			return
		for st in storms:
			var p: Vector2 = st["pos"]
			var r2 := STORM_R * STORM_R
			if (Vector2(pos) + Vector2(0.5, 0.5)).distance_squared_to(p) < r2:
				_die("storm")
				return
			for c in trail:
				if (Vector2(c) + Vector2(0.5, 0.5)).distance_squared_to(p) < r2 * 0.7:
					_die("storm")
					return


func _die(how: String) -> void:
	lives -= 1
	event.emit("die", {"how": how, "cell": pos})
	if drawing():
		for c in trail:
			if at(c) == TRAIL:
				_put(c, FREE)
		pos = trail[0]
		trail.clear()
	fuse = -1.0
	_still = 0.0
	phase = Phase.DYING
	phase_t = DIE_TIME
	_reset_sparks()
	for s in sparks:
		# sparks restart far from the marker
		s["cell"] = _nearest_edge(Vector2i(W - 1 - pos.x, 0 if pos.y > H / 2 else H - 1))
		s["prev"] = s["cell"]
