class_name NovaBot
extends RefCounted
## The Nova Wardens autopilot (the demo). It first stays out of the way of falling bombs (where each will be when it
## reaches the cannon's row), then lines up under its target and fires whenever its shot is free: the mystery ship
## when it passes, otherwise the outermost column with invaders (the classic way: the fleet then has further to go
## before it turns, so it comes down more slowly), the lowest invader in it first.

const N = preload("res://games/novawardens/engine/nova_engine.gd")

var _target := 104.0


func drive(e: NovaEngine) -> void:
	e.move_x = 0.0
	e.fire_pressed = false
	if e.phase != N.Phase.PLAY:
		return
	var cx := e.cannon_x + N.CANNON_W * 0.5
	_target = _aim(e)
	# bombs: where will each be when it reaches the cannon?
	var danger := []
	for b in e.bombs:
		var p: Vector2 = b["pos"]
		if p.y < N.CANNON_Y + 8:
			var t := (N.CANNON_Y - p.y) / N.BOMB_SPEED
			if t < 1.2:
				danger.append(p.x)
	var best := 0.0
	var best_s := -INF
	for dir in [-1.0, 0.0, 1.0]:
		var nx := clampf(cx + dir * N.CANNON_SPEED * 0.25, 16.0 + N.CANNON_W * 0.5, N.W - 16.0 - N.CANNON_W * 0.5)
		var s := -absf(nx - _target) * 0.2
		for dx in danger:
			var gap: float = absf(nx - dx)
			if gap < N.CANNON_W * 0.5 + 5.0:
				s -= 100.0 + (N.CANNON_W * 0.5 + 5.0 - gap) * 10.0
		if s > best_s:
			best_s = s
			best = dir
	e.move_x = best
	if absf(cx - _target) < 3.0 and best_s > -50.0:
		e.move_x = 0.0
	if e.shot.is_empty() and _something_above(e, cx):
		e.fire_pressed = true


func _aim(e: NovaEngine) -> float:
	if not e.ufo.is_empty():
		# lead the ship: the shot takes a while to climb
		var t := (N.CANNON_Y - N.UFO_Y) / N.SHOT_SPEED
		return clampf(e.ufo["x"] + 8.0 + e.ufo["dir"] * N.UFO_SPEED * t, 20.0, N.W - 20.0)
	# the fleet's speed now: one whole step each time every surviving invader has moved once
	var left := e.invaders_left()
	var speed := N.STEP_X * 60.0 / maxf(1.0, left) * e.dir
	var lo := N.COLS
	var hi := -1
	for c in N.COLS:
		for r in N.ROWS:
			if e.alive[r * N.COLS + c] == 1:
				lo = mini(lo, c)
				hi = maxi(hi, c)
				break
	if hi < 0:
		return 104.0
	# the edge the fleet is heading for first (the lowest invader of that column), where it will be when a shot
	# fired now gets there
	var col := hi if e.dir > 0 else lo
	for r in range(N.ROWS - 1, -1, -1):
		var i := r * N.COLS + col
		if e.alive[i] == 1:
			return _future_x(e, i, speed)
	return 104.0


## Where invader i's middle will be when a shot fired now reaches its row (bouncing off the side walls).
func _future_x(e: NovaEngine, i: int, speed: float) -> float:
	var p := e.invader_pos(i)
	var t := (N.CANNON_Y - (p.y + N.INV_H)) / N.SHOT_SPEED
	var x := p.x + N.INV_W * 0.5 + speed * t
	var lo := 8.0 + N.INV_W * 0.5
	var hi := N.W - 8.0 - N.INV_W * 0.5
	if x > hi:
		x = hi - (x - hi)
	elif x < lo:
		x = lo + (lo - x)
	return clampf(x, 20.0, N.W - 20.0)


func _something_above(e: NovaEngine, cx: float) -> bool:
	if not e.ufo.is_empty():
		var t := (N.CANNON_Y - N.UFO_Y) / N.SHOT_SPEED
		var ux: float = e.ufo["x"] + 8.0 + e.ufo["dir"] * N.UFO_SPEED * t
		if absf(ux - cx) < 5.0:
			return true
	var speed := N.STEP_X * 60.0 / maxf(1.0, e.invaders_left()) * e.dir
	for i in N.COLS * N.ROWS:
		if e.alive[i] == 1 and absf(_future_x(e, i, speed) - cx) < N.INV_W * 0.5 - 1.0:
			return true
	return false
