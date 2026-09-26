class_name HopEngine
extends RefCounted
## Hopline rules (a lane-crossing game in the Frogger tradition; our own tuning), fixed 60 Hz ticks, seeded.
## The board is W columns by 13 rows: row 12 the start bank, rows 11-7 the road, row 6 the median, rows 5-1 the
## canal, row 0 the hedge with five home bays. Everything in a lane moves at a steady speed and wraps round, so where
## it is is a pure function of time (the autopilot plans with that). On the road a vehicle squashes the frog; on the
## canal the frog must stand on a log, a lily pad or a turtle that is not under water, and rides it; carried off the
## side it is lost. Each life has a time bar. Fill all five bays to finish the stage; stages get faster, more turtles
## dive, a crocodile lurks in the bays. A fly in a bay and a lady frog on a log are worth a bonus.
## Events: "hop", "land" {row}, "home" {bay, time_bonus}, "all_home", "die" {how}, "fly", "lady", "lady_home",
## "extra_life", "turtle_dive" {row}, "game_over", "time_warn".

signal event(kind: String, data: Dictionary)

enum Phase { READY, PLAY, DYING, CLEARED, OVER }
const TICK := 1.0 / 60.0
const W := 14
const ROWS := 13
const START_ROW := 12
const HOP_TICKS := 9
const HOP_TIME := HOP_TICKS * TICK
const LIFE_TIME := 30.0
const BAYS := [1.0, 4.0, 7.0, 10.0, 13.0]
const SPAN := 8.0            ## lanes wrap over W + SPAN so objects enter and leave off screen
const DIRS := {"up": Vector2i(0, -1), "down": Vector2i(0, 1), "left": Vector2i(-1, 0), "right": Vector2i(1, 0)}

var stage := 0
var rng := RandomNumberGenerator.new()
var phase := Phase.READY
var phase_t := 1.5
var time := 0.0              ## lane clock
var life_t := LIFE_TIME
var score := 0
var lives := 4
var row := START_ROW
var x := 7.0                 ## the frog's centre, in cells (can be fractional while riding)
var facing := Vector2i(0, -1)
var hop_t := 0.0             ## > 0 while in the air (seconds left, for the view)
var hop_left := 0            ## ticks left in the air
var hop_from := Vector2(7.0, START_ROW)
var want := ""               ## the direction asked for (one hop per press)
var lanes: Array[Dictionary] = []   ## per row: {kind, dir, speed, objs: [{x0, len, type, dive}], river}
var filled := [false, false, false, false, false]
var best_row := START_ROW
var fly_bay := -1
var fly_t := 0.0
var croc_bay := -1
var croc_t := 0.0
var croc_rise := 0.0         ## 0..1: how far the crocodile's head is out
var lady := {}               ## {row, obj, on (riding with the frog)} or empty
var _next_life := 10000
var _warned := false


func _init(stage_ := 0, seed_ := 1, lives_ := 4, score_ := 0) -> void:
	stage = stage_
	rng.seed = seed_
	lives = lives_
	score = score_
	_next_life = (score / 10000 + 1) * 10000
	_build_lanes()
	fly_t = 6.0
	croc_t = 12.0


func _build_lanes() -> void:
	var k := 1.0 + minf(stage, 6) * 0.14
	var dive := mini(stage + 1, 4)   ## how many turtle groups dive
	lanes.resize(ROWS)
	for r in ROWS:
		lanes[r] = {"kind": "safe", "dir": 0, "speed": 0.0, "objs": [], "river": false}
	# the road, bottom lane first: type, dir, speed, length, count
	var road := [["car_a", -1, 1.1, 1.2, 3], ["bulldozer", 1, 0.8, 1.4, 3], ["car_b", -1, 1.5, 1.6, 3],
		["racecar", 1, 3.2, 1.2, 1 + mini(stage, 1)], ["truck", -1, 1.2, 2.6, 2]]
	for i in 5:
		var d: Array = road[i]
		lanes[11 - i] = _lane(d[0], d[1], d[2] * k, d[3], d[4], false)
	# the canal, bottom lane first
	var river := [["turtle3", -1, 1.2, 3.0, 4], ["log_short", 1, 0.9, 3.0, 3], ["log_long", 1, 1.9, 6.0, 2],
		["turtle2", -1, 1.2, 2.0, 4], ["log_mid", 1, 1.4, 4.0, 3]]
	for i in 5:
		var d: Array = river[i]
		lanes[5 - i] = _lane(d[0], d[1], d[2] * k, d[3], d[4], true)
	# some turtle groups dive, now and then
	var groups: Array = []
	for r in [5, 2]:
		for o in lanes[r]["objs"]:
			groups.append(o)
	for i in mini(dive, groups.size()):
		groups[i * 3 % groups.size()]["dive"] = rng.randf_range(0.0, 6.0) + 0.5


func _lane(type: String, dir: int, speed: float, length: float, count: int, river: bool) -> Dictionary:
	var objs := []
	var period := W + SPAN
	var gap := period / count
	var off := rng.randf_range(0.0, gap)
	for i in count:
		objs.append({"x0": off + i * gap, "len": length, "type": type, "dive": -1.0})
	return {"kind": type, "dir": dir, "speed": speed, "objs": objs, "river": river}


# ------------------------------------------------------------------ where things are

## Left end of an object at time t, in cells (it may be off screen).
func obj_x(r: int, o: Dictionary, t: float) -> float:
	var ln: Dictionary = lanes[r]
	return fposmod(o["x0"] + ln["dir"] * ln["speed"] * t, W + SPAN) - SPAN * 0.5


## How far under a diving turtle group is at time t: 0 up, 1 fully under (a 7 s cycle).
func sunk(o: Dictionary, t: float) -> float:
	if o["dive"] < 0.0:
		return 0.0
	var p := fposmod(t + o["dive"], 7.0)
	if p < 4.0: return 0.0
	if p < 4.6: return (p - 4.0) / 0.6
	if p < 6.2: return 1.0
	if p < 6.8: return 1.0 - (p - 6.2) / 0.6
	return 0.0


## Is the frog safe at (r, fx) at time t (not counting the clock)? For the canal it also tells what carries it.
func safe_at(r: int, fx: float, t: float) -> bool:
	if r == 0:
		return false  # the hedge row is handled by landing in a bay
	var ln: Dictionary = lanes[r]
	if ln["river"]:
		if fx < 0.25 or fx > W - 0.25:
			return false
		for o in ln["objs"]:
			var ox := obj_x(r, o, t)
			if fx >= ox + 0.1 and fx <= ox + o["len"] - 0.1 and sunk(o, t) < 0.7:
				return true
		return false
	if ln["kind"] == "safe":
		return fx >= 0.2 and fx <= W - 0.2
	for o in ln["objs"]:
		var ox := obj_x(r, o, t)
		if fx > ox - 0.3 and fx < ox + o["len"] + 0.3:
			return false
	return true


func drift(r: int) -> float:
	var ln: Dictionary = lanes[r]
	return ln["dir"] * ln["speed"] if ln["river"] else 0.0


func bay_at(fx: float) -> int:
	for i in BAYS.size():
		if absf(fx - BAYS[i]) < 0.45:
			return i
	return -1


# ------------------------------------------------------------------ the tick

func tick() -> void:
	time += TICK
	match phase:
		Phase.READY:
			phase_t -= TICK
			if phase_t <= 0.0:
				phase = Phase.PLAY
			return
		Phase.DYING:
			phase_t -= TICK
			if phase_t <= 0.0:
				if lives <= 0:
					phase = Phase.OVER
					event.emit("game_over", {})
				else:
					_respawn()
			return
		Phase.CLEARED, Phase.OVER:
			phase_t -= TICK
			return
	life_t -= TICK
	if life_t < 8.0 and not _warned:
		_warned = true
		event.emit("time_warn", {})
	if life_t <= 0.0:
		_die("time")
		return
	_bonuses()
	if hop_left > 0:
		hop_left -= 1
		hop_t = hop_left * TICK
		if hop_left == 0:
			_land()
		return
	# riding
	x += drift(row) * TICK
	if lanes[row]["river"] and (x < 0.25 or x > W - 0.25):
		_die("swept")
		return
	if not safe_at(row, x, time):
		_die("drown" if lanes[row]["river"] else "splat")
		return
	if want != "":
		_hop(want)
		want = ""


func _hop(dir: String) -> void:
	var d: Vector2i = DIRS[dir]
	facing = d
	var nr := row + d.y
	var nx := x + d.x
	if nr > START_ROW or nx < 0.3 or nx > W - 0.3:
		return
	hop_from = Vector2(x, row)
	row = nr
	x = nx
	hop_left = HOP_TICKS
	hop_t = HOP_TIME
	event.emit("hop", {})


func _land() -> void:
	if not lanes[row]["river"] and row != 0:
		x = clampf(roundf(x), 1.0, W - 1.0)  # on land the frog keeps to the grid (whole cells, as the bays)
	if row < best_row:
		best_row = row
		score += 10
	event.emit("land", {"row": row})
	if row == 0:
		var b := bay_at(x)
		if b < 0 or filled[b] or (b == croc_bay and croc_rise >= 1.0):
			_die("hedge" if b < 0 or filled[b] else "croc")
			return
		filled[b] = true
		var bonus := int(life_t * 2.0) * 10
		score += 50 + bonus
		if b == fly_bay:
			score += 200
			fly_bay = -1
			event.emit("fly", {})
		if lady.get("on", false):
			score += 200
			event.emit("lady_home", {})
		lady = {}
		event.emit("home", {"bay": b, "time_bonus": bonus})
		_extra()
		if not filled.has(false):
			score += 1000
			phase = Phase.CLEARED
			phase_t = 3.0
			event.emit("all_home", {})
			_extra()
			return
		_respawn(false)
		return
	if not safe_at(row, x, time):
		_die("drown" if lanes[row]["river"] else "splat")
		return
	# picking up the lady frog
	if not lady.is_empty() and not lady.get("on", false) and lady["row"] == row:
		var o: Dictionary = lanes[row]["objs"][lady["obj"]]
		var lx: float = obj_x(row, o, time) + o["len"] * 0.5
		if absf(lx - x) < 0.8:
			lady["on"] = true
			event.emit("lady", {})


func _extra() -> void:
	if score >= _next_life:
		_next_life += 10000
		lives += 1
		event.emit("extra_life", {})


func _die(how: String) -> void:
	lives -= 1
	phase = Phase.DYING
	phase_t = 1.6
	if lady.get("on", false):
		lady = {}
	event.emit("die", {"how": how, "x": x, "row": row})


func _respawn(reset_time := true) -> void:
	row = START_ROW
	x = 7.0
	facing = Vector2i(0, -1)
	hop_t = 0.0
	hop_left = 0
	best_row = START_ROW
	life_t = LIFE_TIME
	_warned = false
	phase = Phase.PLAY if not reset_time else Phase.READY
	phase_t = 0.6


func _bonuses() -> void:
	fly_t -= TICK
	if fly_t <= 0.0:
		if fly_bay >= 0:
			fly_bay = -1
			fly_t = rng.randf_range(4.0, 8.0)
		else:
			var free := []
			for i in 5:
				if not filled[i] and i != croc_bay:
					free.append(i)
			if not free.is_empty():
				fly_bay = free[rng.randi_range(0, free.size() - 1)]
			fly_t = 5.0
	if stage >= 1:
		croc_t -= TICK
		if croc_t <= 0.0:
			if croc_bay >= 0:
				croc_bay = -1
				croc_t = rng.randf_range(6.0, 10.0)
			else:
				var free := []
				for i in 5:
					if not filled[i] and i != fly_bay:
						free.append(i)
				if not free.is_empty():
					croc_bay = free[rng.randi_range(0, free.size() - 1)]
					croc_rise = 0.0
				croc_t = 5.0
	croc_rise = minf(1.0, croc_rise + TICK / 1.5)  # the head comes up slowly: it bites only once it is out
	if lady.is_empty() and rng.randf() < TICK / 20.0:
		lady = {"row": 4, "obj": rng.randi_range(0, lanes[4]["objs"].size() - 1), "on": false}
	# the turtles' dives are sounded as they start
	for r in [5, 2]:
		for o in lanes[r]["objs"]:
			if o["dive"] >= 0.0 and sunk(o, time) > 0.0 and sunk(o, time - TICK) == 0.0:
				event.emit("turtle_dive", {"row": r})
