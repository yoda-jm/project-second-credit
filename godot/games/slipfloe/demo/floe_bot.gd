class_name FloeBot
extends RefCounted
## The Slipfloe autopilot (the demo). From every cell it can reach it looks at each block it could push: the lane the
## block would slide down, and the mites in that lane now. The best nearby shot wins; it walks there, turns and
## pushes. Stunned mites are stamped on; with no shot it breaks egg blocks or closes in; a mite too close is fled.

var _rng := RandomNumberGenerator.new()
var _path: Array[Vector2i] = []
var _shot := Vector2i.ZERO        ## the push to make at the end of the path
var _turned := false
var _wait := 0


func _init(seed_ := 1) -> void:
	_rng.seed = seed_


func drive(e: FloeEngine) -> void:
	e.want = Vector2i.ZERO
	if e.phase != FloeEngine.Phase.PLAY:
		_path.clear()
		return
	var o := e.otter
	if o["pos"] != Vector2(o["cell"]):
		return
	var here: Vector2i = o["cell"]
	if _wait > 0:
		_wait -= 1
		return
	# at the end of the path: turn, then push
	if _path.is_empty() and _shot != Vector2i.ZERO:
		if not _turned:
			e.want = _shot
			_turned = true
			return
		e.push_pressed = true
		_shot = Vector2i.ZERO
		_turned = false
		_wait = 6
		return
	if _danger(e, here) or _path.is_empty() or _path[0] != here:
		_plan(e)
	if _path.size() > 1 and _path[0] == here:
		var d := _path[1] - _path[0]
		_path.remove_at(0)
		if _mite_near(e, _path[0], 0.9):
			_path.clear()  # a mite stepped in: think again
			return
		e.want = d
		if _path.size() == 1:
			_path.clear()
	elif _path.size() <= 1:
		_path.clear()


func _danger(e: FloeEngine, c: Vector2i) -> bool:
	return _mite_near(e, c, 2.2)


func _mite_near(e: FloeEngine, c: Vector2i, r: float) -> bool:
	for m in e.mites:
		if m["stun"] <= 0.0 and not m["carried"] and (m["pos"] as Vector2).distance_to(Vector2(c)) < r:
			return true
	return false


func _plan(e: FloeEngine) -> void:
	var start: Vector2i = e.otter["cell"]
	var prev := {start: start}
	var dist := {start: 0}
	var q: Array[Vector2i] = [start]
	var head := 0
	var best := -INF
	var best_cell := start
	var best_dir := Vector2i.ZERO
	while head < q.size():
		var c := q[head]
		head += 1
		var dc: int = dist[c]
		# stunned mites here are worth stamping on
		for m in e.mites:
			if m["stun"] > 0.6 + dc * 0.2 and m["cell"] == c and not m["carried"]:
				var sc := 30.0 - dc
				if sc > best:
					best = sc
					best_cell = c
					best_dir = Vector2i.ZERO
		for d in FloeEngine.DIRS:
			var b: Vector2i = c + d
			var v := e.at(b)
			if v == FloeEngine.ICE or v == FloeEngine.GEM:
				var sc := _shot_score(e, b, d, dc)
				if sc > best:
					best = sc
					best_cell = c
					best_dir = d
			elif v == -1 and dc < 6:
				# a wall shake: mites along that wall
				var n := 0
				for m in e.mites:
					var mc: Vector2i = m["cell"]
					if m["stun"] <= 0.0 and ((d.x < 0 and mc.x == 0) or (d.x > 0 and mc.x == FloeEngine.W - 1) or (d.y < 0 and mc.y == 0) or (d.y > 0 and mc.y == FloeEngine.H - 1)):
						n += 1
				if n > 0:
					var sc := 12.0 * n - dc
					if sc > best:
						best = sc
						best_cell = c
						best_dir = d
		if dc >= 16:
			continue
		for d in FloeEngine.DIRS:
			var n: Vector2i = c + d
			if dist.has(n) or e.at(n) != FloeEngine.EMPTY:
				continue
			if _mite_near(e, n, 1.2) and dc < 3:
				continue
			dist[n] = dc + 1
			prev[n] = c
			q.append(n)
	_path.clear()
	if best <= 0.0:
		# nothing worth doing: flee from the nearest mite, or wander
		var far := -1.0
		var pick := start
		for c in dist:
			if dist[c] > 4:
				continue
			var near := 99.0
			for m in e.mites:
				near = minf(near, (m["pos"] as Vector2).distance_to(Vector2(c)))
			near += _rng.randf() * 0.5
			if near > far:
				far = near
				pick = c
		best_cell = pick
		best_dir = Vector2i.ZERO
	var chain: Array[Vector2i] = [best_cell]
	while chain[0] != start:
		chain.push_front(prev[chain[0]])
	_path = chain
	_shot = best_dir
	_turned = false
	if _path.size() == 1:
		_path.clear()


## How good pushing the block at b towards d would be, from dc steps away.
func _shot_score(e: FloeEngine, b: Vector2i, d: Vector2i, dc: int) -> float:
	var beyond := b + d
	if e.at(beyond) != FloeEngine.EMPTY:
		# it would shatter: good for an egg
		if e.at(b) == FloeEngine.ICE and e.eggs.has(b):
			return 8.0 - dc * 0.5
		return -1.0
	var sc := 0.0
	var c := beyond
	var steps := 0
	while e.at(c) == FloeEngine.EMPTY and steps < 14:
		for m in e.mites:
			if m["carried"] or m["hatch"] > 0.0:
				continue
			var mp: Vector2 = m["pos"]
			# where it is, and where it is heading
			if Vector2i(mp.round()) == c or (m["cell"] == c):
				# the block needs time to get there; a mite coming this way stays in the lane longer
				var travel := dc / FloeEngine.OTTER_SPEED + steps / FloeEngine.SLIDE_SPEED + 0.3
				sc += 20.0 - travel * 4.0
		c += d
		steps += 1
	return sc - dc * 0.8
