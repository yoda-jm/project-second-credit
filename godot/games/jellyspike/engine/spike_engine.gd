class_name SpikeEngine
extends RefCounted
## Jelly Spike rules (blob volleyball in the Blobby Volley tradition; our own tuning), 60 Hz ticks. The court is 16
## wide, y up, the floor at 0, the net in the middle (x = 8, 2.4 high). Each side has one jelly blob (a circle) that
## walks and jumps on its own half. The beach ball is floaty; it bounces off the walls, the net and the blobs, taking
## on the blob's own speed, so a blob jumping into it spikes it. A side may touch the ball three times; the ball on the
## floor of your half, or a fourth touch, gives the point to the other side. Rally points to 15, won by two; the side
## that won the rally serves: the ball hangs over the server's head until the server touches it.
## Events: "serve" {side}, "touch" {side, n, speed}, "jump" {side}, "land" {side}, "net", "wall", "floor" {x},
## "point" {side, why}, "match" {winner}.

signal event(kind: String, data: Dictionary)

enum Phase { SERVE, RALLY, POINT, OVER }
const TICK := 1.0 / 60.0
const W := 16.0
const NET_X := 8.0
const NET_H := 2.4
const NET_HALF := 0.08
const BLOB_R := 0.62
const BALL_R := 0.36
const WALK := 5.6
const JUMP_V := 10.5
const BLOB_G := 26.0
const BALL_G := 9.5
const BOUNCE := 10.0          ## the least speed the ball leaves a blob with
const MAX_BALL := 14.0
const TOUCHES := 3
const TARGET := 15

var phase := Phase.SERVE
var phase_t := 0.8
var time := 0.0
var score := [0, 0]
var server := 0
var touches := [0, 0]
var last_side := -1
var blobs: Array[Dictionary] = []   ## {pos (centre), vel, ground, cool}
var ball := {}                      ## {pos, vel, hanging}
var move := [0.0, 0.0]              ## input per side: -1, 0, 1
var jump := [false, false]          ## held per side
var winner := -1
var rng := RandomNumberGenerator.new()


func _init(first_server := 0, seed_ := 1) -> void:
	rng.seed = seed_
	server = first_server
	for s in 2:
		blobs.append({"pos": Vector2(_home(s), BLOB_R), "vel": Vector2.ZERO, "ground": true, "cool": 0.0})
	_serve()


static func _home(side: int) -> float:
	return 3.0 if side == 0 else W - 3.0


## The x range a side's blob may stand in (its half of the court, clear of the net).
static func half(side: int) -> Vector2:
	return Vector2(BLOB_R, NET_X - NET_HALF - BLOB_R) if side == 0 else Vector2(NET_X + NET_HALF + BLOB_R, W - BLOB_R)


func _serve() -> void:
	phase = Phase.SERVE
	phase_t = 0.8
	touches = [0, 0]
	last_side = -1
	for s in 2:
		var b := blobs[s]
		b["pos"] = Vector2(_home(s), BLOB_R)
		b["vel"] = Vector2.ZERO
		b["ground"] = true
	ball = {"pos": Vector2(_home(server), 3.3), "vel": Vector2.ZERO, "hanging": true}
	event.emit("serve", {"side": server})


# ------------------------------------------------------------------ the tick

func tick() -> void:
	time += TICK
	match phase:
		Phase.OVER:
			return
		Phase.POINT:
			phase_t -= TICK
			_move_ball()  # it rolls to a stop
			_move_blobs()
			if phase_t <= 0.0:
				_serve()
			return
		Phase.SERVE:
			phase_t -= TICK
			_move_blobs()
			if _touch():
				phase = Phase.RALLY
			return
	_move_blobs()
	_move_ball()
	_touch()


func _move_blobs() -> void:
	for s in 2:
		var b := blobs[s]
		var v: Vector2 = b["vel"]
		var p: Vector2 = b["pos"]
		b["cool"] = maxf(0.0, b["cool"] - TICK)
		v.x = move[s] * WALK
		if jump[s] and b["ground"]:
			v.y = JUMP_V
			b["ground"] = false
			event.emit("jump", {"side": s})
		# let go early and the jump is lower (a quick hop)
		if not jump[s] and v.y > 0.0 and not b["ground"]:
			v.y -= BLOB_G * TICK * 0.8
		v.y -= BLOB_G * TICK
		p += v * TICK
		var h := half(s)
		p.x = clampf(p.x, h.x, h.y)
		if p.y <= BLOB_R:
			if not b["ground"]:
				event.emit("land", {"side": s})
			p.y = BLOB_R
			v.y = 0.0
			b["ground"] = true
		b["pos"] = p
		b["vel"] = v


func _move_ball() -> void:
	if ball["hanging"]:
		return
	var p: Vector2 = ball["pos"]
	var v: Vector2 = ball["vel"]
	var was_left: bool = p.x < NET_X
	v.y -= BALL_G * TICK
	p += v * TICK
	if (p.x < NET_X) != was_left:
		# over the net: a fresh set of touches for both sides
		touches = [0, 0]
		last_side = -1
	# walls
	if p.x < BALL_R:
		p.x = BALL_R
		v.x = absf(v.x) * 0.9
		event.emit("wall", {})
	elif p.x > W - BALL_R:
		p.x = W - BALL_R
		v.x = -absf(v.x) * 0.9
		event.emit("wall", {})
	# the net: a post with a round top
	var top := Vector2(NET_X, NET_H)
	if p.y < NET_H and absf(p.x - NET_X) < NET_HALF + BALL_R:
		p.x = NET_X + signf(p.x - NET_X + 0.0001) * (NET_HALF + BALL_R)
		v.x = -v.x * 0.8
		event.emit("net", {})
	elif p.distance_to(top) < NET_HALF + BALL_R and p.y >= NET_H:
		var n := (p - top).normalized()
		p = top + n * (NET_HALF + BALL_R)
		v = v - 2.0 * v.dot(n) * n * (1.0 if v.dot(n) < 0.0 else 0.0)
		v *= 0.85
		event.emit("net", {})
	# the floor
	if p.y < BALL_R:
		p.y = BALL_R
		if phase == Phase.RALLY:
			event.emit("floor", {"x": p.x})
			_point(1 if p.x < NET_X else 0, "floor")
		v.y = absf(v.y) * 0.45
		v.x *= 0.7
	ball["pos"] = p
	ball["vel"] = v


## Blob against ball; true when a blob touched it this tick.
func _touch() -> bool:
	var hit := false
	for s in 2:
		var b := blobs[s]
		var bp: Vector2 = b["pos"]
		var p: Vector2 = ball["pos"]
		var d := p - bp
		var r := BLOB_R + BALL_R
		if d.length() >= r or d.length() < 0.0001:
			continue
		var n := d.normalized()
		if n.y < -0.3 and not b["ground"]:
			n = Vector2(n.x, 0.0).normalized() if absf(n.x) > 0.01 else Vector2(signf(NET_X - bp.x), 0)
		ball["pos"] = bp + n * r
		var bv: Vector2 = b["vel"]
		var v: Vector2 = ball["vel"]
		var rel := v - bv
		var out := rel - 2.0 * rel.dot(n) * n if rel.dot(n) < 0.0 else rel
		out = out + bv * 0.6
		if out.dot(n) < BOUNCE:
			out += n * (BOUNCE - out.dot(n))
		if out.length() > MAX_BALL:
			out = out.normalized() * MAX_BALL
		ball["vel"] = out
		ball["hanging"] = false
		hit = true
		if b["cool"] <= 0.0 and phase != Phase.POINT:
			b["cool"] = 0.25
			if last_side != s:
				touches[1 - s] = 0
			last_side = s
			touches[s] += 1
			event.emit("touch", {"side": s, "n": touches[s], "speed": out.length()})
			if touches[s] > TOUCHES and phase == Phase.RALLY:
				_point(1 - s, "touches")
	return hit


func _point(side: int, why: String) -> void:
	score[side] += 1
	server = side
	event.emit("point", {"side": side, "why": why})
	if score[side] >= TARGET and score[side] - score[1 - side] >= 2:
		phase = Phase.OVER
		winner = side
		event.emit("match", {"winner": side})
		return
	phase = Phase.POINT
	phase_t = 1.6
