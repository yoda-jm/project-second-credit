class_name FloeEngine
extends RefCounted
## Slipfloe rules (a block-pushing maze game in the Pengo tradition; our own tuning), fixed 60 Hz ticks, seeded.
## A W x H arena of ice blocks carved as a maze. The otter walks the open cells; facing a block, a push sends it
## sliding until it meets something, crushing every mite in its way; a block that cannot move shatters instead (with
## any egg inside). Pushing the outer wall shakes it: mites beside that wall are stunned, and walking over a stunned
## mite finishes it. Mites hatch from eggs in the ice, chase the otter and chew through blocks. Line up the three gem
## blocks for a big bonus. A stage is cleared when every mite and egg is gone.
## Events: "push", "slide" {id}, "stop" {id}, "shatter" {cell, egg}, "crush" {pos, n, points}, "hatch" {cell},
## "shake" {side}, "stun", "stomp" {pos}, "gems" {points}, "chew" {cell}, "die", "cleared" {bonus}, "game_over",
## "extra_life".

signal event(kind: String, data: Dictionary)

enum Phase { READY, PLAY, DYING, CLEARED, OVER }
const TICK := 1.0 / 60.0
const W := 13
const H := 15
const EMPTY := 0
const ICE := 1
const GEM := 2
const DIRS := [Vector2i(0, -1), Vector2i(0, 1), Vector2i(-1, 0), Vector2i(1, 0)]
const OTTER_SPEED := 5.0
const SLIDE_SPEED := 14.0
const CRUSH_POINTS := [400, 1600, 3200, 6400]

var stage := 0
var rng := RandomNumberGenerator.new()
var phase := Phase.READY
var phase_t := 2.0
var time := 0.0
var score := 0
var lives := 3
var grid := PackedByteArray()
var eggs := {}                ## cell -> true (an egg hidden in the ice there)
var otter := {"cell": Vector2i(6, 7), "pos": Vector2(6, 7), "facing": Vector2i(0, 1), "moving": false}
var want := Vector2i.ZERO     ## direction held
var push_pressed := false
var mites: Array[Dictionary] = []   ## {id, cell, pos, dir, stun, speed, chew, carried}
var slides: Array[Dictionary] = []  ## {id, kind, pos (Vector2), dir, egg, carried: [mite ids]}
var gem_done := false
var _next_id := 1
var _next_life := 30000
var _hatch_t := 0.0


func _init(stage_ := 0, seed_ := 1, lives_ := 3, score_ := 0) -> void:
	stage = stage_
	rng.seed = seed_
	lives = lives_
	score = score_
	_next_life = (score / 30000 + 1) * 30000
	_generate()


# ------------------------------------------------------------------ the arena

func at(c: Vector2i) -> int:
	if c.x < 0 or c.y < 0 or c.x >= W or c.y >= H:
		return -1
	return grid[c.y * W + c.x]


func _put(c: Vector2i, v: int) -> void:
	grid[c.y * W + c.x] = v


## A maze carved on the odd cells (every corridor cell starts open), then some extra openings and loops so the
## arena is not a pure tree, then the gems and eggs placed in the ice.
func _generate() -> void:
	grid.resize(W * H)
	grid.fill(ICE)
	var start := Vector2i(6, 7)
	var stack: Array[Vector2i] = [start]
	_put(start, EMPTY)
	var seen := {start: true}
	while not stack.is_empty():
		var c: Vector2i = stack.back()
		var opts: Array[Vector2i] = []
		for d in DIRS:
			var n: Vector2i = c + d * 2
			if n.x >= 0 and n.y >= 0 and n.x < W and n.y < H and not seen.has(n):
				opts.append(d)
		if opts.is_empty():
			stack.pop_back()
			continue
		var d: Vector2i = opts[rng.randi_range(0, opts.size() - 1)]
		_put(c + d, EMPTY)
		_put(c + d * 2, EMPTY)
		seen[c + d * 2] = true
		stack.append(c + d * 2)
	# knock out some walls for loops
	for i in 10:
		var c := Vector2i(rng.randi_range(1, W - 2), rng.randi_range(1, H - 2))
		if at(c) == ICE and ((at(c + Vector2i(1, 0)) == EMPTY and at(c - Vector2i(1, 0)) == EMPTY) or (at(c + Vector2i(0, 1)) == EMPTY and at(c - Vector2i(0, 1)) == EMPTY)):
			_put(c, EMPTY)
	otter["cell"] = start
	otter["pos"] = Vector2(start)
	# three gems, not on the edge, not touching each other
	var ice_cells: Array[Vector2i] = []
	for y in H:
		for x in W:
			if grid[y * W + x] == ICE:
				ice_cells.append(Vector2i(x, y))
	var gems: Array[Vector2i] = []
	while gems.size() < 3:
		var c: Vector2i = ice_cells[rng.randi_range(0, ice_cells.size() - 1)]
		if c.x < 1 or c.y < 1 or c.x > W - 2 or c.y > H - 2:
			continue
		var ok := true
		for g in gems:
			if absi(g.x - c.x) + absi(g.y - c.y) < 3:
				ok = false
		if ok:
			gems.append(c)
			_put(c, GEM)
	# eggs, far from the otter
	var n_eggs := 6 + mini(stage, 4)
	while eggs.size() < n_eggs:
		var c: Vector2i = ice_cells[rng.randi_range(0, ice_cells.size() - 1)]
		if at(c) == ICE and absi(c.x - start.x) + absi(c.y - start.y) > 5:
			eggs[c] = true
	# the first mites hatch at once
	for i in 3:
		_hatch()


func _hatch() -> void:
	if eggs.is_empty():
		return
	# the egg farthest from the otter
	var best := Vector2i(-1, -1)
	var bd := -1
	for c in eggs:
		var d := absi(c.x - otter["cell"].x) + absi(c.y - otter["cell"].y)
		if d > bd:
			bd = d
			best = c
	eggs.erase(best)
	_put(best, EMPTY)
	mites.append({"id": _next_id, "cell": best, "pos": Vector2(best), "dir": Vector2i.ZERO, "stun": 0.0,
		"speed": 3.0 + minf(stage, 6) * 0.25, "chew": 0.0, "carried": false, "hatch": 0.8})
	_next_id += 1
	event.emit("hatch", {"cell": best})


func mite_at(c: Vector2i) -> Dictionary:
	for m in mites:
		if m["cell"] == c and not m["carried"]:
			return m
	return {}


func _blocked_for_slide(c: Vector2i) -> bool:
	if at(c) != EMPTY:
		return true
	if otter["cell"] == c:
		return true
	for s in slides:
		if Vector2i(s["pos"].round()) == c:
			return true
	return false


# ------------------------------------------------------------------ the tick

func tick() -> void:
	time += TICK
	match phase:
		Phase.READY:
			phase_t -= TICK
			if phase_t <= 0.0:
				phase = Phase.PLAY
			return
		Phase.DYING:
			phase_t -= TICK
			if phase_t <= 0.0:
				if lives <= 0:
					phase = Phase.OVER
					event.emit("game_over", {})
				else:
					_respawn()
			return
		Phase.CLEARED, Phase.OVER:
			phase_t -= TICK
			return
	_move_otter()
	_move_slides()
	_move_mites()
	_touch()
	if mites.is_empty() and eggs.is_empty() and slides.is_empty() and phase == Phase.PLAY:
		var bonus := 0
		if time < 30.0: bonus = 5000
		elif time < 45.0: bonus = 2000
		elif time < 60.0: bonus = 1000
		elif time < 90.0: bonus = 500
		score += bonus
		phase = Phase.CLEARED
		phase_t = 3.5
		event.emit("cleared", {"bonus": bonus})


func _move_otter() -> void:
	var o := otter
	var p: Vector2 = o["pos"]
	var target := Vector2(o["cell"])
	if p != target:
		o["pos"] = p.move_toward(target, OTTER_SPEED * TICK)
		o["moving"] = true
		return
	o["moving"] = false
	if push_pressed:
		push_pressed = false
		_push()
		return
	if want == Vector2i.ZERO:
		return
	o["facing"] = want
	var n: Vector2i = o["cell"] + want
	if at(n) == EMPTY and not _slide_at(n):
		o["cell"] = n
		o["pos"] = p.move_toward(Vector2(n), OTTER_SPEED * TICK)
		o["moving"] = true
		# walking over a stunned mite finishes it
		var m := mite_at(n)
		if not m.is_empty() and m["stun"] > 0.0:
			mites.erase(m)
			score += 100
			event.emit("stomp", {"pos": Vector2(n)})
			_hatch_later()


func _slide_at(c: Vector2i) -> bool:
	for s in slides:
		if Vector2i(s["pos"].round()) == c:
			return true
	return false


func _push() -> void:
	var o := otter
	var d: Vector2i = o["facing"]
	var c: Vector2i = o["cell"] + d
	event.emit("push", {})
	var v := at(c)
	if v == -1:
		_shake(d)
		return
	if v == EMPTY:
		return
	if _blocked_for_slide(c + d):
		# it cannot move: ice shatters (gems do not)
		if v == ICE:
			_put(c, EMPTY)
			var egg := eggs.has(c)
			if egg:
				eggs.erase(c)
				score += 500
			else:
				score += 30
			event.emit("shatter", {"cell": c, "egg": egg})
		return
	_put(c, EMPTY)
	var s := {"id": _next_id, "kind": v, "pos": Vector2(c), "dir": d, "egg": eggs.has(c), "carried": []}
	if s["egg"]:
		eggs.erase(c)
	_next_id += 1
	slides.append(s)
	event.emit("slide", {"id": s["id"]})


func _shake(side: Vector2i) -> void:
	var n := 0
	for m in mites:
		var c: Vector2i = m["cell"]
		var by := (side.x < 0 and c.x == 0) or (side.x > 0 and c.x == W - 1) or (side.y < 0 and c.y == 0) or (side.y > 0 and c.y == H - 1)
		if by and not m["carried"]:
			m["stun"] = 4.0
			n += 1
	event.emit("shake", {"side": side, "stunned": n})
	if n > 0:
		event.emit("stun", {})


func _move_slides() -> void:
	for s in slides.duplicate():
		var d: Vector2i = s["dir"]
		var p: Vector2 = s["pos"]
		var step := SLIDE_SPEED * TICK
		var cur := Vector2i(p.round())
		# crossing the centre of a cell: go on only if the next one is free (mites do not count: they are swept)
		var ahead := (Vector2(cur) - p).dot(Vector2(d))
		if ahead >= 0.0 and ahead < step and _blocked_for_slide(cur + d):
			s["pos"] = Vector2(cur)
			_carry(s)
			_stop(s, cur)
			continue
		s["pos"] = p + Vector2(d) * step
		_carry(s)


## Mites just in front of a sliding block are swept along with it.
func _carry(s: Dictionary) -> void:
	var d := Vector2(s["dir"])
	var p: Vector2 = s["pos"]
	for m in mites:
		if m["carried"]:
			continue
		var rel: Vector2 = (m["pos"] as Vector2) - p
		if rel.dot(d) > 0.0 and rel.dot(d) < 1.0 and absf(rel.dot(Vector2(-d.y, d.x))) < 0.5:
			m["carried"] = true
			s["carried"].append(m["id"])
	for m in mites:
		if s["carried"].has(m["id"]):
			m["pos"] = p + d * 0.8
			m["cell"] = Vector2i((p + d).round())


func _stop(s: Dictionary, c: Vector2i) -> void:
	slides.erase(s)
	_put(c, s["kind"])
	if s["egg"]:
		eggs[c] = true
	event.emit("stop", {"id": s["id"], "cell": c})
	var n: int = s["carried"].size()
	if n > 0:
		var pts: int = CRUSH_POINTS[mini(n, 4) - 1]
		score += pts
		mites = mites.filter(func(m): return not s["carried"].has(m["id"]))
		event.emit("crush", {"pos": Vector2(c + s["dir"]), "n": n, "points": pts})
		for i in n:
			_hatch_later()
		_extra()
	if s["kind"] == GEM:
		_check_gems()


func _hatch_later() -> void:
	if not eggs.is_empty():
		_hatch()


func _check_gems() -> void:
	if gem_done:
		return
	var gems: Array[Vector2i] = []
	for y in H:
		for x in W:
			if grid[y * W + x] == GEM:
				gems.append(Vector2i(x, y))
	if gems.size() != 3:
		return
	gems.sort()
	var row := gems[0].y == gems[1].y and gems[1].y == gems[2].y and gems[1].x == gems[0].x + 1 and gems[2].x == gems[1].x + 1
	var col := gems[0].x == gems[1].x and gems[1].x == gems[2].x and gems[1].y == gems[0].y + 1 and gems[2].y == gems[1].y + 1
	if row or col:
		gem_done = true
		var edge := false
		for g in gems:
			if g.x == 0 or g.y == 0 or g.x == W - 1 or g.y == H - 1:
				edge = true
		var pts := 5000 if edge else 10000
		score += pts
		for m in mites:
			m["stun"] = 6.0
		event.emit("gems", {"points": pts})
		_extra()


func _extra() -> void:
	if score >= _next_life:
		_next_life += 30000
		lives += 1
		event.emit("extra_life", {})


# ------------------------------------------------------------------ mites

func _move_mites() -> void:
	var dist := _distances(otter["cell"])
	for m in mites:
		if m["carried"]:
			continue
		if m["hatch"] > 0.0:
			m["hatch"] -= TICK
			continue
		if m["stun"] > 0.0:
			m["stun"] -= TICK
			continue
		var p: Vector2 = m["pos"]
		var target := Vector2(m["cell"])
		if p != target:
			m["pos"] = p.move_toward(target, m["speed"] * TICK)
			continue
		if m["chew"] > 0.0:
			m["chew"] -= TICK
			if m["chew"] <= 0.0:
				var c: Vector2i = m["cell"] + m["dir"]
				if at(c) == ICE:
					_put(c, EMPTY)
					if eggs.has(c):
						eggs.erase(c)
					event.emit("shatter", {"cell": c, "egg": false, "chewed": true})
			continue
		# choose: towards the otter along open cells, sometimes wandering, sometimes chewing through ice
		var c: Vector2i = m["cell"]
		var best := Vector2i.ZERO
		var bd := 1 << 30
		var opts: Array[Vector2i] = []
		for d in DIRS:
			var n: Vector2i = c + d
			if at(n) == EMPTY and not _slide_at(n) and mite_at(n).is_empty():
				opts.append(d)
				var dd: int = dist.get(n, 999)
				if dd < bd:
					bd = dd
					best = d
		var chase := rng.randf() < 0.7 + minf(stage, 5) * 0.05
		if not chase and not opts.is_empty():
			best = opts[rng.randi_range(0, opts.size() - 1)]
		if best == Vector2i.ZERO or (bd >= 999 and rng.randf() < 0.3):
			# walled in, or the otter unreachable: chew towards it
			var to: Vector2i = otter["cell"] - c
			var d := Vector2i(signi(to.x), 0) if absi(to.x) > absi(to.y) else Vector2i(0, signi(to.y))
			if d != Vector2i.ZERO and at(c + d) == ICE:
				m["dir"] = d
				m["chew"] = 1.2
				event.emit("chew", {"cell": c + d})
				continue
			if opts.is_empty():
				continue
			best = opts[rng.randi_range(0, opts.size() - 1)]
		m["dir"] = best
		m["cell"] = c + best
		m["pos"] = p.move_toward(Vector2(c + best), m["speed"] * TICK)


func _distances(from: Vector2i) -> Dictionary:
	var out := {from: 0}
	var q: Array[Vector2i] = [from]
	var head := 0
	while head < q.size():
		var c := q[head]
		head += 1
		for d in DIRS:
			var n: Vector2i = c + d
			if not out.has(n) and at(n) == EMPTY:
				out[n] = out[c] + 1
				q.append(n)
	return out


func _touch() -> void:
	var op: Vector2 = otter["pos"]
	for m in mites:
		if m["carried"] or m["stun"] > 0.0 or m["hatch"] > 0.0:
			continue
		if (m["pos"] as Vector2).distance_to(op) < 0.6:
			_die()
			return


func _die() -> void:
	lives -= 1
	phase = Phase.DYING
	phase_t = 2.0
	slides.clear()
	event.emit("die", {"pos": otter["pos"]})


func _respawn() -> void:
	# back to a safe open cell far from the mites
	var dist := {}
	var best: Vector2i = otter["cell"]
	var bd := -1
	for y in H:
		for x in W:
			var c := Vector2i(x, y)
			if at(c) != EMPTY:
				continue
			var near := 999
			for m in mites:
				near = mini(near, absi(m["cell"].x - x) + absi(m["cell"].y - y))
			if near > bd:
				bd = near
				best = c
	otter["cell"] = best
	otter["pos"] = Vector2(best)
	phase = Phase.READY
	phase_t = 1.0
