class_name HenEngine
extends RefCounted
## Henhouse Heist rules (a ladders-and-eggs platformer in the Chuckie Egg tradition; our own tuning), 60 Hz ticks.
## Tiles, y down; the farmhand's (x, y) is the middle of its feet. It walks, climbs ladders (it can grab one in mid
## jump), jumps a fixed arc, drops off edges, and rides the lifts (the top of the shaft is fatal). Collect every egg to
## finish; grain stops the clock for a while (hens stop to eat it too). Hens wander the platforms and ladders; on
## goose stages the goose leaves its cage and flies after the farmhand, through everything. Out of time is a life.
## Events: "egg" {cell, left}, "grain" {cell}, "jump", "land", "step", "die" {how, pos}, "cleared" {bonus}, "goose_free",
## "cluck" {id}, "peck" {id}, "game_over", "extra_life", "time_low".

signal event(kind: String, data: Dictionary)

enum Phase { READY, PLAY, DYING, CLEARED, OVER }
const TICK := 1.0 / 60.0
const W := 32
const H := 26
const WALK := 4.2
const CLIMB := 3.4
const JUMP_V := -10.0
const GRAV := 30.0
const HALF := 0.3
const LIFT_SPEED := 2.2
const LIFT_TOP := 7.0      ## the lifts turn round below the top bridge

var level: HenLevel
var stage := 0
var rng := RandomNumberGenerator.new()
var phase := Phase.READY
var phase_t := 1.5
var time := 0.0
var score := 0
var lives := 5
var clock := 90.0          ## the time bonus, counting down
var freeze := 0.0          ## grain stops the clock for this long
var eggs := {}             ## cell -> true (still there)
var grain := {}
var hero := {}
var move_x := 0.0
var up := false
var down := false
var jump_pressed := false
var hens: Array[Dictionary] = []
var lifts: Array[float] = []   ## the top of each lift (y)
var goose := {}
var _next_life := 10000
var _step_t := 0.0


func _init(lv: HenLevel, stage_ := 0, seed_ := 1, lives_ := 5, score_ := 0) -> void:
	level = lv
	stage = stage_
	rng.seed = seed_
	lives = lives_
	score = score_
	_next_life = (score / 10000 + 1) * 10000
	clock = lv.time_limit
	for c in lv.eggs:
		eggs[c] = true
	for c in lv.grain:
		grain[c] = true
	for i in mini(lv.hen_count + stage / 4, lv.hens.size()):
		var c: Vector2i = lv.hens[i]
		hens.append({"id": i, "pos": Vector2(c.x + 0.5, c.y + 1.0), "dir": Vector2i(1 if i % 2 == 0 else -1, 0), "climb": false,
			"peck": 0.0, "speed": 2.2 + minf(stage, 8) * 0.12})
	if lv.lift_col >= 0:
		lifts = [6.0, 6.0 + H * 0.5]
	_reset_hero()


func _reset_hero() -> void:
	hero = {"pos": Vector2(level.start.x + 0.5, level.start.y + 1.0), "vel": Vector2.ZERO, "state": "walk", "facing": 1, "lift": -1}


func solid(x: int, y: int) -> bool:
	if x < 0 or x >= W:
		return true
	if y < 0 or y >= H:
		return false
	return level.solid[y * W + x] == 1


func ladder(x: int, y: int) -> bool:
	if x < 0 or x >= W or y < 0 or y >= H:
		return false
	return level.ladder[y * W + x] == 1


## The lift under a point, if any (index), when its top is within reach of the feet.
func lift_under(p: Vector2, reach := 0.2) -> int:
	if level.lift_col < 0 or absf(p.x - (level.lift_col + 1.0)) > 1.1:
		return -1
	for i in lifts.size():
		if absf(p.y - lifts[i]) <= reach:
			return i
	return -1


## Can one stand at (x, y) (feet on the top of the row y)?
func standable(x: float, y: float) -> bool:
	var row := int(round(y))
	if absf(y - row) > 0.05:
		return false
	return solid(int(floor(x)), row) or (ladder(int(floor(x)), row) and not ladder(int(floor(x)), row - 1))


# ------------------------------------------------------------------ the tick

func tick() -> void:
	time += TICK
	match phase:
		Phase.READY:
			phase_t -= TICK
			if phase_t <= 0.0:
				phase = Phase.PLAY
			jump_pressed = false
			return
		Phase.DYING:
			phase_t -= TICK
			if phase_t <= 0.0:
				if lives <= 0:
					phase = Phase.OVER
					event.emit("game_over", {})
				else:
					_reset_hero()
					clock = maxf(clock, 30.0)
					goose = {}
					phase = Phase.READY
					phase_t = 1.0
			return
		Phase.CLEARED, Phase.OVER:
			phase_t -= TICK
			return
	if freeze > 0.0:
		freeze -= TICK
	else:
		clock -= TICK
		if clock < 15.0 and clock + TICK >= 15.0:
			event.emit("time_low", {})
		if clock <= 0.0:
			_die("time")
			return
	_move_lifts()
	_move_hero()
	jump_pressed = false
	if phase != Phase.PLAY:
		return
	_collect()
	_move_hens()
	_move_goose()
	_touch()


func _move_lifts() -> void:
	for i in lifts.size():
		lifts[i] -= LIFT_SPEED * TICK
		if lifts[i] < LIFT_TOP:
			lifts[i] += H - LIFT_TOP


func _move_hero() -> void:
	var h := hero
	var p: Vector2 = h["pos"]
	var v: Vector2 = h["vel"]
	var st: String = h["state"]
	var tx := int(floor(p.x))
	if move_x != 0.0 and st != "climb":
		h["facing"] = int(signf(move_x))
	# grab a ladder (walking, or in the air)
	if st != "climb" and (up or down):
		var here := ladder(tx, int(floor(p.y - 0.5)))
		var below := ladder(tx, int(round(p.y))) and st == "walk"
		if (up and here) or (down and (below or (here and st != "walk"))):
			st = "climb"
			p.x = tx + 0.5
			v = Vector2.ZERO
			h["lift"] = -1
	match st:
		"climb":
			var dy := (-1.0 if up else 0.0) + (1.0 if down else 0.0)
			var np := p + Vector2(0, dy * CLIMB * TICK)
			var on := ladder(tx, int(floor(np.y - 0.05))) or ladder(tx, int(floor(np.y + 0.05)))
			if not on or (dy > 0.0 and solid(tx, int(floor(np.y))) and not ladder(tx, int(floor(np.y)))):
				# off the end of the ladder: stand at the nearest row
				np.y = round(np.y)
				st = "walk" if standable(np.x, np.y) else "fall"
			elif move_x != 0.0 and standable(p.x, round(p.y)) and absf(p.y - round(p.y)) < 0.15:
				np.y = round(p.y)
				st = "walk"
			p = np
			if dy != 0.0:
				_steps(0.3)
		"walk":
			var li: int = h["lift"]
			if li >= 0:
				p.y = lifts[li]
				if lifts[li] < LIFT_TOP + 1.2:  # squashed against the top of the shaft
					_die("lift")
					return
			if jump_pressed:
				st = "jump"
				v = Vector2(move_x * WALK, JUMP_V)
				h["lift"] = -1
				event.emit("jump", {})
			else:
				var nx := p.x + move_x * WALK * TICK
				nx = clampf(nx, HALF, W - HALF)
				p.x = nx
				if move_x != 0.0:
					_steps(0.25)
				if li >= 0:
					if lift_under(p, 0.3) != li:
						h["lift"] = -1
						st = "fall"
				elif not standable(p.x, p.y) and not standable(p.x - HALF * 0.9, p.y) and not standable(p.x + HALF * 0.9, p.y):
					st = "fall"
					v = Vector2.ZERO
		"jump", "fall":
			v.y = minf(v.y + GRAV * TICK, 14.0)
			var np := p + v * TICK
			if np.x < HALF or np.x > W - HALF:
				v.x = -v.x * 0.5
				np.x = clampf(np.x, HALF, W - HALF)
			if v.y > 0.0:
				# land on a row crossed on the way down
				var r0 := int(floor(p.y - 0.001)) + 1
				var r1 := int(floor(np.y))
				for r in range(r0, r1 + 1):
					if standable(np.x, float(r)):
						np.y = float(r)
						st = "walk"
						v = Vector2.ZERO
						event.emit("land", {})
						break
				var li := lift_under(np, 0.4)
				if st != "walk" and li >= 0 and np.y >= lifts[li] - 0.1:
					np.y = lifts[li]
					st = "walk"
					h["lift"] = li
					v = Vector2.ZERO
			p = np
			if p.y > H + 1.0:
				_die("fall")
				return
	if st == "walk" and h["lift"] < 0:
		var li := lift_under(p, 0.25)
		if li >= 0 and not standable(p.x, p.y):
			h["lift"] = li
	h["pos"] = p
	h["vel"] = v
	h["state"] = st


func _steps(every: float) -> void:
	_step_t -= TICK
	if _step_t <= 0.0:
		_step_t = every
		event.emit("step", {})


func _collect() -> void:
	var p: Vector2 = hero["pos"]
	for c in eggs.keys():
		if absf(p.x - (c.x + 0.5)) < 0.6 and p.y > c.y and p.y < c.y + 2.2:
			eggs.erase(c)
			score += 100
			_extra()
			event.emit("egg", {"cell": c, "left": eggs.size()})
	for c in grain.keys():
		if absf(p.x - (c.x + 0.5)) < 0.6 and p.y > c.y and p.y < c.y + 2.2:
			grain.erase(c)
			score += 50
			freeze = 6.0
			_extra()
			event.emit("grain", {"cell": c})
	if eggs.is_empty():
		var bonus := int(clock) * 10
		score += bonus
		phase = Phase.CLEARED
		phase_t = 3.0
		event.emit("cleared", {"bonus": bonus})


func _extra() -> void:
	if score >= _next_life:
		_next_life += 10000
		lives += 1
		event.emit("extra_life", {})


# ------------------------------------------------------------------ hens and the goose

func _move_hens() -> void:
	for hn in hens:
		if hn["peck"] > 0.0:
			hn["peck"] -= TICK
			continue
		var p: Vector2 = hn["pos"]
		var d: Vector2i = hn["dir"]
		var step: float = hn["speed"] * TICK
		var target := p + Vector2(d) * step
		# at a cell centre (x) or a row (y): decide
		var cx: float = floor(p.x) + 0.5
		var crossing: bool = (d.x != 0 and signf(cx - p.x) == d.x and absf(cx - p.x) <= step) or (d.y != 0 and absf(round(p.y) - p.y) <= step and signf(round(p.y) - p.y) == d.y)
		if crossing or d == Vector2i.ZERO:
			var at := Vector2(cx if d.x != 0 else p.x, round(p.y) if d.y != 0 else p.y)
			var c := Vector2i(int(floor(at.x)), int(round(at.y)))
			var opts: Array[Vector2i] = []
			if standable(at.x, at.y):
				for dx in [-1, 1]:
					if standable(at.x + dx, at.y):
						opts.append(Vector2i(dx, 0))
			if ladder(c.x, c.y - 1):
				opts.append(Vector2i(0, -1))
			if ladder(c.x, c.y) and c.y < H - 1:
				opts.append(Vector2i(0, 1))
			# eat grain here
			var g := Vector2i(c.x, c.y - 1)
			if grain.has(g):
				grain.erase(g)
				hn["peck"] = 1.5
				event.emit("peck", {"id": hn["id"]})
			if not opts.is_empty():
				var keep := opts.has(d) and rng.randf() < (0.8 if d.x != 0 else 0.6)
				var back := -d
				if not keep:
					var choice := opts.filter(func(o): return o != back)
					if choice.is_empty():
						choice = opts
					d = choice[rng.randi_range(0, choice.size() - 1)]
			else:
				d = -d
			hn["dir"] = d
			p = at
			target = p + Vector2(d) * step
			if rng.randf() < 0.05:
				event.emit("cluck", {"id": hn["id"]})
		hn["climb"] = d.y != 0
		hn["pos"] = target


func _move_goose() -> void:
	if not level.goose:
		return
	if goose.is_empty():
		if time > 3.0 and level.cage.x >= 0:
			goose = {"pos": Vector2(level.cage.x + 1.0, level.cage.y + 1.0), "vel": Vector2.ZERO}
			event.emit("goose_free", {})
		return
	var to: Vector2 = (hero["pos"] + Vector2(0, -1.0)) - goose["pos"]
	var v: Vector2 = goose["vel"]
	v += to.normalized() * 2.0 * TICK
	var top := 1.6 + minf(stage, 6) * 0.1
	if v.length() > top:
		v = v.normalized() * top
	goose["vel"] = v
	goose["pos"] += v * TICK


func _touch() -> void:
	var p: Vector2 = hero["pos"]
	var body := Rect2(p.x - HALF, p.y - 1.8, HALF * 2.0, 1.8)
	for hn in hens:
		var hp: Vector2 = hn["pos"]
		if body.intersects(Rect2(hp.x - 0.35, hp.y - 0.9, 0.7, 0.9)):
			_die("hen")
			return
	if not goose.is_empty() and (goose["pos"] as Vector2).distance_to(p + Vector2(0, -0.9)) < 1.1:
		_die("goose")


func _die(how: String) -> void:
	lives -= 1
	phase = Phase.DYING
	phase_t = 2.0
	event.emit("die", {"how": how, "pos": hero["pos"]})
