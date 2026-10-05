class_name BloomEngine
extends RefCounted
## Bloomwand rules (a single-screen fairy platformer in the Rod Land tradition; our own tuning), 60 Hz ticks. One or
## two fairies on a screen of blocks and ladders (x right, y up, a tile a unit; the fairy's position is her feet).
## Fairies walk, fall off edges, climb ladders, and (pushing up where there is no ladder) conjure a magic ladder up to
## the platform above (up to six tiles; it fades once left). They cannot jump. The wand's beam reaches three tiles
## ahead and catches the first creature: held over her head, it is slammed down in front and behind by itself,
## each slam a hit (and a knock to any creature it lands on); out of hits it bursts into a fruit, sometimes a letter
## bubble. Flowers are picked by walking through them; all of them before the last creature goes is a big bonus.
## E X T R A in letters is an extra life. A creature's touch costs a life. After a while the creatures hurry.
## Events: "cast" {p}, "catch" {p, id}, "slam" {p, id, side}, "hit" {id}, "pop" {id, pos, points}, "fruit" {pos, kind},
## "take" {p, kind, points}, "flower" {p, pos}, "bloom" (all flowers), "letter" {p, letter}, "extra" {p},
## "ladder" {p, x, from, to}, "die" {p, pos}, "hurry", "cleared", "game_over".

signal event(kind: String, data: Dictionary)

enum Phase { READY, PLAY, CLEARED, OVER }
const TICK := 1.0 / 60.0
const WALK := 3.6
const CLIMB := 3.0
const GRAV := 24.0
const HALF := 0.3
const TALL := 0.9
const REACH := 3.0
const SLAM_EVERY := 0.4
const HURRY_AT := 60.0
const HP := {"g": 3, "b": 3, "s": 4, "c": 2}
const SPEEDS := {"g": 1.3, "b": 1.8, "s": 2.4, "c": 1.0}
const FRUITS := ["cherry", "pear", "grapes", "cake", "crystal"]
const LETTERS := ["E", "X", "T", "R", "A"]

var lv: BloomLevel
var phase := Phase.READY
var phase_t := 2.0
var time := 0.0
var fairies: Array[Dictionary] = []
var foes: Array[Dictionary] = []
var flowers: Array[Vector2] = []
var flowers_total := 0
var items: Array[Dictionary] = []       ## fruit and letter bubbles: {pos, kind, vy, t}
var magic: Array[Dictionary] = []       ## magic ladders: {x (column), y0, y1, owner, life}
var hurry := false
var rng := RandomNumberGenerator.new()
var _next_id := 0


## `players` holds one or two dictionaries {score, lives, letters} carried over from the last level.
func _init(level: BloomLevel, players: Array, seed_ := 1) -> void:
	lv = level
	rng.seed = seed_
	var starts := []
	for row in BloomLevel.H:
		for x in BloomLevel.W:
			var ch := lv.at(x, row)
			var p := Vector2(x + 0.5, BloomLevel.H - 1 - row)
			match ch:
				"P": starts.push_front(p)
				"Q": starts.append(p)
				"*": flowers.append(p + Vector2(0, 0.3))
				"g", "b", "s", "c":
					foes.append({"id": _next_id, "kind": ch, "pos": p, "vy": 0.0, "dir": 1 if rng.randf() < 0.5 else -1, "hp": HP[ch],
						"held_by": -1, "stun": 0.0, "climb": 0, "climb_t": 0.0, "dead": false})
					_next_id += 1
	flowers_total = flowers.size()
	if starts.size() < 2:
		starts.append(starts[0] + Vector2(1.0, 0) if not solid_at(starts[0].x + 1.0, starts[0].y + 0.4) else starts[0])
	for i in players.size():
		var pl: Dictionary = players[i]
		fairies.append({"i": i, "pos": starts[i], "start": starts[i], "vy": 0.0, "face": 1, "climbing": false, "move": 0, "climb_in": 0,
			"cast_pressed": false, "cast_held": false, "ladder_pressed": false, "beam": 0.0, "holding": -1, "slam_t": 0.0, "side": 1,
			"dead": false, "dead_t": 0.0, "safe": 2.0, "score": pl.get("score", 0), "lives": pl.get("lives", 3),
			"letters": pl.get("letters", []).duplicate(), "anim": "idle"})


# ------------------------------------------------------------------ the grid

func tile(x: float, y: float) -> String:
	return lv.at(floori(x), BloomLevel.H - 1 - floori(y))


func solid_at(x: float, y: float) -> bool:
	return y < 0.0 or tile(x, y) == "#"


func ladder_at(x: float, y: float) -> bool:
	if tile(x, y) == "H":
		return true
	var col := floori(x)
	for m in magic:
		if m["x"] == col and y >= m["y0"] - 0.01 and y < m["y1"]:
			return true
	return false


## Whether a body at feet (x, y) stands on something: a block, or the top of a ladder.
func standing(x: float, y: float) -> bool:
	for dx in [-HALF + 0.05, HALF - 0.05]:
		if solid_at(x + dx, y - 0.02) and absf(y - roundf(y)) < 0.05:
			return true
	return absf(y - roundf(y)) < 0.05 and ladder_at(x, y - 0.5) and not ladder_at(x, y + 0.2)


# ------------------------------------------------------------------ the tick

func tick() -> void:
	time += TICK
	match phase:
		Phase.READY:
			phase_t -= TICK
			if phase_t <= 0.0:
				phase = Phase.PLAY
			return
		Phase.CLEARED, Phase.OVER:
			phase_t -= TICK
			_items()
			return
	if not hurry and time > HURRY_AT:
		hurry = true
		event.emit("hurry", {})
	for f in fairies:
		_fairy(f)
	_magic()
	_foes()
	_items()
	_touch()
	if foes.filter(func(f): return not f["dead"]).is_empty():
		phase = Phase.CLEARED
		phase_t = 3.5
		if flowers.is_empty() and flowers_total > 0:
			for f in fairies:
				_score(f, 3000)
		event.emit("cleared", {})


func _fairy(f: Dictionary) -> void:
	if f["dead"]:
		f["dead_t"] -= TICK
		if f["dead_t"] <= 0.0:
			if f["lives"] > 0:
				f["dead"] = false
				f["pos"] = f["start"]
				f["vy"] = 0.0
				f["safe"] = 2.5
				f["climbing"] = false
			elif fairies.all(func(g): return g["dead"] and g["lives"] <= 0):
				phase = Phase.OVER
				phase_t = 3.0
				event.emit("game_over", {})
		f["cast_pressed"] = false
		f["ladder_pressed"] = false
		return
	f["safe"] = maxf(0.0, f["safe"] - TICK)
	var p: Vector2 = f["pos"]
	# holding a creature: slam it to and fro while the wand is held; let go and it drops
	if f["holding"] >= 0:
		var c := _foe(f["holding"])
		if c.is_empty() or c["dead"]:
			f["holding"] = -1
		else:   # a caught creature is slammed to and fro by itself until it bursts
			f["slam_t"] += TICK
			c["pos"] = p + Vector2(0, 1.0)
			if f["slam_t"] >= SLAM_EVERY:
				f["slam_t"] = 0.0
				f["side"] = -f["side"]
				_slam(f, c)
		f["cast_pressed"] = false
		f["ladder_pressed"] = false
		f["anim"] = "hold"
		return
	# the beam
	f["beam"] = maxf(0.0, f["beam"] - TICK)
	if f["cast_pressed"]:
		_cast(f)   # from a ladder too: the beam runs along the row
	f["cast_pressed"] = false
	# up where there's no ladder: a rainbow ladder to the floor above
	if (f["ladder_pressed"] or (f["climb_in"] > 0 and not ladder_at(p.x, p.y + 0.1))) and standing(p.x, p.y) and not f["climbing"]:
		_conjure(f)
	f["ladder_pressed"] = false
	# climbing
	var col_x := floorf(p.x) + 0.5
	var on_ladder := ladder_at(p.x, p.y + 0.1) or ladder_at(p.x, p.y - 0.1)
	if f["climb_in"] != 0 and (on_ladder or (f["climb_in"] < 0 and ladder_at(p.x, p.y - 0.5))) and absf(p.x - col_x) < 0.35:
		f["climbing"] = true
	if f["climbing"]:
		p.x = move_toward(p.x, col_x, 6.0 * TICK)
		var dy: float = f["climb_in"] * CLIMB * TICK
		var ny := p.y + dy
		if f["climb_in"] > 0 and not ladder_at(p.x, ny) and not ladder_at(p.x, ny + 0.4):
			ny = ceilf(p.y - 0.001)   # the top: step off onto the platform
			f["climbing"] = false
		if f["climb_in"] < 0 and solid_at(p.x, ny - 0.01) and not ladder_at(p.x, ny - 0.5):
			ny = roundf(p.y)
			f["climbing"] = false
		if not ladder_at(p.x, ny + 0.1) and not ladder_at(p.x, ny - 0.4) and f["climbing"]:
			f["climbing"] = false
		p.y = ny
		f["vy"] = 0.0
		# sideways: step off onto a floor she is (nearly) level with, or let go and drop
		if f["move"] != 0 and f["climb_in"] == 0:
			if absf(p.y - roundf(p.y)) < 0.45 and standing(p.x, roundf(p.y)):
				p.y = roundf(p.y)
			f["climbing"] = false
		f["anim"] = "climb"
	if not f["climbing"]:
		# walking and falling
		if f["move"] != 0:
			f["face"] = f["move"]
			var nx: float = p.x + f["move"] * WALK * TICK
			var edge: float = nx + f["move"] * HALF
			if not solid_at(edge, p.y + 0.1) and not solid_at(edge, p.y + TALL - 0.1):
				p.x = nx
		if standing(p.x, p.y):
			f["vy"] = 0.0
			p.y = roundf(p.y)
			f["anim"] = "walk" if f["move"] != 0 else "idle"
		else:
			f["vy"] = maxf(f["vy"] - GRAV * TICK, -12.0)
			var ny: float = p.y + f["vy"] * TICK
			if f["vy"] < 0.0 and (solid_at(p.x - HALF + 0.05, ny) or solid_at(p.x + HALF - 0.05, ny) or (ladder_at(p.x, ny - 0.02) and not ladder_at(p.x, floorf(p.y) + 0.5) and floorf(p.y) != floorf(ny))):
				ny = floorf(p.y) if floorf(ny) != floorf(p.y) else ny
				ny = roundf(ny) if absf(ny - roundf(ny)) < 0.3 else ceilf(ny)
				f["vy"] = 0.0
			p.y = ny
			f["anim"] = "fall"
	p.x = clampf(p.x, HALF, BloomLevel.W - HALF)
	f["pos"] = p
	# flowers, fruit and letters
	for fl in flowers.duplicate():
		if fl.distance_to(p + Vector2(0, 0.45)) < 0.6:
			flowers.erase(fl)
			_score(f, 100)
			event.emit("flower", {"p": f["i"], "pos": fl})
			if flowers.is_empty():
				event.emit("bloom", {})
	for it in items.duplicate():
		if (it["pos"] as Vector2).distance_to(p + Vector2(0, 0.45)) < 0.65 and it["t"] > 0.4:
			items.erase(it)
			if it["kind"].length() == 1:
				if not f["letters"].has(it["kind"]):
					f["letters"].append(it["kind"])
				_score(f, 500)
				event.emit("letter", {"p": f["i"], "letter": it["kind"]})
				if f["letters"].size() >= LETTERS.size():
					f["letters"].clear()
					f["lives"] += 1
					event.emit("extra", {"p": f["i"]})
			else:
				var pts: int = [500, 700, 1000, 2000, 3000][FRUITS.find(it["kind"])]
				_score(f, pts)
				event.emit("take", {"p": f["i"], "kind": it["kind"], "points": pts})


func _score(f: Dictionary, pts: int) -> void:
	f["score"] += pts


## The beam: three tiles ahead at body height; the first creature in it is caught.
func _cast(f: Dictionary) -> void:
	f["beam"] = 0.25
	var p: Vector2 = f["pos"]
	event.emit("cast", {"p": f["i"]})
	var best := {}
	var bd := INF
	for c in foes:
		if c["dead"] or c["held_by"] >= 0:
			continue
		var d: Vector2 = c["pos"] - p
		if d.x * f["face"] > -0.2 and absf(d.x) < REACH + 0.4 and absf(d.y) < 0.7:
			# blocks stop the beam
			var clear := true
			var k := 0.5
			while k < absf(d.x):
				if solid_at(p.x + f["face"] * k, p.y + 0.5):
					clear = false
				k += 0.5
			if clear and absf(d.x) < bd:
				bd = absf(d.x)
				best = c
	if not best.is_empty():
		best["held_by"] = f["i"]
		f["holding"] = best["id"]
		f["slam_t"] = SLAM_EVERY * 0.5
		f["side"] = f["face"]
		event.emit("catch", {"p": f["i"], "id": best["id"]})


func _slam(f: Dictionary, c: Dictionary) -> void:
	var p: Vector2 = f["pos"]
	var at := p + Vector2(f["side"] * 1.0, 0.0)
	c["hp"] -= 1
	event.emit("slam", {"p": f["i"], "id": c["id"], "side": f["side"], "pos": at})
	# it lands on whatever is there
	for o in foes:
		if o["dead"] or o["id"] == c["id"] or o["held_by"] >= 0:
			continue
		if (o["pos"] as Vector2).distance_to(at) < 1.1:
			o["hp"] -= 1
			o["stun"] = 1.2
			event.emit("hit", {"id": o["id"]})
			if o["hp"] <= 0:
				_pop(f, o)
	if c["hp"] <= 0:
		_pop(f, c)
		f["holding"] = -1


func _pop(f: Dictionary, c: Dictionary) -> void:
	c["dead"] = true
	c["held_by"] = -1
	var pts: int = {"g": 200, "b": 300, "s": 500, "c": 400}[c["kind"]]
	_score(f, pts)
	var at: Vector2 = c["pos"]
	event.emit("pop", {"id": c["id"], "pos": at, "points": pts})
	# a fruit, or now and then a letter the fairy hasn't got yet
	var missing: Array = LETTERS.filter(func(l): return not f["letters"].has(l))
	var kind: String = FRUITS[mini(rng.randi() % 3 + (1 if hurry else 0), FRUITS.size() - 1)]
	if not missing.is_empty() and rng.randf() < 0.35:
		kind = missing[rng.randi() % missing.size()]
	items.append({"pos": at + Vector2(0, 0.5), "kind": kind, "vy": 4.0, "t": 0.0})
	event.emit("fruit", {"pos": at, "kind": kind})


## A magic ladder from her feet up to the next floor above (within six tiles), if there is one.
func _conjure(f: Dictionary) -> void:
	var p: Vector2 = f["pos"]
	var col := floori(p.x)
	var y := roundi(p.y)
	for up in range(2, 8):
		var ty := y + up
		if ty >= BloomLevel.H:
			break
		if solid_at(col + 0.5, ty - 1 + 0.5) and not solid_at(col + 0.5, ty + 0.5):
			magic.append({"x": col, "y0": float(y), "y1": float(ty), "owner": f["i"], "life": 2.5})
			f["pos"] = Vector2(col + 0.5, p.y)
			f["climbing"] = true
			event.emit("ladder", {"p": f["i"], "x": col, "from": y, "to": ty})
			return


func _magic() -> void:
	for m in magic:
		var used := false
		for f in fairies:
			var p: Vector2 = f["pos"]
			if floori(p.x) == m["x"] and p.y >= m["y0"] - 0.1 and p.y <= m["y1"] + 0.1 and f["climbing"]:
				used = true
		if not used:
			m["life"] -= TICK
	magic = magic.filter(func(m): return m["life"] > 0.0)


# ------------------------------------------------------------------ creatures

func _foe(id: int) -> Dictionary:
	for c in foes:
		if c["id"] == id:
			return c
	return {}


func _foes() -> void:
	for c in foes:
		if c["dead"] or c["held_by"] >= 0:
			continue
		if c["stun"] > 0.0:
			c["stun"] -= TICK
			_fall(c)
			continue
		var p: Vector2 = c["pos"]
		var sp: float = SPEEDS[c["kind"]] * (1.45 if hurry else 1.0)
		if c["kind"] == "c":
			# the cloudlet drifts for the nearest fairy, through anything
			var tgt := _nearest_fairy(p)
			if not tgt.is_empty():
				c["pos"] = p.move_toward(tgt["pos"] + Vector2(0, 0.2), sp * TICK)
				c["dir"] = 1 if tgt["pos"].x > p.x else -1
			continue
		if c["climb"] != 0:
			p.x = move_toward(p.x, floorf(p.x) + 0.5, 4.0 * TICK)
			p.y += c["climb"] * sp * 0.8 * TICK
			c["climb_t"] -= TICK
			if (c["climb"] > 0 and not ladder_at(p.x, p.y) and not ladder_at(p.x, p.y + 0.3)) or (c["climb"] < 0 and solid_at(p.x, p.y - 0.02)):
				p.y = roundf(p.y)
				c["climb"] = 0
			c["pos"] = p
			continue
		if not standing(p.x, p.y):
			_fall(c)
			continue
		# at a ladder, sometimes take it (more often toward a fairy)
		var tgt := _nearest_fairy(p)
		if absf(p.x - (floorf(p.x) + 0.5)) < 0.06 and c["climb_t"] <= 0.0:
			var want_up: bool = not tgt.is_empty() and tgt["pos"].y > p.y + 0.5
			var want_down: bool = not tgt.is_empty() and tgt["pos"].y < p.y - 0.5
			if ladder_at(p.x, p.y + 0.5) and (want_up and rng.randf() < 0.6 or rng.randf() < 0.15):
				c["climb"] = 1
				c["climb_t"] = 2.0
				continue
			if ladder_at(p.x, p.y - 0.5) and (want_down and rng.randf() < 0.6 or rng.randf() < 0.15):
				c["climb"] = -1
				c["climb_t"] = 2.0
				continue
			c["climb_t"] = 0.5
		c["climb_t"] -= TICK
		var nx: float = p.x + c["dir"] * sp * TICK
		var ahead: float = nx + c["dir"] * HALF
		# turn at walls, and at edges (a bopper sometimes hops down instead)
		var wall := solid_at(ahead, p.y + 0.3)
		var edge := not solid_at(ahead, p.y - 0.1) and not ladder_at(ahead, p.y - 0.5)
		if wall or (edge and not (c["kind"] == "b" and rng.randf() < 0.004)):
			c["dir"] = -c["dir"]
		else:
			p.x = nx
		# snappers turn towards a fairy on their floor
		if c["kind"] == "s" and not tgt.is_empty() and absf(tgt["pos"].y - p.y) < 0.3 and rng.randf() < 0.02:
			c["dir"] = 1 if tgt["pos"].x > p.x else -1
		c["pos"] = p


func _fall(c: Dictionary) -> void:
	var p: Vector2 = c["pos"]
	if standing(p.x, p.y) or c["kind"] == "c":
		c["vy"] = 0.0
		return
	c["vy"] = maxf(c["vy"] - GRAV * TICK, -12.0)
	var ny: float = p.y + c["vy"] * TICK
	if solid_at(p.x, ny):
		ny = ceilf(ny)
		c["vy"] = 0.0
	c["pos"] = Vector2(p.x, ny)


func _nearest_fairy(p: Vector2) -> Dictionary:
	var best := {}
	var bd := INF
	for f in fairies:
		if f["dead"]:
			continue
		var d := (f["pos"] as Vector2).distance_to(p)
		if d < bd:
			bd = d
			best = f
	return best


func _items() -> void:
	for it in items:
		it["t"] += TICK
		var p: Vector2 = it["pos"]
		if it["kind"].length() == 1:
			p.y += sin(it["t"] * 2.0) * 0.004   # letter bubbles float
		else:
			it["vy"] = maxf(it["vy"] - GRAV * TICK, -10.0)
			var ny: float = p.y + it["vy"] * TICK
			if solid_at(p.x, ny - 0.3) and it["vy"] < 0.0:
				ny = floorf(ny - 0.3) + 1.3
				it["vy"] = 0.0
			p.y = ny
		it["pos"] = p
	items = items.filter(func(it): return it["t"] < 12.0)


func _touch() -> void:
	for f in fairies:
		if f["dead"] or f["safe"] > 0.0:
			continue
		for c in foes:
			if c["dead"] or c["held_by"] >= 0 or c["stun"] > 0.0:
				continue
			if ((c["pos"] as Vector2) - (f["pos"] as Vector2)).length() < 0.62:
				f["dead"] = true
				f["dead_t"] = 2.0
				f["lives"] -= 1
				if f["holding"] >= 0:
					var h := _foe(f["holding"])
					if not h.is_empty():
						h["held_by"] = -1
					f["holding"] = -1
				event.emit("die", {"p": f["i"], "pos": f["pos"]})
				break
