class_name PopEngine
extends RefCounted
## Pop Voyage rules (balloon-splitting in the Pang tradition; our own tuning), 60 Hz ticks. The arena is 16 wide and
## 10 high, y up, the floor at 0. Balloons come in four sizes; each bounces to its own height and drifts sideways at a
## steady speed. The traveller walks the floor and fires a harpoon wire straight up: a balloon it touches splits into
## two of the next size down (the smallest just pops). Blocks stand in the air: balloons bounce off them, the wire stops
## under them, and cracked ones break. Popped balloons sometimes drop an item: double wire, sticky wire (it stays up a
## while), a shield, a clock (balloons freeze) or a charge (every balloon splits down to the smallest).
## Clear the stage before the clock runs out; a touch costs a life and restarts the stage.
## Events: "fire", "pop" {size, pos, left}, "split" {size, pos}, "block" {pos}, "item" {kind, pos}, "take" {kind},
## "shield_lost", "die" {pos}, "timeout", "cleared" {bonus}, "game_over", "extra_life".

signal event(kind: String, data: Dictionary)

enum Phase { READY, PLAY, DYING, CLEARED, OVER }
const TICK := 1.0 / 60.0
const W := 16.0
const H := 10.0
const G := 15.0
const RADIUS := [0.24, 0.44, 0.72, 1.05]
const BOUNCE := [2.4, 3.6, 5.0, 6.4]    ## how high each size bounces above what it lands on
const SPEED_X := 2.6
const WALK := 5.5
const WIRE_SPEED := 13.0
const HALF := 0.32
const TALL := 1.3
const STICKY_TIME := 2.5
const ITEM_KINDS := ["double", "sticky", "shield", "clock", "charge"]

var stage: PopStage
var phase := Phase.READY
var phase_t := 1.4
var time := 0.0
var clock := 90.0
var score := 0
var lives := 3
var balls: Array[Dictionary] = []
var blocks: Array[Dictionary] = []
var items: Array[Dictionary] = []
var wires: Array[Dictionary] = []      ## {x, tip, stuck}
var hero := {}
var move_x := 0.0
var fire_pressed := false
var weapon := "wire"                   ## wire, double, sticky
var shield := false
var frozen := 0.0
var rng := RandomNumberGenerator.new()
var _next_life := 20000
var _combo := 0
var _combo_t := 0.0


func _init(st: PopStage, lives_ := 3, score_ := 0) -> void:
	stage = st
	lives = lives_
	score = score_
	_next_life = (score / 20000 + 1) * 20000
	_reset()


func _reset() -> void:
	rng.seed = hash(stage.name) + lives
	clock = stage.time
	balls.clear()
	for b in stage.balls:
		var s: int = b["size"]
		balls.append({"size": s, "pos": b["pos"], "vel": Vector2(SPEED_X * b["dir"], 0.0)})
	blocks.clear()
	for b in stage.blocks:
		blocks.append(b.duplicate())
	items.clear()
	wires.clear()
	weapon = "wire"
	shield = false
	frozen = 0.0
	hero = {"x": W * 0.5, "facing": 1, "vel": 0.0}


# ------------------------------------------------------------------ the tick

func tick() -> void:
	time += TICK
	match phase:
		Phase.READY:
			phase_t -= TICK
			if phase_t <= 0.0:
				phase = Phase.PLAY
			fire_pressed = false
			return
		Phase.DYING:
			phase_t -= TICK
			if phase_t <= 0.0:
				if lives <= 0:
					phase = Phase.OVER
					phase_t = 3.0
					event.emit("game_over", {})
				else:
					_reset()
					phase = Phase.READY
					phase_t = 1.2
			return
		Phase.CLEARED:
			if clock > 0.0:
				var d := minf(clock, TICK * 40.0)
				clock -= d
				score += int(round(d * 20.0))
				_extra()
			phase_t -= TICK
			return
		Phase.OVER:
			phase_t -= TICK
			return
	clock -= TICK
	if clock <= 0.0:
		clock = 0.0
		event.emit("timeout", {})
		_die()
		return
	_combo_t -= TICK
	if _combo_t <= 0.0:
		_combo = 0
	_move_hero()
	_move_wires()
	if frozen > 0.0:
		frozen -= TICK
	else:
		for b in balls:
			_move_ball(b)
	_move_items()
	_hit_balls()
	if phase == Phase.PLAY:
		_touch()
	fire_pressed = false


func _move_hero() -> void:
	var h := hero
	var x: float = h["x"] + move_x * WALK * TICK
	x = clampf(x, HALF, W - HALF)
	# blocks standing on the floor stop him
	for bl in blocks:
		var r: Rect2 = bl["rect"]
		if r.position.y < TALL and x + HALF > r.position.x and x - HALF < r.end.x:
			x = h["x"]
	h["vel"] = (x - h["x"]) / TICK
	h["x"] = x
	if move_x != 0.0:
		h["facing"] = int(signf(move_x))
	if fire_pressed:
		var limit := 2 if weapon == "double" else 1
		if wires.filter(func(w): return not w["stuck"]).size() < limit and wires.size() < limit + 1:
			wires.append({"x": h["x"], "tip": TALL * 0.6, "stuck": false, "stuck_t": 0.0})
			event.emit("fire", {})


func _move_wires() -> void:
	for w in wires:
		if w["stuck"]:
			w["stuck_t"] -= TICK
			if w["stuck_t"] <= 0.0:
				w["done"] = true
			continue
		w["tip"] += WIRE_SPEED * TICK
		var top := H
		for bl in blocks:
			var r: Rect2 = bl["rect"]
			if w["x"] > r.position.x and w["x"] < r.end.x and r.position.y >= w["tip"] - WIRE_SPEED * TICK - 0.01:
				top = minf(top, r.position.y)
		if w["tip"] >= top:
			w["tip"] = top
			# a cracked block breaks
			for bl in blocks:
				var r: Rect2 = bl["rect"]
				if bl["breakable"] and absf(r.position.y - top) < 0.01 and w["x"] > r.position.x and w["x"] < r.end.x:
					bl["gone"] = true
					score += 200
					event.emit("block", {"pos": r.get_center()})
			if weapon == "sticky":
				w["stuck"] = true
				w["stuck_t"] = STICKY_TIME
			else:
				w["done"] = true
	blocks = blocks.filter(func(b): return not b.has("gone"))
	wires = wires.filter(func(w): return not w.has("done"))


func _move_ball(b: Dictionary) -> void:
	var s: int = b["size"]
	var r: float = RADIUS[s]
	var v: Vector2 = b["vel"]
	var p: Vector2 = b["pos"]
	v.y -= G * TICK
	p += v * TICK
	if p.x - r < 0.0:
		p.x = r
		v.x = absf(v.x)
	elif p.x + r > W:
		p.x = W - r
		v.x = -absf(v.x)
	if p.y + r > H:
		p.y = H - r
		v.y = -absf(v.y)
	if p.y - r < 0.0:
		p.y = r
		v.y = sqrt(2.0 * G * BOUNCE[s])
	for bl in blocks:
		var rect: Rect2 = bl["rect"]
		var q := Vector2(clampf(p.x, rect.position.x, rect.end.x), clampf(p.y, rect.position.y, rect.end.y))
		var d := p - q
		if d.length_squared() < r * r and d.length_squared() > 0.000001:
			var n := d.normalized()
			p = q + n * r
			if absf(n.y) > absf(n.x):
				if n.y > 0.0:
					v.y = sqrt(2.0 * G * BOUNCE[s]) * 0.85  # bounces off the top of a block
				else:
					v.y = -absf(v.y)
			else:
				v.x = absf(v.x) * signf(n.x)
	b["pos"] = p
	b["vel"] = v


func _move_items() -> void:
	for it in items:
		it["t"] += TICK
		var p: Vector2 = it["pos"]
		if p.y > 0.3:
			p.y = maxf(0.3, p.y - 5.0 * TICK)
			it["pos"] = p
		if it["t"] > 7.0:
			it["gone"] = true
			continue
		if absf(p.x - hero["x"]) < HALF + 0.35 and p.y < TALL:
			it["gone"] = true
			_take(it["kind"])
	items = items.filter(func(i): return not i.has("gone"))


func _take(kind: String) -> void:
	score += 100
	event.emit("take", {"kind": kind})
	match kind:
		"double", "sticky":
			weapon = kind
		"shield":
			shield = true
		"clock":
			frozen = 5.0
		"charge":
			var out: Array[Dictionary] = []
			for b in balls:
				out.append_array(_shatter(b))
			balls = out
			_check_clear()


## A balloon broken all the way down to the smallest ones (the charge).
func _shatter(b: Dictionary) -> Array[Dictionary]:
	if b["size"] == 0:
		return [b]
	var out: Array[Dictionary] = []
	for kid in _split(b):
		out.append_array(_shatter(kid))
	return out


func _split(b: Dictionary) -> Array[Dictionary]:
	var s: int = b["size"] - 1
	var p: Vector2 = b["pos"]
	event.emit("split", {"size": b["size"], "pos": p})
	var up := sqrt(2.0 * G * 1.4)
	return [{"size": s, "pos": p + Vector2(-0.05, 0), "vel": Vector2(-SPEED_X, up)},
		{"size": s, "pos": p + Vector2(0.05, 0), "vel": Vector2(SPEED_X, up)}]


func _hit_balls() -> void:
	for w in wires:
		for i in balls.size():
			var b: Dictionary = balls[i]
			var r: float = RADIUS[b["size"]]
			var p: Vector2 = b["pos"]
			if absf(p.x - w["x"]) < r and p.y - r < w["tip"]:
				w["done"] = true
				balls.remove_at(i)
				_combo += 1
				_combo_t = 1.0
				score += [100, 70, 50, 30][b["size"]] * _combo  # the smaller the balloon, the more it is worth
				_extra()
				if b["size"] > 0:
					balls.append_array(_split(b))
				else:
					event.emit("pop", {"size": 0, "pos": p, "left": balls.size()})
				if rng.randf() < 0.14:
					var kind: String = ITEM_KINDS[rng.randi() % ITEM_KINDS.size()]
					items.append({"kind": kind, "pos": p, "t": 0.0})
					event.emit("item", {"kind": kind, "pos": p})
				break
	wires = wires.filter(func(w): return not w.has("done"))
	_check_clear()


func _check_clear() -> void:
	if balls.is_empty() and phase == Phase.PLAY:
		phase = Phase.CLEARED
		phase_t = 3.5
		var bonus := int(clock) * 20
		wires.clear()
		event.emit("cleared", {"bonus": bonus})


func _touch() -> void:
	var body := Rect2(hero["x"] - HALF + 0.08, 0.0, (HALF - 0.08) * 2.0, TALL - 0.1)
	for b in balls:
		var r: float = RADIUS[b["size"]] * 0.9
		var p: Vector2 = b["pos"]
		var q := Vector2(clampf(p.x, body.position.x, body.end.x), clampf(p.y, body.position.y, body.end.y))
		if p.distance_squared_to(q) < r * r:
			if shield:
				shield = false
				event.emit("shield_lost", {})
				# the balloon is knocked away from him
				b["vel"] = Vector2(SPEED_X * signf(p.x - hero["x"] + 0.001), absf(b["vel"].y) + 3.0)
				return
			_die()
			return


func _extra() -> void:
	if score >= _next_life:
		_next_life += 20000
		lives += 1
		event.emit("extra_life", {})


func _die() -> void:
	lives -= 1
	phase = Phase.DYING
	phase_t = 2.2
	wires.clear()
	event.emit("die", {"pos": Vector2(hero["x"], 0.6)})
