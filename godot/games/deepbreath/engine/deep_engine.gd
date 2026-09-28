class_name DeepEngine
extends RefCounted
## Deep Breath rules (a single-screen cavern platformer in the Manic Miner tradition; our own tuning), 60 Hz ticks.
## Tiles, y down; the miner's (x, y) is the middle of his feet. He walks, and jumps a fixed arc (no steering in the
## air); dropping more than a few tiles below where he took off (or stepped off) is fatal. Floors are stood on from above; rock walls block; crumbling floor
## gives way a moment after he stands on it; conveyors carry him. Spikes, plants and steam kill, and so do the
## guardians on their patrols. Take every key and the lift opens: step in. All the while the air runs out.
## Events: "key" {cell, left}, "open", "jump", "land", "step", "crumble" {cell}, "die" {how, pos}, "cleared" {bonus},
## "game_over", "air_low", "extra_life".

signal event(kind: String, data: Dictionary)

enum Phase { READY, PLAY, DYING, CLEARED, OVER }
const TICK := 1.0 / 60.0
const WALK := 4.0
const CONVEYOR := 2.6
const JUMP_V := -16.0
const GRAV := 40.0
const FALL_LIMIT := 4.6     ## tiles: a longer drop is fatal
const HALF := 0.3
const TALL := 1.8
const CRUMBLE_TIME := 0.4

var level: DeepLevel
var phase := Phase.READY
var phase_t := 1.6
var time := 0.0
var score := 0
var lives := 3
var air := 60.0
var tiles := PackedByteArray()
var keys := {}
var crumble := {}        ## cell -> seconds stood on
var guards: Array[Dictionary] = []
var hero := {}
var move_x := 0.0
var jump_pressed := false
var open := false
var _step_t := 0.0
var _next_life := 10000
var _warned := false


func _init(lv: DeepLevel, lives_ := 3, score_ := 0) -> void:
	level = lv
	lives = lives_
	score = score_
	_next_life = (score / 10000 + 1) * 10000
	_reset()


func _reset() -> void:
	tiles = level.tiles.duplicate()
	keys.clear()
	for k in level.keys:
		keys[k] = true
	crumble.clear()
	guards.clear()
	for g in level.guards:
		guards.append({"kind": g["kind"], "pos": g["pos"], "axis": g["axis"], "min": g["min"], "max": g["max"],
			"speed": g["speed"], "dir": 1})
	air = level.air
	open = keys.is_empty()
	_warned = false
	hero = {"pos": Vector2(level.start.x + 0.5, level.start.y + 1.0), "vel": Vector2.ZERO, "state": "walk", "facing": 1,
		"fall_from": 0.0}


func at(x: int, y: int) -> String:
	if x < 0 or x >= DeepLevel.W:
		return "#"
	if y < 0 or y >= DeepLevel.H:
		return "."
	return char(tiles[y * DeepLevel.W + x])


func wall(x: int, y: int) -> bool:
	return at(x, y) == "#"


## Can the miner stand on the top of tile (x, y)?
func floor_at(x: int, y: int) -> bool:
	return at(x, y) in ["#", "=", "~", "<", ">"]


func _standing_cell(p: Vector2) -> Vector2i:
	var row := int(round(p.y))
	for x in [int(floor(p.x)), int(floor(p.x - HALF + 0.05)), int(floor(p.x + HALF - 0.05))]:
		if floor_at(x, row):
			return Vector2i(x, row)
	return Vector2i(-1, -1)


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
					_reset()
					phase = Phase.READY
					phase_t = 1.0
			return
		Phase.CLEARED:
			# the air left counts into the score
			if air > 0.0:
				var d := minf(air, TICK * 30.0)
				air -= d
				score += int(d * 10.0)
				_extra()
			phase_t -= TICK
			return
		Phase.OVER:
			return
	air -= TICK
	if air < 12.0 and not _warned:
		_warned = true
		event.emit("air_low", {})
	if air <= 0.0:
		air = 0.0
		_die("air")
		return
	_move_hero()
	jump_pressed = false
	if phase != Phase.PLAY:
		return
	_move_guards()
	_touch()


func _move_hero() -> void:
	var h := hero
	var p: Vector2 = h["pos"]
	var v: Vector2 = h["vel"]
	var st: String = h["state"]
	if st == "walk":
		var cell := _standing_cell(p)
		var belt := 0.0
		match at(cell.x, cell.y):
			"<": belt = -1.0
			">": belt = 1.0
			"~":
				crumble[cell] = crumble.get(cell, 0.0) + TICK
				if crumble[cell] >= CRUMBLE_TIME:
					tiles[cell.y * DeepLevel.W + cell.x] = ".".unicode_at(0)
					crumble.erase(cell)
					event.emit("crumble", {"cell": cell})
		if move_x != 0.0:
			h["facing"] = int(signf(move_x))
		# a conveyor carries him; walking against it just holds him still
		var vx := move_x * WALK
		if belt != 0.0:
			vx = belt * CONVEYOR if move_x == 0.0 or signf(move_x) == belt else 0.0
			if move_x != 0.0 and signf(move_x) == belt:
				vx = belt * WALK
		if jump_pressed:
			st = "air"
			v = Vector2(move_x * WALK, JUMP_V)
			h["fall_from"] = p.y
			event.emit("jump", {})
		else:
			var nx := p.x + vx * TICK
			if not _blocked(Vector2(nx, p.y)):
				p.x = nx
			if absf(vx) > 0.1:
				_step_t -= TICK
				if _step_t <= 0.0:
					_step_t = 0.26
					event.emit("step", {})
			if _standing_cell(p).x < 0:
				st = "air"
				v = Vector2(0.0, 0.0)  # he walks off the edge: straight down
				h["fall_from"] = p.y
	if st == "air":
		v.y = minf(v.y + GRAV * TICK, 16.0)
		var np := p + v * TICK
		if _blocked(Vector2(np.x, p.y)):
			np.x = p.x
			v.x = 0.0
		if v.y < 0.0 and wall(int(floor(np.x)), int(floor(np.y - TALL))):
			v.y = 0.0  # head against rock
			np.y = p.y
		if v.y > 0.0:
			for r in range(int(floor(p.y - 0.001)) + 1, int(floor(np.y)) + 1):
				if _standing_cell(Vector2(np.x, float(r))).x >= 0:
					np.y = float(r)
					var drop: float = np.y - h["fall_from"]
					if drop > FALL_LIMIT:
						h["pos"] = np
						_die("fall")
						return
					st = "walk"
					v = Vector2.ZERO
					event.emit("land", {})
					break
		p = np
		if p.y > DeepLevel.H + 2:
			_die("fall")
			return
	h["pos"] = p
	h["vel"] = v
	h["state"] = st


## Rock at the miner's body height beside him.
func _blocked(p: Vector2) -> bool:
	for dy in [0.3, 1.0, 1.6]:
		for dx in [-HALF, HALF]:
			if wall(int(floor(p.x + dx)), int(floor(p.y - dy))):
				return true
	return false


func _move_guards() -> void:
	for g in guards:
		var axis_x: bool = g["axis"] == "h"
		var p: Vector2 = g["pos"]
		var v: float = (p.x if axis_x else p.y) + g["dir"] * g["speed"] * TICK
		if v > g["max"]:
			v = g["max"]
			g["dir"] = -1
		elif v < g["min"]:
			v = g["min"]
			g["dir"] = 1
		if axis_x:
			p.x = v
		else:
			p.y = v
		g["pos"] = p


func _touch() -> void:
	var p: Vector2 = hero["pos"]
	var body := Rect2(p.x - HALF + 0.08, p.y - TALL + 0.1, (HALF - 0.08) * 2.0, TALL - 0.15)
	for c in level.hazards:
		if body.intersects(Rect2(c.x + 0.15, c.y + 0.3, 0.7, 0.7)):
			_die("hazard")
			return
	for g in guards:
		var gp: Vector2 = g["pos"]
		if body.intersects(Rect2(gp.x - 0.4, gp.y - 1.6, 0.8, 1.5)):
			_die("guard")
			return
	for k in keys.keys():
		if body.grow(0.1).has_point(Vector2(k) + Vector2(0.5, 0.5)):
			keys.erase(k)
			score += 100
			_extra()
			event.emit("key", {"cell": k, "left": keys.size()})
			if keys.is_empty():
				open = true
				event.emit("open", {})
	if open:
		var pr := Rect2(level.portal.x, level.portal.y, 2.0, 2.0)
		if pr.has_point(p + Vector2(0, -0.5)):
			phase = Phase.CLEARED
			phase_t = 3.5
			event.emit("cleared", {"bonus": int(air * 10.0)})


func _extra() -> void:
	if score >= _next_life:
		_next_life += 10000
		lives += 1
		event.emit("extra_life", {})


func _die(how: String) -> void:
	lives -= 1
	phase = Phase.DYING
	phase_t = 2.0
	event.emit("die", {"how": how, "pos": hero["pos"]})
