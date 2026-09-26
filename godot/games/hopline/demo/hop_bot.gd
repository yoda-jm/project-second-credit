class_name HopBot
extends RefCounted
## The Hopline autopilot (the demo). Lanes move as pure functions of time, so it searches forward in time: every
## step (one hop, or a wait of the same length) it keeps the most advanced safe positions (a beam), until one lands
## in a free bay. Then it plays the plan tick for tick, and plans again if anything differs.

const STEP := 10            ## ticks per step: a hop lands after 9 ticks and the next can start on the 10th
const BEAM := 70
const DEPTH := 160

var _plan: Array[String] = []   ## one action per step: "", "up", "down", "left", "right"
var _start := 0.0
var _expect: Array[Vector2] = []  ## (x, row) expected at the start of each step
var _rng := RandomNumberGenerator.new()


func _init(seed_ := 1) -> void:
	_rng.seed = seed_


func drive(e: HopEngine) -> void:
	if e.phase != HopEngine.Phase.PLAY or e.hop_left > 0:
		return
	var k := int(round((e.time - _start) / (STEP * HopEngine.TICK)))
	var on_step := absf(e.time - _start - k * STEP * HopEngine.TICK) < HopEngine.TICK * 0.5
	if _plan.is_empty() or k >= _plan.size() or (on_step and _off(e, k)):
		_search(e)
		k = 0
		on_step = true
	# a crocodile surfacing in the bay ahead: think again
	if on_step and k < _plan.size() and _plan[k] == "up" and e.row == 1 and e.bay_at(e.x) == e.croc_bay:
		_search(e)
		k = 0
	if on_step and k < _plan.size() and _plan[k] != "":
		e.want = _plan[k]


func _off(e: HopEngine, k: int) -> bool:
	if k >= _expect.size():
		return true
	return e.row != int(_expect[k].y) or absf(e.x - _expect[k].x) > 0.05


func _search(e: HopEngine) -> void:
	var dt := STEP * HopEngine.TICK
	var t0 := e.time + HopEngine.TICK  # the engine moves its clock on before it looks
	_start = t0  # the first step is taken on the next tick, when the clock reads t0
	# a node: [x, row, parent index, action]
	var nodes: Array = [[e.x, e.row, -1, ""]]
	var layer: Array[int] = [0]
	var goal := -1
	for step in DEPTH:
		var t := t0 + step * dt
		var next: Array[int] = []
		var seen := {}
		for ni in layer:
			var n: Array = nodes[ni]
			var fx: float = n[0]
			var r: int = n[1]
			for act in ["up", "", "left", "right", "down"]:
				var nx := fx
				var nr := r
				if act == "":
					# waiting: ride along, and stay safe all the way
					var ok := true
					for s in [0.33, 0.66, 1.0]:
						if not e.safe_at(r, fx + e.drift(r) * dt * s, t + dt * s):
							ok = false
							break
					if not ok:
						continue
					nx = fx + e.drift(r) * dt
				else:
					var d: Vector2i = HopEngine.DIRS[act]
					nr = r + d.y
					nx = fx + d.x + e.drift(r) * HopEngine.TICK
					if nr > HopEngine.START_ROW or nx < 0.5 or nx > HopEngine.W - 0.5:
						continue
					if not e.lanes[nr]["river"] and nr != 0:
						nx = clampf(roundf(nx), 1.0, HopEngine.W - 1.0)
					var tl := t + (HopEngine.HOP_TIME + HopEngine.TICK)
					if nr == 0:
						var b := e.bay_at(nx)
						if b >= 0 and not e.filled[b] and b != e.croc_bay:
							nodes.append([nx, nr, ni, act])
							goal = nodes.size() - 1
							break
						continue
					if not e.safe_at(nr, nx, tl):
						continue
					# and it must still be safe for the rest of the step
					var rest := t + dt
					if not e.safe_at(nr, nx + e.drift(nr) * (rest - tl), rest):
						continue
					nx += e.drift(nr) * (t + dt - tl)
				var key := Vector3i(nr, int(round(nx * 4.0)), 0)
				if seen.has(key):
					continue
				seen[key] = true
				nodes.append([nx, nr, ni, act])
				next.append(nodes.size() - 1)
			if goal >= 0:
				break
		if goal >= 0:
			break
		if next.is_empty():
			break
		# keep the most advanced, with a little variety
		next.sort_custom(func(a, b): return nodes[a][1] * 10.0 + _jitter(a) < nodes[b][1] * 10.0 + _jitter(b))
		layer = next.slice(0, BEAM)
	_plan.clear()
	_expect.clear()
	if goal < 0:
		# nothing reaches home: the safest single step
		_plan = [""]
		_expect = [Vector2(e.x, e.row)]
		return
	var chain: Array = []
	var i := goal
	while i > 0:
		chain.push_front(nodes[i])
		i = nodes[i][2]
	var prev: Array = nodes[0]
	for n in chain:
		_plan.append(n[3])
		_expect.append(Vector2(prev[0], prev[1]))
		prev = n


func _jitter(i: int) -> float:
	return float((i * 2654435761) % 1000) / 1000.0
