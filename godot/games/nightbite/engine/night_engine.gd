class_name NightEngine
extends RefCounted
## Nightbite rules (a maze chase in the spirit of the arcade classics; our own names, tuning and twists), at fixed
## 60 Hz ticks, seeded. The hero runs the lanes and turns as soon as a way opens (a turn pressed early is kept);
## four lantern spirits hunt with four temperaments, in waves of scattering and chasing; a power orb frightens them
## for a while and each one eaten scores double the last; eaten spirits race home as eyes and come back.
## Bonus gems appear twice a stage. Clear every pellet to go on; the stages get faster.
## Events: "pellet", "power", "eat_spirit" {chain}, "spirit_home", "bonus_show", "bonus_eat", "died", "cleared",
## "mode" {scatter|chase}, "extra_life".

signal event(kind: String, data: Dictionary)

enum Phase { READY, PLAY, DYING, CLEARED }
const TICK := 1.0 / 60.0
const DIRS: Array[Vector2i] = [Vector2i(0, -1), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(1, 0)]  ## tie order: up, left, down, right
const NAMES := ["Ember", "Wisp", "Gloom", "Drift"]
const WAVES := [7.0, 20.0, 7.0, 20.0, 5.0, 20.0, 5.0, INF]  ## scatter, chase, scatter, chase...
const READY_TIME := 2.2
const EXTRA_AT := 10000

var maze: NightMaze
var stage := 0
var rng := RandomNumberGenerator.new()
var phase := Phase.READY
var phase_t := READY_TIME
var time := 0.0
var score := 0
var lives := 3
var pellets := {}
var powers := {}
var hero := {}
var spirits: Array[Dictionary] = []
var fright := 0.0
var chain := 0
var mode := "scatter"
var wave := 0
var wave_t := 0.0
var bonus_t := -1.0  ## seconds the bonus gem stays
var bonus_kind := 0
var eaten_count := 0
var want := Vector2i.ZERO  ## the direction the player holds or last pressed
var _extra_given := false


func _init(m: NightMaze, stage_ := 0, seed_ := 1, lives_ := 3, score_ := 0) -> void:
	maze = m
	stage = stage_
	lives = lives_
	score = score_
	rng.seed = seed_
	pellets = m.pellets.duplicate()
	powers = m.powers.duplicate()
	_place()


func _place() -> void:
	hero = {"pos": Vector2(maze.hero) + Vector2(0.5, 0.5), "dir": Vector2i(-1, 0), "moving": false}
	spirits.clear()
	for i in 4:
		var c: Vector2i = maze.spirits[i]
		spirits.append({"id": i, "pos": Vector2(c) + Vector2(0.5, 0.5), "dir": Vector2i(-1, 0) if i == 0 else Vector2i(0, -1),
			"state": "out" if i == 0 else "home", "release": [0.0, 2.5, 6.0, 10.0][i] * maxf(0.4, 1.0 - stage * 0.15), "scared": false})
	fright = 0.0
	mode = "scatter"
	wave = 0
	wave_t = 0.0
	phase = Phase.READY
	phase_t = READY_TIME


# ------------------------------------------------------------------ speeds (cells per second)

func hero_speed() -> float:
	var base := 7.4 + minf(stage, 6) * 0.35
	return base * (1.08 if fright > 0.0 else 1.0)


func spirit_speed(s: Dictionary) -> float:
	var base := 7.0 + minf(stage, 6) * 0.4
	match s["state"]:
		"eyes": return 16.0
		"home", "leaving": return 3.5
	if s["scared"]:
		return base * 0.55
	var c := cell(s["pos"])
	if c.x <= 1 or c.x >= maze.w - 2:
		return base * 0.5  # tunnels slow the spirits
	if s["id"] == 0 and pellets.size() < 25:
		return base * 1.08  # Ember speeds up near the end
	return base


static func cell(p: Vector2) -> Vector2i:
	return Vector2i(p.floor())


func open_for(c: Vector2i, spirit: Dictionary = {}) -> bool:
	if maze.wall(c):
		return false
	if maze.gate.has(maze.wrap_cell(c)):
		return not spirit.is_empty() and spirit["state"] in ["eyes", "leaving"]
	return true


# ------------------------------------------------------------------ the tick

func tick() -> void:
	time += TICK
	match phase:
		Phase.READY:
			phase_t -= TICK
			if phase_t <= 0.0:
				phase = Phase.PLAY
			return
		Phase.DYING, Phase.CLEARED:
			phase_t -= TICK
			return
	_waves()
	_move_hero()
	_eat()
	for s in spirits:
		_move_spirit(s)
	_touch()
	if bonus_t > 0.0:
		bonus_t -= TICK
	if not _extra_given and score >= EXTRA_AT:
		_extra_given = true
		lives += 1
		event.emit("extra_life", {})


func _waves() -> void:
	if fright > 0.0:
		fright -= TICK
		if fright <= 0.0:
			for s in spirits:
				s["scared"] = false
		return
	wave_t += TICK
	if wave < WAVES.size() and wave_t >= WAVES[wave]:
		wave_t = 0.0
		wave += 1
		mode = "chase" if wave % 2 == 1 else "scatter"
		for s in spirits:
			if s["state"] == "out":
				s["reverse"] = true
		event.emit("mode", {"mode": mode})


func _move_hero() -> void:
	var p: Vector2 = hero["pos"]
	var d: Vector2i = hero["dir"]
	var step := hero_speed() * TICK
	var c := cell(p)
	var centre := Vector2(c) + Vector2(0.5, 0.5)
	# reverse at once
	if want == -d and want != Vector2i.ZERO:
		hero["dir"] = want
		d = want
	# a turn: taken as soon as the hero is near the centre of a cell that opens that way (pre-turn forgiveness)
	if want != Vector2i.ZERO and want != d and open_for(c + want):
		var off := (p - centre).length()
		if off <= step * 1.5 + 0.12:
			p = centre
			d = want
			hero["dir"] = d
	var along := (p - centre).dot(Vector2(d))
	if open_for(c + d) or along < -0.001:
		var np := p + Vector2(d) * step
		if not open_for(c + d) and (np - centre).dot(Vector2(d)) > 0.0:
			np = centre
		p = np
		hero["moving"] = true
	else:
		p = centre
		hero["moving"] = false
	# keep to the lane's axis
	if d.x != 0:
		p.y = centre.y
	else:
		p.x = centre.x
	hero["pos"] = _wrap_pos(p)


func _wrap_pos(p: Vector2) -> Vector2:
	if p.x < 0.0:
		p.x += maze.w
	elif p.x >= maze.w:
		p.x -= maze.w
	return p


func _eat() -> void:
	var c := maze.wrap_cell(cell(hero["pos"]))
	if pellets.has(c):
		pellets.erase(c)
		score += 10
		event.emit("pellet", {"cell": c})
		_after_pellet()
	elif powers.has(c):
		powers.erase(c)
		score += 50
		fright = maxf(1.5, 7.0 - stage * 0.8)
		chain = 0
		for s in spirits:
			if s["state"] == "out":
				s["scared"] = true
				s["reverse"] = true
		event.emit("power", {"cell": c, "time": fright})
		_after_pellet()
	if bonus_t > 0.0 and c == maze.bonus:
		bonus_t = -1.0
		var pts: int = [100, 300, 500, 700, 1000, 2000][mini(stage, 5)]
		score += pts
		event.emit("bonus_eat", {"points": pts, "kind": bonus_kind})


func _after_pellet() -> void:
	eaten_count += 1
	if eaten_count == 60 or eaten_count == 130:
		bonus_t = 9.5
		bonus_kind = mini(stage, 3)
		event.emit("bonus_show", {"kind": bonus_kind})
	if pellets.is_empty() and powers.is_empty():
		phase = Phase.CLEARED
		phase_t = 3.0
		event.emit("cleared", {})


# ------------------------------------------------------------------ spirits

func _target(s: Dictionary) -> Vector2i:
	var hc := cell(hero["pos"])
	var hd: Vector2i = hero["dir"]
	var corners: Array[Vector2i] = [Vector2i(maze.w - 2, -2), Vector2i(1, -2), Vector2i(maze.w - 2, maze.h + 1), Vector2i(1, maze.h + 1)]
	if mode == "scatter" and not (s["id"] == 0 and pellets.size() < 25):
		return corners[s["id"]]
	match s["id"]:
		0: return hc                                   # Ember: straight at you
		1: return hc + hd * 4                          # Wisp: where you are going
		2:                                             # Gloom: flanks, mirroring Ember across the cell ahead of you
			var pivot := hc + hd * 2
			return pivot + (pivot - cell(spirits[0]["pos"]))
		_:                                             # Drift: close in, then lose its nerve
			return hc if Vector2(cell(s["pos"])).distance_to(Vector2(hc)) > 7.0 else corners[3]


func _move_spirit(s: Dictionary) -> void:
	var p: Vector2 = s["pos"]
	var step := spirit_speed(s) * TICK
	match s["state"]:
		"home":
			s["release"] -= TICK
			# bob in the house
			s["pos"] = Vector2(p.x, p.y + sin(time * 6.0 + s["id"]) * 0.01)
			if s["release"] <= 0.0:
				s["state"] = "leaving"
			return
		"leaving":
			var door := Vector2(maze.spirits[0]) + Vector2(0.5, 0.5)
			if absf(p.x - door.x) > step:
				p.x = move_toward(p.x, door.x, step)
			else:
				p.x = door.x
				p.y = move_toward(p.y, door.y, step)
			s["pos"] = p
			if p.distance_to(door) < 0.01:
				s["state"] = "out"
				s["dir"] = Vector2i(-1, 0)
				s["scared"] = false
			return
	var c := cell(p)
	var centre := Vector2(c) + Vector2(0.5, 0.5)
	var d: Vector2i = s["dir"]
	var dist := (p - centre).dot(Vector2(d))
	if s.get("reverse", false):
		s["reverse"] = false
		s["dir"] = -d
		d = -d
		dist = (p - centre).dot(Vector2(d))
	# decide at the centre of each cell
	if dist >= 0.0 and dist < step + 0.001 and s.get("decided", Vector2i(-99, -99)) != c:
		s["decided"] = c
		p = centre
		if s["state"] == "eyes" and c == maze.spirits[0]:
			s["state"] = "entering"
		else:
			d = _choose(s, c, d)
			s["dir"] = d
	if s["state"] == "entering":  # through the gate, into the house, then out again
		var home := Vector2(maze.house[s["id"] % maze.house.size()]) + Vector2(0.5, 0.5) if not maze.house.is_empty() else centre
		p.x = move_toward(p.x, home.x, step)
		p.y = move_toward(p.y, home.y, step) if absf(p.x - home.x) < 0.01 else p.y
		s["pos"] = p
		if p.distance_to(home) < 0.01:
			s["state"] = "leaving"
			s["scared"] = false
			event.emit("spirit_home", {"id": s["id"]})
		return
	s["pos"] = _wrap_pos(p + Vector2(d) * step)


func _choose(s: Dictionary, c: Vector2i, d: Vector2i) -> Vector2i:
	var options: Array[Vector2i] = []
	for nd in DIRS:
		if nd != -d and open_for(c + nd, s):
			options.append(nd)
	if options.is_empty():
		return -d
	if s["scared"]:
		return options[rng.randi_range(0, options.size() - 1)]
	var target: Vector2i = maze.spirits[0] if s["state"] == "eyes" else _target(s)
	var best := options[0]
	var bd := INF
	for nd in options:
		var dd := Vector2(c + nd).distance_squared_to(Vector2(target))
		if dd < bd:
			bd = dd
			best = nd
	return best


func _touch() -> void:
	var hp: Vector2 = hero["pos"]
	for s in spirits:
		if s["state"] != "out":
			continue
		var d: Vector2 = s["pos"] - hp
		d.x = wrapf(d.x, -maze.w * 0.5, maze.w * 0.5)
		if d.length() < 0.6:
			if s["scared"]:
				s["scared"] = false
				s["state"] = "eyes"
				s["decided"] = Vector2i(-99, -99)
				chain += 1
				var pts: int = 200 << (chain - 1)
				score += pts
				event.emit("eat_spirit", {"id": s["id"], "chain": chain, "points": pts, "pos": s["pos"]})
			else:
				phase = Phase.DYING
				phase_t = 2.0
				lives -= 1
				event.emit("died", {"pos": hp})
				return


## After a death: the actors go back to their starts; the pellets stay eaten.
func respawn() -> void:
	_place()
