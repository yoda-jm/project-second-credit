class_name TumbleEngine
extends RefCounted
## Tumbletop rules (a pyramid-hopping game in the Q*bert tradition; our own tuning), 60 Hz ticks.
## The pyramid has 7 rows of cubes; cube (r, c) with 0 <= c <= r. Four hops: "ur" (r-1, c), "ul" (r-1, c-1),
## "dr" (r+1, c+1), "dl" (r+1, c). Landing on a cube steps its top towards the target colour (the level's rule says
## how many steps, and whether stepping on a finished cube undoes it). Hop off the edge and you fall, unless a
## cloud-disc floats there: it carries you back to the top, and a serpent close behind follows you off the edge.
## Enemies drop in from above: red balls bounce down and off the bottom; a green ball freezes everything for a while;
## a purple ball hatches into the serpent, who chases; imps bounce down undoing colours (catch them for points).
## Events: "hop" {who}, "land" {who, cell}, "paint" {cell, state, done}, "undo" {cell}, "fall" {who}, "disc" {side, row},
## "ride_end", "spawn" {kind}, "hatch", "lure", "freeze", "catch", "die" {how, cell}, "cleared" {bonus}, "game_over",
## "extra_life".

signal event(kind: String, data: Dictionary)

enum Phase { READY, PLAY, RIDE, DYING, CLEARED, OVER }
const TICK := 1.0 / 60.0
const ROWS := 7
const HOP := 0.32            ## seconds a hop takes
const FALL_TIME := 1.4
const RIDE_TIME := 2.2
const FREEZE_TIME := 4.0
const DIRS := {"ur": Vector2i(-1, 0), "ul": Vector2i(-1, -1), "dr": Vector2i(1, 1), "dl": Vector2i(1, 0)}
## per level: steps to reach the target, and whether hopping on a finished cube undoes a step
const RULES := [
	{"steps": 1, "undo": false},
	{"steps": 2, "undo": false},
	{"steps": 1, "undo": true},
	{"steps": 2, "undo": true},
]
const ROUNDS := 4

var level := 0               ## 0-based
var round := 0               ## 0-based within the level
var rule: Dictionary
var phase := Phase.READY
var phase_t := 1.2
var time := 0.0
var round_time := 0.0
var score := 0
var lives := 3
var tiles := PackedByteArray()   ## the step each cube has reached (0 = start)
var discs: Array[Dictionary] = []  ## {side: -1 left / 1 right, row, used}
var hero := {}
var enemies: Array[Dictionary] = []
var want := ""               ## the hop the player (or the bot) asks for
var frozen := 0.0
var rng := RandomNumberGenerator.new()
var _spawn_t := 0.0
var _next_life := 8000
var _ride := {}


func _init(level_ := 0, round_ := 0, lives_ := 3, score_ := 0) -> void:
	level = level_
	round = round_
	lives = lives_
	score = score_
	_next_life = (score / 8000 + 1) * 8000
	rule = RULES[level % RULES.size()]
	rng.seed = 1000 + level * 17 + round * 5
	tiles.resize(cell_count())
	tiles.fill(0)
	# two discs, on rows that change with the round; later levels float them lower (harder to reach in a hurry)
	var rows: Array = [[3, 4], [4, 2], [2, 5], [5, 3]][round % 4]
	discs = [{"side": -1, "row": rows[0], "used": false}, {"side": 1, "row": rows[1], "used": false}]
	_reset_positions()


static func cell_count() -> int:
	return ROWS * (ROWS + 1) / 2


static func index(c: Vector2i) -> int:
	return c.x * (c.x + 1) / 2 + c.y


static func on_pyramid(c: Vector2i) -> bool:
	return c.x >= 0 and c.x < ROWS and c.y >= 0 and c.y <= c.x


static func cells() -> Array[Vector2i]:
	var out: Array[Vector2i] = []
	for r in ROWS:
		for c in r + 1:
			out.append(Vector2i(r, c))
	return out


## Cube coordinates in 3D: a staircase of unit cubes, the top at the origin (x = c, y = -r, z = r - c).
static func cube3(c: Vector2i) -> Vector3:
	return Vector3(c.y, -c.x, c.x - c.y)


## The disc hovering off the edge that a hop from a cell in a direction reaches (or -1).
func disc_at(c: Vector2i) -> int:
	for i in discs.size():
		var d: Dictionary = discs[i]
		if d["used"]:
			continue
		if d["side"] < 0 and c == Vector2i(d["row"], -1):
			return i
		if d["side"] > 0 and c == Vector2i(d["row"], d["row"] + 1):
			return i
	return -1


func target() -> int:
	return rule["steps"]


func done(c: Vector2i) -> bool:
	return tiles[index(c)] >= target()


func remaining() -> int:
	var n := 0
	for i in tiles.size():
		if tiles[i] < target():
			n += 1
	return n


func _reset_positions() -> void:
	hero = {"at": Vector2i(0, 0), "to": Vector2i(0, 0), "t": 1.0, "dir": "dl", "state": "stand", "fall_t": 0.0}
	enemies.clear()
	frozen = 0.0
	_spawn_t = 2.2


## Where an actor is for collisions: the cell it left until half-way through the hop, then the one it lands on.
static func occupied(a: Dictionary) -> Vector2i:
	return a["from_cell"] if a.has("from_cell") and a["t"] < 0.5 else a["to"]


func hero_cell() -> Vector2i:
	return hero["at"] if hero["t"] < 0.5 else hero["to"]


# ------------------------------------------------------------------ the tick

func tick() -> void:
	time += TICK
	match phase:
		Phase.READY:
			phase_t -= TICK
			if phase_t <= 0.0:
				phase = Phase.PLAY
			want = ""
			return
		Phase.DYING:
			phase_t -= TICK
			if phase_t <= 0.0:
				if lives <= 0:
					phase = Phase.OVER
					phase_t = 3.0
					event.emit("game_over", {})
				else:
					var back: Vector2i = hero["to"] if on_pyramid(hero["to"]) else Vector2i(0, 0)
					enemies.clear()
					frozen = 0.0
					_spawn_t = 2.0
					hero = {"at": back, "to": back, "t": 1.0, "dir": hero["dir"], "state": "stand", "fall_t": 0.0}
					phase = Phase.READY
					phase_t = 0.8
			return
		Phase.CLEARED:
			phase_t -= TICK
			return
		Phase.OVER:
			phase_t -= TICK
			return
		Phase.RIDE:
			_tick_ride()
			return
	round_time += TICK
	_tick_hero()
	if phase != Phase.PLAY:
		return
	if frozen > 0.0:
		frozen -= TICK
	else:
		_tick_enemies()
		_spawn()
	_collide()
	enemies = enemies.filter(func(e): return not e.has("gone"))
	want = ""


func _tick_hero() -> void:
	var h := hero
	if h["state"] == "fall":
		h["fall_t"] += TICK
		if h["fall_t"] >= FALL_TIME:
			_die("fall")
		return
	if h["t"] < 1.0:
		h["t"] = minf(1.0, h["t"] + TICK / HOP)
		if h["t"] >= 1.0:
			_land_hero()
		return
	if want == "" or not DIRS.has(want):
		return
	var to: Vector2i = h["to"] + DIRS[want]
	h["at"] = h["to"]
	h["to"] = to
	h["t"] = 0.0
	h["dir"] = want
	event.emit("hop", {"who": "hero"})


func _land_hero() -> void:
	var h := hero
	var c: Vector2i = h["to"]
	if not on_pyramid(c):
		var di := disc_at(c)
		if di >= 0:
			_start_ride(di)
			return
		h["state"] = "fall"
		h["fall_t"] = 0.0
		event.emit("fall", {"who": "hero"})
		return
	h["at"] = c
	event.emit("land", {"who": "hero", "cell": c})
	_paint(c)


func _paint(c: Vector2i) -> void:
	var i := index(c)
	var s := tiles[i]
	if s < target():
		tiles[i] = s + 1
		score += 25
		_extra()
		event.emit("paint", {"cell": c, "state": s + 1, "done": s + 1 >= target()})
		if remaining() == 0:
			_clear()
	elif rule["undo"]:
		tiles[i] = s - 1
		event.emit("undo", {"cell": c})


func _clear() -> void:
	phase = Phase.CLEARED
	phase_t = 3.0
	var bonus := 1000 + 250 * (level * ROUNDS + round)
	score += bonus
	_extra()
	enemies.clear()
	event.emit("cleared", {"bonus": bonus})


func _start_ride(di: int) -> void:
	var d: Dictionary = discs[di]
	d["used"] = true
	phase = Phase.RIDE
	phase_t = RIDE_TIME
	_ride = {"disc": di, "from": hero["to"]}
	hero["state"] = "ride"
	event.emit("disc", {"side": d["side"], "row": d["row"]})
	# a serpent close behind follows him off the edge
	for e in enemies:
		if e["kind"] == "serpent" and not e.has("gone"):
			var dist: int = absi(e["to"].x - d["row"]) + absi(e["to"].y - hero["to"].y)
			if dist <= 3:
				e["lured"] = true
	# other enemies vanish as he rises
	for e in enemies:
		if not e.has("lured"):
			e["gone"] = true


func _tick_ride() -> void:
	phase_t -= TICK
	for e in enemies:
		if e.has("lured"):
			if e["t"] < 1.0:
				e["t"] = minf(1.0, e["t"] + TICK / HOP)
			elif not on_pyramid(e["to"]):
				e["fall_t"] = e.get("fall_t", 0.0) + TICK
				if not e.has("scored"):
					e["scored"] = true
					score += 500
					_extra()
					event.emit("lure", {})
			else:
				# hop towards the edge he left from
				var goal: Vector2i = _ride["from"]
				var best := _step_toward(e["to"], goal, true)
				e["from_cell"] = e["to"]
				e["to"] = best
				e["t"] = 0.0
	if phase_t <= 0.0:
		enemies.clear()
		hero = {"at": Vector2i(0, 0), "to": Vector2i(0, 0), "t": 1.0, "dir": "dl", "state": "stand", "fall_t": 0.0}
		phase = Phase.PLAY
		_spawn_t = 1.5
		event.emit("ride_end", {})
		event.emit("land", {"who": "hero", "cell": Vector2i(0, 0)})
		_paint(Vector2i(0, 0))


func _enemy_period() -> float:
	return maxf(0.42, 0.95 - 0.08 * level - 0.03 * round)


func _spawn() -> void:
	_spawn_t -= TICK
	if _spawn_t > 0.0:
		return
	_spawn_t = rng.randf_range(3.0, 5.5) - minf(1.5, 0.25 * level)
	var kinds := ["red", "red"]
	if not enemies.any(func(e): return e["kind"] in ["purple", "serpent"]):
		kinds.append_array(["purple", "purple"])
	if round_time > 12.0:
		kinds.append("green")
	if level >= 1 or round >= 2:
		kinds.append("imp")
	var kind: String = kinds[rng.randi() % kinds.size()]
	if enemies.size() >= 3 + mini(level, 2):
		return
	var c := Vector2i(1, rng.randi() % 2)
	enemies.append({"kind": kind, "to": c, "from_cell": c, "t": 1.0, "wait": 0.6, "drop": 0.6})
	event.emit("spawn", {"kind": kind})


func _tick_enemies() -> void:
	var period := _enemy_period()
	for e in enemies:
		if e.has("gone"):
			continue
		if e.get("drop", 0.0) > 0.0:
			e["drop"] -= TICK
			continue
		if e.has("fall_t"):
			e["fall_t"] += TICK
			if e["fall_t"] > FALL_TIME:
				e["gone"] = true
			continue
		if e["t"] < 1.0:
			e["t"] = minf(1.0, e["t"] + TICK / HOP)
			if e["t"] >= 1.0:
				_land_enemy(e)
			continue
		e["wait"] -= TICK
		if e["wait"] > 0.0:
			continue
		e["wait"] = period - HOP if e["kind"] != "serpent" else period * 0.85 - HOP
		var at: Vector2i = e["to"]
		var to: Vector2i
		match e["kind"]:
			"serpent":
				to = _step_toward(at, hero["to"] if on_pyramid(hero["to"]) else hero["at"], false)
			"purple":
				if at.x == ROWS - 1:
					e["kind"] = "serpent"
					e["wait"] = 0.6
					event.emit("hatch", {})
					continue
				to = at + (DIRS["dl"] if rng.randf() < 0.5 else DIRS["dr"])
			_:
				to = at + (DIRS["dl"] if rng.randf() < 0.5 else DIRS["dr"])
		e["from_cell"] = at
		e["to"] = to
		e["t"] = 0.0


func _land_enemy(e: Dictionary) -> void:
	if not on_pyramid(e["to"]):
		e["fall_t"] = 0.0
		return
	if e["kind"] == "imp":
		var i := index(e["to"])
		if tiles[i] > 0:
			tiles[i] -= 1
			event.emit("undo", {"cell": e["to"]})


## The hop from a cell that brings it closest to a goal (off the pyramid only if allowed).
func _step_toward(at: Vector2i, goal: Vector2i, allow_off: bool) -> Vector2i:
	var best := at
	var bd := INF
	var g3 := cube3(goal)
	for k in ["ur", "ul", "dr", "dl"]:
		var c: Vector2i = at + DIRS[k]
		if not allow_off and not on_pyramid(c):
			continue
		var d := cube3(c).distance_squared_to(g3)
		if d < bd:
			bd = d
			best = c
	return best


func _collide() -> void:
	if hero["state"] != "stand":
		return
	var hc := hero_cell()
	for e in enemies:
		if e.has("gone") or e.has("fall_t") or e.get("drop", 0.0) > 0.0:
			continue
		var ec := occupied(e)
		var crossing: bool = hero["t"] < 1.0 and e["t"] < 1.0 and hero["at"] == e["to"] and hero["to"] == e.get("from_cell", e["to"]) \
			and absf(hero["t"] - 0.5) < 0.3 and absf(e["t"] - 0.5) < 0.3
		if ec != hc and not crossing:
			continue
		match e["kind"]:
			"green":
				e["gone"] = true
				frozen = FREEZE_TIME
				score += 100
				_extra()
				event.emit("freeze", {})
			"imp":
				e["gone"] = true
				score += 300
				_extra()
				event.emit("catch", {})
			_:
				_die("hit")
				return


func _extra() -> void:
	if score >= _next_life:
		_next_life += 8000
		lives += 1
		event.emit("extra_life", {})


func _die(how: String) -> void:
	lives -= 1
	phase = Phase.DYING
	phase_t = 1.8
	event.emit("die", {"how": how, "cell": hero_cell()})
