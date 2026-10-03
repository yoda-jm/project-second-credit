class_name DriftEngine
extends RefCounted
## Marble Drift rules (a marble race down floating courses in the Marble Madness tradition; our own tuning), 60 Hz.
## The marble rolls on the course's height field: slopes pull it along, the player pushes it (screen-relative, turned
## into course directions by the game), floors grip more or less (glass is slippery, rough floor holds). It flies off
## edges and lands; a fall of more than BREAK_DROP shatters it, acid dissolves it, the void swallows it: it comes back
## at the last checkpoint (the route's points double as checkpoints) and the clock keeps running. Walls bounce it.
## The black steelie hunts the marble and knocks it about; hoppers patrol and bump it. Reach the goal before the
## clock runs out: the time left carries over to the next course (and scores).
## Events: "bump" {speed}, "land" {drop}, "shatter" {pos}, "fall" {pos}, "acid" {pos}, "respawn", "checkpoint" {n},
## "knock" {kind, speed}, "finish" {time_left}, "time_low", "time_up", "go".

signal event(kind: String, data: Dictionary)

enum Phase { READY, PLAY, DYING, FINISHED, OVER }
const TICK := 1.0 / 60.0
const R := 0.3               ## the marble's radius
const G := 22.0
const PUSH := 10.0           ## how hard the player pushes (units/s² at full stick)
const DRAG := 0.55           ## rolling resistance, per second
const MAX_SPEED := 15.0
const BREAK_DROP := 3.2      ## a fall from higher than this shatters the marble
const STEP := 0.45           ## a rise sharper than this is a wall
const GRIP := {".": 1.0, "G": 1.0, "=": 0.45, "^": 1.5, "~": 1.0, "#": 1.0}
const DRAGS := {".": 1.0, "G": 1.0, "=": 0.35, "^": 2.2, "~": 1.0, "#": 1.0}

var course: DriftCourse
var phase := Phase.READY
var phase_t := 2.0
var time := 0.0
var clock := 60.0
var score := 0
var ball := {}
var input := Vector2.ZERO      ## the push, in course directions (x, z), length <= 1
var checkpoint := 0            ## the furthest route point reached
var enemies: Array[Dictionary] = []
var death := ""
var _warned := false


func _init(c: DriftCourse, carried := 0.0, score_ := 0) -> void:
	course = c
	clock = c.time + carried
	score = score_
	for e in c.enemies:
		var d: Dictionary = e.duplicate()
		d["home"] = d["pos"]
		d["vel"] = Vector3.ZERO
		d["y"] = c.height_at(d["pos"])
		d["air"] = false
		d["t"] = 0.0
		d["gone"] = 0.0
		enemies.append(d)
	_place(c.start)


func _place(p: Vector2) -> void:
	ball = {"pos": Vector3(p.x, course.height_at(p), p.y), "vel": Vector3.ZERO, "air": false, "fall_from": 0.0, "spin": Vector3.ZERO}


func ball_xz() -> Vector2:
	return Vector2(ball["pos"].x, ball["pos"].z)


## Where a broken marble comes back: the last checkpoint reached, skipping run-up points (a route point with a speed:
## coming back there at a standstill, with no room to gather speed, would only lead to the same fall).
func respawn_point() -> Vector2:
	for i in range(mini(checkpoint, course.route.size()) - 1, -1, -1):
		if i >= course.route_speed.size() or course.route_speed[i] <= 0.0:
			return course.route[i]
	return course.start


# ------------------------------------------------------------------ the tick

func tick() -> void:
	time += TICK
	match phase:
		Phase.READY:
			phase_t -= TICK
			if phase_t <= 0.0:
				phase = Phase.PLAY
				event.emit("go", {})
			return
		Phase.DYING:
			phase_t -= TICK
			clock -= TICK  # the clock does not stop for a broken marble
			if clock <= 0.0:
				_time_up()
				return
			if phase_t <= 0.0:
				_place(respawn_point())
				phase = Phase.PLAY
				event.emit("respawn", {})
			return
		Phase.FINISHED, Phase.OVER:
			phase_t -= TICK
			return
	clock -= TICK
	if clock < 10.0 and not _warned:
		_warned = true
		event.emit("time_low", {})
	if clock <= 0.0:
		_time_up()
		return
	_roll(ball, input, true)
	if phase != Phase.PLAY:
		return
	_enemies()
	_checkpoints()


## Moves a marble (the player's or the steelie) one tick: on the floor it follows the slope, in the air it falls.
func _roll(b: Dictionary, push: Vector2, player: bool) -> void:
	var p: Vector3 = b["pos"]
	var v: Vector3 = b["vel"]
	var xz := Vector2(p.x, p.z)
	var k := course.kind(int(floor(xz.x)), int(floor(xz.y)))
	if not b["air"]:
		var grad := course.gradient(xz)
		var acc := -G * grad / (1.0 + grad.length_squared())
		acc += push.limit_length(1.0) * PUSH * GRIP.get(k, 1.0)
		var hv := Vector2(v.x, v.z)
		hv += acc * TICK
		hv -= hv * DRAG * DRAGS.get(k, 1.0) * TICK
		hv = hv.limit_length(MAX_SPEED)
		v.x = hv.x
		v.z = hv.y
	else:
		v.y -= G * TICK
	var nxz := xz + Vector2(v.x, v.z) * TICK
	# walls and steps: a rise too sharp to roll up bounces the marble back
	var here := course.height_at(xz)
	for axis in 2:
		var probe := xz
		probe[axis] = nxz[axis] + signf(nxz[axis] - xz[axis]) * R
		var hp := course.height_at(probe)
		var floor_y: float = p.y if b["air"] else here
		if hp > floor_y + STEP:
			var spd := absf(v.x if axis == 0 else v.z)
			if axis == 0:
				v.x = -v.x * 0.45
			else:
				v.z = -v.z * 0.45
			nxz[axis] = xz[axis]
			if player and spd > 2.0:
				event.emit("bump", {"speed": spd})
	var g := course.height_at(nxz)
	if not b["air"]:
		if g == -INF or g < here - 0.35:
			# off an edge: it flies on with the slope's vertical speed
			b["air"] = true
			b["fall_from"] = p.y
			v.y = course.gradient(xz).dot(Vector2(v.x, v.z))
			p = Vector3(nxz.x, p.y + v.y * TICK, nxz.y)
		else:
			v.y = (g - p.y) / TICK
			p = Vector3(nxz.x, g, nxz.y)
	else:
		p = Vector3(nxz.x, p.y + v.y * TICK, nxz.y)
		if g != -INF and p.y <= g:
			var drop: float = b["fall_from"] - g
			p.y = g
			b["air"] = false
			if player:
				if drop > BREAK_DROP:
					b["pos"] = p
					_die("shatter")
					return
				if drop > 0.6:
					event.emit("land", {"drop": drop})
			# a landing on a slope keeps the speed along the floor
			v.y = 0.0
		elif p.y < -30.0:
			if player:
				b["pos"] = p
				_die("fall")
				return
			b["gone"] = 3.0
	b["pos"] = p
	b["vel"] = v
	# the marble's spin, for the view (rolling without slipping)
	b["spin"] = Vector3(v.z, 0.0, -v.x) / R
	if player and not b["air"]:
		var kk := course.kind(int(floor(p.x)), int(floor(p.z)))
		if kk == "~":
			_die("acid")
		elif kk == "G":
			_finish()


func _checkpoints() -> void:
	var r := course.route
	for i in range(checkpoint, r.size()):
		if ball_xz().distance_to(r[i]) < 1.6 and not ball["air"]:
			checkpoint = i + 1
			event.emit("checkpoint", {"n": checkpoint})


func _enemies() -> void:
	var me := ball_xz()
	for e in enemies:
		if e["gone"] > 0.0:
			e["gone"] -= TICK
			if e["gone"] <= 0.0:
				e["pos"] = e["home"]
				e["vel"] = Vector3.ZERO
				e["air"] = false
			continue
		match e["kind"]:
			"steelie":
				if not e.has("b"):
					e["b"] = {"pos": Vector3(e["pos"].x, course.height_at(e["pos"]), e["pos"].y), "vel": Vector3.ZERO, "air": false, "fall_from": 0.0, "spin": Vector3.ZERO, "gone": 0.0}
				var b: Dictionary = e["b"]
				var bxz := Vector2(b["pos"].x, b["pos"].z)
				var near := bxz.distance_to(me) < 9.0
				_roll(b, (me - bxz).normalized() * (0.75 if near else 0.0), false)
				if b.get("gone", 0.0) > 0.0:
					e["gone"] = 3.0
					e.erase("b")
					continue
				e["pos"] = Vector2(b["pos"].x, b["pos"].z)
				_collide_marbles(b)
			"hopper":
				# patrols to its end and back, hopping
				e["t"] += TICK
				var a: Vector2 = e["home"]
				var to: Vector2 = e.get("to", a)
				var span := maxf(0.5, a.distance_to(to))
				var k := 0.5 - 0.5 * cos(e["t"] * 1.6 / span * PI)
				e["pos"] = a.lerp(to, k)
				var d: Vector2 = me - e["pos"]
				if d.length() < R + 0.35 and not ball["air"]:
					var n := d.normalized() if d.length() > 0.001 else Vector2(1, 0)
					ball["vel"] += Vector3(n.x, 0, n.y) * 7.0
					event.emit("knock", {"kind": "hopper", "speed": 7.0})


## The player's marble and the steelie bounce off each other (the heavier steelie gives less).
func _collide_marbles(b: Dictionary) -> void:
	var pa: Vector3 = ball["pos"]
	var pb: Vector3 = b["pos"]
	var d := Vector2(pa.x - pb.x, pa.z - pb.z)
	if d.length() >= R * 2.0 or d.length() < 0.0001 or absf(pa.y - pb.y) > 0.6:
		return
	var n := d.normalized()
	var va := Vector2(ball["vel"].x, ball["vel"].z)
	var vb := Vector2(b["vel"].x, b["vel"].z)
	var rel := (va - vb).dot(n)
	if rel >= 0.0:
		return
	var j := -1.6 * rel
	va += n * j * 0.7   # the steelie is heavier
	vb -= n * j * 0.3
	ball["vel"] = Vector3(va.x, ball["vel"].y, va.y)
	b["vel"] = Vector3(vb.x, b["vel"].y, vb.y)
	var sep := (R * 2.0 - d.length()) * 0.5
	ball["pos"] += Vector3(n.x, 0, n.y) * sep
	b["pos"] -= Vector3(n.x, 0, n.y) * sep
	event.emit("knock", {"kind": "steelie", "speed": absf(rel)})


func _die(how: String) -> void:
	death = how
	phase = Phase.DYING
	phase_t = 2.0
	event.emit(how, {"pos": ball["pos"]})


func _finish() -> void:
	phase = Phase.FINISHED
	phase_t = 3.0
	score += int(clock * 10.0) + 1000
	event.emit("finish", {"time_left": clock})


func _time_up() -> void:
	clock = 0.0
	phase = Phase.OVER
	phase_t = 3.0
	event.emit("time_up", {})
