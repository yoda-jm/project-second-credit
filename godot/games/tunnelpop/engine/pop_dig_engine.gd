class_name DigEngine
extends RefCounted
## Tunnel Pop rules (dig and pump in the Dig Dug tradition; our own tuning), 60 Hz ticks. A cross-section of earth:
## a grid of cells (x right, y down: row 0 is sky, row 1 the surface lane, rows 2 down are earth in four layers).
## The hero moves along rows and columns (turning only at a cell's centre, as in the classic) and digs as he goes:
## each cell and each link between two cells opens once he passes. Creatures follow the tunnels towards him; one
## that cannot reach him turns into a pair of eyes and drifts through the earth, then takes shape again in a tunnel.
## The pump: a hose shoots up to three cells along open tunnel; a creature it reaches is caught and each squeeze puffs
## it up a step (it shrinks back when left alone); the fourth pops it, worth more the deeper it was (a drake pumped
## from the side scores double). Drakes breathe fire along their row, through the earth too. A rock falls when the
## cell under it is dug, crushing whatever is below; two dropped rocks bring out a vegetable in the middle. The last
## creature runs for the surface and away. A level is cleared when no creature is left.
## Events: "dig", "shoot" {dir}, "hook" {id}, "pump" {id, step}, "pop" {id, pos, points}, "miss", "ghost" {id},
## "solid" {id}, "breathe" {id}, "fire" {id, from, to}, "wobble" {rock}, "fall" {rock}, "land" {rock, crushed},
## "crush" {id, points}, "veg" {pos}, "veg_take" {points}, "die" {pos, how}, "last" {id}, "escape" {id}, "cleared",
## "game_over", "extra_life", "level" {n}.

signal event(kind: String, data: Dictionary)

enum Phase { READY, PLAY, DYING, CLEARED, OVER }
const TICK := 1.0 / 60.0
const COLS := 14
const ROWS := 15
const SPEED := 3.6              ## cells/s in a tunnel
const DIG_SPEED := 2.7          ## cells/s through earth
const HOSE := 3.0
const DIRS := [Vector2i(1, 0), Vector2i(0, 1), Vector2i(-1, 0), Vector2i(0, -1)]   ## right, down, left, up
const LAYER_POINTS := [200, 300, 400, 500]
const VEG_POINTS := [400, 600, 800, 1000, 2000, 3000, 4000, 5000]
const CRUSH_POINTS := [1000, 2500, 4000, 6000, 8000, 10000]

var level := 0
var phase := Phase.READY
var phase_t := 2.0
var time := 0.0
var score := 0
var lives := 3
var open := PackedByteArray()          ## cells dug (COLS * ROWS)
var hlink := PackedByteArray()         ## link between (x, y) and (x + 1, y) dug
var vlink := PackedByteArray()         ## link between (x, y) and (x, y + 1) dug
var hero := {}
var want := Vector2i.ZERO              ## the direction held
var pump_pressed := false
var pump_held := false
var hose := {}                         ## the hose out: {dir, len, t, id (caught creature or -1)}
var foes: Array[Dictionary] = []
var rocks: Array[Dictionary] = []
var dropped := 0
var veg := {}                          ## the vegetable when out: {pos, t}
var fires: Array[Dictionary] = []      ## {from, to, t}
var rng := RandomNumberGenerator.new()
var _next_id := 0
var _next_life := 10000
var _crushed_now := 0


func _init(level_ := 0, score_ := 0, lives_ := 3, seed_ := 1) -> void:
	level = level_
	score = score_
	lives = lives_
	rng.seed = seed_ * 101 + level_ * 7
	_next_life = (score / 10000 + 1) * 10000
	_layout()


static func layer_of(y: int) -> int:
	return clampi((y - 2) / 3 if y < 11 else 3, 0, 3)


static func inside(c: Vector2i) -> bool:
	return c.x >= 0 and c.y >= 1 and c.x < COLS and c.y < ROWS


func idx(c: Vector2i) -> int:
	return c.y * COLS + c.x


func is_open(c: Vector2i) -> bool:
	return inside(c) and open[idx(c)] == 1


## Whether one can pass between two neighbouring cells along a dug tunnel.
func linked(a: Vector2i, b: Vector2i) -> bool:
	if not is_open(a) or not is_open(b):
		return false
	if a.y == b.y:
		return hlink[idx(Vector2i(mini(a.x, b.x), a.y))] == 1
	return vlink[idx(Vector2i(a.x, mini(a.y, b.y)))] == 1


func _dig_cell(c: Vector2i) -> void:
	if inside(c) and open[idx(c)] == 0:
		open[idx(c)] = 1


func _dig_link(a: Vector2i, b: Vector2i) -> void:
	if not inside(a) or not inside(b):
		return
	if a.y == b.y:
		hlink[idx(Vector2i(mini(a.x, b.x), a.y))] = 1
	else:
		vlink[idx(Vector2i(a.x, mini(a.y, b.y)))] = 1


func _dig_line(a: Vector2i, b: Vector2i) -> void:
	var d := Vector2i(signi(b.x - a.x), signi(b.y - a.y))
	var c := a
	_dig_cell(c)
	while c != b:
		_dig_link(c, c + d)
		c += d
		_dig_cell(c)


# ------------------------------------------------------------------ the level

func _layout() -> void:
	open.resize(COLS * ROWS)
	open.fill(0)
	hlink.resize(COLS * ROWS)
	hlink.fill(0)
	vlink.resize(COLS * ROWS)
	vlink.fill(0)
	# the surface lane is open all along; the shaft from it to the middle
	_dig_line(Vector2i(0, 1), Vector2i(COLS - 1, 1))
	var mid := Vector2i(COLS / 2, 7)
	_dig_line(Vector2i(mid.x, 1), mid)
	hero = {"pos": Vector2(mid), "dir": 0, "moving": false, "digging": false, "dead": false, "face": 0, "aim": 0}
	# creatures in pockets of tunnel of their own
	var count := mini(4 + level / 2, 8)
	var drakes := clampi(1 + level / 3, 1, count / 2)
	var taken := {}
	for c in range(mid.x - 1, mid.x + 2):
		for r in range(1, 9):
			taken[Vector2i(c, r)] = true
	for i in count:
		for tries in 60:
			var horiz := rng.randf() < 0.6
			var length := rng.randi_range(3, 4)
			var a := Vector2i(rng.randi_range(0, COLS - (length if horiz else 1)), rng.randi_range(3, ROWS - (1 if horiz else length)))
			var b := a + (Vector2i(length - 1, 0) if horiz else Vector2i(0, length - 1))
			var ok := true
			for x in range(a.x - 1, b.x + 2):
				for y in range(a.y - 1, b.y + 2):
					if taken.has(Vector2i(x, y)):
						ok = false
			if not ok:
				continue
			for x in range(a.x - 1, b.x + 2):
				for y in range(a.y - 1, b.y + 2):
					taken[Vector2i(x, y)] = true
			_dig_line(a, b)
			var at := a if rng.randf() < 0.5 else b
			_spawn(at, "drake" if i < drakes else "puffer")
			break
	# rocks: in the earth, with earth under them
	var n_rocks := 3 + mini(level / 3, 2)
	for i in n_rocks:
		for tries in 60:
			var c := Vector2i(rng.randi_range(1, COLS - 2), rng.randi_range(3, ROWS - 4))
			if is_open(c) or is_open(c + Vector2i(0, 1)) or taken.has(c):
				continue
			var near := false
			for rk in rocks:
				if (rk["cell"] as Vector2i).distance_to(c) < 3.0:
					near = true
			if near:
				continue
			rocks.append({"cell": c, "y": float(c.y), "state": "rest", "t": 0.0, "id": i, "crushed": 0})
			break


func _spawn(c: Vector2i, kind: String) -> void:
	foes.append({"id": _next_id, "kind": kind, "pos": Vector2(c), "home": c, "dir": 0, "target": c, "ghost": false,
		"ghost_t": rng.randf_range(6.0, 12.0), "puff": 0.0, "puff_t": 0.0, "breath": 0.0, "fire_t": rng.randf_range(3.0, 7.0),
		"fleeing": false, "dead": false, "speed": 2.2 + level * 0.12 + rng.randf_range(-0.1, 0.1)})
	_next_id += 1


func hero_cell() -> Vector2i:
	var p: Vector2 = hero["pos"]
	return Vector2i(roundi(p.x), roundi(p.y))


# ------------------------------------------------------------------ the tick

func tick() -> void:
	time += TICK
	match phase:
		Phase.READY:
			phase_t -= TICK
			if phase_t <= 0.0:
				phase = Phase.PLAY
				event.emit("level", {"n": level + 1})
			return
		Phase.DYING:
			phase_t -= TICK
			_rocks()
			if phase_t <= 0.0:
				if lives <= 0:
					phase = Phase.OVER
					phase_t = 3.0
					event.emit("game_over", {})
				else:
					_restart()
			return
		Phase.CLEARED, Phase.OVER:
			phase_t -= TICK
			return
	# the hose aims where the stick points (or where he last faced); a shot doesn't take a step
	if want != Vector2i.ZERO:
		hero["aim"] = DIRS.find(want)
	if not (pump_pressed and hose.is_empty()):
		_move_hero()
	_pump()
	_foes()
	_rocks()
	_fires()
	_veg()
	_touch()
	var alive := foes.filter(func(f): return not f["dead"])
	if alive.is_empty():
		phase = Phase.CLEARED
		phase_t = 3.0
		event.emit("cleared", {})
	elif alive.size() == 1 and not alive[0]["fleeing"]:
		alive[0]["fleeing"] = true
		alive[0]["ghost"] = false
		event.emit("last", {"id": alive[0]["id"]})


## The hero walks the grid: along a row or a column, turning only at a cell's centre (asked to turn between two,
## he carries on to the next centre first), digging what he passes: the cell ahead and the link to it open once
## he is halfway there.
func _move_hero() -> void:
	var p: Vector2 = hero["pos"]
	hero["moving"] = false
	hero["digging"] = false
	if not hose.is_empty() and hose["id"] >= 0:
		return   # pumping: he stands
	if want == Vector2i.ZERO:
		return
	var cur: Vector2i = DIRS[hero["dir"]]
	var on_col := absf(p.x - roundf(p.x)) < 0.01      # free to go up and down
	var on_row := absf(p.y - roundf(p.y)) < 0.01      # free to go left and right
	var d := want
	if d.x != 0 and not on_row:
		d = cur if cur.y != 0 else Vector2i(0, 1 if roundf(p.y) > p.y else -1)
	elif d.y != 0 and not on_col:
		d = cur if cur.x != 0 else Vector2i(1 if roundf(p.x) > p.x else -1, 0)
	var nx := (floori(p.x + 0.001) + 1 if d.x > 0 else ceili(p.x - 0.001) - 1) if d.x != 0 else roundi(p.x)
	var ny := (floori(p.y + 0.001) + 1 if d.y > 0 else ceili(p.y - 0.001) - 1) if d.y != 0 else roundi(p.y)
	var next := Vector2i(nx, ny)
	var prev := next - d
	if not inside(next) or _rock_at(next):
		return
	var digging := not linked(prev, next)
	var target := Vector2(next)
	p = p.move_toward(target, (DIG_SPEED if digging else SPEED) * TICK)
	hero["pos"] = p
	hero["dir"] = DIRS.find(d)
	if d.x != 0:
		hero["face"] = 0 if d.x > 0 else 2
	hero["moving"] = true
	hero["digging"] = digging
	if digging and p.distance_to(target) < 0.5:
		_dig_cell(next)
		_dig_link(prev, next)
		event.emit("dig", {"cell": next})


func _pump() -> void:
	if not hose.is_empty():
		hose["t"] += TICK
		if hose["id"] >= 0:
			var f := _foe(hose["id"])
			if f.is_empty() or f["dead"]:
				hose = {}
			elif want != Vector2i.ZERO and want != DIRS[hose["dir"]]:
				hose = {}   # he walks away: the creature is let go
			elif pump_pressed:
				f["puff"] = minf(4.0, floorf(f["puff"]) + 1.0)
				f["puff_t"] = 0.0
				event.emit("pump", {"id": f["id"], "step": int(f["puff"])})
				if f["puff"] >= 4.0:
					_pop(f, hose["dir"])
					hose = {}
		elif hose["t"] > 0.35:
			hose = {}
	if pump_pressed and hose.is_empty() and phase == Phase.PLAY:
		_shoot()
	pump_pressed = false


## The hose runs along the hero's facing through open tunnel, up to HOSE cells; the first creature on it is caught.
func _shoot() -> void:
	var dir := int(hero.get("aim", hero["face"]))
	var d: Vector2 = Vector2(DIRS[dir])
	var p: Vector2 = hero["pos"]
	var reach := 0.0
	var caught := -1
	var step := 0.25
	var cur := Vector2i(roundi(p.x), roundi(p.y))
	while reach < HOSE:
		var q := p + d * (reach + step)
		var qc := Vector2i(roundi(q.x), roundi(q.y))
		if qc != cur:
			if not linked(cur, qc):
				break
			cur = qc
		reach += step
		for f in foes:
			if f["dead"] or f["ghost"]:
				continue
			if (f["pos"] as Vector2).distance_to(q) < 0.55:
				caught = f["id"]
				break
		if caught >= 0:
			break
	hose = {"dir": dir, "len": reach, "t": 0.0, "id": caught}
	event.emit("shoot", {"dir": dir, "len": reach})
	if caught >= 0:
		var f := _foe(caught)
		f["puff"] = maxf(f["puff"], 1.0)
		f["puff_t"] = 0.0
		event.emit("hook", {"id": caught})
		event.emit("pump", {"id": caught, "step": 1})
	else:
		event.emit("miss", {})


func _foe(id: int) -> Dictionary:
	for f in foes:
		if f["id"] == id:
			return f
	return {}


func _pop(f: Dictionary, dir: int) -> void:
	f["dead"] = true
	var pts: int = LAYER_POINTS[layer_of(roundi(f["pos"].y))]
	if f["kind"] == "drake" and DIRS[dir].x != 0:
		pts *= 2
	_score(pts)
	event.emit("pop", {"id": f["id"], "pos": f["pos"], "points": pts})


func _score(pts: int) -> void:
	score += pts
	if score >= _next_life:
		_next_life += 10000
		lives += 1
		event.emit("extra_life", {})


# ------------------------------------------------------------------ the creatures

## The walking distances to the hero over the open tunnels (cells), for the creatures to follow.
func _tunnel_field() -> Dictionary:
	var start := hero_cell()
	var dist := {start: 0}
	var q: Array[Vector2i] = [start]
	while not q.is_empty():
		var c: Vector2i = q.pop_front()
		for d in DIRS:
			var n: Vector2i = c + d
			if not dist.has(n) and linked(c, n):
				dist[n] = dist[c] + 1
				q.append(n)
	return dist


func _foes() -> void:
	var field := _tunnel_field()
	for f in foes:
		if f["dead"]:
			continue
		# a puffed creature can't move; it shrinks back when left alone
		if f["puff"] > 0.0:
			f["puff_t"] += TICK
			if hose.is_empty() or hose["id"] != f["id"]:
				if f["puff_t"] > 0.7:
					f["puff"] = maxf(0.0, f["puff"] - 1.0)
					f["puff_t"] = 0.0
			continue
		if f["breath"] > 0.0:
			f["breath"] -= TICK
			if f["breath"] <= 0.0:
				_breathe(f)
			continue
		var p: Vector2 = f["pos"]
		var sp: float = f["speed"]
		if f["ghost"]:
			# eyes drift straight for the hero through the earth, and take shape again in a tunnel near him
			var to: Vector2 = hero["pos"]
			p = p.move_toward(to, sp * 0.65 * TICK)
			f["pos"] = p
			f["ghost_t"] -= TICK
			var c := Vector2i(roundi(p.x), roundi(p.y))
			if f["ghost_t"] < -1.5 and is_open(c) and p.distance_to(Vector2(c)) < 0.08 and field.has(c):
				f["ghost"] = false
				f["ghost_t"] = rng.randf_range(8.0, 14.0)
				f["pos"] = Vector2(c)
				f["target"] = c
				event.emit("solid", {"id": f["id"]})
			elif f["ghost_t"] < -1.5 and is_open(c) and p.distance_to(Vector2(c)) < 0.3:
				f["pos"] = p.move_toward(Vector2(c), sp * TICK)
			continue
		var tgt: Vector2i = f["target"]
		if p.distance_to(Vector2(tgt)) < 0.01:
			p = Vector2(tgt)
			f["target"] = _next_cell(f, tgt, field)
			# a drake level with the hero, not too far, may take a breath
			f["fire_t"] -= 0.0
			if f["kind"] == "drake" and absi(tgt.y - hero_cell().y) == 0 and absi(tgt.x - hero_cell().x) <= 5 and f["fire_t"] <= 0.0 and not f["fleeing"]:
				f["breath"] = 0.6
				f["dir"] = 0 if hero["pos"].x > p.x else 2
				f["fire_t"] = rng.randf_range(3.0, 6.0)
				event.emit("breathe", {"id": f["id"]})
		else:
			p = p.move_toward(Vector2(tgt), sp * TICK)
			var dd: Vector2 = Vector2(tgt) - p
			if absf(dd.x) > 0.01:
				f["dir"] = 0 if dd.x > 0 else 2
		f["pos"] = p
		f["fire_t"] -= TICK
		# cut off from the hero for long enough: eyes through the earth
		if not field.has(Vector2i(roundi(p.x), roundi(p.y))) or rng.randf() < 0.0004:
			f["ghost_t"] -= TICK
		else:
			f["ghost_t"] -= TICK * 0.25
		if f["ghost_t"] <= 0.0 and not f["fleeing"] and p.distance_to(Vector2(f["target"])) < 0.02:
			f["ghost"] = true
			f["ghost_t"] = 0.0
			event.emit("ghost", {"id": f["id"]})
		# the last one runs off along the surface
		if f["fleeing"] and Vector2i(roundi(p.x), roundi(p.y)) == Vector2i(0, 1) and p.distance_to(Vector2(0, 1)) < 0.02:
			f["dead"] = true
			event.emit("escape", {"id": f["id"]})


## Where a creature goes from a cell: the open neighbour nearest the hero (or the surface's left end, for the last one
## running), sometimes a random one, never straight back unless it must.
func _next_cell(f: Dictionary, c: Vector2i, field: Dictionary) -> Vector2i:
	var options: Array[Vector2i] = []
	for d in DIRS:
		var n: Vector2i = c + d
		if linked(c, n) and not _rock_at(n):
			options.append(n)
	if options.is_empty():
		f["ghost_t"] = minf(f["ghost_t"], 0.5)
		return c
	var back: Vector2i = c - DIRS[f["dir"]] if f["dir"] in [0, 2] else c
	if f["fleeing"]:
		# up to the surface lane, then left
		var best := options[0]
		var bs := INF
		for n in options:
			var s := float(n.y) * 3.0 + float(n.x) if c.y > 1 else float(n.x)
			if s < bs:
				bs = s
				best = n
		return best
	if field.has(c) and rng.randf() < 0.8:
		var best := options[0]
		var bd := 1 << 20
		for n in options:
			var dd: int = field.get(n, 1 << 19)
			if dd < bd:
				bd = dd
				best = n
		return best
	if options.size() > 1:
		options.erase(back)
	return options[rng.randi() % options.size()]


func _rock_at(c: Vector2i) -> bool:
	for rk in rocks:
		if rk["state"] != "gone" and Vector2i(rk["cell"]) == c:
			return true
	return false


func _breathe(f: Dictionary) -> void:
	var p: Vector2 = f["pos"]
	var d := 1.0 if f["dir"] == 0 else -1.0
	var to := Vector2(clampf(p.x + d * 3.5, 0.0, COLS - 1.0), p.y)
	fires.append({"from": p + Vector2(d * 0.5, 0), "to": to, "t": 0.0, "id": f["id"]})
	event.emit("fire", {"id": f["id"], "from": p, "to": to})


func _fires() -> void:
	for fr in fires:
		fr["t"] += TICK
	fires = fires.filter(func(fr): return fr["t"] < 0.55)


# ------------------------------------------------------------------ rocks, the vegetable, touches

func _rocks() -> void:
	for rk in rocks:
		var c: Vector2i = rk["cell"]
		match rk["state"]:
			"rest":
				var below := c + Vector2i(0, 1)
				if is_open(below) and hero_cell() != below:
					rk["state"] = "wobble"
					rk["t"] = 0.0
					event.emit("wobble", {"rock": rk["id"]})
			"wobble":
				rk["t"] += TICK
				if rk["t"] > 0.7:
					rk["state"] = "fall"
					rk["crushed"] = 0
					event.emit("fall", {"rock": rk["id"]})
			"fall":
				rk["y"] += 7.5 * TICK
				var cy := floori(rk["y"])
				var under := Vector2i(c.x, cy + 1)
				var rp := Vector2(c.x, rk["y"])
				# it crushes what it meets
				for f in foes:
					if not f["dead"] and not f["ghost"] and (f["pos"] as Vector2).distance_to(rp + Vector2(0, 0.5)) < 0.7:
						f["dead"] = true
						var pts: int = CRUSH_POINTS[mini(rk["crushed"], CRUSH_POINTS.size() - 1)]
						rk["crushed"] += 1
						_score(pts)
						event.emit("crush", {"id": f["id"], "points": pts, "pos": f["pos"]})
				if phase == Phase.PLAY and (hero["pos"] as Vector2).distance_to(rp + Vector2(0, 0.5)) < 0.7:
					_die("crushed")
				if not is_open(under) or under.y >= ROWS:
					rk["y"] = float(cy)
					rk["cell"] = Vector2i(c.x, cy)
					rk["state"] = "land"
					rk["t"] = 0.0
					dropped += 1
					event.emit("land", {"rock": rk["id"], "crushed": rk["crushed"]})
					if dropped == 2 and veg.is_empty():
						veg = {"pos": Vector2(COLS / 2, 7), "t": 0.0, "kind": mini(level, VEG_POINTS.size() - 1)}
						event.emit("veg", {"pos": veg["pos"]})
			"land":
				rk["t"] += TICK
				if rk["t"] > 0.6:
					rk["state"] = "gone"


func _veg() -> void:
	if veg.is_empty():
		return
	veg["t"] += TICK
	if (hero["pos"] as Vector2).distance_to(veg["pos"]) < 0.6:
		var pts: int = VEG_POINTS[veg["kind"]]
		_score(pts)
		event.emit("veg_take", {"points": pts, "pos": veg["pos"]})
		veg = {"taken": true}
	elif veg["t"] > 10.0:
		veg = {"taken": true}


func _touch() -> void:
	var p: Vector2 = hero["pos"]
	for f in foes:
		if f["dead"] or f["puff"] > 0.0:
			continue
		if (f["pos"] as Vector2).distance_to(p) < 0.6 and not f["ghost"]:
			_die("caught")
			return
	for fr in fires:
		if fr["t"] < 0.15:
			continue
		var a: Vector2 = fr["from"]
		var b: Vector2 = fr["to"]
		if absf(p.y - a.y) < 0.5 and p.x >= minf(a.x, b.x) - 0.3 and p.x <= maxf(a.x, b.x) + 0.3:
			_die("burnt")
			return


func _die(how: String) -> void:
	if phase != Phase.PLAY:
		return
	lives -= 1
	phase = Phase.DYING
	phase_t = 2.5
	hose = {}
	event.emit("die", {"pos": hero["pos"], "how": how})


## After a life is lost: the hero back in the middle, the creatures back home.
func _restart() -> void:
	hero["pos"] = Vector2(COLS / 2, 7)
	hero["dir"] = 0
	for f in foes:
		if not f["dead"]:
			f["pos"] = Vector2(f["home"])
			f["target"] = f["home"]
			f["ghost"] = false
			f["puff"] = 0.0
			f["breath"] = 0.0
			f["ghost_t"] = rng.randf_range(6.0, 12.0)
	fires.clear()
	phase = Phase.READY
	phase_t = 1.5
