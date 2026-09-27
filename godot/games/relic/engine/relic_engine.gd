class_name RelicEngine
extends RefCounted
## Relic Run rules (a trap-filled flip-screen platformer in the Rick Dangerous tradition; our own tuning), 60 Hz.
## Positions are in tiles, y down; a body's (x, y) is the middle of its feet. The hero walks, jumps a little over a
## tile, climbs ladders, crawls under low passages, fires a pistol (six shots, more in bullet boxes) and plants
## dynamite (it goes off after two seconds, breaking cracked stone and anything near, the hero included). Spikes spring
## from the floor as the hero comes near, dart holes fire along their row, the boulder rolls once the hero passes its
## mark, crushers drop on whoever walks under. Dying sends the hero back to where it entered the screen.
## Events: "shot", "empty", "hit" {pos, kind, dead}, "plant", "boom" {pos}, "break" {cell}, "spikes" {cell},
## "dart" {id}, "dart_hit" {pos}, "roll", "crush" {cell}, "pickup" {kind, pos}, "die" {how, pos}, "screen" {sx, sy},
## "exit", "game_over", "jump", "land", "step".

signal event(kind: String, data: Dictionary)

enum Phase { READY, PLAY, DYING, CLEARED, OVER }
const TICK := 1.0 / 60.0
const GRAV := 42.0
const JUMP_V := -12.0
const WALK := 5.2
const CRAWL := 2.4
const CLIMB := 3.6
const HALF := 0.33
const TALL := 1.4
const LOW := 0.72
const SOLID := "#B="

var level: RelicLevel
var rng := RandomNumberGenerator.new()
var phase := Phase.READY
var phase_t := 1.5
var time := 0.0
var score := 0
var lives := 6
var bullets := 6
var dynamite := 6
var tiles := PackedByteArray()
var hero := {}
var move_x := 0.0
var up := false
var down := false
var jump_pressed := false
var fire_pressed := false
var plant_pressed := false
var respawn := Vector2.ZERO
var screen := Vector2i.ZERO
var spikes: Array[Dictionary] = []   ## {cell, up (0..1), t, state: rest/arming/up/down}
var shooters: Array[Dictionary] = [] ## {cell, dir, cool}
var darts: Array[Dictionary] = []    ## {id, pos, dir}
var crushers: Array[Dictionary] = [] ## {cell, drop (tiles down), state, t}
var enemies: Array[Dictionary] = []  ## {id, kind, pos, facing, hp, home, alive}
var pickups: Array[Dictionary] = []  ## {kind, cell, taken}
var shots: Array[Dictionary] = []    ## {pos, dir}
var bombs: Array[Dictionary] = []    ## {pos, fuse}
var boulder := {}                    ## {pos, dir, rolling, done, vy}
var _id := 1
var _step_t := 0.0


func _init(lv: RelicLevel, seed_ := 1, lives_ := 6, score_ := 0) -> void:
	level = lv
	rng.seed = seed_
	lives = lives_
	score = score_
	tiles = lv.tiles.duplicate()
	for t in lv.things:
		var c: Vector2i = t["cell"]
		match t["kind"]:
			"S": spikes.append({"cell": c, "up": 0.0, "t": 0.0, "state": "rest"})
			"D", "d": shooters.append({"cell": c, "dir": 1 if t["kind"] == "D" else -1, "cool": 0.0})
			"C": crushers.append({"cell": c, "drop": 0.0, "state": "rest", "t": 0.0})
			"e", "k", "b":
				var kind: String = {"e": "automaton", "k": "skeleton", "b": "bat"}[t["kind"]]
				enemies.append({"id": _next(), "kind": kind, "pos": Vector2(c.x + 0.5, c.y + 1.0), "facing": -1, "alive": true,
					"hp": 2 if kind == "automaton" else 1, "home": Vector2(c.x + 0.5, c.y + 1.0), "vy": 0.0})
			"$", "a", "x": pickups.append({"kind": t["kind"], "cell": c, "taken": false})
	if lv.boulder.x >= 0:
		boulder = {"pos": Vector2(lv.boulder.x + 0.5, lv.boulder.y + 0.1), "dir": signi(lv.trigger_col - lv.boulder.x), "rolling": false,
			"done": false, "vy": 0.0, "start": Vector2(lv.boulder.x + 0.5, lv.boulder.y + 0.1)}
	var s := Vector2(lv.start.x + 0.5, lv.start.y + 1.0)
	hero = {"pos": s, "vel": Vector2.ZERO, "facing": 1, "state": "ground", "tall": TALL}
	respawn = s
	screen = _screen_of(s)


func _next() -> int:
	_id += 1
	return _id


func at(x: int, y: int) -> String:
	if x < 0 or y < 0 or x >= level.w or y >= level.h:
		return "#"
	return char(tiles[y * level.w + x])


func solid(x: int, y: int) -> bool:
	return SOLID.contains(at(x, y))


func ladder(x: int, y: int) -> bool:
	return at(x, y) == "H"


## Can a body stand on the top of tile (x, y)?
func floor_at(x: int, y: int) -> bool:
	return solid(x, y) or (ladder(x, y) and not ladder(x, y - 1))


func _screen_of(p: Vector2) -> Vector2i:
	return Vector2i(clampi(int(floor(p.x / RelicLevel.SW)), 0, level.cols - 1), clampi(int(floor((p.y - 0.5) / RelicLevel.SH)), 0, level.rows - 1))


# ------------------------------------------------------------------ the tick

func tick() -> void:
	time += TICK
	match phase:
		Phase.READY:
			phase_t -= TICK
			if phase_t <= 0.0:
				phase = Phase.PLAY
			_edges()
			return
		Phase.DYING:
			phase_t -= TICK
			_move_boulder()
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
	_move_hero()
	if phase != Phase.PLAY:
		return
	_traps()
	_move_boulder()
	_move_enemies()
	_move_shots()
	_bombs()
	_touch()
	_edges()


func _edges() -> void:
	jump_pressed = false
	fire_pressed = false
	plant_pressed = false


# ------------------------------------------------------------------ the hero

func _body_blocked(p: Vector2, tall: float) -> bool:
	var x0 := int(floor(p.x - HALF))
	var x1 := int(floor(p.x + HALF))
	var y0 := int(floor(p.y - tall + 0.02))
	var y1 := int(floor(p.y - 0.02))
	for y in range(y0, y1 + 1):
		for x in range(x0, x1 + 1):
			if solid(x, y):
				return true
	return false


func _on_ladder(p: Vector2) -> bool:
	var x := int(floor(p.x))
	return ladder(x, int(floor(p.y - 0.1))) or ladder(x, int(floor(p.y - 0.8)))


func _move_hero() -> void:
	var h := hero
	var p: Vector2 = h["pos"]
	var v: Vector2 = h["vel"]
	var st: String = h["state"]
	if move_x != 0.0:
		h["facing"] = int(signf(move_x))
	# ladders: grab with up or down
	if st != "climb":
		var tx := int(floor(p.x))
		var below_ladder := ladder(tx, int(floor(p.y + 0.1)))
		if (up and _on_ladder(p)) or (down and below_ladder and st == "ground"):
			st = "climb"
			p.x = tx + 0.5
			v = Vector2.ZERO
	if st == "climb":
		var dy := (-1.0 if up else 0.0) + (1.0 if down else 0.0)
		var np := p + Vector2(0, dy * CLIMB * TICK)
		if move_x != 0.0 and not up and not down:
			# step off sideways onto a floor
			st = "ground" if floor_at(int(floor(p.x)), int(floor(p.y + 0.05))) else "air"
		elif not (_on_ladder(np) or ladder(int(floor(np.x)), int(floor(np.y + 0.05)))):
			# off the top: stand on it; off the bottom: fall or land
			st = "ground" if floor_at(int(floor(np.x)), int(floor(np.y + 0.05))) else "air"
			if dy < 0.0:
				np.y = floor(np.y + 0.05)
		elif dy > 0.0 and solid(int(floor(np.x)), int(floor(np.y))):
			np.y = floor(np.y)
			st = "ground"
		p = np
		h["pos"] = p
		h["vel"] = Vector2.ZERO
		h["state"] = st
		h["tall"] = TALL
		_screen_check()
		return
	# crawling
	var want_low := down and st in ["ground", "crawl"]
	if st == "crawl" and not want_low and _body_blocked(p, TALL):
		want_low = true  # no room to stand
	if want_low and st == "ground":
		st = "crawl"
	elif not want_low and st == "crawl":
		st = "ground"
	var tall := LOW if st == "crawl" else TALL
	var speed := CRAWL if st == "crawl" else WALK
	v.x = move_x * speed
	if jump_pressed and st == "ground":
		v.y = JUMP_V
		st = "air"
		event.emit("jump", {})
	v.y = minf(v.y + GRAV * TICK, 20.0)
	# sideways
	var nx := p + Vector2(v.x * TICK, 0)
	if not _body_blocked(nx, tall):
		p = nx
	elif st == "ground" and v.x != 0.0:
		# a small step (a quarter tile) is climbed
		var stepped := nx + Vector2(0, -0.3)
		if not _body_blocked(stepped, tall):
			p = stepped
	# vertical
	var ny := p.y + v.y * TICK
	if v.y > 0.0:
		var landed := false
		for row in range(int(floor(p.y - 0.001)) + 1, int(floor(ny)) + 1):
			for tx in [int(floor(p.x - HALF + 0.05)), int(floor(p.x + HALF - 0.05))]:
				if floor_at(tx, row):
					landed = true
			if landed:
				ny = float(row)
				break
		if landed:
			if st == "air" and v.y > 6.0:
				event.emit("land", {})
			v.y = 0.0
			if st == "air":
				st = "ground"
		elif st in ["ground", "crawl"] and ny - p.y > 0.0:
			if not floor_at(int(floor(p.x - HALF + 0.05)), int(floor(p.y + 0.05))) and not floor_at(int(floor(p.x + HALF - 0.05)), int(floor(p.y + 0.05))):
				st = "air"
		p.y = ny
	else:
		var np := Vector2(p.x, ny)
		if _body_blocked(np, tall):
			v.y = 0.0
		else:
			p = np
	if st in ["ground", "crawl"] and absf(v.x) > 0.1:
		_step_t -= TICK
		if _step_t <= 0.0:
			_step_t = 0.28 if st == "ground" else 0.4
			event.emit("step", {})
	h["pos"] = p
	h["vel"] = v
	h["state"] = st
	h["tall"] = tall
	# the pistol and the dynamite
	if fire_pressed:
		if bullets > 0:
			bullets -= 1
			var y := p.y - (0.45 if st == "crawl" else 0.95)
			shots.append({"pos": Vector2(p.x + h["facing"] * 0.4, y), "dir": h["facing"]})
			event.emit("shot", {})
		else:
			event.emit("empty", {})
	if plant_pressed and dynamite > 0 and st in ["ground", "crawl"]:
		dynamite -= 1
		bombs.append({"pos": Vector2(p.x, p.y), "fuse": 2.0})
		event.emit("plant", {})
	if p.y > level.h + 2.0:
		_die("fall")
	_screen_check()


func _screen_check() -> void:
	var s := _screen_of(hero["pos"])
	if s != screen:
		screen = s
		respawn = hero["pos"]
		event.emit("screen", {"sx": s.x, "sy": s.y})
	elif hero["state"] == "ground" and absf(hero["pos"].x - respawn.x) < 0.01:
		pass
	# the exit
	var e := level.exit
	var hp: Vector2 = hero["pos"]
	if absf(hp.x - (e.x + 0.5)) < 0.8 and absf(hp.y - (e.y + 1.0)) < 1.2:
		phase = Phase.CLEARED
		phase_t = 3.0
		score += 5000
		event.emit("exit", {})


# ------------------------------------------------------------------ traps

func _traps() -> void:
	var hp: Vector2 = hero["pos"]
	for s in spikes:
		var c: Vector2i = s["cell"]
		match s["state"]:
			"rest":
				if absf(hp.x - (c.x + 0.5)) < 1.6 and absf(hp.y - (c.y + 1.0)) < 1.1:
					s["state"] = "arming"
					s["t"] = 0.05
			"arming":
				s["t"] -= TICK
				if s["t"] <= 0.0:
					s["state"] = "up"
					s["t"] = 1.4
					event.emit("spikes", {"cell": c})
			"up":
				s["up"] = minf(1.0, s["up"] + TICK * 14.0)
				s["t"] -= TICK
				if s["t"] <= 0.0:
					s["state"] = "down"
			"down":
				s["up"] = maxf(0.0, s["up"] - TICK * 3.0)
				if s["up"] <= 0.0:
					s["state"] = "cool"
					s["t"] = 0.8
			"cool":
				s["t"] -= TICK
				if s["t"] <= 0.0:
					s["state"] = "rest"
	for sh in shooters:
		sh["cool"] = maxf(0.0, sh["cool"] - TICK)
		var c: Vector2i = sh["cell"]
		var mid_y: float = hp.y - hero["tall"] * 0.5
		var ahead: float = (hp.x - (c.x + 0.5)) * sh["dir"]
		if sh["cool"] <= 0.0 and absf(mid_y - (c.y + 0.5)) < 0.9 and ahead > 0.0 and ahead < 11.0:
			sh["cool"] = 2.2
			darts.append({"id": _next(), "pos": Vector2(c.x + 0.5 + sh["dir"] * 0.6, c.y + 0.2), "dir": sh["dir"], "from": c.x + 0.5})
			event.emit("dart", {"id": _id})
	for d in darts.duplicate():
		d["pos"] += Vector2(d["dir"] * 11.0 * TICK, 0)
		var dp: Vector2 = d["pos"]
		if absf(dp.x - d["from"]) > 12.0:
			darts.erase(d)  # spent: it drops out of sight
		elif solid(int(floor(dp.x + d["dir"] * 0.2)), int(floor(dp.y))):
			darts.erase(d)
			event.emit("dart_hit", {"pos": dp})
	for cr in crushers:
		var c: Vector2i = cr["cell"]
		match cr["state"]:
			"rest":
				if absf(hp.x - (c.x + 0.5)) < 0.7 and hp.y > c.y and hp.y < c.y + 8:
					cr["state"] = "drop"
			"drop":
				cr["drop"] += 14.0 * TICK
				var bottom: float = c.y + 1.0 + cr["drop"]
				if solid(c.x, int(floor(bottom))):
					cr["drop"] = floor(bottom) - c.y - 1.0
					cr["state"] = "hold"
					cr["t"] = 1.0
					event.emit("crush", {"cell": c})
			"hold":
				cr["t"] -= TICK
				if cr["t"] <= 0.0:
					cr["state"] = "rise"
			"rise":
				cr["drop"] = maxf(0.0, cr["drop"] - 2.0 * TICK)
				if cr["drop"] <= 0.0:
					cr["state"] = "cool"
					cr["t"] = 1.0
			"cool":
				cr["t"] -= TICK
				if cr["t"] <= 0.0:
					cr["state"] = "rest"
	# the boulder waits for the hero to pass its mark
	if not boulder.is_empty() and not boulder["rolling"] and not boulder["done"] and level.trigger_col >= 0:
		if int(floor(hp.x)) == level.trigger_col:
			boulder["rolling"] = true
			event.emit("roll", {})


func _move_boulder() -> void:
	if boulder.is_empty() or not boulder["rolling"] or boulder["done"]:
		return
	var p: Vector2 = boulder["pos"]
	boulder["vy"] = minf(boulder["vy"] + GRAV * TICK, 18.0)
	var ny: float = p.y + boulder["vy"] * TICK
	# the ball's bottom is 0.9 below its centre
	var row := int(floor(ny + 0.9))
	if floor_at(int(floor(p.x - 0.7)), row) or floor_at(int(floor(p.x)), row) or floor_at(int(floor(p.x + 0.7)), row):
		ny = floor(ny + 0.9) - 0.9
		boulder["vy"] = 0.0
	p.y = ny
	var nx: float = p.x + boulder["dir"] * 5.0 * TICK
	if solid(int(floor(nx + boulder["dir"] * 0.9)), int(floor(p.y))) or solid(int(floor(nx + boulder["dir"] * 0.9)), int(floor(p.y + 0.5))):
		boulder["done"] = true  # smashed against the wall
		event.emit("crush", {"cell": Vector2i(p)})
	else:
		p.x = nx
	boulder["pos"] = p


# ------------------------------------------------------------------ enemies, shots, bombs

func _move_enemies() -> void:
	for en in enemies:
		if not en["alive"]:
			continue
		var p: Vector2 = en["pos"]
		if en["kind"] == "bat":
			p.x += en["facing"] * 2.5 * TICK
			p.y = en["home"].y - 0.6 + sin(time * 3.0 + en["id"]) * 0.6
			if absf(p.x - en["home"].x) > 4.0 or solid(int(floor(p.x + en["facing"] * 0.4)), int(floor(p.y - 0.3))):
				en["facing"] = -en["facing"]
			en["pos"] = p
			continue
		var speed := 1.6 if en["kind"] == "automaton" else 2.2
		var nx: float = p.x + en["facing"] * speed * TICK
		var ahead := int(floor(nx + en["facing"] * 0.4))
		var wall := solid(ahead, int(floor(p.y - 0.5))) or solid(ahead, int(floor(p.y - 1.2)))
		var edge := not floor_at(ahead, int(floor(p.y + 0.05)))
		if wall or edge:
			en["facing"] = -en["facing"]
		else:
			p.x = nx
		en["pos"] = p


func _move_shots() -> void:
	for s in shots.duplicate():
		s["pos"] += Vector2(s["dir"] * 18.0 * TICK, 0)
		var sp: Vector2 = s["pos"]
		if solid(int(floor(sp.x)), int(floor(sp.y))):
			shots.erase(s)
			event.emit("dart_hit", {"pos": sp, "shot": true})
			continue
		for en in enemies:
			if not en["alive"]:
				continue
			var ep: Vector2 = en["pos"]
			var top := ep.y - (0.9 if en["kind"] == "bat" else 1.5)
			if absf(sp.x - ep.x) < 0.45 and sp.y > top and sp.y < ep.y:
				shots.erase(s)
				en["hp"] -= 1
				var dead: bool = en["hp"] <= 0
				if dead:
					en["alive"] = false
					score += 200 if en["kind"] == "automaton" else 100
				event.emit("hit", {"pos": sp, "kind": en["kind"], "dead": dead})
				break
		if absf(sp.x - hero["pos"].x) > 24.0:
			shots.erase(s)


func _bombs() -> void:
	for b in bombs.duplicate():
		b["fuse"] -= TICK
		if b["fuse"] > 0.0:
			continue
		bombs.erase(b)
		var c: Vector2 = b["pos"] + Vector2(0, -0.5)
		event.emit("boom", {"pos": c})
		for y in range(int(c.y) - 2, int(c.y) + 3):
			for x in range(int(c.x) - 2, int(c.x) + 3):
				if at(x, y) == "B" and Vector2(x + 0.5, y + 0.5).distance_to(c) < 2.0:
					tiles[y * level.w + x] = ".".unicode_at(0)
					score += 50
					event.emit("break", {"cell": Vector2i(x, y)})
		for en in enemies:
			if en["alive"] and (en["pos"] - Vector2(0, 0.7)).distance_to(c) < 1.9:
				en["alive"] = false
				score += 200
				event.emit("hit", {"pos": en["pos"], "kind": en["kind"], "dead": true})
		if (hero["pos"] - Vector2(0, 0.6)).distance_to(c) < 1.6 and phase == Phase.PLAY:
			_die("boom")


func _touch() -> void:
	var hp: Vector2 = hero["pos"]
	var tall: float = hero["tall"]
	var box := Rect2(hp.x - HALF, hp.y - tall, HALF * 2.0, tall)
	# pits
	if at(int(floor(hp.x)), int(floor(hp.y - 0.3))) == "~":
		_die("pit")
		return
	for s in spikes:
		var c: Vector2i = s["cell"]
		if s["up"] > 0.5 and box.intersects(Rect2(c.x + 0.1, c.y + 1.0 - 0.8 * s["up"], 0.8, 0.8 * s["up"])):
			_die("spikes")
			return
	for d in darts:
		if box.has_point(d["pos"]):
			darts.erase(d)
			_die("dart")
			return
	for cr in crushers:
		var c: Vector2i = cr["cell"]
		var r := Rect2(c.x + 0.05, c.y + cr["drop"], 0.9, 1.0)
		if cr["drop"] > 0.2 and box.intersects(r):
			_die("crush")
			return
	if not boulder.is_empty() and boulder["rolling"] and not boulder["done"]:
		if (boulder["pos"] as Vector2).distance_to(hp + Vector2(0, -tall * 0.5)) < 1.2:
			_die("boulder")
			return
	for en in enemies:
		if en["alive"] and box.intersects(Rect2(en["pos"].x - 0.35, en["pos"].y - (0.7 if en["kind"] == "bat" else 1.4), 0.7, 0.7 if en["kind"] == "bat" else 1.4)):
			_die(en["kind"])
			return
	for pk in pickups:
		if not pk["taken"] and box.grow(0.1).has_point(Vector2(pk["cell"]) + Vector2(0.5, 0.6)):
			pk["taken"] = true
			match pk["kind"]:
				"$": score += 1000
				"a": bullets = 6
				"x": dynamite = 6
			event.emit("pickup", {"kind": pk["kind"], "pos": Vector2(pk["cell"]) + Vector2(0.5, 0.5)})


func _die(how: String) -> void:
	lives -= 1
	phase = Phase.DYING
	phase_t = 2.0
	event.emit("die", {"how": how, "pos": hero["pos"]})


func _respawn() -> void:
	hero["pos"] = respawn
	hero["vel"] = Vector2.ZERO
	hero["state"] = "ground"
	darts.clear()
	shots.clear()
	bombs.clear()
	bullets = maxi(bullets, 3)
	dynamite = maxi(dynamite, 2)
	# the boulder waits again if it had not finished its run
	if not boulder.is_empty() and not boulder["done"]:
		boulder["rolling"] = false
		boulder["pos"] = boulder["start"]
		boulder["vy"] = 0.0
	for s in spikes:
		s["state"] = "rest"
		s["up"] = 0.0
	phase = Phase.READY
	phase_t = 0.8
