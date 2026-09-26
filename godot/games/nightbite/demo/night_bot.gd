class_name NightBot
extends RefCounted
## The Nightbite autopilot (the demo): at each cell it looks for the nearest pellet over lanes the spirits cannot
## reach first; when a spirit is scared and close it gives chase; a power orb near a pursuing spirit is worth a detour.

var _rng := RandomNumberGenerator.new()


func _init(seed_ := 1) -> void:
	_rng.seed = seed_


func drive(e: NightEngine) -> void:
	if e.phase != NightEngine.Phase.PLAY:
		return
	var here := e.maze.wrap_cell(NightEngine.cell(e.hero["pos"]))
	var danger := _danger(e)
	var best := _search(e, here, danger, true)
	if best == Vector2i.ZERO:
		best = _search(e, here, danger, false)
	if best == Vector2i.ZERO:
		best = _escape(e, here)
	if best != Vector2i.ZERO:
		e.want = best


## Seconds before each cell could hold a (non-scared) spirit, by a breadth-first spread along the lanes.
func _danger(e: NightEngine) -> Dictionary:
	var out := {}
	var q: Array = []
	for s in e.spirits:
		if s["state"] != "out" or s["scared"]:
			continue
		var c := e.maze.wrap_cell(NightEngine.cell(s["pos"]))
		out[c] = 0.0
		q.append(c)
	var step := 1.0 / (7.0 + minf(e.stage, 6) * 0.4)
	var head := 0
	while head < q.size():
		var c: Vector2i = q[head]
		head += 1
		if out[c] > 2.0:
			continue
		for d in NightEngine.DIRS:
			var n := e.maze.wrap_cell(c + d)
			if e.open_for(n) and not out.has(n):
				out[n] = out[c] + step
				q.append(n)
	return out


func _search(e: NightEngine, from: Vector2i, danger: Dictionary, careful: bool) -> Vector2i:
	var first := {from: Vector2i.ZERO}
	var dist := {from: 0}
	var q: Array[Vector2i] = [from]
	var head := 0
	var hero_step := 1.0 / e.hero_speed()
	while head < q.size() and head < 800:
		var c := q[head]
		head += 1
		if c != from:
			var goal := e.pellets.has(c) or e.powers.has(c)
			for s in e.spirits:
				if s["scared"] and s["state"] == "out" and e.maze.wrap_cell(NightEngine.cell(s["pos"])) == c and dist[c] < 8:
					goal = true
			if goal:
				return first[c]
		for d in NightEngine.DIRS:
			var n := e.maze.wrap_cell(c + d)
			if first.has(n) or not e.open_for(n):
				continue
			var t := float(dist[c] + 1) * hero_step
			if careful and danger.has(n) and danger[n] < t + 0.45:
				continue
			first[n] = d if c == from else first[c]
			dist[n] = dist[c] + 1
			q.append(n)
	return Vector2i.ZERO


func _escape(e: NightEngine, from: Vector2i) -> Vector2i:
	var best := Vector2i.ZERO
	var far := -1.0
	for d in NightEngine.DIRS:
		var n := e.maze.wrap_cell(from + d)
		if not e.open_for(n):
			continue
		var near := INF
		for s in e.spirits:
			if s["state"] == "out" and not s["scared"]:
				near = minf(near, Vector2(n).distance_to(s["pos"]))
		if near > far:
			far = near
			best = d
	return best
