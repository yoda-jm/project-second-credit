class_name DriftBot
extends RefCounted
## The Marble Drift autopilot (the demo): it rolls from route point to route point, steering like a careful player:
## it wants a speed towards the next point (slower before a sharp turn and when close), and pushes to close the gap
## between that and how it is rolling (a damped controller), so it brakes on downhill stretches. After a broken
## marble it carries on from the checkpoint.

const D = preload("res://games/marbledrift/engine/drift_engine.gd")
const CRUISE := 5.5
const REACH := 1.1

var _i := 0


func drive(e: DriftEngine) -> void:
	e.input = Vector2.ZERO
	if e.phase != D.Phase.PLAY:
		if e.phase == D.Phase.DYING:
			# carry on from where the marble comes back
			var rp := e.respawn_point()
			_i = maxi(0, e.course.route.find(rp))
		return
	var r := e.course.route
	if r.is_empty():
		return
	var p := e.ball_xz()
	while _i < r.size() - 1 and p.distance_to(r[_i]) < REACH:
		_i += 1
	var target: Vector2 = r[mini(_i, r.size() - 1)]
	var to := target - p
	var dist := to.length()
	# slow before a sharp turn at the next point
	var speed := CRUISE
	if _i + 1 < r.size():
		var nxt: Vector2 = r[_i + 1] - target
		var turn := 1.0 - clampf(to.normalized().dot(nxt.normalized()), -1.0, 1.0)
		speed = lerpf(CRUISE, 2.2, clampf(turn, 0.0, 1.0)) if dist < 3.5 else CRUISE
	speed = minf(speed, 1.2 + dist * 1.5)
	var hint: float = e.course.route_speed[mini(_i, r.size() - 1)] if _i < e.course.route_speed.size() else 0.0
	if hint > 0.0:
		speed = hint  # the course asks for this speed here (a run-up to a jump)
	var want := to.normalized() * speed
	var v := Vector2(e.ball["vel"].x, e.ball["vel"].z)
	e.input = ((want - v) * 0.6).limit_length(1.0)
