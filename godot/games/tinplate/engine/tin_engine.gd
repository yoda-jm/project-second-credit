class_name TinEngine
extends RefCounted
## Tinplate Turbo rules (single-screen racing in the Super Sprint tradition; our own tuning), 60 Hz ticks. Four tin
## cars race the laps of one track: steering turns the car (it can turn slowly even when nearly stopped), the
## throttle pushes it along its nose, and the tyres grip sideways only so much, so fast corners slide. The track's
## walls bounce cars back; cars knock each other; oil takes the grip away for a moment; puddles slow you; a ramp sends
## a fast car flying; a bridge carries the road over itself where it crosses. Wrenches turn up on the road now and
## then: collect them to buy upgrades between races (top speed, grip, acceleration). Positions go by laps and how far
## round; finishing places score championship points.
## Events: "go", "countdown" {n}, "bump" {car, speed}, "knock" {a, b, speed}, "oil" {car}, "splash" {car},
## "jump" {car}, "land" {car}, "wrench" {car, pos}, "wrench_spawn" {pos}, "lap" {car, lap}, "final_lap" {car},
## "finish" {car, place}, "race_over".

signal event(kind: String, data: Dictionary)

enum Phase { COUNTDOWN, RACE, DONE }
const TICK := 1.0 / 60.0
const R := 0.85                 ## a car's radius for walls and knocks
const BASE_SPEED := 17.0
const BASE_ACC := 16.0
const BASE_GRIP := 7.0
const TURN := 3.3               ## rad/s at speed
const DRAG := 0.35
const G := 22.0
const POINTS := [4, 3, 2, 1]
const COLOURS := [Color(0.92, 0.2, 0.18), Color(0.2, 0.45, 0.95), Color(0.98, 0.78, 0.15), Color(0.2, 0.75, 0.35)]
const NAMES := ["RED", "BLUE", "YELLOW", "GREEN"]

var track: TinTrack
var cars: Array[Dictionary] = []
var phase := Phase.COUNTDOWN
var phase_t := 3.0
var time := 0.0
var wrench := {}                 ## the wrench on the road, or empty
var _wrench_t := 6.0
var finished := 0
var rng := RandomNumberGenerator.new()


## `cars_` is an array of dictionaries {cpu, upgrades: {speed, grip, accel}} for the four cars.
func _init(t: TinTrack, cars_: Array, seed_ := 1) -> void:
	track = t
	rng.seed = seed_
	var n := t.count()
	for i in cars_.size():
		var c: Dictionary = cars_[i]
		# the grid: two by two behind the line
		var s := (n - 6 - (i / 2) * 6) % n
		var side := 1.0 if i % 2 == 0 else -1.0
		var p := t.pos[s] + t.left_normal(s) * side * t.width * 0.22
		cars.append({"i": i, "cpu": c.get("cpu", true), "up": c.get("up", {"speed": 0, "grip": 0, "accel": 0}),
			"pos": p, "vel": Vector2.ZERO, "heading": t.dir[s].angle(), "steer": 0.0, "throttle": 0.0,
			"s": s, "lap": -1, "progress": -1.0 + float(s) / n, "half": true, "y": t.height[s], "vy": 0.0, "air": false,
			"oil": 0.0, "wet": 0.0, "done": false, "place": 0, "wrenches": c.get("wrenches", 0), "slide": 0.0, "time": 0.0,
			"best": INF, "lap_start": 0.0})


func top_speed(c: Dictionary) -> float:
	return BASE_SPEED * (1.0 + 0.08 * c["up"]["speed"])


func grip(c: Dictionary) -> float:
	return BASE_GRIP * (1.0 + 0.15 * c["up"]["grip"])


func accel(c: Dictionary) -> float:
	return BASE_ACC * (1.0 + 0.12 * c["up"]["accel"])


# ------------------------------------------------------------------ the tick

func tick() -> void:
	time += TICK
	match phase:
		Phase.COUNTDOWN:
			var before := ceili(phase_t)
			phase_t -= TICK
			if ceili(phase_t) != before and phase_t > 0.0:
				event.emit("countdown", {"n": ceili(phase_t)})
			if phase_t <= 0.0:
				phase = Phase.RACE
				for c in cars:
					c["lap_start"] = time
				event.emit("go", {})
			return
		Phase.DONE:
			phase_t += TICK
	for c in cars:
		_drive(c)
	_knocks()
	for c in cars:
		_progress(c)
	_wrenches()


func _drive(c: Dictionary) -> void:
	var p: Vector2 = c["pos"]
	var v: Vector2 = c["vel"]
	var h: float = c["heading"]
	if c["done"] and c["cpu"] == false:
		c["throttle"] = 0.0
	var fwd := Vector2.from_angle(h)
	var speed := v.length()
	var along := v.dot(fwd)
	if not c["air"]:
		# steering: a little even at a crawl, full from walking pace up
		var steer_k := clampf(0.35 + absf(along) / 5.0, 0.0, 1.0) * (1.0 if along >= -0.5 else -1.0)
		h += c["steer"] * TURN * steer_k * TICK
		fwd = Vector2.from_angle(h)
		var side := Vector2(-fwd.y, fwd.x)
		along = v.dot(fwd)
		var lat := v.dot(side)
		# the throttle (and a reverse at a crawl)
		along += c["throttle"] * accel(c) * TICK
		var top := top_speed(c) * (0.55 if c["wet"] > 0.0 else 1.0)
		along = clampf(along, -4.0, top)
		# sideways grip: the slide decays (oil all but removes it)
		var g := grip(c) * (0.12 if c["oil"] > 0.0 else 1.0)
		lat *= exp(-g * TICK)
		c["slide"] = absf(lat)
		v = fwd * along + side * lat
		v *= 1.0 - DRAG * TICK * (1.0 if c["throttle"] > 0.0 else 2.2)
	else:
		c["vy"] -= G * TICK
		c["y"] += c["vy"] * TICK
	c["oil"] = maxf(0.0, c["oil"] - TICK)
	c["wet"] = maxf(0.0, c["wet"] - TICK)
	p += v * TICK
	# the road under the car (following its own road where the track crosses)
	var s := track.nearest_near(p, c["s"])
	c["s"] = s
	var ground := track.height[s]
	if c["air"]:
		if c["y"] <= ground:
			c["air"] = false
			c["y"] = ground
			c["vy"] = 0.0
			event.emit("land", {"car": c["i"]})
	else:
		c["y"] = ground
		for r in track.ramps:
			var ds := absi(s - r)
			if ds <= 1 and v.length() > 7.0 and v.dot(track.dir[s]) > 0.0:
				c["air"] = true
				c["vy"] = v.length() * 0.42
				event.emit("jump", {"car": c["i"]})
	# the walls
	var off := track.offset(p, s)
	var half := track.width * 0.5 - R * 0.6
	if absf(off) > half:
		var n := track.left_normal(s) * signf(off)
		p -= n * (absf(off) - half)
		var into := v.dot(n)
		if into > 0.0:
			v -= n * into * 1.6
			v *= 0.85
			if into > 2.0:
				event.emit("bump", {"car": c["i"], "speed": into})
	# hazards
	if not c["air"]:
		for o in track.oil:
			if p.distance_to(o) < 1.3 and c["oil"] <= 0.0 and v.length() > 3.0:
				c["oil"] = 0.9
				event.emit("oil", {"car": c["i"]})
		for w in track.puddles:
			if p.distance_to(w) < 1.4:
				if c["wet"] <= 0.0 and v.length() > 3.0:
					event.emit("splash", {"car": c["i"]})
				c["wet"] = 0.4
	c["pos"] = p
	c["vel"] = v
	c["heading"] = wrapf(h, -PI, PI)


## Cars knock each other apart (only on the same level: never across the bridge).
func _knocks() -> void:
	for a in cars.size():
		for b in range(a + 1, cars.size()):
			var ca := cars[a]
			var cb := cars[b]
			if absf(ca["y"] - cb["y"]) > 1.0:
				continue
			var d: Vector2 = cb["pos"] - ca["pos"]
			var dist := d.length()
			if dist >= R * 2.0 or dist < 0.0001:
				continue
			var n := d / dist
			var rel: float = (cb["vel"] - ca["vel"]).dot(n)
			if rel < 0.0:
				var j := -rel * 0.9
				ca["vel"] -= n * j * 0.5
				cb["vel"] += n * j * 0.5
				if -rel > 2.5:
					event.emit("knock", {"a": a, "b": b, "speed": -rel})
			var push := (R * 2.0 - dist) * 0.5
			ca["pos"] -= n * push
			cb["pos"] += n * push


## Laps: a lap counts once the car has been round past halfway and crosses the line. `lap` is the laps done (-1 on
## the grid, behind the line), so progress (laps and the fraction round) only grows.
func _progress(c: Dictionary) -> void:
	var n := track.count()
	var s: int = c["s"]
	if s > n * 0.4 and s < n * 0.6:
		c["half"] = true
	var frac := float(s) / n
	var prev_frac: float = c["progress"] - floorf(c["progress"])
	if c["half"] and frac < 0.1 and prev_frac > 0.9:
		c["half"] = false
		if c["lap"] < 0:
			c["lap"] = 0
			c["lap_start"] = time
		elif not c["done"]:
			c["lap"] += 1
			var lt: float = time - c["lap_start"]
			c["best"] = minf(c["best"], lt)
			c["lap_start"] = time
			if c["lap"] >= track.laps:
				c["done"] = true
				finished += 1
				c["place"] = finished
				c["time"] = time
				event.emit("finish", {"car": c["i"], "place": finished})
				if finished == 1:
					phase = Phase.DONE
					phase_t = 0.0
				if finished == cars.size():
					event.emit("race_over", {})
			else:
				event.emit("lap", {"car": c["i"], "lap": c["lap"]})
				if c["lap"] == track.laps - 1:
					event.emit("final_lap", {"car": c["i"]})
	c["progress"] = c["lap"] + frac


func _wrenches() -> void:
	if phase != Phase.RACE:
		return
	if wrench.is_empty():
		_wrench_t -= TICK
		if _wrench_t <= 0.0:
			var s := rng.randi() % track.count()
			var p := track.pos[s] + track.left_normal(s) * rng.randf_range(-0.3, 0.3) * track.width
			wrench = {"pos": p, "s": s, "y": track.height[s], "t": 0.0}
			event.emit("wrench_spawn", {"pos": p})
		return
	wrench["t"] += TICK
	for c in cars:
		if (c["pos"] as Vector2).distance_to(wrench["pos"]) < 1.3 and absf(c["y"] - wrench["y"]) < 1.0 and not c["air"]:
			c["wrenches"] += 1
			event.emit("wrench", {"car": c["i"], "pos": wrench["pos"]})
			wrench = {}
			_wrench_t = rng.randf_range(6.0, 11.0)
			return
	if wrench["t"] > 14.0:
		wrench = {}
		_wrench_t = rng.randf_range(3.0, 6.0)


## The order of the cars: finished ones by place, the rest by how far round.
func order() -> Array[int]:
	var idx: Array[int] = []
	for i in cars.size():
		idx.append(i)
	idx.sort_custom(func(a, b):
		var ca := cars[a]
		var cb := cars[b]
		if ca["done"] != cb["done"]:
			return ca["done"]
		if ca["done"]:
			return ca["place"] < cb["place"]
		return ca["progress"] > cb["progress"])
	return idx


## Ends the race for the cars still running once the winner is in for a while (places by position).
func close_race() -> void:
	for i in order():
		var c := cars[i]
		if not c["done"]:
			c["done"] = true
			finished += 1
			c["place"] = finished
	event.emit("race_over", {})
