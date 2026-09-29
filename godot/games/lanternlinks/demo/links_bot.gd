class_name LinksBot
extends RefCounted
## The CPU golfer (and the demo's autopilot). It plans a shot by simulating candidates with the game's own physics
## from the moment it will strike (the gadgets are functions of the hole clock): a coarse ring of angles and
## powers, then a finer search around the best few. A resting ball is scored by the walking distance to the cup
## (a distance field over the cells: through water and chasms at a price, pipes as shortcuts); a holed shot scores
## best, a lost ball worst. Among holed shots it prefers the one whose neighbours hole too (a robust line). The
## work is sliced: `think` runs until a time budget is spent and says when the plan is ready. `skill` scatters the
## final stroke a little (0: perfect).

const H = preload("res://games/lanternlinks/engine/links_hole.gd")
const B = preload("res://games/lanternlinks/engine/links_ball.gd")
const P = preload("res://games/lanternlinks/engine/links_physics.gd")

const ANGLES := 40
const POWERS: Array[float] = [0.12, 0.21, 0.31, 0.43, 0.57, 0.73, 0.88, 1.0]
const TOP := 4
const FINE := 1                 ## the fine grid is (2 FINE + 1)² around each of the top candidates
const FINE_DA := 0.022          ## radians between fine angles
const FINE_DP := 0.025

var hole: LinksHole
var dist := PackedFloat32Array()
var angle := 0.0
var power := 0.0
var ready := false
var skill := 0.0
var rng := RandomNumberGenerator.new()

var _ball: LinksBall
var _clock := 0.0
var _queue: Array = []          ## [angle, power] still to try in this stage
var _scored: Array = []         ## [cost, angle, power]
var _stage := 0
var _fine := {}                 ## "a|p" -> cost, for the robustness pass


func _init(h: LinksHole, seed_value := 7) -> void:
	hole = h
	rng.seed = seed_value
	_distance_field()


## Starts planning a shot for `ball` struck at hole time `clock`.
func plan(ball: LinksBall, clock: float) -> void:
	_ball = ball.copy()
	_clock = clock
	ready = false
	_stage = 0
	_scored.clear()
	_fine.clear()
	_queue.clear()
	# the ring starts from the line to the cup, so the first candidates are the likeliest
	var base := (hole.cup - ball.pos).angle()
	for i in ANGLES:
		var k := (i + 1) / 2 * (1 if i % 2 == 1 else -1)
		for p in POWERS:
			_queue.append([base + k * TAU / ANGLES, p])


## Works on the plan for about `budget_ms`; returns true once `angle` and `power` are set.
func think(budget_ms := 1000000.0) -> bool:
	if ready:
		return true
	var until := Time.get_ticks_usec() + int(budget_ms * 1000.0)
	while Time.get_ticks_usec() < until:
		if _queue.is_empty():
			if _next_stage():
				return true
			continue
		var c: Array = _queue.pop_back()
		var cost := evaluate(c[0], c[1])
		_scored.append([cost, c[0], c[1]])
		if _stage == 1:
			_fine["%d|%d" % [roundi(c[0] / FINE_DA), roundi(c[1] / FINE_DP)]] = cost
	return false


func _next_stage() -> bool:
	_scored.sort_custom(func(a, b): return a[0] < b[0])
	if _stage == 0:
		_stage = 1
		var seen := {}
		var picked := 0
		for s in _scored:
			if picked >= TOP:
				break
			var key := "%d|%d" % [roundi(s[1] / (TAU / ANGLES)), roundi(s[2] * 10.0)]
			if seen.has(key):
				continue
			seen[key] = true
			picked += 1
			var a0 := roundf(s[1] / FINE_DA) * FINE_DA
			var p0 := roundf(s[2] / FINE_DP) * FINE_DP
			for da in range(-FINE, FINE + 1):
				for dp in range(-FINE, FINE + 1):
					var p := p0 + dp * FINE_DP
					if p > 0.04 and p <= 1.0:
						_queue.append([a0 + da * FINE_DA, p])
		return false
	# robustness: a candidate's cost blended with its fine neighbours'
	var best := INF
	for s in _scored:
		var ka := roundi(s[1] / FINE_DA)
		var kp := roundi(s[2] / FINE_DP)
		var sum: float = s[0] * 2.0
		var n := 2.0
		for d in [[1, 0], [-1, 0], [0, 1], [0, -1]]:
			var key := "%d|%d" % [ka + d[0], kp + d[1]]
			if _fine.has(key):
				sum += _fine[key]
				n += 1.0
		var v := sum / n
		if v < best:
			best = v
			angle = s[1]
			power = s[2]
	if skill > 0.0:
		angle += rng.randfn(0.0, 0.05 * skill)
		power = clampf(power * (1.0 + rng.randfn(0.0, 0.09 * skill)), 0.05, 1.0)
	ready = true
	return true


## Simulates a stroke and scores where it ends (lower is better).
func evaluate(a: float, p: float) -> float:
	var b := _ball.copy()
	b.vel = Vector2.from_angle(a) * p * P.MAX_SPEED
	var end := P.simulate(hole, b, _clock)
	return outcome(end, _ball.pos)


func outcome(end: LinksBall, from: Vector2) -> float:
	match end.mode:
		B.Mode.SUNK:
			return -10.0
		B.Mode.LOST:
			return field(from) + 3.0
	var c := field(end.pos)
	if hole.kind_at(end.pos) == H.SAND:
		c += 0.6
	return c


## The walking distance (m) from a point to the cup.
func field(p: Vector2) -> float:
	var i := hole.index(p)
	if i < 0:
		return 100.0
	var cc := hole.centre(i % hole.w, i / hole.w)
	if i == hole.index(hole.cup):
		return p.distance_to(hole.cup)
	return dist[i] + p.distance_to(cc) * 0.5


func _distance_field() -> void:
	var n := hole.w * hole.h
	dist.resize(n)
	dist.fill(1000.0)
	var ci := hole.index(hole.cup)
	dist[ci] = 0.0
	var open := [ci]
	var links := {}   # pipe exits lead back to their mouths
	for g in hole.gadgets:
		if g["type"] == "pipe":
			links[hole.index(g["b"])] = hole.index(g["a"])
	# a simple label-correcting search (the grids are small)
	while not open.is_empty():
		var i: int = open.pop_front()
		var x := i % hole.w
		var y := i / hole.w
		var steps: Array = []
		for d in [[1, 0, 1.0], [-1, 0, 1.0], [0, 1, 1.0], [0, -1, 1.0], [1, 1, 1.414], [1, -1, 1.414], [-1, 1, 1.414], [-1, -1, 1.414]]:
			var nx: int = x + d[0]
			var ny: int = y + d[1]
			if nx < 0 or ny < 0 or nx >= hole.w or ny >= hole.h:
				continue
			var j := ny * hole.w + nx
			if hole.kind[j] <= H.WALL:
				continue
			if d[2] > 1.0 and (hole.kind[y * hole.w + nx] <= H.WALL or hole.kind[ny * hole.w + x] <= H.WALL):
				continue
			var cost: float = d[2] * H.CELL
			if hole.kind[j] in [H.WATER, H.CHASM]:
				cost *= 3.0
			elif hole.kind[j] == H.SAND:
				cost *= 1.5
			steps.append([j, cost])
		if links.has(i):
			steps.append([links[i], 0.5])
		for s in steps:
			var nd: float = dist[i] + s[1]
			if nd < dist[s[0]] - 1e-4:
				dist[s[0]] = nd
				open.append(s[0])
	# a pipe's mouth is as good as where it leads
	for g in hole.gadgets:
		if g["type"] == "pipe":
			var a := hole.index(g["a"])
			dist[a] = minf(dist[a], dist[hole.index(g["b"])] + 0.5)
