class_name InkBot
extends RefCounted
## The Inkstorm autopilot (the demo). On the land's edge it plans a box out into the open (out, across, back),
## checked cell by cell to stay clear of the storm and of its own line, and picks the one that claims most for the
## time it takes; with no good box it walks along the edge away from the sparks. While drawing it follows the plan,
## slow when the storm is far (double points); if the storm comes close it runs for the nearest land instead.

var _rng := RandomNumberGenerator.new()
var _path: Array[Vector2i] = []   ## planned cells, the first is the start on the edge
var _home: Array[Vector2i] = []
var _slow := false
var _walk_prev := Vector2i(-1, -1)
var _walk := 0
var _last := Vector2i(-1, -1)


func _init(seed_ := 1) -> void:
	_rng.seed = seed_


func drive(e: InkEngine) -> void:
	e.draw_fast = false
	e.draw_slow = false
	if e.pos != _last:
		_walk_prev = _last
		_last = e.pos
	if e.phase != InkEngine.Phase.PLAY:
		e.want = Vector2i.ZERO
		_path.clear()
		_home.clear()
		return
	if e.drawing():
		_draw(e)
		return
	_home.clear()
	if _path.is_empty() or _path[0] != e.pos:
		_path.clear()
		if _walk <= 0 or _spark_steps(e) < 16:
			_plan(e)
		if _path.is_empty() and _spark_steps(e) < 12:
			for d in InkEngine.DIRS:
				var n: Vector2i = e.pos + d
				if e.at(n) == InkEngine.FREE and not _storm_near(e, n, InkEngine.STORM_R + 6.0):
					_path = [e.pos, n]
					_slow = false
					break
		if _path.is_empty():
			_walk_along(e)
			return
	# leave the edge along the plan
	e.want = _path[1] - _path[0]
	e.draw_fast = not _slow
	e.draw_slow = _slow


func _draw(e: InkEngine) -> void:
	var danger := _storm_near(e, e.pos, InkEngine.STORM_R + 9.0)
	if _home.is_empty() and (danger or _path.find(e.pos) < 0):
		_home = _way_home(e)
	var route := _home if not _home.is_empty() else _path
	var i := route.find(e.pos)
	# a spark waiting where the line will land: land somewhere else
	if i >= 0 and route.size() > 1 and _spark_near(e, route[route.size() - 1]) < 4.0 + (route.size() - i) * 0.6:
		var other := _way_home(e)
		if not other.is_empty():
			_home = other
			route = _home
			i = 0
	if i < 0 or i + 1 >= route.size():
		_home = _way_home(e)
		route = _home
		i = 0
	if route.size() < 2:
		e.want = Vector2i.ZERO
		return
	e.want = route[i + 1] - route[i]
	var hurry := not _home.is_empty()
	e.draw_fast = hurry or not _slow
	e.draw_slow = not e.draw_fast


func _storm_near(e: InkEngine, c: Vector2i, r: float) -> bool:
	for s in e.storms:
		if (Vector2(c) + Vector2(0.5, 0.5)).distance_to(s["pos"]) < r:
			return true
	return false


func _storm_dist(e: InkEngine, c: Vector2i) -> float:
	var best := INF
	for s in e.storms:
		best = minf(best, (Vector2(c) + Vector2(0.5, 0.5)).distance_to(s["pos"]))
	return best


## Boxes out from here: depth k, across m (either side), back to land.
func _plan(e: InkEngine) -> void:
	var best := 0.0
	var start := e.pos
	var spark_close := _spark_steps(e) < 14
	for d in InkEngine.DIRS:
		if e.at(start + d) != InkEngine.FREE:
			continue
		for k in [3, 6, 10, 15, 22]:
			for side in [1, -1]:
				var t: Vector2i = Vector2i(-d.y, d.x) * side
				for m in [4, 8, 14, 22, 32]:
					var p := _box(e, start, d, t, k, m)
					if p.is_empty():
						continue
					var area := float(k * m)
					var cost := float(p.size()) / InkEngine.FAST + 0.5
					var near := 99.0
					for c in p:
						near = minf(near, _storm_dist(e, c))
					if near < InkEngine.STORM_R + 12.0 + p.size() * 0.25:
						continue
					if _spark_near(e, p[p.size() - 1]) < 8.0 + p.size() * 0.6:
						continue
					var score := area / cost * (1.0 + _rng.randf() * 0.2)
					if spark_close:
						score *= 2.0  # get off the edge
					if score > best:
						best = score
						_path = p
						_slow = near > 38.0 and not spark_close and p.size() < 50
	if _path.is_empty():
		_walk = 8


func _box(e: InkEngine, start: Vector2i, d: Vector2i, t: Vector2i, k: int, m: int) -> Array[Vector2i]:
	var p: Array[Vector2i] = [start]
	var mine := {start: true}
	var legs := [[d, k], [t, m], [-d, k + 40]]
	var c := start
	for leg in legs:
		var dir: Vector2i = leg[0]
		for i in leg[1]:
			var n := c + dir
			var v := e.at(n)
			if v == InkEngine.CLAIMED:
				if p.size() < 3:
					return []
				p.append(n)
				return p
			if v != InkEngine.FREE:
				return []
			for dd in InkEngine.DIRS:
				var nb: Vector2i = n + dd
				if nb != c and mine.has(nb):
					return []
			p.append(n)
			mine[n] = true
			c = n
	return []


## The shortest line from here through open cells to any land, not touching the trail, keeping off the storm.
func _way_home(e: InkEngine) -> Array[Vector2i]:
	var from := e.pos
	var prev := {from: from}
	var depth := {from: 0}
	var q: Array[Vector2i] = [from]
	var head := 0
	var goal := Vector2i(-1, -1)
	while head < q.size() and head < 6000:
		var c := q[head]
		head += 1
		for d in InkEngine.DIRS:
			var n: Vector2i = c + d
			if prev.has(n):
				continue
			var v := e.at(n)
			if v == InkEngine.CLAIMED and (c != from or e.trail.size() > 2) and _spark_near(e, n) > 4.0 + depth[c] * 0.6:
				prev[n] = c
				goal = n
				break
			if v != InkEngine.FREE:
				continue
			var ok := true
			for dd in InkEngine.DIRS:
				var nb: Vector2i = n + dd
				if nb != c and e.at(nb) == InkEngine.TRAIL:
					ok = false
			if not ok or _storm_near(e, n, InkEngine.STORM_R + 1.0):
				continue
			prev[n] = c
			depth[n] = depth[c] + 1
			q.append(n)
		if goal.x >= 0:
			break
	if goal.x < 0:
		return []
	var out: Array[Vector2i] = [goal]
	while out[0] != from:
		out.push_front(prev[out[0]])
	return out


func _spark_near(e: InkEngine, c: Vector2i) -> float:
	var best := 999.0
	for s in e.sparks:
		best = minf(best, float(absi(s["cell"].x - c.x) + absi(s["cell"].y - c.y)))
	return best


func _spark_steps(e: InkEngine) -> float:
	var best := 999.0
	for s in e.sparks:
		best = minf(best, float(absi(s["cell"].x - e.pos.x) + absi(s["cell"].y - e.pos.y)))
	return best


## Along the edge, away from the nearest spark.
func _walk_along(e: InkEngine) -> void:
	_walk -= 1
	var best := -INF
	var pick := Vector2i.ZERO
	var cornered := _spark_steps(e) < 10
	for d in InkEngine.DIRS:
		var n: Vector2i = e.pos + d
		if not e.is_edge(n) or (n == _walk_prev and not cornered):
			continue
		var sd := 999.0
		for s in e.sparks:
			sd = minf(sd, float(absi(s["cell"].x - n.x) + absi(s["cell"].y - n.y)))
		var score := minf(sd, 30.0) + _storm_dist(e, n) * 0.1 + _rng.randf()
		if score > best:
			best = score
			pick = d
	if pick == Vector2i.ZERO and e.is_edge(_walk_prev):
		pick = _walk_prev - e.pos
	e.want = pick
