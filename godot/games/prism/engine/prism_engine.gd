class_name PrismEngine
extends RefCounted
## Prism Breaker rules (a brick breaker in the Arkanoid tradition; our own tuning), at fixed 120 Hz sub-steps, seeded.
## Field coordinates: x from 0 to 13 (bricks are 1 wide), y downward, bricks from y = TOP in rows of 0.5, the paddle
## at y = PADDLE_Y. Where the ball meets the paddle sets its angle (the edges send it wide). The ball speeds up as it
## goes. Capsules: wide, laser, catch, slow, multi (three balls), life, break (a door opens: leave the stage).
## Events: "paddle", "wall", "brick" {row, col, broken, kind}, "capsule_drop", "capsule" {kind}, "laser", "drone_pop",
## "lose_ball", "launch", "drone" {x}, "cleared", "game_over", "warp".

signal event(kind: String, data: Dictionary)

enum Phase { SERVE, PLAY, LOST, CLEARED, OVER }
const TICK := 1.0 / 120.0
const W := 13.0
const H := 17.0
const TOP := 2.0
const PADDLE_Y := 15.6
const BALL_R := 0.15
const SPEED0 := 8.5
const SPEED_MAX := 15.0
const GATES := [4.0, 9.0]  ## drones come in through two doors in the top of the frame (2 wide, centred here)
const WARP_Y := 16.0      ## the break door in the right wall (2 tall, centred here)
const CAPSULE_KINDS := ["wide", "laser", "catch", "slow", "multi", "life", "break"]
const CAPSULE_WEIGHTS := [24, 16, 16, 16, 16, 5, 7]

var level: PrismLevel
var stage := 0
var rng := RandomNumberGenerator.new()
var phase := Phase.SERVE
var time := 0.0
var score := 0
var lives := 3
var bricks := {}      ## Vector2i(col, row) -> {kind, hits}
var balls: Array[Dictionary] = []   ## {pos, vel, held (x offset on the paddle or -99), speed}
var paddle_x := 6.5
var paddle_w := 2.0
var target_x := 6.5   ## where the player wants the paddle (mouse, keys, bot)
var power := ""       ## the current capsule effect
var power_t := 0.0
var capsules: Array[Dictionary] = []  ## {pos, kind}
var bolts: Array[Dictionary] = []     ## {pos}
var drones: Array[Dictionary] = []    ## {pos, vel, kind, id}
var warp_open := false
var breakable := 0
var _next_drone := 6.0
var _laser_cool := 0.0
var _id := 1
var _since_break := 0.0  ## a ball stuck in a loop gets a nudge off the paddle after a while


func _init(lv: PrismLevel, stage_ := 0, seed_ := 1, lives_ := 3, score_ := 0) -> void:
	level = lv
	stage = stage_
	lives = lives_
	score = score_
	rng.seed = seed_
	for r in lv.rows.size():
		for c in PrismLevel.W:
			var ch := lv.rows[r][c]
			if ch == ".":
				continue
			var hits := 1
			match ch:
				"H": hits = 2 + mini(stage / 2, 3)
				"S", "G": hits = -1
			bricks[Vector2i(c, r)] = {"kind": ch, "hits": hits}
			if hits > 0:
				breakable += 1
	_serve()


func _serve() -> void:
	balls = [{"pos": Vector2(paddle_x, PADDLE_Y - BALL_R - 0.2), "vel": Vector2.ZERO, "held": 0.0, "speed": SPEED0 + stage * 0.3}]
	phase = Phase.SERVE
	capsules.clear()
	bolts.clear()
	power = ""
	paddle_w = 2.0


func brick_rect(c: Vector2i) -> Rect2:
	return Rect2(c.x, TOP + c.y * 0.5, 1.0, 0.5)


func launch() -> void:
	var any := false
	for b in balls:
		if b["held"] > -90.0:
			var off: float = b["held"]
			var ang := clampf(off / (paddle_w * 0.5), -1.0, 1.0) * 0.9
			b["vel"] = Vector2(sin(ang), -cos(ang)) * b["speed"]
			b["held"] = -99.0
			any = true
	if phase == Phase.SERVE:
		phase = Phase.PLAY
	if any:
		event.emit("launch", {})


func fire() -> void:
	if power == "laser" and _laser_cool <= 0.0 and phase == Phase.PLAY:
		_laser_cool = 0.3
		for dx in [-paddle_w * 0.4, paddle_w * 0.4]:
			bolts.append({"pos": Vector2(paddle_x + dx, PADDLE_Y - 0.3)})
		event.emit("laser", {})


# ------------------------------------------------------------------ the tick

func tick() -> void:
	time += TICK
	if phase == Phase.LOST or phase == Phase.CLEARED or phase == Phase.OVER:
		return
	# the paddle glides to where it is aimed, fast
	var half := paddle_w * 0.5
	var tx := clampf(target_x, half, W - half)
	paddle_x = move_toward(paddle_x, tx, 26.0 * TICK)
	if warp_open and target_x >= W - half + 0.05 and paddle_x >= W - half - 0.01:
		phase = Phase.CLEARED
		score += 10000
		event.emit("warp", {})
		return
	_laser_cool -= TICK
	_since_break += TICK
	if power_t > 0.0:
		power_t -= TICK
		if power_t <= 0.0 and power == "slow":
			for b in balls:
				b["speed"] = minf(SPEED_MAX, b["speed"] / 0.7)
			power = ""
	for b in balls.duplicate():
		_move_ball(b)
	balls = balls.filter(func(b): return b["pos"].y < H + 1.0)
	if balls.is_empty() and phase == Phase.PLAY:
		lives -= 1
		event.emit("lose_ball", {})
		phase = Phase.OVER if lives <= 0 else Phase.LOST
		if phase == Phase.OVER:
			event.emit("game_over", {})
		return
	_move_capsules()
	_move_bolts()
	_move_drones()


func respawn() -> void:
	_serve()


func _move_ball(b: Dictionary) -> void:
	if b["held"] > -90.0:
		b["pos"] = Vector2(paddle_x + b["held"], PADDLE_Y - BALL_R - 0.2)
		return
	# speed creeps up during play
	if power != "slow":
		b["speed"] = minf(SPEED_MAX, b["speed"] + TICK * 0.08)
	b["vel"] = b["vel"].normalized() * b["speed"]
	var steps := 2
	for i in steps:
		var p: Vector2 = b["pos"] + b["vel"] * TICK / steps
		var v: Vector2 = b["vel"]
		# the frame
		if p.x < BALL_R:
			p.x = BALL_R; v.x = absf(v.x); event.emit("wall", {})
		elif p.x > W - BALL_R:
			p.x = W - BALL_R; v.x = -absf(v.x); event.emit("wall", {})
		if p.y < BALL_R:
			p.y = BALL_R; v.y = absf(v.y); event.emit("wall", {})
		# the paddle
		if v.y > 0.0 and p.y + BALL_R >= PADDLE_Y - 0.17 and p.y < PADDLE_Y + 0.2 and absf(p.x - paddle_x) <= paddle_w * 0.5 + BALL_R:
			var off := (p.x - paddle_x) / (paddle_w * 0.5 + BALL_R)
			var ang := clampf(off, -1.0, 1.0) * 1.1  # up to ~63 degrees from straight up
			if _since_break > 7.0:
				ang = clampf(ang + rng.randf_range(-0.35, 0.35), -1.1, 1.1)
			v = Vector2(sin(ang), -cos(ang)) * b["speed"]
			p.y = PADDLE_Y - 0.17 - BALL_R
			event.emit("paddle", {"x": p.x})
			if power == "catch":
				b["held"] = p.x - paddle_x
				b["vel"] = Vector2.ZERO
				b["pos"] = p
				return
		# bricks: the nearest overlapping one bounces the ball on its shallower axis
		var hit := _brick_hit(p)
		if hit.x > -90:
			var r := brick_rect(hit)
			var cx := clampf(p.x, r.position.x, r.end.x)
			var cy := clampf(p.y, r.position.y, r.end.y)
			var d := p - Vector2(cx, cy)
			if absf(d.x) > absf(d.y) * 2.0:  # side hit (bricks are twice as wide as tall)
				v.x = absf(v.x) * signf(d.x) if d.x != 0.0 else -v.x
				p.x = cx + signf(d.x) * (BALL_R + 0.001)
			else:
				v.y = absf(v.y) * (signf(d.y) if d.y != 0.0 else -signf(v.y))
				p.y = cy + signf(d.y if d.y != 0.0 else -v.y) * (BALL_R + 0.001)
			_hit_brick(hit)
		# keep the ball from going too flat
		if absf(v.y) < b["speed"] * 0.22:
			v.y = signf(v.y if v.y != 0.0 else -1.0) * b["speed"] * 0.22
			v = v.normalized() * b["speed"]
		b["pos"] = p
		b["vel"] = v
		for dr in drones:
			if dr["pos"].distance_to(p) < 0.45:
				_pop_drone(dr)
				b["vel"].y = -b["vel"].y


func _brick_hit(p: Vector2) -> Vector2i:
	var col := int(floor(p.x))
	var row := int(floor((p.y - TOP) / 0.5))
	var best := Vector2i(-99, -99)
	var bd := INF
	for dy in range(-1, 2):
		for dx in range(-1, 2):
			var c := Vector2i(col + dx, row + dy)
			if not bricks.has(c):
				continue
			var r := brick_rect(c)
			var q := Vector2(clampf(p.x, r.position.x, r.end.x), clampf(p.y, r.position.y, r.end.y))
			var dist := p.distance_to(q)
			if dist <= BALL_R and dist < bd:
				bd = dist
				best = c
	return best


func _hit_brick(c: Vector2i) -> void:
	var b: Dictionary = bricks[c]
	if b["hits"] < 0:
		event.emit("brick", {"row": c.y, "col": c.x, "broken": false, "kind": b["kind"]})
		return
	b["hits"] -= 1
	if b["hits"] > 0:
		event.emit("brick", {"row": c.y, "col": c.x, "broken": false, "kind": b["kind"]})
		return
	bricks.erase(c)
	breakable -= 1
	_since_break = 0.0
	score += 50 + 10 * "abcdef".find(b["kind"]) if b["kind"] != "H" else 50 * (1 + stage)
	event.emit("brick", {"row": c.y, "col": c.x, "broken": true, "kind": b["kind"]})
	if b["kind"] != "H" and rng.randf() < 0.14 and capsules.size() < 2 and balls.size() == 1:
		var total := 0
		for w in CAPSULE_WEIGHTS:
			total += w
		var pick := rng.randi_range(0, total - 1)
		var k := 0
		while pick >= CAPSULE_WEIGHTS[k]:
			pick -= CAPSULE_WEIGHTS[k]
			k += 1
		capsules.append({"pos": brick_rect(c).get_center(), "kind": CAPSULE_KINDS[k]})
		event.emit("capsule_drop", {"kind": CAPSULE_KINDS[k]})
	if breakable <= 0:
		phase = Phase.CLEARED
		event.emit("cleared", {})


func _move_capsules() -> void:
	for cp in capsules.duplicate():
		cp["pos"].y += 3.0 * TICK
		if cp["pos"].y > PADDLE_Y - 0.25 and cp["pos"].y < PADDLE_Y + 0.25 and absf(cp["pos"].x - paddle_x) < paddle_w * 0.5 + 0.4:
			capsules.erase(cp)
			_take(cp["kind"])
		elif cp["pos"].y > H:
			capsules.erase(cp)


func _take(k: String) -> void:
	score += 1000
	# a new power ends the old one (catch lets go of held balls)
	if power == "catch" and k != "catch":
		launch()
	paddle_w = 2.0
	power = k
	power_t = 0.0
	match k:
		"wide": paddle_w = 3.0
		"slow":
			power_t = 10.0
			for b in balls:
				b["speed"] = maxf(SPEED0 * 0.7, b["speed"] * 0.7)
		"multi":
			power = ""
			var src: Dictionary = balls[0]
			for ang in [-0.5, 0.5]:
				var v: Vector2 = (src["vel"] if src["vel"] != Vector2.ZERO else Vector2(0, -src["speed"])).rotated(ang)
				balls.append({"pos": src["pos"], "vel": v, "held": -99.0, "speed": src["speed"]})
		"life":
			power = ""
			lives += 1
		"break":
			warp_open = true
	event.emit("capsule", {"kind": k})


func _move_bolts() -> void:
	for bo in bolts.duplicate():
		bo["pos"].y -= 18.0 * TICK
		var c := Vector2i(int(floor(bo["pos"].x)), int(floor((bo["pos"].y - TOP) / 0.5)))
		if bricks.has(c):
			bolts.erase(bo)
			_hit_brick(c)
		elif bo["pos"].y < 0.0:
			bolts.erase(bo)
		else:
			for dr in drones.duplicate():
				if dr["pos"].distance_to(bo["pos"]) < 0.4:
					bolts.erase(bo)
					_pop_drone(dr)
					break


func _move_drones() -> void:
	_next_drone -= TICK
	if _next_drone <= 0.0 and drones.size() < 3:
		_next_drone = rng.randf_range(8.0, 14.0)
		var x: float = GATES[rng.randi_range(0, 1)]
		drones.append({"pos": Vector2(x, 0.4), "vel": Vector2(rng.randf_range(-1, 1), 1.0).normalized() * 1.4, "kind": rng.randi_range(0, 2), "id": _id})
		_id += 1
		event.emit("drone", {"x": x})
	for dr in drones.duplicate():
		var p: Vector2 = dr["pos"] + dr["vel"] * TICK
		var v: Vector2 = dr["vel"]
		if p.x < 0.4 or p.x > W - 0.4:
			v.x = -v.x
		# drift round the bricks, sway down
		var c := Vector2i(int(floor(p.x)), int(floor((p.y - TOP) / 0.5)))
		if bricks.has(c):
			v = Vector2(-v.x, -absf(v.y) * 0.5)
			p = dr["pos"]
		v = (v + Vector2(sin(time * 1.3 + dr["id"]) * 0.02, 0.01)).normalized() * 1.4
		dr["pos"] = p
		dr["vel"] = v
		if p.y > PADDLE_Y - 0.3 and absf(p.x - paddle_x) < paddle_w * 0.5 + 0.3:
			_pop_drone(dr)
		elif p.y > H:
			drones.erase(dr)


func _pop_drone(dr: Dictionary) -> void:
	if drones.has(dr):
		drones.erase(dr)
		score += 100
		event.emit("drone_pop", {"pos": dr["pos"]})
