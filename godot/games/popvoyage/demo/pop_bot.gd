class_name PopBot
extends RefCounted
## The Pop Voyage autopilot (the demo). Every few ticks it plays the balloons forward about a second for each choice
## (walk left, stand, walk right), throws out the choices a balloon would touch him in, and of the safe ones takes the
## one that brings him under a balloon he can shoot; it fires when a balloon is over his head. Items are picked up on
## the way.

const P = preload("res://games/popvoyage/engine/pop_engine.gd")
const HORIZON := 1.3
const DT := 1.0 / 30.0

var _choice := 0.0
var _think := 0


func drive(e: PopEngine) -> void:
	e.move_x = 0.0
	if e.phase != P.Phase.PLAY:
		return
	_think -= 1
	if _think <= 0:
		_think = 4
		_choice = _decide(e)
	e.move_x = _choice
	var x: float = e.hero["x"]
	if e.wires.filter(func(w): return not w["stuck"]).size() >= (2 if e.weapon == "double" else 1):
		return
	for b in e.balls:
		if _hits(e, b, x):
			e.fire_pressed = true
			break


## Would a wire fired now from x meet this balloon? (It rises at WIRE_SPEED while the balloon drifts on.)
func _hits(e: PopEngine, b: Dictionary, x: float) -> bool:
	var r: float = P.RADIUS[b["size"]]
	var p: Vector2 = b["pos"]
	var v: Vector2 = b["vel"] if e.frozen <= 0.0 else Vector2.ZERO
	# a big one split low over his head drops its halves on him
	if b["size"] > 0 and p.y - r < 2.6 and b["vel"].y < 3.0:
		return false
	var t := maxf(0.0, (p.y - r - P.TALL * 0.6) / P.WIRE_SPEED)
	var px := p.x + v.x * t
	if px < r or px > P.W - r:
		px = p.x  # it turns at the wall: just use where it is
	return absf(px - x) < r * 0.85 + (0.12 if b["size"] == 0 else 0.0)


func _decide(e: PopEngine) -> float:
	var best := 0.0
	var best_score := -INF
	var x: float = e.hero["x"]
	var target := _target(e)
	# two-step plans: a move now, then maybe another; the first move of the best plan is taken
	for d1 in [-1.0, 0.0, 1.0]:
		for d2 in [-1.0, 0.0, 1.0]:
			var clear := _clearance(e, d1, d2)
			var nx := clampf(x + d1 * P.WALK * 0.35, P.HALF, P.W - P.HALF)
			var s := 0.0
			if clear < 0.45:
				s -= 100.0 + (0.45 - clear) * 100.0
			s += minf(clear, 1.5)
			s -= absf(nx - target) * 1.5
			s -= maxf(0.0, 1.8 - minf(nx, P.W - nx)) * 3.0  # a wall is a trap
			if s > best_score:
				best_score = s
				best = d1
	return best


## Where to stand: under the balloon that is highest above him (a safe shot), or an item.
func _target(e: PopEngine) -> float:
	var x: float = e.hero["x"]
	for it in e.items:
		if absf(it["pos"].x - x) < 4.0:
			return it["pos"].x
	# a low balloon coming at him first: meet it with the wire
	var threat := INF
	var tx := x
	for b in e.balls:
		var p: Vector2 = b["pos"]
		var coming: bool = signf(x - p.x) == signf(b["vel"].x)
		var d := absf(p.x - x)
		if coming and b["size"] <= 1 and d < 3.5 and p.y < 3.5 and d < threat:
			threat = d
			tx = p.x + b["vel"].x * 0.35
	if threat < INF:
		return clampf(tx, 1.0, P.W - 1.0)
	var best := x
	var best_s := -INF
	for b in e.balls:
		var p: Vector2 = b["pos"]
		var s: float = p.y - absf(p.x - x) * 0.6 + (1.5 if b["vel"].y > 0.0 else 0.0) - b["size"] * 0.3
		if s > best_s:
			best_s = s
			best = p.x + b["vel"].x * maxf(0.0, p.y - 1.0) / P.WIRE_SPEED  # where the wire will meet it
	return clampf(best, 1.0, P.W - 1.0)


## The nearest a balloon comes to him over the horizon if he keeps walking this way (without the wire's help).
func _clearance(e: PopEngine, d1: float, d2: float) -> float:
	if e.frozen > HORIZON:
		return 9.0
	var x: float = e.hero["x"]
	var sims: Array = []
	for b in e.balls:
		sims.append([b["pos"], b["vel"], b["size"]])
	var best := 9.0
	var t := 0.0
	var frozen: float = e.frozen
	while t < HORIZON:
		t += DT
		x = clampf(x + (d1 if t < 0.4 else d2) * P.WALK * DT, P.HALF, P.W - P.HALF)
		if frozen > 0.0:
			frozen -= DT
		for s in sims:
			var p: Vector2 = s[0]
			var v: Vector2 = s[1]
			var sz: int = s[2]
			var r: float = P.RADIUS[sz]
			if frozen <= 0.0:
				v.y -= P.G * DT
				p += v * DT
				if p.x - r < 0.0 or p.x + r > P.W:
					v.x = -v.x
				if p.y - r < 0.0:
					p.y = r
					v.y = sqrt(2.0 * P.G * P.BOUNCE[sz])
				if p.y + r > P.H:
					v.y = -absf(v.y)
				s[0] = p
				s[1] = v
			var q := Vector2(clampf(p.x, x - P.HALF, x + P.HALF), clampf(p.y, 0.0, P.TALL))
			best = minf(best, p.distance_to(q) - r)
	return best
