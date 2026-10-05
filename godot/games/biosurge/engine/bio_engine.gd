class_name BioEngine
extends RefCounted
## Biosurge rules (a vertical-scrolling shooter through living caverns in the Xenon 2 tradition; our own tuning), 60 Hz.
## Positions are (x across 0..16, d along the level in metres); the screen shows SCREEN metres from `scroll` and climbs
## at a steady pace, stopping at the end where the level's boss waits. The cavern is a wall profile (`left`, `right`
## per metre) with islands: touching a wall stings and pushes the ship back. The ship flies anywhere on screen and
## fires while the button is held: its main gun (levels 1-5 widen it), side pods, a rear gun, homing missiles, a
## laser and a drone are bought in the shop between levels with the credits enemies drop. Energy runs down with hits;
## at nothing a life goes. Enemy waves come by distance: drifters, darts that dive, spinners, turrets on the walls,
## worms out of the walls, egg pods that hatch drifters, crabs walking the walls. The boss has a core to shoot.
## Events: "shoot", "laser", "homing", "hit" {pos, kind}, "kill" {pos, kind, points}, "credit" {pos, value},
## "pickup" {kind}, "enemy_shoot" {pos}, "player_hit" {damage}, "wall", "die" {pos}, "warning", "boss" {hp},
## "boss_hit", "boss_die" {pos}, "cleared", "game_over", "shield".

signal event(kind: String, data: Dictionary)

enum Phase { READY, PLAY, DYING, BOSS, CLEARED, OVER }
const TICK := 1.0 / 60.0
const W := 16.0
const SCREEN := 15.0
const SCROLL := 3.4
const SPEED := 8.6
const SHOT := 26.0
const R := 0.45                 ## the ship's radius
const NAMES := ["SPAWNING GROUNDS", "CORAL ABYSS", "CRYSTAL HIVE", "FURNACE GUT", "THE HEART"]
const HP := {"drifter": 2, "dart": 1, "spinner": 3, "turret": 6, "worm": 3, "pod": 14, "crab": 5}
const POINTS := {"drifter": 100, "dart": 150, "spinner": 200, "turret": 400, "worm": 250, "pod": 800, "crab": 500}
const RADIUS := {"drifter": 0.6, "dart": 0.45, "spinner": 0.55, "turret": 0.6, "worm": 0.5, "pod": 1.0, "crab": 0.7}

var level := 0
var length := 320.0
var left := PackedFloat32Array()
var right := PackedFloat32Array()
var islands: Array[Rect2] = []          ## x, d, width, depth
var phase := Phase.READY
var phase_t := 2.0
var time := 0.0
var scroll := 0.0
var ship := {}
var input := Vector2.ZERO               ## x across, y along (+ = up the screen)
var firing := false
var loadout := {"gun": 1, "side": false, "rear": false, "homing": false, "laser": false, "drone": false, "speed": 0}
var energy := 100.0
var shield := 0.0
var lives := 3
var score := 0
var credits := 0
var shots: Array[Dictionary] = []       ## {pos, vel, dmg, kind}
var foes: Array[Dictionary] = []
var bullets: Array[Dictionary] = []     ## enemy shots {pos, vel}
var drops: Array[Dictionary] = []       ## {pos, kind, value}
var waves: Array[Dictionary] = []       ## {d, kind, n, x}
var boss := {}
var rng := RandomNumberGenerator.new()
var _fire_t := 0.0
var _laser := false
var _next_id := 0


func _init(level_ := 0, carry := {}, seed_ := 1) -> void:
	level = level_
	rng.seed = seed_ * 31 + level_ * 977
	score = carry.get("score", 0)
	credits = carry.get("credits", 0)
	lives = carry.get("lives", 3)
	if carry.has("loadout"):
		loadout = carry["loadout"].duplicate()
	length = 380.0 + level * 40.0
	_cavern()
	_plan_waves()
	ship = {"pos": Vector2(W * 0.5, 3.0), "vel": Vector2.ZERO, "bank": 0.0, "hurt": 0.0, "drone": 0.0}


# ------------------------------------------------------------------ the level

## The cavern: walls that wander and breathe, narrows now and then, islands to fly round.
func _cavern() -> void:
	var n := int(length) + 40
	left.resize(n)
	right.resize(n)
	var waves_ := []
	for k in 4:
		waves_.append([rng.randf_range(0.5, 1.6) * (k + 1) * 0.012, rng.randf() * TAU, rng.randf_range(0.6, 1.4) / (k + 1)])
	for i in n:
		var d := float(i)
		var c := W * 0.5
		var half := 6.4
		for wv in waves_:
			c += sin(d * wv[0] * TAU + wv[1]) * wv[2] * 1.6
			half += cos(d * wv[0] * TAU * 0.7 + wv[1]) * wv[2] * 0.9
		# narrows
		var nar := 0.5 + 0.5 * sin(d * 0.021 + level * 1.3)
		half -= smoothstep(0.82, 1.0, nar) * 2.6
		half = clampf(half, 3.0 + 0.0, 7.6)
		if d < 20.0 or d > length - 30.0:
			half = 7.6   # open at the start, and the boss's arena
			c = W * 0.5
		left[i] = clampf(c - half, 0.0, W * 0.5 - 2.5)
		right[i] = clampf(c + half, W * 0.5 + 2.5, W)
	# islands in the wide stretches
	var d2 := 45.0
	while d2 < length - 60.0:
		var i := int(d2)
		if right[i] - left[i] > 10.0 and rng.randf() < 0.55:
			var w := rng.randf_range(1.6, 3.0)
			var x := (left[i] + right[i]) * 0.5 + rng.randf_range(-1.0, 1.0) - w * 0.5
			islands.append(Rect2(x, d2, w, rng.randf_range(2.0, 4.5)))
		d2 += rng.randf_range(28.0, 45.0)


func _plan_waves() -> void:
	var kinds := ["drifter", "dart", "spinner", "turret", "worm", "pod", "crab"]
	var d := 18.0
	while d < length - 34.0:
		var pool := kinds.slice(0, mini(3 + level, kinds.size()))
		var k: String = pool[rng.randi() % pool.size()]
		var n := 1
		match k:
			"drifter", "dart": n = rng.randi_range(3, 5 + level)
			"spinner": n = rng.randi_range(2, 4)
			"worm": n = 5
		waves.append({"d": d, "kind": k, "n": n, "x": rng.randf_range(3.0, W - 3.0), "done": false})
		d += rng.randf_range(7.0, 12.0) - level * 0.4


func wall_hit(p: Vector2, r: float) -> bool:
	var i := clampi(int(p.y), 0, left.size() - 1)
	if p.x - r < left[i] or p.x + r > right[i]:
		return true
	for isl in islands:
		if isl.grow(r).has_point(p):
			return true
	return false


## `p` moved into the open cavern (between the walls at its row, and out of any island), `r` from the rock.
func inside(p: Vector2, r: float) -> Vector2:
	var i := clampi(int(p.y), 0, left.size() - 1)
	var lo := left[i] + r
	var hi := right[i] - r
	p.x = clampf(p.x, lo, hi) if lo < hi else (left[i] + right[i]) * 0.5
	for isl in islands:
		var g := isl.grow(r)
		if g.has_point(p):
			p.x = g.position.x if p.x - g.position.x < g.end.x - p.x else g.end.x
			p.x = clampf(p.x, lo, hi)
	return p


func _id() -> int:
	_next_id += 1
	return _next_id


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
			_shots()
			return
		Phase.DYING:
			phase_t -= TICK
			_foes()
			_bullets()
			if phase_t <= 0.0:
				if lives <= 0:
					phase = Phase.OVER
					phase_t = 3.0
					event.emit("game_over", {})
				else:
					energy = 100.0
					shield = 2.5
					ship["pos"] = Vector2(W * 0.5, scroll + 3.0)
					phase = Phase.BOSS if not boss.is_empty() else Phase.PLAY
			return
	# the screen climbs until the boss's arena
	var stop := length - SCREEN + 1.0
	if scroll < stop:
		scroll = minf(stop, scroll + SCROLL * TICK)
		if scroll >= stop - 0.01 and boss.is_empty():
			_boss()
	_move_ship()
	_fire()
	_shots()
	_spawn()
	_foes()
	_bullets()
	_drops()
	if not boss.is_empty():
		_boss_tick()
	shield = maxf(0.0, shield - TICK)


func _move_ship() -> void:
	var p: Vector2 = ship["pos"]
	var sp: float = SPEED * (1.0 + 0.12 * loadout["speed"])
	var want: Vector2 = input.limit_length(1.0) * sp
	var v: Vector2 = ship["vel"]
	v = v.lerp(want, minf(1.0, TICK * 14.0))
	ship["vel"] = v
	ship["bank"] = lerpf(ship["bank"], -v.x / sp * 0.6, minf(1.0, TICK * 8.0))
	var np := p + v * TICK
	np.x = clampf(np.x, 0.6, W - 0.6)
	np.y = clampf(np.y, scroll + 0.8, scroll + SCREEN - 2.0)
	# the walls sting and push back
	if wall_hit(np, R * 0.85):
		var i := clampi(int(np.y), 0, left.size() - 1)
		var mid := (left[i] + right[i]) * 0.5
		np.x = move_toward(np.x, mid, 6.0 * TICK + absf(v.x) * TICK)
		if wall_hit(np, R * 0.85):
			np.y = maxf(np.y, p.y) if np.y < p.y else p.y
		if ship["hurt"] <= 0.0:
			_hurt(6.0)
			event.emit("wall", {})
	ship["pos"] = np
	ship["hurt"] = maxf(0.0, ship["hurt"] - TICK)
	ship["drone"] += TICK * 3.0


func _fire() -> void:
	_fire_t -= TICK
	var was := _laser
	_laser = firing and loadout["laser"]
	if _laser != was and _laser:
		event.emit("laser", {})
	if not firing or _fire_t > 0.0:
		return
	_fire_t = 0.14
	var p: Vector2 = ship["pos"] + Vector2(0, 0.6)
	var g: int = loadout["gun"]
	var angles := [0.0]
	match g:
		2: angles = [-0.05, 0.05]
		3: angles = [-0.12, 0.0, 0.12]
		4: angles = [-0.2, -0.07, 0.07, 0.2]
		5: angles = [-0.26, -0.13, 0.0, 0.13, 0.26]
	if not loadout["laser"]:
		for a in angles:
			shots.append({"pos": p, "vel": Vector2(sin(a), cos(a)) * SHOT, "dmg": 1.0, "kind": "pulse"})
	if loadout["side"]:
		for s in [-1.0, 1.0]:
			shots.append({"pos": p + Vector2(s * 0.7, -0.4), "vel": Vector2(s * 0.45, 0.9).normalized() * SHOT * 0.85, "dmg": 1.0, "kind": "pulse"})
	if loadout["rear"]:
		shots.append({"pos": p + Vector2(0, -1.0), "vel": Vector2(0, -SHOT * 0.8), "dmg": 1.0, "kind": "pulse"})
	if loadout["homing"] and int(time / 0.14) % 4 == 0:
		shots.append({"pos": p, "vel": Vector2(0, 10.0), "dmg": 2.0, "kind": "homing", "life": 2.5})
		event.emit("homing", {})
	if loadout["drone"]:
		var dp: Vector2 = drone_pos()
		shots.append({"pos": dp, "vel": Vector2(0, SHOT), "dmg": 0.6, "kind": "pulse"})
	event.emit("shoot", {"gun": g})


func drone_pos() -> Vector2:
	return ship["pos"] + Vector2(cos(ship["drone"]), sin(ship["drone"]) * 0.6) * 1.3


## The laser: a beam straight ahead, hurting whatever is in it each tick (stopped by walls).
func laser_reach() -> float:
	var p: Vector2 = ship["pos"]
	var d := 0.0
	while d < SCREEN:
		if wall_hit(p + Vector2(0, d + 0.6), 0.05):
			break
		d += 0.5
	return d


func _shots() -> void:
	var keep: Array[Dictionary] = []
	for s in shots:
		if s["kind"] == "homing":
			s["life"] -= TICK
			var tgt := _nearest_foe(s["pos"])
			if not tgt.is_empty():
				var want: Vector2 = ((tgt["pos"] as Vector2) - s["pos"]).normalized() * 16.0
				s["vel"] = (s["vel"] as Vector2).lerp(want, minf(1.0, TICK * 4.0))
			if s["life"] <= 0.0:
				continue
		s["pos"] += s["vel"] * TICK
		var p: Vector2 = s["pos"]
		if p.y > scroll + SCREEN + 1.0 or p.y < scroll - 1.0 or p.x < -1.0 or p.x > W + 1.0:
			continue
		if wall_hit(p, 0.05):
			event.emit("hit", {"pos": p, "kind": "wall"})
			continue
		var hit := false
		for f in foes:
			if f["dead"]:
				continue
			if p.distance_to(f["pos"]) < RADIUS[f["kind"]] + 0.15:
				_damage(f, s["dmg"])
				hit = true
				break
		if not hit and not boss.is_empty() and boss["hp"] > 0.0 and p.distance_to(boss["core"]) < 1.6:
			_boss_damage(s["dmg"])
			hit = true
		if not hit:
			keep.append(s)
	shots = keep
	if _laser and phase in [Phase.PLAY, Phase.BOSS]:
		var p: Vector2 = ship["pos"]
		var reach := laser_reach()
		for f in foes:
			if not f["dead"] and absf(f["pos"].x - p.x) < RADIUS[f["kind"]] + 0.2 and f["pos"].y > p.y and f["pos"].y < p.y + reach:
				_damage(f, 4.0 * TICK * (1.0 + 0.3 * loadout["gun"]))
		if not boss.is_empty() and absf(boss["core"].x - p.x) < 1.5 and boss["core"].y < p.y + reach:
			_boss_damage(4.0 * TICK * (1.0 + 0.3 * loadout["gun"]))


func _nearest_foe(p: Vector2) -> Dictionary:
	var best := {}
	var bd := 12.0
	for f in foes:
		if not f["dead"] and (f["pos"] as Vector2).distance_to(p) < bd:
			bd = (f["pos"] as Vector2).distance_to(p)
			best = f
	if best.is_empty() and not boss.is_empty():
		return {"pos": boss["core"]}
	return best


func _damage(f: Dictionary, dmg: float) -> void:
	f["hp"] -= dmg
	f["flash"] = 0.1
	if f["hp"] <= 0.0 and not f["dead"]:
		f["dead"] = true
		var pts: int = POINTS[f["kind"]]
		score += pts
		event.emit("kill", {"pos": f["pos"], "kind": f["kind"], "points": pts})
		# credits, sometimes a power-up
		var value: int = {"drifter": 10, "dart": 10, "spinner": 20, "turret": 40, "worm": 20, "pod": 80, "crab": 50}[f["kind"]]
		drops.append({"pos": f["pos"], "kind": "credit", "value": value, "t": 0.0})
		if rng.randf() < 0.06:
			drops.append({"pos": f["pos"] + Vector2(0.5, 0), "kind": ["gun", "speed", "shield", "life"][rng.randi() % 4], "value": 0, "t": 0.0})
	else:
		event.emit("hit", {"pos": f["pos"], "kind": f["kind"]})


# ------------------------------------------------------------------ enemies

func _spawn() -> void:
	for w in waves:
		if w["done"] or w["d"] > scroll + SCREEN + 2.0:
			continue
		w["done"] = true
		var k: String = w["kind"]
		var top: float = scroll + SCREEN + 1.0
		match k:
			"drifter", "dart", "spinner":
				for j in w["n"]:
					var q := Vector2(w["x"] + (j - w["n"] * 0.5) * 1.3, top + j * (0.9 if k == "dart" else 1.6))
					_add(k, inside(q, RADIUS[k]), {"phase": j * 0.7})
			"turret", "crab":
				var i := clampi(int(top), 0, left.size() - 1)
				var side := 1.0 if rng.randf() < 0.5 else -1.0
				var x := left[i] + 0.75 if side < 0.0 else right[i] - 0.75   # on the wall's face, in reach
				_add(k, Vector2(x, top), {"side": side})
			"worm":
				var i := clampi(int(top - 3.0), 0, left.size() - 1)
				var x0 := left[i]
				for j in w["n"]:
					_add("worm", Vector2(x0 - j * 0.6, top - 3.0), {"seg": j, "lead": j == 0, "phase": -j * 0.25})
			"pod":
				_add("pod", Vector2(w["x"], top + 1.0), {"hatch": 1.5})


func _add(kind: String, p: Vector2, extra := {}) -> void:
	var f := {"id": _id(), "kind": kind, "pos": p, "vel": Vector2.ZERO, "hp": float(HP[kind]) * (1.0 + level * 0.25), "t": 0.0, "dead": false,
		"shoot_t": rng.randf_range(1.0, 2.5), "flash": 0.0}
	f.merge(extra)
	foes.append(f)


func _foes() -> void:
	var sp: Vector2 = ship["pos"]
	for f in foes:
		if f["dead"]:
			continue
		f["t"] += TICK
		f["flash"] = maxf(0.0, f["flash"] - TICK)
		var p: Vector2 = f["pos"]
		match f["kind"]:
			"drifter":
				p += Vector2(sin(f["t"] * 1.6 + f["phase"]) * 1.4, -1.2) * TICK
			"dart":
				if f["t"] < 0.8:
					p.y -= 1.5 * TICK
				else:
					var to := (sp - p).normalized() if f["t"] < 1.2 else (f["vel"] as Vector2).normalized()
					f["vel"] = (f["vel"] as Vector2).lerp(to * 9.0, minf(1.0, TICK * 3.0))
					p += f["vel"] * TICK
			"spinner":
				var sx := signf(sin(f["t"] * 1.2 + f["phase"])) * 3.0
				if inside(p + Vector2(sx * 0.2, 0), RADIUS["spinner"]) != p + Vector2(sx * 0.2, 0):
					f["phase"] += PI   # bounces off a wall
				p += Vector2(sx, -1.6) * TICK
			"turret":
				pass
			"crab":
				p.y += sin(f["t"] * 0.8) * 1.0 * TICK
				var ci := clampi(int(p.y), 0, left.size() - 1)
				p.x = left[ci] + 0.75 if f["side"] < 0.0 else right[ci] - 0.75
			"worm":
				# the lead snakes out from the wall; the segments follow its trail
				if f["lead"]:
					f["trail"] = f.get("trail", [])
					p += Vector2(2.6, sin(f["t"] * 2.4) * 2.2) * TICK
					(f["trail"] as Array).push_front(p)
					if (f["trail"] as Array).size() > 120:
						(f["trail"] as Array).pop_back()
				else:
					var lead := _worm_lead(f)
					if not lead.is_empty():
						var tr: Array = lead.get("trail", [])
						var k: int = f["seg"] * 9
						if k < tr.size():
							p = tr[k]
			"pod":
				f["hatch"] -= TICK
				if f["hatch"] <= 0.0 and p.y < scroll + SCREEN - 1.0:
					f["hatch"] = 2.2
					_add("drifter", p + Vector2(rng.randf_range(-0.8, 0.8), -0.8), {"phase": rng.randf() * TAU})
		# everything that flies keeps to the cavern, where the ship can reach it (worms only once out of the wall)
		if f["kind"] in ["drifter", "dart", "spinner", "pod"] or (f["kind"] == "worm" and f["t"] > 1.2):
			p = inside(p, RADIUS[f["kind"]])
		f["pos"] = p
		# shooting at the ship
		if f["kind"] in ["turret", "crab", "drifter", "pod"] and p.y < scroll + SCREEN and p.y > sp.y:
			f["shoot_t"] -= TICK
			if f["shoot_t"] <= 0.0:
				f["shoot_t"] = rng.randf_range(1.4, 2.8) / (1.0 + level * 0.15)
				var dir := (sp - p).normalized()
				bullets.append({"pos": p, "vel": dir * (6.0 + level * 0.5)})
				event.emit("enemy_shoot", {"pos": p})
		# off the bottom
		if p.y < scroll - 2.0:
			f["dead"] = true
			f["gone"] = true
		# touching the ship
		if p.distance_to(sp) < RADIUS[f["kind"]] + R * 0.8 and phase in [Phase.PLAY, Phase.BOSS] and ship["hurt"] <= 0.0:
			_hurt(18.0)
			if f["kind"] in ["drifter", "dart", "spinner"]:
				_damage(f, 99.0)
	foes = foes.filter(func(f): return not f["dead"] or f.get("flash", 0.0) > 0.0 and not f.get("gone", false))


func _worm_lead(f: Dictionary) -> Dictionary:
	for o in foes:
		if o["kind"] == "worm" and o.get("lead", false) and not o["dead"] and absi(o["id"] - f["id"]) <= 6 and o["id"] < f["id"]:
			return o
	return {}


func _bullets() -> void:
	var sp: Vector2 = ship["pos"]
	var keep: Array[Dictionary] = []
	for b in bullets:
		b["pos"] += b["vel"] * TICK
		var p: Vector2 = b["pos"]
		if p.y < scroll - 1.0 or p.y > scroll + SCREEN + 1.0 or p.x < -1.0 or p.x > W + 1.0 or wall_hit(p, 0.0):
			continue
		if p.distance_to(sp) < R and phase in [Phase.PLAY, Phase.BOSS]:
			_hurt(12.0)
			continue
		keep.append(b)
	bullets = keep


func _hurt(dmg: float) -> void:
	if shield > 0.0:
		return
	energy -= dmg
	ship["hurt"] = 0.35
	event.emit("player_hit", {"damage": dmg})
	if energy <= 0.0:
		energy = 0.0
		lives -= 1
		phase = Phase.DYING
		phase_t = 2.0
		bullets.clear()
		event.emit("die", {"pos": ship["pos"]})


func _drops() -> void:
	var sp: Vector2 = ship["pos"]
	var keep: Array[Dictionary] = []
	for dr in drops:
		dr["t"] += TICK
		var p: Vector2 = dr["pos"]
		# credits drift to a nearby ship
		if p.distance_to(sp) < 2.5:
			p = p.move_toward(sp, 8.0 * TICK)
		dr["pos"] = p
		if p.distance_to(sp) < 0.8:
			match dr["kind"]:
				"credit":
					credits += dr["value"]
					event.emit("credit", {"pos": p, "value": dr["value"]})
				"gun": loadout["gun"] = mini(5, loadout["gun"] + 1)
				"speed": loadout["speed"] = mini(3, loadout["speed"] + 1)
				"shield":
					shield = 6.0
					event.emit("shield", {})
				"life": lives += 1
			if dr["kind"] != "credit":
				event.emit("pickup", {"kind": dr["kind"]})
			continue
		if p.y < scroll - 1.0 or dr["t"] > 14.0:
			continue
		keep.append(dr)
	drops = keep


# ------------------------------------------------------------------ the boss

func _boss() -> void:
	var hp := 260.0 + level * 140.0
	boss = {"hp": hp, "max": hp, "pos": Vector2(W * 0.5, length - 3.0), "core": Vector2(W * 0.5, length - 4.0), "t": 0.0, "fire_t": 1.5,
		"pattern": 0, "flash": 0.0}
	phase = Phase.BOSS
	event.emit("warning", {})
	event.emit("boss", {"hp": hp})


func _boss_tick() -> void:
	if boss["hp"] <= 0.0:
		return
	boss["t"] += TICK
	boss["flash"] = maxf(0.0, boss["flash"] - TICK)
	var t: float = boss["t"]
	var p := Vector2(W * 0.5 + sin(t * 0.5) * 4.0, length - 3.0 + sin(t * 0.9) * 0.6)
	boss["pos"] = p
	boss["core"] = p + Vector2(0, -1.2)
	boss["fire_t"] -= TICK
	if boss["fire_t"] <= 0.0:
		var pat: int = boss["pattern"] % 3
		boss["pattern"] += 1
		var c: Vector2 = boss["core"]
		match pat:
			0:   # a fan
				for k in 9 + level * 2:
					var a := lerpf(-1.0, 1.0, k / float(8 + level * 2))
					bullets.append({"pos": c, "vel": Vector2(sin(a), -cos(a)) * (5.5 + level * 0.4)})
			1:   # aimed bursts
				var dir := ((ship["pos"] as Vector2) - c).normalized()
				for k in 4:
					bullets.append({"pos": c - dir * k * 0.5, "vel": dir * (8.0 + level * 0.5)})
			2:   # spawn
				for k in 3:
					_add("drifter", c + Vector2((k - 1) * 2.0, -1.0), {"phase": k})
		boss["fire_t"] = maxf(0.9, 2.0 - level * 0.2)
		event.emit("enemy_shoot", {"pos": c})


func _boss_damage(dmg: float) -> void:
	if boss["hp"] <= 0.0:
		return
	boss["hp"] -= dmg
	boss["flash"] = 0.08
	event.emit("boss_hit", {})
	if boss["hp"] <= 0.0:
		score += 5000 + level * 2500
		credits += 400
		bullets.clear()
		for f in foes:
			f["dead"] = true
		phase = Phase.CLEARED
		phase_t = 4.0
		event.emit("boss_die", {"pos": boss["core"]})
		event.emit("cleared", {})


# ------------------------------------------------------------------ the shop

const SHOP := [
	["gun", "GUN POWER", 300], ["side", "SIDE PODS", 400], ["rear", "REAR GUN", 250], ["homing", "HOMING MISSILES", 600],
	["laser", "LASER", 900], ["drone", "DRONE", 500], ["speed", "SPEED", 200], ["life", "EXTRA SHIP", 1000],
]


## Whether the item can be bought now (affordable and not maxed).
func can_buy(item: String, price: int) -> bool:
	if credits < price:
		return false
	match item:
		"gun": return loadout["gun"] < 5
		"speed": return loadout["speed"] < 3
		"life": return true
	return not loadout[item]


func buy(item: String, price: int) -> bool:
	if not can_buy(item, price):
		return false
	credits -= price
	match item:
		"gun": loadout["gun"] += 1
		"speed": loadout["speed"] += 1
		"life": lives += 1
		_: loadout[item] = true
	return true


func carry() -> Dictionary:
	return {"score": score, "credits": credits, "lives": lives, "loadout": loadout}
