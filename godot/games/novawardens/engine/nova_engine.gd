class_name NovaEngine
extends RefCounted
## Nova Wardens rules (fixed-shooter defence in the Space Invaders tradition; the classic's rules and our own timings
## tuned to feel like it), 60 Hz ticks, in a 224 x 256 pixel field (y down, like the arcade screen).
## The fleet: 5 rows of 11 (squids on top worth 30, crabs 20, octopuses 10). It marches as a ripple: one invader moves
## each tick, so the fewer are left the faster the fleet goes. At a side wall the whole fleet drops 8 pixels and turns.
## Invaders drop bombs (at most three at once) of three kinds: a rolling one aimed near the cannon, a plunger and a
## squiggly one. The cannon has one shot on screen at a time. Four shields erode pixel by pixel from shots, bombs and
## invaders marching through them. A mystery ship crosses the top every so often (50 to 300: the classic 23rd shot,
## then every 15th, gives 300). An invader reaching the cannon's row ends the game; clear the fleet and the next wave
## starts lower. Extra life at 1500.
## Events: "shot", "hit" {kind, pos, points}, "bomb" {kind}, "bomb_hit" {pos}, "shield" {pos}, "step" {n} (the march's
## four-note beat), "ufo", "ufo_hit" {pos, points}, "ufo_gone", "die" {pos}, "wave" {n}, "cleared", "game_over",
## "extra_life", "land".

signal event(kind: String, data: Dictionary)

enum Phase { READY, PLAY, DYING, CLEARED, OVER }
const TICK := 1.0 / 60.0
const W := 224
const H := 256
const COLS := 11
const ROWS := 5
const GAP_X := 16
const GAP_Y := 16
const INV_W := 12
const INV_H := 8
const CANNON_Y := 216
const CANNON_W := 13
const CANNON_SPEED := 60.0       ## pixels a second
const SHOT_SPEED := 240.0
const BOMB_SPEED := 75.0
const STEP_X := 2
const DROP_Y := 8
const SHIELD_W := 22
const SHIELD_H := 16
const SHIELD_Y := 192
const UFO_Y := 40
const UFO_SPEED := 40.0
const START_ROWS := [120, 144, 160, 168, 168, 168, 176, 176, 176]  ## the fleet's bottom row y, wave after wave
const POINTS := [30, 20, 20, 10, 10]
const UFO_TABLE := [100, 50, 50, 100, 150, 100, 100, 50, 300, 100, 100, 100, 50, 150, 100]

var phase := Phase.READY
var phase_t := 1.5
var time := 0.0
var wave := 0
var score := 0
var lives := 3
var alive := PackedByteArray()      ## per invader (row * COLS + col): 1 while alive
var origin := Vector2(24, 64)       ## top-left of the formation (col 0, row 0)
var offsets: Array[Vector2i] = []   ## per invader: its lag behind the ripple (0 or the pending step)
var dir := 1
var ripple := 0                     ## the next invader to move
var dropping := false
var frame := 0                      ## the invaders' two-frame walk, flips each full march step
var cannon_x := 104.0
var move_x := 0.0
var fire_pressed := false
var shot := {}                      ## {pos} or empty
var shots_fired := 0
var bombs: Array[Dictionary] = []   ## {kind, pos, t}
var bomb_t := 0.8
var shields: Array[PackedByteArray] = []   ## 4 bitmaps of SHIELD_W x SHIELD_H, 1 solid
var ufo := {}
var ufo_t := 25.0
var landed := false
var rng := RandomNumberGenerator.new()
var _next_life := 1500
var _beat := 0


func _init(wave_ := 0, lives_ := 3, score_ := 0, seed_ := 1) -> void:
	wave = wave_
	lives = lives_
	score = score_
	rng.seed = seed_ + wave * 31
	_next_life = 1500 if score < 1500 else 1 << 30
	_new_wave()


func _new_wave() -> void:
	alive.resize(COLS * ROWS)
	alive.fill(1)
	offsets.clear()
	for i in COLS * ROWS:
		offsets.append(Vector2i.ZERO)
	var bottom: int = START_ROWS[mini(wave, START_ROWS.size() - 1)]
	origin = Vector2(24, bottom - (ROWS - 1) * GAP_Y)
	dir = 1
	ripple = 0
	dropping = false
	shields.clear()
	for i in 4:
		shields.append(_shield_bitmap())
	bombs.clear()
	shot = {}
	ufo = {}
	ufo_t = 25.0
	cannon_x = 104.0


## The classic shield shape: a block with a rounded top and a notch cut from the bottom middle.
static func _shield_bitmap() -> PackedByteArray:
	var b := PackedByteArray()
	b.resize(SHIELD_W * SHIELD_H)
	for y in SHIELD_H:
		for x in SHIELD_W:
			var solid := true
			var cx := minf(x, SHIELD_W - 1 - x)
			if y < 4 and cx < 4 - y:
				solid = false  # rounded corners
			if y >= 11 and x >= 7 - (y - 11) and x <= SHIELD_W - 8 + (y - 11):
				solid = false  # the arch under the middle, widening to the ground
			b[y * SHIELD_W + x] = 1 if solid else 0
	return b


static func shield_x(i: int) -> int:
	return 32 + i * 45


func invader_pos(i: int) -> Vector2:
	var r := i / COLS
	var c := i % COLS
	return origin + Vector2(c * GAP_X, r * GAP_Y) + Vector2(offsets[i])


func invaders_left() -> int:
	var n := 0
	for a in alive:
		n += a
	return n


func kind_of(i: int) -> String:
	var r := i / COLS
	return "squid" if r == 0 else ("crab" if r < 3 else "octopus")


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
				if lives <= 0 or landed:
					phase = Phase.OVER
					phase_t = 3.0
					event.emit("game_over", {})
				else:
					bombs.clear()
					cannon_x = 104.0
					phase = Phase.READY
					phase_t = 1.0
			return
		Phase.CLEARED:
			phase_t -= TICK
			if phase_t <= 0.0:
				wave += 1
				_new_wave()
				phase = Phase.READY
				phase_t = 1.5
				event.emit("wave", {"n": wave})
			return
		Phase.OVER:
			phase_t -= TICK
			return
	_move_cannon()
	_march()
	_move_shot()
	_bombs()
	_ufo()
	fire_pressed = false


func _move_cannon() -> void:
	cannon_x = clampf(cannon_x + move_x * CANNON_SPEED * TICK, 16.0, W - 16.0 - CANNON_W)
	if fire_pressed and shot.is_empty():
		shot = {"pos": Vector2(cannon_x + CANNON_W * 0.5, CANNON_Y - 4)}
		shots_fired += 1
		event.emit("shot", {})


## One invader moves each tick; after the last one in the ripple, the fleet has taken a whole step.
func _march() -> void:
	var n := COLS * ROWS
	if invaders_left() == 0:
		return
	# the next living invader in the ripple; past the last one, the fleet completes its step and starts again
	while ripple < n and alive[ripple] == 0:
		ripple += 1
	if ripple >= n:
		_complete_step()
		if phase != Phase.PLAY:
			return
		ripple = 0
		while alive[ripple] == 0:
			ripple += 1
	var i := ripple
	if dropping:
		offsets[i] += Vector2i(0, DROP_Y)
	else:
		offsets[i] += Vector2i(STEP_X * dir, 0)
	_crush_shields(i)
	ripple += 1


## Every living invader has moved once: fold the offsets into the formation, turn at a wall, check for a landing.
func _complete_step() -> void:
	var n := COLS * ROWS
	var d: Vector2i = Vector2i(0, DROP_Y) if dropping else Vector2i(STEP_X * dir, 0)
	origin += Vector2(d)
	for k in n:
		offsets[k] -= d
	frame = 1 - frame
	event.emit("step", {"n": _beat})
	_beat = (_beat + 1) % 4
	if dropping:
		dropping = false
		dir = -dir
	else:
		for k in n:
			if alive[k] == 1:
				var p := invader_pos(k)
				if (dir > 0 and p.x + INV_W + STEP_X > W - 8) or (dir < 0 and p.x - STEP_X < 8):
					dropping = true
					break
	for k in n:
		if alive[k] == 1 and invader_pos(k).y + INV_H >= CANNON_Y:
			landed = true
			event.emit("land", {})
			_die()
			return


## An invader marching through a shield eats it.
func _crush_shields(i: int) -> void:
	var p := invader_pos(i)
	if p.y + INV_H < SHIELD_Y:
		return
	for s in 4:
		var sx := shield_x(s)
		var r := Rect2i(int(p.x) - sx, int(p.y) - SHIELD_Y, INV_W, INV_H)
		for y in range(maxi(r.position.y, 0), mini(r.end.y, SHIELD_H)):
			for x in range(maxi(r.position.x, 0), mini(r.end.x, SHIELD_W)):
				shields[s][y * SHIELD_W + x] = 0


func _move_shot() -> void:
	if shot.is_empty():
		return
	var p: Vector2 = shot["pos"]
	p.y -= SHOT_SPEED * TICK
	shot["pos"] = p
	if p.y < 24:
		shot = {}
		event.emit("miss", {"pos": p})
		return
	# the mystery ship
	if not ufo.is_empty() and Rect2(ufo["x"], UFO_Y, 16, 7).has_point(p):
		var pts := _ufo_points()
		score += pts
		_extra()
		event.emit("ufo_hit", {"pos": Vector2(ufo["x"] + 8, UFO_Y + 4), "points": pts})
		ufo = {}
		ufo_t = 25.0
		shot = {}
		return
	# invaders
	for i in COLS * ROWS:
		if alive[i] == 0:
			continue
		var ip := invader_pos(i)
		if Rect2(ip, Vector2(INV_W, INV_H)).has_point(p):
			alive[i] = 0
			var pts: int = POINTS[i / COLS]
			score += pts
			_extra()
			event.emit("hit", {"kind": kind_of(i), "pos": ip + Vector2(INV_W, INV_H) * 0.5, "points": pts, "index": i})
			shot = {}
			if invaders_left() == 0:
				phase = Phase.CLEARED
				phase_t = 2.5
				bombs.clear()
				event.emit("cleared", {})
			return
	# bombs: a shot can meet one head on
	for b in bombs:
		if (b["pos"] as Vector2).distance_to(p) < 3.0:
			bombs.erase(b)
			shot = {}
			event.emit("bomb_hit", {"pos": p})
			return
	# shields
	if _hit_shield(p, 1):
		shot = {}


## The classic's mystery-ship scoring: the 23rd shot, and every 15th after, is worth 300.
func _ufo_points() -> int:
	if shots_fired >= 23 and (shots_fired - 23) % 15 == 0:
		return 300
	return UFO_TABLE[(shots_fired - 1) % UFO_TABLE.size()]


## A shot (dir -1 up... here 1 = from below) or bomb hitting a shield erodes a small blast around the impact.
func _hit_shield(p: Vector2, from_below: int) -> bool:
	for s in 4:
		var lx := int(p.x) - shield_x(s)
		var ly := int(p.y) - SHIELD_Y
		if lx < 0 or lx >= SHIELD_W or ly < 0 or ly >= SHIELD_H:
			continue
		if shields[s][ly * SHIELD_W + lx] == 0:
			continue
		for dy in range(-3, 4):
			for dx in range(-2, 3):
				var x := lx + dx
				var y := ly + dy + from_below  # the blast digs in the way it came
				if x >= 0 and x < SHIELD_W and y >= 0 and y < SHIELD_H and (absi(dx) + absi(dy) < 4) and rng.randf() < 0.8:
					shields[s][y * SHIELD_W + x] = 0
		event.emit("shield", {"pos": p, "index": s})
		return true
	return false


func _bombs() -> void:
	# drop: at most three at once, from the bottom invader of a column
	bomb_t -= TICK
	if bomb_t <= 0.0 and bombs.size() < 3:
		bomb_t = maxf(0.35, 1.1 - wave * 0.08) * rng.randf_range(0.6, 1.3)
		var kinds := ["rolling", "plunger", "squiggly"]
		var kind: String = kinds[rng.randi() % 3]
		var col := _bomb_column(kind)
		if col >= 0:
			for r in range(ROWS - 1, -1, -1):
				var i := r * COLS + col
				if alive[i] == 1:
					var ip := invader_pos(i)
					bombs.append({"kind": kind, "pos": ip + Vector2(INV_W * 0.5, INV_H + 2), "t": 0.0})
					event.emit("bomb", {"kind": kind})
					break
	for b in bombs.duplicate():
		var p: Vector2 = b["pos"]
		b["t"] += TICK
		p.y += BOMB_SPEED * TICK * (1.25 if invaders_left() < 9 else 1.0)
		b["pos"] = p
		if p.y > 232:
			bombs.erase(b)
			event.emit("bomb_ground", {"pos": p})
			continue
		if _hit_shield(p, -1):
			bombs.erase(b)
			continue
		if phase == Phase.PLAY and Rect2(cannon_x, CANNON_Y, CANNON_W, 8).has_point(p):
			bombs.erase(b)
			_die()
			return


## The rolling bomb comes from the column over the cannon; the others from any column with invaders left.
func _bomb_column(kind: String) -> int:
	var cols := []
	for c in COLS:
		for r in ROWS:
			if alive[r * COLS + c] == 1:
				cols.append(c)
				break
	if cols.is_empty():
		return -1
	if kind == "rolling":
		var best: int = cols[0]
		var bd := INF
		for c in cols:
			var d := absf(origin.x + c * GAP_X + INV_W * 0.5 - (cannon_x + CANNON_W * 0.5))
			if d < bd:
				bd = d
				best = c
		return best
	return cols[rng.randi() % cols.size()]


func _ufo() -> void:
	if ufo.is_empty():
		ufo_t -= TICK
		if ufo_t <= 0.0 and invaders_left() >= 8:
			var from_left := shots_fired % 2 == 0
			ufo = {"x": 8.0 if from_left else W - 24.0, "dir": 1.0 if from_left else -1.0}
			event.emit("ufo", {})
		return
	ufo["x"] += ufo["dir"] * UFO_SPEED * TICK
	if ufo["x"] < 0.0 or ufo["x"] > W - 16:
		ufo = {}
		ufo_t = 25.0
		event.emit("ufo_gone", {})


func _extra() -> void:
	if score >= _next_life:
		_next_life = 1 << 30
		lives += 1
		event.emit("extra_life", {})


func _die() -> void:
	lives -= 1
	phase = Phase.DYING
	phase_t = 2.0
	shot = {}
	event.emit("die", {"pos": Vector2(cannon_x + CANNON_W * 0.5, CANNON_Y + 4)})
