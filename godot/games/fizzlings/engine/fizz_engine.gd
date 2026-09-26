class_name FizzEngine
extends RefCounted
## Fizzlings rules (a single-screen bubble platformer in the Bubble Bobble tradition; our own tuning), 60 Hz ticks.
## A level is 32 x 26 tiles; positions are in tiles, y down, a body's (x, y) is the middle of its feet. Platforms can
## be jumped through from below and stood on from above; the side walls are solid; what falls out of the bottom comes
## back in at the top. Heroes blow bubbles that fly a short way, then float up and drift; a bubble that meets a toy
## traps it. Touching a bubble pops it (jumping on one bounces you off instead, if you hold jump); popping sets off the
## bubbles touching it, so a chain of trapped toys pays a lot. A popped toy becomes a treat. A trapped toy left too
## long breaks out, angry. After a while the toys turn angry, then a ghost comes for the slowest hero.
## Events: "blow" {p}, "jump" {p}, "trap" {pos}, "pop" {pos, n (in the chain), trapped}, "treat_drop" {pos, kind},
## "treat" {p, pos, points}, "angry", "hurry", "ghost", "die" {p, pos}, "cleared", "game_over", "extra_life", "escape".

signal event(kind: String, data: Dictionary)

enum Phase { READY, PLAY, CLEARED, OVER }
const TICK := 1.0 / 60.0
const W := 32
const H := 26
const GRAV := 60.0
const JUMP_V := -25.5
const WALK := 6.5
const HALF_W := 0.75        ## a body's half width
const TALL := 1.7
const BUBBLE_R := 0.85
const TREATS := ["cherry", "melon", "cupcake", "icecream", "gem", "crown"]
const TREAT_POINTS := {"cherry": 100, "melon": 300, "cupcake": 500, "icecream": 1000, "gem": 2000, "crown": 5000}
const CHAIN_POINTS := [1000, 2000, 4000, 8000, 16000, 32000, 64000]

var level: FizzLevel
var stage := 0
var rng := RandomNumberGenerator.new()
var phase := Phase.READY
var phase_t := 2.0
var time := 0.0
var solid := PackedByteArray()
var heroes: Array[Dictionary] = []    ## {p, pos, vel, facing, ground, lives, score, dead_t, blow_cool, inv, want_x, jump, blow}
var bubbles: Array[Dictionary] = []   ## {id, pos, vel, age, fly, trapped (toy dict or {}), life}
var toys: Array[Dictionary] = []      ## {id, kind, pos, vel, facing, ground, angry, think, flyer}
var treats: Array[Dictionary] = []    ## {pos, vel, kind, ground, age}
var ghost := {}
var hurried := false
var _next_id := 1
var _clear_t := 0.0


func _init(lv: FizzLevel, stage_ := 0, seed_ := 1, players := 1, carry: Array = []) -> void:
	level = lv
	stage = stage_
	rng.seed = seed_
	solid = lv.solid.duplicate()
	for i in players:
		var start: Vector2 = lv.starts[mini(i, lv.starts.size() - 1)]
		var h := {"p": i, "pos": start, "vel": Vector2.ZERO, "facing": 1 if i == 0 else -1, "ground": true,
			"lives": 3, "score": 0, "dead_t": 0.0, "blow_cool": 0.0, "inv": 2.0, "want_x": 0.0, "jump": false,
			"blow": false, "alive": true, "next_life": 30000}
		if i < carry.size():
			h["lives"] = carry[i]["lives"]
			h["score"] = carry[i]["score"]
			h["next_life"] = carry[i]["next_life"]
			h["alive"] = carry[i]["lives"] > 0
		heroes.append(h)
	for t in lv.toys:
		toys.append({"id": _id(), "kind": t["kind"], "pos": t["pos"], "vel": Vector2.ZERO, "facing": -1 if t["pos"].x > W * 0.5 else 1,
			"ground": false, "angry": false, "think": rng.randf_range(0.2, 1.0), "flyer": t["kind"] == "flyer",
			"speed": 3.2 + minf(stage, 8) * 0.15})
		if t["kind"] == "flyer":
			toys.back()["vel"] = Vector2(1, 1).normalized() * 4.0


func _id() -> int:
	_next_id += 1
	return _next_id


func is_solid(tx: int, ty: int) -> bool:
	if tx < 0 or tx >= W:
		return true
	ty = posmod(ty, H)
	return solid[ty * W + tx] == 1


## Side walls (the outer columns) block sideways; everything else is a platform you stand on from above.
func _wall(tx: int, ty: int) -> bool:
	if tx <= 1 or tx >= W - 2:
		return true
	return false


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
			_move_treats()
			for h in heroes:
				_move_hero(h)
				_collect(h)
			return
	for h in heroes:
		_move_hero(h)
	_move_bubbles()
	_move_toys()
	_move_treats()
	_move_ghost()
	for h in heroes:
		_collide(h)
		_collect(h)
	if not hurried and time > 30.0 + level.hurry_extra:
		hurried = true
		for t in toys:
			t["angry"] = true
		event.emit("hurry", {})
		event.emit("angry", {})
	if ghost.is_empty() and time > 45.0 + level.hurry_extra and not toys.is_empty():
		ghost = {"pos": Vector2(W * 0.5, 2.0), "vel": Vector2.ZERO}
		event.emit("ghost", {})
	var trapped_left := bubbles.any(func(b): return not b["trapped"].is_empty())
	if toys.is_empty() and not trapped_left:
		_clear_t += TICK
		if _clear_t > (3.0 if not treats.is_empty() else 1.2):
			phase = Phase.CLEARED
			phase_t = 2.5
			ghost = {}
			event.emit("cleared", {})
	if heroes.all(func(h): return h["lives"] <= 0 and not h["alive"]):
		phase = Phase.OVER
		phase_t = 3.0
		event.emit("game_over", {})


# ------------------------------------------------------------------ bodies

## Moves a body with gravity: side walls stop it, platforms catch it from above. Returns whether it stands.
func _body(pos: Vector2, vel: Vector2, dt: float) -> Array:
	var p := pos
	var v := vel
	v.y = minf(v.y + GRAV * dt, 18.0)
	# sideways
	var nx := p.x + v.x * dt
	var side := int(floor(nx + signf(v.x) * HALF_W)) if v.x != 0.0 else -99
	if v.x != 0.0 and (_wall(side, int(floor(p.y - 0.5))) or _wall(side, int(floor(p.y - 1.2)))):
		v.x = 0.0
	else:
		p.x = nx
	# down: land on the top of a platform tile, only when falling onto it
	var ground := false
	var ny := p.y + v.y * dt
	if v.y >= 0.0:
		var row_before := int(floor(p.y - 0.001))
		var row_after := int(floor(ny))
		for row in range(row_before + 1, row_after + 1):
			var hit := false
			for tx in [int(floor(p.x - HALF_W + 0.1)), int(floor(p.x)), int(floor(p.x + HALF_W - 0.1))]:
				if is_solid(tx, row) and not is_solid(tx, row - 1):
					hit = true
			if hit:
				ny = float(row)
				v.y = 0.0
				ground = true
				break
	p.y = ny
	# out of the bottom, back at the top
	if p.y > H + 1.0:
		p.y -= H + 1.0
	return [p, v, ground]


func _move_hero(h: Dictionary) -> void:
	if not h["alive"]:
		if h["lives"] > 0:
			h["dead_t"] -= TICK
			if h["dead_t"] <= 0.0:
				h["alive"] = true
				h["pos"] = level.starts[mini(h["p"], level.starts.size() - 1)]
				h["vel"] = Vector2.ZERO
				h["inv"] = 2.5
		return
	h["inv"] = maxf(0.0, h["inv"] - TICK)
	h["blow_cool"] = maxf(0.0, h["blow_cool"] - TICK)
	var v: Vector2 = h["vel"]
	v.x = h["want_x"] * WALK
	if h["want_x"] != 0.0:
		h["facing"] = int(signf(h["want_x"]))
	if h["jump"] and h["ground"]:
		v.y = JUMP_V
		h["ground"] = false
		event.emit("jump", {"p": h["p"]})
	var r := _body(h["pos"], v, TICK)
	h["pos"] = r[0]
	h["vel"] = r[1]
	h["ground"] = r[2]
	if h["blow"] and h["blow_cool"] <= 0.0 and phase == Phase.PLAY:
		h["blow_cool"] = 0.3
		bubbles.append({"id": _id(), "pos": h["pos"] + Vector2(h["facing"] * 0.9, -0.9), "vel": Vector2(h["facing"] * 16.0, 0.0),
			"age": 0.0, "fly": 0.32, "trapped": {}, "life": 9.0 + rng.randf() * 2.0, "owner": h["p"]})
		event.emit("blow", {"p": h["p"]})
	h["blow"] = false


# ------------------------------------------------------------------ bubbles

func _move_bubbles() -> void:
	for b in bubbles.duplicate():
		b["age"] += TICK
		var p: Vector2 = b["pos"]
		var v: Vector2 = b["vel"]
		if b["age"] < b["fly"]:
			# flying out: stops at walls, traps the first toy it meets
			p += v * TICK
			if p.x < 2.0 + BUBBLE_R or p.x > W - 2.0 - BUBBLE_R:
				p.x = clampf(p.x, 2.0 + BUBBLE_R, W - 2.0 - BUBBLE_R)
				b["age"] = b["fly"]
			if b["trapped"].is_empty():
				for t in toys:
					if (t["pos"] + Vector2(0, -0.8)).distance_to(p) < BUBBLE_R + 0.6:
						b["trapped"] = t
						b["life"] = maxf(6.0, 10.0 - stage * 0.2)
						b["age"] = b["fly"]
						toys.erase(t)
						event.emit("trap", {"pos": p})
						break
		else:
			# floating: up to the ceiling, then drift towards the middle, jostling the others
			var target := Vector2(W * 0.5 + sin(b["id"] * 1.7) * 6.0, 3.0 + (b["id"] % 3) * 1.2)
			var drift := (target - p)
			v = v.lerp(Vector2(clampf(drift.x, -2.0, 2.0), clampf(drift.y, -3.0, 1.0)), minf(1.0, TICK * 3.0))
			v += Vector2(sin(time * 2.0 + b["id"]), cos(time * 1.7 + b["id"])) * 0.02
			for o in bubbles:
				if o != b:
					var d: Vector2 = p - o["pos"]
					var l := d.length()
					if l < BUBBLE_R * 1.9 and l > 0.001:
						v += d / l * (BUBBLE_R * 1.9 - l) * 0.5
			p += v * TICK
			p.x = clampf(p.x, 2.0 + BUBBLE_R, W - 2.0 - BUBBLE_R)
		b["pos"] = p
		b["vel"] = v
		b["life"] -= TICK
		if b["life"] <= 0.0:
			if not b["trapped"].is_empty():
				# it breaks out, angry
				var t: Dictionary = b["trapped"]
				t["pos"] = p + Vector2(0, 0.8)
				t["angry"] = true
				t["vel"] = Vector2.ZERO
				toys.append(t)
				bubbles.erase(b)
				event.emit("escape", {"pos": p})
			else:
				bubbles.erase(b)
				event.emit("pop", {"pos": p, "n": 0, "trapped": false})


## Pops a bubble and every bubble touching it, in a chain. The hero gets the points.
func _pop_chain(first: Dictionary, h: Dictionary) -> void:
	var queue: Array = [first]
	var done := {first["id"]: true}
	var trapped := 0
	var head := 0
	while head < queue.size():
		var b: Dictionary = queue[head]
		head += 1
		for o in bubbles:
			if not done.has(o["id"]) and (o["pos"] as Vector2).distance_to(b["pos"]) < BUBBLE_R * 2.3:
				done[o["id"]] = true
				queue.append(o)
	for i in queue.size():
		var b: Dictionary = queue[i]
		bubbles.erase(b)
		var has: bool = not b["trapped"].is_empty()
		event.emit("pop", {"pos": b["pos"], "n": i, "trapped": has})
		if has:
			trapped += 1
			var kind: String = TREATS[mini(trapped - 1 + stage / 3, TREATS.size() - 1)]
			treats.append({"pos": b["pos"], "vel": Vector2(rng.randf_range(-3, 3), -8.0), "kind": kind, "ground": false, "age": 0.0})
			event.emit("treat_drop", {"pos": b["pos"], "kind": kind})
		else:
			_score(h, 10)
	if trapped > 0:
		_score(h, CHAIN_POINTS[mini(trapped, CHAIN_POINTS.size()) - 1])


func _score(h: Dictionary, pts: int) -> void:
	h["score"] += pts
	if h["score"] >= h["next_life"]:
		h["next_life"] += 50000
		h["lives"] += 1
		event.emit("extra_life", {"p": h["p"]})


# ------------------------------------------------------------------ toys, treats, the ghost

func _move_toys() -> void:
	var target_h := _nearest_hero(Vector2(W * 0.5, H * 0.5))
	for t in toys:
		var speed: float = t["speed"] * (1.5 if t["angry"] else 1.0)
		if t["flyer"]:
			var p: Vector2 = t["pos"]
			var v: Vector2 = t["vel"].normalized() * speed * 1.1
			var np := p + v * TICK
			if np.x < 2.0 + HALF_W or np.x > W - 2.0 - HALF_W:
				v.x = -v.x
			if np.y < 2.0 or np.y > H - 1.0:
				v.y = -v.y
			var tile := Vector2i(floor(np.x), floor(np.y - 0.5))
			if is_solid(tile.x, tile.y) and np.y > 2.0:
				v.y = -v.y
				v.x += rng.randf_range(-0.5, 0.5)
			t["vel"] = v
			t["pos"] = p + v * TICK
			t["facing"] = int(signf(v.x)) if v.x != 0.0 else t["facing"]
			continue
		t["think"] -= TICK
		var v: Vector2 = t["vel"]
		v.x = t["facing"] * speed
		if t["ground"] and t["think"] <= 0.0:
			t["think"] = rng.randf_range(0.6, 1.8)
			var h := _nearest_hero(t["pos"])
			if not h.is_empty():
				var hp: Vector2 = h["pos"]
				if hp.y < t["pos"].y - 2.0 and rng.randf() < 0.6:
					v.y = JUMP_V * 0.95  # jump up after the hero
				elif absf(hp.y - t["pos"].y) < 1.5 and rng.randf() < 0.7:
					t["facing"] = 1 if hp.x > t["pos"].x else -1
				elif rng.randf() < 0.25:
					t["facing"] = -t["facing"]
		var r := _body(t["pos"], v, TICK)
		if r[1].x == 0.0 and v.x != 0.0:
			t["facing"] = -t["facing"]  # a wall: turn back
		t["pos"] = r[0]
		t["vel"] = Vector2(0.0, r[1].y)
		t["ground"] = r[2]


func _nearest_hero(p: Vector2) -> Dictionary:
	var best := {}
	var bd := INF
	for h in heroes:
		if h["alive"] and (h["pos"] as Vector2).distance_to(p) < bd:
			bd = (h["pos"] as Vector2).distance_to(p)
			best = h
	return best


func _move_treats() -> void:
	for tr in treats:
		tr["age"] += TICK
		if not tr["ground"]:
			var r := _body(tr["pos"], tr["vel"], TICK)
			tr["pos"] = r[0]
			tr["vel"] = Vector2(r[1].x * 0.98, r[1].y)
			tr["ground"] = r[2]
	treats = treats.filter(func(tr): return tr["age"] < 12.0)


func _move_ghost() -> void:
	if ghost.is_empty():
		return
	var h := _nearest_hero(ghost["pos"])
	if h.is_empty():
		return
	var to: Vector2 = (h["pos"] + Vector2(0, -0.9)) - ghost["pos"]
	ghost["vel"] = (ghost["vel"] as Vector2).lerp(to.normalized() * 4.5, TICK * 2.0)
	ghost["pos"] += ghost["vel"] * TICK


# ------------------------------------------------------------------ contact

func _collide(h: Dictionary) -> void:
	if not h["alive"]:
		return
	var hp: Vector2 = h["pos"]
	var centre := hp + Vector2(0, -0.85)
	# bubbles: from above with jump held, a bounce; otherwise a pop
	for b in bubbles.duplicate():
		if not bubbles.has(b) or b["age"] < b["fly"] and b["trapped"].is_empty():
			continue
		var bp: Vector2 = b["pos"]
		if centre.distance_to(bp) < BUBBLE_R + 0.7:
			if h["vel"].y > 0.0 and hp.y < bp.y - BUBBLE_R * 0.3 and h["jump"]:
				h["vel"].y = JUMP_V * 0.85
				event.emit("bounce", {"p": h["p"], "pos": bp})
			else:
				_pop_chain(b, h)
	if h["inv"] > 0.0:
		return
	for t in toys:
		if (t["pos"] as Vector2).distance_to(hp) < 1.2:
			_hit(h)
			return
	if not ghost.is_empty() and (ghost["pos"] as Vector2).distance_to(centre) < 1.0:
		_hit(h)


func _hit(h: Dictionary) -> void:
	h["alive"] = false
	h["lives"] -= 1
	h["dead_t"] = 2.0
	event.emit("die", {"p": h["p"], "pos": h["pos"]})


func _collect(h: Dictionary) -> void:
	if not h["alive"]:
		return
	for tr in treats.duplicate():
		if tr["age"] > 0.4 and (tr["pos"] as Vector2).distance_to(h["pos"]) < 1.3:
			treats.erase(tr)
			var pts: int = TREAT_POINTS[tr["kind"]]
			_score(h, pts)
			event.emit("treat", {"p": h["p"], "pos": tr["pos"], "points": pts, "kind": tr["kind"]})
