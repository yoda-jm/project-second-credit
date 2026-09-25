class_name BootsEngine
extends RefCounted
## Rules of Muddy Boots (inspired by Cannon Fodder, 1993). Pure logic, fixed ticks, seeded random generator.
##
## A squad of up to four soldiers: the leader walks where the player points (A* over the map), the others follow
## in single file on the leader's trail. The squad shoots at a point (bullets stop at trees and rock), throws
## grenades and fires rockets. Enemies spot the squad within sight (trees and rock block the view) and shoot back;
## huts keep sending soldiers out until a grenade or a rocket brings them down. Hostages who are reached follow the
## squad to the rescue tent. One hit is enough to kill anybody. The mission ends when its goals are met, or when the
## squad is gone. Positions are in tiles (float), x right, y down. Our own tuning throughout.

signal event(kind: String, data: Dictionary)  ## "shot", "enemy_shot", "hit", "death", "enemy_death", "grenade",
## "rocket", "explosion", "hut_destroyed", "spawn", "pickup", "rescued", "mine", "splash", "won", "lost", "phase"

enum Phase { PLAY, WON, LOST }
const T = BootsMap.T
const TICK := 1.0 / 60.0
const SPEED := 3.3  ## tiles per second on land
const TERRAIN_SPEED := {T.LAND: 1.0, T.ROUGH: 0.7, T.WATER: 0.4, T.SHALLOW: 0.65, T.QUICKSAND: 0.35, T.SNOW: 0.6}
const FOLLOW_GAP := 0.9  ## tiles between soldiers in the file
const FIRE_EVERY := 0.22
const BULLET_SPEED := 16.0
const BULLET_RANGE := 9.0
const SPREAD := 0.06  ## radians
const GRENADE_RANGE := 7.0
const GRENADE_FLIGHT := 0.9
const BLAST := 1.7  ## radius, tiles
const ROCKET_SPEED := 12.0
const SIGHT := 8.5
const ENEMY_FIRE := Vector2(1.1, 1.9)
const ENEMY_SPREAD := 0.14
const ENEMY_BULLET := 11.0
const ENEMY_SPEED := 1.8
const HUT_SPAWN := Vector2(6.0, 10.0)
const HUT_WAKE := 14.0  ## huts send soldiers out when the squad is this close
const HIT_R := 0.45

var map: BootsMap
var rng := RandomNumberGenerator.new()
var phase := Phase.PLAY
var time := 0.0
var soldiers: Array[Dictionary] = []  ## {id, pos, alive, kills}
var enemies: Array[Dictionary] = []   ## {id, pos, home, alive, fire_in, alert, wander, target}
var huts: Array[Dictionary] = []      ## {cell, alive, spawn_in, door}
var hostages: Array[Dictionary] = []  ## {id, pos, following, rescued}
var tents: Array[Vector2] = []
var crates: Array[Dictionary] = []    ## {kind, pos}
var mines: Array[Vector2] = []
var bullets: Array[Dictionary] = []   ## {pos, vel, left (range), ours}
var grenades_air: Array[Dictionary] = []  ## {from, to, t, dur}
var rockets_air: Array[Dictionary] = []   ## {pos, vel, left}
var grenades := 0
var rockets := 0
var path: Array[Vector2] = []  ## the leader's waypoints (tile centres)
var trail: Array[Vector2] = []  ## where the leader has been, newest first
var aim := Vector2.ZERO
var firing := false  ## held by the game
var kills := 0
var _fire_in := 0.0
var _astar := AStarGrid2D.new()
var _next_id := 1
var _blocked := {}  ## cells taken by huts


func _init(m: BootsMap = null, seed := 1, squad := 4) -> void:
	rng.seed = seed
	if m != null:
		load_map(m, squad)


func load_map(m: BootsMap, squad := 4) -> void:
	map = m
	grenades = m.grenades
	rockets = m.rockets
	phase = Phase.PLAY
	for t in m.things:
		var c: Vector2i = t["cell"]
		var p := Vector2(c) + Vector2(0.5, 0.5)
		match t["kind"]:
			"start":
				if soldiers.is_empty():
					for i in squad:
						soldiers.append({"id": _id(), "pos": p + Vector2(0, 0.3 * i), "alive": true, "kills": 0})
			"enemy": enemies.append(_enemy(p))
			"hut":
				var door := p + Vector2(0.5, 2.0) if m.source == "text" else p + Vector2(0, 0.8)
				huts.append({"cell": c, "alive": true, "spawn_in": rng.randf_range(2.0, HUT_SPAWN.y), "door": door, "id": _id()})
				if m.source == "text":
					for dy in 2:
						for dx in 2:
							_blocked[c + Vector2i(dx, dy)] = true
			"hostage": hostages.append({"id": _id(), "pos": p, "following": false, "rescued": false})
			"tent": tents.append(p)
			"grenades", "rockets": crates.append({"kind": t["kind"], "pos": p, "id": _id()})
			"mine": mines.append(p)
	_astar.region = Rect2i(0, 0, m.w, m.h)
	_astar.diagonal_mode = AStarGrid2D.DIAGONAL_MODE_ONLY_IF_NO_OBSTACLES
	_astar.default_compute_heuristic = AStarGrid2D.HEURISTIC_OCTILE
	_astar.update()
	for y in m.h:
		for x in m.w:
			var c := Vector2i(x, y)
			if blocked(c):
				_astar.set_point_solid(c, true)
			else:
				_astar.set_point_weight_scale(c, 1.0 / TERRAIN_SPEED.get(m.at(c), 1.0))
	trail.clear()
	if not soldiers.is_empty():
		trail.append(soldiers[0]["pos"])


func _id() -> int:
	_next_id += 1
	return _next_id


func _enemy(p: Vector2) -> Dictionary:
	return {"id": _id(), "pos": p, "home": p, "alive": true, "fire_in": rng.randf_range(ENEMY_FIRE.x, ENEMY_FIRE.y),
		"alert": false, "wander": rng.randf_range(0.0, 3.0), "target": p}


# ------------------------------------------------------------------ queries

func blocked(c: Vector2i) -> bool:
	return map.blocks(c) or _blocked.has(c)


func cell_of(p: Vector2) -> Vector2i:
	return Vector2i(floori(p.x), floori(p.y))


func terrain_at(p: Vector2) -> int:
	return map.at(cell_of(p))


func alive_soldiers() -> Array[Dictionary]:
	var out: Array[Dictionary] = []
	for s in soldiers:
		if s["alive"]:
			out.append(s)
	return out


func leader() -> Dictionary:
	for s in soldiers:
		if s["alive"]:
			return s
	return {}


func swimming(p: Vector2) -> bool:
	return terrain_at(p) == T.WATER


## True when nothing blocks the view (or a shot) between two points.
func clear_line(a: Vector2, b: Vector2) -> bool:
	var d := a.distance_to(b)
	var n := int(d / 0.25) + 1
	for i in range(1, n):
		var p := a.lerp(b, float(i) / n)
		if blocked(cell_of(p)):
			return false
	return true


func goal_done(g: String) -> bool:
	match g:
		"kill": return enemies.filter(func(e): return e["alive"]).is_empty() and huts.filter(func(h): return h["alive"]).is_empty()
		"destroy": return huts.filter(func(h): return h["alive"]).is_empty()
		"rescue": return hostages.filter(func(h): return not h["rescued"]).is_empty()
	return false  # an unknown goal (tests use "none") is never done: the mission runs until the squad falls


# ------------------------------------------------------------------ orders

func move_to(target: Vector2) -> void:
	var l := leader()
	if l.is_empty():
		return
	var from := cell_of(l["pos"])
	var to := cell_of(target)
	if not map.inside(to) or blocked(to):
		return
	var cells := _astar.get_id_path(from, to)
	path.clear()
	for i in range(1, cells.size()):
		path.append(Vector2(cells[i]) + Vector2(0.5, 0.5))
	if not path.is_empty():
		path[path.size() - 1] = target.clamp(Vector2(to), Vector2(to) + Vector2(0.99, 0.99))


func throw_grenade(target: Vector2) -> void:
	var l := leader()
	if l.is_empty() or grenades <= 0 or phase != Phase.PLAY or swimming(l["pos"]):
		return
	var to: Vector2 = l["pos"] + (target - l["pos"]).limit_length(GRENADE_RANGE)
	grenades -= 1
	grenades_air.append({"from": l["pos"], "to": to, "t": 0.0, "dur": GRENADE_FLIGHT})
	event.emit("grenade", {"from": l["pos"], "to": to})


func fire_rocket(target: Vector2) -> void:
	var l := leader()
	if l.is_empty() or rockets <= 0 or phase != Phase.PLAY or swimming(l["pos"]):
		return
	rockets -= 1
	var dir: Vector2 = (target - l["pos"]).normalized()
	rockets_air.append({"pos": l["pos"] + dir * 0.4, "vel": dir * ROCKET_SPEED, "left": l["pos"].distance_to(target)})
	event.emit("rocket", {"from": l["pos"], "to": target})


# ------------------------------------------------------------------ tick

func tick() -> void:
	if phase != Phase.PLAY:
		return
	time += TICK
	_move_squad(TICK)
	_squad_fire(TICK)
	_move_enemies(TICK)
	_huts(TICK)
	_projectiles(TICK)
	_pickups()
	_check_end()


func _move_squad(dt: float) -> void:
	var l := leader()
	if l.is_empty():
		return
	if not path.is_empty():
		var p: Vector2 = l["pos"]
		var step: float = SPEED * TERRAIN_SPEED.get(terrain_at(p), 1.0) * dt
		var to := path[0]
		if p.distance_to(to) <= step:
			l["pos"] = to
			path.remove_at(0)
		else:
			l["pos"] = p + (to - p).normalized() * step
		if trail.is_empty() or trail[0].distance_to(l["pos"]) > 0.1:
			trail.push_front(l["pos"])
			if trail.size() > 400:
				trail.resize(400)
	# followers keep their place on the leader's trail
	var k := 0
	for s in soldiers:
		if not s["alive"] or s == l:
			continue
		k += 1
		var want := _trail_point(k * FOLLOW_GAP)
		var sp: Vector2 = s["pos"]
		var step: float = SPEED * TERRAIN_SPEED.get(terrain_at(sp), 1.0) * dt * 1.15
		if sp.distance_to(want) > 0.05:
			s["pos"] = sp.move_toward(want, step)
	# mines
	for s in alive_soldiers():
		for i in mines.size():
			if mines[i].distance_to(s["pos"]) < 0.5:
				var at := mines[i]
				mines.remove_at(i)
				event.emit("mine", {"pos": at})
				_explode(at, true)
				return


func _trail_point(dist: float) -> Vector2:
	var acc := 0.0
	for i in range(1, trail.size()):
		var seg := trail[i - 1].distance_to(trail[i])
		if acc + seg >= dist:
			return trail[i - 1].lerp(trail[i], (dist - acc) / maxf(seg, 0.001))
		acc += seg
	return trail.back() if not trail.is_empty() else Vector2.ZERO


func _squad_fire(dt: float) -> void:
	_fire_in -= dt
	if not firing or _fire_in > 0.0:
		return
	_fire_in = FIRE_EVERY
	for s in alive_soldiers():
		if swimming(s["pos"]):
			continue
		var dir: Vector2 = (aim - s["pos"]).normalized().rotated(rng.randf_range(-SPREAD, SPREAD))
		if dir == Vector2.ZERO:
			continue
		bullets.append({"pos": s["pos"] + dir * 0.35, "vel": dir * BULLET_SPEED, "left": BULLET_RANGE, "ours": true, "by": s["id"]})
		event.emit("shot", {"from": s["pos"], "dir": dir})


func _move_enemies(dt: float) -> void:
	var squad := alive_soldiers()
	for e in enemies:
		if not e["alive"]:
			continue
		var p: Vector2 = e["pos"]
		var target: Dictionary = {}
		var best := SIGHT
		for s in squad:
			var d := p.distance_to(s["pos"])
			if d < best and clear_line(p, s["pos"]):
				best = d
				target = s
		e["alert"] = not target.is_empty()
		if e["alert"]:
			e["fire_in"] -= dt
			if e["fire_in"] <= 0.0:
				e["fire_in"] = rng.randf_range(ENEMY_FIRE.x, ENEMY_FIRE.y)
				var dir: Vector2 = (target["pos"] - p).normalized().rotated(rng.randf_range(-ENEMY_SPREAD, ENEMY_SPREAD))
				bullets.append({"pos": p + dir * 0.35, "vel": dir * ENEMY_BULLET, "left": SIGHT + 1.0, "ours": false, "by": e["id"]})
				event.emit("enemy_shot", {"from": p, "dir": dir})
			# keep a fighting distance: close in when far, stand when near
			if best > 5.0:
				e["target"] = target["pos"]
		else:
			e["wander"] -= dt
			if e["wander"] <= 0.0:
				e["wander"] = rng.randf_range(2.0, 4.5)
				e["target"] = e["home"] + Vector2(rng.randf_range(-2.5, 2.5), rng.randf_range(-2.5, 2.5))
		var to: Vector2 = e["target"]
		if p.distance_to(to) > 0.2:
			var np := p.move_toward(to, ENEMY_SPEED * TERRAIN_SPEED.get(terrain_at(p), 1.0) * dt)
			if not blocked(cell_of(np)) and map.inside(cell_of(np)):
				e["pos"] = np
			else:
				e["target"] = p


func _huts(dt: float) -> void:
	var l := leader()
	if l.is_empty():
		return
	for h in huts:
		if not h["alive"]:
			continue
		if (h["door"] as Vector2).distance_to(l["pos"]) > HUT_WAKE:
			continue
		h["spawn_in"] -= dt
		if h["spawn_in"] <= 0.0:
			h["spawn_in"] = rng.randf_range(HUT_SPAWN.x, HUT_SPAWN.y)
			var e := _enemy(h["door"])
			e["home"] = (h["door"] as Vector2) + Vector2(0, 1.5)
			e["target"] = e["home"]
			enemies.append(e)
			event.emit("spawn", {"pos": h["door"], "id": e["id"]})


func _projectiles(dt: float) -> void:
	var i := 0
	while i < bullets.size():
		var b := bullets[i]
		var step: Vector2 = b["vel"] * dt
		b["pos"] += step
		b["left"] -= step.length()
		var hit := false
		if blocked(cell_of(b["pos"])) or not map.inside(cell_of(b["pos"])):
			event.emit("impact", {"pos": b["pos"]})
			hit = true
		elif b["ours"]:
			for e in enemies:
				if e["alive"] and (e["pos"] as Vector2).distance_to(b["pos"]) < HIT_R:
					_kill_enemy(e, b["by"])
					hit = true
					break
		else:
			for s in soldiers:
				if s["alive"] and (s["pos"] as Vector2).distance_to(b["pos"]) < HIT_R:
					_kill_soldier(s, "bullet")
					hit = true
					break
		if hit or b["left"] <= 0.0:
			bullets.remove_at(i)
			continue
		i += 1
	i = 0
	while i < grenades_air.size():
		var g := grenades_air[i]
		g["t"] += dt
		if g["t"] >= g["dur"]:
			_explode(g["to"], false)
			grenades_air.remove_at(i)
			continue
		i += 1
	i = 0
	while i < rockets_air.size():
		var r := rockets_air[i]
		var step: Vector2 = r["vel"] * dt
		r["pos"] += step
		r["left"] -= step.length()
		var boom: bool = r["left"] <= 0.0 or blocked(cell_of(r["pos"])) or not map.inside(cell_of(r["pos"]))
		for e in enemies:
			if e["alive"] and (e["pos"] as Vector2).distance_to(r["pos"]) < HIT_R:
				boom = true
		for h in huts:
			if h["alive"] and Rect2(Vector2(h["cell"]), Vector2(2, 2)).grow(0.1).has_point(r["pos"]):
				boom = true
		if boom:
			_explode(r["pos"], false)
			rockets_air.remove_at(i)
			continue
		i += 1


func _explode(at: Vector2, mine: bool) -> void:
	event.emit("explosion", {"pos": at, "splash": swimming(at), "mine": mine})
	for e in enemies:
		if e["alive"] and (e["pos"] as Vector2).distance_to(at) < BLAST:
			_kill_enemy(e, -1)
	for s in soldiers:
		if s["alive"] and (s["pos"] as Vector2).distance_to(at) < BLAST * (1.0 if mine else 0.8):
			_kill_soldier(s, "blast")
	for h in huts:
		if h["alive"] and Rect2(Vector2(h["cell"]), Vector2(2, 2) if map.source == "text" else Vector2(1, 1)).grow(BLAST * 0.6).has_point(at):
			h["alive"] = false
			for dy in 2:
				for dx in 2:
					_blocked.erase(h["cell"] + Vector2i(dx, dy))
					if not map.blocks(h["cell"] + Vector2i(dx, dy)):
						_astar.set_point_solid(h["cell"] + Vector2i(dx, dy), false)
			event.emit("hut_destroyed", {"pos": Vector2(h["cell"]) + Vector2(1, 1), "id": h["id"]})


func _kill_enemy(e: Dictionary, by: int) -> void:
	e["alive"] = false
	kills += 1
	for s in soldiers:
		if s["id"] == by:
			s["kills"] += 1
	event.emit("enemy_death", {"pos": e["pos"], "id": e["id"]})


func _kill_soldier(s: Dictionary, why: String) -> void:
	s["alive"] = false
	event.emit("death", {"pos": s["pos"], "who": "soldier", "id": s["id"], "why": why})


func _pickups() -> void:
	for s in alive_soldiers():
		var i := 0
		while i < crates.size():
			if (crates[i]["pos"] as Vector2).distance_to(s["pos"]) < 0.7:
				var c := crates[i]
				if c["kind"] == "grenades":
					grenades += 4
				else:
					rockets += 4
				event.emit("pickup", {"kind": c["kind"], "pos": c["pos"], "id": c["id"]})
				crates.remove_at(i)
				continue
			i += 1
		for hs in hostages:
			if not hs["following"] and not hs["rescued"] and (hs["pos"] as Vector2).distance_to(s["pos"]) < 0.9:
				hs["following"] = true
				event.emit("hostage_found", {"pos": hs["pos"]})
	# hostages follow the tail of the squad and walk into the tent
	var tail := _trail_point(float(alive_soldiers().size()) * FOLLOW_GAP + 0.6)
	for t in tents:  # once the squad reaches the tent, the hostages walk in
		for s in alive_soldiers():
			if t.distance_to(s["pos"]) < 2.0:
				tail = t
	for hs in hostages:
		if hs["following"] and not hs["rescued"]:
			hs["pos"] = (hs["pos"] as Vector2).move_toward(tail, SPEED * TICK)
			for t in tents:
				if t.distance_to(hs["pos"]) < 1.2:
					hs["rescued"] = true
					event.emit("rescued", {"pos": hs["pos"]})


func _check_end() -> void:
	if alive_soldiers().is_empty():
		phase = Phase.LOST
		event.emit("lost", {})
		return
	for g in map.goals:
		if not goal_done(g):
			return
	phase = Phase.WON
	event.emit("won", {"kills": kills})
