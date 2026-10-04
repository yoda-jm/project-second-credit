class_name FuseBot
extends RefCounted
## The Fuseflight autopilot (the demo). A few times a second it tries six moves on a copy of the game (run left,
## stand, run right, each with or without a leap, held for a moment) and takes the one that keeps it alive and brings
## it closest to its target: the lit firework (or the nearest one before any is lit), the power star when it is near,
## the enemies while the power lasts. A target higher than a leap goes by the platform below it (chosen on the
## ground, kept through the leap). Leaps are held to rise; falls glide when there is ground to cover sideways. Paths
## score by how near they pass the target and where they end.

const F = preload("res://games/fuseflight/engine/fuse_engine.gd")
const LOOK := 30          ## ticks to look ahead
const EVERY := 8          ## ticks between decisions

var _plan := [0.0, false]
var _aim := Vector2.ZERO
var _aim_set := false
var _t := 0
var _held := 0
var _idle := 0.0          ## seconds since the last firework taken
var _left := -1
var _skip := -1          ## a firework it gave up on for now (out of reach from here)


func drive(e: FuseEngine) -> void:
	e.move_x = 0.0
	e.jump_held = false
	e.jump_pressed = false
	if e.phase != F.Phase.PLAY:
		return
	if e.left() != _left:
		_left = e.left()
		_idle = 0.0
		_skip = -1
	_idle += F.TICK
	if _idle > 15.0:
		# no firework for a while: give up on this one for now and go for another (and, after as long again, retry it)
		_idle = 0.0
		_skip = e.lit if _skip == -1 else -1
	_t -= 1
	if _t <= 0:
		_t = EVERY
		_plan = _choose(e)
		_held = 0
	e.move_x = _plan[0]
	_apply_jump(e, _plan[1], _held, _target(e))
	_held += 1


func _apply_jump(e: FuseEngine, leap: bool, t: int, aim: Vector2) -> void:
	var h := e.hero
	if leap:
		e.jump_pressed = h["ground"] and t == 0
		e.jump_held = true
	else:
		# no leap: glide on the way down when the target is to the side
		var to: Vector2 = aim - h["pos"]
		e.jump_held = not h["ground"] and absf(to.x) > 1.0


func _choose(e: FuseEngine) -> Array:
	var target := _target(e)
	var best := [0.0, false]
	var best_s := -INF
	for mx in [-1.0, 0.0, 1.0]:
		for leap in [false, true]:
			var c := e.copy()
			var dead := false
			var nearest := INF
			var closest := INF
			for k in LOOK:
				c.move_x = mx
				_apply_jump(c, leap, k, target)
				c.tick()
				if c.phase == F.Phase.DYING:
					dead = true
					break
				if c.phase != F.Phase.PLAY:
					break
				for en in c.enemies:
					nearest = minf(nearest, (en["pos"] as Vector2).distance_to(c.hero["pos"]))
				closest = minf(closest, (c.hero["pos"] as Vector2).distance_to(target))
			# the path that passes nearest the target, then ends nearest it
			var s: float = -0.6 * closest - 0.4 * (c.hero["pos"] as Vector2).distance_to(target)
			if c.left() < e.left():
				s += 20.0  # it took a firework
			if dead:
				s -= 1000.0
			s += minf(nearest, 3.0) * 0.4
			if leap and e.hero["ground"]:
				s -= 0.3  # no needless leaps
			if s > best_s:
				best_s = s
				best = [mx, leap]
	return best


const REACH := 3.6        ## how far above its feet a held leap lifts the sprite's feet


## Where to aim on the way to a goal (the sprite's feet): a goal higher than a leap from here goes by the platform
## below it that a leap does reach (and one below that, if need be).
func _waypoint(e: FuseEngine, goal: Vector2) -> Vector2:
	var feet: Vector2 = e.hero["pos"]
	for step in 3:
		if goal.y - feet.y <= REACH:
			return goal
		var best := Rect2()
		var bd := INF
		for r in e.stage.platforms:
			var top := r.end.y
			if top > goal.y - 0.2 or top < goal.y - REACH:
				continue
			var dx := maxf(0.0, maxf(r.position.x - goal.x, goal.x - r.end.x))
			if dx < bd:
				bd = dx
				best = r
		if bd == INF:
			return goal
		var stand := Vector2(clampf(goal.x, best.position.x + 0.4, best.end.x - 0.4), best.end.y)
		if absf(feet.y - stand.y) < 0.1 and feet.x > best.position.x and feet.x < best.end.x:
			return goal  # already on it
		goal = stand
	return goal


## The aim is chosen on the ground and kept through a leap (else leaving a waypoint platform would pull it back).
func _target(e: FuseEngine) -> Vector2:
	if e.hero["ground"] or not _aim_set or e.power > 0.0:
		_aim = _waypoint(e, _goal(e))
		_aim_set = true
	return _aim


func _goal(e: FuseEngine) -> Vector2:
	var p: Vector2 = e.hero["pos"]
	if e.power > 0.0 and not e.enemies.is_empty():
		var best: Vector2 = e.enemies[0]["pos"]
		for en in e.enemies:
			if (en["pos"] as Vector2).distance_to(p) < best.distance_to(p):
				best = en["pos"]
		return best
	if not e.star.is_empty() and (e.star["pos"] as Vector2).distance_to(p) < 4.0:
		return e.star["pos"]
	if e.lit >= 0 and e.lit != _skip:
		return e.stage.bombs[e.lit] - Vector2(0, F.TALL * 0.5)
	var best := Vector2(8, 6)
	var bd := INF
	var skip := _skip if e.left() > 1 else -1
	for i in e.stage.bombs.size():
		if e.taken[i] == 0 and i != skip:
			var d := (e.stage.bombs[i] as Vector2).distance_to(p)
			if d < bd:
				bd = d
				best = e.stage.bombs[i]
	return best - Vector2(0, F.TALL * 0.5)
