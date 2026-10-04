class_name FuseEngine
extends RefCounted
## Fuseflight rules (a single-screen leaping collector in the Bomb Jack tradition; our own tuning), 60 Hz ticks.
## The arena is 16 x 12 units, y up, the floor at 0. The sprite runs, leaps high (a held jump goes higher) and, falling,
## glides on a held jump. Platforms are solid all round (a leap under one bumps the head). Collect every firework on the
## stage: after the first, one firework's fuse is lit, always the next in the stage's order; taking the lit one scores
## double and lights the next. At the end, the lit ones taken make a bonus. Enemies drop in from the top: walkers walk
## the platforms and, after a while, take wing as flyers that chase; orbs bounce round the arena. Now and then a
## power star bounces in: take it and every enemy becomes a spark worth points, for a few seconds. Touching an enemy
## costs a life. Bonus letters drift down too: B (bonus), E (extra life).
## Events: "jump", "land", "bump", "take" {i, lit, points}, "lit" {i}, "spawn" {kind}, "wing" {id}, "power", "power_end",
## "eat" {pos, points}, "letter" {kind}, "die" {pos}, "cleared" {bonus, lit}, "game_over", "extra_life".

signal event(kind: String, data: Dictionary)

enum Phase { READY, PLAY, DYING, CLEARED, OVER }
const TICK := 1.0 / 60.0
const W := 16.0
const H := 12.0
const RUN := 5.0
const LEAP := 15.5        ## the leap's take-off speed
const GRAV := 18.0
const CUT := 2.4          ## a jump let go early rises less: gravity times this while still rising
const GLIDE := 1.6        ## the fall speed while gliding
const HALF := 0.3
const TALL := 0.9
const POWER_TIME := 6.0
const WING_TIME := 13.0

var stage: FuseStage
var phase := Phase.READY
var phase_t := 1.5
var time := 0.0
var score := 0
var lives := 3
var taken := PackedByteArray()
var lit := -1                    ## the index of the lit firework (-1 before the first is taken)
var lit_taken := 0
var hero := {}
var move_x := 0.0
var jump_held := false
var jump_pressed := false
var enemies: Array[Dictionary] = []
var power := 0.0
var star := {}                   ## the bouncing power star, or empty
var letters: Array[Dictionary] = []
var rng := RandomNumberGenerator.new()
var _spawn_t := 3.0
var _star_t := 15.0
var _letter_t := 20.0
var _next_id := 0
var _next_life := 30000
var _chain := 0


func _init(st: FuseStage, lives_ := 3, score_ := 0, seed_ := 1) -> void:
	stage = st
	lives = lives_
	score = score_
	rng.seed = seed_ + hash(st.name)
	_next_life = (score / 30000 + 1) * 30000
	taken.resize(st.bombs.size())
	taken.fill(0)
	_reset_hero()


func _reset_hero() -> void:
	hero = {"pos": stage.start, "vel": Vector2.ZERO, "ground": true, "facing": 1, "gliding": false}


## A copy of the whole state, to try moves on (the autopilot looks ahead with it); it sends no events.
func copy() -> FuseEngine:
	var c := FuseEngine.new(stage, lives, score)
	c.phase = phase
	c.phase_t = phase_t
	c.time = time
	c.taken = taken.duplicate()
	c.lit = lit
	c.lit_taken = lit_taken
	c.hero = hero.duplicate()
	c.enemies.assign(enemies.map(func(e): return e.duplicate()))
	c.power = power
	c.star = star.duplicate()
	c.letters.assign(letters.map(func(l): return l.duplicate()))
	c.rng.state = rng.state
	c._spawn_t = _spawn_t
	c._star_t = _star_t
	c._letter_t = _letter_t
	c._next_id = _next_id
	return c


func left() -> int:
	return taken.count(0)


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
					phase_t = 3.0
					event.emit("game_over", {})
				else:
					enemies.clear()
					star = {}
					power = 0.0
					_spawn_t = 2.0
					_reset_hero()
					phase = Phase.READY
					phase_t = 1.0
			return
		Phase.CLEARED, Phase.OVER:
			phase_t -= TICK
			return
	_move_hero()
	jump_pressed = false
	_take_bombs()
	if phase != Phase.PLAY:
		return
	if power > 0.0:
		power -= TICK
		if power <= 0.0:
			event.emit("power_end", {})
	_spawn()
	_move_enemies()
	_move_star()
	_move_letters()
	_touch()


func _solid_at(r: Rect2) -> Rect2:
	for p in stage.platforms:
		if (p as Rect2).intersects(r):
			return p
	return Rect2()


func _move_hero() -> void:
	var h := hero
	var p: Vector2 = h["pos"]
	var v: Vector2 = h["vel"]
	v.x = move_x * RUN
	if move_x != 0.0:
		h["facing"] = int(signf(move_x))
	if jump_pressed and h["ground"]:
		v.y = LEAP
		h["ground"] = false
		event.emit("jump", {})
	var g := GRAV
	if v.y > 0.0 and not jump_held:
		g *= CUT
	v.y -= g * TICK
	h["gliding"] = v.y < 0.0 and jump_held and not h["ground"]
	if h["gliding"]:
		v.y = maxf(v.y, -GLIDE)
	v.y = maxf(v.y, -14.0)
	# move x, then y, against the walls, the floor, the ceiling and the platforms
	var nx := clampf(p.x + v.x * TICK, HALF, W - HALF)
	var body := Rect2(nx - HALF, p.y, HALF * 2.0, TALL)
	var hit := _solid_at(body)
	if hit.has_area():
		nx = p.x
	p.x = nx
	var ny := p.y + v.y * TICK
	var was_ground: bool = h["ground"]
	h["ground"] = false
	if ny <= 0.0:
		ny = 0.0
		h["ground"] = true
	elif ny + TALL >= H:
		ny = H - TALL
		v.y = minf(v.y, 0.0)
	body = Rect2(p.x - HALF, ny, HALF * 2.0, TALL)
	hit = _solid_at(body)
	if hit.has_area():
		if v.y <= 0.0:
			ny = hit.end.y
			h["ground"] = true
		else:
			ny = hit.position.y - TALL
			v.y = 0.0
			event.emit("bump", {})
	if h["ground"]:
		if not was_ground and v.y < -6.0:
			event.emit("land", {})
		v.y = 0.0
	p.y = ny
	h["pos"] = p
	h["vel"] = v


func _take_bombs() -> void:
	var body := Rect2(hero["pos"].x - HALF, hero["pos"].y, HALF * 2.0, TALL)
	for i in stage.bombs.size():
		if taken[i] == 1:
			continue
		var b: Vector2 = stage.bombs[i]
		if body.grow(0.18).has_point(b):
			taken[i] = 1
			var was_lit := i == lit
			var pts := 200 if was_lit else 100
			if power > 0.0:
				pts *= 2
			score += pts
			_extra()
			if was_lit:
				lit_taken += 1
			event.emit("take", {"i": i, "lit": was_lit, "points": pts, "pos": b})
			# the next firework in the stage's order lights up
			lit = -1
			for k in range(1, stage.bombs.size() + 1):
				var j := (i + k) % stage.bombs.size()
				if taken[j] == 0:
					lit = j
					break
			if lit >= 0:
				event.emit("lit", {"i": lit})
			if left() == 0:
				# 200 for each lit one taken, and a big bonus for taking (almost) all of them lit
				var bonus := lit_taken * 200 + (10000 if lit_taken >= stage.bombs.size() - 2 else 0)
				score += bonus
				_extra()
				phase = Phase.CLEARED
				phase_t = 3.0
				event.emit("cleared", {"bonus": bonus, "lit": lit_taken})
				return


func _spawn() -> void:
	_spawn_t -= TICK
	if _spawn_t <= 0.0 and enemies.size() < stage.max_enemies:
		_spawn_t = rng.randf_range(4.0, 7.0)
		var kind := "walker" if rng.randf() < 0.65 else "orb"
		_next_id += 1
		var x := rng.randf_range(2.0, W - 2.0)
		var e := {"id": _next_id, "kind": kind, "pos": Vector2(x, H - 0.6), "vel": Vector2(0, -2.0), "t": 0.0, "ground": false,
			"dir": 1.0 if rng.randf() < 0.5 else -1.0}
		if kind == "orb":
			e["vel"] = Vector2(2.4 * e["dir"], -2.4)
		enemies.append(e)
		event.emit("spawn", {"kind": kind})
	_star_t -= TICK
	if _star_t <= 0.0 and star.is_empty() and power <= 0.0:
		_star_t = rng.randf_range(18.0, 26.0)
		star = {"pos": Vector2(rng.randf_range(2.0, W - 2.0), H - 1.0), "vel": Vector2(2.0, -1.8), "t": 0.0}
	_letter_t -= TICK
	if _letter_t <= 0.0:
		_letter_t = rng.randf_range(25.0, 35.0)
		letters.append({"kind": "E" if rng.randf() < 0.3 else "B", "pos": Vector2(rng.randf_range(2.0, W - 2.0), H - 0.5), "t": 0.0})


func _move_enemies() -> void:
	var me: Vector2 = hero["pos"] + Vector2(0, TALL * 0.5)
	for e in enemies:
		e["t"] += TICK
		var p: Vector2 = e["pos"]
		var v: Vector2 = e["vel"]
		match e["kind"]:
			"walker":
				if e["t"] > WING_TIME:
					e["kind"] = "flyer"
					event.emit("wing", {"id": e["id"]})
					continue
				if not e["ground"]:
					v = Vector2(0, maxf(v.y - GRAV * 0.4 * TICK, -5.0))
				else:
					v = Vector2(e["dir"] * 2.0, 0)
				var np := p + v * TICK
				var feet := Rect2(np.x - 0.25, np.y - 0.02, 0.5, 0.02)
				var under := _solid_at(feet)
				if np.y <= 0.0:
					np.y = 0.0
					e["ground"] = true
				elif under.has_area() and v.y <= 0.0:
					np.y = under.end.y
					e["ground"] = true
				elif e["ground"]:
					# the edge of its ledge (or the arena's wall): it turns back
					e["dir"] = -e["dir"]
					np.x = p.x
				if np.x < 0.4 or np.x > W - 0.4:
					e["dir"] = -e["dir"]
					np.x = clampf(np.x, 0.4, W - 0.4)
				p = np
			"flyer":
				# it homes on the sprite, wavering
				var to := (me - p).normalized()
				var wob := Vector2(-to.y, to.x) * sin(e["t"] * 2.3 + e["id"]) * 0.9
				v = v.lerp((to + wob) * (1.6 + 0.15 * stage.speed), TICK * 1.2)
				p += v * TICK
			"orb":
				p += v * TICK
				if p.x < 0.3 or p.x > W - 0.3:
					v.x = -v.x
				if p.y < 0.3 or p.y > H - 0.3:
					v.y = -v.y
				var hit := _solid_at(Rect2(p - Vector2(0.25, 0.25), Vector2(0.5, 0.5)))
				if hit.has_area():
					v.y = -v.y
					p += v * TICK * 2.0
		e["pos"] = p.clamp(Vector2(0.3, 0.0), Vector2(W - 0.3, H - 0.3))
		e["vel"] = v


func _move_star() -> void:
	if star.is_empty():
		return
	star["t"] += TICK
	var p: Vector2 = star["pos"]
	var v: Vector2 = star["vel"]
	p += v * TICK
	if p.x < 0.4 or p.x > W - 0.4:
		v.x = -v.x
	if p.y < 0.4 or p.y > H - 0.4:
		v.y = -v.y
	star["pos"] = p
	star["vel"] = v
	if star["t"] > 12.0:
		star = {}


func _move_letters() -> void:
	for l in letters:
		l["t"] += TICK
		var p: Vector2 = l["pos"]
		p.y = maxf(0.4, p.y - 1.2 * TICK)
		p.x += sin(l["t"] * 2.0) * 0.6 * TICK
		l["pos"] = p
	letters = letters.filter(func(l): return l["t"] < 14.0)


func _touch() -> void:
	var body := Rect2(hero["pos"].x - HALF, hero["pos"].y, HALF * 2.0, TALL)
	if not star.is_empty() and body.grow(0.25).has_point(star["pos"]):
		star = {}
		power = POWER_TIME
		_chain = 0
		score += 500
		_extra()
		event.emit("power", {})
	for l in letters.duplicate():
		if body.grow(0.25).has_point(l["pos"]):
			letters.erase(l)
			if l["kind"] == "E":
				lives += 1
				event.emit("extra_life", {})
			else:
				score += 2000
				_extra()
			event.emit("letter", {"kind": l["kind"]})
	for e in enemies.duplicate():
		var ep: Vector2 = e["pos"]
		if body.grow(-0.05).intersects(Rect2(ep - Vector2(0.28, 0.0 if e["kind"] == "walker" else 0.28), Vector2(0.56, 0.56))):
			if power > 0.0:
				_chain += 1
				var pts: int = mini(100 * int(pow(2, _chain - 1)), 3200)
				score += pts
				_extra()
				enemies.erase(e)
				event.emit("eat", {"pos": ep, "points": pts})
			else:
				_die()
				return


func _extra() -> void:
	if score >= _next_life:
		_next_life += 30000
		lives += 1
		event.emit("extra_life", {})


func _die() -> void:
	lives -= 1
	phase = Phase.DYING
	phase_t = 2.0
	event.emit("die", {"pos": hero["pos"]})
